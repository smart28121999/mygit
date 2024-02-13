import boto3

def create_ALB():
    ec2 = boto3.client('ec2')

    #create vpc
    vpc = ec2.create_vpc(cidrblock='10.0.0.0/16')

    #create subnets
    public_subnet_az1 = vpc.create_subnet(
        cidrblock='10.0.1.0/24',
        AvailabilityZone='us-east-1a'
    )

    private_subnet_az1 = vpc.create_subnet(
        cidrblock='10.0.2.0/24',
        AvailabilityZone='us-east-1a'
    )

    public_subnet_az2 = vpc.create_subnet(
        cidrblock='10.0.3.0/24',
        AvailabilityZone='us-east-2a'
    )

    private_subnet_az2 = vpc.create_subnet(
        cidrblock='10.0.4.0/24',
        AvailabilityZone='us-east-2a'
    )

    #create IGW
    internet_gateway=ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)

    #create route tables
    RT_pub_subnet_az1=vpc.create_route_table()
    RT_pub_subnet_az1.associate_with_subnet(subnetId=public_subnet_az1.id)
    RT_pub_subnet_az1.create_route(
        DestCidrBlock = '0.0.0.0/0',
        GatewayId=internet_gateway.id
    )

    RT_pub_subnet_az2=vpc.create_route_table()
    RT_pub_subnet_az2.associate_with_subnet(subnetId=public_subnet_az2.id)
    RT_pub_subnet_az2.create_route(
        DestCidrBlock='0.0.0.0/0',
        GatewayId=internet_gateway.id
    )

    #create NATG in az1
    nat_gateway_az1=ec2.create_nat_gateway(
        subnetId=public_subnet_az1.id
    )

    #create NATG in az2
    nat_gateway_az2=ec2.create_nat_gateway(
        subnetId=public_subnet_az2.id
    )

    #create RT for private subnets
    RT_pri_subnet_az1=vpc.create_route_table()
    RT_pri_subnet_az1.associate_route_table(subnetId=private_subnet_az1)
    RT_pri_subnet_az1.create_route(
        DestCidrBlock='0.0.0.0/0',
        GatewwayId=nat_gateway_az1.id
    )

    RT_pri_subnet_az2=vpc.create_route_table()
    RT_pri_subnet_az2.associate_route_table(subnetId=private_subnet_az2)
    RT_pri_subnet_az2.create_route(
        DestCidrBlock='0.0.0.0/0',
        GatewayId=nat_gateway_az2.id
    )

    #create SG
    sg = ec2.create_security_group(
         GroupName='My SG',
         Description='SG for ALB-ec2 attachement',\
         vpc=vpc.id
         )
    
    ec2.authorize_security_group_ingress(
        GroupId=sg.id,
        IpPermissions=[
            {
                'IpProtocol':'tcp',
                'FromPort':80,
                'ToPort':80,
                'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            }
        ]
    )

    #create ec2 instance
    ec2.run_instances(
        ImageId='ami-id',
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        SubnetId=private_subnet_az1.id,
        SG_ID=sg.id
    )

    #create lambda function
    create_lambda = boto3.client('lambda')

    create_lambda.create_function(
        FunctionName='my_lambda_function',
        Runtime='python3.10',
        Role='lambda_role_arn',
        Code={'ZipFile':open('lambda_function.zip','rib').read()}
    )

    #create Application Load Balancer
    elbv2=boto3.client('ElasticLoadBalancingv2')

    alb = elbv2.create_load_balancer(
        Name='my-alb',
        Subnets=[private_subnet_az1,private_subnet_az2],
        SecurityGroups=[sg.id],
        Scheme='internet_facing',
        Tags=[
            {
                'Key': 'Name',
                'Value': 'my_alb'
            },
        ],
        Type='application',
        IpAddressType='ipv4'
    )

    #create target groups
    target_group1=elbv2.create_target_group(
        Name='target_group_1',
        Protocol='HTTP',
        Port=80,
        VpcId='string',
        TargetType='instance',
        IpAddressType='ipv4'
    )

    target_group2=elbv2.create_target_group(
        Name='target_group_2',
        TargetType='lambda',
        IpAddressType='ipv4'
    )

    #create listeners for path based routing
    listener1=elbv2.create_listener(
    LoadBalancerArn='elbv2_arn',
    Protocol='HTTP',
    Port=80,
    DefaultActions=[
        {
        'Type': 'forward',
        'ForwardConfig': {
                'TargetGroups': [
                    {
                        'TargetGroupArn': 'target_group1_arn',
                    },
                ],
        }
        }
    ]    
    )

    #create rules to distribute traffic based on path
    rule1=elbv2.create_rule(
    ListenerArn='listener1_arn',
    Conditions=[
        {
            'Field':'path-pattern',
            'Values':['/user']
        }
    ],
    Priority=1,
    Actions=[
        {
            'Type': 'forward',
            'TargetGroupArn': 'target_group1_arn'
        }
    ]
    )

    rule1=elbv2.create_rule(
    ListenerArn='listener1_arn',
    Conditions=[
        {
            'Field':'path-pattern',
            'Values':['/search']
        }
    ],
    Priority=2,
    Actions=[
        {
            'Type': 'forward',
            'TargetGroupArn': 'target_group2_arn'
        }
    ]
    )
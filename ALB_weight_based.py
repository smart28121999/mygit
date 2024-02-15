import boto3

#architecture same as ALB_demo path based routing

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

#register target group for ec2 instance
reg_ec2_tg=elbv2.register_targets(
        TargetGroupArn='Target_group1_arn',
        Targets=[
            {
                'Id':'ec2.id',
                'Port':80,
            }
        ]
    )

#create target group for lambda
target_group2=elbv2.create_target_group(
        Name='target_group_2',
        TargetType='lambda',
        IpAddressType='ipv4'
    )

#register target group for lambda
reg_lambda_tg=elbv2.register_targets(
        TargetGroupArn='Target_group2_arn',
        Targets=[
            {
                'Id':'lambda.id',
                'Port':80,
            }
        ]
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
                        'Weight':10
                    },
                    {
                        'TargetGroupArn': 'target_group2_arn',
                        'Weight':20
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
import boto3

def create_vpc():
    ec2 = boto3.resource('ec2')
    
    #create vpc
    vpc = ec2.create_vpc(cidrblock='10.0.0.0/16')
    
    #create public subnet
    pub_subnet1 = vpc.create_subnet(
        cidrblock='10.0.1.0/24',
        AvailabilityZone='us-east-1a'
    )
    pub_subnet2 = vpc.create_subnet(
        cidrblock='10.0.2.0/24',
        AvailabilityZone='us-east-1a'
    )
    
    #create private subent
    pri_subnet=vpc.create_subnet(
        cidrblock='10.0.3.0/24',
        AvailabilityZone='us-east-1a'
    )
    
    #create natgateway
    nat_gateway=ec2.create_nat_gateway(
        subnetID=pub_subnet1.id
    )
    
    #create internet gateway
    internet_gateway=ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)
    
    #create route table for public subnet1
    route_table_pub1=vpc.create_route_table()
    route_table_pub1.associate_with_subnet(subnetId=pub_subnet1.id)
    route_table_pub1.create_route(
        DestCidrBlock = '0.0.0.0/0',
        GatewayId=internet_gateway.id
    )
    
    #create route table for public subnet2
    route_table_pub2=vpc.create_route_table()
    route_table_pub2.associate_with_subnet(subnetId=pub_subnet2.id)
    route_table_pub2.create_route(
        DestCidrBlock = '0.0.0.0/0',
        NatGatewayId=nat_gateway.id
    )
    
    #create route table for private subnet
    route_table_pri=vpc.create_route_table()
    route_table_pri.associate_with_subnet(subnetId=pub_subnet1.id)
    route_table_pri.create_route(
        DestCidrBlock = '0.0.0.0/0',
        NatGatewatId=nat_gateway.id
    )
    
    #launch ec2 instance in public subnet
    ec2.create_instances(
        ImageId='ami-id',
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=2,
        NetwokInterfaces=[
            {
                'SubnetId':pub_subnet1.id,
                'Groups':['security-group-id']
            }
        ]
    )
    
    ec2.create_security_group(
        GroupName='VPC_DEMO_SG',
        Description='MY_SG_Group',
        VpcId=vpc_id
    )
    ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol':'tcp',
                'FromPort':80,
                'ToPort':80,
                'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            }
        ]
    )
    
    #launch ec2 instance in private subnet
    ec2.create_instances(
        ImageId='ami-id',
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[
            {
                'SubnetId':pri_subnet.id,
                'Groups':['security-group-id']
            }
        ]
        SG_Id=security_group_id
        subnet_Id=pri_subnet.id
    )
    
    
    if __name__=="main":
        create_vpc()
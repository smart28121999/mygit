import boto3

def route53():
    ec2 = boto3.client('ec2')

    #create vpc
    vpc = ec2.create_vpc(cidrblock='10.0.0.0/16')

    #create subnets
    public_subnet = vpc.create_subnet(
        cidrblock='10.0.0.0/24',
        AvailabilityZone='us-east-1a'
    )

    private_subnet_1 = vpc.create_subnet(
        cidrblock='10.0.10.0/24',
        AvailabilityZone='us-east-1a'
    )

    private_subnet_2 = vpc.create_subnet(
        cidrblock='10.0.11.0/24',
        AvailabilityZone='us-east-1a'
    )

    #create IGW
    internet_gateway=ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)

    #create NATG in az1
    nat_gateway=ec2.create_nat_gateway(
        subnetId=public_subnet.id
    )

    #create route tables
    RT_pub_subnet=vpc.create_route_table()
    RT_pub_subnet.associate_with_subnet(subnetId=public_subnet.id)
    RT_pub_subnet.create_route(
        DestCidrBlock = '0.0.0.0/0',
        GatewayId=internet_gateway.id
    )

    RT_pri_subnet_1=vpc.create_route_table()
    RT_pri_subnet_1.associate_with_subnet(subnetId=public_subnet.id)
    RT_pri_subnet_1.create_route(
        DestCidrBlock = '0.0.0.0/0',
        GatewayId=nat_gateway.id
    )

    RT_pri_subnet_2=vpc.create_route_table()
    RT_pri_subnet_2.associate_with_subnet(subnetId=public_subnet.id)
    RT_pri_subnet_2.create_route(
        DestCidrBlock = '0.0.0.0/0',
        GatewayId=nat_gateway.id
    )

    #create Security_Group
    security_group = ec2.create_security_group(
         GroupName='My SG',
         Description='SG for ALB-ec2 attachement',
         vpc=vpc.id
         )
    
    ec2.authorize_security_group_ingress(
        GroupId=security_group.id,
        IpPermissions=[
            {
                'IpProtocol':'tcp',
                'FromPort':22,
                'ToPort':22,
                'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            }
        ]
    )

    ec2.authorize_security_group_ingress(
        GroupId=security_group.id,
        IpPermissions=[
            {
                'IpProtocol':'icmp',
                'FromPort':-1,
                'ToPort':-1,
                'IpRanges':[{'CidrIp':'192.168.0.0/16'}]
            }
        ]
    )

    #create ec2 instance
    ec2.run_instances(
        ImageId='ami-id',
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        SubnetId=public_subnet.id,
        SG_ID=security_group.id
    )

    #create virtual private gateway
    vpn_gateway=ec2.create_vpn_gateway(
    AvailabilityZone='us-east-1a',
    Type='ipsec.1',
    TagSpecifications=[
        {
            'ResourceType': 'vpn-gateway',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'MyVpnGateway'
                },
            ]
        },
    ],
    )

    #attach vpn gateway to vpc
    attach_vpn_gateway=ec2.attach_vpn_gateway(
    VpcId='vpc_id',
    VpnGatewayId='vpn_gateway_id'
    )

    #create customer gateway
    customer_gateway=ec2.create_customer_gateway(
    PublicIp='11.11.11.11',
    Type='ipsec.1',
    TagSpecifications=[
        {
            'ResourceType': 'customer-gateway',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'MyCustomerGateway'
                },
            ]
        },
    ],
    )

    #create site-to-site vpn connection
    vpn_connection=ec2.create_vpn_connection(
        CustomerGatewayId='customer_gateway_id',
        Type='ipsec.1',
        VpnGatewayId='vpn_gateway_id',
        Options={
            'StaticRoutesOnly':True,
            'TunnelInsideIpVersion': 'ipv4',
            'TunnelOptions':[
                {
                    'TunnelInsideCidr':'198.162.0.0/16',
                    'PreSharedKey': 'pre_shared_key'
                }
            ]
        }
    )

    ec2.enable_vgw_route_propagation(
        GatewayId='vpn_gateway_id',
        RouteTableId='RT_pub_subnet_id',
    )

    #modify dns resolution & dns hostnames
    enable=ec2.modify_vpc_attribute(
        EnableDnsHostnames={
            'Value': True
        },
        EnableDnsSupport={
        'Value': True
        },
        VpcId='vpc_id',
    )
    
    #create route53 for cloud.com
    route53=boto3.client('route53')

    #create private hosted zone
    hosted_zone=route53.create_hosted_zone(
        Name='www.cloud.com',
        VPC={
            'VPCRegion': 'us-east-1',
            'VPCId': 'vpc_id'
        },
        CallerReference='any_unique_string',
        HostedZoneConfig={
            'Comment': 'string',
            'PrivateZone': True
        }
    )

    #attach private hosted zone to vpc
    route53.associate_vpc_with_hosted_zone(
        HostedZoneId='string',
        VPC={
            'VPCRegion': 'us-east-1',
            'VPCId': 'vpc_id'
        }
    )

    #create resource records
    route53.change_resource_record_sets(
        HostedZoneId='hosted_zone_id',
        ChangeBatch={
            'Changes':[
                {
                    'Action':'Create',
                    'ResourceRecordSet':{
                        'Name':'app.cloud.com',
                        'Type':'A',
                        'TTL':300,
                        'ResourceRecords':[
                            {
                                'Value':'ec2_private_ip'
                            }
                        ]
                    }
                }
            ]
        }
    )

    #create SG for route53 resolver inbound endpoint
    Resolver_SG_1 = ec2.create_security_group(
         GroupName='My_Resolver_SG_1',
         Description='SG Resolver Inbound/Outbound Endpoint',
         vpc=vpc.id
         )
    
    #allow dns(udp 53) from on-prem
    ec2.authorize_security_group_ingress(
        GroupId=Resolver_SG_1.id,
        IpPermissions=[
            {
                'IpProtocol':'udp',
                'FromPort':53,
                'ToPort':53,
                'IpRanges':[{'CidrIp':'192.168.0.0/16'}]
            }
        ]
    )

    #create route53 resolver inbound endpoint
    route53_resolver=boto3.client('route53resolver')

    route53_resolver.create_resolver_endpoint(
        CreatorRequestId='15-02-2024',
        SecurityGroupIds=[
            'Resolver_SG_1_id',
        ],
        Direction='INBOUND',
        IpAddresses=[
            {
                'SubnetId': 'private_subnet_1_id',
            },
        ],
    )

    route53_resolver.create_resolver_endpoint(
        CreatorRequestId='5_pm',
        SecurityGroupIds=[
            'Resolver_SG_1_id',
        ],
        Direction='OUTBOUND',
        IpAddresses=[
            {
                'SubnetId': 'private_subnet_1_id',
            },
        ],
    )

    #create SG for route53 resolver inbound endpoint
    Resolver_SG_2 = ec2.create_security_group(
         GroupName='My_Resolver_SG_2',
         Description='SG Resolver Inbound/Outbound Endpoint',
         vpc=vpc.id
         )
    
    #allow dns(udp 53) from on-prem
    ec2.authorize_security_group_ingress(
        GroupId=Resolver_SG_2.id,
        IpPermissions=[
            {
                'IpProtocol':'udp',
                'FromPort':53,
                'ToPort':53,
                'IpRanges':[{'CidrIp':'192.168.0.0/16'}]
            }
        ]
    )

    route53_resolver.create_resolver_endpoint(
        CreatorRequestId='8_pm',
        SecurityGroupIds=[
            'Resolver_SG_2_id',
        ],
        Direction='INBOUND',
        IpAddresses=[
            {
                'SubnetId': 'private_subnet_1_id',
            },
        ],
    )

    route53_resolver.create_resolver_endpoint(
        CreatorRequestId='5_pm',
        SecurityGroupIds=[
            'Resolver_SG_2_id',
        ],
        Direction='OUTBOUND',
        IpAddresses=[
            {
                'SubnetId': 'private_subnet_1_id',
            },
        ],
    )
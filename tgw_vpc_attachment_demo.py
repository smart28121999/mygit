import boto3

def create_vpc_tgw_attachment():
    ec2 = boto3.client('ec2')
    #
    #create prod vpc
    Prod_VPC = ec2.create_vpc(cidrblock='10.0.0.0/16')
    
    prod_public_subnet=Prod_VPC.create_subnet(
        cidrblock='10.0.1.0/24',
        AvailabilityZone='us-east-1a'
    )
    
    prod_private_subnet=Prod_VPC.create_subnet(
        cidrblock='10.0.2.0/24',
        AvailabilityZone='us-east-1a'
    )
    
    #
    #create transit gateway
    transit_gateway = ec2.create_transit_gateway(
        Description='This is transit gateway',
        TagSpecifications=[
        {
            'ResourceType': 'transit-gateway',
            'Tags': [
                {
                    'Key': 'anything',
                    'Value': 'anything'
                },
            ]
        },
    ],
    )
    
    #create route table
    prod_vpc_route_table=ec2.create_route_table()
    prod_vpc_route_table.associate_with_subnet(subnetId=prod_public_subnet.id)
    prod_vpc_route_table.create_route(
        DestCidrBlock = '10.2.0.0/16',
        GatewayId=transit_gateway.id
    )
    
    #
    #create non-prod vpc
    Non_prod_vpc = ec2.create_vpc(cidrblock='10.1.0.0/16')
    
    non_prod_private_subnet = Non_prod_vpc.create_subnet(
        cidrblock='10.1.1.0/24',
        AvailabilityZone='us-east-1a'
    )
    
    #create route table
    non_prod_vpc_route_table=ec2.create_route_table()
    non_prod_vpc_route_table.associte_with_subnet(subnetId=non_prod_private_subnet.id)
    non_prod_vpc_route_table.create_route(
        DestCidrBlock = '10.2.0.0/16',
        GatewayId=transit_gateway.id
    )
    
    #
    #create junction vpc
    junction_vpc = ec2.create_vpc(cidrblock='10.2.0.0/16')
    
    junction_private_subnet = junction_vpc.create_subnet(
        cidrblock='10.2.1.0/24',
        AvailabilityZone='us-east-1a'
    )
    
    #create route table
    junction_vpc_route_table=ec2.create_route_table()
    junction_vpc_route_table.associte_with_subnet(subnetId=junction_private_subnet.id)
    junction_vpc_route_table.create_route(
        DestCidrBlock='10.0.0.0/16',
        #GatewayId='string'
    )
    junction_vpc_route_table.create_route(
        DestCidrBlock='10.1.0.0/16',
        #GatewayId='string'
    )
 
#-----------   
    #create tgw attachment
    vpc_transit_gateway_attachment1 = ec2.create_transit_gateway_vpc_attachment(
        TransitGatewayId='transit_gateway.id',
        VpcId='Prod_VPC.id',
        SubnetIds=[
            'prod_public_subnet.id',
            'prod_priavte_subnet.id'
    ],
        TagSpecifications=[
        {
            'ResourceType': 'transit-gateway-attachment',
            'Tags': [
                {
                    'Key': 'anything',
                    'Value': 'anything'
                },
            ]
        },
    ],  
    )
    
    #create tgw route table for prod vpc
    prod_vpc_transit_gateway_RT = ec2.create_transit_gateway_route_table(
    TransitGatewayId='transit_gateway.id',
    TagSpecifications=[
        {
            'ResourceType': 'transit_gateway_route_table',
            'Tags': [
                {
                    'Key': 'string',
                    'Value': 'string'
                },
            ]
        },
    ],
    )
    
    #associating route table
    associate_RT_with_attachment1 = prod_vpc_transit_gateway_RT.associate_transit_gateway_route_table(
    TransitGatewayRouteTableId='prod_vpc_transit_gateway_RT.id',
    TransitGatewayAttachmentId='vpc_transit_gateway_attachment1.id',
    )
    
#-----------
    #create tgw attachment    
    vpc_transit_gateway_attachment2 = ec2.create_transit_gateway_vpc_attachment(
        TransitGatewayId='transit_gateway.id',
        VpcId='Non_prod_vpc.id',
        SubnetIds=[
            'non_prod_private_subnet.id',
    ],
        TagSpecifications=[
        {
            'ResourceType': 'transit-gateway-attachment',
            'Tags': [
                {
                    'Key': 'anything',
                    'Value': 'anything'
                },
            ]
        },
    ],  
    )
    
    # #create tgw route table for non_prod vpc
    non_prod_vpc_transit_gateway_RT = ec2.create_transit_gateway_route_table(
    TransitGatewayId='transit_gateway.id',
    TagSpecifications=[
        {
            'ResourceType': 'transit_gateway_route_table',
            'Tags': [
                {
                    'Key': 'string',
                    'Value': 'string'
                },
            ]
        },
    ],
    )
    
    #associating route table
    associate_RT_with_attachment2 = prod_vpc_transit_gateway_RT.associate_transit_gateway_route_table(
    TransitGatewayRouteTableId='non_prod_vpc_transit_gateway_RT.id',
    TransitGatewayAttachmentId='vpc_transit_gateway_attachment2.id',
    )
    
#-----------    
    #create tgw attachment
    vpc_transit_gateway_attachment3 = ec2.create_transit_gateway_vpc_attachment(
        TransitGatewayId='transit_gateway.id',
        VpcId='junction_vpc.id',
        SubnetIds=[
            'junction_private_subnet.id',
    ],
        TagSpecifications=[
        {
            'ResourceType': 'transit-gateway-attachment',
            'Tags': [
                {
                    'Key': 'anything',
                    'Value': 'anything'
                },
            ]
        },
    ],  
    )
    
    # #create tgw route table for junction vpc
    junction_vpc_transit_gateway_RT = ec2.create_transit_gateway_route_table(
    TransitGatewayId='transit_gateway.id',
    TagSpecifications=[
        {
            'ResourceType': 'transit_gateway_route_table',
            'Tags': [
                {
                    'Key': 'string',
                    'Value': 'string'
                },
            ]
        },
    ],
    )
    
    #associating route table
    associate_RT_with_attachment3 = prod_vpc_transit_gateway_RT.associate_transit_gateway_route_table(
    TransitGatewayRouteTableId='junction_vpc_transit_gateway_RT.id',
    TransitGatewayAttachmentId='vpc_transit_gateway_attachment3.id',
    )
    
#-----------    

    #dynamically propagating the route tables of VPC to tgw
    ec2.enable_transit_gateway_route_table_propagation(
    TransitGatewayRouteTableId='transit_gateway_route_table.id',
    TransitGatewayAttachmentId='vpc_transit_gateway_attachment1.id',
    )
    
    ec2.enable_transit_gateway_route_table_propagation(
    TransitGatewayRouteTableId='transit_gateway_route_table.id',
    TransitGatewayAttachmentId='vpc_transit_gateway_attachment2.id',
    )
    
    ec2.enable_transit_gateway_route_table_propagation(
    TransitGatewayRouteTableId='transit_gateway_route_table.id',
    TransitGatewayAttachmentId='vpc_transit_gateway_attachment3.id',
    )

    #create internet gateway
    internet_gateway=ec2.create_internet_gateway()
    Prod_VPC.attach_internet_gateway(InternetGatewayId=internet_gateway.id)
    
if __name__=="main":
        create_vpc_tgw_attachment()

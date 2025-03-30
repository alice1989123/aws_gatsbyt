from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class VpcConstruct(Construct):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        self.vpc = ec2.Vpc(
            self, "CryptoAppVpc",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ],
            nat_gateways=0  # no need for NAT if we're going fully public
        )

from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy
)
import boto3
from constructs import Construct
from aws_cdk import SecretValue
import os
import dotenv
dotenv.load_dotenv("btc_forecast_aws/.env")

DBUSER = os.getenv("DBUSER")
if not DBUSER:
    raise ValueError("DBUSER not found in environment!")

DBPASSWORD = os.getenv("DBPASSWORD")
if not DBPASSWORD:
    raise ValueError("DBPASSWORD not found in environment!")

credentials = rds.Credentials.from_password(
    username=DBUSER,
    password=SecretValue.plain_text(DBPASSWORD)
)
identifier ='crypto-postgres-db'


def get_rds_endpoint(instance_identifier: str) -> str:
    rds = boto3.client("rds")
    try:
        response = rds.describe_db_instances(DBInstanceIdentifier=instance_identifier)
        return response["DBInstances"][0]["Endpoint"]["Address"]
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve RDS endpoint: {e}")
    
class PostgresDatabase(Construct):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, bastion_sg: ec2.ISecurityGroup = None, **kwargs):
        super().__init__(scope, id, **kwargs)

        rds_exists = self.node.try_get_context("rds_exists") == "true"
        
        if rds_exists:
                endpoint_address = get_rds_endpoint(identifier)
  
                self.db_instance = rds.DatabaseInstance.from_database_instance_attributes(
                self, identifier,
                instance_identifier=identifier,
                instance_endpoint_address=endpoint_address,  
                port=5432,
                security_groups=[],  
            )
        else:
            self.db_instance = rds.DatabaseInstance(
                self, "crypto-postgres-db",
                engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_17),
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO,
                ),
                instance_identifier="crypto-postgres-db",
                vpc=vpc,
                credentials=credentials,
                database_name="cryptodata",
                allocated_storage=20,
                max_allocated_storage=100,
                publicly_accessible=False,
                removal_policy=RemovalPolicy.DESTROY,
                delete_automated_backups=True,
                multi_az=False,
                vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                
                 # 🔒 only one AZ
                ),
            )
        bastion_sg = kwargs.pop("bastion_sg", None)

        if bastion_sg :
            self.db_instance.connections.allow_from(
            bastion_sg,
            ec2.Port.tcp(5432),
            "Allow Bastion Host to access PostgreSQL"
        )

            self.secret = self.db_instance.secret

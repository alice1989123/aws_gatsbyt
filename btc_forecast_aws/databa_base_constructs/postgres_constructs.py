import boto3
from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy
)
from constructs import Construct

# Define identifier
identifier = 'crypto-postgres-db2'

# External credentials defined elsewhere
from aws_cdk import SecretValue
import os, dotenv
dotenv.load_dotenv("btc_forecast_aws/.env")

DBUSER = os.getenv("DBUSER")
DBPASSWORD = os.getenv("DBPASSWORD")

credentials = rds.Credentials.from_password(
    username=DBUSER,
    password=SecretValue.plain_text(DBPASSWORD)
)

# Safely fetch endpoint
def get_rds_endpoint(instance_identifier: str) -> str:
    rds_client = boto3.client("rds")
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_identifier)
        return response["DBInstances"][0]["Endpoint"]["Address"]
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve RDS endpoint: {e}")

# Main construct
class PostgresDatabase(Construct):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, bastion_sg: ec2.ISecurityGroup = None, **kwargs):
        super().__init__(scope, id, **kwargs)

        rds_exists = self.node.try_get_context("rds_exists") == "true"

        if rds_exists:
            endpoint_address = get_rds_endpoint(identifier)

            self.db_instance = rds.DatabaseInstance.from_database_instance_attributes(
                self, "ImportedRDSInstance",
                instance_identifier=identifier,
                instance_endpoint_address=endpoint_address,
                port=5321,
                security_groups=[] 
            )
            self.secret = None  
        else:
            self.db_instance = rds.DatabaseInstance(
                self, identifier,
                engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_17),
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
                ),
                instance_identifier=identifier,
                vpc=vpc,
                credentials=credentials,
                database_name="cryptodata",
                allocated_storage=20,
                max_allocated_storage=100,
                publicly_accessible=True,
                removal_policy=RemovalPolicy.RETAIN,
                delete_automated_backups=True,
                multi_az=False,
                #vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                #security_groups=[bastion_sg] if bastion_sg else None
            )
            self.secret = self.db_instance.secret
        if bastion_sg:
            self.db_instance.connections.allow_from(
                bastion_sg,
                ec2.Port.tcp(5432),
                "Allow Bastion Host to access PostgreSQL"
        )

        

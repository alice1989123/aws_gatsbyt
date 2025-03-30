from aws_cdk import (
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct

class DynamoTables(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.crypto_data_table = dynamodb.Table(
            self, "CryptoDataTable",
            table_name="crypto_news",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="date", type=dynamodb.AttributeType.STRING),
            max_read_request_units=10,
            max_write_request_units=10,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.predictions_table = dynamodb.Table(
            self, "PredictionsTable",
            table_name="crypto_predictions_",
            partition_key=dynamodb.Attribute(name="coin", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            max_read_request_units=10,
            max_write_request_units=10
        )
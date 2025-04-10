from aws_cdk import (
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct

class DynamoTables(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        crypto_news_exists = self.node.try_get_context("crypto_news_exists") == "true"
        crypto_predictions_exists = self.node.try_get_context("crypto_predictions_exists") == "true"

        if crypto_news_exists:
            self.crypto_data_table = dynamodb.Table.from_table_name(
                self, "CryptoDataTableImport", table_name="crypto_news"
            )
        else:
            self.crypto_data_table = dynamodb.Table(
                self, "CryptoDataTable",
                table_name="crypto_news",
                billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
                sort_key=dynamodb.Attribute(name="date", type=dynamodb.AttributeType.STRING),
                removal_policy=RemovalPolicy.RETAIN,
                max_read_request_units=10,
                max_write_request_units=10,
            )

        if crypto_predictions_exists:
            self.predictions_table = dynamodb.Table.from_table_name(
                self, "PredictionsTableImport", table_name="crypto_predictions_"
            )
        else:
            self.predictions_table = dynamodb.Table(
                self, "PredictionsTable",
                table_name="crypto_predictions_",
                billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                partition_key=dynamodb.Attribute(name="coin", type=dynamodb.AttributeType.STRING),
                sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
                removal_policy=RemovalPolicy.RETAIN,
                max_read_request_units=10,
                max_write_request_units=10,
            )

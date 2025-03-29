from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    RemovalPolicy
)
from constructs import Construct
from btc_forecast_aws.lambda_constructs.lambda_constructs import ForecastLambdas
from btc_forecast_aws.dynamo_constructs.dynamo_constructs import DynamoTables
class BtcForecastAwsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define all DynamoDB tables
        tables = DynamoTables(self, "DynamoTables")

        # Define all Lambda functions and link to tables
        lambdas = ForecastLambdas(self, "ForecastLambdas", tables=tables)

        # Create the API Gateway
        self.api = apigw.RestApi(
            self, "CryptoAPI",
            rest_api_name="CryptoAPI",
            deploy_options=apigw.StageOptions(stage_name="default")
        )

        # Create the /news resource
        news_resource = self.api.root.add_resource("news")
        news_integration = apigw.LambdaIntegration(lambdas.crypto_news_lambda)
        news_resource.add_method("GET", news_integration, authorization_type=apigw.AuthorizationType.IAM)

        # Create the /predictions resource
        predictions_resource = self.api.root.add_resource("predictions")
        predictions_integration = apigw.LambdaIntegration(lambdas.predictions_lambda)
        predictions_resource.add_method("GET", predictions_integration, authorization_type=apigw.AuthorizationType.IAM)
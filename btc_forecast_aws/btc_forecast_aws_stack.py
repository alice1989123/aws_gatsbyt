from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
     aws_sqs as sqs
)
from constructs import Construct
from btc_forecast_aws.lambda_constructs.lambda_constructs import ForecastLambdas
from btc_forecast_aws.dynamo_constructs.dynamo_constructs import DynamoTables
from btc_forecast_aws.ecs.ecr_constructs import EcrConstruct
from btc_forecast_aws.ecs.ecs_cluster_construct  import EcsClusterConstruct
from btc_forecast_aws.ecs.ecs_service_construct import ScheduledScraperTaskConstruct
from btc_forecast_aws.network.vpc_construct import VpcConstruct
import os
import dotenv
import boto3

dotenv.load_dotenv("btc_forecast_aws/.env")

ssm = boto3.client('ssm')

# Get API key from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment!")

response = ssm.put_parameter(
    Name='/scraper/OPENAI_API_KEY',
    Value=OPENAI_API_KEY,
    Type='SecureString',
    Overwrite=True  # Set to False if you don't want to overwrite existing
)


image_uri="390402534126.dkr.ecr.eu-central-1.amazonaws.com/crypto_repo:latest"



class BtcForecastAwsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define all DynamoDB tables
        tables = DynamoTables(self, "DynamoTables")
    # Create the SQS queues

        dlq = sqs.Queue(
            self, "ScraperDLQ",
            queue_name="ScraperDLQ"
        )

        scraper_queue = sqs.Queue(
            self, "ScraperQueue",
            queue_name="ScraperQueue",
            dead_letter_queue=sqs.DeadLetterQueue(
            max_receive_count=3,  # After 3 failed receives, message goes to DLQ
            queue=dlq)
            )
        # Define all Lambda functions and link to tables
        lambdas = ForecastLambdas(self, "ForecastLambdas", tables=tables ,queue=scraper_queue)

        # Create the API Gateway
        self.api = apigw.RestApi(
            self, "CryptoAPI",
            rest_api_name="CryptoAPI",
            deploy_options=apigw.StageOptions(stage_name="default")
        )

        self.ecr_construct = EcrConstruct(self, "EcrConstruct", repo_name="crypto_repo")

       

        # Create the /news resource
        news_resource = self.api.root.add_resource("news")
        news_integration = apigw.LambdaIntegration(lambdas.crypto_news_lambda)
        news_resource.add_method("GET", news_integration, authorization_type=apigw.AuthorizationType.IAM)

        # Create the /predictions resource
        predictions_resource = self.api.root.add_resource("predictions")
        predictions_integration = apigw.LambdaIntegration(lambdas.predictions_lambda)
        predictions_resource.add_method("GET", predictions_integration, authorization_type=apigw.AuthorizationType.IAM)

        vpc = VpcConstruct(self, "VpcConstruct").vpc
        cluster = EcsClusterConstruct(self, "EcsCluster", vpc=vpc).cluster


        
        ScheduledScraperTaskConstruct(
            self, "ScheduledScraperTask",
            cluster=cluster,
            image_uri=image_uri,
            queue=scraper_queue
        )
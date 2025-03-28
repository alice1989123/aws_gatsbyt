from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    RemovalPolicy

)
from constructs import Construct


class BtcForecastAwsStack(Stack):

        def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
            super().__init__(scope, construct_id, **kwargs)

            binance_layer = _lambda.LayerVersion.from_layer_version_arn(
                self,
                "BinanceLayer",
                "arn:aws:lambda:eu-central-1:390402534126:layer:PythonBinance:1"  
            )
            pandas_layer = _lambda.LayerVersion.from_layer_version_arn(
                self,
                "PandasLayer",
                "arn:aws:lambda:eu-central-1:390402534126:layer:python-pandas-layer:1"  
            )
            numpy_layer = _lambda.LayerVersion.from_layer_version_arn(
                self,
                "NumpyLayer",
                "arn:aws:lambda:eu-central-1:390402534126:layer:python-numpy-layer:1"  
            )

            # Define the Lambda function
            lambda_function = _lambda.Function(
                self, "BtcForecastFunction",
                function_name="btc-forecast-handler",
                runtime=_lambda.Runtime.PYTHON_3_10,  # Match runtime with the layer's compatibility
                handler="get_klines.lambda_handler",  # Entry point for the Lambda function
                code=_lambda.Code.from_asset("lambda/get_klines"),  # Path to the Lambda function code
                layers=[binance_layer ,pandas_layer , numpy_layer],  # Attach the existing layer
                timeout=Duration.seconds(30), 
            )

            # Grant Lambda function permissions to read from SSM Parameter Store
            lambda_function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["ssm:GetParameter"],
                    resources=[
                        "arn:aws:ssm:eu-central-1:390402534126:parameter/Binance/*"
                    ]
                ))
            
            lambda_function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=[
                        "arn:aws:s3:::gatsbyt-binancedata",
                        "arn:aws:s3:::gatsbyt-binancedata/*"

                    ]
                ),
            )


            crypto_data_table = dynamodb.Table(
                self, "CryptoDataTable",
                table_name="crypto_data",
                billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
                
                sort_key=dynamodb.Attribute(name="date", type=dynamodb.AttributeType.STRING),
                max_read_request_units=10,    # ✅ Max 20 strongly consistent read units
                max_write_request_units=10,   # ✅ Max 10 write units
                removal_policy=RemovalPolicy.DESTROY
            )
            crypto_news_lambda = _lambda.Function(
                self, "crypoNewsAPI",
                function_name="crypto_news",
                runtime=_lambda.Runtime.PYTHON_3_12,  # Match runtime with the layer's compatibility
                handler="get_news.lambda_handler",  # Entry point for the Lambda function
                code=_lambda.Code.from_asset("lambda/get_news"),  # Path to the Lambda function code
                timeout=Duration.seconds(30), 
            )
            crypto_news_lambda.add_environment("DYNAMO_TABLE_NAME", crypto_data_table.table_name)
            crypto_data_table.grant_read_data(crypto_news_lambda)

            predictions_table = dynamodb.Table(
            self, "PredictionsTable",
            table_name="crypto_predictions_",
            partition_key=dynamodb.Attribute(name="coin", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            max_read_request_units=10,    # ✅ Max 20 strongly consistent read units
            max_write_request_units=10,   
                )

            predictions_lambda = _lambda.Function(
            self, "PredictionsAPI",
            function_name="crypto_predictions_handler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_predictions.lambda_handler",
            code=_lambda.Code.from_asset("lambda/get_predictions"),  # adjust path
            environment={
                "PREDICTIONS_TABLE": predictions_table.table_name
            },
            timeout=Duration.seconds(30)
        )

            predictions_table.grant_read_data(predictions_lambda)


            # Create the API Gateway
            self.api = apigw.RestApi(
                self, "CryptoAPI",
                rest_api_name="CryptoAPI",
                deploy_options=apigw.StageOptions(stage_name="default") )


            
            # Create the /news resource
            news_resource = self.api.root.add_resource("news")

            # Create the integration with the Lambda function
            news_integration = apigw.LambdaIntegration(crypto_news_lambda)

            # Add GET method with IAM authorization
            news_resource.add_method(
                "GET",
                news_integration,
                authorization_type=apigw.AuthorizationType.IAM
            )

            predictions_resource = self.api.root.add_resource("predictions")

            # Create the integration with the Lambda function
            predictions_integration = apigw.LambdaIntegration(predictions_lambda)

            # Add GET method with IAM authorization
            predictions_resource.add_method(
                "GET",
                predictions_integration,
                authorization_type=apigw.AuthorizationType.IAM
            )


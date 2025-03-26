from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration
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
            )
        )


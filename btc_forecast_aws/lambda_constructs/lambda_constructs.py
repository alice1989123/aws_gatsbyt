from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class ForecastLambdas(Construct):
    def __init__(self, scope: Construct, id: str, tables, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.binance_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "BinanceLayer",
            "arn:aws:lambda:eu-central-1:390402534126:layer:PythonBinance:1"
        )
        self.pandas_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "PandasLayer",
            "arn:aws:lambda:eu-central-1:390402534126:layer:python-pandas-layer:1"
        )
        self.numpy_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "NumpyLayer",
            "arn:aws:lambda:eu-central-1:390402534126:layer:python-numpy-layer:1"
        )

        self.forecast_lambda = _lambda.Function(
            self, "BtcForecastFunction",
            function_name="btc-forecast-handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="get_klines.lambda_handler",
            code=_lambda.Code.from_asset("lambda/get_klines"),
            layers=[self.binance_layer, self.pandas_layer, self.numpy_layer],
            timeout=Duration.seconds(30)
        )

        self.forecast_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=["arn:aws:ssm:eu-central-1:390402534126:parameter/Binance/*"]
            )
        )

        self.forecast_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=[
                    "arn:aws:s3:::gatsbyt-binancedata",
                    "arn:aws:s3:::gatsbyt-binancedata/*"
                ]
            )
        )

        self.crypto_news_lambda = _lambda.Function(
            self, "CryptoNewsAPI",
            function_name="crypto_news",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_news.lambda_handler",
            code=_lambda.Code.from_asset("lambda/get_news"),
            timeout=Duration.seconds(30)
        )
        self.crypto_news_lambda.add_environment("DYNAMO_TABLE_NAME", tables.crypto_data_table.table_name)
        tables.crypto_data_table.grant_read_data(self.crypto_news_lambda)

        self.crypto_news_insert_lambda = _lambda.Function(
            self, "CryptoNewsInsert",
            function_name="crypoNewsInsert",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="insert_news.lambda_handler",
            code=_lambda.Code.from_asset("lambda/insert_news"),
            timeout=Duration.seconds(30)
        )
        self.crypto_news_insert_lambda.add_environment("DYNAMO_TABLE_NAME", tables.crypto_data_table.table_name)
        tables.crypto_data_table.grant_write_data(self.crypto_news_insert_lambda)

        self.predictions_lambda = _lambda.Function(
            self, "PredictionsAPI",
            function_name="crypto_predictions_handler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_predictions.lambda_handler",
            code=_lambda.Code.from_asset("lambda/get_predictions"),
            environment={"PREDICTIONS_TABLE": tables.predictions_table.table_name},
            timeout=Duration.seconds(30)
        )
        tables.predictions_table.grant_read_data(self.predictions_lambda)
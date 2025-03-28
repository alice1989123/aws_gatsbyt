import boto3
from datetime import datetime
from binance.client import Client
import pandas as pd
import io
import json

def lambda_handler(event, context):
    try:
        coin = event["coin"]
        start = event["start"]
        end = event["end"]
        s3_key = f"data/{coin}_{start.replace(' ', '-')}_{end.replace(' ', '-')}.json"
        s3_bucket = "gatsbyt-binancedata"
    except KeyError as e:
        return {
            "statusCode": 400,
            "body": f"Missing required query parameter: {e}"
        }

    # Get secrets from Parameter Store
    ssm = boto3.client("ssm", region_name="eu-central-1")
    API_SECRET = ssm.get_parameter(Name="/Binance/API_SECRET", WithDecryption=True)["Parameter"]["Value"]
    API_KEY = ssm.get_parameter(Name="/Binance/API_KEY", WithDecryption=True)["Parameter"]["Value"]

    # Get Binance data
    def get_klines(coin, start, end, interval=Client.KLINE_INTERVAL_1HOUR):
        client = Client(API_KEY, API_SECRET)
        data = client.get_historical_klines(symbol=coin, interval=interval, start_str=start, end_str=end)
        return data

    def data_parser(data):
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df.drop("ignore", axis=1, inplace=True)

        # Convert timestamps
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

        # Convert numeric columns only
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume',
                        'num_trades', 'taker_base_vol', 'taker_quote_vol']
        df[numeric_cols] = df[numeric_cols].astype(float)

        return df

    try:
        data = get_klines(coin, start, end)
        df = data_parser(data)

        # Upload to S3
        s3 = boto3.client('s3')
        json_buffer = io.StringIO()
        df.to_json(json_buffer, orient='records')
        s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=json_buffer.getvalue())

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Data fetched and uploaded to S3 successfully.",
                "s3_uri": f"s3://{s3_bucket}/{s3_key}"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error fetching or uploading Binance data: {str(e)}"
        }

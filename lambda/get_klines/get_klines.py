import boto3
from datetime import datetime
from binance.client import Client
import pandas as pd


   
   
def lambda_handler(event, context):
        # Initialize SSM client
        # Fetch parameters from the event
        try:
            coin = event["coin"]
            start = event["start"]
            end = event["end"]
        except KeyError as e:
            return {
                "statusCode": 400,
                "body": f"Missing required query parameter: {e}"
            }
        ssm = boto3.client("ssm", region_name="eu-central-1")

        # Fetch the Binance API keys from AWS Systems Manager Parameter Store
        API_SECRET = ssm.get_parameter(
            Name="/Binance/API_SECRET",
            WithDecryption=True
        )["Parameter"]["Value"]
        API_KEY = ssm.get_parameter(
            Name="/Binance/API_KEY",  # Corrected to fetch the right key
            WithDecryption=True
        )["Parameter"]["Value"]

                # Helper function to convert date string to timestamp
        def get_timestamp(date_str):
                date_obj = datetime.strptime(date_str, "%d %b %Y")
                timestamp_int = int(date_obj.timestamp())
                return timestamp_int
            
            
            # Helper function to get Binance data
        def get_klines(coin, start, end, interval=Client.KLINE_INTERVAL_1HOUR):
                client = Client(None, None)
                data = client.get_historical_klines(
                    symbol=coin,
                    interval=interval,
                    start_str=start,
                    end_str=end
                )
                return data
            

        def  data_parser(data):
                df_pred = pd.DataFrame(data , columns = ['open_time','open', 'high', 'low', 'close', 'volume','close_time', 'quote_asset_volume','num_trades','taker_base_vol','taker_quote_vol', 'ignore'] )
                # Convert Unix time to datetime format
                df_pred.drop("ignore", axis=1, inplace=True)
                df_pred['open_time'] = pd.to_datetime(df_pred['open_time'], unit='ms')

                # Set the datetime column as the index
                df_pred.set_index('open_time', inplace=True)

                # Convert the rest of the columns to float
                df_pred = df_pred.astype(float)
                return df_pred
                # Print the first few rows of the dataframe

        # Fetch Binance data
        try:
            data_pred = get_klines(coin, start, end)
            df_pred = data_parser(data_pred)
            print(df_pred )
            return {
                "statusCode": 200,
                "body": {
                    "data": df_pred.to_json(orient='records')
                }
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": f"Error fetching Binance data: {str(e)}"
            }
        
        
  

   

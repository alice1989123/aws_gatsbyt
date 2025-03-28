import json
import boto3
import os
import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            # Convert Decimal to float or int (depending on value)
            return float(obj) if '.' in str(obj) else int(obj)
        return super(JSONEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('PREDICTIONS_TABLE', 'crypto_predictions')

def lambda_handler(event, context):
    result = "none"
    try:
        query_params = event.get('queryStringParameters', {})
        coin = query_params.get('collection_name', 'BTCUSDT')  # Using 'coin' as partition key

        table = dynamodb.Table(TABLE_NAME)

        response = table.query(
            KeyConditionExpression=Key('coin').eq(coin),
            ScanIndexForward=False,  # Sort descending by timestamp
            Limit=1
        )

        items = response.get('Items', [])
        if items:
            item = items[0]
            result = {
                "predictions": item.get("predictions"),
                "metadata": item.get("metadata")
            }
        else:
            result = []

    except Exception as e:
        print(f"Error: {e}")
        result = {"error": str(e)}

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': JSONEncoder().encode(result)
    }

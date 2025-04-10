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
cache = {}

def lambda_handler(event, context):
    query_params = event.get('queryStringParameters', {})
    coin = query_params.get('collection_name', 'BTCUSDT')

    if coin in cache:
        print("💾 Served from memory cache!")
        result = cache[coin]
    else:
        # ... DynamoDB logic ...
        table = dynamodb.Table(TABLE_NAME)
        response = table.query(
            KeyConditionExpression=Key('coin').eq(coin),
            ScanIndexForward=False,
            Limit=1
        )
        items = response.get('Items', [])
        result = {"predictions": [], "metadata": {}}
        if items:
            item = items[0]
            result = {
                "predictions": item.get("predictions"),
                "metadata": item.get("metadata")
            }
        cache[coin] = result  # save in cache
        print("📥 Cached from DynamoDB")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': JSONEncoder().encode(result)
    }

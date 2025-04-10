import json
import boto3
import os
import datetime
import time
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Custom JSON encoder to handle datetime & Decimal
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj) if '.' in str(obj) else int(obj)
        return super(JSONEncoder, self).default(obj)

# Setup
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('PREDICTIONS_TABLE', 'crypto_predictions')
cache = {}
CACHE_TTL_SECONDS = 5 * 60  # 20 minutes

# DynamoDB query helper
def query_dynamodb(coin):
    table = dynamodb.Table(TABLE_NAME)
    response = table.query(
        KeyConditionExpression=Key('coin').eq(coin),
        ScanIndexForward=False,  # descending sort (latest first)
        Limit=1
    )
    items = response.get('Items', [])
    if items:
        return {
            "predictions": items[0].get("predictions"),
            "metadata": items[0].get("metadata")
        }
    return {"predictions": [], "metadata": {}}

def lambda_handler(event, context):
    query_params = event.get('queryStringParameters', {}) or {}
    coin = query_params.get('collection_name', 'BTCUSDT')

    cached_entry = cache.get(coin)
    now = time.time()

    if cached_entry:
        age = now - cached_entry["cached_at"]
        if age < CACHE_TTL_SECONDS:
            print("💾 Served from memory cache!")
            result = cached_entry["result"]
        else:
            print("♻️ Cache expired. Refreshing from DynamoDB...")
            result = query_dynamodb(coin)
            cache[coin] = {"result": result, "cached_at": now}
    else:
        print("📡 No cache found. Querying DynamoDB...")
        result = query_dynamodb(coin)
        cache[coin] = {"result": result, "cached_at": now}

    # Optional: Add cache timestamp to response (visible in frontend)
    result["cached_at"] = datetime.datetime.fromtimestamp(cache[coin]["cached_at"]).isoformat()

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

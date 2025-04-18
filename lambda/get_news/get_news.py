import json
import os
import time
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from decimal import Decimal

# Custom encoder for DynamoDB responses
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Clean up the item for frontend display
def clean_item(item):
    if "PK" in item:
        del item["PK"]
    if "date" in item and "T" in item["date"]:
        try:
            dt = datetime.fromisoformat(item["date"].replace("Z", ""))
            item["date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    return item

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ["DYNAMO_TABLE_NAME"])

# In-memory cache with TTL
cache = {}
CACHE_TTL_SECONDS = 5 * 60  # 20 minutes

def lambda_handler(event, context):
    try:
        # Defaults
        sources = event.get("sources", ["crypto.news"])
        limit = event.get("limit", 10)

        results = []
        now = time.time()

        for source in sources:
            # Check cache
            cache_entry = cache.get(source)
            if cache_entry and (now - cache_entry["cached_at"] < CACHE_TTL_SECONDS):
                print(f"💾 Served from memory cache for {source}")
                items = cache_entry["data"]
            else:
                print(f"📡 Querying DynamoDB for {source}")
                response = table.query(
                    KeyConditionExpression=Key('PK').eq(source),
                    ScanIndexForward=False,
                    Limit=limit,
                    ConsistentRead=False
                )
                items = response.get('Items', [])
                cache[source] = {
                    "data": items,
                    "cached_at": now
                }

            results.extend([clean_item(item) for item in items])

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': JSONEncoder().encode({
                "news": results
            })
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({"error": str(e)})
        }

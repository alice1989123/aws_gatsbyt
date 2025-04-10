import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from decimal import Decimal


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

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

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ["DYNAMO_TABLE_NAME"])

def lambda_handler(event, context):
    try:
        sources = event.get("sources", ["crypto.news"])  # Default to crypto.news if none given
        limit = event.get("limit", 10)

        results = []

        for source in sources:
            response = table.query(
                KeyConditionExpression=Key('PK').eq(source),
                ScanIndexForward=False,
                Limit=limit,
                ConsistentRead=False
            )
            items = response.get('Items', [])
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
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({"error": str(e)})
        }

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from botocore.exceptions import ClientError
from decimal import Decimal


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimals to float or str depending on use case
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
def clean_item(item):
    # Remove PK and format date
    if "PK" in item:
        del item["PK"]
    if "date" in item and "T" in item["date"]:
        # Convert ISO format to "YYYY-MM-DD HH:MM:SS"
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
        def get_latest(pk):
            response = table.query(
                KeyConditionExpression=Key('PK').eq(pk),
                ScanIndexForward=False,
                Limit=1,
                ConsistentRead=False
            )
            items = response.get('Items', [])
            return items[0] if items else {}

        latest_news = get_latest('news')
        latest_sentiment = get_latest('sentiment')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': JSONEncoder().encode({
                "news": clean_item(latest_news),
                "sentiment": clean_item(latest_sentiment)
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

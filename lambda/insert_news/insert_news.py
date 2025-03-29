import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
table_name = os.environ["DYNAMO_TABLE_NAME"]
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    news_list = event.get("news", [])

    for news_item in news_list:
        try:
            # Validate required keys
            required_keys = ["headline", "summary", "url", "timestamp", "source"]
            if not all(key in news_item for key in required_keys):
                print(f"❌ Skipping item, missing fields: {news_item}")
                continue

            item = {
                "PK": news_item["source"],
                "date": news_item["timestamp"],
                "headline": news_item["headline"],
                "summary": news_item["summary"],
                "url": news_item["url"]
            }

            table.put_item(Item=item)
            print(f"✅ Inserted: {item['headline']}")

        except Exception as e:
            print(f"❌ Error inserting news: {e}")

    return {
        "statusCode": 200,
        "body": "News items inserted successfully."
    }

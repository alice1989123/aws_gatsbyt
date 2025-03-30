import boto3
import os
import re
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
table_name = os.environ["DYNAMO_TABLE_NAME"]
table = dynamodb.Table(table_name)

def preprocess_content(content: str):
    """Extract headline, summary, and url from raw content string."""
    try:
        headline_match = re.search(r'- Headline:\s*(.+?)\n', content, re.DOTALL)
        summary_match = re.search(r'- Summary:\s*(.+?)\n', content, re.DOTALL)
        url_match = re.search(r'- URL:\s*(https?://\S+)', content)

        if not (headline_match and summary_match and url_match):
            raise ValueError("Missing one or more fields in content")

        return {
            "headline": headline_match.group(1).strip(),
            "summary": summary_match.group(1).strip(),
            "url": url_match.group(1).strip()
        }
    except Exception as e:
        print(f"❌ Error during preprocessing: {e}")
        return None

def lambda_handler(event, context):
    news_list = event.get("news", [])

    for news_item in news_list:
        try:
            content = news_item.get("content", "")
            timestamp = news_item.get("timestamp")

            if not content or not timestamp:
                print(f"❌ Skipping item, missing content or timestamp: {news_item}")
                continue

            processed = preprocess_content(content)
            if not processed:
                continue  # Skip if preprocessing failed

            item = {
                "PK": "crypto.news",
                "date": timestamp,
                "headline": processed["headline"],
                "summary": processed["summary"],
                "url": processed["url"]
            }

            table.put_item(Item=item)
            print(f"✅ Inserted: {item['headline']}")

        except Exception as e:
            print(f"❌ Error inserting news: {e}")

    return {
        "statusCode": 200,
        "body": "News items inserted successfully."
    }

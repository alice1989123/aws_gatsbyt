import boto3
import os
import re
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB resource and table object
dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
table_name = os.environ["DYNAMO_TABLE_NAME"]
table = dynamodb.Table(table_name)

def preprocess_content(content: dict) -> dict:
    """Extract headline, summary, and URL from raw content string."""
    
    def extract_headline(text: str) -> str:
        """
        Extracts the headline from the text.
        Expected format: "Headline: <headline text> - ..."
        """
        match = re.search(r"Headline:\s*(.+?)(?:\s*-\s*|$)", text, re.DOTALL)
        if not match:
            raise ValueError("Headline not found in text.")
        return match.group(1).strip()

    def extract_summary(text: str) -> str:
        """
        Extracts the summary from the text.
        Expected format: "... - Summary: <summary text> - URL: ..."
        The regex captures everything between 'Summary:' and ' - URL:'.
        """
        match = re.search(r"Summary:\s*(.+?)\s*-\s*URL:", text, re.DOTALL)
        if not match:
            raise ValueError("Summary not found in text.")
        return match.group(1).strip()

    def extract_url(text: str) -> str:
        """
        Extracts the URL from the text.
        Expected format: "... - URL: <url>"
        """
        match = re.search(r"URL:\s*(https?://\S+)", text)
        if not match:
            raise ValueError("URL not found in text.")
        return match.group(1).strip()

    print("Preprocess content input:", content)
    
    # Use the 'summary' field as the source text for extraction. Adjust if necessary.
    text = content.get("summary", "")
    
    try:
        headline_match = extract_headline(text)
    except Exception as e:
        print(f"❌ Error during headline parsing: {e}")
        headline_match = content.get("headline", "")
    
    try:
        summary_match = extract_summary(text)
    except Exception as e:
        print(f"❌ Error during summary parsing: {e}")
        summary_match = content.get("summary", "")
    
    try:
        url_match = extract_url(text)
    except Exception as e:
        print(f"❌ Error during URL extraction: {e}")
        url_match = content.get("url", "")
    
    print("Extracted values:", headline_match, summary_match, url_match)

    if not (headline_match and summary_match and url_match):
        raise ValueError("Missing one or more fields in content")

    return {
        "headline": headline_match,
        "summary": summary_match,
        "url": url_match
    }
    

def lambda_handler(event, context):
    news_list = event.get("Records", [])
    
    # Counter to add a minute for each news item
    minute_increment = 0

    for news_item in news_list:
        try:
            # The SQS message body is expected to be a JSON string.
            content = news_item.get("body", "")
            parsed_content = json.loads(content)  # Parse JSON string into a dictionary
            timestamp_str = parsed_content.get("timestamp")
            
            if not parsed_content or not timestamp_str:
                print(f"❌ Skipping item, missing content or timestamp: {news_item}")
                continue

            # Parse the original timestamp; adjust format if necessary.
            try:
                # Attempt to parse with microseconds
                base_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                # Fallback if no microseconds are present
                base_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
            
            # Add the minute increment to create a unique timestamp
            new_timestamp = base_timestamp + timedelta(minutes=minute_increment)
            minute_increment += 1  # Increment for the next item

            # Convert the new timestamp back to a string (ISO format)
            new_timestamp_str = new_timestamp.isoformat()
            
            processed = preprocess_content(parsed_content)
            if not processed:
                continue  # Skip if preprocessing failed

            item = {
                "PK": "crypto.news",  # Adjust partition key if needed
                "date": new_timestamp_str,
                "headline": processed["headline"],
                "summary": processed["summary"],
                "url": processed["url"]
            }

            table.put_item(Item=item)
            print(f"✅ Inserted: {item['headline']} with date {new_timestamp_str}")

        except Exception as e:
            print(f"❌ Error inserting news: {e}")

    return {
        "statusCode": 200,
        "body": "News items inserted successfully."
    }

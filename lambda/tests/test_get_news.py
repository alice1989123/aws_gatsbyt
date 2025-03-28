import boto3
import json

# ---- CONFIG ----
function_name = "crypto_news"  # Replace with your actual Lambda function name
region_name = "eu-central-1"   # Replace if using a different AWS region

# Optional: payload to send (if your Lambda accepts event params)
payload = {
    # "queryStringParameters": {
    #     "collection_name": "BTCUSDT"
    # }
}


# ---- INVOKE LAMBDA ----
client = boto3.client("lambda", region_name=region_name)

response = client.invoke(
    FunctionName=function_name,
    InvocationType="RequestResponse",  # synchronous
    Payload=json.dumps(payload)
)

# ---- PARSE RESULT ----
response_payload = response["Payload"].read().decode("utf-8")
print("🔁 Lambda Response:")
print(json.dumps(json.loads(response_payload), indent=2))

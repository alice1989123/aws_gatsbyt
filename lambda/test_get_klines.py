import boto3
import json

# Initialize Lambda client
client = boto3.client("lambda", region_name="eu-central-1")

# Prepare the payload
event = {
    "coin": "BTCUSDT",
    "start": "1731613408219",
    "end": "1731973408219"
}

# Invoke the Lambda function
response = client.invoke(
    FunctionName="arn:aws:lambda:eu-central-1:390402534126:function:BtcForecastAwsStack-BtcForecastFunction784E5E0A-vXSiLYA4HFVX",
    InvocationType="RequestResponse",  # Optional: For synchronous invocation
    Payload=json.dumps(event)          # Pass the payload here
)

# Print the response
print(json.loads(response["Payload"].read()))

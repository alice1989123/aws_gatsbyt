import boto3
import json
from datetime import datetime, timedelta

# ---- CONFIG ----
region_name = "eu-central-1"
# Replace this with your actual function name
lambda_function_name = "crypoNewsInsert"
client = boto3.client("lambda", region_name=region_name)


# Your sample payload
payload = {
    "news": [
        {
            "content": "- Headline: Trump pardons BitMEX founders, is ‘Bitcoin Jesus’ Roger Ver next?\n- Summary: President Donald Trump has pardoned the founders of BitMEX...\n- URL: https://crypto.news/trump-bitmex-founders-bitcoin-jesus-roger-ver-next/",
            "timestamp": "2025-03-29T22:27:40.869822"
        },
        {
            "content": "- Headline: NFT Sales Recover 4.5% to $102.8M, CryptoPunks Sales Surge 140%\n- Summary: The NFT market has shown resilience...\n- URL: https://crypto.news/nft-sales-recover-8m-cryptopunks-sales-surge-140/",
            "timestamp": "2025-03-29T22:27:52.424625"
        }
    ]
}

# Initialize the boto3 Lambda client
client = boto3.client('lambda', region_name='eu-central-1')

# Invoke the function
response = client.invoke(
    FunctionName=lambda_function_name,
    InvocationType='RequestResponse',  # You can also use 'Event' for async
    Payload=json.dumps(payload)
)

# Read and print the result
response_payload = response['Payload'].read().decode('utf-8')
print("🔁 Lambda response:")
print(response_payload)

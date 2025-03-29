import boto3
import json
from datetime import datetime, timedelta

# ---- CONFIG ----
function_name = "crypto_news"  # Replace if your function name is different
region_name = "eu-central-1"

# ---- TEST PAYLOAD ----
now = datetime.utcnow()

news_payload = {
    "news": [
        {
            "headline": "Bitcoin Hits New High",
            "summary": "Bitcoin price surged past $85,000 for the first time.",
            "url": "https://crypto.news/bitcoin-hits-new-high",
            "timestamp": (now).isoformat(),
            "source": "crypto.news"
        },
        {
            "headline": "Ethereum Gas Fees Drop",
            "summary": "Ethereum's gas fees are at their lowest in months.",
            "url": "https://crypto.news/ethereum-gas-fees-drop",
            "timestamp": (now + timedelta(seconds=5)).isoformat(),
            "source": "crypto.news"
        },
        {
            "headline": "Solana Network Upgrade",
            "summary": "Solana releases a major update improving TPS performance.",
            "url": "https://crypto.news/solana-network-upgrade",
            "timestamp": (now + timedelta(seconds=10)).isoformat(),
            "source": "crypto.news"
        }
    ]
}

# ---- INVOKE LAMBDA ----
client = boto3.client("lambda", region_name=region_name)

response = client.invoke(
    FunctionName=function_name,
    InvocationType="RequestResponse",
    Payload=json.dumps(news_payload)
)

# ---- PARSE RESPONSE ----
response_payload = response["Payload"].read().decode("utf-8")
print("🔁 Lambda Response:")
print(json.dumps(json.loads(response_payload), indent=2))

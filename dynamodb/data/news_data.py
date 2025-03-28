import boto3
from decimal import Decimal


dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
table = dynamodb.Table('crypto_data')
from decimal import Decimal

news_item = {
    "PK": "news",
    "date": "2023-07-02T20:30:39Z",
    "news": [
        {
            "summary": "Bitcoin has emerged as a gamechanger...",
            "source": "No specific sources mentioned",
            "sentiment": Decimal("0.6"),
            "entities": "Bitcoin, cryptocurrency",
            "image_description": "Bitcoin's impact on technology and finance"
        },
        {
            "summary": "Kraken, a cryptocurrency exchange, has been ordered by a court...",
            "source": "Multiple sources",
            "sentiment": Decimal("0.2"),
            "entities": "Kraken, Internal Revenue Service (IRS)",
            "image_description": "Kraken ordered to provide user data to IRS for tax compliance."
        }
    ]
}


# Item for PK='sentiment'
sentiment_item = {
    "PK": "sentiment",
    "date": "2023-07-02T20:30:39Z",
    "Algorand": 2,
    "Amp": 26,
    "ApeCoin": 10,
    "Arbitrum": 2,
    "BNB": 6,
    "Bancor": 1,
    "Bitcoin": 366,
    "Bitcoin Cash": 13,
    "Cardano": 6,
    "Chainlink": 1,
    "Compound": 28,
    "Cosmos": 2,
    "Cronos": 7,
    "Curve DAO Token": 2,
    "Dai": 10,
    "Decentraland": 3,
    "Dogecoin": 11,
    "Ethereum": 89,
    "Filecoin": 37,
    "Litecoin": 36,
    "Maker": 1,
    "NEAR Protocol": 5,
    "OKB": 2,
    "Polkadot": 1,
    "Polygon": 2,
    "Shiba Inu": 2,
    "Solana": 18,
    "Stellar": 3,
    "THETA": 4,
    "TRON": 7,
    "TerraUSD": 37,
    "Tether": 2,
    "Toncoin": 14,
    "Uniswap": 12,
    "VeChain": 1,
    "XRP": 10
}

# Upload the items
table.put_item(Item=news_item)
table.put_item(Item=sentiment_item)

print("✅ Sample data inserted into DynamoDB.")

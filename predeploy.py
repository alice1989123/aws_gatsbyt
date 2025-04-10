import boto3

dynamodb = boto3.client("dynamodb")

def table_exists(name):
    try:
        dynamodb.describe_table(TableName=name)
        return True
    except dynamodb.exceptions.ResourceNotFoundException:
        return False

if __name__ == "__main__":
    args = []
    if table_exists("crypto_news"):
        args.append("-c crypto_news_exists=true")
    if table_exists("crypto_predictions_"):
        args.append("-c crypto_predictions_exists=true")

    print(" ".join(args))

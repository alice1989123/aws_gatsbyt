import boto3

dynamodb = boto3.client("dynamodb")
rds = boto3.client("rds")

def table_exists(name):
    try:
        dynamodb.describe_table(TableName=name)
        return True
    except dynamodb.exceptions.ResourceNotFoundException:
        return False
def rds_instance_exists(identifier):
    try:
        response = rds.describe_db_instances(DBInstanceIdentifier=identifier)
        return len(response["DBInstances"]) > 0
    except rds.exceptions.DBInstanceNotFoundFault:
        return False

if __name__ == "__main__":
    args = []
    if table_exists("crypto_news"):
        args.append("-c crypto_news_exists=true")
    if table_exists("crypto_predictions_"):
        args.append("-c crypto_predictions_exists=true")
    if rds_instance_exists("crypto-postgres-db"):
        args.append("-c rds_exists=true")

    print(" ".join(args))

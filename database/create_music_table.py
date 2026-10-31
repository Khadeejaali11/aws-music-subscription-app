import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

try:
    table = dynamodb.create_table(
        TableName="music",

        KeySchema=[
            {"AttributeName": "title", "KeyType": "HASH"},
            {"AttributeName": "song_id", "KeyType": "RANGE"}
        ],

        AttributeDefinitions=[
            {"AttributeName": "title", "AttributeType": "S"},
            {"AttributeName": "song_id", "AttributeType": "S"},
            {"AttributeName": "artist", "AttributeType": "S"},
            {"AttributeName": "album", "AttributeType": "S"},
            {"AttributeName": "year", "AttributeType": "S"}
        ],

        LocalSecondaryIndexes=[
            {
                "IndexName": "title-year-index",
                "KeySchema": [
                    {"AttributeName": "title", "KeyType": "HASH"},
                    {"AttributeName": "year", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ],

        GlobalSecondaryIndexes=[
            {
                "IndexName": "artist-album-index",
                "KeySchema": [
                    {"AttributeName": "artist", "KeyType": "HASH"},
                    {"AttributeName": "album", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ],

        BillingMode="PAY_PER_REQUEST"
    )

    print("Creating music table...")
    table.wait_until_exists()
    print("music table created successfully")

except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print("music table already exists")
    else:
        raise
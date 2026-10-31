import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)

try:
    table = dynamodb.create_table(
        TableName="subscriptions",

        # Composite key
        KeySchema=[
            {
                "AttributeName": "email",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "song_id",
                "KeyType": "RANGE"
            }
        ],

        AttributeDefinitions=[
            {
                "AttributeName": "email",
                "AttributeType": "S"
            },
            {
                "AttributeName": "song_id",
                "AttributeType": "S"
            }
        ],

        BillingMode="PAY_PER_REQUEST"
    )

    print("Creating subscriptions table...")
    table.wait_until_exists()
    print("subscriptions table created successfully")

except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print("subscriptions table already exists")
    else:
        raise
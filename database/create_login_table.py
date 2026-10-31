import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)

try:
    table = dynamodb.create_table(
        TableName="login",

        # Primary key
        KeySchema=[
            {
                "AttributeName": "email",
                "KeyType": "HASH"
            }
        ],

        # Define data type of key
        AttributeDefinitions=[
            {
                "AttributeName": "email",
                "AttributeType": "S"
            }
        ],

        BillingMode="PAY_PER_REQUEST"
    )

    print("Creating login table...")
    table.wait_until_exists()
    print("Login table created successfully")

except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print("Login table already exists")
    else:
        raise
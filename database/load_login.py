import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table("login")

# Seed user details (test data only)
base_id = "testuser"
first_name = "Test"
last_name = "User"


# Password pattern: 012345 → 123456 → ...
def generate_password(start):
    digits = "0123456789"
    return "".join(digits[(start + i) % 10] for i in range(6))


# Insert 10 users
for i in range(10):
    email = f"{base_id}{i}@example.com"
    user_name = f"{first_name}{last_name}{i}"
    password = generate_password(i)

    try:
        table.put_item(
            Item={
                "email": email,
                "user_name": user_name,
                "password": password
            },
            ConditionExpression="attribute_not_exists(email)"
        )

        print(f"Inserted: {email} | {user_name}")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"Skipped (already exists): {email}")
        else:
            raise

print("\n✅ Login table population complete")
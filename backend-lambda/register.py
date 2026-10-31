"""
Lambda Function: User Registration
Author: Khadeeja Ali
Date: 03/05/2026
Citation: Based on AWS Lambda with DynamoDB documentation
Purpose: Register new users with unique email validation
"""

import json
import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
login_table = dynamodb.Table('login')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        email = body.get('email')
        username = body.get('username')
        password = body.get('password')

        # Validate required fields
        if not email or not username or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': 'Email, username, and password required'
                })
            }

        # Check if email already exists
        response = login_table.get_item(Key={'email': email})
        
        if 'Item' in response:
            return {
                'statusCode': 409,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': 'Email already exists'
                })
            }

        # Create new user
        login_table.put_item(Item={
            'email': email,
            'user_name': username,
            'password': password
        })

        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'User registered successfully'
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")  # CloudWatch logging
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error'
            })
        }
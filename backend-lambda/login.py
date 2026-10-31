"""
Lambda Function: User Authentication
Author: Khadeeja Ali
Date: 03/05/2026
Citation: Based on AWS Lambda with DynamoDB documentation
Purpose: Validate user credentials against login table
"""

import json
import boto3

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
        password = body.get('password')

        if not email or not password:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': 'Email and password required'
                })
            }

        # Query DynamoDB
        response = login_table.get_item(Key={'email': email})
        user = response.get('Item')

        if not user:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': 'User not found'
                })
            }

        if user['password'] != password:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': 'Incorrect password'
                })
            }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Login successful',
                'user_name': user['user_name']
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error'
            })
        }
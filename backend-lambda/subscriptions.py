"""
Lambda Function: Manage Subscriptions (Path Parameter Version)
Author: Khadeeja Ali
Date: 07/05/2026
Purpose: Retrieve user subscriptions using path parameter /subscriptions/{email}
"""

import json
import boto3
import urllib.parse

from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
subscriptions_table = dynamodb.Table('subscriptions')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    try:
        # Get the HTTP method
        method = event.get('httpMethod', 'GET')
        
        # GET method - Retrieve subscriptions
        if method == 'GET':
            # Get email from path parameter and decode it
            email = None
            if event.get('pathParameters'):
                email_raw = event['pathParameters'].get('email')
                if email_raw:
                    # Decode URL-encoded characters (like %40 back to @)
                    email = urllib.parse.unquote(email_raw)
            
            if not email and event.get('queryStringParameters'):
                email = event['queryStringParameters'].get('email')
            
            if not email:
                email = event.get('email')
            
            print(f"Looking for subscriptions for: '{email}'")
            
            if not email:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'message': 'Email required'})
                }
            
            # Query DynamoDB
            response = subscriptions_table.query(
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            items = response.get('Items', [])
            print(f"Found {len(items)} subscriptions for {email}")
            
            # Format the response (remove DynamoDB metadata)
            formatted_items = []
            for item in items:
                formatted_items.append({
                    'email': item.get('email'),
                    'song_id': item.get('song_id'),
                    'title': item.get('title'),
                    'artist': item.get('artist'),
                    'album': item.get('album'),
                    'year': item.get('year'),
                    'image_url': item.get('image_url')
                })
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'subscriptions': formatted_items})
            }
        
        # POST method - Add subscription
        elif method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            email = body.get('email')
            title = body.get('title')
            artist = body.get('artist')
            album = body.get('album')
            year = body.get('year')
            image_url = body.get('image_url')

            if not email or not title or not artist:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'message': 'Missing required fields'})
                }

            song_id = f"{title}#{artist}#{album}#{year}"

            print(f"Adding subscription: {email} -> {title} by {artist}")

            subscriptions_table.put_item(
                Item={
                    'email': email,
                    'song_id': song_id,
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'year': year,
                    'image_url': image_url
                }
            )

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True, 'message': 'Subscribed successfully'})
            }

        # DELETE method - Remove subscription
        elif method == 'DELETE':
            body = json.loads(event.get('body', '{}'))

            email = body.get('email')
            title = body.get('title')
            artist = body.get('artist')
            album = body.get('album')
            year = body.get('year')
            song_id = body.get('song_id')

            if not song_id and all([title, artist, album, year]):
                song_id = f"{title}#{artist}#{album}#{year}"

            if not email or not song_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'message': 'Missing email and song identification'})
                }

            subscriptions_table.delete_item(Key={'email': email, 'song_id': song_id})

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'Unsubscribed successfully'})
            }

        else:
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'message': f'Method {method} not supported'})
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'message': 'Error', 'details': str(e)})
        }
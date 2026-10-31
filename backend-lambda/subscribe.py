"""
Lambda Function: Add Subscription
Author: Khadeeja Ali
Date: 03/05/2026
Purpose: Add a song to user's subscription list in DynamoDB
"""

import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
subscriptions_table = dynamodb.Table('subscriptions')

def make_song_id(title, artist, album, year):
    return f"{title}#{artist}#{album}#{year}"

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        email = body.get('email')
        title = body.get('title')
        artist = body.get('artist')
        album = body.get('album')
        year = body.get('year')
        image_url = body.get('image_url')

        if not all([email, title, artist, album, year]):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Missing required fields'})
            }

        song_id = make_song_id(title, artist, album, year)

        subscriptions_table.put_item(Item={
            'email': email,
            'song_id': song_id,
            'title': title,
            'artist': artist,
            'album': album,
            'year': year,
            'image_url': image_url
        })

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'Subscribed successfully'})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'message': 'Error'})
        }
"""
Lambda Function: Music Search (Simplified Working Version)
Author: Khadeeja Ali
Date: 04/05/2026
Purpose: Search music with case-insensitive matching
"""

import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
music_table = dynamodb.Table('music')

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    try:
        # Get query parameters
        if 'queryStringParameters' in event and event['queryStringParameters']:
            params = event['queryStringParameters']
        else:
            params = event

        title = params.get('title', '').strip().lower()
        artist = params.get('artist', '').strip().lower()
        album = params.get('album', '').strip().lower()
        year = params.get('year', '').strip()

        print(f"Searching - Title:{title}, Artist:{artist}, Album:{album}, Year:{year}")

        # Scan all items from DynamoDB
        response = music_table.scan()
        all_songs = response.get('Items', [])
        
        print(f"Total songs in database: {len(all_songs)}")
        
        # Filter results
        results = []
        
        for song in all_songs:
            match = True
            
            # Case-insensitive matching
            if title and title not in song.get('title', '').lower():
                match = False
            if artist and artist not in song.get('artist', '').lower():
                match = False
            if album and album not in song.get('album', '').lower():
                match = False
            if year and song.get('year') != year:
                match = False
            
            if match:
                # Remove internal fields
                song_copy = {
                    'title': song.get('title', ''),
                    'artist': song.get('artist', ''),
                    'album': song.get('album', ''),
                    'year': song.get('year', ''),
                    'image_url': song.get('image_url', '')
                }
                results.append(song_copy)
        
        print(f"Found {len(results)} matching songs")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'results': results})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'results': [], 'error': str(e)})
        }
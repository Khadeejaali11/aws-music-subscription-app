import json
import boto3
import os
from botocore.exceptions import ClientError

REGION = "us-east-1"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(CURRENT_DIR, "2026a2_songs.json")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table("music")


def clean_key(value):
    return str(value).replace("#", "-").strip()


def make_song_id(song, row_number):
    artist = clean_key(song["artist"])
    album = clean_key(song["album"])
    year = clean_key(song["year"])
    return f"{artist}#{album}#{year}#{row_number}"


with open(JSON_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

songs = data["songs"]

inserted_count = 0
duplicate_count = 0

for index, song in enumerate(songs):
    song_id = make_song_id(song, index)

    item = {
        "title": str(song["title"]),
        "song_id": song_id,
        "artist": str(song["artist"]),
        "year": str(song["year"]),
        "album": str(song["album"]),
        "image_url": str(song["img_url"])
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(title) AND attribute_not_exists(song_id)"
        )

        inserted_count += 1
        print(f"Inserted {index}: {item['title']} - {item['artist']} - {item['album']} - {item['year']}")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            duplicate_count += 1
            print(f"Skipped duplicate: {item['title']} - {item['song_id']}")
        else:
            raise

print("\nLoad complete")
print("Inserted songs:", inserted_count)
print("Skipped duplicates:", duplicate_count)
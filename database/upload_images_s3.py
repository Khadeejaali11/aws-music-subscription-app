import json
import os
import boto3
import requests
from botocore.exceptions import ClientError

REGION = "us-east-1"
BUCKET_NAME = os.environ.get("MUSIC_IMAGES_BUCKET", "your-unique-bucket-name")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(CURRENT_DIR, "2026a2_songs.json")

s3 = boto3.client("s3", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
music_table = dynamodb.Table("music")


def clean_key(value):
    return str(value).replace("#", "-").strip()


def make_song_id(song, row_number):
    artist = clean_key(song["artist"])
    album = clean_key(song["album"])
    year = clean_key(song["year"])
    return f"{artist}#{album}#{year}#{row_number}"


def create_bucket():
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print("Bucket created:", BUCKET_NAME)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code in ["BucketAlreadyOwnedByYou", "BucketAlreadyExists"]:
            print("Bucket already exists:", BUCKET_NAME)
        else:
            raise


def make_bucket_public_read():
    s3.put_public_access_block(
        Bucket=BUCKET_NAME,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False
        }
    )

    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowPublicReadForArtistImages",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{BUCKET_NAME}/artist-images/*"
            }
        ]
    }

    s3.put_bucket_policy(
        Bucket=BUCKET_NAME,
        Policy=json.dumps(bucket_policy)
    )

    print("Public read policy added")


def clean_file_name(name):
    return (
        name.replace(" ", "_")
        .replace("/", "_")
        .replace("&", "and")
        .replace("'", "")
        .replace('"', "")
        .replace(".", "")
    )


def upload_images_and_update_table():
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    songs = data["songs"]

    downloaded_folder = os.path.join(CURRENT_DIR, "downloaded_images")
    os.makedirs(downloaded_folder, exist_ok=True)

    processed_artists = {}

    for index, song in enumerate(songs):
        title = song["title"]
        song_id = make_song_id(song, index)
        artist = song["artist"]
        original_img_url = song["img_url"]

        if artist in processed_artists:
            s3_image_url = processed_artists[artist]
        else:
            response = requests.get(original_img_url, timeout=20)

            if response.status_code != 200:
                print("Failed to download image:", artist)
                continue

            file_name = clean_file_name(artist) + ".jpg"
            local_file_path = os.path.join(downloaded_folder, file_name)

            with open(local_file_path, "wb") as image_file:
                image_file.write(response.content)

            s3_key = f"artist-images/{file_name}"

            s3.upload_file(
                local_file_path,
                BUCKET_NAME,
                s3_key,
                ExtraArgs={"ContentType": "image/jpeg"}
            )

            s3_image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
            processed_artists[artist] = s3_image_url

            print("Uploaded:", artist, "->", s3_image_url)

        music_table.update_item(
            Key={
                "title": title,
                "song_id": song_id
            },
            UpdateExpression="SET image_url = :url",
            ExpressionAttributeValues={
                ":url": s3_image_url
            }
        )

    print("All images uploaded and music table updated")


if __name__ == "__main__":
    create_bucket()
    make_bucket_public_read()
    upload_images_and_update_table()
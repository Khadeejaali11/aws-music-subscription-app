from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key, Attr

REGION = "us-east-1"

app = Flask(__name__)
CORS(app)

dynamodb = boto3.resource("dynamodb", region_name=REGION)

login_table = dynamodb.Table("login")
music_table = dynamodb.Table("music")
subscriptions_table = dynamodb.Table("subscriptions")


@app.route("/")
def home():
    return jsonify({"message": "Music subscription backend running"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    response = login_table.get_item(Key={"email": email})
    user = response.get("Item")

    if user and user.get("password") == password:
        return jsonify({
            "success": True,
            "user_name": user.get("user_name")
        })

    return jsonify({"success": False})


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    existing = login_table.get_item(Key={"email": email})

    if "Item" in existing:
        return jsonify({
            "success": False,
            "message": "The email already exists"
        })

    login_table.put_item(
        Item={
            "email": email,
            "user_name": username,
            "password": password
        }
    )

    return jsonify({"success": True})


@app.route("/music/search", methods=["GET"])
def music_search():
    title = request.args.get("title")
    artist = request.args.get("artist")
    album = request.args.get("album")
    year = request.args.get("year")

    results = []

    if artist and album:
        response = music_table.query(
            IndexName="artist-album-index",
            KeyConditionExpression=Key("artist").eq(artist) & Key("album").eq(album)
        )
        results = response.get("Items", [])

    elif artist:
        response = music_table.query(
            IndexName="artist-album-index",
            KeyConditionExpression=Key("artist").eq(artist)
        )
        results = response.get("Items", [])

    elif title:
     response = music_table.scan()
     results = response.get("Items", [])

    else:
        filter_expr = None

        if year:
            filter_expr = Attr("year").eq(year)

        if album:
            condition = Attr("album").contains(album)
            filter_expr = condition if filter_expr is None else filter_expr & condition

        response = music_table.scan(FilterExpression=filter_expr)
        results = response.get("Items", [])

    if title:
        results = [
            song for song in results
            if title.lower() in song.get("title", "").lower()
        ]

    if artist:
        results = [
            song for song in results
            if artist.lower() in song.get("artist", "").lower()
        ]

    if album:
        results = [
            song for song in results
            if album.lower() in song.get("album", "").lower()
        ]

    if year:
        results = [
            song for song in results
            if song.get("year") == year
        ]

    formatted_results = []

    for song in results:
        formatted_results.append({
            "title": song.get("title"),
            "artist": song.get("artist"),
            "album": song.get("album"),
            "year": song.get("year"),
            "image_url": song.get("image_url")
        })

    return jsonify({"results": formatted_results})


@app.route("/subscriptions/<path:email>", methods=["GET"])
def get_subscriptions(email):
    response = subscriptions_table.query(
        KeyConditionExpression=Key("email").eq(email)
    )

    subscriptions = []

    for song in response.get("Items", []):
        subscriptions.append({
            "title": song.get("title"),
            "artist": song.get("artist"),
            "album": song.get("album"),
            "year": song.get("year"),
            "image_url": song.get("image_url")
        })

    return jsonify({"subscriptions": subscriptions})


@app.route("/subscriptions", methods=["POST"])
def add_subscription():
    data = request.get_json()

    email = data.get("email")
    title = data.get("title")
    artist = data.get("artist")
    album = data.get("album")
    year = data.get("year")
    image_url = data.get("image_url")

    song_id = f"{title}#{artist}"

    subscriptions_table.put_item(
        Item={
            "email": email,
            "song_id": song_id,
            "title": title,
            "artist": artist,
            "album": album,
            "year": year,
            "image_url": image_url
        }
    )

    return jsonify({"success": True})


@app.route("/subscriptions", methods=["DELETE"])
def delete_subscription():
    data = request.get_json()

    email = data.get("email")
    title = data.get("title")
    artist = data.get("artist")

    song_id = f"{title}#{artist}"

    subscriptions_table.delete_item(
        Key={
            "email": email,
            "song_id": song_id
        }
    )

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
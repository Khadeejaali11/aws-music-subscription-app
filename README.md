# Music Subscription App (AWS)

A full-stack music subscription web app where users register, log in, search a song catalogue, and subscribe to songs to build a personal library. The same REST API is implemented **three ways on AWS** (serverless, VM, and container) so the architectures can be compared, and the frontend switches between them by changing a single line.

> University group project (RMIT). See [Credits](#credits).

## Architecture

```
                         +--> API Gateway + Lambda (serverless) --+
Static frontend  --------+--> Flask on EC2 (port 80)              +--> DynamoDB (login, music, subscriptions)
(HTML / CSS / JS)        +--> Flask in Docker on ECS Fargate (80) +
                                                                      S3 (artist images, public read)
```

| Backend | Folder | Notes |
|---|---|---|
| Lambda + API Gateway | `backend-lambda/` | One function per concern: login, register, songs (search), subscribe, subscriptions |
| Flask on EC2 | `backend-ec2-flask/` | Single `app.py`, listens on port 80 |
| Flask on ECS Fargate | `backend-ecs/` | Dockerfile (gunicorn), task definition, and `deploy.sh` that builds, pushes to ECR, and creates the cluster, security group and service |

The frontend picks a backend through `BACKEND_URL` in `frontend/config.js`.

## Features

- Register and log in (session kept in `sessionStorage`)
- Search songs by title, artist, album and year (case-insensitive, partial match)
- Subscribe to and remove songs from a personal library
- Artist images served from S3

## Data model (DynamoDB)

| Table | Key | Indexes |
|---|---|---|
| `login` | `email` (partition) | none |
| `music` | `title` (partition), `song_id` (sort) | LSI `title-year-index` (title, year); GSI `artist-album-index` (artist, album) |
| `subscriptions` | `email` (partition), `song_id` (sort) | none |

The EC2/ECS backends use the `artist-album-index` GSI when searching by artist; other searches fall back to a scan with in-memory filtering.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/login` | Check credentials |
| POST | `/register` | Create a user (rejects duplicate email) |
| GET | `/music/search?title=&artist=&album=&year=` | Search songs |
| GET | `/subscriptions/{email}` | List a user's subscriptions |
| POST | `/subscriptions` | Subscribe to a song |
| DELETE | `/subscriptions` | Remove a subscription |

For the Lambda version, these routes are wired up in API Gateway (the API Gateway configuration is not included in this repository).

## Repository layout

```
frontend/          Static site: login, register, main dashboard
backend-lambda/    Lambda handlers
backend-ec2-flask/ Flask app for EC2
backend-ecs/       Flask app, Dockerfile, ECS task definition, deploy script
database/          Table creation, seed data loading, S3 image upload
```

## Running it yourself

**Prerequisites:** an AWS account (or AWS Academy lab), AWS CLI configured for `us-east-1`, Python 3.11, and Docker (ECS option only).

1. **Create the tables**
   ```bash
   pip install boto3 requests
   python database/create_login_table.py
   python database/create_music_table.py
   python database/create_subscription_table.py
   ```
2. **Load songs.** The song dataset is not included in this repository. Provide `database/2026a2_songs.json` as `{"songs": [{"title", "artist", "year", "album", "img_url"}, ...]}`, then:
   ```bash
   python database/load_songs.py
   ```
3. **(Optional) Upload artist images to S3**
   ```bash
   export MUSIC_IMAGES_BUCKET=your-unique-bucket-name
   python database/upload_images_s3.py
   ```
   This script makes the `artist-images/` prefix publicly readable.
4. **(Optional) Seed test users:** `python database/load_login.py` (creates `testuser0..9@example.com`).
5. **Deploy one backend**
   - **Lambda:** create one function per file in `backend-lambda/` (handler `<file>.lambda_handler`, Python 3.x) with a role that can access DynamoDB, then expose them through API Gateway using the routes above.
   - **EC2:** `pip install -r backend-ec2-flask/requirements.txt && python backend-ec2-flask/app.py` on an instance with a DynamoDB-enabled role and port 80 open.
   - **ECS:** `cd backend-ecs && ./deploy.sh` (needs Docker and AWS CLI; prints the task's public IP when done).
6. **Point the frontend at it:** edit `BACKEND_URL` in `frontend/config.js`, then open `frontend/login.html` or host the `frontend/` folder on any static host (for example S3).

`backend-ecs/task-definition.json` uses `ACCOUNT_ID` as a placeholder (filled in by `deploy.sh`) and the `LabRole` IAM role from AWS Academy. If you are not using AWS Academy, replace `LabRole` with your own task and execution roles.

## Known limitations

This was built as a coursework prototype, not for production:

- **Passwords are stored and compared in plain text** in DynamoDB. Do not reuse real passwords. A production version would hash with a slow salted algorithm (for example bcrypt or scrypt).
- CORS is open to all origins (`*`) and there are no session tokens or authorisation checks on the API.
- The Lambda search function scans the whole `music` table instead of using the indexes.
- The ECS backend builds subscription IDs as `title#artist`, whereas the EC2 and Lambda backends use `title#artist#album#year`, so subscriptions are not interchangeable between backends.
- The S3 image bucket is configured for public read.
- No automated tests.

## Credits

Group project built at RMIT University by Khadeeja Ali and three teammates.

**My contribution (Khadeeja Ali):** the Lambda backend (login, register, search, subscribe and subscriptions handlers).

The song dataset and artist images were provided by the course and are not included here.

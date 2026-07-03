"""
Upload a video to YouTube via the Data API v3.
Handles OAuth token refresh automatically.
"""
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from config import YT_CLIENT_SECRET_FILE, YT_TOKEN_FILE, YT_SCOPES


def _get_credentials() -> Credentials:
    creds = None
    if YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), YT_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not YT_CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"YouTube client secret not found at {YT_CLIENT_SECRET_FILE}\n"
                    "Run: python3 setup_oauth.py"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(YT_CLIENT_SECRET_FILE), YT_SCOPES
            )
            creds = flow.run_local_server(port=0)

        YT_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        YT_TOKEN_FILE.write_text(creds.to_json())

    return creds


def upload_video(video_path: Path, script: dict) -> str:
    """Upload video and return the YouTube video ID."""
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    title = script.get("title", "Did You Know? 🤯 #Shorts")[:100]
    description = script.get("description", "") + "\n\n" + " ".join(script.get("hashtags", []))
    tags = [h.lstrip("#") for h in script.get("hashtags", [])]

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",       # People & Blogs
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=4 * 1024 * 1024,   # 4 MB chunks
    )

    print(f"⬆️  Uploading: {title}")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"   {pct}% uploaded...", end="\r")

    video_id = response["id"]
    print(f"\n✅ Published: https://www.youtube.com/shorts/{video_id}")
    return video_id

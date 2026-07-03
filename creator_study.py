"""
CreatorStudy loop (daily): find real top-performing competitor Shorts in our niche,
have Claude extract their techniques, and grow the competitor playbook.
Uses YouTube Data API search (100 quota units/run — cheap).
"""
import json
from datetime import date
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from claude_cli import ask
from config import YT_TOKEN_FILE, YT_SCOPES, CHANNEL_NICHE, DATA_DIR

PLAYBOOK = DATA_DIR / "competitor_playbook.md"
STUDIED  = DATA_DIR / "studied_videos.md"


def _yt():
    creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), YT_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def _already_studied() -> set:
    if not STUDIED.exists():
        return set()
    return {l.split()[0] for l in STUDIED.read_text().splitlines() if l.strip()}


def find_top_shorts(query: str, n: int = 10) -> list[dict]:
    yt = _yt()
    resp = yt.search().list(
        part="snippet", q=query, type="video", videoDuration="short",
        order="viewCount", maxResults=n, relevanceLanguage="en",
    ).execute()

    ids = [item["id"]["videoId"] for item in resp["items"]]
    stats = yt.videos().list(part="statistics,snippet", id=",".join(ids)).execute()

    videos = []
    for v in stats["items"]:
        videos.append({
            "id": v["id"],
            "title": v["snippet"]["title"],
            "channel": v["snippet"]["channelTitle"],
            "description": v["snippet"].get("description", "")[:300],
            "views": int(v["statistics"].get("viewCount", 0)),
            "likes": int(v["statistics"].get("likeCount", 0)),
            "comments": int(v["statistics"].get("commentCount", 0)),
            "url": f"https://www.youtube.com/shorts/{v['id']}",
        })
    videos.sort(key=lambda v: v["views"], reverse=True)
    return videos


def study():
    print(f"🔎 Finding top competitor Shorts: '{CHANNEL_NICHE}'...")
    studied = _already_studied()
    videos = find_top_shorts(f"{CHANNEL_NICHE} shorts", n=10)
    fresh = [v for v in videos if v["id"] not in studied][:5]

    if not fresh:
        print("Nothing new to study today.")
        return

    for v in fresh:
        print(f"   {v['views']:>12,} views — {v['title'][:60]}")

    videos_json = json.dumps(fresh, indent=2)
    playbook_current = PLAYBOOK.read_text()[-4000:] if PLAYBOOK.exists() else "(empty)"

    prompt = f"""You are a YouTube Shorts technique analyst for a "{CHANNEL_NICHE}" channel.

Study these REAL top-performing competitor Shorts (by actual view count):
{videos_json}

Current playbook (last section, avoid repeating):
{playbook_current}

For each video, extract from its title/description/engagement ratio:
1. The HOOK pattern (what makes someone stop scrolling)
2. Title formula (be specific: structure, word choice, numbers/emoji use)
3. The engagement driver (like/view and comment/view ratios reveal what makes people act)
4. One technique WE should adopt this week

End with a "## Techniques to adopt — {date.today()}" section: max 3 concrete, testable
techniques ranked by expected impact. Output markdown only."""

    print("🧠 Analyzing techniques...")
    analysis = ask(prompt)

    with open(PLAYBOOK, "a") as f:
        f.write(f"\n\n---\n# Study run {date.today()}\n\n{analysis}\n")
    with open(STUDIED, "a") as f:
        for v in fresh:
            f.write(f"{v['id']} {v['views']} {v['title'][:80]}\n")

    print(f"✅ Playbook updated: {PLAYBOOK}")


if __name__ == "__main__":
    study()

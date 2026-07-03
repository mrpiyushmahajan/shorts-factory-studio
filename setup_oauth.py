"""
One-time YouTube OAuth setup — run once per channel.
Usage:
  python setup_oauth.py --channel did_you_know
  python setup_oauth.py --channel desi_memes
"""
import argparse
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from config import get_channel, YT_SCOPES

parser = argparse.ArgumentParser()
parser.add_argument("--channel", default="did_you_know",
                    choices=["did_you_know", "desi_memes"])
args = parser.parse_args()

channel = get_channel(args.channel)
SECRET_FILE = channel["secret_file"]
TOKEN_FILE  = channel["token_file"]


def main():
    print("=" * 60)
    print(f"YouTube OAuth Setup — {args.channel}")
    print("=" * 60)

    if not SECRET_FILE.exists():
        print(f"""
❌  Client secret not found at:
    {SECRET_FILE}

Steps:
  1. Go to https://console.cloud.google.com/
  2. Enable YouTube Data API v3 + YouTube Analytics API
  3. APIs & Services → Credentials → Create OAuth 2.0 Client ID → Desktop app
  4. Download JSON → save it here:
     {SECRET_FILE}
  5. Run this script again.
""")
        return

    print(f"\n✅ Found: {SECRET_FILE}")
    print(f"🌐 Opening browser — select the '{args.channel}' YouTube channel...\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_FILE), YT_SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())
    print(f"\n✅ Token saved: {TOKEN_FILE}")
    print(f"\n🎉 Done! Test with:")
    print(f"   venv\\Scripts\\python daily_shorts.py --channel {args.channel}")


if __name__ == "__main__":
    main()

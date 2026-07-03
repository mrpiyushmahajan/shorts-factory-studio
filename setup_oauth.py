"""
One-time setup: authenticate with YouTube and save the refresh token.
Run this once before the pipeline will work: python3 setup_oauth.py
"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from config import YT_CLIENT_SECRET_FILE, YT_TOKEN_FILE, YT_SCOPES


def main():
    print("=" * 60)
    print("YouTube OAuth Setup")
    print("=" * 60)

    if not YT_CLIENT_SECRET_FILE.exists():
        print(f"""
❌  Client secret not found at:
    {YT_CLIENT_SECRET_FILE}

To get it:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or select existing)
  3. Enable "YouTube Data API v3" and "YouTube Analytics API"
  4. Go to APIs & Services → Credentials
  5. Create OAuth 2.0 Client ID → Desktop app
  6. Download JSON → save it to:
     {YT_CLIENT_SECRET_FILE}
  7. Run this script again.
""")
        return

    print(f"\n✅ Found client secret: {YT_CLIENT_SECRET_FILE}")
    print("\n🌐 Opening browser for YouTube authorization...")
    print("   (Grant access to your YouTube channel)\n")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(YT_CLIENT_SECRET_FILE), YT_SCOPES
    )
    creds = flow.run_local_server(port=0)

    YT_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    YT_TOKEN_FILE.write_text(creds.to_json())
    print(f"\n✅ Token saved: {YT_TOKEN_FILE}")
    print("\n🎉 YouTube auth complete! You can now run the pipeline:")
    print("   python3 daily_shorts.py")


if __name__ == "__main__":
    main()

"""
Download trending Indian meme sounds from myinstants.com into assets/sounds/.
Run occasionally to refresh the library:  python3 meme_sounds.py [pages]

Note: these are user-uploaded meme soundbites — fine for meme-format content,
but review anything you're unsure about before publishing.
"""
import re
import sys
import time
from pathlib import Path

import requests

from config import SOUNDS_DIR

BASE = "https://www.myinstants.com"
INDEX = BASE + "/en/index/in/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def scrape_page(page: int) -> list[tuple[str, str]]:
    """Return (name, mp3_url) pairs from one index page."""
    url = INDEX if page == 1 else f"{INDEX}?page={page}"
    html = requests.get(url, headers=HEADERS, timeout=30).text
    # buttons look like: onclick="play('/media/sounds/xxx.mp3', ...)"  + nearby title
    sounds = []
    for m in re.finditer(r"play\('(/media/sounds/[^']+\.mp3)'", html):
        path = m.group(1)
        name = Path(path).stem
        sounds.append((name, BASE + path))
    # de-dupe preserving order
    seen, out = set(), []
    for name, u in sounds:
        if u not in seen:
            seen.add(u)
            out.append((name, u))
    return out


def download_all(pages: int = 3):
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for page in range(1, pages + 1):
        try:
            sounds = scrape_page(page)
        except Exception as e:
            print(f"page {page} failed: {e}")
            continue
        print(f"page {page}: {len(sounds)} sounds")
        for name, url in sounds:
            safe = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:60]
            out = SOUNDS_DIR / f"{safe}.mp3"
            if out.exists():
                continue
            try:
                r = requests.get(url, headers=HEADERS, timeout=30)
                r.raise_for_status()
                out.write_bytes(r.content)
                total += 1
                print(f"   ↓ {safe}.mp3")
                time.sleep(0.5)   # be polite
            except Exception as e:
                print(f"   ✗ {name}: {e}")
    print(f"\n✅ {total} new sounds → {SOUNDS_DIR} ({len(list(SOUNDS_DIR.glob('*.mp3')))} total)")


if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    download_all(pages)

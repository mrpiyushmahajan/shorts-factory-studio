"""
Weekly learning loop: reads real analytics + rewrites the producer's learned rules.
Runs once a week (Sunday) via launchd.
"""
import json
import re
from datetime import date
from pathlib import Path

from claude_cli import ask
from config import DATA_DIR
from analytics import get_analytics_report

LEARNINGS_FILE = DATA_DIR / "learnings.md"
PLAYBOOK_FILE  = DATA_DIR / "competitor_playbook.md"


def _load_current_learnings() -> str:
    if LEARNINGS_FILE.exists():
        return LEARNINGS_FILE.read_text()
    return "(No learnings yet — this is the first run.)"


def run_learning_loop():
    print("📊 Fetching analytics...")
    try:
        report = get_analytics_report(days=28)
    except Exception as e:
        print(f"⚠️  Analytics unavailable: {e}")
        report = {"channel": {}, "videos": [], "period_days": 28}

    current_learnings = _load_current_learnings()
    report_json = json.dumps(report, indent=2)

    prompt = f"""You are a YouTube Shorts growth analyst for a "Did You Know?" facts channel.

## Current analytics (last 28 days)
{report_json}

## Current learned rules
{current_learnings}

## Your task
1. Identify what's working and what isn't from the data.
2. Propose SPECIFIC rule updates — not vague advice.
   - Rules must be actionable: "Use X instead of Y because Z"
   - Keep rules that are working
   - Remove or update rules that the data contradicts
3. Output an updated "## Learned Rules" section only.

Format as markdown. Be concrete. Today's date: {date.today()}"""

    print("🧠 Running learning analysis...")
    new_rules = ask(prompt)

    # Append to learnings log
    entry = f"\n\n---\n## Update: {date.today()}\n\n{new_rules}\n"
    with open(LEARNINGS_FILE, "a") as f:
        f.write(entry)

    print(f"✅ Learnings updated: {LEARNINGS_FILE}")
    return new_rules


if __name__ == "__main__":
    run_learning_loop()

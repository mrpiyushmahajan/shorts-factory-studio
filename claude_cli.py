"""
Thin wrapper around the Claude Code CLI for headless use.
Uses your Claude subscription — no API key or extra cost.
"""
import json
import re
import subprocess
from pathlib import Path


def ask(prompt: str, max_tokens: int = 4000) -> str:
    """Send a prompt to Claude via CLI and return the text response."""
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
    return result.stdout.strip()


def ask_json(prompt: str):
    """Ask Claude for a JSON response and parse it."""
    raw = ask(prompt)
    # strip markdown fences if present
    raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)

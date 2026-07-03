"""
ShortsDigest loop (daily): email a summary of what shipped + how it's performing.
Uses Gmail SMTP with an app password (set NOTIFY_EMAIL + GMAIL_APP_PASSWORD in .env).
"""
import smtplib
import ssl
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from config import NOTIFY_EMAIL, GMAIL_APP_PASSWORD, DATA_DIR, LOGS_DIR


def _recent_ledger_entries(hours: int = 26) -> list[str]:
    ledger = DATA_DIR / "posts_ledger.md"
    if not ledger.exists():
        return []
    cutoff = datetime.now() - timedelta(hours=hours)
    entries, current, keep = [], [], False
    for line in ledger.read_text().splitlines():
        if line.startswith("## Video — "):
            if current and keep:
                entries.append("\n".join(current))
            current, keep = [line], False
            try:
                ts = datetime.strptime(line.replace("## Video — ", "").strip(), "%Y-%m-%d %H:%M")
                keep = ts >= cutoff
            except ValueError:
                pass
        elif current:
            current.append(line)
    if current and keep:
        entries.append("\n".join(current))
    return entries


def _recent_failures() -> list[str]:
    fails = []
    if LOGS_DIR.exists():
        cutoff = datetime.now() - timedelta(hours=26)
        for f in LOGS_DIR.glob("*.log"):
            if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff:
                text = f.read_text()
                if text.startswith("FAILURE"):
                    fails.append(f"{f.stem}: {text[:300]}")
    return fails


def _channel_stats_block() -> str:
    try:
        from analytics import get_channel_stats
        s = get_channel_stats()
        return (f"<p><b>{s['name']}</b> — {s['subscribers']} subs · "
                f"{s['total_views']:,} total views · {s['video_count']} videos</p>")
    except Exception as e:
        return f"<p>(analytics unavailable: {e})</p>"


def build_digest() -> str:
    entries = _recent_ledger_entries()
    failures = _recent_failures()

    shipped = ""
    for e in entries:
        shipped += f"<pre style='background:#f4f4f4;padding:10px;border-radius:6px'>{e}</pre>"
    if not shipped:
        shipped = "<p>⚠️ Nothing shipped in the last 26 hours.</p>"

    fail_html = ""
    if failures:
        fail_html = "<h3 style='color:#c00'>❌ Failures</h3>" + "".join(
            f"<pre style='background:#fee;padding:10px'>{f}</pre>" for f in failures
        )

    return f"""<html><body style="font-family:Arial,sans-serif;max-width:640px">
<h2>🎬 Shorts Factory digest — {date.today()}</h2>
{_channel_stats_block()}
<h3>Shipped (last 26h): {len(entries)}</h3>
{shipped}
{fail_html}
<p style="color:#888;font-size:12px">Sent automatically by shorts-factory</p>
</body></html>"""


def send_digest():
    if not NOTIFY_EMAIL or not GMAIL_APP_PASSWORD:
        print("⚠️ NOTIFY_EMAIL / GMAIL_APP_PASSWORD not set in .env — printing digest instead\n")
        print(build_digest())
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎬 Shorts digest {date.today()}"
    msg["From"] = NOTIFY_EMAIL
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(build_digest(), "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(NOTIFY_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(NOTIFY_EMAIL, NOTIFY_EMAIL, msg.as_string())
    print(f"✅ Digest sent to {NOTIFY_EMAIL}")


if __name__ == "__main__":
    send_digest()

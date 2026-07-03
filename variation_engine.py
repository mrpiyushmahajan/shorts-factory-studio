"""
Anti-repetition engine — reads the variation library from the cloned reference repo
and ensures each video differs from the last 6 on title shape, skin, and voice.
"""
from pathlib import Path
from datetime import datetime

VARIATION_DIR = Path(__file__).parent / "variation"
LEDGER_FILE   = Path(__file__).parent / "data" / "variation_ledger.md"

# ── Ledger ────────────────────────────────────────────────────────────────────

def _read_ledger() -> list[dict]:
    if not LEDGER_FILE.exists():
        return []
    entries = []
    current = {}
    for line in LEDGER_FILE.read_text().splitlines():
        if line.startswith("## "):
            if current:
                entries.append(current)
            current = {"date": line[3:].strip()}
        elif line.startswith("- "):
            k, _, v = line[2:].partition(": ")
            current[k.strip()] = v.strip()
    if current:
        entries.append(current)
    return entries


def _recent_values(key: str, n: int = 6) -> list[str]:
    return [e[key] for e in _read_ledger()[-n:] if key in e]


def record_variation(title_shape_id: str, skin_id: str, voice: str):
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"- title_shape: {title_shape_id}\n"
        f"- skin: {skin_id}\n"
        f"- voice: {voice}\n"
    )
    with open(LEDGER_FILE, "a") as f:
        f.write(entry)


# ── Title shapes ──────────────────────────────────────────────────────────────

def _load_title_shapes() -> list[dict]:
    """Parse title_shapes.md into list of {id, type, shape, example}."""
    f = VARIATION_DIR / "title_shapes.md"
    if not f.exists():
        return []
    shapes = []
    for line in f.read_text().splitlines():
        if line.startswith("| T") and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                shapes.append({
                    "id": parts[0],
                    "type": parts[1],
                    "shape": parts[2],
                    "example": parts[3] if len(parts) > 3 else "",
                })
    return shapes


def pick_title_shape() -> dict:
    shapes = _load_title_shapes()
    recent = _recent_values("title_shape", n=6)
    available = [s for s in shapes if s["id"] not in recent]
    if not available:
        available = shapes  # all used — reset
    return available[0]   # first available (sorted by id)


# ── Visual skins ──────────────────────────────────────────────────────────────

def _load_skins() -> list[dict]:
    f = VARIATION_DIR / "visual_skins.md"
    if not f.exists():
        return []
    skins = []
    for line in f.read_text().splitlines():
        if line.startswith("| S") and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                # extract bg color hint from description
                bg = "#0D0D0D"
                accent = "#FFD700"
                desc = " ".join(parts[1:])
                import re
                colors = re.findall(r"#[0-9A-Fa-f]{6}", desc)
                if len(colors) >= 2:
                    bg, accent = colors[0], colors[1]
                elif len(colors) == 1:
                    bg = colors[0]
                skins.append({"id": parts[0], "name": parts[1], "bg": bg, "accent": accent, "text": "#FFFFFF"})
    return skins


def pick_skin() -> dict:
    skins = _load_skins()
    recent = _recent_values("skin", n=4)
    available = [s for s in skins if s["id"] not in recent]
    if not available:
        available = skins
    return available[0]


# ── Voices ────────────────────────────────────────────────────────────────────

def _load_voices() -> list[str]:
    f = VARIATION_DIR / "voices.md"
    if not f.exists():
        from config import VOICES
        return VOICES
    voices = []
    for line in f.read_text().splitlines():
        # lines like: en-US-AndrewNeural  or  | en-US-Andrew ...
        import re
        m = re.search(r"([a-z]{2,3}-[A-Z]{2}-\w+Neural)", line)
        if m:
            voices.append(m.group(1))
    return voices if voices else ["en-US-AndrewNeural", "en-US-JennyNeural"]


def pick_voice() -> str:
    voices = _load_voices()
    recent = _recent_values("voice", n=len(voices) - 1)
    available = [v for v in voices if v not in recent]
    return available[0] if available else voices[0]


# ── Full variation pick ───────────────────────────────────────────────────────

def pick_variation() -> dict:
    """Returns {title_shape, skin, voice} — all guaranteed non-repetitive."""
    return {
        "title_shape": pick_title_shape(),
        "skin": pick_skin(),
        "voice": pick_voice(),
    }


if __name__ == "__main__":
    v = pick_variation()
    print(f"Title shape: {v['title_shape']['id']} — {v['title_shape']['shape']}")
    print(f"Skin: {v['skin']['id']} — {v['skin']['name']}")
    print(f"Voice: {v['voice']}")

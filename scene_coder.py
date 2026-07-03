"""
The repo's real edge, ported: Claude writes a BESPOKE animated Remotion layer
for each video — topic-specific SVG hero elements, counters, arrows, diagrams —
composited over the AI image backdrops.

Safety: the generated file is bundle-checked with esbuild before render.
If it fails, the safe stub is restored and the video still renders.
"""
import shutil
import subprocess
from pathlib import Path

from claude_cli import ask

REMOTION_SRC = Path(__file__).parent / "remotion" / "src"
BESPOKE_FILE = REMOTION_SRC / "Bespoke.tsx"
STUB_FILE    = REMOTION_SRC / "Bespoke.stub.tsx"
ESBUILD      = Path(__file__).parent / "remotion" / "node_modules" / ".bin" / "esbuild"


PROMPT_TEMPLATE = """You are an expert Remotion motion-designer. Write a bespoke animated overlay
layer for a YouTube Short about: "{topic}"

The video already has: photoreal AI image backdrops with Ken Burns motion, karaoke
captions at the bottom, a badge at top, progress bar. YOUR job is the topic-specific
animated HERO layer between them — the thing that makes this video look hand-crafted.

Segments (each is a Remotion <Sequence>, durations in seconds):
{segments_desc}

Skin: background {bg}, accent {accent}.

Requirements:
- Output ONE complete TSX file, nothing else. No markdown fences, no explanation.
- It must compile standalone. Imports allowed: react, remotion ONLY.
- Must default-export: `BespokeOverlay: React.FC<{{segments: Segment[]; skin: {{bg: string; accent: string}}}}>`
- Define locally: `type Segment = {{displayText: string; durationS: number; imagePath: string | null}}`
- Use useVideoConfig() fps and segments[i].durationS to compute per-segment frame ranges;
  wrap each segment's visuals in <Sequence from={{...}} durationInFrames={{...}}>.
- For EACH segment draw 1-2 topic-specific animated SVG elements — and make them BOLD:
  huge animated counters (200px+ digits counting up), pulsing glowing shapes, motion
  streaks, exploding particle bursts on reveals, arrows that draw themselves, size
  comparisons that slam in with spring overshoot. Subtle = invisible = scrolled past.
- Give the biggest visual moment to the REVEAL segment (usually segment 1 or 2):
  e.g. a number that counts up with a glow burst when it lands.
- Position visuals in the MIDDLE band of the 1080x1920 frame (y between 350 and 1250).
  NEVER draw in the bottom 550px (captions live there) or top 250px (badge).
- Semi-transparent / glowing elements that complement the photo backdrop, not cover it.
  Use the accent color {accent} prominently.
- Keep it under 250 lines. No external assets, no images, no staticFile.

Write the file now. Your ENTIRE response must be raw TSX starting with `import` —
no prose, no markdown, no explanation before or after."""


def _segments_desc(script: dict) -> str:
    return "\n".join(
        f"  {i}: \"{s['text']}\" ({s.get('duration_s', 3)}s)"
        for i, s in enumerate(script["segments"])
    )


def _bundle_check() -> bool:
    """Verify the generated file bundles cleanly."""
    result = subprocess.run(
        [str(ESBUILD), str(BESPOKE_FILE), "--bundle",
         "--external:react", "--external:remotion", "--external:react/jsx-runtime",
         "--loader:.tsx=tsx", "--outfile=/dev/null"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"   bundle check failed:\n{result.stderr[-800:]}")
    return result.returncode == 0


def restore_stub():
    shutil.copy(STUB_FILE, BESPOKE_FILE)


def generate_bespoke_scene(script: dict, skin: dict) -> bool:
    """
    Have Claude write the bespoke overlay. Returns True if a valid custom
    scene is in place, False if we fell back to the stub.
    """
    prompt = PROMPT_TEMPLATE.format(
        topic=script.get("topic", "amazing facts"),
        segments_desc=_segments_desc(script),
        bg=skin.get("bg", "#0b1220"),
        accent=skin.get("accent", "#FFD23F"),
    )

    for attempt in range(2):
        print(f"🎭 Claude coding bespoke scene (attempt {attempt + 1})...")
        try:
            code = ask(prompt)
        except Exception as e:
            print(f"   claude failed: {e}")
            continue

        # strip accidental markdown fences
        code = code.strip()
        if code.startswith("```"):
            code = code.split("\n", 1)[1]
            code = code.rsplit("```", 1)[0]

        BESPOKE_FILE.write_text(code)
        if _bundle_check():
            print("   ✅ bespoke scene compiled")
            return True
        prompt += "\n\nYour previous attempt failed to compile. Fix all errors. Output ONLY the TSX file."

    print("   ⚠️ falling back to stub overlay")
    restore_stub()
    return False


if __name__ == "__main__":
    sample = {
        "topic": "Octopuses have three hearts",
        "segments": [
            {"text": "An octopus has three hearts.", "duration_s": 4},
            {"text": "One stops beating when it swims.", "duration_s": 4},
            {"text": "That's why they prefer to crawl.", "duration_s": 4},
        ],
    }
    skin = {"bg": "#0b1220", "accent": "#FFD23F"}
    ok = generate_bespoke_scene(sample, skin)
    print("bespoke:", ok)

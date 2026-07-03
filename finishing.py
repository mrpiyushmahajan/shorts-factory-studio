"""
Finishing layer — NVENC GPU encode, meme sounds, recut, music bed.
"""
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).parent
SFX_DIR    = ROOT / "assets" / "sfx"
MUSIC_DIR  = ROOT / "assets" / "music"

CUE_MATCH = {
    "vine-boom": ["vine-boom"],
    "aayein":    ["aayein"],
    "dramatic":  ["dun-dun-dun", "dramatic"],
    "slap":      ["slap", "punch"],
    "laugh":     ["laugh", "baby-laughing"],
    "cricket":   ["cricket"],
    "run":       ["run-vine"],
    "wow":       ["anime-wow", "shocked"],
    "fail":      ["spongebob-fail", "fail", "error"],
}


def _find_sound(sounds_dir: Path, cue: str):
    for sub in CUE_MATCH.get(cue, [cue]):
        hits = [p for p in sounds_dir.glob("*.mp3") if sub in p.name]
        if hits:
            return random.choice(hits)
    return None


def add_meme_sounds(video_path: Path, script: dict, channel: dict) -> Path:
    sounds_dir = channel.get("sounds_dir")
    if not sounds_dir or not Path(sounds_dir).exists():
        return video_path

    cues, t = [], 0.0
    for seg in script.get("segments", []):
        cue = seg.get("sound_cue", "none")
        if cue and cue != "none":
            snd = _find_sound(Path(sounds_dir), cue)
            if snd:
                cues.append((t, snd))
        t += float(seg.get("duration_s", 3))
    if not cues:
        return video_path

    out = video_path.parent / f"{video_path.stem}_sounds.mp4"
    inputs, filters, labels = [], [], []
    for i, (start, snd) in enumerate(cues):
        inputs += ["-i", str(snd)]
        filters.append(
            f"[{i+1}:a]atrim=0:2.0,volume=0.35,"
            f"adelay={int(start*1000)}|{int(start*1000)}[s{i}]"
        )
        labels.append(f"[s{i}]")
    filters.append(
        f"[0:a]{''.join(labels)}amix=inputs={len(cues)+1}:duration=first:normalize=0[a]"
    )
    print(f"🔊 Meme sounds: {', '.join(s.name for _, s in cues)}")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), *inputs,
         "-filter_complex", ";".join(filters),
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", str(out)],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0 or not out.exists():
        print(f"   ⚠️ sound overlay failed:\n{r.stderr[-300:]}")
        return video_path
    return out


def recut(video_path: Path) -> Path:
    """Speed-up + hard cuts + SFX."""
    if not any(SFX_DIR.glob("*.wav")):
        print("   (no SFX — run make_sfx.py) skipping recut")
        return video_path
    out = video_path.parent / f"{video_path.stem}_punchy.mp4"
    cmd = [
        sys.executable, str(ROOT / "recut.py"),
        "--input", str(video_path), "--out", str(out),
        "--speed", "1.06", "--interval", "2.2", "--punch", "0.05",
        "--sfx-dir", str(SFX_DIR),
        "--cut-sfx", "whoosh_01.wav,whoosh_02.wav,whoosh_03.wav,whoosh_04.wav",
        "--whoosh-gain", "0.35",
        "--impact-file", str(SFX_DIR / "impact_01.wav"),
        "--impact-every", "3", "--impact-gain", "0.4", "--no-swell",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not out.exists():
        print(f"   ⚠️ recut failed:\n{r.stderr[-500:]}")
        return video_path
    print(f"   ✅ {out.name}")
    return out


def add_music(video_path: Path) -> Path:
    tracks = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    if not tracks:
        return video_path
    track = random.choice(tracks)
    out = video_path.parent / f"{video_path.stem}_music.mp4"
    print(f"🎵 Music bed: {track.name}")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-stream_loop", "-1", "-i", str(track),
         "-filter_complex",
         "[1:a]volume=0.12,afade=t=in:d=1[m];[0:a][m]amix=inputs=2:duration=first[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", str(out)],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0 or not out.exists():
        return video_path
    return out


def nvenc_encode(video_path: Path) -> Path:
    """Re-encode final video with NVENC for smaller file + GPU speed."""
    out = video_path.parent / "final_studio.mp4"
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23",
         "-c:a", "aac", "-b:a", "192k", str(out)],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0 or not out.exists():
        print("   ⚠️ NVENC failed — keeping CPU-encoded file")
        return video_path
    print(f"   ✅ NVENC encode: {out.name}")
    return out


def finish(video_path: Path, script: dict = None, channel: dict = None) -> Path:
    v = video_path
    if script and channel and channel.get("script_rules") == "memes":
        v = add_meme_sounds(v, script, channel)
    v = recut(v)
    v = add_music(v)
    v = nvenc_encode(v)
    return v

"""
Remotion renderer — passes video clips (AnimateDiff) or still images into the TSX.
"""
import json
import shutil
import subprocess
from pathlib import Path

REMOTION_DIR = Path(__file__).parent / "remotion"


def build_video_remotion(script: dict, output_dir: Path, skin: dict, channel: dict) -> Path:
    public = REMOTION_DIR / "public"
    public.mkdir(exist_ok=True)

    segments_props = []
    for i, seg in enumerate(script["segments"]):
        image_names, video_names = [], []

        # copy still images
        for j, img in enumerate(seg.get("image_paths") or
                                 ([seg["image_path"]] if seg.get("image_path") else [])):
            if img and Path(img).exists():
                name = f"img_{i:02d}_{j}.jpg"
                shutil.copy(img, public / name)
                image_names.append(name)

        # copy video clips (AnimateDiff output)
        for j, vid in enumerate(seg.get("video_paths") or []):
            if vid and Path(vid).exists():
                ext = Path(vid).suffix or ".mp4"
                name = f"vid_{i:02d}_{j}{ext}"
                shutil.copy(vid, public / name)
                video_names.append(name)

        segments_props.append({
            "displayText": seg.get("display_text", seg["text"]),
            "durationS":   max(float(seg.get("duration_s", 3)), 1.0),
            "imagePath":   image_names[0] if image_names else None,
            "imagePaths":  image_names,
            "videoPaths":  video_names,   # real video clips if available
        })

    audio_name = None
    audio = script.get("full_audio_path")
    if audio and Path(audio).exists():
        audio_name = "voiceover.mp3"
        shutil.copy(audio, public / audio_name)

    props = {
        "segments":  segments_props,
        "audioPath": audio_name,
        "skin":      {"bg": skin.get("bg", "#0b1220"), "accent": skin.get("accent", "#FFD23F")},
        "badge":     channel.get("badge", "DID YOU KNOW?"),
        "words":     script.get("words", []),
        "followCta": channel.get("follow_cta", "FOLLOW"),
    }
    props_file = REMOTION_DIR / "props.json"
    props_file.write_text(json.dumps(props, indent=2, ensure_ascii=False))

    out_path = output_dir / "final_video.mp4"
    print("🎬 Rendering with Remotion...")
    result = subprocess.run(
        ["npx", "remotion", "render", "src/index.ts", "Short",
         str(out_path), f"--props={props_file}"],
        cwd=str(REMOTION_DIR),
        capture_output=True, text=True, timeout=900,
        shell=True,   # needed on Windows for npx
    )
    if result.returncode != 0:
        raise RuntimeError(f"Remotion render failed:\n{result.stderr[-3000:]}")
    print(f"✅ Video: {out_path}")
    return out_path

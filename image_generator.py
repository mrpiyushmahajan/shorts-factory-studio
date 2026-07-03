"""
Image generation — Flux.1-dev on RTX 4090 via ComfyUI.
Generates MULTIPLE shots per segment (~1 per 2.2s beat), each from a different
camera angle, then optionally animates each into a video clip via AnimateDiff.
"""
import time
from pathlib import Path

from claude_cli import ask_json
from config import BEAT_SECONDS, VIDEO_SHOTS


def _beats_for(seg: dict) -> int:
    return max(1, round(float(seg.get("duration_s", 3)) / BEAT_SECONDS))


def write_image_prompts(script: dict, channel: dict) -> list[list[str]]:
    """Ask Claude to storyboard multi-angle shots per segment."""
    style = channel.get("image_prompt_style", "cinematic photoreal")
    niche  = channel.get("niche", "")
    lines = [
        f"{i}: \"{s['text']}\" → {_beats_for(s)} shot(s)"
        for i, s in enumerate(script["segments"])
    ]

    meme_hint = ""
    if channel.get("script_rules") == "memes":
        meme_hint = (
            "\nIMPORTANT: ALL prompts must describe the SAME cartoon characters "
            "with identical designs across every shot (e.g. 'a chubby brown street dog "
            "with a red collar and big expressive eyes'). Consistency = character recognition."
        )

    prompt = f"""You are a film director storyboarding a viral YouTube Short.
Channel: {niche}
Art style: {style}

For each segment, write the requested number of DISTINCT image-generation prompts —
consecutive shots from different angles/scales (wide → close-up → reaction → detail).
{meme_hint}

Rules per prompt:
- Concrete subject + camera angle + lighting
- NO text, letters, or words in the image
- Vertical 9:16 composition
- {style} quality — this must stop a scrolling thumb

Segments:
{chr(10).join(lines)}

JSON array of arrays (outer = segments, inner = shot prompts). JSON only."""

    raw = ask_json(prompt)
    result = []
    for i, seg in enumerate(script["segments"]):
        want = _beats_for(seg)
        shots = raw[i] if i < len(raw) and isinstance(raw[i], list) else []
        shots = [p for p in shots if isinstance(p, str)]
        topic = script.get("topic", "the subject")
        while len(shots) < want:
            shots.append(f"dramatic {style} shot of {topic}")
        result.append(shots[:want])
    return result


def generate_images(script: dict, output_dir: Path, channel: dict) -> dict:
    """
    Generate shots for each segment.
    With VIDEO_SHOTS=True: Flux image → AnimateDiff video clip per beat.
    With VIDEO_SHOTS=False: Flux still images (Ken Burns in Remotion).
    """
    from comfyui_client import start_comfyui, generate_image, generate_video_shot

    style_suffix = channel.get("style_suffix", ", cinematic, no text, no watermark")

    print("🖼️  Storyboarding shots with Claude...")
    all_prompts = write_image_prompts(script, channel)
    total = sum(len(p) for p in all_prompts)
    done = 0

    start_comfyui()

    for i, (seg, seg_prompts) in enumerate(zip(script["segments"], all_prompts)):
        image_paths = []
        video_paths = []
        beat_s = float(seg.get("duration_s", 3)) / max(1, len(seg_prompts))

        for j, img_prompt in enumerate(seg_prompts):
            done += 1
            full_prompt = img_prompt + style_suffix
            img_out = output_dir / f"img_{i:02d}_{j}.jpg"
            vid_out = output_dir / f"vid_{i:02d}_{j}.mp4"

            print(f"   Shot {done}/{total}: {img_prompt[:55]}...")

            ok = False
            for attempt in range(3):
                if generate_image(full_prompt, img_out):
                    ok = True
                    break
                print(f"      retry {attempt+1}/3")
                time.sleep(3)

            if not ok:
                print("      ⚠️ image failed — skipping shot")
                continue

            image_paths.append(str(img_out))

            if VIDEO_SHOTS:
                print(f"   Animating shot {done}/{total}...")
                if generate_video_shot(img_out, img_prompt, vid_out, beat_s):
                    video_paths.append(str(vid_out))
                else:
                    print("      ⚠️ animation failed — using still")
                    video_paths.append(str(img_out))   # still as fallback

        seg["image_paths"] = image_paths
        seg["image_path"]  = image_paths[0] if image_paths else None
        seg["video_paths"] = video_paths if VIDEO_SHOTS else []

    return script

"""
Shorts Factory Studio — main pipeline.
Usage:
  python daily_shorts.py --channel did_you_know
  python daily_shorts.py --channel desi_memes
"""
import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ── arg parse first so imports can use channel ───────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--channel", default="did_you_know",
                    choices=["did_you_know", "desi_memes"])
args, _ = parser.parse_known_args()

from config import get_channel, ROOT
channel = get_channel(args.channel)

from claude_cli import ask_json
from topic_researcher import pick_topic
from script_writer import write_script
from image_generator import generate_images
from voice_generator import generate_voiceover, hinglishify_words
from scene_coder import generate_bespoke_scene, restore_stub
from remotion_renderer import build_video_remotion
from finishing import finish
from youtube_uploader import upload_video


def _log(topic, script, video_id, run_dir):
    ledger = channel["data_dir"] / "posts_ledger.md"
    entry = (
        f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"- Topic: {topic['topic']}\n"
        f"- Title: {script['title']}\n"
        f"- YouTube ID: {video_id}\n"
        f"- URL: https://www.youtube.com/shorts/{video_id}\n"
        f"- Voice: {script.get('voice', '?')}\n"
        f"- Gate: {topic.get('total', '?')}/50\n"
    )
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(entry)


def run():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = channel["output_dir"] / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    ROOT.joinpath("logs").mkdir(exist_ok=True)
    log_file = ROOT / "logs" / f"{args.channel}_{ts}.log"

    print(f"\n{'='*60}")
    print(f"🎬 SHORTS FACTORY STUDIO — {args.channel} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    try:
        # 1. Research + validate topic
        topic = pick_topic(channel)
        print(f"\n✅ Topic: {topic['topic']}\n")

        # 2. Write script
        print("✍️  Writing script...")
        script = write_script(topic, channel)
        (run_dir / "script.json").write_text(
            json.dumps(script, indent=2, ensure_ascii=False))
        print(f"   Title: {script['title']}")

        # 3. Voice (Chatterbox CUDA or edge-tts for Hindi)
        print("\n🎙️  Generating voiceover...")
        script = generate_voiceover(script, run_dir, channel)
        if channel["script_rules"] == "memes":
            script = hinglishify_words(script)

        # 4. Images + video shots (Flux.1-dev + AnimateDiff on RTX 4090)
        print("\n🖼️  Generating AI images + video shots...")
        script = generate_images(script, run_dir, channel)

        # 5. Bespoke Claude-coded overlay
        print("\n🎭 Coding bespoke scene overlay...")
        skin = channel["visual_skins"][0]  # variation engine can rotate this
        try:
            generate_bespoke_scene(script, skin)
        except Exception as e:
            print(f"   ⚠️ scene coder failed ({e}) — using stub")
            restore_stub()

        # 6. Remotion render (NVENC GPU encode)
        print("\n🎬 Rendering with Remotion + NVENC...")
        video_path = build_video_remotion(script, run_dir, skin, channel)

        # 7. Finishing (meme sounds, recut, music)
        print("\n✂️  Finishing pass...")
        video_path = finish(video_path, script, channel)

        # 8. Upload
        print("\n⬆️  Uploading to YouTube...")
        video_id = upload_video(video_path, script, channel)

        _log(topic, script, video_id, run_dir)
        url = f"https://www.youtube.com/shorts/{video_id}"
        print(f"\n🎉 Done! {url}")
        log_file.write_text(f"SUCCESS: {video_id} — {script['title']}")
        return 0

    except Exception:
        err = traceback.format_exc()
        print(f"\n❌ Pipeline failed:\n{err}")
        log_file.write_text(f"FAILURE:\n{err}")
        return 1


if __name__ == "__main__":
    sys.exit(run())

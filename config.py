"""
Shorts Factory Studio — Windows RTX 4090
Central config. Pass --channel did_you_know or --channel desi_memes.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ROOT       = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
LOGS_DIR   = ROOT / "logs"
ASSETS_DIR = ROOT / "assets"

# ── GPU ──────────────────────────────────────────────────────────────────────
GPU_DEVICE       = "cuda"          # RTX 4090
COMFYUI_HOST     = "127.0.0.1"
COMFYUI_PORT     = 8188
COMFYUI_DIR      = ROOT / "comfyui"
COMFYUI_MODELS   = COMFYUI_DIR / "models"

# ── Video / render ───────────────────────────────────────────────────────────
VIDEO_WIDTH      = 1080
VIDEO_HEIGHT     = 1920
VIDEO_FPS        = 30
FFMPEG_ENCODER   = "h264_nvenc"    # GPU encoding on RTX 4090
FFMPEG_PRESET    = "p4"            # NVENC quality preset (p1=fastest p7=best)

# ── Image generation (Flux.1-dev via ComfyUI) ─────────────────────────────
FLUX_MODEL       = "flux1-dev.safetensors"
FLUX_VAE         = "ae.safetensors"
FLUX_CLIP1       = "t5xxl_fp16.safetensors"
FLUX_CLIP2       = "clip_l.safetensors"
FLUX_STEPS       = 20
FLUX_GUIDANCE    = 3.5
BEAT_SECONDS     = 2.2             # one new shot every 2.2s

# ── Video shot generation (AnimateDiff via ComfyUI) ──────────────────────
ANIMDIFF_MODEL   = "animatediff_lightning_8step.ckpt"
ANIMDIFF_FRAMES  = 16              # ~0.5s at 30fps per chunk → looped to fill beat
VIDEO_SHOTS      = True            # False = fall back to still images + Ken Burns

# ── Voice (Chatterbox CUDA + faster-whisper) ─────────────────────────────
WHISPER_MODEL    = "base"          # base/small/medium — tradeoff speed vs accuracy
VOICE_REF_WAV    = ASSETS_DIR / "voice_ref.wav"   # optional cloning reference

# ── Channels ─────────────────────────────────────────────────────────────────
CHANNELS = {
    "did_you_know": {
        "niche": "Did you know facts",
        "lang": "English",
        "audience": "curious people aged 16-35 who love learning surprising facts",
        "badge": "DID YOU KNOW?",
        "voices_edge": [                    # edge-tts fallback
            "en-US-AndrewNeural",
            "en-US-JennyNeural",
            "en-GB-RyanNeural",
            "en-AU-NatashaNeural",
        ],
        "style_suffix": (
            ", cinematic photoreal, hyper detailed, dramatic studio lighting, "
            "8K octane render, 9:16 vertical, no text, no watermark"
        ),
        "image_prompt_style": "photoreal cinematic",
        "title_shapes": [
            "You Won't Believe {fact_hook}",
            "{fact_hook} — Most People Don't Know This",
            "The Shocking Truth About {topic}",
            "Nobody Talks About {fact_hook}",
            "{number} Facts About {topic} That Will Blow Your Mind",
            "Science Just Proved {fact_hook}",
        ],
        "visual_skins": [
            {"id": "S1", "name": "Cinematic Gold",   "bg": "#0D0D0D", "accent": "#FFD700"},
            {"id": "S2", "name": "Deep Blue Cyan",   "bg": "#0A0A2E", "accent": "#00F5FF"},
            {"id": "S3", "name": "Dark Orange",      "bg": "#1A0A00", "accent": "#FF6B00"},
            {"id": "S4", "name": "Neon Green",       "bg": "#0A1A0A", "accent": "#39FF14"},
            {"id": "S5", "name": "Magenta",          "bg": "#1A0A1A", "accent": "#FF00FF"},
        ],
        "oauth_dir": Path.home() / ".config" / "shorts-factory",
        "follow_cta": "FOLLOW FOR DAILY FACTS",
        "script_rules": "facts",
    },
    "desi_memes": {
        "niche": (
            "Funny Indian meme videos — cartoonish comedy skits of animals with humans, "
            "humans with humans, animals with animals in relatable Indian everyday situations"
        ),
        "lang": "Hindi (Devanagari voiceover, Hinglish captions)",
        "audience": "Indians aged 13-35 who share funny memes",
        "badge": "😂 WAIT FOR IT",
        "voices_edge": [
            "hi-IN-MadhurNeural",
            "hi-IN-SwaraNeural",
        ],
        "style_suffix": (
            ", 3D Pixar-style cartoon, exaggerated funny facial expressions, "
            "vibrant saturated colors, comedic pose, soft studio lighting, "
            "9:16 vertical, no text, no watermark"
        ),
        "image_prompt_style": "3D Pixar cartoon",
        "title_shapes": [
            "POV: {fact_hook} 😂",
            "{fact_hook} 💀💀💀",
            "Every Indian knows this feeling 😭 {topic}",
            "Wait for it... {topic} 🤣",
            "{topic} be like:",
            "Desi {topic} hits different 😂",
        ],
        "visual_skins": [
            {"id": "S1", "name": "Saffron Pop",  "bg": "#1A0A00", "accent": "#FF9933"},
            {"id": "S2", "name": "Dark Gold",    "bg": "#0D0D0D", "accent": "#FFD700"},
            {"id": "S3", "name": "Neon Green",   "bg": "#0A1A0A", "accent": "#39FF14"},
            {"id": "S4", "name": "Magenta",      "bg": "#1A0A1A", "accent": "#FF00FF"},
            {"id": "S5", "name": "Cyan",         "bg": "#0A0A2E", "accent": "#00F5FF"},
        ],
        "oauth_dir": Path.home() / ".config" / "shorts-factory-memes",
        "follow_cta": "FOLLOW FOR DAILY MEMES",
        "script_rules": "memes",
        "sounds_dir": ASSETS_DIR / "sounds",
    },
}


def get_channel(name: str) -> dict:
    if name not in CHANNELS:
        raise ValueError(f"Unknown channel: {name}. Choose: {list(CHANNELS.keys())}")
    ch = CHANNELS[name].copy()
    ch["name"] = name
    ch["data_dir"]   = ROOT / "data" / name
    ch["output_dir"] = OUTPUT_DIR / name
    ch["token_file"] = ch["oauth_dir"] / "yt_token.json"
    ch["secret_file"]= ch["oauth_dir"] / "client_secret.json"
    ch["data_dir"].mkdir(parents=True, exist_ok=True)
    ch["output_dir"].mkdir(parents=True, exist_ok=True)
    return ch

# Shorts Factory Studio — RTX 4090 Windows Edition

Full GPU-accelerated autonomous YouTube Shorts factory.
Two channels, six videos/day, zero human intervention.

## Hardware
- **GPU**: NVIDIA RTX 4090 (24GB VRAM)
- **OS**: Windows 10/11
- **RAM**: 16GB+ recommended

## What runs on GPU vs CPU

| Layer | Tool | GPU? | Quality vs Mac |
|---|---|---|---|
| Image generation | Flux.1-dev via ComfyUI | ✅ RTX 4090 | 10× better, 8× faster |
| Video shots | AnimateDiff via ComfyUI | ✅ RTX 4090 | Real motion vs Ken Burns |
| Voice (English) | Chatterbox TTS | ✅ CUDA | 10× faster |
| Voice (Hindi) | edge-tts | ❌ cloud | Same (free, accurate) |
| Word timing | faster-whisper | ✅ CUDA | More precise captions |
| Rendering | Remotion + NVENC | ✅ NVENC | 3× faster encode |
| AI scripting | Claude CLI | ❌ API | Same |
| Upload | YouTube Data API | ❌ cloud | Same |

## One-click setup

```bat
git clone <your-repo> shorts-factory-studio
cd shorts-factory-studio
setup.bat
```

`setup.bat` installs:
- Python venv + PyTorch 2.4 CUDA 12.1
- Chatterbox TTS + faster-whisper
- ComfyUI + AnimateDiff extension
- Node.js Remotion
- Downloads all models (~20GB, one-time)

## Channel schedule

```
12:00 / 17:00 / 21:00  →  Did You Know (facts, English, Chatterbox voice)
13:30 / 18:30 / 22:30  →  Desi Memes Daily (Hindi, Flux cartoon, myinstants sounds)
10:00 / 10:30           →  CreatorStudy (studies competitors daily)
22:00                   →  ShortsDigest (email summary)
Sun 09:00 / 09:30       →  Learning loop (rewrites rules from analytics)
```

## First run

```bat
:: 1. Auth both channels
python setup_oauth.py --channel did_you_know
python setup_oauth.py --channel desi_memes

:: 2. Test one video each
python daily_shorts.py --channel did_you_know
python daily_shorts.py --channel desi_memes

:: 3. Activate auto-schedule
schedulers\setup_schedule.bat
```

## Model downloads (required)

`download_models.py` fetches:
- `flux1-dev.safetensors` (23.8GB) — requires free HuggingFace account + model access
- `ae.safetensors` VAE (0.3GB)
- `t5xxl_fp16.safetensors` CLIP (9.8GB)
- `clip_l.safetensors` (0.2GB)
- `animatediff_lightning_8step.ckpt` (1.7GB)
- `v1-5-pruned-emaonly.ckpt` SD1.5 base (4.0GB)

Total ~40GB disk. Accept Flux.1-dev terms at huggingface.co/black-forest-labs/FLUX.1-dev first.

## Video pipeline (per video)

```
Claude  →  topic gate  →  skit/fact script
GPU     →  Flux.1-dev images (1080×1920, ~5s each)
GPU     →  AnimateDiff animates each image into a 2s video clip
edge-tts / Chatterbox  →  voiceover + word timings
faster-whisper  →  precise caption alignment
Claude  →  codes bespoke animated TSX overlay per topic
Remotion  →  composites clips + overlay + captions → raw MP4
NVENC  →  GPU re-encode (smaller file, faster)
ffmpeg  →  meme sounds + music bed + recut
YouTube API  →  upload
```

## Adding more channels

Copy a channel config block in `config.py`, add its OAuth dir, run `setup_oauth.py --channel <name>`.
Add two Task Scheduler entries in `schedulers/setup_schedule.bat`.

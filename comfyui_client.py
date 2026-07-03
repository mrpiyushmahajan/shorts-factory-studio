"""
ComfyUI API client — handles both image generation (Flux.1-dev) and
video shot generation (AnimateDiff) on the local RTX 4090.

ComfyUI must be running: python comfyui/main.py --listen 127.0.0.1 --port 8188
The manager (start_comfyui / stop_comfyui) handles that automatically.
"""
import json
import random
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

from config import COMFYUI_HOST, COMFYUI_PORT, COMFYUI_DIR, COMFYUI_MODELS
from config import FLUX_MODEL, FLUX_VAE, FLUX_CLIP1, FLUX_CLIP2
from config import FLUX_STEPS, FLUX_GUIDANCE
from config import ANIMDIFF_MODEL, ANIMDIFF_FRAMES

BASE_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"
_comfyui_proc = None


# ── Server lifecycle ─────────────────────────────────────────────────────────

def start_comfyui():
    global _comfyui_proc
    if _is_running():
        print("   ComfyUI already running")
        return
    print("🚀 Starting ComfyUI...")
    _comfyui_proc = subprocess.Popen(
        ["python", "main.py", "--listen", COMFYUI_HOST, "--port", str(COMFYUI_PORT),
         "--highvram", "--fast"],
        cwd=str(COMFYUI_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        if _is_running():
            print("   ✅ ComfyUI ready")
            return
        time.sleep(2)
    raise RuntimeError("ComfyUI failed to start in 120s")


def stop_comfyui():
    global _comfyui_proc
    if _comfyui_proc:
        _comfyui_proc.terminate()
        _comfyui_proc = None


def _is_running() -> bool:
    try:
        urllib.request.urlopen(f"{BASE_URL}/system_stats", timeout=3)
        return True
    except Exception:
        return False


# ── Workflow execution ───────────────────────────────────────────────────────

def _queue(workflow: dict) -> list[Path]:
    """Submit workflow, wait for result, return output file paths."""
    client_id = str(uuid.uuid4())
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(f"{BASE_URL}/prompt", data=payload,
                                  headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req).read())
    prompt_id = resp["prompt_id"]

    # poll until done
    for _ in range(600):
        hist = json.loads(urllib.request.urlopen(f"{BASE_URL}/history/{prompt_id}").read())
        if prompt_id in hist:
            outputs = hist[prompt_id]["outputs"]
            paths = []
            for node_out in outputs.values():
                for imgs in node_out.get("images", []):
                    p = COMFYUI_DIR / "output" / imgs["filename"]
                    if p.exists():
                        paths.append(p)
                for vids in node_out.get("gifs", []):
                    p = COMFYUI_DIR / "output" / vids["filename"]
                    if p.exists():
                        paths.append(p)
            return paths
        time.sleep(1)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} timed out")


# ── Flux.1-dev image workflow ────────────────────────────────────────────────

def _flux_workflow(prompt: str, width: int, height: int, seed: int) -> dict:
    neg = "text, watermark, blurry, low quality, deformed, ugly"
    return {
        "6":  {"class_type": "CLIPTextEncode",
               "inputs": {"text": prompt, "clip": ["11", 0]}},
        "7":  {"class_type": "CLIPTextEncode",
               "inputs": {"text": neg, "clip": ["11", 0]}},
        "8":  {"class_type": "VAEDecode",
               "inputs": {"samples": ["13", 0], "vae": ["10", 0]}},
        "9":  {"class_type": "SaveImage",
               "inputs": {"filename_prefix": "studio_img", "images": ["8", 0]}},
        "10": {"class_type": "VAELoader",
               "inputs": {"vae_name": FLUX_VAE}},
        "11": {"class_type": "DualCLIPLoader",
               "inputs": {"clip_name1": FLUX_CLIP1, "clip_name2": FLUX_CLIP2, "type": "flux"}},
        "12": {"class_type": "UNETLoader",
               "inputs": {"unet_name": FLUX_MODEL, "weight_dtype": "fp8_e4m3fn"}},
        "13": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["25", 0], "guider": ["22", 0],
                          "sampler": ["16", 0], "sigmas": ["17", 0],
                          "latent_image": ["27", 0]}},
        "16": {"class_type": "KSamplerSelect",
               "inputs": {"sampler_name": "euler"}},
        "17": {"class_type": "BasicScheduler",
               "inputs": {"scheduler": "simple", "steps": FLUX_STEPS,
                          "denoise": 1.0, "model": ["12", 0]}},
        "22": {"class_type": "BasicGuider",
               "inputs": {"model": ["12", 0], "conditioning": ["6", 0]}},
        "25": {"class_type": "RandomNoise",
               "inputs": {"noise_seed": seed}},
        "27": {"class_type": "EmptySD3LatentImage",
               "inputs": {"width": width, "height": height, "batch_size": 1}},
    }


def generate_image(prompt: str, out_path: Path,
                   width: int = 1080, height: int = 1920) -> bool:
    """Generate one image with Flux.1-dev. Returns True on success."""
    seed = random.randint(0, 2**32 - 1)
    try:
        results = _queue(_flux_workflow(prompt, width, height, seed))
        if results:
            import shutil
            shutil.copy(results[0], out_path)
            return True
    except Exception as e:
        print(f"      ComfyUI image error: {e}")
    return False


# ── AnimateDiff video shot workflow ──────────────────────────────────────────

def _animdiff_workflow(image_path: Path, prompt: str, frames: int, seed: int) -> dict:
    """Animate a Flux image into a short video clip using AnimateDiff Lightning."""
    return {
        "1":  {"class_type": "CheckpointLoaderSimple",
               "inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"}},
        "2":  {"class_type": "ADE_AnimateDiffLoaderWithContext",
               "inputs": {"model": ["1", 0], "motion_module": ANIMDIFF_MODEL,
                          "beta_schedule": "sqrt_linear (AnimateDiff)",
                          "motion_scale": 1.0}},
        "3":  {"class_type": "CLIPTextEncode",
               "inputs": {"text": prompt, "clip": ["1", 1]}},
        "4":  {"class_type": "CLIPTextEncode",
               "inputs": {"text": "text, watermark, blur, distortion", "clip": ["1", 1]}},
        "5":  {"class_type": "LoadImage",
               "inputs": {"image": str(image_path)}},
        "6":  {"class_type": "VAEEncode",
               "inputs": {"pixels": ["5", 0], "vae": ["1", 2]}},
        "7":  {"class_type": "KSampler",
               "inputs": {"model": ["2", 0], "positive": ["3", 0], "negative": ["4", 0],
                          "latent_image": ["6", 0], "seed": seed, "steps": 8,
                          "cfg": 7.0, "sampler_name": "euler_ancestral",
                          "scheduler": "linear", "denoise": 0.7}},
        "8":  {"class_type": "VAEDecode",
               "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        "9":  {"class_type": "VHS_VideoCombine",
               "inputs": {"images": ["8", 0], "frame_rate": 30,
                          "loop_count": 0, "filename_prefix": "studio_vid",
                          "format": "video/h264-mp4", "pingpong": False,
                          "save_output": True}},
    }


def generate_video_shot(image_path: Path, prompt: str, out_path: Path,
                        duration_s: float = 2.2) -> bool:
    """Animate a still image into a video clip. Returns True on success."""
    seed = random.randint(0, 2**32 - 1)
    frames = max(8, int(duration_s * 30))
    try:
        results = _queue(_animdiff_workflow(image_path, prompt, frames, seed))
        if results:
            import shutil
            shutil.copy(results[0], out_path)
            return True
    except Exception as e:
        print(f"      AnimateDiff error: {e}")
    return False

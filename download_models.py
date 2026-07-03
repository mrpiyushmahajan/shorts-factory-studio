"""
One-time model downloader — run during setup.
Downloads Flux.1-dev and AnimateDiff Lightning to ComfyUI's model directories.
"""
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
COMFYUI_MODELS = ROOT / "comfyui" / "models"

MODELS = [
    # Flux.1-dev (text-to-image)
    {
        "name": "flux1-dev.safetensors",
        "dest": COMFYUI_MODELS / "unet",
        "url": "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors",
        "size_gb": 23.8,
        "requires_hf_token": True,
    },
    {
        "name": "ae.safetensors",
        "dest": COMFYUI_MODELS / "vae",
        "url": "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors",
        "size_gb": 0.3,
        "requires_hf_token": True,
    },
    {
        "name": "t5xxl_fp16.safetensors",
        "dest": COMFYUI_MODELS / "clip",
        "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors",
        "size_gb": 9.8,
        "requires_hf_token": False,
    },
    {
        "name": "clip_l.safetensors",
        "dest": COMFYUI_MODELS / "clip",
        "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors",
        "size_gb": 0.2,
        "requires_hf_token": False,
    },
    # AnimateDiff Lightning (8-step, fast video animation)
    {
        "name": "animatediff_lightning_8step.ckpt",
        "dest": COMFYUI_MODELS / "animatediff_models",
        "url": "https://huggingface.co/ByteDance/AnimateDiff-Lightning/resolve/main/animatediff_lightning_8step_comfyui.safetensors",
        "size_gb": 1.7,
        "requires_hf_token": False,
    },
    # SD 1.5 base (required by AnimateDiff)
    {
        "name": "v1-5-pruned-emaonly.ckpt",
        "dest": COMFYUI_MODELS / "checkpoints",
        "url": "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt",
        "size_gb": 3.97,
        "requires_hf_token": False,
    },
]

HF_TOKEN_FILE = Path.home() / ".config" / "huggingface" / "token"


def _hf_token() -> str:
    if HF_TOKEN_FILE.exists():
        return HF_TOKEN_FILE.read_text().strip()
    token = os.getenv("HF_TOKEN", "")
    if token:
        return token
    print()
    print("Flux.1-dev requires a HuggingFace token.")
    print("1. Create account at https://huggingface.co")
    print("2. Accept model terms at https://huggingface.co/black-forest-labs/FLUX.1-dev")
    print("3. Generate token at https://huggingface.co/settings/tokens")
    token = input("Paste your HF token: ").strip()
    HF_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    HF_TOKEN_FILE.write_text(token)
    return token


def _download(url: str, dest: Path, token: str = ""):
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        block = 1024 * 1024   # 1MB
        while True:
            chunk = r.read(block)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r   {pct:.1f}%  {downloaded/1e9:.2f}/{total/1e9:.2f} GB", end="")
        print()


def main():
    token = _hf_token()
    total_gb = sum(m["size_gb"] for m in MODELS)
    print(f"\nDownloading {len(MODELS)} models ({total_gb:.1f} GB total)\n")

    for m in MODELS:
        dest = m["dest"] / m["name"]
        if dest.exists():
            print(f"   [skip] {m['name']} already present")
            continue
        print(f"   ↓ {m['name']} ({m['size_gb']:.1f} GB)")
        t = token if m["requires_hf_token"] else ""
        try:
            _download(m["url"], dest, t)
            print(f"   ✅ {m['name']}")
        except Exception as e:
            print(f"   ✗ {m['name']}: {e}")
            print(f"     Manual download: {m['url']}")
            print(f"     Place at: {dest}")

    print("\n✅ Model download complete.")
    print("   If any failed, download manually and place in the paths shown above.")


if __name__ == "__main__":
    main()

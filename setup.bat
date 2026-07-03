@echo off
setlocal enabledelayedexpansion
title Shorts Factory Studio — One-Click Setup

echo ============================================================
echo  SHORTS FACTORY STUDIO — RTX 4090 Setup
echo ============================================================
echo.

:: ── 0. Check prerequisites ──────────────────────────────────────────────────
where git >nul 2>&1 || (echo [ERROR] Git not found. Install from https://git-scm.com & pause & exit /b 1)
where python >nul 2>&1 || (echo [ERROR] Python 3.11+ not found. Install from https://python.org & pause & exit /b 1)
where node >nul 2>&1 || (echo [ERROR] Node.js not found. Install from https://nodejs.org & pause & exit /b 1)
where ffmpeg >nul 2>&1 || (echo [ERROR] FFmpeg not found. Install from https://ffmpeg.org or: winget install ffmpeg & pause & exit /b 1)
where claude >nul 2>&1 || (
    echo [ERROR] Claude CLI not found.
    echo.
    echo Install it:
    echo   1. Go to https://claude.ai/claude-code
    echo   2. Download the Windows installer
    echo   3. Sign in with your Claude subscription
    echo   4. Re-run this setup.bat
    pause & exit /b 1
)

echo [OK] Prerequisites found.
echo.

:: ── 1. Python venv ──────────────────────────────────────────────────────────
echo [1/7] Creating Python virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

:: ── 2. PyTorch CUDA ─────────────────────────────────────────────────────────
echo [2/7] Installing PyTorch 2.6 + CUDA 12.4 (RTX 4090)...
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124 --quiet
if errorlevel 1 (echo [ERROR] PyTorch install failed. & pause & exit /b 1)
python -c "import torch; print('[OK] CUDA:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NOT AVAILABLE')"
if errorlevel 1 (echo [ERROR] CUDA check failed. Ensure NVIDIA drivers installed. & pause & exit /b 1)

:: ── 3. Core Python deps ──────────────────────────────────────────────────────
echo [3/7] Installing Python dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (echo [ERROR] pip install failed. & pause & exit /b 1)
echo [OK] Python deps installed.

:: ── 4. Chatterbox TTS ───────────────────────────────────────────────────────
echo [4/7] Installing Chatterbox TTS (voice cloning)...
pip install chatterbox-tts --quiet
python -c "from chatterbox.tts import ChatterboxTTS; print('[OK] Chatterbox ready')" 2>nul || (
    echo [WARN] Chatterbox install needs build tools. Installing...
    pip install setuptools^<81 chatterbox-tts --quiet
)

:: ── 5. ComfyUI ───────────────────────────────────────────────────────────────
echo [5/7] Setting up ComfyUI (image + video generation)...
if not exist comfyui (
    git clone https://github.com/comfyanonymous/ComfyUI.git comfyui --depth=1 --quiet
    cd comfyui
    pip install -r requirements.txt --quiet
    cd ..
    echo [OK] ComfyUI cloned.
) else (
    echo [OK] ComfyUI already present.
)

:: Install ComfyUI-VideoHelperSuite for video clip handling
if not exist comfyui\custom_nodes\ComfyUI-VideoHelperSuite (
    cd comfyui\custom_nodes
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git --depth=1 --quiet
    cd ..\..
)

:: Install ComfyUI-Advanced-ControlNet + AnimateDiff for video shots
if not exist comfyui\custom_nodes\ComfyUI-AnimateDiff-Evolved (
    cd comfyui\custom_nodes
    git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git --depth=1 --quiet
    cd ..\..
)

echo [OK] ComfyUI + extensions installed.

:: ── 6. Models ────────────────────────────────────────────────────────────────
echo [6/7] Downloading AI models (one-time, ~20GB)...
echo       This takes 10-30 min depending on connection. Ctrl+C to skip and do later.
python download_models.py
echo [OK] Models ready.

:: ── 7. Remotion ──────────────────────────────────────────────────────────────
echo [7/7] Installing Remotion...
cd remotion
call npm install --silent
cd ..
echo [OK] Remotion installed.

:: ── OAuth ────────────────────────────────────────────────────────────────────
echo.
echo ============================================================
echo  SETUP COMPLETE
echo ============================================================
echo.
echo Next steps:
echo   1. Copy your YouTube client_secret.json files:
echo      mkdir %%USERPROFILE%%\.config\shorts-factory
echo      copy client_secret.json %%USERPROFILE%%\.config\shorts-factory\
echo.
echo   2. Authenticate each channel:
echo      python setup_oauth.py --channel did_you_know
echo      python setup_oauth.py --channel desi_memes
echo.
echo   3. Test one video:
echo      python daily_shorts.py --channel did_you_know
echo.
echo   4. Activate auto-schedule:
echo      schedulers\setup_schedule.bat
echo.
pause

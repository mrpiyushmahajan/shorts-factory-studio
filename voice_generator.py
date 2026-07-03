"""
Voice generation — RTX 4090 studio version.

Priority chain:
  1. Chatterbox TTS (CUDA) — expressive, cloneable voice
  2. edge-tts — free fallback (required for Hindi; Chatterbox English-only)

Word timings:
  - Chatterbox path: faster-whisper (GPU) aligns words to audio precisely
  - edge-tts path:   WordBoundary events from edge-tts
"""
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

import edge_tts
import torch

from config import GPU_DEVICE, WHISPER_MODEL, VOICE_REF_WAV


# ── faster-whisper word alignment ────────────────────────────────────────────

def _transcribe_words(audio_path: Path) -> list[dict]:
    """Run faster-whisper on GPU to get precise word-level timings."""
    try:
        from faster_whisper import WhisperModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute)
        segments, _ = model.transcribe(str(audio_path), word_timestamps=True)
        words = []
        for seg in segments:
            for w in (seg.words or []):
                words.append({"text": w.word.strip(), "start": round(w.start, 3),
                               "end": round(w.end, 3)})
        return words
    except Exception as e:
        print(f"   ⚠️ faster-whisper failed ({e}) — no word timings")
        return []


# ── Chatterbox CUDA ──────────────────────────────────────────────────────────

def _chatterbox_generate(text: str, out_path: Path) -> bool:
    """Generate with Chatterbox on CUDA. Returns True on success."""
    try:
        from chatterbox.tts import ChatterboxTTS
        device = GPU_DEVICE if torch.cuda.is_available() else "cpu"
        model = ChatterboxTTS.from_pretrained(device=device)
        ref = str(VOICE_REF_WAV) if VOICE_REF_WAV.exists() else None
        wav = model.generate(text, audio_prompt_path=ref)
        import torchaudio
        torchaudio.save(str(out_path), wav, model.sr)
        return True
    except Exception as e:
        print(f"   Chatterbox: {e}")
        return False


# ── edge-tts (Hindi + fallback) ──────────────────────────────────────────────

async def _edge_generate(text: str, voice: str, out_path: Path) -> list[dict]:
    communicate = edge_tts.Communicate(text=text, voice=voice,
                                        rate="+5%", boundary="WordBoundary")
    words = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })
    return words


def _audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _concat(paths: list[str], output: Path):
    list_file = output.parent / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in paths))
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c:a", "libmp3lame", "-q:a", "2", str(output)],
        check=True, capture_output=True,
    )
    list_file.unlink(missing_ok=True)


# ── Public API ───────────────────────────────────────────────────────────────

def generate_voiceover(script: dict, output_dir: Path, channel: dict) -> dict:
    """
    Generate voiceover for all segments.
    Uses Chatterbox (CUDA) for English, edge-tts for Hindi.
    Runs faster-whisper on Chatterbox output for precise word timing.
    """
    voice = script.pop("_voice_override", None) or channel["voices_edge"][0]
    use_edge = voice.startswith("hi-")   # Hindi must use edge-tts

    print(f"🎙️  Voice: {voice} | GPU: {'edge-tts' if use_edge else 'Chatterbox CUDA'}")

    segment_paths = []
    all_words = []
    t_offset = 0.0

    for i, seg in enumerate(script["segments"]):
        out = output_dir / f"seg_{i:02d}.mp3"
        words = []

        if use_edge:
            # edge-tts gives us word timings directly
            words = asyncio.run(_edge_generate(seg["text"], voice, out))
        else:
            # Chatterbox CUDA → faster-whisper for timing
            wav_tmp = output_dir / f"seg_{i:02d}.wav"
            if _chatterbox_generate(seg["text"], wav_tmp):
                # convert to mp3 with NVENC-aware FFmpeg
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(wav_tmp),
                     "-c:a", "libmp3lame", "-q:a", "2", str(out)],
                    capture_output=True, check=True,
                )
                wav_tmp.unlink(missing_ok=True)
                words = _transcribe_words(out)
            else:
                # fallback to edge-tts
                print(f"   Chatterbox failed seg {i} — falling back to edge-tts")
                fb_voice = channel["voices_edge"][i % len(channel["voices_edge"])]
                words = asyncio.run(_edge_generate(seg["text"], fb_voice, out))

        seg["audio_path"] = str(out)
        real_dur = _audio_duration(out)
        if real_dur > 0.3:
            seg["duration_s"] = round(real_dur + 0.15, 2)

        seg["words"] = words
        for w in words:
            all_words.append({
                "text": w["text"],
                "start": round(t_offset + w["start"], 3),
                "end":   round(t_offset + w["end"], 3),
            })
        t_offset += seg["duration_s"]
        segment_paths.append(str(out))
        print(f"   Seg {i}: {seg['duration_s']}s, {len(words)} words")

    full_audio = output_dir / "voiceover_full.mp3"
    _concat(segment_paths, full_audio)
    script["full_audio_path"] = str(full_audio)
    script["words"] = all_words
    script["voice"] = voice
    (output_dir / "words.json").write_text(json.dumps(all_words, indent=2))
    return script


def hinglishify_words(script: dict) -> dict:
    """Transliterate Devanagari word timings → Hinglish for karaoke captions."""
    words = script.get("words", [])
    if not words:
        return script
    originals = [w["text"] for w in words]
    try:
        from claude_cli import ask_json
        translit = ask_json(
            "Transliterate each Hindi word to casual Hinglish (Latin script, as Indians "
            "type in chats). Return a JSON array of strings, SAME length and order. "
            f"Input: {originals}"
        )
        if isinstance(translit, list) and len(translit) == len(words):
            for w, t in zip(words, translit):
                if isinstance(t, str) and t.strip():
                    w["text"] = t.strip()
    except Exception as e:
        print(f"   ⚠️ transliteration failed ({e})")
    return script

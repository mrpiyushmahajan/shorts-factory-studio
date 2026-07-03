#!/usr/bin/env python3
"""
recut.py - turn a finished cinematic short into a punchy, fast-cut version.

Takes an already-rendered narration-driven vertical short (e.g. the output of
make_elephant_short.py) and:

  1. Re-times it to "normal" energy with a mild, PITCH-PRESERVING speed-up
     (setpts on video + atempo on audio, so the narrator doesn't chipmunk).
  2. Chops the VIDEO into fixed-interval beats and alternates a static
     zoom-punch between beats -> hard "fast cut" jumps at every interval.
  3. Lays a whoosh SFX from the library on each cut (and an optional impact
     on emphasis beats), mixed OVER the original narration which is left at
     full level.

The narration audio stays one continuous stream, so only the VIDEO is cut --
nothing ever drifts out of sync. Pure stdlib + ffmpeg/ffprobe.

Example (the elephant short this was built against):

  python .claude/skills/punchy-recut/recut.py \
      --input output/elephant_keeper_final_goodbye_short.mp4

Output defaults to <input_stem>_punchy.mp4 next to the input.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

# Default SFX pool, relative to --sfx-dir. Short whooshes from the CC0/CC-BY
# soundfx-rse set (license-clean for monetized use). whoosh3/4/5 are 0.2-0.47s
# -> snappy. Rotated per cut in order.
DEFAULT_WHOOSHES = [
    "soundfx-rse/soundfx.d/whoosh3.mp3",
    "soundfx-rse/soundfx.d/whoosh4.mp3",
    "soundfx-rse/soundfx.d/whoosh5.mp3",
]
# Longer swell used once at the very start (optional, --no-swell to disable).
DEFAULT_SWELL = "soundfx-rse/soundfx.d/whoosh2.mp3"


def run(args: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run([str(a) for a in args], cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-of", "json",
         "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_type",
         str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    vid = next(s for s in data["streams"] if s["codec_type"] == "video")
    num, den = vid["r_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    return {
        "duration": float(data["format"]["duration"]),
        "w": int(vid["width"]),
        "h": int(vid["height"]),
        "fps": round(fps),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path, help="finished short .mp4")
    ap.add_argument("--out", type=Path, default=None, help="output path")
    ap.add_argument("--interval", type=float, default=1.4,
                    help="seconds between cuts (smaller = faster cutting). default 1.4")
    ap.add_argument("--cuts-file", type=Path, default=None,
                    help="file of explicit cut timestamps (seconds, ORIGINAL timeline, "
                         "one per line). Overrides --interval. Use for phrase-aligned cuts.")
    ap.add_argument("--impact-at-file", type=Path, default=None,
                    help="file of timestamps (seconds, ORIGINAL timeline) where --impact-file "
                         "is dropped. Overrides --impact-every. Use to hit narration reveals.")
    ap.add_argument("--speed", type=float, default=1.1,
                    help="pitch-preserving tempo (1.0 = no change). default 1.1")
    ap.add_argument("--punch", type=float, default=0.06,
                    help="zoom-in fraction on punched beats (0 = no zoom pulse at all). default 0.06")
    ap.add_argument("--punch-every", type=int, default=2,
                    help="punch one beat out of every N (rest stay flat). 2 = alternate (legacy). "
                         "Higher = rarer, calmer zoom pulse. default 2")
    ap.add_argument("--sfx-dir", type=Path, default=Path("assets/sound_effects"))
    ap.add_argument("--cut-sfx", type=str, default=None,
                    help="scene-matched cut sound(s): a directory of audio files, OR a "
                         "comma-separated list of files (paths, or relative to --sfx-dir). "
                         "Overrides the default whooshes. Rotated per cut. "
                         "Use to stop defaulting to swooshes (e.g. UI clicks for tech, "
                         "risers for tension, glass for shatter beats).")
    ap.add_argument("--whoosh-gain", type=float, default=0.5)
    ap.add_argument("--sfx-every", type=int, default=1,
                    help="place a cut whoosh only on every Nth cut (1 = every cut). "
                         "Higher = sparser, less 'whoosh on every cut'. default 1")
    ap.add_argument("--lead", type=float, default=0.18,
                    help="start each whoosh this many secs before its cut. default 0.18")
    ap.add_argument("--impact-file", type=Path, default=None,
                    help="optional impact sfx, dropped on every --impact-every'th cut")
    ap.add_argument("--impact-every", type=int, default=4)
    ap.add_argument("--impact-gain", type=float, default=0.6)
    ap.add_argument("--no-swell", action="store_true", help="skip the intro swell")
    ap.add_argument("--no-sfx", action="store_true", help="skip all sound effects")
    ap.add_argument("--keep-work", action="store_true")
    # --- optional split-screen gameplay final stage (see stack_gameplay.py) ---
    ap.add_argument("--gameplay-dir", type=Path, default=None,
                    help="if set, run the split-screen final stage once the recut is done: "
                         "stack the finished short on TOP and a RANDOM, MUTED clip from this "
                         "folder (e.g. downloads/gta5-gameplay) on the bottom, as one 9:16 "
                         "video. Writes <out_stem>_gameplay.mp4 alongside the recut.")
    ap.add_argument("--gameplay-split", type=float, default=0.5,
                    help="height fraction for the TOP (your) video in the stack. default 0.5")
    ap.add_argument("--gameplay-fit", choices=["blur", "pad", "crop"], default="blur",
                    help="how the short fills the top half: blur=whole+blurred fill "
                         "(caption-safe, default), pad=black bars, crop=cover-crop (CUTS "
                         "lower-third captions). default blur")
    ap.add_argument("--gameplay-seed", type=int, default=None,
                    help="RNG seed for reproducible gameplay clip/start choice")
    args = ap.parse_args()

    inp = args.input.resolve()
    if not inp.exists():
        print(f"ERROR: input not found: {inp}", file=sys.stderr)
        return 2
    out = (args.out or inp.with_name(inp.stem + "_punchy.mp4")).resolve()
    work = out.with_name(out.stem + "_work")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    info = probe(inp)
    W, H, FPS = info["w"], info["h"], info["fps"]
    speed = max(0.5, min(2.0, args.speed))  # atempo single-stage range
    print(f"[1/4] input {W}x{H}@{FPS} {info['duration']:.2f}s -> speed x{speed}")

    # --- 1. global pitch-preserving speed-up --------------------------------
    sped = work / "sped.mp4"
    run([
        "ffmpeg", "-hide_banner", "-y", "-i", inp,
        "-filter:v", f"setpts=PTS/{speed}",
        "-filter:a", f"atempo={speed}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", sped,
    ])
    dur = info["duration"] / speed

    def read_times(path: Path) -> list[float]:
        vals = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                vals.append(float(line))
        return vals

    # --- 2. fast-cut the VIDEO (alternating zoom-punch per beat) -------------
    if args.cuts_file and args.cuts_file.exists():
        # explicit cut points given in ORIGINAL timeline -> map into sped timeline
        pts = sorted({round(t / speed, 3) for t in read_times(args.cuts_file)
                      if 0.05 < t / speed < dur - 0.05})
        bounds = [0.0] + pts + [dur]
        n = len(bounds) - 1
    else:
        n = max(2, math.floor(dur / args.interval))
        bounds = [round(k * args.interval, 3) for k in range(n)] + [dur]
    z = 1.0 + max(0.0, args.punch)
    base = f"setsar=1,fps={FPS},format=yuv420p"
    punch_vf = f"crop=iw/{z}:ih/{z},scale={W}:{H},{base}"
    flat_vf = f"scale={W}:{H},{base}"
    pe = max(1, args.punch_every)
    do_punch = args.punch > 0.0
    print(f"[2/4] {n} beats @ {args.interval}s, zoom-punch x{z:.3f} "
          f"({'off' if not do_punch else f'1 in {pe}'})")

    segs = []
    for i in range(n):
        start, end = bounds[i], bounds[i + 1]
        seg = work / f"seg_{i:03d}.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-y", "-i", sped, "-ss", f"{start:.3f}"]
        if i < n - 1:
            cmd += ["-t", f"{end - start:.3f}"]
        punched = do_punch and (i % pe == pe - 1)
        cmd += ["-an", "-vf", (punch_vf if punched else flat_vf),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", seg]
        run(cmd)
        segs.append(seg)

    concat = work / "concat.txt"
    concat.write_text("".join(f"file '{s.name}'\n" for s in segs), encoding="utf-8")
    cut_video = work / "cut_video.mp4"
    run(["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0",
         "-i", concat.name, "-c", "copy", cut_video.name], cwd=work)

    # --- 3. build the SFX bed -----------------------------------------------
    sfx_bed = None
    if not args.no_sfx:
        cuts = [bounds[k] for k in range(1, n)]  # interior boundaries = the cuts
        placements = []  # (file_path, delay_seconds, gain)
        AUDIO_EXT = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aif", ".aiff"}
        if args.cut_sfx:
            cand = Path(args.cut_sfx)
            if cand.is_dir():
                whooshes = sorted(p for p in cand.iterdir()
                                  if p.suffix.lower() in AUDIO_EXT)
            else:
                whooshes = []
                for part in args.cut_sfx.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    p = Path(part)
                    if not p.exists():
                        p = args.sfx_dir / part
                    whooshes.append(p)
            whooshes = [w for w in whooshes if w.exists()]
            if whooshes:
                print(f"  cut-sfx: {len(whooshes)} scene-matched sound(s)")
        else:
            whooshes = [args.sfx_dir / w for w in DEFAULT_WHOOSHES]
            whooshes = [w for w in whooshes if w.exists()]
        if not args.no_swell:
            sw = args.sfx_dir / DEFAULT_SWELL
            if sw.exists():
                placements.append((sw, 0.0, args.whoosh_gain * 0.8))
        if whooshes:
            se = max(1, args.sfx_every)
            for j, t in enumerate(cuts):
                if j % se == 0:
                    placements.append((whooshes[(j // se) % len(whooshes)],
                                       max(0.0, t - args.lead), args.whoosh_gain))
                if args.impact_file and args.impact_file.exists() \
                        and not args.impact_at_file \
                        and (j + 1) % args.impact_every == 0:
                    placements.append((args.impact_file, max(0.0, t - args.lead),
                                       args.impact_gain))
        else:
            print("  WARN: no whoosh files found under --sfx-dir; skipping SFX")
        # explicit impacts on narration reveals (original timeline -> sped)
        if args.impact_file and args.impact_file.exists() \
                and args.impact_at_file and args.impact_at_file.exists():
            hits = [t / speed for t in read_times(args.impact_at_file)]
            for ts in hits:
                if 0.0 <= ts < dur:
                    placements.append((args.impact_file, max(0.0, ts - args.lead),
                                       args.impact_gain))
            print(f"  + {len([h for h in hits if 0 <= h < dur])} reveal impacts")

        if placements:
            sfx_bed = work / "sfx_bed.wav"
            cmd = ["ffmpeg", "-hide_banner", "-y",
                   "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={dur:.3f}"]
            for f, _, _ in placements:
                cmd += ["-i", str(f)]
            parts, labels = [], ["[0:a]"]
            for k, (_, delay, gain) in enumerate(placements, start=1):
                ms = int(round(delay * 1000))
                parts.append(f"[{k}:a]aformat=channel_layouts=stereo,"
                             f"adelay={ms}|{ms},volume={gain}[s{k}]")
                labels.append(f"[s{k}]")
            fc = ";".join(parts) + ";" + "".join(labels) + \
                 f"amix=inputs={len(placements)+1}:normalize=0[mix]"
            cmd += ["-filter_complex", fc, "-map", "[mix]",
                    "-t", f"{dur:.3f}", "-ar", "48000", "-ac", "2", sfx_bed]
            run(cmd)
            print(f"[3/4] SFX bed: {len(placements)} hits")
    if sfx_bed is None:
        print("[3/4] SFX skipped")

    # --- 4. final mux: cut video + narration (+ sfx) ------------------------
    cmd = ["ffmpeg", "-hide_banner", "-y", "-i", cut_video, "-i", sped]
    if sfx_bed is not None:
        cmd += ["-i", sfx_bed,
                "-filter_complex",
                "[1:a]volume=1.0[narr];[2:a]volume=1.0[sfx];"
                "[narr][sfx]amix=inputs=2:normalize=0:duration=first[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{dur:.3f}", "-movflags", "+faststart", out]
    run(cmd)
    print(f"[4/4] wrote {out}  ({dur:.2f}s)")

    # --- optional final stage: stack a random muted gameplay clip below -------
    if args.gameplay_dir:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from stack_gameplay import build_stack
        stacked = out.with_name(out.stem + "_gameplay.mp4")
        print("[5/5] split-screen gameplay stage")
        build_stack(out, args.gameplay_dir, stacked,
                    split=args.gameplay_split, top_fit=args.gameplay_fit,
                    seed=args.gameplay_seed)

    if not args.keep_work:
        shutil.rmtree(work)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

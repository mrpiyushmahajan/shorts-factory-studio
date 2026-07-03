"""
Synthesize a small SFX library with ffmpeg — whooshes, impacts, riser, pop.
100% generated, zero licensing issues. Run once: python3 make_sfx.py
"""
import subprocess
from pathlib import Path

SFX_DIR = Path(__file__).parent / "assets" / "sfx"


def _run(args):
    subprocess.run(["ffmpeg", "-y", *args], check=True, capture_output=True)


def make_whoosh(out: Path, dur=0.5, f_start=200, f_end=4000, vol=0.9):
    """Filtered noise sweep = whoosh."""
    _run([
        "-f", "lavfi",
        "-i", f"anoisesrc=color=pink:duration={dur}:amplitude=0.8",
        "-af",
        f"bandpass=f={f_start}:width_type=o:w=2,"
        f"afade=t=in:d={dur*0.35},afade=t=out:st={dur*0.4}:d={dur*0.6},"
        f"volume={vol}",
        str(out),
    ])


def make_impact(out: Path, freq=55, dur=0.45):
    """Low sine thump with fast decay = impact."""
    _run([
        "-f", "lavfi",
        "-i", f"sine=frequency={freq}:duration={dur}",
        "-af",
        f"afade=t=out:st=0.03:d={dur-0.03},volume=1.4,"
        "aecho=0.6:0.4:40:0.3",
        str(out),
    ])


def make_riser(out: Path, dur=1.2):
    """Rising filtered noise = tension riser for the hook."""
    _run([
        "-f", "lavfi",
        "-i", f"anoisesrc=color=brown:duration={dur}:amplitude=0.7",
        "-af",
        "highpass=f=100,lowpass=f=3000,"
        f"afade=t=in:d={dur*0.8},afade=t=out:st={dur*0.85}:d={dur*0.15},"
        "volume=0.8",
        str(out),
    ])


def make_pop(out: Path):
    """Short click-pop for text reveals."""
    _run([
        "-f", "lavfi",
        "-i", "sine=frequency=900:duration=0.09",
        "-af", "afade=t=out:st=0.01:d=0.08,volume=0.7",
        str(out),
    ])


def main():
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    print("🔊 Synthesizing SFX library...")

    # variety of whooshes (different sweeps/lengths → rotate per cut)
    make_whoosh(SFX_DIR / "whoosh_01.wav", dur=0.45, f_start=300)
    make_whoosh(SFX_DIR / "whoosh_02.wav", dur=0.60, f_start=150)
    make_whoosh(SFX_DIR / "whoosh_03.wav", dur=0.35, f_start=600)
    make_whoosh(SFX_DIR / "whoosh_04.wav", dur=0.50, f_start=250)

    make_impact(SFX_DIR / "impact_01.wav", freq=50)
    make_impact(SFX_DIR / "impact_02.wav", freq=70, dur=0.35)

    make_riser(SFX_DIR / "riser_01.wav")
    make_pop(SFX_DIR / "pop_01.wav")

    files = sorted(SFX_DIR.glob("*.wav"))
    print(f"✅ {len(files)} SFX files in {SFX_DIR}")
    for f in files:
        print(f"   {f.name}")


if __name__ == "__main__":
    main()

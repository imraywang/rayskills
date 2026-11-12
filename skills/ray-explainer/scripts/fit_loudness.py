#!/usr/bin/env python3
"""Bring a rendered film to the target loudness without touching the picture.

usage: python3 fit_loudness.py <video.mp4> [--lufs -21] [--tol 1.0]

Measures integrated loudness (ffmpeg ebur128). When it is more than --tol LU away from the target, applies one
constant gain to the audio (video stream copied) and replaces the file; otherwise leaves it alone. A constant gain,
not loudnorm: the mix (voice over music, sfx) keeps its balance and dynamics.
2026-11-12: `hyperframes render` 0.9.39 delivered a film at -18.5 LUFS with the peak at exactly -1.0 dBFS although the
narration went in at -21.5 LUFS; qa_video.py failed the loudness check and the gain was applied by hand.
"""
import os, re, subprocess, sys

args = sys.argv[1:]
if not args or args[0].startswith("-"): sys.exit(__doc__)
SRC = os.path.abspath(args[0])
TARGET = float(args[args.index("--lufs") + 1]) if "--lufs" in args else -21.0
TOL = float(args[args.index("--tol") + 1]) if "--tol" in args else 1.0


def lufs(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?\d+(?:\.\d+)?) LUFS", err)
    if not m: sys.exit(f"could not measure loudness of {path}")
    return float(m[-1])


now = lufs(SRC)
if abs(now - TARGET) <= TOL:
    print(f"{os.path.basename(SRC)}: {now:.1f} LUFS, within {TOL} LU of {TARGET} — unchanged"); sys.exit(0)
gain = TARGET - now
tmp = SRC + ".loud.mp4"
r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", SRC, "-c:v", "copy", "-af", f"volume={gain:.2f}dB",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], capture_output=True, text=True)
if r.returncode: sys.exit(f"ffmpeg failed: {r.stderr.strip()[-300:]}")
after = lufs(tmp)
os.replace(tmp, SRC)
print(f"{os.path.basename(SRC)}: {now:.1f} → {after:.1f} LUFS (gain {gain:+.1f} dB, picture untouched)")

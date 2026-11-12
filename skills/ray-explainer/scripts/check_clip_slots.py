#!/usr/bin/env python3
"""Find video clips that end before their slot on the timeline (they freeze on the last frame: looks like a stutter).
usage: python3 check_clip_slots.py <hf project>/index.html
Reads every <video ... src data-media-start data-duration> in index.html AND in the scene files next to it
(compositions/*.html — in a film built from sub-compositions that is where the videos are; until 2026-11-12 this
script read index.html only and answered "0 short clip(s) of 0 videos" for such a film), probes the file and prints
the ones short by more than 0.1 s. A clip's need is data-duration × data-playback-rate (default 1).
Exit 1 when any clip is short. 2026-10-25 (国内AI产业链): five shots were 0.2–1.3 s short; Ray saw it as a stutter at 1:20."""
import os, re, subprocess, sys

html_path = sys.argv[1]
root = os.path.dirname(os.path.abspath(html_path))
import glob
files = [html_path] + sorted(glob.glob(os.path.join(root, "compositions", "*.html")))
lengths, short, total = {}, [], 0
for f, tag in ((f, t) for f in files for t in re.findall(r"<video\b[^>]*>", open(f, encoding="utf-8").read())):
    a = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
    if "src" not in a or "data-duration" not in a: continue
    total += 1
    src = os.path.join(root, a["src"])
    if src not in lengths:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
        lengths[src] = float(out) if out else 0.0
    have = lengths[src] - float(a.get("data-media-start", 0) or 0)
    need = float(a["data-duration"]) * float(a.get("data-playback-rate", 1) or 1)
    if have < need - 0.1:   # 3 frames; HeyGen clips run a hair short
        short.append((os.path.basename(f), float(a.get("data-start", 0)), a["src"], need, have))
for f, st, src, need, have in sorted(short):
    print(f"{f:22s} {st:7.2f}s  {src:32s} needs {need:5.2f}s of clip, has {have:5.2f}s  short by {need - have:.2f}s")
print(f"{len(short)} short clip(s) of {total} videos in {len(files)} file(s)")
sys.exit(1 if short else 0)

#!/usr/bin/env python3
"""Find video clips that end before their slot on the timeline (they freeze on the last frame: looks like a stutter).
usage: python3 check_clip_slots.py <hf project>/index.html
Reads every <video ... src data-media-start data-duration>, probes the file and prints the ones short by more than 0.1 s.
Exit 1 when any clip is short. 2026-10-25 (国内AI产业链): five shots were 0.2–1.3 s short; Ray saw it as a stutter at 1:20."""
import os, re, subprocess, sys

html_path = sys.argv[1]
root = os.path.dirname(os.path.abspath(html_path))
html = open(html_path, encoding="utf-8").read()
lengths, short = {}, []
for tag in re.findall(r"<video\b[^>]*>", html):
    a = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
    if "src" not in a or "data-duration" not in a: continue
    src = os.path.join(root, a["src"])
    if src not in lengths:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
        lengths[src] = float(out) if out else 0.0
    have = lengths[src] - float(a.get("data-media-start", 0) or 0)
    need = float(a["data-duration"])
    if have < need - 0.1:   # 3 frames; HeyGen clips run a hair short
        short.append((float(a.get("data-start", 0)), a["src"], need, have))
for st, src, need, have in sorted(short):
    print(f"{st:7.2f}s  {src:32s} on screen {need:5.2f}s  clip {have:5.2f}s  short by {need - have:.2f}s")
print(f"{len(short)} short clip(s) of {sum(1 for t in re.findall(r'<video', html))} videos")
sys.exit(1 if short else 0)

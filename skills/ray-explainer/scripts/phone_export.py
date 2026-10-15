"""Phone copy of the film that fits SendUserFile's 30 MB limit (phone / web clients can't open bigger files).

usage: python3 phone_export.py <project> [-i out.mp4] [-o out_phone.mp4] [--max-mb 28]

Bitrate comes from the duration (720 px wide, two-pass x264, AAC 96k), so a 4-minute film no longer lands at
30.4 MB the way a fixed 900k did. If the result is still over --max-mb (MiB) it re-encodes 8 % lower, up to 3 times.
"""
import argparse, os, subprocess, sys, tempfile

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("-i", default="out.mp4"); ap.add_argument("-o", default="out_phone.mp4")
ap.add_argument("--max-mb", type=float, default=28.0)
a = ap.parse_args()
PROJ = os.path.abspath(a.project); src = os.path.join(PROJ, a.i); out = os.path.join(PROJ, a.o)
if not os.path.exists(src): sys.exit(f"no {src}")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
limit = a.max_mb * 1024 * 1024
AUDIO_K = 96
vk = int((limit * 8 * 0.96 / dur) / 1000 - AUDIO_K)        # 4 % container overhead
vk = min(vk, 2500)                                        # 720p doesn't need more
for attempt in range(4):
    if vk < 300: sys.exit(f"film too long for {a.max_mb} MB at a watchable bitrate ({vk}k)")
    log = os.path.join(tempfile.mkdtemp(), "x264")
    common = ["-vf", "scale=720:-2", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{vk}k", "-maxrate", f"{int(vk * 1.25)}k", "-bufsize", f"{vk * 2}k", "-passlogfile", log]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, *common, "-pass", "1", "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, *common, "-pass", "2", "-c:a", "aac", "-b:a", f"{AUDIO_K}k", "-movflags", "+faststart", out], check=True)
    size = os.path.getsize(out)
    print(f"{os.path.basename(out)}  {dur:.0f}s  video {vk}k  → {size / 1024 / 1024:.1f} MB")
    if size <= limit: break
    vk = int(vk * 0.92)
else:
    sys.exit("still over the limit")

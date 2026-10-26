#!/usr/bin/env python3
"""On-camera lines with Ray's HeyGen digital twin, lip-synced to the narration we already have (Eleven / MiniMax / VoxCPM).
usage:
  python3 heygen_host.py <project> --lines h0=hook.5 c1=st1_ipo.3-st1_ipo.5 ... [--matte h0] [--look <look id>] [--dry-run]
Each NAME=FIRST[-LAST] takes the narration slice of those timeline lines (timeline.json, 1-based like build.py anchors),
uploads it, renders 1080p 16:9 with engine avatar_v and a blink/nod motion prompt, and saves host/<NAME>.mp4 (+ the slice
in host/plan.json: start/end seconds, which the page uses as data-media-start offset). --matte NAME also runs HeyGen
background removal and saves host/<NAME>-foreground.webm (alpha) for text behind the head.
Needs the heygen CLI signed in (`heygen auth login --oauth`). Cost ≈ 0.8–1 premium credit per second, matte 1 credit;
--dry-run prints the seconds first. Details and look ids: references/host.md「HeyGen」."""
import argparse, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

LOOK = "91d5d799b91ac3b46da41d991cb544db"   # 「Ray - dark finance studio」, 2026-10-25
MOTION = ("Natural, relaxed presenter. He blinks naturally every 2 to 4 seconds throughout, including while speaking. "
          "Subtle head nods and small head tilts on emphasis, calm shoulders, occasional slight eyebrow raise. Hands stay out of frame.")

ap = argparse.ArgumentParser()
ap.add_argument("project"); ap.add_argument("--lines", nargs="+", required=True)
ap.add_argument("--matte", nargs="*", default=[]); ap.add_argument("--look", default=LOOK); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
P = os.path.abspath(a.project); H = os.path.join(P, "host"); os.makedirs(H, exist_ok=True)
tl = json.load(open(os.path.join(P, "timeline.json")))
L = {f"{s['id']}.{i}": l for s in tl["scenes"] for i, l in enumerate(s["lines"], 1)}
plan_p = os.path.join(H, "plan.json"); plan = json.load(open(plan_p)) if os.path.exists(plan_p) else {}

def heygen(*args, data=None):
    cmd = ["heygen", *args] + (["-d", json.dumps(data)] if data else [])
    out = subprocess.run(cmd, capture_output=True, text=True)
    try: return json.loads(out.stdout)
    except Exception: sys.exit(f"heygen {' '.join(args)} failed: {out.stdout[:300]} {out.stderr[:300]}")

jobs = []
for spec in a.lines:
    name, rng = spec.split("="); first, _, last = rng.partition("-")
    s, e = L[first]["start"], L[last or first]["end"]
    jobs.append((name, round(s, 3), round(e, 3)))
print("\n".join(f"{n}: {s:.2f}-{e:.2f}s ({e - s:.1f}s)" for n, s, e in jobs), f"\ntotal {sum(e - s for _, s, e in jobs):.1f}s ≈ credits")
if a.dry_run: sys.exit(0)

def make(job):
    name, s, e = job
    mp3 = os.path.join(H, f"{name}.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s), "-to", str(e), "-i", os.path.join(P, "narration.wav"), "-c:a", "libmp3lame", "-b:a", "192k", mp3], check=True)
    aid = heygen("asset", "create", "--file", mp3)["data"]["asset_id"]
    v = heygen("video", "create", "--wait", "--timeout", "25m", data={"type": "avatar", "avatar_id": a.look, "audio_asset_id": aid,
        "engine": {"type": "avatar_v"}, "motion_prompt": MOTION, "resolution": "1080p", "aspect_ratio": "16:9", "title": f"{os.path.basename(P)} {name}"})["data"]
    subprocess.run(["heygen", "video", "download", v["id"]], cwd=H, capture_output=True, check=True)
    os.replace(os.path.join(H, f"{v['id']}.mp4"), os.path.join(H, f"{name}.mp4"))
    if name in a.matte:
        vid = heygen("asset", "create", "--file", os.path.join(H, f"{name}.mp4"))["data"]["asset_id"]
        job_id = heygen("background-removal", "create", data={"video": {"type": "asset_id", "asset_id": vid}, "layers": ["foreground"]})["data"]["id"]
        while (r := heygen("background-removal", "get", job_id)["data"])["status"] not in ("completed", "failed"): time.sleep(10)
        url = r["layers"]["foreground"]; url = url if isinstance(url, str) else url.get("url")
        subprocess.run(["curl", "-sL", "-o", os.path.join(H, f"{name}-foreground.webm"), url], check=True)
    return name, s, e

with ThreadPoolExecutor(5) as ex:
    for name, s, e in ex.map(make, jobs):
        plan[name] = {"start": s, "end": e}; print(name, "done")
json.dump(plan, open(plan_p, "w"), indent=1)
print(heygen("user", "me", "get")["data"]["subscription"]["credits"])

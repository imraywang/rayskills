#!/usr/bin/env python3
"""Open a render on the review page (review_page.py): Ray plays it on a scene timeline, comments on any frame and
clicks 发送. The notes (time, scene, words being said, a still of the frame) go to review/feedback-<video>.md and are
printed; then the script exits. Run it in the background and read the notes when it returns.

usage:
  python3 review.py <video> [--scenes scenes.json | --timeline timeline.json] [--tailnet] [--no-open] [--port 8791]

Scene bands, first that exists:
  --scenes FILE, or scenes.json next to the video / in its project (written by the style templates' build.py):
      [{"id": "s01", "start": 0, "end": 6.8, "label": "画板", "visual": "冰的手机画面", "spoken": "你现在看到..."}]
  --timeline FILE, or timeline.json in the project (ray-explainer narration timeline): one band per scene
  otherwise: ffmpeg scene-change detection (bands without words)
--tailnet also opens the page on this Mac's Tailscale address, for review on Ray's phone.
After the first round pass --no-open: the open page reloads itself when the video file changes."""
import argparse, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_page import probe, serve, write_page


def find_up(start, name, levels=3):
    d = start
    for _ in range(levels):
        for p in (os.path.join(d, name), os.path.join(d, "hf", name), os.path.join(d, "src", name)):
            if os.path.isfile(p):
                return p
        d = os.path.dirname(d)
    return None


def from_timeline(path, dur):
    tl = json.load(open(path))
    scenes = []
    for sc in tl["scenes"]:
        lines = sc.get("lines") or []
        if not lines:
            continue
        scenes.append({"id": sc["id"], "start": lines[0]["start"], "label": sc["id"],
                       "spoken": "".join(l.get("text", "") for l in lines)})
    for i, s in enumerate(scenes):
        s["start"] = 0.0 if i == 0 else s["start"]
        s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else dur
    return scenes


def from_cuts(video, dur):
    err = subprocess.run(["ffmpeg", "-i", video, "-vf", "scale=320:-2,select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    cuts = [float(t) for t in re.findall(r"pts_time:([\d.]+)", err)]
    marks = [0.0] + [t for t in cuts if t > 0.5] + [dur]
    marks = [t for i, t in enumerate(marks) if i == 0 or t - marks[i - 1] > 0.8 or t == dur]
    return [{"id": f"s{i + 1:02d}", "start": a, "end": b, "spoken": ""} for i, (a, b) in enumerate(zip(marks, marks[1:]))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--scenes")
    ap.add_argument("--timeline")
    ap.add_argument("--tailnet", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--timeout", type=int, default=7200)
    a = ap.parse_args()
    video = os.path.abspath(a.video)
    root = os.path.dirname(video)
    dur, _ = probe(video)
    scenes_file = a.scenes or (None if a.timeline else find_up(root, "scenes.json"))
    if scenes_file:
        scenes = json.load(open(scenes_file))
        src = scenes_file
    else:
        tl = a.timeline or find_up(root, "timeline.json")
        scenes, src = (from_timeline(tl, dur), tl) if tl else (from_cuts(video, dur), "镜头检测")
    scenes = [s for s in scenes if s["end"] > s["start"]]
    if scenes:
        scenes[-1]["end"] = max(scenes[-1]["end"], dur)
    print(f"场景 {len(scenes)} 段，来自 {src}", flush=True)
    stem = os.path.splitext(os.path.basename(video))[0]
    page = os.path.join(root, ".review", "index.html")
    write_page(root, page, video, scenes)
    os.makedirs(os.path.join(root, "review"), exist_ok=True)
    serve(root, page, os.path.join(root, "review", f"feedback-{stem}.md"), scenes, video, a.port,
          not a.no_open, a.timeout, tailnet=a.tailnet)


if __name__ == "__main__":
    main()

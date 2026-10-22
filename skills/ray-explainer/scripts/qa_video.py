#!/usr/bin/env python3
"""Measure a finished render and export frames to look at, before Ray sees it.
Idea and checks from Peter Yang's video-short qa.py (MIT, https://github.com/petergyang/video-short), adapted.

usage: python3 qa_video.py <video> [--scenes scenes.json | --timeline timeline.json] [--lufs -21] [--out DIR]

Hard checks (exit 1 if any fails):
  audio stream present · audio and video lengths within 2 frames · integrated loudness within ±1.5 LU of --lufs
  (−21 for explainers, −14 for the course videos) · true peak ≤ −1 dBFS · no black gap (blackdetect ≥ 0.1 s)
Reported only: size, frame rate, frozen stretches ≥ 2 s (a still board can be intended; check them).
Frames, in qa/<video name>/ next to the video:
  contact.jpg   the whole video, 1 frame every 1–2 s
  opening.jpg   the first 3 s at 6 fps (is the hook already on screen?)
  cuts/*.jpg    10 frames around every scene change (5 before, 5 after): jumps, flashes, a frame of the wrong shot
Scenes come from the same places as review.py (scenes.json, timeline.json, else scene detection)."""
import argparse, glob, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review import find_up, from_cuts, from_timeline


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", *args], capture_output=True, text=True).stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--scenes")
    ap.add_argument("--timeline")
    ap.add_argument("--lufs", type=float, default=-21.0)
    ap.add_argument("--out")
    a = ap.parse_args()
    video = os.path.abspath(a.video)
    root = os.path.dirname(video)
    out = a.out or os.path.join(root, "qa", os.path.splitext(os.path.basename(video))[0])
    os.makedirs(os.path.join(out, "cuts"), exist_ok=True)
    for f in glob.glob(os.path.join(out, "cuts", "*.jpg")):
        os.remove(f)

    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                      "stream=codec_type,width,height,r_frame_rate,duration", "-of", "json", video],
                                     capture_output=True, text=True).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    n, d = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = n / d
    vdur = float(v.get("duration") or 0)
    adur = float(au.get("duration") or 0) if au else 0.0

    err = ff(["-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"])
    lufs = re.findall(r"I:\s+(-?[\d.]+)\s+LUFS", err)
    peak = re.findall(r"Peak:\s+(-?[\d.]+)\s+dBFS", err)
    lufs = float(lufs[-1]) if lufs else None
    peak = float(peak[-1]) if peak else None
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)",
                        ff(["-i", video, "-vf", "blackdetect=d=0.1:pix_th=0.04", "-an", "-f", "null", "-"]))
    frozen = re.findall(r"freeze_start: ([\d.]+)[\s\S]*?freeze_end: ([\d.]+)",
                        ff(["-i", video, "-vf", "scale=480:-2,freezedetect=n=-60dB:d=2", "-an", "-f", "null", "-"]))

    hard = [
        ("有音轨", au is not None, "有" if au else "没有音轨"),
        ("音画长度一致（2 帧内）", au is not None and abs(vdur - adur) <= 2 / fps, f"画面 {vdur:.3f}s，声音 {adur:.3f}s"),
        (f"响度在 {a.lufs:g} ±1.5 LUFS", lufs is not None and abs(lufs - a.lufs) <= 1.5, f"{lufs} LUFS"),
        ("峰值 ≤ −1 dBFS", peak is not None and peak <= -1.0, f"{peak} dBFS"),
        ("没有黑场", not blacks, "、".join(f"{float(s):.2f}–{float(e):.2f}s" for s, e in blacks) or "无"),
    ]
    info_rows = [
        ("尺寸", f"{v['width']}×{v['height']}"), ("帧率", f"{fps:g} fps"),
        ("静止 ≥ 2 秒的段落（可能是有意的，看一眼）", "、".join(f"{float(s):.1f}–{float(e):.1f}s" for s, e in frozen) or "无"),
    ]

    step = 1 if vdur <= 120 else 2
    cols = 10
    ff(["-y", "-i", video, "-vf", f"fps=1/{step},scale=192:-2,tile={cols}x{int(vdur / step / cols) + 1}",
        "-frames:v", "1", os.path.join(out, "contact.jpg")])
    ff(["-y", "-t", "3", "-i", video, "-vf", "fps=6,scale=320:-2,tile=6x3", "-frames:v", "1", os.path.join(out, "opening.jpg")])

    scenes_file = a.scenes or (None if a.timeline else find_up(root, "scenes.json"))
    if scenes_file:
        scenes = json.load(open(scenes_file))
    else:
        tl = a.timeline or find_up(root, "timeline.json")
        scenes = from_timeline(tl, vdur) if tl else from_cuts(video, vdur)
    for s in scenes[1:]:
        t = max(0.0, s["start"] - 5 / fps)
        ff(["-y", "-ss", f"{t:.3f}", "-i", video, "-vf", "scale=192:-2,tile=10x1", "-frames:v", "1",
            os.path.join(out, "cuts", f"{s['id']}_{s['start']:.2f}.jpg")])

    lines = [f"# 成片检查：{os.path.basename(video)}", ""]
    lines += [f"- [{'x' if ok else ' '}] {name}：{detail}" for name, ok, detail in hard]
    lines += [f"- {name}：{detail}" for name, detail in info_rows]
    lines += ["", f"再用 Read 看 contact.jpg、opening.jpg 和 cuts/ 下 {len(scenes) - 1} 张切点图（每张是切点前后各 5 帧）。"]
    open(os.path.join(out, "report.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n文件在 {out}")
    sys.exit(0 if all(ok for _, ok, _ in hard) else 1)


if __name__ == "__main__":
    main()

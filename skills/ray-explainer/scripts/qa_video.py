#!/usr/bin/env python3
"""Measure a finished render and export frames to look at, before Ray sees it. One command after every render.
Idea and the frame exports from Peter Yang's video-short qa.py (MIT, https://github.com/petergyang/video-short); the
blank-frame and blue/purple checks are the two parts of film_gate.py (huashu-art-motion, MIT) that proved useful on
Ray's films. film_gate's motion metrics are gone: Ray 10-16 and 10-22, our films are mostly real footage, so "fast
motion ratio" and the other twenty readings never changed a film (red on 12 of 15 films, none fixed for it).

usage: python3 qa_video.py <video> [--scenes scenes.json | --timeline timeline.json] [--lufs -21] [--out DIR]
                           [--allow-blue-purple 理由]

Hard checks (exit 1 if any fails):
  audio stream · audio and video lengths within 2 frames · loudness within ±1.5 LU of --lufs (−21 explainers,
  −14 course videos) · true peak ≤ −1 dBFS · no black gap (blackdetect ≥ 0.1 s)
  no blank frames mid-film: ≥ 0.3 s where almost nothing has an edge (gradient > 24 on < 0.2 % of pixels, caption
    band and the frames next to cuts ignored) — a flat colour screen, black or not
  blue/purple background < 30 % of the film (hue 225–300°, sat ≥ 0.30: the AI-slop palette); 12–30 % is noted.
    A topic that needs it (cyberpunk purple, Starry Night): --allow-blue-purple "理由" turns it into a note.
Reported, to look at:
  stretches ≥ 3 s with no visible change (ffmpeg freezedetect at −35 dB, so a uniform slow push of a few percent
  counts as still: it is not motion). On 10-13 this kind of reading took a scene from 12 s to 6 s without change.
Frames, in qa/<video name>/ next to the video:
  contact.jpg   the whole video, 1 frame every 1–2 s
  opening.jpg   the first 3 s at 6 fps (is the hook already on screen?)
  cuts/*.jpg    10 frames around every scene change (5 before, 5 after): jumps, flashes, a frame of the wrong shot
Scenes come from the same places as review.py (scenes.json, timeline.json, else scene detection)."""
import argparse, glob, json, os, re, subprocess, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review import find_up, from_cuts, from_timeline


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", *args], capture_output=True, text=True).stderr


def gray_frames(video, w, h, fps=12, width=320):
    hh = int(round(h * width / w / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={width}:{hh}:flags=area",
                          "-pix_fmt", "gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (width * hh)
    return np.frombuffer(raw[:n * width * hh], np.uint8).reshape(n, hh, width).astype(np.float32)


def blank_runs(F, fps=12, sub_band=0.15, grad=24.0, frac=0.002, edge_s=0.5, min_s=0.3):
    """Mid-film stretches where a frame has almost no edges (film_gate.blank_frames, Sobel in numpy)."""
    n = len(F)
    if n < 3:
        return []
    G = F[:, : int(F.shape[1] * (1 - sub_band))]            # leave the caption band out
    p = np.pad(G, ((0, 0), (1, 1), (1, 1)), mode="edge")
    gx = (p[:, :-2, 2:] + 2 * p[:, 1:-1, 2:] + p[:, 2:, 2:]) - (p[:, :-2, :-2] + 2 * p[:, 1:-1, :-2] + p[:, 2:, :-2])
    gy = (p[:, 2:, :-2] + 2 * p[:, 2:, 1:-1] + p[:, 2:, 2:]) - (p[:, :-2, :-2] + 2 * p[:, :-2, 1:-1] + p[:, :-2, 2:])
    blank = (np.hypot(gx, gy) > grad).reshape(n, -1).mean(1) < frac
    d = np.abs(np.diff(G, axis=0)).reshape(n - 1, -1).mean(1)
    ok = np.ones(n, bool)
    e = int(round(edge_s * fps)); ok[:e] = False; ok[max(0, n - e):] = False
    for i in range(n - 1):                                   # frames next to a cut don't count (film_gate cut_like)
        nb = np.concatenate([d[max(0, i - 6):i], d[i + 1:min(n - 1, i + 7)]])
        if d[i] >= max(8.0, 3 * (np.median(nb) if len(nb) else 0) + 2):
            ok[i] = ok[i + 1] = False
    runs, s0 = [], None
    for i, v in enumerate(list(blank & ok) + [False]):
        if v and s0 is None:
            s0 = i
        elif not v and s0 is not None:
            if (i - s0) / fps >= min_s - 1e-9:
                runs.append((round(s0 / fps, 2), round(i / fps, 2)))
            s0 = None
    return runs


def blue_purple(video, w, h, fps=2, width=160):
    """Share of frames whose pixels are ≥ 30 % blue/purple (hue 225–300°, sat ≥ 0.30, value 0.06–0.90), and spans."""
    hh = max(2, int(round(h * width / w / 2)) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={width}:{hh}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, hh, width, 3).astype(np.float32) / 255
    if not len(F):
        return 0.0, []
    r, g, b = F[..., 0], F[..., 1], F[..., 2]
    mx, mn = F.max(-1), F.min(-1); dd = mx - mn + 1e-6
    hue = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60
    m = (hue >= 225) & (hue <= 300) & (dd / (mx + 1e-6) >= 0.30) & (mx >= 0.06) & (mx <= 0.90)
    bad = m.reshape(len(F), -1).mean(1) >= 0.30
    spans, st = [], None
    for i, x in enumerate(list(bad) + [False]):
        if x and st is None:
            st = i
        if not x and st is not None:
            if i - st >= 2:
                spans.append((round(st / fps, 1), round(i / fps, 1)))
            st = None
    return round(float(bad.mean()), 3), spans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--scenes")
    ap.add_argument("--timeline")
    ap.add_argument("--lufs", type=float, default=-21.0)
    ap.add_argument("--out")
    ap.add_argument("--allow-blue-purple", metavar="理由")
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
    frz = ff(["-i", video, "-vf", "scale=320:-2,freezedetect=n=-35dB:d=3", "-an", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", frz)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", frz)] + [vdur]
    frozen = sorted(((s0, ends[k]) for k, s0 in enumerate(starts)), key=lambda x: x[0] - x[1])
    W, H = int(v["width"]), int(v["height"])
    blanks = blank_runs(gray_frames(video, W, H), sub_band=0.18 if H > W else 0.15)
    bp, bp_spans = blue_purple(video, W, H)
    bp_ok = bp < 0.30 or bool(a.allow_blue_purple)

    hard = [
        ("有音轨", au is not None, "有" if au else "没有音轨"),
        ("音画长度一致（2 帧内）", au is not None and abs(vdur - adur) <= 2 / fps, f"画面 {vdur:.3f}s，声音 {adur:.3f}s"),
        (f"响度在 {a.lufs:g} ±1.5 LUFS", lufs is not None and abs(lufs - a.lufs) <= 1.5, f"{lufs} LUFS"),
        ("峰值 ≤ −1 dBFS", peak is not None and peak <= -1.0, f"{peak} dBFS"),
        ("没有黑场", not blacks, "、".join(f"{float(s):.2f}–{float(e):.2f}s" for s, e in blacks) or "无"),
        ("中段没有空画面（≥0.3 秒几乎没有边缘）", not blanks, "、".join(f"{x:.2f}–{y:.2f}s" for x, y in blanks) or "无"),
        ("蓝紫底 < 30%", bp_ok, f"{bp:.0%}" + (f"（{'、'.join(f'{x}–{y}s' for x, y in bp_spans[:6])}）" if bp_spans else "")
         + (f"，已声明：{a.allow_blue_purple}" if a.allow_blue_purple and bp >= 0.30 else "")),
    ]
    info_rows = [
        ("尺寸", f"{v['width']}×{v['height']}"), ("帧率", f"{fps:g} fps"),
        ("3 秒以上没有明显变化的段落（匀速慢推几个百分点也算没变化；按长短排）",
         "、".join(f"{x:.1f}–{y:.1f}s（{y - x:.1f}s）" for x, y in frozen[:8]) + (f" 等 {len(frozen)} 段" if len(frozen) > 8 else "") or "无"),
        *([("蓝紫底偏多（12–30%），看一眼配色", f"{bp:.0%}")] if 0.12 <= bp < 0.30 else []),
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

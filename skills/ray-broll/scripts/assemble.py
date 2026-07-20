#!/usr/bin/env python3
"""Assemble a full explainer from beats.json — 旁白 master clock 拼装引擎.

读项目根目录的 beats.json,自动完成:
  角色表推导 tempo/tail → ffprobe 实测旁白时长 → beat 时长与 tpad 计算
  → 缺失字幕 PNG 渲染 → 单次 ffmpeg filter_complex 拼装 → 音量核查
  → assembly/assemble-report.json

Usage:
  python assemble.py --project <dir> [--output final.mp4] [--force-captions]
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

ROLE_TABLE = {
    "hook": (1.04, 0.35),
    "definition": (1.10, 0.35),
    "mechanism": (1.10, 0.35),
    "risk": (1.09, 0.35),
    "authority": (1.05, 0.50),
    "synthesis": (1.07, 0.35),
    "closing": (1.02, 0.85),
}


def probe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(f"ffprobe 失败: {path}\n{r.stderr[:200]}")
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--output", default=None)
    ap.add_argument("--force-captions", action="store_true")
    args = ap.parse_args()

    P = os.path.abspath(args.project)
    mf_path = os.path.join(P, "beats.json")
    if not os.path.exists(mf_path):
        sys.exit(f"缺少 {mf_path}(schema 见 references/beats-manifest.md)")
    mf = json.load(open(mf_path))
    beats = mf["beats"]
    lead = mf.get("defaults", {}).get("lead", 0.4)
    fps = mf.get("canvas", {}).get("fps", 24)

    caps_dir = os.path.join(P, "assembly", "caps")
    os.makedirs(caps_dir, exist_ok=True)

    plan = []
    for b in beats:
        role = b.get("role", "definition")
        if role not in ROLE_TABLE:
            sys.exit(f"beat {b['id']}: 未知 role '{role}'"
                     f"(可选:{', '.join(ROLE_TABLE)})")
        tempo = b.get("tempo") or ROLE_TABLE[role][0]
        tail = b.get("tail") if b.get("tail") is not None else ROLE_TABLE[role][1]
        video = os.path.join(P, b["video"])
        vo = os.path.join(P, b["vo"])
        for f in (video, vo):
            if not os.path.exists(f):
                sys.exit(f"beat {b['id']}: 文件不存在 {f}")
        vlen = probe_duration(video)
        volen = probe_duration(vo)
        dur = round(max(vlen, lead + volen / tempo + tail), 2)
        tpad = round(max(0.0, dur - vlen), 2)

        cap_png = os.path.join(caps_dir, f"{b['id']}.png")
        if b.get("caption") and (args.force_captions or not os.path.exists(cap_png)):
            r = subprocess.run(
                [sys.executable, os.path.join(HERE, "render_caption.py"),
                 "--text", b["caption"], "--output", cap_png],
                capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"字幕渲染失败 {b['id']}: {r.stderr[:200]}")
        plan.append({"id": b["id"], "role": role, "tempo": tempo,
                     "tail": tail, "video": video, "vo": vo,
                     "vo_len": round(volen, 2), "video_len": round(vlen, 2),
                     "dur": dur, "tpad": tpad,
                     "cap": cap_png if b.get("caption") else None})

    n = len(plan)
    total = round(sum(p["dur"] for p in plan), 2)
    for p in plan:
        print(f"  {p['id']}: role={p['role']} tempo={p['tempo']} "
              f"vo={p['vo_len']}s dur={p['dur']}s tpad={p['tpad']}s")
    print(f"  total: {total}s / {n} beats")

    out = args.output or os.path.join(
        P, "assembly", f"{mf.get('title', 'final')}-final.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    cmd = ["ffmpeg", "-y", "-v", "error"]
    for p in plan:
        cmd += ["-i", p["video"]]
    for p in plan:
        cmd += ["-i", p["vo"]]
    # 输入序号布局:0..n-1 视频,n..2n-1 旁白,2n.. 字幕
    fc = []
    for i, p in enumerate(plan):
        pad = (f"tpad=stop_mode=clone:stop_duration={p['tpad']},"
               if p["tpad"] > 0 else "")
        fc.append(f"[{i}:v]{pad}null[p{i}]")
    cap_inputs = [p for p in plan if p["cap"]]
    for p in cap_inputs:
        cmd += ["-loop", "1", "-i", p["cap"]]
    cap_pos = {p["id"]: 2 * n + j for j, p in enumerate(cap_inputs)}
    for i, p in enumerate(plan):
        if p["cap"]:
            fc.append(f"[p{i}][{cap_pos[p['id']]}:v]"
                      f"overlay=(W-w)/2:H-h-170:shortest=1[v{i}]")
        else:
            fc.append(f"[p{i}]null[v{i}]")
        fc.append(f"[{n + i}:a]atempo={p['tempo']},adelay={int(lead * 1000)},"
                  f"apad=whole_dur={p['dur']}[a{i}]")
    fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) +
              f"concat=n={n}:v=1:a=1[v][a]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
            "-r", str(fps), "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", out]
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit("ffmpeg 拼装失败")

    final_dur = probe_duration(out)
    vol = subprocess.run(
        ["ffmpeg", "-i", out, "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    vol_lines = [l.split("] ")[-1] for l in vol.splitlines()
                 if "mean_volume" in l or "max_volume" in l]

    report = {"output": out, "duration": round(final_dur, 2),
              "beats": plan, "volume": vol_lines}
    rp = os.path.join(P, "assembly", "assemble-report.json")
    json.dump(report, open(rp, "w"), ensure_ascii=False, indent=2)
    print(f"  -> {out} ({final_dur:.2f}s)")
    for l in vol_lines:
        print(f"  {l}")
    print(f"  report: {rp}")


if __name__ == "__main__":
    main()

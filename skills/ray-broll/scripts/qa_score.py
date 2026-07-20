#!/usr/bin/env python3
"""Objective QA scores for a rendered beat — 首帧纯净度 + 尾帧还原度.

轻量代理指标(无 numpy 依赖):
  first_frame_purity  0-1:首帧中与目标底色偏差 ≤ tol 的像素占比
  end_frame_similarity 0-1:尾帧 vs 确认静帧的灰度归一化相关(降采样 90x160)

分数是给人看的辅助数字,不替代目测;阈值经验:purity ≥ 0.97 视为纯净空场,
similarity ≥ 0.90 视为高还原。注意:similarity 衡量的是与确认静帧的
构图级一致——HyperFrames 路线若重新构图(元素缩放/位置与静帧不同),
分数会显著偏低但不代表质量差,此时仅当参考;只有以复刻静帧构图为目标时
才按 ≥0.90 要求。(实测例:视频模型忠实复刻可到 0.99+,重构图的 HF 版 0.62)

Usage:
  python qa_score.py --video final.mp4 --still confirmed.png [--bg-hex D5A22D]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from PIL import Image  # noqa: E402


def extract_frame(video, out, last=False):
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if last:
        cmd += ["-sseof", "-0.1"]
    cmd += ["-i", video, "-frames:v", "1", out]
    subprocess.run(cmd, check=True)


def purity(frame_path, bg_hex=None, tol=20):
    im = Image.open(frame_path).convert("RGB")
    im = im.resize((90, 160))
    px = list(im.getdata())
    if bg_hex:
        target = tuple(int(bg_hex[i:i + 2], 16) for i in (0, 2, 4))
    else:
        corners = [px[0], px[89], px[-90], px[-1]]
        target = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    ok = sum(1 for p in px
             if all(abs(p[i] - target[i]) <= tol for i in range(3)))
    return ok / len(px)


def similarity(a_path, b_path):
    def gray(p):
        return list(Image.open(p).convert("L").resize((90, 160)).getdata())
    a, b = gray(a_path), gray(b_path)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0:
        return 0.0
    corr = cov / (va ** 0.5 * vb ** 0.5)
    return max(0.0, round((corr + 1) / 2, 4))  # 映射到 0-1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--still", required=True, help="确认静帧(尾帧还原基准)")
    ap.add_argument("--bg-hex", default=None, help="期望首帧底色(不带#)")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as td:
        ff = os.path.join(td, "first.png")
        lf = os.path.join(td, "last.png")
        extract_frame(args.video, ff)
        extract_frame(args.video, lf, last=True)
        result = {
            "video": args.video,
            "first_frame_purity": round(purity(ff, args.bg_hex), 4),
            "end_frame_similarity": similarity(args.still, lf),
        }
    print(json.dumps(result, ensure_ascii=False))
    if result["first_frame_purity"] < 0.97:
        print("  ! 首帧不够纯净(<0.97),检查是否提前露出", file=sys.stderr)
    if result["end_frame_similarity"] < 0.90:
        print("  ! 尾帧还原偏低(<0.90),对照确认静帧目测", file=sys.stderr)


if __name__ == "__main__":
    main()

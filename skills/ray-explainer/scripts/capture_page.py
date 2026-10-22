#!/usr/bin/env python3
"""Capture a web page as one tall PNG at the video's width, so its text reflows to fit and no line is cut off at the
frame edge; the video then drifts slowly down one complete section of it (never a still screenshot cropped by hand).
From Peter Yang's video-short capture.py (MIT, https://github.com/petergyang/video-short), with a landscape width.

usage: python3 capture_page.py URL OUT.png [--portrait | --landscape] [--height 6000]
  --portrait  (default) 540 CSS px wide → 1080-px PNG, the page's phone layout
  --landscape 960 CSS px wide → 1920-px PNG, the desktop layout
Uses the headless Chrome that HyperFrames installs (`npx hyperframes browser path`). Pages behind a login: use Ray's
Chrome (Claude in Chrome) and take the screenshot there instead; same when the PNG shows a bot check
(Cloudflare "Performing security verification": trumpaccounts.gov does this)."""
import argparse, os, subprocess, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--portrait", action="store_true")
    g.add_argument("--landscape", action="store_true")
    ap.add_argument("--height", type=int, default=6000, help="PNG height in pixels")
    a = ap.parse_args()
    width = 960 if a.landscape else 540
    lines = subprocess.run(["npx", "-y", "hyperframes", "browser", "path"], capture_output=True, text=True).stdout.strip().splitlines()
    chrome = lines[-1] if lines else ""
    if not os.path.isfile(chrome):
        sys.exit("找不到 HyperFrames 的 Chrome：先跑一次 npx hyperframes browser ensure")
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:   # some pages never let virtual time settle (codebuddy.cn hung forever): give up after 60 s
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--window-size={width},{a.height // 2}", "--virtual-time-budget=8000", f"--screenshot={out}", a.url],
                       capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        sys.exit(f"60 秒内没截到 {a.url}（页面一直在加载）：改用 Ray 的 Chrome 截")
    if not os.path.isfile(out):
        sys.exit(f"Chrome 没截到 {a.url}")
    print(f"{a.url} → {out}（{width * 2}px 宽）。先用 Read 看图，挑一整段，再在画面里从上往下慢慢移。")


if __name__ == "__main__":
    main()

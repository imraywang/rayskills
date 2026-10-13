#!/usr/bin/env python3
"""../host/plan.json（ray-explainer 的 host.py 算出的角落口型、眨眼、Kling 大机位段落）→ compositions/s-host.html。

- 角落（免费）：Ray 的卡通形象 + 按逐字时间切换的口型图层 + 眨眼 + 轻微摆动。
- 大机位（Kling，可选）：段落开始前 0.4 秒从角落放大到大机位位置，播透明 WebM（自动从 host/frames 转出），说完缩回。
  段落自带 "big": {x, y, w}（host.py 的 big[].pos）时用它，避开这一幕居中的主画面。
用法：python3 host_build.py && python3 build.py"""
import json, os, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
plan = json.load(open(os.path.join(PROJ, "host", "plan.json")))
TOTAL = json.load(open(os.path.join(HERE, "beats.json")))["total"]
W0, H0 = plan["avatar"]["size"]
X, Y, W = 0, 1520, 380            # 角落：左下只露头肩；字幕带顶要 ≤1420
k = W / W0

# 形象图层拷进 assets/host/
AD = os.path.join(HERE, "assets", "host"); os.makedirs(AD, exist_ok=True)
for f in os.listdir(os.path.join(PROJ, "host", "avatar")):
    shutil.copy(os.path.join(PROJ, "host", "avatar", f), AD)

imgs = [f'<img id="hs-{n}" class="hs-p" src="assets/host/{n}.png" alt="" style="left:{px*k:.1f}px;top:{py*k:.1f}px;width:{pw*k:.1f}px;height:{ph*k:.1f}px" />'
        for n, (px, py, pw, ph) in plan["avatar"]["patches"].items()]
tw, cur = [], None
for t, s in plan["mouth"]:
    if t > TOTAL: break
    nxt = None if s == "X" else s
    if nxt == cur: continue
    if cur: tw.append(f'tl.set("#hs-{cur}", {{ opacity: 0 }}, {t});')
    if nxt: tw.append(f'tl.set("#hs-{nxt}", {{ opacity: 1 }}, {t});')
    cur = nxt
for b in plan["blinks"]:
    if b > TOTAL - 0.3: break
    tw.append(f'tl.set("#hs-B", {{ opacity: 1 }}, {b}); tl.set("#hs-B", {{ opacity: 0 }}, {round(b + 0.12, 3)});')

vids = []
OPEN = 'tl.fromTo("#hs-wrap", { y: 360 }, { y: 0, duration: 0.6, ease: "back.out(1.4)" }, 0.1);'
for i, seg in enumerate(plan.get("segments", [])):
    a, b = seg["start"], seg["end"]
    key = seg["dir"].rstrip("/").split("/")[-1]
    webm = os.path.join(AD, f"big_{key}.webm")
    if not os.path.exists(webm):   # 抠好绿幕的 RGBA 帧 → 带透明通道的 VP9
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(seg.get("fps", 30)), "-i", os.path.join(PROJ, "host", "frames", key, "%04d.webp"),
                        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "2500k", "-auto-alt-ref", "0", webm], check=True)
    big = seg.get("big") or plan["big"]
    bx, by, sc = big["x"], big["y"], big["w"] / W
    vids.append(f'<video id="hs-v{i}" class="hs-v" src="assets/host/big_{key}.webm" muted playsinline data-start="{a}" data-duration="{round(b - a, 3)}" data-track-index="{40 + i}"></video>')
    if i == 0 and a < 1.0:   # 开场就是大机位：直接在大机位淡入，不和角落滑入抢在一起
        OPEN = f'tl.fromTo("#hs-wrap", {{ x: {bx - X}, y: {by - Y}, scale: {sc:.4f}, opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power1.out" }}, 0.05);'
    else:
        tw.append(f'tl.to("#hs-wrap", {{ x: {bx - X}, y: {by - Y}, scale: {sc:.4f}, duration: 0.6, ease: "power2.inOut" }}, {round(a - 0.6, 3)});')
    tw.append(f'tl.set("#hs-body", {{ opacity: 0 }}, {a}); tl.set("#hs-v{i}", {{ opacity: 1 }}, {a});')
    tw.append(f'tl.set("#hs-v{i}", {{ opacity: 0 }}, {b}); tl.set("#hs-body", {{ opacity: 1 }}, {b});')
    tw.append(f'tl.to("#hs-wrap", {{ x: 0, y: 0, scale: 1, duration: 0.8, ease: "power2.inOut" }}, {round(b + 0.15, 3)});')

period = 4.2
reps = max(0, int(TOTAL // period) - 1)
H = H0 * k
doc = f'''<!doctype html>
<html>
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <style>
        #s-host {{ position: absolute; inset: 0; pointer-events: none; }}
        #hs-wrap {{ position: absolute; left: {X}px; top: {Y}px; width: {W}px; height: {H:.1f}px; transform-origin: 0 0; }}
        #hs-body {{ position: absolute; inset: 0; transform-origin: 50% 70%; }}
        #hs-body img {{ position: absolute; display: block; }}
        #hs-base {{ left: 0; top: 0; width: {W}px; height: {H:.1f}px; }}
        .hs-p {{ opacity: 0; }}
        .hs-v {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H:.1f}px; opacity: 0; }}
      </style>
      <div id="s-host" data-composition-id="s-host" data-width="1080" data-height="1920">
        <div id="hs-wrap" data-layout-ignore>
          <div id="hs-body">
            <img id="hs-base" src="assets/host/base.png" alt="" />
            {chr(10).join("            " + i for i in imgs).lstrip()}
          </div>
          {chr(10).join("          " + v for v in vids).lstrip()}
        </div>
      </div>
      <script>
        (function () {{
          const tl = gsap.timeline({{ paused: true }});
          {OPEN}
          tl.fromTo("#hs-body", {{ rotation: -1.2 }}, {{ rotation: 1.2, duration: {period / 2}, ease: "sine.inOut", yoyo: true, repeat: {reps * 2 + 1} }}, 0.7);
          {chr(10).join("          " + t for t in tw).lstrip()}
          window.__timelines["s-host"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
'''
os.makedirs(os.path.join(HERE, "compositions"), exist_ok=True)
open(os.path.join(HERE, "compositions", "s-host.html"), "w").write(doc)
print(f"s-host.html: {len(tw)} tweens, {len(vids)} big segments")

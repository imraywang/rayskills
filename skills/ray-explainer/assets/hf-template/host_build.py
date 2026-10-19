#!/usr/bin/env python3
"""../host/plan.json（ray-explainer 的 host.py 算出的角落口型、眨眼、大机位段落）→ compositions/s-host.html。

- 角落（免费）：Ray 的卡通形象 + 按逐字时间切换的口型图层 + 眨眼 + 轻微摆动。
- 大机位（MiniMax H3 / Kling，可选）：段落开始前 0.4 秒从角落放大到大机位位置，播透明 WebM（自动从 host/frames 转出），说完缩回。
  段落自带 "big": {x, y, w}（host.py 的 big[].pos）时用它，避开这一幕居中的主画面。
- 横屏（script.json "aspect": "landscape"）：Screen Studio 式圆角气泡，左下角墨绿方块里只露头肩；大机位是气泡放大露出半身，
  段落的 "big" 写 {x, y, w, h}。版位在 canvas.json（和 build.py 读同一份）。
用法：python3 host_build.py && python3 build.py"""
import json, os, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
plan = json.load(open(os.path.join(PROJ, "host", "plan.json")))
TOTAL = json.load(open(os.path.join(HERE, "beats.json")))["total"]
W0, H0 = plan["avatar"]["size"]
SCRIPT = json.load(open(os.path.join(PROJ, "script.json")))
_cv = next(p for p in (os.path.join(HERE, "canvas.json"), os.path.expanduser("~/.claude/skills/ray-explainer/assets/canvas.json")) if os.path.exists(p))
ASPECT = SCRIPT.get("aspect", "portrait"); CV = json.load(open(_cv))[ASPECT]; CW, CH = CV["W"], CV["H"]
BUB = plan.get("bubble") or CV["host"].get("bubble")    # 横屏小圆窗（host.py 已按 theme 换好底色和细圈）；竖屏没有
if BUB:
    CR, BIG0 = plan.get("crop") or CV["host"]["crop"], plan.get("big_bubble") or CV["host"]["big_bubble"]
    X, Y, W = (round(v, 1) for v in (-CR["x"] * BUB["w"] / CR["w"], -CR["y"] * BUB["w"] / CR["w"], BUB["w"] / CR["w"]))   # 形象在气泡里的位置（气泡左上角为原点）
else:
    X, Y, W = 0, 1520, 380            # 角落：左下只露头肩；字幕带顶要 ≤1420
k = W / W0
H = H0 * k   # 大机位 h3 的 pad 也要用，必须在段落循环之前算好

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
SIDES = plan.get("sides") or [[0, "left"]]
def side_at(t): return [v for a, v in SIDES if a <= t][-1] if any(a <= t for a, _ in SIDES) else "left"
SEGS = plan.get("segments", [])
CHAIN = 0.15 + 0.8 + 0.6   # 两段大机位间隔小于「停 0.15 + 缩回 0.8 + 再放大 0.6」时不回角落，直接接到下一段
for i, seg in enumerate(SEGS):
    a, b = seg["start"], seg["end"]
    chained_in = i > 0 and a - SEGS[i - 1]["end"] < CHAIN
    chained_out = i + 1 < len(SEGS) and SEGS[i + 1]["start"] - b < CHAIN
    key = seg["dir"].rstrip("/").split("/")[-1]
    webm = os.path.join(AD, f"big_{key}.webm")
    if not os.path.exists(webm):   # 抠好绿幕的 RGBA 帧 → 带透明通道的 VP9
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(seg.get("fps", 30)), "-i", os.path.join(PROJ, "host", "frames", key, "%04d.webp"),
                        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "2500k", "-auto-alt-ref", "0", webm], check=True)
    big = seg.get("big") or plan.get("big")   # 竖屏的大机位位置；横屏用下面的气泡
    if BUB:   # 气泡放大：气泡的位置、大小、圆角补间到大机位；形象跟气泡宽度一起放大，左上角留在 crop 处
        bb = {**BIG0, **(seg.get("big") or {})}; s_ = bb["w"] / BUB["w"]
        right = side_at(a) == "right"   # 右下：气泡往左上长（镜像）
        fr = f'x: {(BUB["x"] + BUB["w"] - bb["x"] - bb["w"]) if right else (bb["x"] - BUB["x"])}, y: {bb["y"] - BUB["y"]}, width: {bb["w"]}, height: {bb["h"]}, borderRadius: {bb.get("r", BIG0["r"]) * bb["w"]:.1f}'   # 位移用 transform，不补间 left/top
        wr = f'x: {X * (s_ - 1):.1f}, y: {Y * (s_ - 1):.1f}, scale: {s_:.4f}'
        back_fr = f'x: 0, y: 0, width: {BUB["w"]}, height: {BUB["h"]}, borderRadius: {BUB["r"] * BUB["w"]:.1f}'
    pl, pt, pr, pb = seg.get("pad") or [0, 0, 0, 0]   # 帧四周比形象图多出的边（h3 左右各补绿边）：视频往外放，形象和角落图层对齐
    pad_css = f' style="left:{-pl * W:.1f}px;top:{-pt * H:.1f}px;width:{W * (1 + pl + pr):.1f}px;height:{H * (1 + pt + pb):.1f}px"' if seg.get("pad") else ""
    vids.append(f'<video id="hs-v{i}" class="hs-v" src="assets/host/big_{key}.webm"{pad_css} muted playsinline data-start="{a}" data-duration="{round(b - a, 3)}" data-track-index="{40 + i}"></video>')
    if BUB:
        if i == 0 and a < 1.0:
            OPEN = (f'tl.set(".hs-fr", {{ {fr} }}, 0); tl.set("#hs-wrap", {{ {wr} }}, 0);'
                    f' tl.fromTo(".hs-fr", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power1.out" }}, 0.05);')
        else:
            tw.append(f'tl.to(".hs-fr", {{ {fr}, duration: 0.6, ease: "power2.inOut" }}, {round(a - 0.6, 3)}); tl.to("#hs-wrap", {{ {wr}, duration: 0.6, ease: "power2.inOut" }}, {round(a - 0.6, 3)});')
    elif i == 0 and a < 1.0:   # 开场就是大机位：直接在大机位淡入，不和角落滑入抢在一起
        bx, by, sc = big["x"], big["y"], big["w"] / W
        OPEN = f'tl.fromTo("#hs-wrap", {{ x: {bx - X}, y: {by - Y}, scale: {sc:.4f}, opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power1.out" }}, 0.05);'
    else:
        bx, by, sc = big["x"], big["y"], big["w"] / W
        if chained_in:   # 紧接上一段：在两段之间直接移到这一段的位置（位置相同就不动）
            pb_ = SEGS[i - 1].get("big") or plan.get("big")
            if (pb_["x"], pb_["y"], pb_["w"]) != (bx, by, big["w"]):
                gap = max(0.2, a - SEGS[i - 1]["end"])
                tw.append(f'tl.to("#hs-wrap", {{ x: {bx - X}, y: {by - Y}, scale: {sc:.4f}, duration: {gap:.3f}, ease: "power2.inOut" }}, {SEGS[i - 1]["end"]});')
        else:
            tw.append(f'tl.to("#hs-wrap", {{ x: {bx - X}, y: {by - Y}, scale: {sc:.4f}, duration: 0.6, ease: "power2.inOut" }}, {round(a - 0.6, 3)});')
    tw.append(f'tl.set("#hs-body", {{ opacity: 0 }}, {a}); tl.set("#hs-v{i}", {{ opacity: 1 }}, {a});')
    tw.append(f'tl.set("#hs-v{i}", {{ opacity: 0 }}, {b}); tl.set("#hs-body", {{ opacity: 1 }}, {b});')
    if BUB:
        tw.append(f'tl.to(".hs-fr", {{ {back_fr}, duration: 0.8, ease: "power2.inOut" }}, {round(b + 0.15, 3)}); tl.to("#hs-wrap", {{ x: 0, y: 0, scale: 1, duration: 0.8, ease: "power2.inOut" }}, {round(b + 0.15, 3)});')
    elif not chained_out:
        tw.append(f'tl.to("#hs-wrap", {{ x: 0, y: 0, scale: 1, duration: 0.8, ease: "power2.inOut" }}, {round(b + 0.15, 3)});')

if BUB and plan.get("show") is not None and OPEN.startswith('tl.fromTo("#hs-wrap", { y: 360 }'): OPEN = ""   # 只在关键句出现：不做开场滑入
if BUB and OPEN.startswith('tl.fromTo("#hs-wrap", { y: 360 }'):   # 横屏：气泡从画面下方滑入
    OPEN = f'tl.fromTo(".hs-fr", {{ y: {CH - BUB["y"]} }}, {{ y: 0, duration: 0.6, ease: "back.out(1.4)" }}, 0.1);'
period = 4.2
BUB_CSS = BUB_OPEN = BUB_CLOSE = ""
if BUB:   # 换边（学小Lin说）：#hs-side 整体平移到右下；换边时刻前后各 switch 秒缩小消失 → 换角 → 放大出现
    SX, SW = CW - 2 * BUB["x"] - BUB["w"], plan.get("switch", 0.35)
    if SIDES[0][1] == "right": tw.insert(0, f'tl.set("#hs-side", {{ x: {SX} }}, 0);')
    SHOW = plan.get("show")   # 只在关键句出现：#hs-vis 默认隐藏，每段开口前弹出、说完淡出
    if SHOW is not None:
        SI, SO, SH = plan.get("show_in", 0.3), plan.get("show_out", 0.3), plan.get("show_hold", 0.15)
        tw.insert(0, 'tl.set("#hs-vis", { opacity: 0, scale: 0.6 }, 0);')
        for a, b in SHOW:
            tw.append(f'tl.to("#hs-vis", {{ opacity: 1, scale: 1, duration: {SI}, ease: "power2.out" }}, {max(0, round(a - SI, 3))});'
                      f' tl.to("#hs-vis", {{ opacity: 0, scale: 0.6, duration: {SO}, ease: "power2.in" }}, {round(b + SH, 3)});')
    for a, v in SIDES[1:]:
        tw.append(f'tl.to("#hs-side", {{ scale: 0, opacity: 0, duration: {SW}, ease: "power2.inOut" }}, {round(a - SW, 3)});'
                  f' tl.set("#hs-side", {{ x: {SX if v == "right" else 0} }}, {a});'
                  f' tl.to("#hs-side", {{ scale: 1, opacity: 1, duration: {SW}, ease: "power2.inOut" }}, {a});')
if BUB:   # 气泡：#hs-frame 裁出头肩（墨绿底 + 投影），#hs-ring 是同位置的细描边（不被裁，压在形象上面）
    geo = f'left: {BUB["x"]}px; top: {BUB["y"]}px; width: {BUB["w"]}px; height: {BUB["h"]}px; border-radius: {BUB["r"] * BUB["w"]:.1f}px;'
    BUB_CSS = (f'\n        #hs-frame {{{{ position: absolute; {geo} overflow: hidden; background: {BUB["fill"]}; box-shadow: 0 {BUB["dy"]}px {BUB["blur"]}px {BUB["shadow"]}; }}}}'
               f'\n        #hs-ring {{{{ position: absolute; {geo} box-sizing: border-box; border: {BUB.get("ring_w", 4)}px solid {BUB.get("ring", "transparent")}; }}}}')
    BUB_CSS = BUB_CSS.replace("{{", "{").replace("}}", "}")
    BUB_CSS += f'\n        #hs-side {{ position: absolute; inset: 0; transform-origin: {BUB["x"] + BUB["w"] / 2}px {BUB["y"] + BUB["h"]}px; }}'
    BUB_CSS += f'\n        #hs-vis {{ position: absolute; inset: 0; transform-origin: {BUB["x"] + BUB["w"] / 2}px {BUB["y"] + BUB["h"]}px; }}'
    BUB_OPEN = '\n        <div id="hs-side" data-layout-ignore>\n        <div id="hs-vis" data-layout-ignore>\n        <div id="hs-frame" class="hs-fr" data-layout-ignore>'
    BUB_CLOSE = '\n        </div>\n        <div id="hs-ring" class="hs-fr" data-layout-ignore></div>\n        </div>\n        </div>'
reps = max(0, int(TOTAL // period) - 1)
doc = f'''<!doctype html>
<html>
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <style>
        #s-host {{ position: absolute; inset: 0; pointer-events: none; }}
        #hs-wrap {{ position: absolute; left: {X}px; top: {Y}px; width: {W}px; height: {H:.1f}px; transform-origin: 0 0; }}{BUB_CSS}
        #hs-body {{ position: absolute; inset: 0; transform-origin: 50% 70%; }}
        #hs-body img {{ position: absolute; display: block; }}
        #hs-base {{ left: 0; top: 0; width: {W}px; height: {H:.1f}px; }}
        .hs-p {{ opacity: 0; }}
        .hs-v {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H:.1f}px; opacity: 0; }}
      </style>
      <div id="s-host" data-composition-id="s-host" data-width="{CW}" data-height="{CH}">{BUB_OPEN}
        <div id="hs-wrap" data-layout-ignore>
          <div id="hs-body">
            <img id="hs-base" src="assets/host/base.png" alt="" />
            {chr(10).join("            " + i for i in imgs).lstrip()}
          </div>
          {chr(10).join("          " + v for v in vids).lstrip()}
        </div>{BUB_CLOSE}
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

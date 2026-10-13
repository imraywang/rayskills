#!/usr/bin/env python3
"""生成 index.html：旁白 + 配乐（给人声让路）、各幕插槽、顶栏、逐条字幕、音效、角落数字人。
场景动画在 compositions/s-<id>.html（读 window.BEATS[id]，不内联时间）；音效在 compositions/s-<id>.sfx.json
（幕内时间 [[t, "name", vol], ...]，文件在 assets/audio/<name>.mp3）。
用法：python3 make_beats.py && python3 build.py        COVER=1 python3 build.py → 封面版（无字幕、无数字人、加封面字）"""
import json, os, html, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
B = json.load(open(os.path.join(HERE, "beats.json")))
SC, TOTAL, NARR = B["scenes"], B["total"], B["narration"]
COVER = bool(os.environ.get("COVER"))

# ───────────── 本片专属（每片重写这一段，其余不动）─────────────
BG, FG = "#0b0d10", "#e9e6df"                     # 与 assets/style.css 的台面色、正文色一致
CHROME_CSS = ""                                   # 顶栏等全片常驻元素的样式
CHROME_HTML = ""                                  # 常驻元素（放在场景之上、字幕之下）
CHROME_TWEENS = []                                # 常驻元素的动画："tl.fromTo(...)" 字符串，时间是全片秒
CAP_TOP = 1420                                    # 字幕带顶（有角落数字人时 ≤1420，给头部让位）
COVER_HTML = ""                                   # 封面版额外叠加的大字（钩子数字放画面中段，3:4 裁切也完整）
COVER_T = 0.0                                     # 封面取哪一秒（publish.py 读 script.json 的 cover_t，两处保持一致）
BGM = "assets/audio/bgm.m4a"                      # 没有配乐就设为 None
BGM_LEN, BGM_VOL = 0.0, 0.26                      # 配乐长度（秒，比片子短会在尾部接第二段）、音量
# ────────────────────────────────────────────────────────────────

slots, caps, sfx, tweens = [], [], [], list(CHROME_TWEENS)
for i, s in enumerate(SC):
    start, end = s["start"], (SC[i + 1]["start"] if i + 1 < len(SC) else TOTAL)
    sid = f"s-{s['id']}"
    if os.path.exists(os.path.join(HERE, "compositions", sid + ".html")):
        slots.append(f'    <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{start:.3f}" data-duration="{end - start:.3f}" data-track-index="1" data-width="1080" data-height="1920"></div>')
    for c in ([] if COVER else s["caps"]):
        a, b = s["start"] + c["a"], s["start"] + c["b"]
        k = len(caps)
        caps.append(f'    <div id="cap{k}" class="cap clip" data-start="{a:.3f}" data-duration="{max(0.25, b - a):.3f}" data-track-index="9"><span>{html.escape(c["s"])}</span></div>')
        tweens.append(f'tl.fromTo("#cap{k} span", {{ y: 16, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.14, ease: "power2.out" }}, {a:.3f});')
    fx = os.path.join(HERE, "compositions", sid + ".sfx.json")
    for t, name, vol in (json.load(open(fx)) if os.path.exists(fx) else []):
        at = s["start"] + t
        if 0 <= at <= TOTAL - 0.3:
            sfx.append(f'    <audio id="sfx{len(sfx)}" src="assets/audio/{name}.mp3" data-start="{at:.3f}" data-track-index="{20 + len(sfx)}" data-volume="{vol}"></audio>')

host = ""
if os.path.exists(os.path.join(HERE, "compositions", "s-host.html")) and not COVER:   # host_build.py 生成
    host = f'    <div id="s-host" data-composition-id="s-host" data-composition-src="compositions/s-host.html" data-start="0" data-duration="{TOTAL}" data-track-index="8" data-width="1080" data-height="1920"></div>'
bgm = []
if BGM:
    first = min(TOTAL, BGM_LEN or TOTAL)
    bgm.append(f'    <audio id="bgm1" src="{BGM}" data-start="0" data-duration="{first:.3f}" data-track-index="3" data-volume="{BGM_VOL}"></audio>')
    if BGM_LEN and BGM_LEN < TOTAL:   # 配乐不够长：从中段接第二段，重叠 0.4 秒
        bgm.append(f'    <audio id="bgm2" src="{BGM}" data-start="{BGM_LEN - 0.4:.3f}" data-media-start="40" data-duration="{TOTAL - BGM_LEN + 0.4:.3f}" data-track-index="4" data-volume="{BGM_VOL}"></audio>')

doc = f'''<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script src="assets/beats.js"></script>
    <link rel="stylesheet" href="assets/style.css" />
    <style>
      @font-face {{ font-family: "HeiHeavy"; src: url("assets/fonts/NotoSansSC-900.woff") format("woff"); font-weight: 900; }}
      @font-face {{ font-family: "HeiBold"; src: url("assets/fonts/NotoSansSC-700.woff") format("woff"); font-weight: 700; }}
      @font-face {{ font-family: "Hei"; src: url("assets/fonts/NotoSansSC-500.woff") format("woff"); font-weight: 500; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {BG}; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; color: {FG}; background: {BG}; }}
      .cap {{ position: absolute; left: 50px; right: 50px; top: {CAP_TOP}px; height: 150px; z-index: 60; display: flex; align-items: center; justify-content: center; }}
      .cap span {{ display: inline-block; max-width: 980px; padding: 14px 36px; border-radius: 14px; background: rgba(11,13,16,0.86); border: 2px solid rgba(42,50,61,0.9);
        font-family: "HeiBold", sans-serif; font-weight: 700; font-size: 60px; line-height: 1.25; color: {FG}; text-align: center; }}
      {CHROME_CSS}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
    <audio id="narration" src="assets/audio/narration.m4a" data-start="0" data-duration="{NARR}" data-track-index="0" data-volume="1"></audio>
{chr(10).join(bgm)}
{chr(10).join(slots)}
{host}
{CHROME_HTML}
{chr(10).join(caps)}
{COVER_HTML if COVER else ""}
{chr(10).join(sfx)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + t for t in tweens).lstrip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open(os.path.join(HERE, "index.html"), "w").write(doc)
print(f"index.html: {len(slots)} scenes, {len(caps)} captions, {len(sfx)} sfx, total {TOTAL}s" + (" [COVER]" if COVER else ""))

# 配乐给人声让路（hyperframes-audio 的 carve）；每次重建都重新刻，因为上面整页重写了 index.html
CARVE = os.path.expanduser("~/.claude/skills/hyperframes-audio/scripts/carve.mjs")
for bed in ([b.split('"')[1] for b in bgm] if os.path.exists(CARVE) else []):
    r = subprocess.run(["node", CARVE, "--comp", os.path.join(HERE, "index.html"), "--bed", bed, "--voice", "narration", "--strength", "0.7"], capture_output=True, text=True)
    print(f"carve {bed}: " + ("ok" if r.returncode == 0 else "FAILED（项目里先 npm i -D @hyperframes/core）"))

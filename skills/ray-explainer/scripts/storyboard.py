"""Render the storyboard (分镜表) from script.json for Ray to confirm BEFORE any voice or drawing work.

usage: python3 storyboard.py <project>        -> prints and writes <project>/storyboard.md

Per scene, script.json carries (besides id / lines):
  beat     one-line summary of what this scene says (falls back to the narration)
  pattern  kit pattern name, or grammar  huashu grammar name, or neither (= custom kit code)
  visual   what is on screen, in order, as plain language
  anchors  which spoken words trigger which visual events
  footage  the real material on screen (Ray 2026-10-15: real footage first, dynamic before static), a string or a list of
           {"what": "...", "src": "link / file / who", "motion": true} — motion = video / screen recording / real run
Top level: title, central_judgment, to_confirm[], cover_t (optional, seconds; frame used as cover)
"""
import json, os, sys

PROJ = os.path.abspath(sys.argv[1])
s = json.load(open(os.path.join(PROJ, "script.json")))
GAPS = {"lead": .6, "line": .32, "scene": .8, "tail": 1.6, **(s.get("gaps") or {})}
RATE = 5.8 * float(s.get("speed", 1.0))   # measured on full films (pauses excluded): Charon ≈5.7 字/s, Ray clone ≈6.0 字/s

NAMES = {"y5_kinetic_type": "动态文字", "y1_kurzgesagt": "Kurzgesagt", "y3_whiteboard": "白板", "t1_3b1b": "3b1b",
         "t2_keynote_ui": "发布会", "t3_finance_chart": "财经图表", "y2_vox": "Vox 拼贴", "y4_storytime": "故事简笔"}
cell = lambda x: str(x or "").replace("|", "／").replace("\n", " ")


def how(sc):
    if sc.get("grammar"): return f"**{NAMES.get(sc['grammar'], sc['grammar'])}**"
    if sc.get("pattern"): return f"手绘·{sc['pattern']}"
    if os.path.exists(os.path.join(PROJ, "hf", "build.py")): return "HyperFrames"   # 专属风格模式：每幕是 hf/compositions/s-<id>.html
    return "手绘·定制"


rows, total, dist = [], GAPS["lead"] + GAPS["tail"], {}
real_n = motion_n = 0
for i, sc in enumerate(s["scenes"], 1):
    chars = sum(len(l) for l in sc["lines"])
    dur = chars / RATE + GAPS["line"] * (len(sc["lines"]) - 1) + (GAPS["scene"] if i < len(s["scenes"]) else 0)
    total += dur
    key = how(sc); dist[key] = dist.get(key, 0) + 1
    beat = sc.get("beat") or "".join(sc["lines"])[:40]
    ft = sc.get("footage") or []
    ft = [ft] if isinstance(ft, (str, dict)) else ft
    ft = [x if isinstance(x, dict) else {"what": x} for x in ft]
    moving = any(x.get("motion") for x in ft); real_n += bool(ft); motion_n += moving
    fcell = "；".join(("▶ " if x.get("motion") else "") + x.get("what", "") + (f"（{x['src']}）" if x.get("src") else "") for x in ft) or "（无真实素材）"
    rows.append(f"| {i} | {sc['id']} | {cell(beat)} | {key} | {cell(sc.get('visual', '（未写）'))} | {cell(fcell)} | {cell(sc.get('anchors', ''))} | {dur:.0f}s |")

out = [f"# 分镜表：{s.get('title', '')}", ""]
if s.get("central_judgment"): out += [f"**核心判断**：{s['central_judgment']}", ""]
out += ["| # | 幕 | 讲什么 | 画法 | 画面 | 真实素材（▶ 动态） | 卡点 | 时长 |", "|---|---|---|---|---|---|---|---|", *rows, ""]
out += [f"**预计时长**：约 {total / 60:.0f} 分 {total % 60:02.0f} 秒（{sum(len(l) for sc in s['scenes'] for l in sc['lines'])} 字，按 {RATE:.1f} 字/秒估）",
        f"**画法分布**：" + "，".join(f"{k} ×{v}" for k, v in dist.items()), f"**音色**：{s.get('voice', 'Charon')}",
        f"**画幅**：" + ("横屏 1920×1080" if s.get("aspect") == "landscape" else "竖屏 1080×1920"),
        *([f"**风格参考**：{s['style_ref']}（references/style-refs.md）"] if s.get("style_ref") else []), ""]
n = len(s["scenes"])
out += [f"**真实素材**：{real_n}/{n} 幕有真实素材，其中 {motion_n} 幕是动态的（录屏 / 视频 / 实跑）", ""]
if motion_n * 2 < n:   # Ray 2026-10-15: audiences tire of drawn animation; most scenes should carry moving real footage
    out += [f"**⚠ 动态真实素材太少**：不到一半的幕有录屏、视频或实跑画面。先按 hyperframes.md「取材」补，缺的列出来问 Ray 要。", ""]
kit = [sc["id"] for sc in s["scenes"] if not sc.get("grammar")]
if s.get("aspect") == "landscape" and kit and not os.path.exists(os.path.join(PROJ, "hf", "build.py")):
    out += [f"**⚠ 横屏不支持手绘套路**：{'、'.join(kit)} 没写 grammar。横屏片只能用语法片段，或整期走 HyperFrames 模式。", ""]
styles = sorted({sc.get("grammar") or "kit" for sc in s["scenes"]})   # one film, one style (Ray, 2026-10-13); kit patterns + custom kit code = one style
if len(styles) > 1 and not s.get("mix"):
    out += [f"**⚠ 一期只用一种画法**：这条片子混了 {len(styles)} 种（" + "、".join("手绘" if x == "kit" else NAMES.get(x, x) for x in styles) +
            "）。按 grammars.md「一期一种画法」改成一种；确实要混，在 script.json 顶层写 \"mix\": true 并说明理由。", ""]
if s.get("to_confirm"): out += ["**待确认**", *[f"- {x}" for x in s["to_confirm"]], ""]
out += ["## 逐字稿", ""]
for i, sc in enumerate(s["scenes"], 1):
    out += [f"**{i}. {sc['id']}**", "", *[f"> {l}" for l in sc["lines"]], ""]
md = "\n".join(out)
open(os.path.join(PROJ, "storyboard.md"), "w").write(md)
print(md)

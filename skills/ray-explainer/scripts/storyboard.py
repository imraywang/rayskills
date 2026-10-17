"""Render the storyboard (分镜表) from script.json for Ray to confirm BEFORE any voice or drawing work.

usage: python3 storyboard.py <project>        -> prints and writes <project>/storyboard.md

Per scene, script.json carries (besides id / lines):
  beat     one-line summary of what this scene says (falls back to the narration)
  pattern  kit pattern name, or grammar  huashu grammar name, or neither (= custom kit code)
  visual   what is on screen, in order, as plain language
  anchors  which spoken words trigger which visual events
  footage  the real material on screen (Ray 2026-10-15: real footage first, dynamic before static), a string or a list of
           {"what": "...", "src": "link / file / who", "motion": true, "fullscreen": true} — motion = video / screen recording / real run;
           fullscreen = plays as .fullshot over the whole frame (Ray 2026-10-15: the default for real video; false only for
           screenshots, posts, stills and side-by-side comparisons, which go in a window);
           framing = "cover" (default: landscape source cropped to portrait, object-position on the subject) or "band"
           (whole landscape frame across the stage, the same clip blurred and darkened above and below). Use band when
           the subject is a whole device or a wide composition — 2026-10-16 a cover-cropped clip of hands holding a
           landscape iPhone lost the phone and Ray asked for it to be redone.
Top level: title, central_judgment, to_confirm[], cover_t (optional, seconds; frame used as cover),
           design (optional {shell, audio, boundary}: the IP-themed shell, printed under the table)
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
windowed = []   # moving footage put in a window instead of full screen
cropped = []    # full-screen cover crops of footage that looks like a whole device / wide shot
DEVICE = ("手机", "iPhone", "iPad", "平板", "掌机", "Switch", "手持", "握着", "横握", "超宽", "宽屏", "双屏", "笔记本", "显示器", "电视")
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
    fs = lambda x: "" if "fullscreen" not in x and not x.get("motion") else (" ▭整幅" if x.get("framing") == "band" else " ⛶全屏") if x.get("fullscreen") else " ▢窗口" if "fullscreen" in x else " ？全屏未写"
    cropped += [f"{sc['id']}：{x.get('what', '')}" for x in ft if x.get("fullscreen") and "framing" not in x and any(k in x.get("what", "") + x.get("src", "") for k in DEVICE)]
    windowed += [f"{sc['id']}：{x.get('what', '')}" + ("" if "fullscreen" in x else "（未写 fullscreen）") for x in ft if x.get("motion") and not x.get("fullscreen")]
    fcell = "；".join(("▶ " if x.get("motion") else "") + x.get("what", "") + (f"（{x['src']}）" if x.get("src") else "") + fs(x) for x in ft) or "（无真实素材）"
    rows.append(f"| {i} | {sc['id']} | {cell(beat)} | {key} | {cell(sc.get('visual', '（未写）'))} | {cell(fcell)} | {cell(sc.get('anchors', ''))} | {dur:.0f}s |")

out = [f"# 分镜表：{s.get('title', '')}", ""]
if s.get("central_judgment"): out += [f"**核心判断**：{s['central_judgment']}", ""]
out += ["| # | 幕 | 讲什么 | 画法 | 画面 | 真实素材（▶ 动态 · ⛶全屏 / ▭整幅 / ▢窗口） | 卡点 | 时长 |", "|---|---|---|---|---|---|---|---|", *rows, ""]
out += [f"**预计时长**：约 {total / 60:.0f} 分 {total % 60:02.0f} 秒（{sum(len(l) for sc in s['scenes'] for l in sc['lines'])} 字，按 {RATE:.1f} 字/秒估）",
        f"**画法分布**：" + "，".join(f"{k} ×{v}" for k, v in dist.items()), f"**音色**：{s.get('voice', 'Charon')}",
        f"**画幅**：" + ("横屏 1920×1080" if s.get("aspect") == "landscape" else "竖屏 1080×1920"),
        *([f"**风格参考**：{s['style_ref']}（references/style-refs.md）"] if s.get("style_ref") else []), ""]
if s.get("design"):   # IP-themed shell (SKILL.md 1b): show it with the table so Ray confirms it in the same pass
    d = s["design"]; lab = {"shell": "外壳", "audio": "声音", "boundary": "边界"}
    out += ["**主题外壳**", *[f"- {lab.get(k, k)}：{v}" for k, v in d.items()], ""]
n = len(s["scenes"])
out += [f"**真实素材**：{real_n}/{n} 幕有真实素材，其中 {motion_n} 幕是动态的（录屏 / 视频 / 实跑）", ""]
if motion_n * 2 < n:   # Ray 2026-10-15: audiences tire of drawn animation; most scenes should carry moving real footage
    out += [f"**⚠ 动态真实素材太少**：不到一半的幕有录屏、视频或实跑画面。先按 hyperframes.md「取材」补，缺的列出来问 Ray 要。", ""]
if windowed:   # Ray 2026-10-15: real video in a small camera window lacks impact; full screen is the default
    out += ["**⚠ 这些动态素材装在窗口里**（真实视频默认全屏 `fullscreen: true`；只有需要并排对比时才进窗口，确认后保留）：" + "；".join(windowed), ""]
if cropped:   # Ray 2026-10-16: a cover-cropped clip of a landscape iPhone in hands lost the phone
    out += ["**⚠ 这些全屏素材的主体像是整台设备或宽画面**（横屏裁成竖屏会切掉主体）：" + "；".join(cropped) + "。看一眼参考帧：主体要完整就写 `framing: \"band\"`（整幅横放、上下虚化垫底），裁了也没事就写 `framing: \"cover\"`。", ""]
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

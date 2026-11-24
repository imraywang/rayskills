"""Render the storyboard (分镜表) from script.json for Ray to confirm BEFORE any voice or drawing work.

usage: python3 storyboard.py <project>        -> prints and writes <project>/storyboard.md

Per scene, script.json carries (besides id / lines):
  beat     one-line summary of what this scene says (falls back to the narration)
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
Top level: title, central_judgment, cover_t (optional, seconds; frame used as cover),
           design (optional {shell, audio, boundary}: the IP-themed shell, printed under the table)
"""
import json, os, sys

PROJ = os.path.abspath(sys.argv[1])
s = json.load(open(os.path.join(PROJ, "script.json")))
GAPS = {"lead": .6, "line": .32, "scene": .8, "tail": 1.6, **(s.get("gaps") or {})}
RATE = 5.8 * float(s.get("speed", 1.0))   # measured on full films (pauses excluded): Charon ≈5.7 字/s, Ray clone ≈6.0 字/s

cell = lambda x: str(x or "").replace("|", "／").replace("\n", " ")


def spoken(t):
    """Count like the voice reads: a CJK character is one, a Latin letter / digit about half (2026-10-18: the five
    English terms in the Musk film counted as full characters and padded the estimate)."""
    return sum(1 if ord(c) > 0x2e80 else 0.5 if c.isalnum() else 0 for c in t)


rows, total = [], GAPS["lead"] + GAPS["tail"]
real_n = motion_n = 0
windowed = []   # moving footage put in a window instead of full screen
cropped = []    # full-screen cover crops of footage that looks like a whole device / wide shot
DEVICE = ("手机", "iPhone", "iPad", "平板", "掌机", "Switch", "手持", "握着", "横握", "超宽", "宽屏", "双屏", "笔记本", "显示器", "电视")
for i, sc in enumerate(s["scenes"], 1):
    chars = sum(spoken(l) for l in sc["lines"])
    dur = chars / RATE + GAPS["line"] * (len(sc["lines"]) - 1) + (GAPS["scene"] if i < len(s["scenes"]) else 0)
    total += dur
    beat = sc.get("beat") or "".join(sc["lines"])[:40]
    ft = sc.get("footage") or []
    ft = [ft] if isinstance(ft, (str, dict)) else ft
    ft = [x if isinstance(x, dict) else {"what": x} for x in ft]
    moving = any(x.get("motion") for x in ft); real_n += bool(ft); motion_n += moving
    fs = lambda x: "" if "fullscreen" not in x and not x.get("motion") else (" ▭整幅" if x.get("framing") == "band" else " ⛶全屏") if x.get("fullscreen") else " ▢窗口" if "fullscreen" in x else " ？全屏未写"
    cropped += [f"{sc['id']}：{x.get('what', '')}" for x in ft if x.get("fullscreen") and "framing" not in x and any(k in x.get("what", "") + x.get("src", "") for k in DEVICE)]
    windowed += [f"{sc['id']}：{x.get('what', '')}" + ("" if "fullscreen" in x else "（未写 fullscreen）") for x in ft if x.get("motion") and not x.get("fullscreen")]
    fcell = "；".join(("▶ " if x.get("motion") else "") + x.get("what", "") + (f"（{x['src']}）" if x.get("src") else "") + fs(x) for x in ft) or "（无真实素材）"
    rows.append(f"| {i} | {sc['id']} | {cell(beat)} | {cell(sc.get('visual', '（未写）'))} | {cell(fcell)} | {cell(sc.get('anchors', ''))} | {dur:.0f}s |")

out = [f"# 分镜表：{s.get('title', '')}", ""]
if s.get("central_judgment"): out += [f"**核心判断**：{s['central_judgment']}", ""]
out += ["| # | 幕 | 讲什么 | 画面 | 真实素材（▶ 动态 · ⛶全屏 / ▭整幅 / ▢窗口） | 卡点 | 时长 |", "|---|---|---|---|---|---|---|", *rows, ""]
out += [f"**预计时长**：约 {int(total // 60)} 分 {int(total % 60):02d} 秒（{sum(spoken(l) for sc in s['scenes'] for l in sc['lines']):.0f} 字，按 {RATE:.1f} 字/秒估）",
        f"**音色**：{s.get('voice', 'Charon')}",
        f"**画幅**：" + ("横屏 1920×1080" if s.get("aspect") == "landscape" else "竖屏 1080×1920"),
        *([f"**风格参考**：{s['style_ref']}（references/style-refs.md）"] if s.get("style_ref") else []), ""]
if s.get("design"):   # IP-themed shell (references/storyboard.md): show it with the table so Ray confirms it in the same pass
    d = s["design"]; lab = {"shell": "外壳", "audio": "声音", "boundary": "边界"}
    out += ["**主题外壳**", *[f"- {lab.get(k, k)}：{v}" for k, v in d.items()], ""]
n = len(s["scenes"])
out += [f"**真实素材**：{real_n}/{n} 幕有真实素材，其中 {motion_n} 幕是动态的（录屏 / 视频 / 实跑）", ""]
if motion_n * 2 < n:   # Ray 2026-10-15: audiences tire of drawn animation; most scenes should carry moving real footage
    out += [f"**⚠ 动态真实素材太少**：不到一半的幕有录屏、视频或实跑画面。先按 hyperframes.md「取材」补，缺的列出来问用户要。", ""]
if windowed:   # Ray 2026-10-15: real video in a small camera window lacks impact; full screen is the default
    out += ["**⚠ 这些动态素材装在窗口里**（真实视频默认全屏 `fullscreen: true`；只有需要并排对比时才进窗口，确认后保留）：" + "；".join(windowed), ""]
if cropped:   # Ray 2026-10-16: a cover-cropped clip of a landscape iPhone in hands lost the phone
    out += ["**⚠ 这些全屏素材的主体像是整台设备或宽画面**（横屏裁成竖屏会切掉主体）：" + "；".join(cropped) + "。看一眼参考帧：主体要完整就写 `framing: \"band\"`（整幅横放、上下虚化垫底），裁了也没事就写 `framing: \"cover\"`。", ""]
out += ["## 逐字稿", ""]
for i, sc in enumerate(s["scenes"], 1):
    out += [f"**{i}. {sc['id']}**", "", *[f"> {l}" for l in sc["lines"]], ""]
md = "\n".join(out)
open(os.path.join(PROJ, "storyboard.md"), "w").write(md)
print(md)

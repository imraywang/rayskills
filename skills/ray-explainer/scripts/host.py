"""数字人主持人（可选能力）：只在用户确认要加数字人时用。

script.json 顶层写：
  "host": {"avatar": "ray", "big": [{"scene": "hook", "line": 0}, {"scene": "takeaway", "line": 2}], "model": "pro"}
  - avatar：~/.config/ray-explainer/avatars/<name>/ 里的形象（make_avatar.py 生成）
  - big：大机位的句子（line 从 0 数，和 cue 的 line 一致）。同一幕里相邻的句子合成一段
    可选 "pos": {"x": 660, "y": 1150, "w": 420} 让这一段换个位置 / 大小（默认 x 272, y 1010, w 536），避开这一幕居中的主画面
  - model：pro（1080p，约 $0.115/秒，默认）或 standard（720p，约 $0.056/秒，偶尔生成出多余的贴纸，要抽帧检查）

大机位的句子：形象图 + 这段配音 → Kling AI Avatar 生成说话视频（手势、表情），抠绿幕、拆成帧。
其余时间：主持人缩在左下角，用同一形象的换嘴型图层（拼音韵母 → 口型，按逐字时间切换），不花钱。
两者构图完全一致，大机位在段首段尾和角落之间缩放过渡，缩到角落后换成图层，看不出接缝。
产物写在 <project>/host/：plan.json（overlay.js 读它画主持人）、frames/、avatar/、kling/（缓存）、usage.json。

usage:
  python3 host.py <project> --dry-run   # 列出大机位段落和预计费用，不花钱。先给用户看
  python3 host.py <project>             # 用户同意后再跑：生成 / 复用缓存、抠图、写 plan.json
  python3 host.py <project> --plan-only # 只重算口型和 plan.json（改了稿子重新配音之后用；大机位缓存按音频内容命中）
"""
import hashlib, json, os, random, re, shutil, subprocess, sys, urllib.request

PROJ = os.path.abspath(sys.argv[1]); ARGS = sys.argv[2:]
DRY, PLAN_ONLY = "--dry-run" in ARGS, "--plan-only" in ARGS
script = json.load(open(os.path.join(PROJ, "script.json")))
TL = json.load(open(os.path.join(PROJ, "timeline.json")))
H = script.get("host")
if not H: sys.exit('script.json 没有 "host"：这条片子不加数字人')
AV = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "ray-explainer", "avatars", H.get("avatar", "ray"))
if not os.path.exists(os.path.join(AV, "meta.json")): sys.exit(f"形象不存在：{AV}（先用 make_avatar.py 生成）")
MODELS = {"pro": ("fal-ai/kling-video/ai-avatar/v2/pro", 0.115), "standard": ("fal-ai/kling-video/ai-avatar/v2/standard", 0.0562)}
MODEL, PRICE = MODELS[H.get("model", "pro")]
PROMPT = ("A friendly cartoon explainer host talking directly to the camera with lively, natural expressions: expressive hand "
          "gestures (raising an index finger, open palms, small hand waves), slight head tilts, eyebrows and eyes reacting, smiling "
          "while talking. Keep the flat 2D cartoon style, thick outlines and white sticker border exactly. Static camera, the solid "
          "green background stays perfectly flat and unchanged.")
OUT = os.path.join(PROJ, "host"); os.makedirs(OUT, exist_ok=True)
FW, FH = 536, 960            # 大机位帧尺寸（画面里大机位就是这么大）
LAYOUT = {"big": {"x": 272, "y": 1010, "w": 536}, "corner": {"x": -2, "y": 1560, "w": 386}, "trans": 0.4, "caption_y": 1470}

def zshrc_env(name):
    if os.environ.get(name): return os.environ[name]
    for line in open(os.path.expanduser("~/.zshrc")):
        line = line.strip()
        if line.startswith(f"export {name}="): return line.split("=", 1)[1].strip().strip('"\'')
    sys.exit(f"{name} not set")
def sha(path): return hashlib.sha1(open(path, "rb").read()).hexdigest()
def ff(*a): subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *a], check=True)

# ---------- 大机位段落 ----------
scenes = {s["id"]: s for s in TL["scenes"]}
POS = {(b["scene"], int(b["line"])): b["pos"] for b in H.get("big", []) if b.get("pos")}   # 按句指定大机位位置
picks = sorted({(b["scene"], int(b["line"])) for b in H.get("big", [])}, key=lambda x: (list(scenes).index(x[0]), x[1]))
segs = []
for sid, li in picks:
    if sid not in scenes or li >= len(scenes[sid]["lines"]): sys.exit(f"host.big：{sid} 第 {li} 句不存在（line 从 0 数）")
    l = scenes[sid]["lines"][li]
    if segs and segs[-1]["scene"] == sid and segs[-1]["last"] == li - 1: segs[-1].update(end=l["end"], last=li)
    else: segs.append({"scene": sid, "first": li, "last": li, "start": l["start"], "end": l["end"]})
    if (sid, li) in POS: segs[-1]["big"] = POS[(sid, li)]
for s in segs: s["a"], s["b"] = max(0.0, round(s["start"] - 0.08, 3)), round(min(TL["duration"], s["end"] + 0.15), 3)
total = sum(s["b"] - s["a"] for s in segs)
# Kling 按生成视频的实际时长计费，实测比音频段长约 10%（2026-10 一期：估 21.7 秒，计费 23.7 秒）
print(f"大机位 {len(segs)} 段，共 {total:.1f} 秒，{H.get('model', 'pro')} 预计约 ${total * PRICE * 1.1:.2f}（含约 10% 计费余量；已缓存的段落不再花钱）")
for s in segs: print(f"  {s['scene']} 第 {s['first']}–{s['last']} 句  {s['a']:.2f}–{s['b']:.2f}s  ({s['b'] - s['a']:.1f}s)")
if DRY: sys.exit(0)

# ---------- 生成 / 缓存 / 抠图拆帧 ----------
usage_f = os.path.join(OUT, "usage.json"); usage = json.load(open(usage_f)) if os.path.exists(usage_f) else {}
flat = os.path.join(AV, "flat.png"); os.makedirs(os.path.join(OUT, "kling"), exist_ok=True)
for i, s in enumerate(segs):
    wav = os.path.join(OUT, f"seg{i}.wav")
    ff("-ss", str(s["a"]), "-t", str(s["b"] - s["a"]), "-i", os.path.join(PROJ, "narration.wav"), "-af", "afade=t=out:st=%.3f:d=0.1" % (s["b"] - s["a"] - 0.1), wav)
    key = hashlib.sha1(f"{MODEL}|{sha(flat)}|{sha(wav)}|{PROMPT}".encode()).hexdigest()[:12]; s["key"] = key
    mp4 = os.path.join(OUT, "kling", key + ".mp4")
    if not os.path.exists(mp4):
        if PLAN_ONLY: sys.exit(f"段落 {i} 没有缓存（音频变了），去掉 --plan-only 重新生成")
        os.environ["FAL_KEY"] = zshrc_env("FAL_KEY"); import fal_client
        print(f"Kling 生成段落 {i}（{s['b'] - s['a']:.1f}s）…", flush=True)
        r = fal_client.subscribe(MODEL, arguments={"image_url": fal_client.upload_file(flat), "audio_url": fal_client.upload_file(wav), "prompt": PROMPT})
        urllib.request.urlretrieve(r["video"]["url"], mp4)
        usage[key] = {"model": MODEL, "seconds": round(s["b"] - s["a"], 2), "billed": r.get("duration")}; json.dump(usage, open(usage_f, "w"), indent=1)
    fdir = os.path.join(OUT, "frames", key)
    if not os.path.exists(os.path.join(fdir, "0001.webp")):
        from PIL import Image
        tmp = os.path.join(OUT, "frames", key + "_png"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        ff("-i", mp4, "-frames:v", "1", os.path.join(tmp, "probe.png"))
        g = Image.open(os.path.join(tmp, "probe.png")).convert("RGB").getpixel((6, 6))   # 绿幕颜色取左上角
        ff("-i", mp4, "-t", str(s["b"] - s["a"]), "-an", "-vf",
           f"fps=30,chromakey=0x{g[0]:02X}{g[1]:02X}{g[2]:02X}:0.13:0.06,despill=type=green:mix=0.6:expand=0.1,scale={FW}:{FH},format=rgba",
           os.path.join(tmp, "%04d.png"))
        os.makedirs(fdir, exist_ok=True)
        for f in sorted(x for x in os.listdir(tmp) if re.match(r"\d{4}\.png$", x)):
            Image.open(os.path.join(tmp, f)).save(os.path.join(fdir, f[:-4] + ".webp"), quality=88, method=4)
        shutil.rmtree(tmp)
    s["count"] = len([x for x in os.listdir(fdir) if x.endswith(".webp")])

# ---------- 角落口型：逐字时间 → 拼音韵母 → 口型（A O E I U M，X = 闭嘴） ----------
from pypinyin import pinyin, Style
A_ = {"a", "ai", "an", "ang", "ao", "ia", "ua", "uai", "uan", "uang", "iang", "iao"}
O_ = {"o", "uo", "ou", "iou", "iu", "ong", "iong"}
U_ = {"u", "v", "ü", "un", "vn", "ün", "uen"}
LAT = {**{c: "E" for c in "AHJKFLMNSX"}, **{c: "I" for c in "BCDEGPTVZ"}, "I": "A", "Y": "A", "R": "A", "O": "O", "Q": "U", "U": "U", "W": "U"}
def vis(ch):
    if re.match(r"[A-Za-z]", ch): return None, LAT.get(ch.upper(), "E")
    if not re.match(r"[一-鿿]", ch): return None, "X"
    ini = pinyin(ch, style=Style.INITIALS, strict=False)[0][0]; fin = pinyin(ch, style=Style.FINALS, strict=False)[0][0]
    v = "A" if fin in A_ else "O" if fin in O_ else "U" if fin in U_ else "I" if fin in ("i", "in", "ing") else "E"
    return ("M" if ini in ("b", "p", "m") else None), v
seq = []
for sc in TL["scenes"]:
    for ln in sc["lines"]:
        ch, ts = ln["text"], ln.get("chars") or [ln["start"] + (ln["end"] - ln["start"]) * k / len(ln["text"]) for k in range(len(ln["text"]))]
        for k, c in enumerate(ch):
            a = ts[k]; b = min(ts[k + 1] if k + 1 < len(ch) else ln["end"], a + 0.4)
            pre, v = vis(c)
            if v == "X" or b - a < 0.02: seq.append((a, "X")); continue
            if pre: seq.append((a, "M")); a += max(0.04, 0.3 * (b - a))
            if v == "A" and b - a < 0.17: v = "E"          # 大张嘴只给拖长的 a
            seq.append((a, v))
            if k + 1 == len(ch) or ts[k + 1] - b > 0.12: seq.append((b, "X"))
        seq.append((ln["end"], "X"))
mouth = []
for t, s in sorted(seq):
    if mouth and t - mouth[-1][0] < 0.06: mouth[-1] = [mouth[-1][0], s]; continue
    if mouth and mouth[-1][1] == s: continue
    mouth.append([round(t, 3), s])
random.seed(7); blinks, t = [], 1.3
while t < TL["duration"]: blinks.append(round(t, 2)); t += random.uniform(2.4, 4.2)

# ---------- 形象图层 + plan.json ----------
adir = os.path.join(OUT, "avatar"); os.makedirs(adir, exist_ok=True)
meta = json.load(open(os.path.join(AV, "meta.json")))
for f in ["base.png", *[k + ".png" for k in meta["patches"]]]: shutil.copy(os.path.join(AV, f), adir)
plan = {**LAYOUT, "aspect": FH / FW,
        "avatar": {"dir": "/host/avatar/", **meta},
        "segments": [{"start": s["a"], "end": s["b"], "dir": f"/host/frames/{s['key']}/", "count": s["count"], "fps": 30, **({"big": s["big"]} if s.get("big") else {})} for s in segs],
        "mouth": mouth, "blinks": blinks}
json.dump(plan, open(os.path.join(OUT, "plan.json"), "w"), ensure_ascii=False)
print(f"wrote host/plan.json：{len(segs)} 段大机位，角落口型 {len(mouth)} 次切换，眨眼 {len(blinks)} 次")

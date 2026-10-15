"""数字人主持人：左下角换嘴型是 IP 默认（不花钱）；大机位（MiniMax H3 / Kling）要先 --dry-run 报价、用户确认才生成。

script.json 顶层写：
  "host": {"avatar": "ray", "big": [{"scene": "hook", "line": 0}, {"scene": "takeaway", "line": 2}], "model": "pro"}
  - avatar：~/.config/ray-explainer/avatars/<name>/ 里的形象（make_avatar.py 生成）
  - big：大机位的句子（line 从 0 数，和 cue 的 line 一致）。同一幕里相邻的句子合成一段
    可选 "pos": {"x": 660, "y": 1150, "w": 420} 让这一段换个位置 / 大小（默认 x 272, y 1010, w 536），避开这一幕居中的主画面
    可选 "act": "右手食指指向上方，然后点头"（只对 h3）：这一段的动作；不写就用通用的讲解手势。同一段写在任一句上都算
    横屏（"aspect": "landscape"）的大机位是左下角小圆窗放大：pos 写 {"x", "y", "w", "h"}（默认 x 56, y 604, 420×420）
  - show（横屏）：小圆窗出现的关键句 [{"scene": "hook", "line": 0}, …]，写法同 big、不花钱；大机位句子自动算在内。不在这些句子里时主持人不出现
  - model：h3（默认）、pro 或 standard
    h3：MiniMax H3 图生视频，走 MINIMAX_API_KEY 直连（国内 api.minimax.cn 的 /v2 接口）。形象图 + 动作提示词 → 手势、表情、
        嘴在动，但不按配音对口型（Ray 2026-10-15：大机位要的是手势动作，不要求真的对上嘴型）。768P，单次 4–15 秒，
        超过 15 秒的段落接力生成（下一截的首帧是上一截的末帧）；首帧左右各补 17% 绿边，手伸出原图也不会被裁。自带的音轨丢掉
    pro / standard：Kling AI Avatar（fal），形象图 + 这段配音 → 对上口型的说话视频。pro 1080p 约 $0.115/秒；
        standard 720p 约 $0.056/秒，偶尔生成出多余的贴纸，要抽帧检查

大机位的句子：生成带手势的视频，抠绿幕、拆成帧。
其余时间：主持人缩在左下角，用同一形象的换嘴型图层（拼音韵母 → 口型，按逐字时间切换），不花钱。
两者构图完全一致，大机位在段首段尾和角落之间缩放过渡，缩到角落后换成图层，看不出接缝。
产物写在 <project>/host/：plan.json（overlay.js 读它画主持人）、frames/、avatar/、kling/ 或 h3/（缓存）、usage.json。

usage:
  python3 host.py <project> --dry-run   # 列出大机位段落和预计费用，不花钱。先给用户看
  python3 host.py <project>             # 用户同意后再跑：生成 / 复用缓存、抠图、写 plan.json
  python3 host.py <project> --plan-only # 只重算口型和 plan.json（改了稿子重新配音之后用；大机位缓存按音频内容命中）
"""
import base64, hashlib, json, math, os, random, re, shutil, subprocess, sys, time, urllib.request

PROJ = os.path.abspath(sys.argv[1]); ARGS = sys.argv[2:]
DRY, PLAN_ONLY = "--dry-run" in ARGS, "--plan-only" in ARGS
script = json.load(open(os.path.join(PROJ, "script.json")))
TL = json.load(open(os.path.join(PROJ, "timeline.json")))
H = script.get("host")
if not H: sys.exit('script.json 没有 "host"：这条片子不加数字人')
AV = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "ray-explainer", "avatars", H.get("avatar", "ray"))
if not os.path.exists(os.path.join(AV, "meta.json")): sys.exit(f"形象不存在：{AV}（先用 make_avatar.py 生成）")
# H3 的单价官方没公开（2026-10），按 fal 上 768P 的 $0.08/秒估；按生成时长计费（4–15 秒取整），不是按段落长度
MODELS = {"h3": ("MiniMax-H3", 0.08), "pro": ("fal-ai/kling-video/ai-avatar/v2/pro", 0.115), "standard": ("fal-ai/kling-video/ai-avatar/v2/standard", 0.0562)}
MKEY = H.get("model", "h3")
if MKEY not in MODELS: sys.exit(f'host.model 只能是 {" / ".join(MODELS)}')
MODEL, PRICE = MODELS[MKEY]; IS_H3 = MKEY == "h3"
H3_ACT = "双手抬到胸前做讲解的手势，摊开手掌，轻轻点头"
H3_PROMPT = ("扁平卡通人物面对镜头讲解，嘴巴随说话自然开合，表情生动友好。动作：{act}。"
             "保持原图的扁平 2D 卡通画风、粗黑线条和白色贴纸描边完全不变，身体和头部大小不变。固定机位，不推拉不平移，"
             "纯绿色背景始终平整不变。不要字幕，不要文字，不要新增任何物件。角色在说：「{text}」")
H3_PAD = 132 / 768           # 首帧左右各补的绿边（占形象宽度）：768×1376 → 1032×1376，正好 3:4
PROMPT = ("A friendly cartoon explainer host talking directly to the camera with lively, natural expressions: expressive hand "
          "gestures (raising an index finger, open palms, small hand waves), slight head tilts, eyebrows and eyes reacting, smiling "
          "while talking. Keep the flat 2D cartoon style, thick outlines and white sticker border exactly. Static camera, the solid "
          "green background stays perfectly flat and unchanged.")
OUT = os.path.join(PROJ, "host"); os.makedirs(OUT, exist_ok=True)
FW, FH = 536, 960            # 大机位帧尺寸（画面里大机位就是这么大）
# 版位按 script.json 的 aspect 从 assets/canvas.json 取：竖屏是左下角露头肩 + 大机位站在下半屏；横屏是 Screen Studio 式圆角气泡
ASPECT = script.get("aspect", "portrait")
CV = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "canvas.json")))[ASPECT]["host"]
LAYOUT = {**{k: v for k, v in CV.items() if not k.startswith("_")}, "trans": 0.4}

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
ACT = {(b["scene"], int(b["line"])): b["act"] for b in H.get("big", []) if b.get("act")}   # 按句指定 h3 动作
picks = sorted({(b["scene"], int(b["line"])) for b in H.get("big", [])}, key=lambda x: (list(scenes).index(x[0]), x[1]))
segs = []
for sid, li in picks:
    if sid not in scenes or li >= len(scenes[sid]["lines"]): sys.exit(f"host.big：{sid} 第 {li} 句不存在（line 从 0 数）")
    l = scenes[sid]["lines"][li]
    if segs and segs[-1]["scene"] == sid and segs[-1]["last"] == li - 1: segs[-1].update(end=l["end"], last=li)
    else: segs.append({"scene": sid, "first": li, "last": li, "start": l["start"], "end": l["end"]})
    if (sid, li) in POS: segs[-1]["big"] = POS[(sid, li)]
    if (sid, li) in ACT: segs[-1]["act"] = ACT[(sid, li)]
for s in segs:
    s["a"], s["b"] = max(0.0, round(s["start"] - 0.08, 3)), round(min(TL["duration"], s["end"] + 0.15), 3)
    s["text"] = "".join(scenes[s["scene"]]["lines"][k]["text"] for k in range(s["first"], s["last"] + 1))
def h3_chunks(L):   # 每截 4–15 秒的整数，接力盖住整段；返回 [(这一截要用的秒数, 生成秒数)]
    n = math.ceil(L / 15); part = L / n
    return [(part, max(4, math.ceil(part))) for _ in range(n)]
total = sum(s["b"] - s["a"] for s in segs)
if IS_H3:   # H3 按生成时长计费：每截向上取整、最少 4 秒
    billed = sum(g for s in segs for _, g in h3_chunks(s["b"] - s["a"]))
    print(f"大机位 {len(segs)} 段，共 {total:.1f} 秒，h3 计费约 {billed} 秒，预计约 ${billed * PRICE:.2f}（单价按 $0.08/秒估；已缓存的段落不再花钱）")
else:   # Kling 按生成视频的实际时长计费，实测比音频段长约 10%（2026-10 一期：估 21.7 秒，计费 23.7 秒）
    print(f"大机位 {len(segs)} 段，共 {total:.1f} 秒，{MKEY} 预计约 ${total * PRICE * 1.1:.2f}（含约 10% 计费余量；已缓存的段落不再花钱）")
for s in segs: print(f"  {s['scene']} 第 {s['first']}–{s['last']} 句  {s['a']:.2f}–{s['b']:.2f}s  ({s['b'] - s['a']:.1f}s)" + (f"  动作：{s.get('act', H3_ACT)}" if IS_H3 else ""))
if DRY: sys.exit(0)

# ---------- 生成 / 缓存 / 抠图拆帧 ----------
usage_f = os.path.join(OUT, "usage.json"); usage = json.load(open(usage_f)) if os.path.exists(usage_f) else {}
flat = os.path.join(AV, "flat.png"); CACHE = os.path.join(OUT, "h3" if IS_H3 else "kling"); os.makedirs(CACHE, exist_ok=True)

def h3_first_frame():   # flat.png 左右补绿边成 3:4，绿色取原图左上角
    from PIL import Image
    p = os.path.join(CACHE, f"first_{sha(flat)[:8]}.png")
    if not os.path.exists(p):
        im = Image.open(flat).convert("RGB"); w, h = im.size; pad = round(w * H3_PAD)
        c = Image.new("RGB", (w + 2 * pad, h), im.getpixel((6, 6))); c.paste(im, (pad, 0)); c.save(p)
    return p

def h3_call(method, path, body=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import minimax_api as mm
    req = urllib.request.Request(mm.HOST + path, json.dumps(body).encode() if body else None, method=method,
                                 headers={"Authorization": "Bearer " + mm._env("MINIMAX_API_KEY"), "Content-Type": "application/json"})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: sys.exit(f"MiniMax {path}: HTTP {e.code} {e.read().decode()[:300]}")

def h3_gen(first, prompt, dur, out):   # 提交 → 轮询 → 下载；首帧用 data URL，不用另外上传
    img = "data:image/png;base64," + base64.b64encode(open(first, "rb").read()).decode()
    r = h3_call("POST", "/v2/video_generation", {"model": MODEL, "resolution": "768P", "duration": dur, "ratio": "3:4",
                "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": img}, "role": "first_frame"}]})
    tid = r.get("task_id") or sys.exit(f"H3 提交失败：{r}")
    for _ in range(240):
        time.sleep(10); t = h3_call("GET", f"/v2/query/video_generation/{tid}")["task"]
        if t["status"] == "succeeded": urllib.request.urlretrieve(t["content"]["url"], out); return t.get("usage", {})
        if t["status"] == "failed": sys.exit(f"H3 任务 {tid} 失败：{t}")
    sys.exit(f"H3 任务 {tid} 40 分钟没出结果")

for i, s in enumerate(segs):
    L = s["b"] - s["a"]
    if IS_H3:   # 不用配音：按这段的字和动作生成；缓存按 形象 + 提示词 + 时长 命中
        prompt = H3_PROMPT.format(act=s.get("act", H3_ACT), text=s["text"]); first = h3_first_frame()
        key = hashlib.sha1(f"{MODEL}|{sha(flat)}|{prompt}|{H3_PAD}|{L:.1f}".encode()).hexdigest()[:12]; s["key"] = key
        mp4 = os.path.join(CACHE, key + ".mp4")
        if not os.path.exists(mp4):
            if PLAN_ONLY: sys.exit(f"段落 {i} 没有缓存（句子或时长变了），去掉 --plan-only 重新生成")
            parts = []
            for j, (use, dur) in enumerate(h3_chunks(L)):
                part = os.path.join(CACHE, f"{key}_{j}.mp4")
                if not os.path.exists(part):
                    print(f"H3 生成段落 {i}{f' 第 {j + 1} 截' if j else ''}（生成 {dur}s，用 {use:.1f}s）…", flush=True)
                    u = h3_gen(first, prompt, dur, part)
                    usage[f"{key}_{j}"] = {"model": MODEL, "seconds": round(use, 2), "billed": u.get("output_seconds", dur)}; json.dump(usage, open(usage_f, "w"), indent=1)
                parts.append((part, use))
                first = os.path.join(CACHE, f"{key}_{j}_last.png")   # 下一截从这一截用到的最后一帧接着动
                ff("-ss", f"{max(0, use - 0.05):.3f}", "-i", part, "-frames:v", "1", "-vf", "scale=1032:1376", first)
            lst = os.path.join(CACHE, key + "_list.txt")
            open(lst, "w").write("".join(f"file '{p}'\ninpoint 0\noutpoint {u_:.3f}\n" for p, u_ in parts))
            ff("-f", "concat", "-safe", "0", "-i", lst, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", mp4)
    else:
        wav = os.path.join(OUT, f"seg{i}.wav")
        ff("-ss", str(s["a"]), "-t", str(L), "-i", os.path.join(PROJ, "narration.wav"), "-af", "afade=t=out:st=%.3f:d=0.1" % (L - 0.1), wav)
        key = hashlib.sha1(f"{MODEL}|{sha(flat)}|{sha(wav)}|{PROMPT}".encode()).hexdigest()[:12]; s["key"] = key
        mp4 = os.path.join(CACHE, key + ".mp4")
        if not os.path.exists(mp4):
            if PLAN_ONLY: sys.exit(f"段落 {i} 没有缓存（音频变了），去掉 --plan-only 重新生成")
            os.environ["FAL_KEY"] = zshrc_env("FAL_KEY"); import fal_client
            print(f"Kling 生成段落 {i}（{L:.1f}s）…", flush=True)
            r = fal_client.subscribe(MODEL, arguments={"image_url": fal_client.upload_file(flat), "audio_url": fal_client.upload_file(wav), "prompt": PROMPT})
            urllib.request.urlretrieve(r["video"]["url"], mp4)
            usage[key] = {"model": MODEL, "seconds": round(L, 2), "billed": r.get("duration")}; json.dump(usage, open(usage_f, "w"), indent=1)
    if IS_H3: s["pad"] = [H3_PAD, 0, H3_PAD, 0]   # 帧比形象图左右各宽 H3_PAD：渲染时按这个往外画，形象位置和角落图层对齐
    fdir = os.path.join(OUT, "frames", key)
    if not os.path.exists(os.path.join(fdir, "0001.webp")):
        from PIL import Image
        tmp = os.path.join(OUT, "frames", key + "_png"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        ff("-i", mp4, "-frames:v", "1", os.path.join(tmp, "probe.png"))
        g = Image.open(os.path.join(tmp, "probe.png")).convert("RGB").getpixel((6, 6))   # 绿幕颜色取左上角
        fw = round(FW * (1 + 2 * H3_PAD)) if IS_H3 else FW
        # H3 整帧偏绿（白描边约 237,252,242），ffmpeg despill 会把白边染成淡紫；改成逐像素把绿压到不超过红蓝里较大的那个
        spill = "" if IS_H3 else ",despill=type=green:mix=0.6:expand=0.1"
        ff("-i", mp4, "-t", str(s["b"] - s["a"]), "-an", "-vf",
           f"fps=30,chromakey=0x{g[0]:02X}{g[1]:02X}{g[2]:02X}:0.13:0.06{spill},scale={fw}:{FH},format=rgba",
           os.path.join(tmp, "%04d.png"))
        os.makedirs(fdir, exist_ok=True)
        import numpy as np
        for f in sorted(x for x in os.listdir(tmp) if re.match(r"\d{4}\.png$", x)):
            im = Image.open(os.path.join(tmp, f))
            if IS_H3: a_ = np.array(im); a_[..., 1] = np.minimum(a_[..., 1], np.maximum(a_[..., 0], a_[..., 2])); im = Image.fromarray(a_)
            im.save(os.path.join(fdir, f[:-4] + ".webp"), quality=88, method=4)
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
# 横屏气泡换边：script.json 某一幕写 "host_side": "right" / "left"，从这一幕开头起气泡换到那一角（主画面在哪边、气泡去另一边）
sides = []
if "bubble" in LAYOUT:
    starts = {s["id"]: s["start"] for s in TL["scenes"]}
    sides = [[0, "left"]]
    for i, sc in enumerate(script["scenes"]):
        sd = sc.get("host_side")
        if sd not in (None, "left", "right"): sys.exit(f'幕 {sc["id"]}：host_side 只能是 "left" 或 "right"')
        if not sd or sd == sides[-1][1]: continue
        if i == 0: sides = [[0, sd]]                     # 第一幕就在右边：开场直接从右下滑入
        else: sides.append([round(starts[sc["id"]], 3), sd])
# 横屏小圆窗只在关键句出现：host.show 标的句子 + 大机位句子；同一幕相邻的句子、间隔不到 show_merge 秒的段合成一段
show = None
if "bubble" in LAYOUT:
    th = script.get("theme"); th = th if isinstance(th, str) else (th or {}).get("name")
    fill, ring = {"ray-ip-dark": ("#2A2C2C", "#0B6B69")}.get(th, ("#FFFFFF", "#054C4C"))   # 卡片色 + 墨绿细圈（深灰底上墨绿提亮一档）
    LAYOUT["bubble"] = {**LAYOUT["bubble"], "fill": fill, "ring": ring}
    marks = sorted({(b["scene"], int(b["line"])) for b in [*H.get("show", []), *H.get("big", [])]}, key=lambda x: (list(scenes).index(x[0]), x[1]))
    show = []
    for sid, li in marks:
        if sid not in scenes or li >= len(scenes[sid]["lines"]): sys.exit(f"host.show：{sid} 第 {li} 句不存在（line 从 0 数）")
        l = scenes[sid]["lines"][li]
        if show and l["start"] - show[-1][1] < LAYOUT.get("show_merge", 1.2): show[-1][1] = round(l["end"], 3)
        else: show.append([round(l["start"], 3), round(l["end"], 3)])
    if not show: print("注意：横屏主持人只在关键句出现，host.show 和 host.big 都是空的 → 全片不出现。在 host.show 里标 3–6 句（钩子、金句、结尾）")
    else: print(f"横屏小圆窗出现 {len(show)} 段，共 {sum(b - a for a, b in show):.1f} 秒")
plan = {**LAYOUT, "aspect": FH / FW, **({"sides": sides} if sides else {}), **({"show": show} if show is not None else {}),
        "avatar": {"dir": "/host/avatar/", **meta},
        "segments": [{"start": s["a"], "end": s["b"], "dir": f"/host/frames/{s['key']}/", "count": s["count"], "fps": 30, **({"big": s["big"]} if s.get("big") else {}), **({"pad": s["pad"]} if s.get("pad") else {})} for s in segs],
        "mouth": mouth, "blinks": blinks}
json.dump(plan, open(os.path.join(OUT, "plan.json"), "w"), ensure_ascii=False)
print(f"wrote host/plan.json：{len(segs)} 段大机位，角落口型 {len(mouth)} 次切换，眨眼 {len(blinks)} 次")

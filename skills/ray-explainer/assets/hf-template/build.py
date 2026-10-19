#!/usr/bin/env python3
"""生成 index.html：旁白（含插入的原声）+ 配乐（给人声让路）、各幕插槽、章节进度条顶栏、逐条字幕、音效、角落数字人。
场景动画在 compositions/s-<id>.html（读 window.BEATS[id]，不内联时间）；音效在 compositions/s-<id>.sfx.json：
  [[<时刻>, "name", vol], ...]，<时刻> 优先写锚点，配音重做后自动跟上：
    {"line": 0, "phrase": "拍到", "off": 0.05}   这一幕第 line 句里 phrase 开口的时刻 + off
    {"clip": "c1", "t": 2.8}                     原声 c1 开始后 t 秒
    {"cap": 3, "off": 0}                         这一幕第 cap 条字幕出现的时刻 + off
    12.4                                         幕内秒（不推荐：重新配音后会错位）
  文件在 assets/audio/<name>.mp3。
场景里 <video>/<audio> 的 data-start 也写锚点，每次构建换算成幕内秒（写回场景文件，标签里留着 data-anchor-start 供下次重算）：
    data-start="{{line:2}}"  {{phrase:1:订金}}  {{clip:c1}}  {{clip:c1:end}}  {{cap:4}}   可带偏移 {{line:2+0.3}}
narration.wav 比 assets/audio/narration.m4a 新（删幕、重配音之后）会自动重新编码。
用法：python3 make_beats.py && python3 build.py        COVER=1 python3 build.py → 封面版（无字幕、无数字人、加封面字）"""
import json, os, html, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
B = json.load(open(os.path.join(HERE, "beats.json")))
SC, TOTAL, NARR = B["scenes"], B["total"], B["narration"]
SCRIPT = json.load(open(os.path.join(HERE, "..", "script.json")))
COVER = bool(os.environ.get("COVER"))
# 画布：script.json 的 "aspect"（不写 = 竖屏 1080×1920；"landscape" = 横屏 1920×1080）。版位在 canvas.json（项目 hf/ 里的拷贝，没有就读 skill 里的）
_cv = next(p for p in (os.path.join(HERE, "canvas.json"), os.path.expanduser("~/.claude/skills/ray-explainer/assets/canvas.json")) if os.path.exists(p))
ASPECT = SCRIPT.get("aspect", "portrait"); CV = json.load(open(_cv))[ASPECT]; CW, CH, HFV = CV["W"], CV["H"], CV["hf"]

# ───────────── 本片专属（每片改这一段，其余不动）─────────────
DARK = SCRIPT.get("theme") == "ray-ip-dark"      # 底色、顶栏按 script.json 的 theme 取；2026-10-15 深色片沿用浅色顶栏，整条看不见
BG, FG = ("#1C1D1D", "#F3F3F0") if DARK else ("#F3F3F0", "#111111")   # 与 assets/style.css 的底色、正文色一致
TB_INK, TB_DIM, TB_TRACK = ("#F3F3F0", "#9A9A96", "rgba(243,243,240,0.18)") if DARK else ("#111111", "#8C8C8C", "rgba(17,17,17,0.14)")   # 顶栏字 / 次字 / 进度槽
TOPBAR_RIGHT = ""                                 # 顶栏右侧的小字（栏目名 / 本期名），留空不显示
EXTRA_JS = []                                     # 场景要用的全局数据脚本，如 ["assets/data.js"]（window.DATA）
CAP_TOP = None                                    # 字幕带顶；None = 画布默认（竖屏 1420，带高 150，有角落数字人时 ≤1420、没有可放到 1500；横屏 930）
STAGE_FIT = None                                  # 旧片子的场景按 y 132–1408 画的：设 (132, 1408) 就把整个舞台缩放平移进 y 300–1490
COVER_HTML = ""                                   # 封面版额外叠加的大字（用 ray-cover 出封面时留空）
COVER_T = 0.0                                     # 封面取哪一秒（publish.py 读 script.json 的 cover_t，两处保持一致）
BGM = "assets/audio/bgm.m4a"                      # gen_bgm.py → mix_bgm.py 的产物（已按剧情做好包络）；没有配乐设为 None
BGM_LEN, BGM_VOL = 0.0, 0.35                      # 配乐长度（0 = 和片子一样长；比片子短会在尾部接第二段）、音量
# ────────────────────────────────────────────────────────────────

if BGM and not os.path.exists(os.path.join(HERE, BGM)):
    print(f"WARN: {BGM} 不存在，这次不带配乐（先跑 gen_bgm.py / mix_bgm.py）"); BGM = None

# 配乐包络是按某一版时间线烧进去的（原声静音、分段收放、片尾淡出）。重配音、插原声、删幕之后时间线变了，
# 就按 bgm/mix.json 记的源文件自动重跑 mix_bgm.py，不让旧包络进成片（2026-10-18 原声下的配乐从静音变成 -32 dB，渲完才发现）
_MIX, _TLF = os.path.join(HERE, "..", "bgm", "mix.json"), os.path.join(HERE, "..", "timeline.json")
if BGM and os.path.exists(_MIX) and os.path.exists(_TLF):
    _tl, _mix = json.load(open(_TLF)), json.load(open(_MIX))
    _sig = {"total": round(_tl["scenes"][-1]["end"] + 0.4, 2), "scenes": {s["id"]: round(s["start"], 2) for s in _tl["scenes"]},
            "clips": [[c["id"], round(c["start"], 2), round(c["end"], 2)] for c in _tl.get("clips", [])]}
    if _sig != _mix.get("sig"):
        print("bgm: 时间线和上次混音时不一样（重配音 / 原声位置变了），按 bgm/mix.json 自动重跑 mix_bgm.py")
        _mb = os.path.expanduser("~/.claude/skills/ray-explainer/scripts/mix_bgm.py")
        r = subprocess.run([sys.executable, _mb, os.path.join(HERE, ".."), _mix["src"]], capture_output=True, text=True)
        if r.returncode: raise SystemExit(f"bgm 重混失败，先手动跑 mix_bgm.py：{(r.stderr or r.stdout).strip()[-300:]}")
        print("bgm: " + r.stdout.strip().splitlines()[-1])
elif BGM and not os.path.exists(_MIX):
    print("WARN: 没有 bgm/mix.json（旧版 mix_bgm.py 混的），构建时查不了配乐包络是否过期；重配音后记得重跑 mix_bgm.py")

# 旁白音频跟着配音走：2026-10-15 删幕重配后 m4a 还是旧的，音画错位，audio_check 还误报“配乐太响”
WAV, M4A = os.path.join(HERE, "..", "narration.wav"), os.path.join(HERE, "assets", "audio", "narration.m4a")
if os.path.exists(WAV) and (not os.path.exists(M4A) or os.path.getmtime(WAV) > os.path.getmtime(M4A)):
    os.makedirs(os.path.dirname(M4A), exist_ok=True)
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", WAV, "-c:a", "aac", "-b:a", "192k", M4A], capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"narration.wav 比 narration.m4a 新，重新编码失败：{r.stderr.strip()[-300:]}")
    print("narration.m4a: 已按新的 narration.wav 重新编码")

# ── 顶栏：按章节分段的视频进度条 + 当前章节小标题（script.json 的 "chapters"；没写就每幕一段、不显示小标题）──
SIG = {sc["id"] for sc in SCRIPT["scenes"] if sc.get("sig")}
starts = {s["id"]: (0.0 if i == 0 else s["start"]) for i, s in enumerate(SC)}
ends = {s["id"]: (SC[i + 1]["start"] if i + 1 < len(SC) else TOTAL) for i, s in enumerate(SC)}
chap_def = SCRIPT.get("chapters") or [{"title": "", "scenes": [s["id"]]} for s in SC]
CHAPS = [(c.get("title", ""), starts[c["scenes"][0]], ends[c["scenes"][-1]]) for c in chap_def]
CAP_TOP = HFV["cap_top"] if CAP_TOP is None else CAP_TOP
X0, X1, GAP = HFV["bar_x0"], HFV["bar_x1"], 10
span = X1 - X0 - GAP * (len(CHAPS) - 1)
named = any(t for t, _, _ in CHAPS)
# 顶栏底板是上深下透的渐变：真实画面一直铺到进度条下面（Ray 2026-10-18 电视去广告那期），不再压一条实心色带
# 字幕样式用 #root > .cap 限定：2026-10-18 本期 style.css 里给草图写的 .cap 漏进成片，字幕黑底变成满宽长条
CHROME_CSS = """
#topbar { position: absolute; left: 0; right: 0; top: 0; height: %(tbh)spx; z-index: 50; --tb-ink: %(ink)s; --tb-dim: %(dim)s; --tb-track: %(track)s; --tb-bg: %(bg)s; }
#topbar .tb-back { position: absolute; left: 0; right: 0; top: 0; height: %(tbh)spx; background: linear-gradient(to bottom, color-mix(in srgb, var(--tb-bg) 62%%, transparent) 0, color-mix(in srgb, var(--tb-bg) 38%%, transparent) 66%%, transparent 100%%); }
#topbar .tb-no { position: absolute; left: %(x0)spx; top: %(noy)spx; font-family: "JetBrains Mono", monospace; font-size: 26px; letter-spacing: .08em; color: var(--tb-dim); }
#topbar .tb-t { position: absolute; left: %(tx)spx; top: %(ty)spx; font-family: "HeiBold", sans-serif; font-weight: 700; font-size: %(ts)spx; color: var(--tb-ink); opacity: 0; white-space: nowrap; }
#topbar .tb-r { position: absolute; right: %(x0)spx; top: %(noy)spx; font-family: "JetBrains Mono", "HeiBold", monospace; font-size: 24px; letter-spacing: .12em; color: var(--tb-dim); }
#topbar .tb-seg { position: absolute; top: %(segy)spx; height: 8px; border-radius: 4px; background: var(--tb-track); overflow: hidden; }
#topbar .tb-seg i { position: absolute; left: 0; top: 0; bottom: 0; width: 100%%; background: var(--tb-ink); transform-origin: left center; }
#root > .cap span small { display: block; font-family: "JetBrains Mono", monospace; font-weight: 400; font-size: 26px; line-height: 1.35; color: #BDBDB8; margin-top: 6px; }
""" % {"bg": BG, "ink": TB_INK, "dim": TB_DIM, "track": TB_TRACK, "tbh": HFV["topbar_h"], "x0": X0, "noy": HFV["no_y"], "tx": X0 + 108, "ty": HFV["title_y"], "ts": HFV["title_size"], "segy": HFV["seg_y"]}
segs, titles, x = [], [], X0
for k, (t, a0, a1) in enumerate(CHAPS):
    w = span * (a1 - a0) / TOTAL
    segs.append(f'<div class="tb-seg" style="left:{x:.1f}px;width:{w:.1f}px"><i id="tbs{k}"></i></div>')
    if named: titles.append(f'<div class="tb-t" id="tbt{k}">{html.escape(t)}</div>')
    x += w + GAP
TOPBAR = HFV.get("topbar", True)   # 横屏不放进度条和小标题（Ray 2026-10-14）
CHROME_HTML = ('    <div id="topbar"><div class="tb-back"></div>' + ('<div class="tb-no" id="tbno"></div>' if named else "") + "".join(titles)
               + (f'<div class="tb-r">{html.escape(TOPBAR_RIGHT)}</div>' if TOPBAR_RIGHT else "") + "".join(segs) + "</div>")
CHROME_TWEENS = []
if not TOPBAR: CHROME_HTML = ""
for k, (t, a0, a1) in enumerate(CHAPS if TOPBAR else []):
    CHROME_TWEENS.append(f'tl.fromTo("#tbs{k}", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {a1 - a0:.3f}, ease: "none" }}, {a0:.3f});')
    if named:
        CHROME_TWEENS.append(f'tl.fromTo("#tbt{k}", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }}, {a0:.3f});')
        CHROME_TWEENS.append(f'tl.set("#tbno", {{ textContent: "{k + 1:02d}/{len(CHAPS):02d}" }}, {a0:.3f});')
        if k + 1 < len(CHAPS):
            CHROME_TWEENS.append(f'tl.set("#tbt{k}", {{ opacity: 0 }}, {a1:.3f});')
for sid in sorted(SIG, key=starts.get) if TOPBAR else []:   # 签名幕（整屏墨绿）：顶栏换暖白（按时间排，输出稳定）
    CHROME_TWEENS.append(f'tl.set("#topbar", {{ "--tb-ink": "#F3F3F0", "--tb-dim": "#9CC2BF", "--tb-track": "rgba(243,243,240,0.22)", "--tb-bg": "#054C4C" }}, {starts[sid]:.3f});')
    if ends[sid] < TOTAL - 0.01:
        CHROME_TWEENS.append(f'tl.set("#topbar", {{ "--tb-ink": "{TB_INK}", "--tb-dim": "{TB_DIM}", "--tb-track": "{TB_TRACK}", "--tb-bg": "{BG}" }}, {ends[sid]:.3f});')


def sfx_time(s, t):
    """sfx 时刻：数字 = 幕内秒；dict = 锚点（见文件头）。返回幕内秒。"""
    if not isinstance(t, dict): return float(t)
    off = float(t.get("off", 0))
    if "clip" in t:
        c = next((c for c in s.get("clips", []) if c["id"] == t["clip"]), None)
        if not c: raise SystemExit(f'sfx 锚点找不到：原声 {t["clip"]} 不在幕 {s["id"]} 里（BEATS[id].clips 只含落在本幕的原声）')
        return c["start"] + float(t.get("t", 0)) + off
    if "cap" in t: return s["caps"][int(t["cap"])]["a"] + off
    ln = s["lines"][int(t.get("line", 0))]
    i = ln["text"].find(t["phrase"]) if t.get("phrase") else 0
    if i < 0: raise SystemExit(f'sfx 锚点找不到：幕 {s["id"]} 第 {t.get("line", 0)} 句里没有「{t["phrase"]}」')
    return ln["chars"][min(i, len(ln["chars"]) - 1)] + off


ANCHOR = re.compile(r'data-start="\{\{([^}]+)\}\}"|data-anchor-start="([^"]+)" data-start="[^"]*"')


def anchor_time(s, spec):
    """data-start 锚点（见文件头）→ 幕内秒。"""
    m = re.fullmatch(r"\s*(.+?)\s*(?:([+-])\s*(\d+(?:\.\d+)?))?\s*", spec)
    off = float(m.group(3) or 0) * (-1 if m.group(2) == "-" else 1)
    kind, *a = m.group(1).split(":", 2)
    if kind == "line" and len(a) == 1: t = {"line": a[0]}
    elif kind == "phrase" and len(a) == 2: t = {"line": a[0], "phrase": a[1]}
    elif kind == "cap" and len(a) == 1: t = {"cap": a[0]}
    elif kind == "clip" and a and a[1:] in ([], ["end"]):
        t = {"clip": a[0]}
        if a[1:]:   # 原声结束
            c = next((c for c in s.get("clips", []) if c["id"] == a[0]), None)
            if not c: raise SystemExit(f'data-start 锚点找不到：原声 {a[0]} 不在幕 {s["id"]} 里')
            return c["end"] + off
    else: raise SystemExit(f'data-start 锚点写错了：幕 {s["id"]} 的 {{{{{spec}}}}}（可用 line:N / phrase:N:词 / clip:id / clip:id:end / cap:N，可加 +0.3）')
    return sfx_time(s, t) + off


def resolve_anchors(s, path):
    """把场景文件里视频的 data-start 锚点换成这次配音的幕内秒；写死数字的、慢放过头的列出来。"""
    src = open(path).read()
    out = ANCHOR.sub(lambda m: f'data-anchor-start="{m.group(1) or m.group(2)}" data-start="{anchor_time(s, m.group(1) or m.group(2)):.3f}"', src)
    if out != src: open(path, "w").write(out)
    fixed, slow = [], []
    for tag in re.findall(r"<(?:video|audio)\b[^>]*>", out):
        vid = (re.search(r'id="([^"]+)"', tag) or [None, "?"])[1]
        st, rate = re.search(r'data-start="([\d.]+)"', tag), re.search(r'data-playback-rate="([\d.]+)"', tag)
        if st and "data-anchor-start" not in tag and float(st[1]) > 0: fixed.append(vid)
        if rate and float(rate[1]) < 0.35: slow.append(f"{vid} {rate[1]}")
    name = os.path.basename(path)
    if fixed: print(f"WARN: {name} 有 {len(fixed)} 个视频 data-start 写死秒数，改配音会错位，改成 {{{{line:N}}}} / {{{{clip:id}}}} 锚点：{' '.join(fixed)}")
    if slow: print(f"WARN: {name} 慢放低于 0.35 倍会一卡一卡，换一段素材或循环：{'、'.join(slow)}")


slots, caps, sfx, tweens = [], [], [], list(CHROME_TWEENS)
for i, s in enumerate(SC):
    start, end = s["start"], (SC[i + 1]["start"] if i + 1 < len(SC) else TOTAL)
    sid = f"s-{s['id']}"
    if os.path.exists(os.path.join(HERE, "compositions", sid + ".html")):
        resolve_anchors(s, os.path.join(HERE, "compositions", sid + ".html"))
        slots.append(f'    <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{start:.3f}" data-duration="{end - start:.3f}" data-track-index="1" data-width="{CW}" data-height="{CH}"></div>')
    for c in ([] if COVER else s["caps"]):
        a, b = s["start"] + c["a"], s["start"] + c["b"]
        k = len(caps)
        inner = html.escape(c["s"]) + (f'<small>{html.escape(c["en"])}</small>' if c.get("en") else "")   # 原声字幕：中文大字 + 英文原句
        caps.append(f'    <div id="cap{k}" class="cap clip" data-start="{a:.3f}" data-duration="{max(0.25, b - a):.3f}" data-track-index="9"><span>{inner}</span></div>')
        tweens.append(f'tl.fromTo("#cap{k} span", {{ y: 16, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.14, ease: "power2.out" }}, {a:.3f});')
    fx = os.path.join(HERE, "compositions", sid + ".sfx.json")
    for t, name, vol in (json.load(open(fx)) if os.path.exists(fx) else []):
        at = s["start"] + sfx_time(s, t)
        if 0 <= at <= TOTAL - 0.3:
            sfx.append(f'    <audio id="sfx{len(sfx)}" src="assets/audio/{name}.mp3" data-start="{at:.3f}" data-track-index="{20 + len(sfx)}" data-volume="{vol}"></audio>')

stage_open = stage_close = ""
# 横屏字幕：白字 + 黑描边 + 柔和阴影，无底框（小Lin说、差评、漫士的做法）
CAP_OUTLINE_CSS = ("""
      #root > .cap span { background: none; padding: 0 12px; color: #FFFFFF; -webkit-text-stroke: 9px rgba(0,0,0,0.92); paint-order: stroke fill;
        text-shadow: 0 3px 14px rgba(0,0,0,0.45); }""" if HFV.get("cap_style") == "outline" else "")
if STAGE_FIT and ASPECT == "portrait":   # 舞台整体缩放进安全区（只用于竖屏旧片子）；场景自己的底色会跟着缩，外面露出的是 #root 的 BG
    a, b = STAGE_FIT; k = (1490 - 300) / (b - a); ty = 300 - k * a
    stage_open = f'    <div id="stage" style="position:absolute;left:0;top:0;width:1080px;height:1920px;transform:translate(0px,{ty:.1f}px) scale({k:.4f});transform-origin:540px 0px">'
    stage_close = "    </div>"
if SCRIPT.get("host") and not COVER and not os.path.exists(os.path.join(HERE, "compositions", "s-host.html")):   # 2026-10-18 漏跑 host_build.py，第一版成片没有角落主持人
    print("WARN: script.json 有 host，但 compositions/s-host.html 不存在 —— 先跑 host.py --plan-only（或 host.py）和 python3 host_build.py，否则成片没有角落主持人")
host = ""
if os.path.exists(os.path.join(HERE, "compositions", "s-host.html")) and not COVER:   # host_build.py 生成
    host = f'    <div id="s-host" data-composition-id="s-host" data-composition-src="compositions/s-host.html" data-start="0" data-duration="{TOTAL}" data-track-index="8" data-width="{CW}" data-height="{CH}"></div>'
bgm = []
if BGM:
    first = min(TOTAL, BGM_LEN or TOTAL)
    bgm.append(f'    <audio id="bgm1" src="{BGM}" data-start="0" data-duration="{first:.3f}" data-track-index="3" data-volume="{BGM_VOL}"></audio>')
    if BGM_LEN and BGM_LEN < TOTAL:   # 配乐不够长：从中段接第二段，重叠 0.4 秒
        bgm.append(f'    <audio id="bgm2" src="{BGM}" data-start="{BGM_LEN - 0.4:.3f}" data-media-start="40" data-duration="{TOTAL - BGM_LEN + 0.4:.3f}" data-track-index="4" data-volume="{BGM_VOL}"></audio>')
extra_js = "\n".join(f'    <script src="{p}"></script>' for p in EXTRA_JS)

doc = f'''<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={CW}, height={CH}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script src="assets/beats.js"></script>
{extra_js}
    <link rel="stylesheet" href="assets/style.css" />
    <style>
      @font-face {{ font-family: "HeiHeavy"; src: url("assets/fonts/NotoSansSC-900.woff") format("woff"); font-weight: 900; }}
      @font-face {{ font-family: "HeiBold"; src: url("assets/fonts/NotoSansSC-700.woff") format("woff"); font-weight: 700; }}
      @font-face {{ font-family: "Hei"; src: url("assets/fonts/NotoSansSC-500.woff") format("woff"); font-weight: 500; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {CW}px; height: {CH}px; overflow: hidden; background: {BG}; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; color: {FG}; background: {BG}; }}
      #root > .cap {{ position: absolute; left: 50px; right: 50px; top: {CAP_TOP}px; height: {HFV["cap_h"]}px; min-height: 0; z-index: 60; display: flex; align-items: center; justify-content: center; background: none; border-radius: 0; padding: 0; }}
      #root > .cap span {{ display: inline-block; max-width: {HFV["cap_maxw"]}px; padding: 14px 36px; border-radius: 14px; background: rgba(17,17,17,0.88);
        font-family: "HeiBold", sans-serif; font-weight: 700; font-size: {HFV["cap_size"]}px; line-height: 1.25; color: #F3F3F0; text-align: center; }}
      {CHROME_CSS}{CAP_OUTLINE_CSS}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{CW}" data-height="{CH}">
    <audio id="narration" src="assets/audio/narration.m4a" data-start="0" data-duration="{NARR}" data-track-index="0" data-volume="1"></audio>
{chr(10).join(bgm)}
{stage_open}
{chr(10).join(slots)}
{stage_close}
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
print(f"index.html: {len(slots)} scenes, {len(caps)} captions, {len(sfx)} sfx, {len(CHAPS)} chapters, total {TOTAL}s" + (" [COVER]" if COVER else ""))
if len(sfx) > 15: print(f"WARN: {len(sfx)} 个音效偏多（Ray 偏好全片十几个，只标关键节点）")

# 配乐给人声让路（hyperframes-audio 的 carve）；每次重建都重新刻，因为上面整页重写了 index.html
CARVE = os.path.expanduser("~/.claude/skills/hyperframes-audio/scripts/carve.mjs")
for bed in ([b.split('"')[1] for b in bgm] if os.path.exists(CARVE) else []):
    r = subprocess.run(["node", CARVE, "--comp", os.path.join(HERE, "index.html"), "--bed", bed, "--voice", "narration", "--strength", "0.7"], capture_output=True, text=True)
    print(f"carve {bed}: " + ("ok" if r.returncode == 0 else "FAILED（项目里先 npm i -D @hyperframes/core）"))

# 画面文字溯源：场景里的中文必须出自 script.json / STORYBOARD.md，子任务自己编的说明会列出来（只提醒，不拦）
STC = os.path.expanduser("~/.claude/skills/ray-explainer/scripts/screen_text_check.py")
if os.path.exists(STC): subprocess.run([sys.executable, STC, os.path.dirname(HERE)])

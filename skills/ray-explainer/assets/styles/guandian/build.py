"""guandian 观点框架口播构建脚本（从 qingdan 改来）：一张镜头表 + 一张字幕分词表，生成整套工程。
  - index.html：奶油方格纸底、探头真人（窗内原片 + 窗外只留头部一条的抠像）、全屏真人、各场景挂载、音频
  - compositions/*.html：钩子、每一层（步）一个场景、导流、字幕
  - ../scenes.json：审片页按它分段
版式：S 是分屏（上卡片 + 中逐词字幕 + 下探头真人），A 是全屏真人。
动效骨架（参考片的丝滑感都来自这几样，换内容时保留）：
  - 每个场景外面包一层 .cam，整场缓慢推近 4.5%，画面不会停死
  - 每层开头：梯子虚焦进场 → 这一层弹起、发光、扫光 → 镜头扎进这一格（放大 + 虚化）→ 左上小梯子当进度条 → 文档卡从虚焦里浮出来
  - 新元素一律 blur_in（模糊、略大 → 清楚），退场 blur_out（带模糊甩出去）；标题逐字、打字逐字、字幕逐词都带一点虚焦
  - 导流前五格全亮 + 背后一圈放射光，全片只用这一次
时间都是原片时间轴（gate_breaths 只压吸气，不剪时间）。改镜头、改字幕只改「这一期的内容」那一段，然后 python3 build.py。
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
COMP = HERE / "compositions"
FOOTAGE_END = 95.6
TOTAL = 95.75

DARK, CARD, CREAM, INK, GREEN, MINT, GREY = "#0e0f0f", "#1a1c1c", "#f4f1ea", "#111111", "#054c4c", "#9cc2bf", "#767676"
LEVELS = ["念稿", "埋钩子", "跟你有关", "有起伏", "有你自己"]

# ---------------- 这一期的内容 ----------------
# 镜头表：(id, 起, 止, 版式, 底色, 说明)   版式 S = 分屏，A = 全屏真人；底色 d = 深，l = 浅（第 5 层起换幕）
SEG = [
    ("hook", 0, 11.0, "S", "l", "没人看 vs 百万爆款 → 五层梯子亮相"),
    ("a1", 11.0, 14.42, "A", "l", "拿一条新闻从第 1 层讲到第 5 层"),
    ("l1", 14.42, 23.72, "S", "l", "第 1 层 念稿：打字出纯事实 → 被划走"),
    ("a2", 23.72, 27.26, "A", "l", "就是一条新闻播报"),
    ("l2", 27.26, 38.18, "S", "l", "第 2 层 埋钩子：你以为是裁员 → 划掉 → 是问你想不想走"),
    ("a3", 38.18, 41.84, "A", "l", "拽两到三次就赢过大部分人"),
    ("l3", 41.84, 51.28, "S", "l", "第 3 层 跟你有关：签 / 不签"),
    ("a4", 51.28, 54.28, "A", "l", "没有这一步只是看热闹"),
    ("l4", 54.28, 70.08, "S", "l", "第 4 层 有起伏：张力曲线一路画出来"),
    ("l5", 70.08, 80.58, "S", "l", "换浅底。第 5 层 有你自己：判断句 + 三个图标"),
    ("a5", 80.58, 87.04, "A", "l", "只有我会这么说"),
    ("cta", 87.04, TOTAL, "S", "l", "评论区打「阶梯」"),
]

# 字幕分词：按顺序覆盖整条逐字稿。每项是 (显示, whisper 原文) 或单个字符串；显示为 None 的不出字幕
# （层名在标题里、例句在文档卡里打出来，字幕就不重复）。*词* 标墨绿，每个镜头最多一处。
CHUNKS = [
    "说实话", "同样", "一件事情", "有人", "讲出来", "没人看", "有人", "讲出来", "就是", "百万爆款", "差别", "其实", "根本", "不在于", ("素材", "数彩"),
    "而在", "你讲到的", "*第几层*", "我把", "讲故事能力", "分成了", "5层", "你越", "往上走", "观众", "就越容易", "停下来",
    ("我就拿", "我正查"), "这两天的", "一条新闻", "给你", "从第1层", "讲到第5层",
    (None, "第1层叫念稿"), "只把", "事实", "按照顺序", "摆出来", (None, "10月26号微软给6万名员工发了一份自愿离职邀约"),
    "事实全对", "但是", "观众", "听完", ("就*划走了*", "就滑走了"),
    "因为", "这就是", "一条", "新闻播报", "而你要做的", "就是", "尽快", "离开", "这一层",
    (None, "第2层叫埋钩子"), "先把观众", "往一个方向", "带", "再一把", "*拽回来*", "比如说",
    (None, "微软给6万名员工发了一份信你以为是裁员通知不是是问他们想不想拿一笔钱自己走"),
    "一条视频", "里面", "你能", ("这样拽", "只摆"), "两到三次", "就已经", "赢过了", "大部分人了",
    (None, "第3层叫跟你有关"), "光有反转", "还不够", "观众得觉得", "这件事情", "跟他们", "有关系",
    (None, "你们公司会不会也这么干如果说你说到这份信你签还是不签"),
    "没有", ("这一步", "这一部"), "故事", "再精彩", "观众", "也只是", ("看个*热闹*", "看一个论脑"),
    (None, "第4层叫有起伏"), "这时候", "你开始", ("设计节奏", "设计节目"), "一会儿", "抛一个问题", "一会儿", "给个答案", "或者说", "再放一个", "小悬念",
    "微软", "明明不缺钱", "为什么", ("还要减人", "还要解论"), "先吊着", "等你把", "芯片和", "数据中心的账", "算完", "再*揭晓*", "张一下", "松一下", "观众", "就会跟着你", "走完全程",
    (None, "第5层叫有你自己"), "到了", "这一层", "拼的是", "你独一份的", "东西", "你的判断", "你的语气", "你的画面", ("同一条", "通一条"), ("微软的新闻", "微软的信文"), "我会", "把它",
    (None, "讲从前从人身上挪到芯片上面"),
    "这句话", "*只有我*", "会这么说", "刚做", "自媒体的", "同学", "一开始", "到不了", "第5层", "很正常", "但它才是", "让观众", "认准你的", "那一层",
    "所以", "下次", "如果说", "你觉得", "你的选题", "太无聊了", "先别急着", "换题", "你看看", "你自己", "可以讲到", "*第几层*",
    (None, "评论区里面打阶梯我把这5层的自查清单发给你"),
]

# 各场景的关键时间点（原片时间），场景里换算成相对时间
KEY = {
    "hook": {"nobody": 1.72, "viral": 2.92, "layer": 5.2, "five": 7.76, "up": 8.94},
    "l1": {"type0": 17.86, "type1": 21.2, "swipe": 22.98},
    "l2": {"p1a": 32.02, "p1b": 33.96, "p2a": 34.38, "p2b": 35.14, "no": 35.68, "p3a": 36.08, "p3b": 37.76},
    "l3": {"q1a": 47.32, "q1b": 48.42, "q2a": 48.76, "q2b": 50.76, "sign": 50.12, "nosign": 50.56},
    "l4": {"q": 57.78, "why": 62.12, "chip": 64.28, "reveal": 66.44, "tense": 67.26},
    "l5": {"judge": 74.08, "tone": 74.84, "pic": 75.56, "qa": 77.62, "qb": 80.14},
    "cta": {"which": 90.82, "comment": 92.5, "kw": 93.16, "list": 94.44},
}
# 全屏真人段推近：(段起, 推近时刻, 段止)
PUSH = [(23.72, 24.34, 27.26), (38.18, 40.5, 41.84), (51.28, 53.46, 54.28), (80.58, 80.86, 87.04)]
# ---------------- 内容到此为止 ----------------


def norm(s):
    return re.sub(r"[\s，,。、？?！!：:；;“”\"'*「」]", "", s).lower()


def align():
    words = json.loads((HERE.parent / "words.json").read_text(encoding="utf-8"))
    toks = [(norm(w["text"]), w["start"], w["end"]) for w in words]
    toks = [t for t in toks if t[0]]
    out, i = [], 0
    for ch in CHUNKS:
        disp, src = (ch, ch) if isinstance(ch, str) else ch
        need, got, first, last = len(norm(src)), 0, None, None
        while got < need:
            if i >= len(toks):
                raise SystemExit(f"字幕分词对不上逐字稿：卡在「{src}」")
            t, s, e = toks[i]
            first = s if first is None else first
            last = e
            got += len(t)
            i += 1
        if got != need:
            print(f"注意：「{src}」切在一个 whisper 词中间（{got} vs {need}），时间按整词算")
        out.append((disp, first, last))
    caps = []
    for k, (disp, s, e) in enumerate(out):
        if disp is None:
            continue
        nxt = out[k + 1][1] if k + 1 < len(out) else e + 0.3
        end = nxt if nxt - e < 0.5 else e + 0.25
        seg_end = next(b for _, a, b, *_ in SEG if a <= s < b)
        caps.append((disp, round(s, 2), round(min(end, seg_end), 2)))
    return caps


def num(x):
    return f"{x:g}"


def esc(s):
    return html.escape(s, quote=True)


def emph(text):
    parts = text.split("*")
    return "".join(f"<em>{esc(p)}</em>" if k % 2 else esc(p) for k, p in enumerate(parts))


FONTS = """
    @font-face { font-family: "HeiBold"; src: url("assets/fonts/NotoSansSC-700.woff") format("woff"); font-weight: 700; }
    @font-face { font-family: "HeiHeavy"; src: url("assets/fonts/NotoSansSC-900.woff") format("woff"); font-weight: 900; }"""


def theme(t):
    if t == "l":
        return dict(fg=INK, card="#ffffff", line="rgba(17,17,17,0.10)", dim="#b9b6ae", sub=GREY, rung="#dcd8cf", acc=GREEN)
    return dict(fg="#f3f3f0", card=CARD, line="rgba(255,255,255,0.09)", dim="#3a3d3d", sub="#8c8f8f", rung="#2c2f2f", acc=MINT)


def base_css(sid, t):
    c = theme(t)
    return f"""
    #{sid} .ttl {{ position: absolute; left: 0; right: 0; top: 74px; text-align: center; font-family: "HeiHeavy"; font-weight: 900; font-size: 64px; color: {c['fg']}; white-space: nowrap; }}
    #{sid} .ttl i {{ font-family: "Playfair Display", serif; font-style: italic; font-weight: 900; color: {c['acc']}; margin-right: 18px; }}
    #{sid} .doc {{ position: absolute; left: 330px; top: 210px; width: 690px; height: 560px; border-radius: 30px; background: {c['card']};
                 border: 2px solid {c['line']}; box-shadow: 0 30px 70px rgba(0,0,0,{0.45 if t == 'd' else 0.14}); padding: 40px 44px; overflow: hidden; }}
    #{sid} .doc .hd {{ font-family: "JetBrains Mono", monospace; font-size: 24px; color: {c['sub']}; letter-spacing: 0.04em; margin-bottom: 22px; }}
    #{sid} .doc p {{ font-family: "HeiBold"; font-weight: 700; font-size: 40px; line-height: 1.5; color: {c['fg']}; margin-bottom: 18px; }}
    #{sid} .doc p.dim {{ color: {c['dim']}; }}
    #{sid} .doc .ch {{ opacity: 0; display: inline-block; white-space: pre; }}
    #{sid} .doc em {{ font-style: normal; color: {c['acc']}; }}
    #{sid} .ladw {{ position: absolute; left: 340px; top: 190px; width: 400px; height: 620px; }}
    #{sid} .mini {{ position: absolute; left: 40px; top: 230px; width: 240px; height: 372px; opacity: 0; }}
    #{sid} .cam {{ position: absolute; inset: 0; transform-origin: 50% 42%; }}
    #{sid} .tc {{ display: inline-block; white-space: pre; }}"""


def ladder_svg(sid, t, lit, cur=0, w=400):
    """lit = 点亮到第几层（0 = 都没亮），cur = 哪一层带光晕（0 = 没有）。梯子 viewBox 400×620，第 1 层在最下面。
    每格有一层模糊的墨绿光晕（.gl）和一道扫光（.sh，动画改 attr x），横档本身是 .rr。"""
    c = theme(t)
    rungs = []
    for k in range(5):
        y = 560 - k * 118
        on = k < lit
        fill = GREEN if on else c["rung"]
        stroke = MINT if on else "none"
        rungs.append(f'<g class="rung" id="{sid}-r{k}">'
                     f'<rect class="gl" id="{sid}-g{k}" x="30" y="{y - 36}" width="340" height="72" rx="20" fill="{GREEN}" filter="url(#{sid}-blur)" opacity="{0.6 if k == cur - 1 else 0}"/>'
                     f'<rect class="rr" x="40" y="{y - 30}" width="320" height="60" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
                     f'<clipPath id="{sid}-cp{k}"><rect x="40" y="{y - 30}" width="320" height="60" rx="14"/></clipPath>'
                     f'<rect class="sh" id="{sid}-s{k}" clip-path="url(#{sid}-cp{k})" x="-120" y="{y - 30}" width="110" height="60" fill="url(#{sid}-sg)"/>'
                     f'<text x="200" y="{y + 11}" text-anchor="middle" font-family="HeiBold" font-weight="700" font-size="30" fill="{"#f3f3f0" if on else c["sub"]}">{esc(f"第{k + 1}层 · {LEVELS[k]}")}</text></g>')
    return (f'<svg viewBox="0 0 400 620" width="{w}" height="{round(w * 1.55)}" overflow="visible">'
            f'<defs><filter id="{sid}-blur" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="14"/></filter>'
            f'<linearGradient id="{sid}-sg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
            f'<rect class="rail" x="20" y="0" width="14" height="620" rx="7" fill="{c["rung"]}"/><rect class="rail" x="366" y="0" width="14" height="620" rx="7" fill="{c["rung"]}"/>'
            f'{"".join(rungs)}</svg>')


def blur_in(sel, t, d=0.6, y=0, s=1.08, blur=18, ease="expo.out"):
    """虚焦进场：模糊、略大 → 清楚，参考片几乎所有新元素都这么进。"""
    return (f'    tl.fromTo("{sel}", {{ opacity: 0, y: {y}, scale: {s}, filter: "blur({blur}px)" }}, '
            f'{{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: {d}, ease: "{ease}" }}, {t:.2f});')


def blur_out(sel, t, d=0.4, y=-80, x=0, blur=16):
    """甩出去：带运动模糊离场。"""
    return f'    tl.to("{sel}", {{ opacity: 0, x: {x}, y: {y}, filter: "blur({blur}px)", duration: {d}, ease: "power3.in" }}, {t:.2f});'


def tchars(*parts):
    """标题逐字拆开：parts 是 (文字, 是否英文斜体) 或纯文字。"""
    out = []
    for p in parts:
        txt, it = (p, False) if isinstance(p, str) else p
        for ch in txt:
            out.append(f'<i class="tc">{esc(ch)}</i>' if it else f'<span class="tc">{esc(ch)}</span>')
    return "".join(out)


def title_in(sel, t):
    return (f'    tl.fromTo("{sel} .tc", {{ opacity: 0, y: -24, filter: "blur(12px)" }}, '
            f'{{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out", stagger: 0.045 }}, {t:.2f});')


def scene(sid, t, css, body, js, dur):
    return f"""<template>
  <style>{FONTS}
    #{sid} {{ position: absolute; left: 0; top: 0; width: 1080px; height: 960px; overflow: hidden; }}{base_css(sid, t)}{css}
  </style>
  <div id="{sid}" data-composition-id="{sid}" data-width="1080" data-height="960">
    <div id="{sid}-cam" class="cam">
{body}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    // 整场镜头一直在缓慢推近，画面不会停死
    tl.fromTo("#{sid}-cam", {{ scale: 1 }}, {{ scale: 1.045, duration: {dur:.2f}, ease: "none" }}, 0);
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def ladder_intro(sid, n, hold=1.25):
    """场景开头：梯子虚焦进场，第 n 层弹一下、亮起光晕、扫一道光；然后镜头扎进这一格（放大 + 虚化），
    左上角再虚焦进来一架小梯子当进度条。"""
    k, cy = n - 1, 560 - (n - 1) * 118
    return f"""    // 开头：梯子虚焦进场 → 第 {n} 层弹起、发光、扫光 → 镜头扎进这一格 → 左边小梯子当进度条
{blur_in(f"#{sid}-ladw", 0, d=0.55, s=0.9)}
{title_in(f"#{sid}-ttl", 0.08)}
    tl.fromTo("#{sid}-r{k} .rr", {{ scale: 0.82, transformOrigin: "50% 50%" }}, {{ scale: 1, duration: 0.55, ease: "back.out(2.6)" }}, 0.28);
    tl.fromTo("#{sid}-g{k}", {{ opacity: 0 }}, {{ opacity: 0.75, duration: 0.4, ease: "power2.out" }}, 0.28);
    tl.fromTo("#{sid}-s{k}", {{ attr: {{ x: -120 }} }}, {{ attr: {{ x: 380 }}, duration: 0.6, ease: "power2.inOut" }}, 0.5);
    tl.to("#{sid}-ladw", {{ scale: 3.4, opacity: 0, filter: "blur(16px)", transformOrigin: "200px {cy}px", duration: 0.5, ease: "power3.in" }}, {hold});
{blur_in(f"#{sid}-mini", hold + 0.4, d=0.6, s=1.25, blur=14)}"""


def typing(sel, t0, t1):
    """把 sel 里的 .ch 在 [t0, t1] 里一个个显出来（跟着口播打字），每个字从下面虚焦浮上来。"""
    return (f'    tl.fromTo("{sel} .ch", {{ opacity: 0, y: 14, filter: "blur(6px)" }}, '
            f'{{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.22, ease: "power2.out", stagger: {{ amount: {max(t1 - t0, 0.2):.2f} }} }}, {t0:.2f});')


def chars(text):
    """文字拆成一个个 span，*词* 包墨绿。"""
    out, on = [], False
    for ch in text:
        if ch == "*":
            on = not on
            continue
        s = f'<span class="ch">{esc(ch)}</span>'
        out.append(f"<em>{s}</em>" if on else s)
    return "".join(out)


def doc_in(sid, sel):
    """镜头扎进格子之后，文档卡从虚焦里浮出来。"""
    return blur_in(sel, 1.6, d=0.7, y=30, s=1.14, blur=22)


def write_scenes(t0):
    out = {}
    rel = lambda sid, x: round(x - t0[sid], 2)
    dur = {sid: b - a for sid, a, b, *_ in SEG}

    # ---- 钩子：0 秒起 ----
    a = KEY["hook"]
    css = f"""
    #hook .pc {{ position: absolute; top: 230px; width: 380px; height: 470px; border-radius: 30px; background: #fff; border: 2px solid rgba(17,17,17,0.08); box-shadow: 0 24px 50px rgba(17,17,17,0.12); overflow: hidden; }}
    #hook .pc img {{ position: absolute; left: 0; top: 0; width: 380px; height: 360px; object-fit: cover; object-position: 50% 0; }}
    #hook .pc .views {{ position: absolute; left: 0; right: 0; bottom: 28px; display: flex; align-items: center; justify-content: center; gap: 12px; white-space: nowrap;
                       font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 50px; letter-spacing: -0.02em; }}
    #hook .pc .views svg {{ flex: none; }}
    #hook .src {{ position: absolute; left: 0; right: 0; top: 724px; text-align: center; font-family: "HeiBold"; font-weight: 700; font-size: 26px; color: {GREY}; }}
    #hook .vs {{ position: absolute; left: 0; right: 0; top: 420px; text-align: center; font-family: "Playfair Display", serif; font-style: italic; font-weight: 900; font-size: 64px; color: #9a978f; }}"""
    # 真实数据：Ray 自己两条抖音解说片，播放量取自发布笔记的 douyin_views（2026-10-27 同步）
    eye = lambda col: f'<svg width="44" height="44" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="{col}"/></svg>'
    body = f"""    <div id="hook-ttl" class="ttl">{tchars('同一件事')}</div>
    <div id="hook-pa" class="pc" style="left:110px"><img src="assets/img/cover_washer.jpg" alt="" />
      <div class="views" style="color:#9a978f">{eye('#9a978f')}1,103</div>
    </div>
    <div id="hook-vs" class="vs">vs</div>
    <div id="hook-pb" class="pc" style="left:590px;border:3px solid {GREEN}"><img src="assets/img/cover_iphone.jpg" alt="" style="object-position:50% 38%" />
      <div class="views" style="color:{GREEN}">{eye(GREEN)}<span id="hook-cnt">0</span></div>
    </div>
    <div id="hook-src" class="src">我自己的两条抖音 · 播放量</div>
    <div id="hook-ladw" class="ladw" style="opacity:0">{ladder_svg('hook', 'l', 0)}</div>
    <div id="hook-ttl2" class="ttl">{tchars('讲故事的 ', ('5', True), ' 层')}</div>"""
    js = f"""    // 场景从 0 秒开始。「有人讲出来没人看」左卡虚焦落下，「百万爆款」右卡虚焦落下、数字 count-up
{title_in("#hook-ttl", 0.15)}
{blur_in("#hook-pa", a['nobody'] - 0.35, d=0.7, y=60, s=1.18, blur=24)}
{blur_in("#hook-src", a['nobody'], d=0.5, blur=8, s=1)}
{blur_in("#hook-vs", a['viral'] - 0.45, d=0.4, s=1.6, blur=10)}
{blur_in("#hook-pb", a['viral'] - 0.35, d=0.7, y=60, s=1.18, blur=24)}
    const cnt = {{ v: 0 }};
    tl.to(cnt, {{ v: 1300334, duration: 0.9, ease: "power2.in", onUpdate: () => {{ document.getElementById("hook-cnt").textContent = Math.round(cnt.v).toLocaleString("en-US"); }} }}, {a['viral']:.2f});
    tl.fromTo("#hook-pb", {{ scale: 1 }}, {{ scale: 1.06, duration: 0.18, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false }}, {a['viral'] + 0.9:.2f});
    // 「而在你讲到的第几层」两张卡带模糊甩出去，换成梯子
    tl.to(["#hook-pa", "#hook-vs", "#hook-pb", "#hook-ttl", "#hook-src"], {{ opacity: 0, y: -110, filter: "blur(18px)", duration: 0.4, ease: "power3.in", stagger: 0.04 }}, {a['layer'] - 0.45:.2f});
    tl.set("#hook-ladw", {{ opacity: 1 }}, {a['layer']:.2f});
    // 梯子：两根竖杆从下往上长出来，五格从下往上虚焦落位
    tl.fromTo("#hook .rail", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 0.6, ease: "expo.out", stagger: 0.05 }}, {a['layer']:.2f});
    tl.fromTo("#hook .rung", {{ opacity: 0, y: 24, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out", stagger: 0.08 }}, {a['layer'] + 0.15:.2f});
{title_in("#hook-ttl2", a['five'] - 0.15)}
    // 「分成了 5 层」五格从下往上依次点亮，每亮一格起一圈光、扫一道光
    tl.to("#hook .rung .rr", {{ fill: "{GREEN}", stroke: "{MINT}", duration: 0.12, stagger: 0.16 }}, {a['five']:.2f});
    tl.to("#hook .rung text", {{ fill: "#f3f3f0", duration: 0.12, stagger: 0.16 }}, {a['five']:.2f});
    tl.fromTo("#hook .gl", {{ opacity: 0 }}, {{ opacity: 0.55, duration: 0.3, stagger: 0.16 }}, {a['five']:.2f});
    tl.fromTo("#hook .sh", {{ attr: {{ x: -120 }} }}, {{ attr: {{ x: 380 }}, duration: 0.5, ease: "power2.inOut", stagger: 0.16 }}, {a['five'] + 0.05:.2f});
    // 「你越往上走」整架梯子往上抬一下
    tl.to("#hook-ladw", {{ y: -22, duration: 0.5, ease: "power2.out", yoyo: true, repeat: 1 }}, {a['up']:.2f});"""
    out["hook"] = scene("hook", "l", css, body, js, dur["hook"])

    # ---- 第 1 层：念稿 ----
    sid, k = "l1", KEY["l1"]
    css = """
    #l1 .swipe { position: absolute; left: 640px; top: 520px; width: 60px; height: 200px; opacity: 0; }"""
    body = f"""    <div id="l1-ttl" class="ttl">{tchars(('1.', True), LEVELS[0])}</div>
    <div id="l1-ladw" class="ladw">{ladder_svg('l1', 'l', 1)}</div>
    <div id="l1-mini" class="mini">{ladder_svg('l1m', 'l', 1, cur=1, w=240)}</div>
    <div id="l1-doc" class="doc"><div class="hd">CNBC · 2026-10-26</div>
      <img id="l1-news" src="assets/img/news_cnbc.jpg" alt="" style="display:block;width:602px;height:239px;object-fit:cover;object-position:0 0;border-radius:14px;border:2px solid rgba(17,17,17,0.08);margin-bottom:24px" />
      <p id="l1-p">{chars('10 月 26 号，微软给 6 万名员工发了一份自愿离职邀约。')}</p></div>"""
    js = ladder_intro(sid, 1) + "\n" + doc_in(sid, "#l1-doc") + f"""
{typing('#l1-p', rel(sid, k['type0']), rel(sid, k['type1']))}
    // 「观众听完就划走了」：文档卡整张被划上去
    tl.fromTo("#l1-news", {{ opacity: 0, scale: 1.08, filter: "blur(12px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }}, 1.85);
    tl.to("#l1-doc", {{ y: -700, opacity: 0, filter: "blur(14px)", duration: 0.45, ease: "power3.in" }}, {rel(sid, k['swipe']):.2f});
"""
    out[sid] = scene(sid, "l", css, body, js, dur[sid])

    # ---- 第 2 层：埋钩子 ----
    sid, k = "l2", KEY["l2"]
    css = f"""
    #l2 .strike {{ position: absolute; left: 160px; top: 32px; width: 160px; height: 6px; background: {GREEN}; transform-origin: 0 50%; transform: scaleX(0); }}"""
    body = f"""    <div id="l2-ttl" class="ttl">{tchars(('2.', True), LEVELS[1])}</div>
    <div id="l2-ladw" class="ladw">{ladder_svg('l2', 'l', 2)}</div>
    <div id="l2-mini" class="mini">{ladder_svg('l2m', 'l', 2, cur=2, w=240)}</div>
    <div id="l2-doc" class="doc"><div class="hd">HOOK</div>
      <p id="l2-p1">{chars('微软给 6 万名员工发了一封信，')}</p>
      <p id="l2-p2" style="position:relative">{chars('你以为是裁员通知？')}<span id="l2-st" class="strike"></span></p>
      <p id="l2-p3">{chars('不是，是问他们想不想*拿一笔钱自己走*。')}</p></div>"""
    js = ladder_intro(sid, 2) + "\n" + doc_in(sid, "#l2-doc") + f"""
{typing('#l2-p1', rel(sid, k['p1a']), rel(sid, k['p1b']))}
{typing('#l2-p2', rel(sid, k['p2a']), rel(sid, k['p2b']))}
    // 「不是」：一道墨绿线划掉「裁员通知」，整行变暗，卡片往回一顿（被拽回来）
    tl.to("#l2-st", {{ scaleX: 1, duration: 0.22, ease: "power2.out" }}, {rel(sid, k['no']):.2f});
    tl.to("#l2-p2", {{ color: "#b9b6ae", duration: 0.2 }}, {rel(sid, k['no']) + 0.1:.2f});
    tl.to("#l2-doc", {{ x: 28, rotation: 1.2, duration: 0.1, ease: "power2.out", yoyo: true, repeat: 3 }}, {rel(sid, k['no']):.2f});
{typing('#l2-p3', rel(sid, k['p3a']), rel(sid, k['p3b']))}"""
    out[sid] = scene(sid, "l", css, body, js, dur[sid])

    # ---- 第 3 层：跟你有关 ----
    sid, k = "l3", KEY["l3"]
    css = f"""
    #l3 .poll {{ display: flex; gap: 24px; margin-top: 22px; }}
    #l3 .opt {{ flex: 1; height: 96px; border-radius: 22px; border: 3px solid {GREEN}; display: flex; align-items: center; justify-content: center;
               font-family: "HeiHeavy"; font-weight: 900; font-size: 48px; color: {INK}; opacity: 0; }}
    #l3 .opt.b {{ background: {GREEN}; color: #f3f3f0; }}"""
    body = f"""    <div id="l3-ttl" class="ttl">{tchars(('3.', True), LEVELS[2])}</div>
    <div id="l3-ladw" class="ladw">{ladder_svg('l3', 'l', 3)}</div>
    <div id="l3-mini" class="mini">{ladder_svg('l3m', 'l', 3, cur=3, w=240)}</div>
    <div id="l3-doc" class="doc"><div class="hd">YOU</div>
      <p class="dim">微软给 6 万名员工发了一封信……</p>
      <p id="l3-q1">{chars('你们公司会不会*也这么干*？')}</p>
      <p id="l3-q2">{chars('收到这封信，你签还是不签？')}</p>
      <div class="poll"><div class="opt b" id="l3-o1">签</div><div class="opt" id="l3-o2">不签</div></div></div>"""
    js = ladder_intro(sid, 3) + "\n" + doc_in(sid, "#l3-doc") + f"""
{typing('#l3-q1', rel(sid, k['q1a']), rel(sid, k['q1b']))}
{typing('#l3-q2', rel(sid, k['q2a']), rel(sid, k['q2b']))}
    tl.fromTo("#l3-o1", {{ opacity: 0, scale: 0.6, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "back.out(2.4)" }}, {rel(sid, k['sign']):.2f});
    tl.fromTo("#l3-o2", {{ opacity: 0, scale: 0.6, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "back.out(2.4)" }}, {rel(sid, k['nosign']):.2f});"""
    out[sid] = scene(sid, "l", css, body, js, dur[sid])

    # ---- 第 4 层：有起伏 ----
    sid, k = "l4", KEY["l4"]
    css = f"""
    #l4 .wave {{ position: absolute; left: 330px; top: 210px; width: 690px; height: 560px; border-radius: 30px; background: #fff; border: 2px solid rgba(17,17,17,0.08); box-shadow: 0 30px 70px rgba(17,17,17,0.14); }}
    #l4 .tag {{ position: absolute; font-family: "HeiBold"; font-weight: 700; font-size: 32px; color: {INK}; background: #ebe7de; border-radius: 12px; padding: 6px 18px; white-space: nowrap; opacity: 0; }}
    #l4 .tag.g {{ background: {GREEN}; color: #f3f3f0; }}"""
    body = f"""    <div id="l4-ttl" class="ttl">{tchars(('4.', True), LEVELS[3])}</div>
    <div id="l4-ladw" class="ladw">{ladder_svg('l4', 'l', 4)}</div>
    <div id="l4-mini" class="mini">{ladder_svg('l4m', 'l', 4, cur=4, w=240)}</div>
    <div id="l4-wave" class="wave">
      <svg width="690" height="560" viewBox="0 0 690 560">
        <line x1="50" y1="480" x2="650" y2="480" stroke="#e6e2d9" stroke-width="4"/>
        <path id="l4-path" d="M50 440 C 120 430, 150 260, 210 250 S 280 400, 320 380 S 400 120, 470 110 S 540 420, 580 400 S 630 300, 650 290"
          fill="none" stroke="{GREEN}" stroke-width="8" stroke-linecap="round" stroke-dasharray="1400" stroke-dashoffset="1400"/>
        <circle id="l4-d1" cx="210" cy="250" r="14" fill="{GREEN}" opacity="0"/><circle id="l4-d2" cx="470" cy="110" r="14" fill="{GREEN}" opacity="0"/><circle id="l4-d3" cx="580" cy="400" r="14" fill="{INK}" opacity="0"/>
      </svg>
      <div id="l4-t1" class="tag" style="left:178px;top:170px">？</div>
      <div id="l4-t2" class="tag" style="left:340px;top:36px">芯片 · 数据中心</div>
      <div id="l4-t3" class="tag g" style="left:558px;top:426px">！</div>
    </div>"""
    q, why, reveal = rel(sid, k['q']), rel(sid, k['why']), rel(sid, k['reveal'])
    js = ladder_intro(sid, 4) + "\n" + doc_in(sid, "#l4-wave") + f"""
    // 曲线跟着说：「抛一个问题」第一个峰 →「为什么还要减人」第二个峰 →「再揭晓」落下 →「张一下松一下」走完
    tl.to("#l4-path", {{ strokeDashoffset: 1060, duration: {q - 1.9:.2f}, ease: "none" }}, 1.9);
    tl.fromTo("#l4-d1", {{ opacity: 0, scale: 0, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(3)" }}, {q:.2f});
    tl.fromTo("#l4-t1", {{ opacity: 0, y: 16, filter: "blur(8px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "expo.out" }}, {q:.2f});
    tl.to("#l4-path", {{ strokeDashoffset: 560, duration: {why - q:.2f}, ease: "none" }}, {q:.2f});
    tl.fromTo("#l4-d2", {{ opacity: 0, scale: 0, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(3)" }}, {why:.2f});
    tl.fromTo("#l4-t2", {{ opacity: 0, y: 16, filter: "blur(8px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "expo.out" }}, {rel(sid, k['chip']):.2f});
    tl.to("#l4-path", {{ strokeDashoffset: 220, duration: {reveal - why:.2f}, ease: "none" }}, {why:.2f});
    tl.fromTo("#l4-d3", {{ opacity: 0, scale: 0, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(3)" }}, {reveal:.2f});
    tl.to("#l4-wave", {{ scale: 1.04, duration: 0.16, ease: "power2.out", yoyo: true, repeat: 1 }}, {reveal:.2f});
    tl.fromTo("#l4-t3", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "back.out(2.4)" }}, {reveal:.2f});
    tl.to("#l4-path", {{ strokeDashoffset: 0, duration: 1.2, ease: "none" }}, {rel(sid, k['tense']):.2f});"""
    out[sid] = scene(sid, "l", css, body, js, dur[sid])

    # ---- 第 5 层：有你自己 ----
    sid, k = "l5", KEY["l5"]
    css = f"""
    #l5 .row {{ display: flex; gap: 26px; align-items: flex-start; }}
    #l5 .cov {{ flex: none; width: 196px; height: 261px; border-radius: 14px; object-fit: cover; box-shadow: 0 14px 30px rgba(17,17,17,0.18); }}
    #l5 .quote {{ white-space: pre-line; font-family: "HeiHeavy"; font-weight: 900; font-size: 46px; line-height: 1.45; color: {INK}; margin-top: 6px; }}
    #l5 .quote em {{ font-style: normal; color: #f3f3f0; }}
    #l5 .quote em .ch {{ background: {GREEN}; padding: 0 4px; }}
    #l5 .sig {{ margin-top: 10px; font-family: "Playfair Display", serif; font-style: italic; font-weight: 900; font-size: 40px; color: {GREY}; opacity: 0; }}
    #l5 .icons {{ position: absolute; left: 44px; right: 44px; bottom: 40px; display: flex; gap: 22px; }}
    #l5 .ic {{ flex: 1; height: 110px; border-radius: 22px; background: {CREAM}; border: 2px solid rgba(17,17,17,0.08); display: flex; align-items: center; justify-content: center; opacity: 0; }}"""
    st = f'fill="none" stroke="{GREEN}" stroke-width="4"'
    scale = f'<svg width="64" height="64" viewBox="0 0 64 64"><path d="M32 8 V56 M14 56 H50 M12 18 H52 M12 18 L4 38 H20 Z M52 18 L44 38 H60 Z" {st} stroke-linejoin="round"/></svg>'
    mic = f'<svg width="64" height="64" viewBox="0 0 64 64"><rect x="22" y="6" width="20" height="34" rx="10" {st}/><path d="M14 30 a18 18 0 0 0 36 0 M32 48 V58 M22 58 H42" {st} stroke-linecap="round"/></svg>'
    film = f'<svg width="64" height="64" viewBox="0 0 64 64"><rect x="6" y="12" width="52" height="40" rx="6" {st}/><path d="M6 22 H58 M6 42 H58 M18 12 V22 M30 12 V22 M42 12 V22 M18 42 V52 M30 42 V52 M42 42 V52" {st}/></svg>'
    body = f"""    <div id="l5-ttl" class="ttl">{tchars(('5.', True), LEVELS[4])}</div>
    <div id="l5-ladw" class="ladw">{ladder_svg('l5', 'l', 5)}</div>
    <div id="l5-mini" class="mini">{ladder_svg('l5m', 'l', 5, cur=5, w=240)}</div>
    <div id="l5-doc" class="doc"><div class="hd">王Ray说</div>
      <div class="row"><img id="l5-cov" class="cov" src="assets/img/cover_msft.jpg" alt="" />
        <div><div id="l5-q" class="quote">{chars('*钱*从人身上，\n挪到了*芯片*上。')}</div>
        <div id="l5-sig" class="sig">— only me</div></div></div>
      <div class="icons"><div class="ic" id="l5-i1">{scale}</div><div class="ic" id="l5-i2">{mic}</div><div class="ic" id="l5-i3">{film}</div></div></div>"""
    js = ladder_intro(sid, 5) + "\n" + doc_in(sid, "#l5-doc") + f"""
    // 「你的判断 / 你的语气 / 你的画面」三个图标依次弹出（只放图标，字交给字幕）
    tl.fromTo("#l5-i1", {{ opacity: 0, y: 30, scale: 0.7, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "back.out(2.2)" }}, {rel(sid, k['judge']):.2f});
    tl.fromTo("#l5-i2", {{ opacity: 0, y: 30, scale: 0.7, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "back.out(2.2)" }}, {rel(sid, k['tone']):.2f});
    tl.fromTo("#l5-i3", {{ opacity: 0, y: 30, scale: 0.7, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.45, ease: "back.out(2.2)" }}, {rel(sid, k['pic']):.2f});
{typing('#l5-q', rel(sid, k['qa']), rel(sid, k['qb']))}
{blur_in("#l5-sig", rel(sid, k['qb']), d=0.5, blur=10, s=1)}
    tl.fromTo("#l5-cov", {{ opacity: 0, rotation: -6, scale: 1.15, filter: "blur(14px)" }}, {{ opacity: 1, rotation: 0, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 1.9);"""
    out[sid] = scene(sid, "l", css, body, js, dur[sid])

    # ---- 导流：浅底 ----
    sid, k = "cta", KEY["cta"]
    css = f"""
    #cta .gcard {{ position: absolute; left: 60px; top: 170px; width: 960px; height: 220px; border-radius: 34px; background: {GREEN}; box-shadow: 0 28px 60px rgba(5,76,76,0.28); opacity: 0; }}
    #cta .gcard span {{ position: absolute; left: 0; right: 0; top: 66px; text-align: center; font-family: "HeiBold"; font-weight: 700; font-size: 68px; color: #f3f3f0; letter-spacing: 0.08em; }}
    #cta .kw {{ position: absolute; left: 0; right: 0; top: 440px; text-align: center; font-family: "HeiHeavy"; font-weight: 900; font-size: 190px; line-height: 1; color: {INK}; opacity: 0; }}
    #cta .kw em {{ font-style: normal; color: {GREEN}; }}
    #cta .sub {{ position: absolute; left: 0; right: 0; top: 690px; text-align: center; font-family: "HeiBold"; font-weight: 700; font-size: 46px; color: {GREY}; opacity: 0; }}
    #cta .lad2 {{ position: absolute; left: 340px; top: 190px; width: 400px; height: 620px; }}
    #cta .burst {{ position: absolute; left: 140px; top: 100px; width: 800px; height: 800px; opacity: 0; }}"""
    body = f"""    <svg id="cta-burst" class="burst" viewBox="0 0 800 800" opacity="0"><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(0 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(20 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(40 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(60 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(80 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(100 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(120 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(140 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(160 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(180 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(200 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(220 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(240 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(260 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(280 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(300 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(320 400 400)"/><line x1="400" y1="250" x2="400" y2="10" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" transform="rotate(340 400 400)"/></svg>
    <div id="cta-lad" class="lad2">{ladder_svg('cta', 'l', 5)}</div>
    <div id="cta-card" class="gcard"><span>评论区打</span></div>
    <div id="cta-kw" class="kw"><em>「</em>阶梯<em>」</em></div>
    <div id="cta-sub" class="sub">五层自查清单</div>"""
    js = f"""    // 场景从 {t0['cta']} 秒开始：梯子虚焦进场、五格依次发光，背后炸开一圈光（全片只用这一次）→ 镜头扎进梯子 → 导流卡
{blur_in("#cta-lad", 0.05, d=0.6, s=0.9)}
    tl.fromTo("#cta .gl", {{ opacity: 0 }}, {{ opacity: 0.6, duration: 0.3, stagger: 0.1 }}, 0.4);
    tl.fromTo("#cta .sh", {{ attr: {{ x: -120 }} }}, {{ attr: {{ x: 380 }}, duration: 0.5, ease: "power2.inOut", stagger: 0.1 }}, 0.45);
    tl.fromTo("#cta-burst", {{ opacity: 0, scale: 0.5, rotation: -10, transformOrigin: "50% 50%" }}, {{ opacity: 0.35, scale: 1, rotation: 0, duration: 0.8, ease: "expo.out" }}, 0.95);
    tl.to("#cta-burst", {{ rotation: 25, duration: {rel(sid, k['comment']) - 1.75:.2f}, ease: "none" }}, 1.75);
    tl.to(["#cta-lad", "#cta-burst"], {{ opacity: 0, scale: 2.6, filter: "blur(16px)", duration: 0.45, ease: "power3.in" }}, {rel(sid, k['comment']) - 0.45:.2f});
{blur_in("#cta-card", rel(sid, k['comment']), d=0.6, y=80, s=1.1, blur=20)}
{blur_in("#cta-kw", rel(sid, k['kw']), d=0.5, s=1.4, blur=20)}
{blur_in("#cta-sub", rel(sid, k['list']), d=0.5, y=20, s=1, blur=10)}"""
    out[sid] = scene(sid, "l", css, body, js, dur[sid])
    return out


def captions(caps):
    rows, pops = [], []
    for i, (text, s, e) in enumerate(caps, 1):
        pops.append(f'    tl.fromTo("#c{i:03d} span", {{ scale: 1.18, opacity: 0.4, filter: "blur(4px)" }}, {{ scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.14, ease: "power2.out" }}, {s});')
        seg = next(x for x in SEG if x[1] <= s < x[2])
        pos = "low" if seg[3] == "A" else ("mid-l" if seg[4] == "l" else "mid-d")
        rows.append(f'    <div id="c{i:03d}" class="cap {pos} clip" data-start="{s}" data-duration="{round(e - s, 2)}"><span>{emph(text)}</span></div>')
    return f"""<template>
  <style>{FONTS}
    #captions {{ position: absolute; inset: 0; pointer-events: none; }}
    #captions .cap {{ position: absolute; left: 0; right: 0; text-align: center; white-space: nowrap; font-family: "HeiHeavy"; font-weight: 900; }}
    #captions .cap span {{ display: inline-block; }}
    /* 分屏：一次一个词，压在卡片和探头真人之间 */
    #captions .cap.mid-d, #captions .cap.mid-l {{ top: 846px; font-size: 84px; letter-spacing: 0.01em; }}
    #captions .cap.mid-d {{ color: #f3f3f0; }}
    #captions .cap.mid-d em {{ font-style: normal; color: {MINT}; }}
    #captions .cap.mid-l {{ color: {INK}; }}
    #captions .cap.mid-l em {{ font-style: normal; color: {GREEN}; }}
    /* 全屏真人：白字带阴影，偏下 */
    #captions .cap.low {{ top: 1330px; font-size: 76px; color: #fff; text-shadow: 0 4px 18px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.5); }}
    #captions .cap.low em {{ font-style: normal; color: {MINT}; }}
  </style>
  <div id="captions" data-composition-id="captions" data-width="1080" data-height="1920">
    <!-- 一次一个词：由 build.py 按逐字时间生成，改字改时间去那里改 -->
{chr(10).join(rows)}
  </div>
  <script>
    // 每个词出来时从略大、略虚弹到位
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(pops)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""


def index():
    pops, mattes, fulls, scenes = [], [], [], []
    for sid, a, b, lay, th, _ in SEG:
        dur = round(min(b, FOOTAGE_END) - a, 3)
        if lay == "S":
            pops.append(f'        <video id="pw-{sid}" class="clip" src="assets/footage/face_pop.mp4" muted playsinline data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="1"></video>')
            mattes.append(f'        <video id="pm-{sid}" class="clip" src="assets/footage/face_pop_matte.webm" muted playsinline data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="2"></video>')
            scenes.append(f'      <div id="h-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{num(a)}" data-duration="{num(round(b - a, 3))}" '
                          f'data-track-index="4" data-track-kind="graphics" data-width="1080" data-height="960" style="position:absolute;left:0;top:0;width:1080px;height:960px;z-index:5"></div>')
        else:
            fulls.append(f'        <video id="fa-{sid}" class="clip" src="assets/footage/face_full.mp4" muted playsinline data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="3"></video>')
    light_from = next(a for _, a, b, lay, th, _ in SEG if th == "l")

    K = KEY
    sfx = []
    for sid, a, b, lay, th, _ in SEG:
        if sid in ("l1", "l2", "l3", "l4", "l5"):
            sfx.append((f"sfx-{sid}", "whoosh.wav", round(a, 2), 0.7, 0.35, 11))
            sfx.append((f"sfx-{sid}-rung", "click.wav", round(a + 0.27, 2), 0.05, 0.45, 10))
    sfx += [("sfx-viral", "ding.wav", K["hook"]["viral"] + 0.5, 0.7, 0.3, 10), ("sfx-five", "swell.wav", K["hook"]["five"], 1.2, 0.35, 12),
            ("sfx-swipe", "whoosh.wav", K["l1"]["swipe"], 0.7, 0.35, 12), ("sfx-no", "click.wav", K["l2"]["no"], 0.05, 0.5, 12),
            ("sfx-reveal", "ding.wav", K["l4"]["reveal"], 0.7, 0.3, 12), ("sfx-kw", "ding.wav", K["cta"]["kw"], 0.7, 0.35, 12)]
    sfx_html = "\n".join(f'      <audio id="{i}" class="clip" src="assets/audio/{f}" data-start="{s:g}" data-duration="{d}" data-volume="{v}" data-track-index="{tr}"></audio>' for i, f, s, d, v, tr in sfx)
    pushes = "\n".join(f'      tl.set("#face-a-wrap", {{ scale: 1 }}, {a}); tl.to("#face-a-wrap", {{ scale: 1.08, duration: 0.22, ease: "power2.out" }}, {p}); tl.set("#face-a-wrap", {{ scale: 1 }}, {b});' for a, p, b in PUSH)

    return f"""<!doctype html>
<html lang="zh-CN" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: {DARK}; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
      /* 深底：中间一团很暗的墨绿光 */
      #bg {{ position: absolute; inset: 0; background: radial-gradient(900px 700px at 50% 26%, rgba(5,76,76,0.25), rgba(5,76,76,0) 70%), {DARK}; }}
      /* 浅底：第 5 层起换幕，奶油底加细方格纸纹 */
      #bg-light {{ position: absolute; inset: 0; background:
              linear-gradient(rgba(17,17,17,0.045) 1px, transparent 1px) 0 0 / 48px 48px,
              linear-gradient(90deg, rgba(17,17,17,0.045) 1px, transparent 1px) 0 0 / 48px 48px, {CREAM}; }}
      /* 探头真人：窗里放原片，窗上沿以上只放抠像，头顶越出窗框 */
      #pop-win {{ position: absolute; left: 60px; top: 1210px; width: 960px; height: 760px; border-radius: 44px; overflow: hidden; box-shadow: 0 30px 70px rgba(0,0,0,0.35); }}
      #pop-win video {{ position: absolute; left: -60px; top: -250px; width: 1080px; height: 960px; }}
      #pop-out {{ position: absolute; left: 300px; top: 960px; width: 480px; height: 250px; overflow: hidden; }}
      /* 只让头越出窗框：抠像层只留头部那一条，抬起来的手不会跑出窗外 */
      #pop-out video {{ position: absolute; left: -300px; top: 0; width: 1080px; height: 960px; }}
      /* 全屏真人 */
      #face-a-wrap {{ position: absolute; inset: 0; transform-origin: 50% 32%; }}
      #face-a-wrap video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <!-- 观点框架口播：分屏（上卡片 + 探头真人）与全屏真人硬切交替；第 5 层起深底换浅底。镜头表在 build.py。 -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="{num(TOTAL)}" data-width="1080" data-height="1920">
      <div id="bg"></div>
      <div id="bg-light" class="clip" data-start="{num(light_from)}" data-duration="{num(round(TOTAL - light_from, 2))}" data-track-index="0" style="z-index:0"></div>
      <img id="end-still" class="clip" src="assets/img/end_still_pop.jpg" alt="" data-start="{num(FOOTAGE_END - 0.1)}" data-duration="{num(round(TOTAL - FOOTAGE_END + 0.1, 2))}" data-track-index="0" style="position:absolute;left:60px;top:1210px;width:960px;height:710px;object-fit:cover;object-position:50% 0;border-radius:44px;z-index:1" />
      <div id="pop-win" style="z-index:2">
{chr(10).join(pops)}
      </div>
      <div id="pop-out" style="z-index:3">
{chr(10).join(mattes)}
        <!-- 素材结束后的最后几帧：抠像最后一帧的头部，接着越出窗框 -->
        <img id="end-head" class="clip" src="assets/img/end_head.png" alt="" data-start="{num(FOOTAGE_END - 0.1)}" data-duration="{num(round(TOTAL - FOOTAGE_END + 0.1, 2))}" data-track-index="2" style="position:absolute;left:0;top:0;width:480px;height:250px" />
      </div>
      <div id="face-a-wrap" style="z-index:6">
{chr(10).join(fulls)}
      </div>

{chr(10).join(scenes)}

      <div id="captions-host" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{num(TOTAL)}" data-track-index="7" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:10"></div>

      <!-- 人声：原片去掉句间吸气（gate_breaths.py），时间轴不变 -->
      <audio id="voice" class="clip" src="assets/footage/voice.wav" data-start="0" data-duration="{num(FOOTAGE_END)}" data-media-start="0" data-volume="1" data-track-index="8"></audio>
      <audio id="bgm" class="clip" src="assets/audio/bgm.m4a" data-start="0" data-duration="{num(TOTAL)}" data-media-start="0" data-volume="0.3" data-track-index="9"></audio>
{sfx_html}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      // 全屏真人段在情绪词上推近
{pushes}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def main():
    for p, n in zip(SEG, SEG[1:]):
        if abs(p[2] - n[1]) > 1e-6:
            raise SystemExit(f"镜头 {p[0]} 和 {n[0]} 之间有空档或重叠")
    caps = align()
    t0 = {sid: a for sid, a, *_ in SEG}
    for f in COMP.glob("*.html"):
        f.unlink()
    for sid, text in write_scenes(t0).items():
        (COMP / f"{sid}.html").write_text(text, encoding="utf-8")
    (COMP / "captions.html").write_text(captions(caps), encoding="utf-8")
    (HERE / "index.html").write_text(index(), encoding="utf-8")
    out = []
    for i, (sid, a, b, lay, th, visual) in enumerate(SEG, 1):
        spoken = "".join(t.replace("*", "") for t, s, e in caps if a <= s < b)
        out.append({"id": f"s{i:02d}-{sid}", "start": a, "end": b, "label": f"{lay} {sid}", "visual": visual, "spoken": spoken})
    (HERE.parent / "scenes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(SEG)} 个镜头，{len(caps)} 个字幕词，总长 {num(TOTAL)} 秒")


if __name__ == "__main__":
    main()

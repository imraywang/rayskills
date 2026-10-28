"""qingdan（清单口播）构建脚本：一张镜头表 + 一张字幕分词表，生成整套工程。
  - index.html：奶油底、探头真人（窗内原片 + 窗外抠像）、全屏真人、各场景挂载、音频
  - compositions/*.html：钩子 H、编号卡 N、三层卡 P、串线 R、导流 C、字幕
  - ../scenes.json：审片页按它分段
版式：H/P/R/C 是奶油底 + 下方探头真人；N/F 是全屏真人。时间都是原片时间轴（gate_breaths 只压吸气，不剪时间）。
改镜头、改字幕只改这个文件，然后 python3 build.py。
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
COMP = HERE / "compositions"
FOOTAGE_END = 81.47
TOTAL = 81.6

CREAM, INK, GREEN, MINT, GREY = "#f4f1ea", "#111111", "#054c4c", "#9cc2bf", "#767676"

# 镜头表：(id, 起, 止, 版式, 说明)
SEG = [
    ("hook", 0, 7.6, "H", "离不开的 4 个 → 100+ 条视频 / 5 万粉"),
    ("n1", 7.6, 8.9, "N", "#1 Obsidian"),
    ("p1", 8.9, 24.25, "P", "obsidian.md → 知识库文件夹 → AI 扫读"),
    ("n2", 24.25, 26.45, "N", "#2 Claude"),
    ("p2", 26.45, 37.3, "P", "Claude Code → 知识库提交记录"),
    ("n3", 37.3, 38.95, "N", "#3 HyperFrames"),
    ("p3", 38.95, 50.95, "P", "GitHub 仓库 → 本片编号卡源码"),
    ("n4", 50.95, 52.25, "N", "#4 Tailscale"),
    ("p4", 52.25, 64.7, "P", "tailscale.com → 手机上的工作台"),
    ("recap", 64.7, 72.2, "R", "四个连成一条线：存 想 做 带"),
    ("judge", 72.2, 77.35, "F", "全屏真人，串联处推近"),
    ("cta", 77.35, TOTAL, "C", "评论区打「工具」"),
]
CREAMS = "HPRC"

# 编号卡：(编号, 名字)
NUMS = {"n1": (1, "OBSIDIAN"), "n2": (2, "CLAUDE"), "n3": (3, "HYPERFRAMES"), "n4": (4, "TAILSCALE")}

# 字幕分词：按顺序覆盖整条逐字稿。每项是 (显示, whisper 原文) 或单个字符串（两者相同）；显示为 None 的不出字幕
# （钩子、编号卡、串线、导流段由画面本身承担文字）。*词* 用墨绿标重点，一个镜头最多一处。
CHUNKS = [
    (None, "说实话我每天真正离不开的工具就四个就靠这四个过去半年我一个人做了100多条视频全网收获近5万粉丝"),
    (None, "第一个obsidian"),
    "我看到的", "文章", "突然", "冒出来的", "想法", "写到一半的", "稿子", ("全部", "全部都"), "存在这里",
    "最关键的是", "它就是", "存在", "你自己", "电脑上的", "*普通文件*", "不锁在", "任何的", "一个平台", "里面",
    "所以", "AI", "可以直接", "把你", "整个知识库", "从头", "读一遍", "这个价值", "也会", "随着", "你的使用", "越来越大",
    (None, "第二个cloud我真的离不开它一点"),
    "我是让它", "直接", "*住进*", "我的知识库", "读我的", "笔记", "帮我", "写稿", "写代码", "把整套", "流程", "都给跑完",
    "它撑起了", "我所有的", "内容生产", "需要", "从文章", "APP", "视频", "都是它", "来完成的",
    (None, "第三个hyperframes"),
    "这是一个", "用网页代码", "做视频的", "开源工具", "我不会", "剪辑", "字幕", "卡片", "动画", "全部", "让AI",
    "写成网页", ("再渲染", "再缺乱"), "成视频", "你现在", "看到", "这些编号", "和卡片", "就是", "这么", "*做出来的*",
    (None, "第四个talescale"),
    "它能让", "你的手机", "在任何地方", "都连回", "家里的", "那台电脑", "我在外面", "掏出手机", "就能打开", "我自己的",
    "*工作台*", "看今天的", "选题", ("审刚", "省钢"), ("渲染好的", "绚烂好的"), "片子", "随手", ("记一个", "记忆一个"),
    "灵感", "跟坐在", "电脑前面", "没有", "任何的", "区别",
    (None, "所以这四个其实是一条线obsidian负责存cloud负责想hyperframes负责做talescale让你走到哪带到哪"),
    "工具", "真的", "不在于", "多少", "而是在于", "你能不能", "把它们", ("给*串联*", "给串联"), "起来", "变成", "你真正的", "生产力",
    (None, "评论区打工具我把这四个的上手清单和我自己的配置发给你"),
]


def norm(s):
    return re.sub(r"[\s，,。、？?！!：:；;“”\"'*]", "", s).lower()


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

CARD_CSS = """
    .card { position: absolute; left: 60px; top: 150px; width: 960px; height: 600px; border-radius: 36px; overflow: hidden;
            background: #1b1b1b; box-shadow: 0 28px 60px rgba(17,17,17,0.22), 0 4px 12px rgba(17,17,17,0.12); }
    .card img { position: absolute; left: 0; top: 0; width: 960px; height: 600px; object-fit: cover; object-position: 50% 0; }
    .src { position: absolute; left: 66px; top: 92px; font-family: "JetBrains Mono", monospace; font-size: 30px; color: #767676; letter-spacing: 0.02em; }
    .term { padding: 34px 40px; font-family: "JetBrains Mono", "HeiBold", monospace; font-size: 27px; line-height: 1.62; color: #d8d8d4; }
    .term .bar { display: flex; gap: 12px; margin-bottom: 22px; }
    .term .bar i { width: 18px; height: 18px; border-radius: 50%; background: #3a3a3a; display: block; }
    .term .hd { color: #8c8c8c; margin-bottom: 8px; }
    .term .row { white-space: nowrap; overflow: hidden; }
    .term .k { color: #9cc2bf; } .term .s { color: #e8c9a0; } .term .d { color: #6e6e6e; } .term .g { color: #9cc2bf; }"""


def scene(sid, css, body, js):
    return f"""<template>
  <style>{FONTS}
    #{sid} {{ position: absolute; inset: 0; overflow: hidden; }}{css}
  </style>
  <div id="{sid}" data-composition-id="{sid}" data-width="1080" data-height="1920">
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def numcard(sid, n, name):
    size = 104 if len(name) <= 8 else 86
    css = f"""
    #{sid} svg {{ position: absolute; left: 0; top: 1150px; width: 1080px; height: 460px; overflow: visible; }}
    #{sid} .name {{ position: absolute; left: 0; right: 0; top: 1490px; text-align: center; font-family: "Playfair Display", serif;
              font-style: italic; font-weight: 900; font-size: {size}px; color: #fff; letter-spacing: 0.01em;
              text-shadow: 0 6px 24px rgba(0,0,0,0.45), 0 2px 4px rgba(0,0,0,0.35); }}
    #{sid} .name span {{ display: inline-block; }}"""
    letters = "".join(f'<span class="ch">{esc(c)}</span>' for c in name)
    body = f"""    <svg viewBox="0 0 1080 460" data-layout-allow-overlap>
      <defs><linearGradient id="{sid}-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{MINT}"/><stop offset="1" stop-color="{GREEN}"/></linearGradient></defs>
      <g id="{sid}-num"><text x="540" y="400" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-weight="900" font-size="440"
        fill="rgba(5,76,76,0.10)" stroke="url(#{sid}-g)" stroke-width="7" paint-order="stroke">#{n}</text></g>
    </svg>
    <div id="{sid}-name" class="name" data-layout-allow-overlap>{letters}</div>"""
    js = f"""    // 硬切进来：编号先落下，名字逐个字母跟上
    tl.fromTo("#{sid}-num", {{ opacity: 0, scale: 1.18, transformOrigin: "540px 260px" }}, {{ opacity: 1, scale: 1, duration: 0.28, ease: "power3.out" }}, 0);
    tl.fromTo("#{sid}-name .ch", {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "power2.out", stagger: 0.03 }}, 0.2);"""
    return scene(sid, css, body, js)


def cards_scene(sid, cards, extra_css="", extra_js=""):
    """cards: [(id, 相对起点, 源标签, 内容 HTML)]，后一张从下方推上来，前一张往上淡出。"""
    body, js = [], []
    for k, (cid, t, label, inner) in enumerate(cards):
        body.append(f'    <div id="{cid}-src" class="src">{esc(label)}</div>')
        body.append(f'    <div id="{cid}" class="card">{inner}</div>')
        js.append(f'    tl.fromTo("#{cid}", {{ opacity: 0, y: 60, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.42, ease: "power3.out" }}, {t});')
        js.append(f'    tl.fromTo("#{cid}-src", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {t + 0.1:.2f});')
        if k + 1 < len(cards):
            t2 = cards[k + 1][1]
            js.append(f'    tl.to(["#{cid}", "#{cid}-src"], {{ opacity: 0, y: -30, duration: 0.25, ease: "power2.in" }}, {t2 - 0.05:.2f});')
    return scene(sid, CARD_CSS + extra_css, "\n".join(body), "\n".join(js) + "\n" + extra_js)


def img(src):
    return f'<img src="assets/img/{src}" alt="" />'


def push_js(sel, t, dur, to=1.06):
    return f'    tl.fromTo("{sel}", {{ scale: 1 }}, {{ scale: {to}, duration: {dur}, ease: "none", transformOrigin: "50% 0%" }}, {t});'


def vault_tree():
    rows = [("00-入口", "首页、索引"), ("10-创作", "灵感、选题、口播、文章"), ("20-知识", "长期知识"), ("30-资料", "剪藏、访谈、调研"),
            ("40-发布", "已发布的每一条"), ("50-系统", "模板、自动化"), ("60-素材", "图片、视频"), ("70-思考", "原则、当前关注")]
    r = "".join(f'<div class="row"><span class="k">▸ {esc(a)}/</span>  <span class="d">{esc(b)}</span></div>' for a, b in rows)
    return (f'<div class="term"><div class="bar"><i></i><i></i><i></i></div><div class="hd">~/rays-brain</div>{r}'
            f'<div class="row" style="margin-top:10px"><span class="g">4,201</span> <span class="d">× .md · 纯文本</span></div></div>'
            f'<div id="scan" class="scan"></div>')


def git_log():
    rows = [("a787482", "口播草稿：我每天离不开的四个生产力工具"), ("0631dd1", "清单口播包装拆解：Brock Mesarich"),
            ("971f676", "爆款雷达：TikHub 抓取 + 工作台雷达页"), ("2372ccd", "口播草稿：为什么企业上 AI 前半年看不到效果"),
            ("266502c", "候选选题：按爆款雷达规律列出 8 个题"), ("aaf59c7", "爆款选题雷达：方案稿与探针记录")]
    r = "".join(f'<div class="row"><span class="s">{h}</span> {esc(t)}</div>' for h, t in rows)
    return (f'<div class="term"><div class="bar"><i></i><i></i><i></i></div><div class="hd">$ git log --oneline</div>{r}'
            f'<div class="row d" style="margin-top:10px">Co-Authored-By: Claude</div></div>')


def code_card():
    lines = [
        '<span class="d">&lt;!-- compositions/n3.html --&gt;</span>',
        '<span class="k">&lt;text</span> font-size=<span class="s">"440"</span>',
        '  stroke=<span class="s">"url(#grad)"</span><span class="k">&gt;</span>#3<span class="k">&lt;/text&gt;</span>',
        '<span class="k">&lt;div</span> class=<span class="s">"name"</span><span class="k">&gt;</span>HYPERFRAMES<span class="k">&lt;/div&gt;</span>',
        '',
        'tl.<span class="k">fromTo</span>(<span class="s">"#n3-num"</span>,',
        '  { scale: <span class="g">1.18</span> }, { scale: <span class="g">1</span> }, <span class="g">0</span>);',
    ]
    r = "".join(f'<div class="row">{l or "&nbsp;"}</div>' for l in lines)
    return f'<div class="term"><div class="bar"><i></i><i></i><i></i></div>{r}</div>'


LOGOS = {"obsidian": "logo_obsidian.png", "claude": "logo_claude.png", "hyperframes": "logo_hyperframes.svg", "tailscale": "logo_tailscale.svg"}
TOOLS = ["obsidian", "claude", "hyperframes", "tailscale"]

TILE_CSS = """
    .tile { position: absolute; left: 0; top: 0; width: 176px; height: 176px; border-radius: 40px; background: #fff; overflow: hidden;
            box-shadow: 0 18px 40px rgba(17,17,17,0.16), 0 3px 8px rgba(17,17,17,0.1); }
    .tile img { position: absolute; left: 0; top: 0; width: 176px; height: 176px; object-fit: contain; }
    .tile.pad img { padding: 26px; }"""


def tile(name):
    pad = " pad" if name in ("claude", "hyperframes") else ""
    return f'<div class="tile{pad}"><img src="assets/img/{LOGOS[name]}" alt="" /></div>'


def write_scenes(t0):
    """t0[sid] = 镜头起点；场景里的时间都是相对时间，注释里写原片时间。"""
    out = {sid: numcard(sid, n, name) for sid, (n, name) in NUMS.items()}

    # ---- H 钩子：0 秒起 ----
    xs = [80, 312, 592, 824]
    tiles = "\n".join(f'    <div class="tw" style="left:{x}px;top:470px">{tile(n)}</div>' for x, n in zip(xs, TOOLS))
    css = TILE_CSS + f"""
    #hook .tw {{ position: absolute; width: 176px; height: 176px; }}
    #hook .l1 {{ position: absolute; left: 0; right: 0; top: 118px; text-align: center; font-family: "HeiHeavy"; font-weight: 900; font-size: 66px; color: {INK}; }}
    #hook .big {{ position: absolute; left: 0; right: 0; top: 196px; text-align: center; white-space: nowrap; }}
    #hook .big b {{ font-family: "Playfair Display", serif; font-style: italic; font-weight: 900; font-size: 250px; line-height: 1; color: rgba(5,76,76,0.08);
                   -webkit-text-stroke: 7px {GREEN}; vertical-align: -18px; }}
    #hook .big span {{ font-family: "HeiHeavy"; font-weight: 900; font-size: 116px; color: {INK}; margin-left: 18px; }}
    #hook .stat {{ position: absolute; top: 230px; width: 540px; text-align: center; }}
    #hook .stat b {{ display: block; white-space: nowrap; font-family: "Playfair Display", serif; font-style: italic; font-weight: 900; font-size: 200px; line-height: 1; color: {INK}; }}
    #hook .stat b small {{ font-family: "HeiHeavy"; font-style: normal; font-size: 110px; }}
    #hook .stat .lbl {{ display: block; margin-top: 26px; font-family: "HeiBold"; font-weight: 700; font-size: 50px; color: {GREY}; }}
    #hook .stat.r b {{ color: {GREEN}; }}
    #hook .half {{ position: absolute; left: 0; right: 0; top: 120px; text-align: center; font-family: "HeiBold"; font-weight: 700; font-size: 50px; color: {GREY}; }}"""
    body = f"""    <div id="h-l1" class="l1">我每天离不开的</div>
    <div id="h-big" class="big"><b>4</b><span>个工具</span></div>
{tiles}
    <div id="h-half" class="half">过去半年 · 一个人</div>
    <div id="h-s1" class="stat" style="left:0"><b><span id="h-c1">0</span>+</b><span class="lbl">条视频</span></div>
    <div id="h-s2" class="stat r" style="left:540px"><b><small>近</small><span id="h-c2">0</span><small>万</small></b><span class="lbl">全网粉丝</span></div>"""
    js = """    // 场景从 0 秒开始。「每天…离不开」→「四个」大字 →「就靠这四个」四个图标依次弹出 →「过去半年」切到两组数字
    tl.fromTo("#h-l1", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }, 0.5);
    tl.fromTo("#h-big", { opacity: 0, scale: 0.86 }, { opacity: 1, scale: 1, duration: 0.32, ease: "power3.out" }, 2.08);
    tl.fromTo("#hook .tw", { opacity: 0, y: 40, scale: 0.7 }, { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: "back.out(1.6)", stagger: 0.13 }, 2.64);
    tl.to(["#h-l1", "#h-big", "#hook .tw"], { opacity: 0, y: -40, duration: 0.25, ease: "power2.in" }, 3.3);
    tl.fromTo("#h-half", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.3 }, 3.45);
    tl.fromTo("#h-s1", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }, 4.4);
    const c1 = { v: 0 }, c2 = { v: 0 };
    tl.to(c1, { v: 100, duration: 0.6, ease: "power2.out", onUpdate: () => { document.getElementById("h-c1").textContent = Math.round(c1.v); } }, 4.75);
    tl.fromTo("#h-s2", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }, 6.2);
    tl.to(c2, { v: 5, duration: 0.45, ease: "power2.out", onUpdate: () => { document.getElementById("h-c2").textContent = Math.round(c2.v); } }, 6.5);"""
    out["hook"] = scene("hook", css, body, js)

    # ---- P1：8.9 秒起 ----
    a = t0["p1"]
    scan_css = """
    #p1 .scan { position: absolute; left: 0; right: 0; top: 0; height: 120px; opacity: 0;
                background: linear-gradient(180deg, rgba(156,194,191,0) 0%, rgba(156,194,191,0.35) 85%, #9cc2bf 100%); }"""
    out["p1"] = cards_scene("p1", [
        ("p1a", 0.0, "obsidian.md", img("shot_obsidian.jpg")),
        ("p1b", round(13.2 - a, 2), "~/rays-brain · 本地文件夹", vault_tree()),
    ], scan_css, push_js("#p1a img", 0, 4.3) + f"""
    // 「AI 可以直接把你整个知识库从头读一遍」（18.9 秒）：一道扫描线从上扫到下，扫两遍
    tl.set("#scan", {{ opacity: 1 }}, {18.9 - a:.2f});
    tl.fromTo("#scan", {{ y: -120 }}, {{ y: 600, duration: 1.1, ease: "none", repeat: 1 }}, {18.9 - a:.2f});
    tl.set("#scan", {{ opacity: 0 }}, {21.2 - a:.2f});""")

    # ---- P2：26.45 秒起 ----
    a = t0["p2"]
    out["p2"] = cards_scene("p2", [
        ("p2a", 0.0, "claude.com/product/claude-code", img("shot_claude.jpg")),
        ("p2b", round(32.3 - a, 2), "rays-brain · 最近的提交", git_log()),
    ], "", push_js("#p2a img", 0, 5.8) + f"""
    // 「它撑起了我所有的内容生产」（32.4 秒）：提交记录逐行出现
    tl.fromTo("#p2b .row", {{ opacity: 0, x: -14 }}, {{ opacity: 1, x: 0, duration: 0.2, stagger: 0.12 }}, {32.45 - a:.2f});""")

    # ---- P3：38.95 秒起 ----
    a = t0["p3"]
    out["p3"] = cards_scene("p3", [
        ("p3a", 0.0, "github.com/heygen-com/hyperframes", img("shot_hyperframes.jpg")),
        ("p3b", round(47.4 - a, 2), "这一集的编号卡", code_card()),
    ], "", push_js("#p3a img", 0, 8.4) + f"""
    // 「你现在看到这些编号和卡片」（47.5 秒）：换成本片编号卡的源码
    tl.fromTo("#p3b .row", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15, stagger: 0.1 }}, {47.55 - a:.2f});""")

    # ---- P4：52.25 秒起 ----
    a = t0["p4"]
    phone_css = """
    #p4 .phone { position: absolute; left: 380px; top: 110px; width: 320px; height: 692px; border-radius: 52px; background: #111; padding: 11px;
                 box-shadow: 0 30px 70px rgba(17,17,17,0.28); }
    #p4 .phone img { width: 298px; height: 670px; border-radius: 42px; object-fit: cover; object-position: 50% 0; display: block; }"""
    out["p4"] = scene("p4", CARD_CSS + phone_css, """    <div id="p4a-src" class="src">tailscale.com</div>
    <div id="p4a" class="card"><img src="assets/img/shot_tailscale.jpg" alt="" /></div>
    <div id="p4b" class="phone"><img src="assets/img/shot_phone.jpg" alt="" /></div>""", f"""    // 「我在外面掏出手机」（55.7 秒）：网页卡退场，手机从下面立起来
    tl.fromTo("#p4a", {{ opacity: 0, y: 60, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.42, ease: "power3.out" }}, 0);
    tl.fromTo("#p4a-src", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, 0.1);
{push_js("#p4a img", 0, 3.4)}
    tl.to(["#p4a", "#p4a-src"], {{ opacity: 0, y: -30, duration: 0.25, ease: "power2.in" }}, {55.75 - a:.2f});
    tl.fromTo("#p4b", {{ opacity: 0, y: 120, rotation: 6 }}, {{ opacity: 1, y: 0, rotation: 0, duration: 0.5, ease: "power3.out" }}, {55.95 - a:.2f});""")

    # ---- R 串线：64.7 秒起 ----
    a = t0["recap"]
    xs = [70, 318, 586, 834]
    tw = "\n".join(f'    <div class="tw" id="rt-{k}" style="left:{x}px;top:300px">{tile(n)}<div class="lab" id="lab-{k}">{c}</div></div>'
                   for k, (x, n, c) in enumerate(zip(xs, TOOLS, "存想做带")))
    css = TILE_CSS + f"""
    #recap .tw {{ position: absolute; width: 176px; height: 330px; }}
    #recap .lab {{ position: absolute; left: 0; right: 0; top: 210px; text-align: center; font-family: "HeiHeavy"; font-weight: 900; font-size: 96px; color: {GREEN}; }}
    #recap svg {{ position: absolute; left: 0; top: 0; width: 1080px; height: 900px; }}
    #recap .ttl {{ position: absolute; left: 0; right: 0; top: 140px; text-align: center; font-family: "Playfair Display", serif; font-style: italic; font-weight: 900; font-size: 64px; color: {GREY}; }}"""
    body = f"""    <svg viewBox="0 0 1080 900"><line id="r-line" x1="158" y1="388" x2="922" y2="388" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" stroke-dasharray="764" stroke-dashoffset="764"/></svg>
    <div id="r-ttl" class="ttl">one line</div>
{tw}"""
    js = f"""    // 场景从 64.7 秒开始。「这四个」四个图标进；「一条线」（66.0）画线；存 / 想 / 做 / 带 各落在说到的字上
    tl.fromTo("#recap .tw", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "power3.out", stagger: 0.08 }}, {65.1 - a:.2f});
    tl.set("#recap .lab", {{ opacity: 0 }}, 0);
    tl.to("#r-line", {{ strokeDashoffset: 0, duration: 0.6, ease: "power2.inOut" }}, {66.0 - a:.2f});
    tl.fromTo("#r-ttl", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {66.1 - a:.2f});"""
    for k, t in enumerate([67.42, 68.46, 69.78, 71.62]):
        js += f"""
    tl.fromTo("#lab-{k}", {{ opacity: 0, y: 24, scale: 0.8 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.25, ease: "back.out(2)" }}, {t - a - 0.05:.2f});
    tl.fromTo("#rt-{k} .tile", {{ scale: 1 }}, {{ scale: 1.1, duration: 0.12, yoyo: true, repeat: 1, ease: "power2.out" }}, {t - a - 0.05:.2f});"""
    out["recap"] = scene("recap", css, body, js)

    # ---- C 导流：77.35 秒起 ----
    a = t0["cta"]
    css = f"""
    #cta .gcard {{ position: absolute; left: 60px; top: 150px; width: 960px; height: 250px; border-radius: 36px; background: {GREEN};
                  box-shadow: 0 28px 60px rgba(5,76,76,0.28); }}
    #cta .gcard span {{ position: absolute; left: 0; right: 0; top: 78px; text-align: center; font-family: "HeiBold"; font-weight: 700; font-size: 72px; color: #f3f3f0; letter-spacing: 0.08em; }}
    #cta .kw {{ position: absolute; left: 0; right: 0; top: 450px; text-align: center; font-family: "HeiHeavy"; font-weight: 900; font-size: 200px; line-height: 1; color: {INK}; }}
    #cta .kw em {{ font-style: normal; color: {GREEN}; }}
    #cta .sub {{ position: absolute; left: 0; right: 0; top: 700px; text-align: center; font-family: "HeiBold"; font-weight: 700; font-size: 46px; color: {GREY}; }}"""
    body = """    <div id="c-card" class="gcard"><span>评论区打</span></div>
    <div id="c-kw" class="kw"><em>「</em>工具<em>」</em></div>
    <div id="c-sub" class="sub">上手清单 + 我的配置</div>"""
    js = f"""    // 场景从 77.35 秒开始：「评论区打」→「工具」（78.0）→「上手清单和配置」（79.3）
    tl.fromTo("#c-card", {{ opacity: 0, y: 50, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "power3.out" }}, 0.05);
    tl.fromTo("#c-kw", {{ opacity: 0, scale: 1.25 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "power3.out" }}, {77.98 - a:.2f});
    tl.fromTo("#c-sub", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.3 }}, {79.3 - a:.2f});"""
    out["cta"] = scene("cta", css, body, js)
    return out


def captions(caps):
    full = [(a, b) for _, a, b, lay, _ in SEG if lay == "F"]
    rows = []
    for i, (text, s, e) in enumerate(caps, 1):
        pos = "low" if any(a <= s < b for a, b in full) else "mid"
        rows.append(f'    <div id="c{i:03d}" class="cap {pos} clip" data-start="{s}" data-duration="{round(e - s, 2)}"><span>{emph(text)}</span></div>')
    return f"""<template>
  <style>{FONTS}
    #captions {{ position: absolute; inset: 0; pointer-events: none; }}
    #captions .cap {{ position: absolute; left: 0; right: 0; text-align: center; white-space: nowrap; }}
    /* 奶油底：一次一个词，压在截图卡和探头真人之间 */
    #captions .cap.mid {{ top: 846px; font-family: "HeiHeavy"; font-weight: 900; font-size: 84px; color: {INK}; letter-spacing: 0.01em; }}
    #captions .cap.mid em {{ font-style: normal; color: {GREEN}; }}
    /* 全屏真人：白字带阴影，偏下 */
    #captions .cap.low {{ top: 1330px; font-family: "HeiHeavy"; font-weight: 900; font-size: 76px; color: #fff;
                         text-shadow: 0 4px 18px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.5); }}
    #captions .cap.low em {{ font-style: normal; color: {MINT}; }}
  </style>
  <div id="captions" data-composition-id="captions" data-width="1080" data-height="1920">
    <!-- 一次一个词：由 build.py 按逐字时间生成，改字改时间去那里改 -->
{chr(10).join(rows)}
  </div>
  <script>
    window.__timelines["captions"] = gsap.timeline({{ paused: true }});
  </script>
</template>
"""


def index():
    pops, mattes, fulls, scenes = [], [], [], []
    for sid, a, b, lay, _ in SEG:
        dur = round(min(b, FOOTAGE_END) - a, 3)
        if lay in CREAMS:
            pops.append(f'        <video id="pw-{sid}" class="clip" src="assets/footage/face_pop.mp4" muted playsinline data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="1"></video>')
            mattes.append(f'        <video id="pm-{sid}" class="clip" src="assets/footage/face_pop_matte.webm" muted playsinline data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="2"></video>')
        else:
            fulls.append(f'        <video id="fa-{sid}" class="clip" src="assets/footage/face_full.mp4" muted playsinline data-start="{num(a)}" data-duration="{num(dur)}" data-media-start="{num(a)}" data-track-index="3"></video>')
        if lay != "F":
            z, track = (7, 5) if lay == "N" else (5, 4)
            scenes.append(f'      <div id="h-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{num(a)}" data-duration="{num(round(b - a, 3))}" '
                          f'data-track-index="{track}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:{z}"></div>')

    sfx = [(f"sfx-{sid}", "whoosh.wav", round(a - 0.12, 2), 0.7, 0.4, 11) for sid, a, b, lay, _ in SEG if lay == "N"]
    sfx += [("sfx-tiles", "click.wav", 2.64, 0.05, 0.4), ("sfx-100", "ding.wav", 5.3, 0.7, 0.3), ("sfx-5w", "ding.wav", 6.9, 0.7, 0.3),
            ("sfx-phone", "click.wav", 55.95, 0.05, 0.45), ("sfx-line", "whoosh.wav", 65.95, 0.7, 0.3),
            ("sfx-r1", "click.wav", 67.37, 0.05, 0.4), ("sfx-r2", "click.wav", 68.41, 0.05, 0.4), ("sfx-r3", "click.wav", 69.73, 0.05, 0.4),
            ("sfx-r4", "click.wav", 71.57, 0.05, 0.4), ("sfx-kw", "ding.wav", 77.98, 0.7, 0.35)]
    sfx = [x if len(x) == 6 else (*x, 10) for x in sfx]
    sfx_html = "\n".join(f'      <audio id="{i}" class="clip" src="assets/audio/{f}" data-start="{s}" data-duration="{d}" data-volume="{v}" data-track-index="{tr}"></audio>' for i, f, s, d, v, tr in sfx)

    judge = next(s for s in SEG if s[0] == "judge")
    return f"""<!doctype html>
<html lang="zh-CN" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: {CREAM}; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
      /* 奶油底：两团很淡的暖色光，模拟窗边的光影 */
      #bg {{ position: absolute; inset: 0; background:
              radial-gradient(900px 700px at 88% 6%, rgba(255,255,255,0.75), rgba(255,255,255,0) 70%),
              radial-gradient(800px 900px at 0% 60%, rgba(214,204,186,0.35), rgba(214,204,186,0) 70%), {CREAM}; }}
      /* 探头真人：窗里放原片，窗上沿以上只放抠像，头顶越出窗框 */
      #pop-win {{ position: absolute; left: 60px; top: 1210px; width: 960px; height: 760px; border-radius: 44px; overflow: hidden;
                 box-shadow: 0 30px 70px rgba(17,17,17,0.20), 0 4px 14px rgba(17,17,17,0.12); }}
      #pop-win video {{ position: absolute; left: -60px; top: -250px; width: 1080px; height: 960px; }}
      #pop-out {{ position: absolute; left: 300px; top: 960px; width: 480px; height: 250px; overflow: hidden; }}
      /* 只让头越出窗框：抠像层只留头部那一条，抬起来的手不会跑出窗外 */
      #pop-out video {{ position: absolute; left: -300px; top: 0; width: 1080px; height: 960px; }}
      /* 全屏真人（编号卡、判断句） */
      #face-a-wrap {{ position: absolute; inset: 0; transform-origin: 50% 32%; }}
      #face-a-wrap video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <!-- 清单口播：奶油底 + 探头真人（H/P/R/C）与全屏真人（N/F）硬切交替。镜头表在 build.py。 -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="{num(TOTAL)}" data-width="1080" data-height="1920">
      <div id="bg"></div>
      <!-- 结尾垫一帧，免得画面比导流卡先结束 -->
      <img id="end-still" class="clip" src="assets/img/end_still_pop.jpg" alt="" data-start="{num(FOOTAGE_END - 0.1)}" data-duration="{num(round(TOTAL - FOOTAGE_END + 0.1, 2))}" data-track-index="0" style="position:absolute;left:60px;top:1210px;width:960px;height:710px;object-fit:cover;object-position:50% 0;border-radius:44px;z-index:1" />
      <div id="pop-win" style="z-index:2">
{chr(10).join(pops)}
      </div>
      <div id="pop-out" style="z-index:3">
{chr(10).join(mattes)}
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
      // 判断句「串联」上推近
      tl.set("#face-a-wrap", {{ scale: 1 }}, {judge[1]});
      tl.to("#face-a-wrap", {{ scale: 1.08, duration: 0.22, ease: "power2.out" }}, 75.3);
      tl.set("#face-a-wrap", {{ scale: 1 }}, {judge[2]});
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
    for sid, text in write_scenes(t0).items():
        (COMP / f"{sid}.html").write_text(text, encoding="utf-8")
    (COMP / "captions.html").write_text(captions(caps), encoding="utf-8")
    (HERE / "index.html").write_text(index(), encoding="utf-8")
    out = []
    for i, (sid, a, b, lay, visual) in enumerate(SEG, 1):
        spoken = "".join(t.replace("*", "") for t, s, e in caps if a <= s < b)
        out.append({"id": f"s{i:02d}-{sid}", "start": a, "end": b, "label": f"{lay} {sid}", "visual": visual, "spoken": spoken})
    (HERE.parent / "scenes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(SEG)} 个镜头，{len(caps)} 个字幕词，总长 {num(TOTAL)} 秒")


if __name__ == "__main__":
    main()

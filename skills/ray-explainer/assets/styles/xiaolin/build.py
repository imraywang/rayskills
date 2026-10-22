#!/usr/bin/env python3
"""Style `xiaolin` (ray-explainer references/styles/xiaolin.md). Worked example: 马斯克送股, 191.8 s, landscape.
python3 build.py -> index.html + brush.txt
Times come from the narration timeline: @[scene.line.phrase(+/-offset)] in the template is replaced by the second the
phrase starts (first char of the phrase in that line). SHOTS / CHAPTERS / NAMES below use the same anchor syntax."""
import json, re

TL = json.load(open("src/timeline.json"))
DUR = 191.8
LINES = {}
for s in TL["scenes"]:
    for i, l in enumerate(s["lines"], 1):
        LINES[f"{s['id']}.{i}"] = l

def at(ref):
    m = re.fullmatch(r"(\w+)\.(\d+)(?:\.([^+\-]*))?([+\-][\d.]+)?", ref.strip())
    if not m: raise SystemExit(f"bad anchor {ref}")
    sc, ln, ph, off = m.groups()
    l = LINES[f"{sc}.{ln}"]
    if ph:
        k = l["text"].find(ph)
        if k < 0: raise SystemExit(f"phrase {ph!r} not in {sc}.{ln}: {l['text']}")
        t = l["chars"][k]
    else:
        t = l["start"]
    return round(t + float(off or 0), 2)

def T(x): return x if isinstance(x, (int, float)) else at(x)

# (start, clip, media_start, source label)   each shot runs until the next one starts
SHOTS = [
    (0.0, "starship1", 0, "SpaceX · Starship 第十次试飞"),
    (2.4, "musk1", 0, "VideoFromSpace · Starbase"),
    (4.6, None, 0, ""),                       # tweet board
    ("hook.2-0.05", "musk2", 0, "VideoFromSpace · Starbase"),
    ("hook.3-0.05", "kids2", 0, "The White House"),
    ("hook.3.按发推前", "kids1", 0, "The White House"),
    ("hook.3.一共是-0.4", "nyse1", 0, "AFP"),
    ("hook.4-0.05", "kids3", 0, "The White House"),
    ("hook.4.家长", "kids4", 0, "The White House"),
    ("ask.1-0.05", None, 0, ""),
    ("why.1-0.05", "starship2", 0, "SpaceX"),
    ("why.1.就在前一天", "dario1", 0, "CBS Sunday Morning"),
    ("why.2-0.05", None, 0, ""),
    ("account.1-0.05", "obbba", 0, "The White House · 2025-07-04"),
    ("account.2-0.05", None, 0, ""),
    ("tax.1-0.05", None, 0, ""),
    ("kids.1-0.05", "kids1", 0, "The White House"),
    ("kids.1.一股", "kids4", 0, "The White House"),
    ("kids.2-0.05", None, 0, ""),
    ("kids.3-0.05", "kids3", 0, "The White House"),
    ("kids.3.连财政部", None, 0, ""),
    ("kids.4-0.05", "belltrump", 0, "The White House"),
    ("mongolia.1-0.05", "tt2", 0, "VostokMD · 塔温陶勒盖煤矿"),
    ("mongolia.1.2011", "tt1", 0, "MNB World"),
    ("mongolia.2-0.05", "tt2", 3.5, "VostokMD"),
    ("mongolia.3-0.05", "mng1", 0, "AP Archive · 蒙古选举"),
    ("mongolia.3.在选举前", "mng2", 0, "AP Archive"),
    ("russia.1-0.05", "rus1", 0, "AP Archive · 1994 莫斯科"),
    ("russia.1.用来换", None, 0, ""),
    ("charity.1-0.05", None, 0, ""),
    ("charity.3-0.05", "dell1", 0, "KGW News · 2025-12-02"),
    ("buyoff.1-0.05", None, 0, ""),
    ("buyoff.3-0.05", "podium", 0, "The White House"),
    ("buyoff.3.就得先", "belltrump", 1.5, "The White House"),
    ("end.1-0.05", None, 0, ""),
    ("end.1.你觉得-0.05", "launch", 0, "SpaceX · Falcon 9"),
]

CHAPTERS = [  # top-left chapter tag
    ("why.1-0.05", "account.1-0.05", "① 为什么是现在"),
    ("account.1-0.05", "tax.1-0.05", "② 股票怎么送"),
    ("tax.1-0.05", "kids.1-0.05", "③ 为什么绕道基金会"),
    ("kids.1-0.05", "mongolia.1-0.05", "④ 孩子拿到的是什么"),
    ("mongolia.1-0.05", "charity.1-0.05", "⑤ 历史上的先例"),
    ("charity.1-0.05", "end.1-0.05", "⑥ 慈善，还是收买"),
]

def shots_html():
    rows, k = [], 0
    S = [(T(a), c, m, src) for a, c, m, src in SHOTS] + [(DUR, None, 0, "")]
    for i, (t, c, m, src) in enumerate(S[:-1]):
        if not c: continue
        d = S[i + 1][0] - t
        k += 1
        rows.append(f'      <video id="shot{k:02d}" class="clip shot" src="assets/v/{c}.mp4" muted playsinline data-start="{t:.2f}" data-media-start="{m}" data-duration="{d:.2f}" data-track-index="{1 + k % 2}"></video>')
        if src:
            rows.append(f'      <div class="clip srcl" data-start="{t:.2f}" data-duration="{d:.2f}" data-track-index="7">{src}</div>')
    return "\n".join(rows)

def chapters_html():
    return "\n".join(f'      <div class="clip chap" data-start="{T(a):.2f}" data-duration="{T(b) - T(a):.2f}" data-track-index="8"><i></i>{txt}</div>'
                     for a, b, txt in CHAPTERS)

def captions_html():
    rows, k = [], 0
    for key, l in LINES.items():
        text, ch = l["text"], l["chars"]
        parts = [(m.start(), m.group()) for m in re.finditer(r"[^，。：？；！、]+[，。：？；！、]?", text)]
        for j, (p, seg) in enumerate(parts):
            st = ch[p]
            en = ch[parts[j + 1][0]] if j + 1 < len(parts) else l["end"] + 0.25
            seg = seg.rstrip("，。：；、")
            if not seg.strip(): continue
            k += 1
            rows.append(f'      <div class="clip cap" data-start="{st:.2f}" data-duration="{en - st:.2f}" data-track-index="9"><span>{seg.strip()}</span></div>')
    return "\n".join(rows)

def scenes_json():
    """One row per shot: clip name or 画板, source label, words said. For review.py and qa_video.py."""
    S = [(T(a), c, src) for a, c, m, src in SHOTS] + [(DUR, None, "")]
    rows = []
    for (t, c, src), (t2, _, _) in zip(S, S[1:]):
        if t2 - t < 0.05: continue
        said = "".join(l["text"][k] for l in LINES.values() for k, ct in enumerate(l["chars"]) if t <= ct < t2)
        rows.append({"id": f"s{len(rows) + 1:02d}", "start": round(t, 2), "end": round(t2, 2),
                     "label": c or "画板", "visual": src, "spoken": said})
    json.dump(rows, open("scenes.json", "w"), ensure_ascii=False, indent=1)

scenes_json()
html = open("src/template.html", encoding="utf-8").read()
html = re.sub(r"@\[([^\]]+)\]", lambda m: f"{at(m.group(1))}", html)
def until(m):
    st, un = float(m.group(1)), float(m.group(3))
    return f'data-start="{st}"{m.group(2)}data-duration="{min(un, DUR) - st:.2f}"'
html = re.sub(r'data-start="([\d.]+)"([^>]*?)data-until="([\d.]+)"', until, html)
assert "data-until" not in html, "until without start"
html = (html.replace("/*DUR*/", str(DUR)).replace("<!--SHOTS-->", shots_html())
        .replace("<!--CHAPTERS-->", chapters_html()).replace("<!--CAPTIONS-->", captions_html()))
open("index.html", "w", encoding="utf-8").write(html)
brush = set()
for m in re.finditer(r'class="[^"]*brush[^"]*"[^>]*>(.*?)</', html): brush |= set(m.group(1))
open("brush.txt", "w").write("".join(sorted(c for c in brush if ord(c) > 127)))
print("shots", html.count('class="clip shot"'), "caps", html.count('class="clip cap"'), "brush glyphs", len(brush))

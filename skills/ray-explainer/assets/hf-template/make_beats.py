#!/usr/bin/env python3
"""../timeline.json（tts.py + qa_tts.py 产出的逐字时间，已按 script.json 的 display 映射成显示文本；有原声时再经 splice_clips.py）
→ beats.json（每幕的旁白行、字幕节拍、原声段，时间都是幕内秒）+ assets/beats.js（window.BEATS，场景只读不抄）。

每条字幕 = 一个画面节拍：按标点切，过长的按视觉宽度对半切；切得别扭的（拆开了“科学家”这种词）在 FORCE 里手工断句。
原声（timeline.json 的 clips）：字幕带英文原句（caps[].en），每幕的 BEATS[id].clips = [{id, start, end, speaker, utc, segs}]。
改了配音（重跑 tts/qa/splice）以后只需重跑本脚本和 build.py，场景文件和用锚点写的音效都不用动。"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, "..", "timeline.json")))
SCRIPT = json.load(open(os.path.join(HERE, "..", "script.json")))
PUNCT = "，。？！：；、,.?!:;"
SEP = re.compile(r"[，。？！：；、?!:;]|(?<!\d)[,.]|[,.](?!\d)")   # 半角 , . 夹在两个数字中间（2.5%、100,000）不算断句
_cv = next(p for p in (os.path.join(HERE, "canvas.json"), os.path.expanduser("~/.claude/skills/ray-explainer/assets/canvas.json")) if os.path.exists(p))
MAXW = json.load(open(_cv))[SCRIPT.get("aspect", "portrait")]["hf"]["cap_chars"]   # 一条字幕的最大视觉宽度（中文 1，拉丁 0.55）：竖屏 13，横屏 22
FORCE = {          # 手工断句：整段原文 → 各段原文（按顺序、首尾相接）。写稿子原文（二零一九年）或字幕文本（2019 年）都行，空格不算
    # "以前逆向工程师就是对着这一大坨东西": ["以前逆向工程师", "就是对着这一大坨东西"],
}
DISPLAY = SCRIPT.get("display", {})


def _norm(t):
    """Compare FORCE keys the way captions read: display-mapped, whitespace ignored (qa_tts adds spaces around digits)."""
    for k, v in DISPLAY.items(): t = t.replace(k, v)
    return re.sub(r"\s+", "", t)


FN = {_norm(k): (k, [_norm(x) for x in v]) for k, v in FORCE.items()}
USED = set()


def w(s): return sum(1 if ord(c) > 0x2e80 else 0.55 for c in s)


def split_long(text, i0):
    if _norm(text) in FN:
        key, pieces = FN[_norm(text)]; USED.add(key)
        out, j, cnt = [], 0, 0
        for piece in pieces:
            while j < len(text) and text[j].isspace(): j += 1
            start, need = j, len(piece)
            while j < len(text) and need:
                if not text[j].isspace(): need -= 1
                j += 1
            out.append((text[start:j].strip(), i0 + start))
        return out
    if w(text) <= MAXW: return [(text, i0)]
    best, bi = None, None
    for i in range(3, len(text) - 3):
        score = abs(w(text[:i]) - w(text) / 2)
        if text[i - 1] in "的了是把在就和、 " or text[i] == " ": score -= 2
        if text[i - 1].isascii() and text[i].isascii() and text[i] != " ": score += 9   # 不拆英文单词
        if best is None or score < best: best, bi = score, i
    return split_long(text[:bi], i0) + split_long(text[bi:], i0 + bi)


out = []
for n, s in enumerate(T["scenes"]):
    S = 0.0 if n == 0 else s["start"]
    lines, caps = [], []
    for l in s["lines"]:
        tx, ch = l["text"], l["chars"]
        lines.append({"text": tx, "start": round(l["start"] - S, 3), "end": round(l["end"] - S, 3), "chars": [round(c - S, 3) for c in ch]})
        segs = []
        cuts = [0] + [x for m in SEP.finditer(tx) for x in (m.start(), m.end())] + [len(tx)]
        for p0, p1 in zip(cuts[::2], cuts[1::2]):
            raw = tx[p0:p1]; seg = raw.strip()
            if seg: segs += split_long(seg, p0 + (len(raw) - len(raw.lstrip())))
        for k, (seg, at) in enumerate(segs):
            a = ch[min(at, len(ch) - 1)] - S
            b = (ch[min(segs[k + 1][1], len(ch) - 1)] - S) if k + 1 < len(segs) else l["end"] - S
            caps.append({"s": seg.strip(PUNCT + " "), "a": round(a, 3), "b": round(b, 3)})
    sc_clips = []
    for c in T.get("clips", []):   # splice_clips.py 插入的原声：字幕 = 中文大字 + 英文原句（优先用 script.json clips[].caps 的短句）
        if s["start"] <= c["start"] < s["end"]:
            capdef = {x["id"]: x.get("caps") for x in SCRIPT.get("clips", [])}.get(c["id"])
            segs = [[c["start"] + t, en, zh] for t, en, zh in capdef] if capdef else c["segs"]
            for k, (a, en, zh) in enumerate(segs):
                b = segs[k + 1][0] if k + 1 < len(segs) else c["end"]
                caps.append({"s": zh, "en": en, "a": round(a - S, 3), "b": round(b - S, 3), "clip": c["id"]})
            sc_clips.append({"id": c["id"], "start": round(c["start"] - S, 3), "end": round(c["end"] - S, 3), "speaker": c["speaker"], "utc": c["utc"],
                             "segs": [[round(a - S, 3), en, zh] for a, en, zh in c["segs"]]})
    caps.sort(key=lambda c: c["a"])
    for p, q in zip(caps, caps[1:]):   # 数字被切成两条字幕（2 | 5%）：2026-10-15 是 Ray 看片才发现的，现在重建就报
        if re.search(r"\d$", p["s"]) and re.match(r"[\d.,%]", q["s"]):
            print(f"WARN: 字幕把数字切开了：「{p['s']}」|「{q['s']}」（{s['id']} {p['a']:.2f}s），在 FORCE 里手工断句")
    out.append({"id": s["id"], "start": round(S, 3), "end": round(s["end"], 3), "lines": lines, "caps": caps, "clips": sc_clips})

for k in FORCE:
    if k not in USED: print(f"WARN: FORCE 断句没用上：「{k}」——和字幕里的整段文本对不上（是不是跨了标点，或文字改过）")
B = {"scenes": out, "total": round(T["scenes"][-1]["end"] + 0.4, 3), "narration": round(T["duration"], 3)}
json.dump(B, open(os.path.join(HERE, "beats.json"), "w"), ensure_ascii=False)
os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
open(os.path.join(HERE, "assets", "beats.js"), "w").write("window.BEATS=" + json.dumps({s["id"]: s for s in out}, ensure_ascii=False) + ";")
for s in out:
    print(f'{s["id"]:8} {s["start"]:6.1f}–{s["end"]:6.1f}  caps {len(s["caps"])}')
    for c in s["caps"]: print(f'      {c["a"]:6.2f}–{c["b"]:6.2f}  {c["s"]}')

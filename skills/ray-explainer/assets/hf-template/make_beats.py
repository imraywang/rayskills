#!/usr/bin/env python3
"""../timeline.json（tts.py + qa_tts.py 产出的逐字时间，已按 script.json 的 display 映射成显示文本）
→ beats.json（每幕的旁白行与字幕节拍，时间都是幕内秒）+ assets/beats.js（window.BEATS，场景只读不抄）。

每条字幕 = 一个画面节拍：按标点切，过长的按视觉宽度对半切；切得别扭的在 FORCE 里手工断句。
改了配音（重跑 tts/qa）以后只需重跑本脚本和 build.py，场景文件不用动。"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, "..", "timeline.json")))
PUNCT = "，。？！：；、,.?!:;"
MAXW = 13          # 一条字幕的最大视觉宽度（中文 1，拉丁 0.55）
FORCE = {          # 手工断句：整段原文 → 各段原文（按顺序、首尾相接）
    # "以前逆向工程师就是对着这一大坨东西": ["以前逆向工程师", "就是对着这一大坨东西"],
}


def w(s): return sum(1 if ord(c) > 0x2e80 else 0.55 for c in s)


def split_long(text, i0):
    if text in FORCE:
        out, p = [], 0
        for piece in FORCE[text]:
            q = text.index(piece, p); out.append((piece, i0 + q)); p = q + len(piece)
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
        for m in re.finditer(r"[^%s]+" % re.escape(PUNCT), tx):
            seg = m.group(0).strip()
            if seg: segs += split_long(seg, m.start() + (len(m.group(0)) - len(m.group(0).lstrip())))
        for k, (seg, at) in enumerate(segs):
            a = ch[min(at, len(ch) - 1)] - S
            b = (ch[min(segs[k + 1][1], len(ch) - 1)] - S) if k + 1 < len(segs) else l["end"] - S
            caps.append({"s": seg.strip(PUNCT + " "), "a": round(a, 3), "b": round(b, 3)})
    out.append({"id": s["id"], "start": round(S, 3), "end": round(s["end"], 3), "lines": lines, "caps": caps})

B = {"scenes": out, "total": round(T["scenes"][-1]["end"] + 0.4, 3), "narration": round(T["duration"], 3)}
json.dump(B, open(os.path.join(HERE, "beats.json"), "w"), ensure_ascii=False)
os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
open(os.path.join(HERE, "assets", "beats.js"), "w").write("window.BEATS=" + json.dumps({s["id"]: s for s in out}, ensure_ascii=False) + ";")
for s in out:
    print(f'{s["id"]:8} {s["start"]:6.1f}–{s["end"]:6.1f}  caps {len(s["caps"])}')
    for c in s["caps"]: print(f'      {c["a"]:6.2f}–{c["b"]:6.2f}  {c["s"]}')

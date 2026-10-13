"""Whisper-check every clip against the script, then write per-character timing into the timeline.

usage: python3 qa_tts.py <project_dir>      (run after tts.py)

1. Transcribe each clip with local Whisper (mlx_whisper, word timestamps) and compare with the script line.
   Mismatched clips are renamed *.wav.bad so the next tts.py run re-synthesizes them; exit 1.
2. Align script characters to the heard characters and store line["chars"] = absolute start time of every
   script character (punctuation interpolated). kit at() and grammar cues use it to land on the exact syllable.
3. script.json "display" ({"二零一九年": "2019 年"}): lines are voiced as written (years digit by digit),
   then the timeline text and chars are mapped to the display form, so captions and at() see "2019 年".
   Lines whose voiced text still has 3+ Arabic digits get a WARN: TTS reads them as quantities
   (2019 → 两千零一十九); write them in hanzi and add a display entry. check_numbers.py verifies the reading.
"""
import difflib, json, os, re, sys
import mlx_whisper

PROJ = os.path.abspath(sys.argv[1])
TL_F = os.path.join(PROJ, "timeline.json")
tl = json.load(open(TL_F))
DISPLAY = json.load(open(os.path.join(PROJ, "script.json"))).get("display", {})
PUNCT = r"[\s，。：？、！,.:?!；;“”\"'（）()《》·…—\-]"
norm_ch = lambda ch: not re.match(PUNCT, ch)
MODEL = "mlx-community/whisper-large-v3-turbo"


def char_times(line, words):
    """words: whisper words (times relative to the untrimmed clip). Returns absolute time per script char."""
    heard = []  # (char, t)
    for w in words:
        cs = [c for c in w["word"] if norm_ch(c)]
        for k, c in enumerate(cs):
            heard.append((c.lower(), w["start"] + (w["end"] - w["start"]) * k / max(1, len(cs))))
    text = line["text"]
    idx = [i for i, c in enumerate(text) if norm_ch(c)]
    a = [text[i].lower() for i in idx]
    known = {}
    for blk in difflib.SequenceMatcher(None, a, [h[0] for h in heard], autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            known[idx[blk.a + k]] = line["start"] + heard[blk.b + k][1] - line.get("cut", 0)
    # anchors: line start/end bound everything; interpolate unknown chars (incl. punctuation) linearly
    anchors = [(-1, line["start"])] + sorted(known.items()) + [(len(text), line["end"])]
    out = []
    for i in range(len(text)):
        if i in known: out.append(round(min(max(known[i], line["start"]), line["end"]), 3)); continue
        lo = max(p for p in anchors if p[0] < i); hi = min(p for p in anchors if p[0] > i)
        out.append(round(lo[1] + (hi[1] - lo[1]) * (i - lo[0]) / (hi[0] - lo[0]), 3))
    for i in range(1, len(out)): out[i] = max(out[i], out[i - 1])  # monotonic
    return out, len(known) / max(1, len(idx))


def to_display(text, chars):
    """Voiced text → display text; each mapped span's char times are spread evenly over the same interval."""
    for sp, dp in DISPLAY.items():
        i = text.find(sp)
        while i >= 0:
            seg = chars[i:i + len(sp)] if chars else []
            if seg:
                a, b = seg[0], seg[-1]
                seg = [round(a + (b - a) * k / max(1, len(dp) - 1), 3) for k in range(len(dp))]
                chars = chars[:i] + seg + chars[i + len(sp):]
            text = text[:i] + dp + text[i + len(sp):]
            i = text.find(sp, i + len(dp))
    return text, chars


def score(text, heard):
    n1 = "".join(c for c in text if norm_ch(c)).lower(); n2 = "".join(c for c in heard if norm_ch(c)).lower()
    return difflib.SequenceMatcher(None, n1, n2).ratio()


bad = 0
for sc in tl["scenes"]:
    for line in sc["lines"]:
        if "spoken" in line: line["text"] = line.pop("spoken")   # rerun on an already mapped timeline
        f = os.path.join(PROJ, "audio", line["clip"])
        # pass 1 (QA): plain transcription — word_timestamps makes Whisper hallucinate on trailing silence
        heard = mlx_whisper.transcribe(f, path_or_hf_repo=MODEL, language="zh", initial_prompt=line["text"])["text"]
        if score(line["text"], heard) <= .8:   # Whisper sometimes answers in traditional characters or drifts: retry with a simplified-Chinese prompt
            alt = mlx_whisper.transcribe(f, path_or_hf_repo=MODEL, language="zh", initial_prompt="以下是普通话的句子，使用简体中文。")["text"]
            if score(line["text"], alt) > score(line["text"], heard): heard = alt
        # pass 2 (timing only): word timestamps; hallucinated tail chars simply fail to align with the script
        r = mlx_whisper.transcribe(f, path_or_hf_repo=MODEL, language="zh", initial_prompt=line["text"],
                                   word_timestamps=True, condition_on_previous_text=False)
        words = [w for s in r["segments"] for w in s.get("words", [])]
        # Whisper writes numbers as digits whatever was voiced, so also score against the display form
        ratio = max(score(line["text"], heard), score(to_display(line["text"], [])[0], heard))
        ok = ratio > .8
        bad += not ok
        line["chars"], cover = char_times(line, words) if words else ([], 0)
        line["qa"] = round(ratio, 2)
        print(f"{'OK ' if ok else 'BAD'} {ratio:.2f} align {cover:.0%} | {line['text'][:22]} | {heard[:30]}")
        if re.search(r"\d{3,}", line["text"]):
            print(f"WARN 数字会按数值念（2019 → 两千零一十九）：{line['text'][:30]}  年份/编号写成汉字逐位，并在 script.json 的 display 里映射回数字")
        if not ok: os.rename(f, f + ".bad")
        if DISPLAY: line["spoken"] = line["text"]; line["text"], line["chars"] = to_display(line["text"], line["chars"])

json.dump(tl, open(TL_F, "w"), ensure_ascii=False, indent=1)
open(os.path.join(PROJ, "timeline.js"), "w").write("window.TIMELINE=" + json.dumps(tl, ensure_ascii=False) + ";")
print("bad:", bad)
sys.exit(1 if bad else 0)

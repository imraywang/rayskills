"""Whisper-check every clip against the script, then write per-character timing into the timeline.

usage: python3 qa_tts.py <project_dir>      (run after tts.py)

1. Transcribe each clip with local Whisper (mlx_whisper, word timestamps) and compare with the script line.
   Mismatched clips are renamed *.wav.bad so the next tts.py run re-synthesizes them; exit 1.
2. Align script characters to the heard characters and store line["chars"] = absolute start time of every
   script character (punctuation interpolated). kit at() and grammar cues use it to land on the exact syllable.
"""
import difflib, json, os, re, sys
import mlx_whisper

PROJ = os.path.abspath(sys.argv[1])
TL_F = os.path.join(PROJ, "timeline.json")
tl = json.load(open(TL_F))
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


bad = 0
for sc in tl["scenes"]:
    for line in sc["lines"]:
        f = os.path.join(PROJ, "audio", line["clip"])
        # pass 1 (QA): plain transcription — word_timestamps makes Whisper hallucinate on trailing silence
        heard = mlx_whisper.transcribe(f, path_or_hf_repo=MODEL, language="zh", initial_prompt=line["text"])["text"]
        # pass 2 (timing only): word timestamps; hallucinated tail chars simply fail to align with the script
        r = mlx_whisper.transcribe(f, path_or_hf_repo=MODEL, language="zh", initial_prompt=line["text"],
                                   word_timestamps=True, condition_on_previous_text=False)
        words = [w for s in r["segments"] for w in s.get("words", [])]
        n1 = "".join(c for c in line["text"] if norm_ch(c)).lower(); n2 = "".join(c for c in heard if norm_ch(c)).lower()
        ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
        ok = ratio > .8
        bad += not ok
        line["chars"], cover = char_times(line, words) if words else ([], 0)
        line["qa"] = round(ratio, 2)
        print(f"{'OK ' if ok else 'BAD'} {ratio:.2f} align {cover:.0%} | {line['text'][:22]} | {heard[:30]}")
        if not ok: os.rename(f, f + ".bad")

json.dump(tl, open(TL_F, "w"), ensure_ascii=False, indent=1)
open(os.path.join(PROJ, "timeline.js"), "w").write("window.TIMELINE=" + json.dumps(tl, ensure_ascii=False) + ";")
print("bad:", bad)
sys.exit(1 if bad else 0)

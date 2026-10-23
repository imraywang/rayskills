"""Insert real source-audio clips (interviews, mission audio, archive recordings) into narration.wav.

usage: python3 splice_clips.py <project>        run after tts.py + qa_tts.py (and again after every re-voice)

script.json top level:
  "clips": [{
    "id": "c1", "after": ["<scene id>", <line index>],   # the clip plays right after that narration line
    "src": "clips/c1.wav",                               # 24 kHz mono s16 WAV — cut_clips.py writes it from "cut"
    "speaker": "Reid Wiseman · 指令长", "utc": "2026-04-07 00:41:00 UTC",   # optional labels for the scene
    "segs": [[t, "english", "中文"], ...],              # clip-local seconds: what is said when (scenes type this)
    "caps": [[t, "english", "中文"], ...]               # optional: shorter caption lines (make_beats prefers them)
  }]
Each clip is padded by PAD s of silence on both sides; everything after it shifts later. The voice-only build is kept as
narration.voice.wav / timeline.voice.json so reruns don't stack clips. timeline.json gains a top-level "clips" list
(absolute seconds) that hf/make_beats.py turns into captions and per-scene BEATS[id].clips.
Afterwards: host.py <project> --plan-only (mouth closed during clips), then hf: make_beats.py && build.py.
"""
import json, os, shutil, sys, wave

PROJ = os.path.abspath(sys.argv[1])
RATE, PAD = 24000, 0.45
script = json.load(open(os.path.join(PROJ, "script.json")))
if not script.get("clips"):
    sys.exit("script.json has no \"clips\": nothing to splice")
nar, tlf = os.path.join(PROJ, "narration.wav"), os.path.join(PROJ, "timeline.json")
src_nar, src_tl = os.path.join(PROJ, "narration.voice.wav"), os.path.join(PROJ, "timeline.voice.json")
# keep a pristine copy of the voice-only build; refresh it whenever tts.py produced a newer one
if not os.path.exists(src_tl) or json.load(open(tlf)).get("clips") is None:
    shutil.copy(nar, src_nar); shutil.copy(tlf, src_tl)
tl = json.load(open(src_tl))
with wave.open(src_nar) as w:
    pcm = bytearray(w.readframes(w.getnframes()))


def read_clip(path):
    with wave.open(os.path.join(PROJ, path)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        return w.readframes(w.getnframes())


# insertion points in voice-only time: end of the given line (before its trailing gap)
ins = []
for c in script.get("clips", []):
    sid, li = c["after"]
    sc = next(s for s in tl["scenes"] if s["id"] == sid)
    ins.append((sc["lines"][li]["end"], c))
ins.sort(key=lambda x: x[0])

out, shift, cursor, placed = bytearray(), 0.0, 0, []
silence = lambda sec: b"\0\0" * int(round(sec * RATE))
for t0, c in ins:
    cut = int(round(t0 * RATE)) * 2
    out += pcm[cursor:cut]; cursor = cut
    data = read_clip(c["src"]); dur = len(data) / 2 / RATE
    out += silence(PAD)
    start = len(out) / 2 / RATE                     # from the real sample count, so no rounding drift
    out += data + silence(PAD)
    placed.append({"id": c["id"], "start": round(start, 3), "end": round(start + dur, 3), "speaker": c.get("speaker", ""),
                   "utc": c.get("utc", ""), "segs": [[round(start + s, 3), en, zh] for s, en, zh in c["segs"]], "at_voice": t0})
    shift += dur + 2 * PAD
out += pcm[cursor:]


def shifted(t, start=False):
    # a start that sits exactly on an insertion point belongs after the clip (continuous recordings have no gap
    # between lines, so the next line starts at the very time the previous one ends); an end there stays before it
    eps = -1e-6 if start else 1e-6
    return round(t + sum(p["end"] - p["start"] + 2 * PAD for p in placed if p["at_voice"] <= t - eps), 3)


for sc in tl["scenes"]:
    sc["start"], sc["end"] = shifted(sc["start"], True), shifted(sc["end"])
    for ln in sc["lines"]:
        ln["start"], ln["end"] = shifted(ln["start"], True), shifted(ln["end"])
        if "chars" in ln: ln["chars"] = [shifted(x, True) for x in ln["chars"]]
# a scene that contains a clip must stretch to cover it
for p in placed:
    for sc in tl["scenes"]:
        if sc["start"] <= p["start"] <= sc["end"] + 2 * PAD + (p["end"] - p["start"]):
            if any(abs(ln["end"] - (p["start"] - PAD)) < 1e-3 for ln in sc["lines"]):
                sc["end"] = max(sc["end"], round(p["end"] + PAD, 3))
    p.pop("at_voice")
tl["duration"] = round(len(out) / 2 / RATE, 3)
tl["clips"] = placed

with wave.open(nar, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(bytes(out))
json.dump(tl, open(tlf, "w"), ensure_ascii=False, indent=1)
open(os.path.join(PROJ, "timeline.js"), "w").write("window.TIMELINE=" + json.dumps(tl, ensure_ascii=False) + ";")
print(f"spliced {len(placed)} clips, total {tl['duration']:.1f}s")
for p in placed: print(f"  {p['id']} {p['start']:7.2f} → {p['end']:7.2f}  {p['speaker']}")
for s in tl["scenes"]: print(f"  {s['id']:10s} {s['start']:7.2f} → {s['end']:7.2f}")

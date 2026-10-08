"""Synthesize every script line with Gemini TTS, concat into narration.wav, write timeline.json/js.

usage: python3 tts.py <project_dir>
Needs GEMINI_API_KEY. Clips are cached by (model, voice, text) in <project>/audio/, so editing one
line only re-synthesizes that line. Token usage per clip is kept in audio/usage.json for cost.py.

Gemini TTS reads ANY text you send aloud — including "say this in a cheerful tone:" style
instructions, in Chinese or English. Send only the spoken line.
"""
import array, base64, hashlib, json, os, sys, time, urllib.request, wave
from concurrent.futures import ThreadPoolExecutor

PROJ = os.path.abspath(sys.argv[1])
script = json.load(open(os.path.join(PROJ, "script.json")))
MODEL = script.get("tts_model", "gemini-3.8-flash-tts")
VOICE = script.get("voice", "Charon")
LEAD, LINE_GAP, SCENE_GAP, TAIL = (script.get("gaps") or {}).get("lead", .6), (script.get("gaps") or {}).get("line", .32), (script.get("gaps") or {}).get("scene", .8), (script.get("gaps") or {}).get("tail", 1.6)
RATE = 24000
KEY = os.environ.get("GEMINI_API_KEY") or sys.exit("GEMINI_API_KEY not set")
AUDIO = os.path.join(PROJ, "audio"); os.makedirs(AUDIO, exist_ok=True)
USAGE_F = os.path.join(AUDIO, "usage.json")
usage = json.load(open(USAGE_F)) if os.path.exists(USAGE_F) else {}
if script.get("style"):
    print("WARN: script.json 'style' is ignored — Gemini TTS would read it aloud.", file=sys.stderr)


def clip_path(text):
    return os.path.join(AUDIO, hashlib.sha1(f"{MODEL}|{VOICE}|{text}".encode()).hexdigest()[:16] + ".wav")


def synth(text):
    out = clip_path(text)
    if os.path.exists(out):
        return out
    body = json.dumps({"contents": [{"parts": [{"text": text}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                           "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    for attempt in range(8):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"}), timeout=120))
            open(out, "wb").write(base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]))
            u = d.get("usageMetadata", {})
            usage[os.path.basename(out)] = {"model": MODEL, "in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0)}
            return out
        except Exception as e:  # 429s are common on low tiers: back off and keep going
            print(f"retry {attempt} [{text[:12]}] {e}", file=sys.stderr)
            time.sleep(20 * (attempt + 1))
    raise RuntimeError("TTS failed: " + text)


def pcm(path):
    with wave.open(path) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1, path
        return w.readframes(w.getnframes())


def trim(raw, thresh=300):
    a = array.array("h", raw); s, e = 0, len(a)
    while s < e and abs(a[s]) < thresh: s += 1
    while e > s and abs(a[e - 1]) < thresh: e -= 1
    pad = int(.04 * RATE)
    return a[max(0, s - pad):min(len(a), e + pad)].tobytes()


lines = [l for sc in script["scenes"] for l in sc["lines"]]
with ThreadPoolExecutor(2) as ex:
    paths = dict(zip(lines, ex.map(synth, lines)))
json.dump(usage, open(USAGE_F, "w"), indent=1)

silence = lambda sec: b"\0\0" * int(sec * RATE)
buf, t, timeline = bytearray(silence(LEAD)), LEAD, []
for si, sc in enumerate(script["scenes"]):
    scene = {"id": sc["id"], "start": round(t, 3), "lines": []}
    for li, text in enumerate(sc["lines"]):
        clip = trim(pcm(paths[text])); dur = len(clip) / 2 / RATE
        scene["lines"].append({"text": text, "start": round(t, 3), "end": round(t + dur, 3)})
        buf += clip; t += dur
        gap = LINE_GAP if li < len(sc["lines"]) - 1 else (SCENE_GAP if si < len(script["scenes"]) - 1 else TAIL)
        buf += silence(gap); t += gap
    scene["end"] = round(t, 3); timeline.append(scene)

with wave.open(os.path.join(PROJ, "narration.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(bytes(buf))
tl = {"duration": round(t, 3), "scenes": timeline}
json.dump(tl, open(os.path.join(PROJ, "timeline.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(PROJ, "timeline.js"), "w").write("window.TIMELINE=" + json.dumps(tl, ensure_ascii=False) + ";")
print(f"total {t:.1f}s")
for s in timeline:
    print(f"  {s['id']:12s} {s['start']:6.1f} → {s['end']:6.1f}")
for sc in script["scenes"]:  # flag lines whose speech rate looks off (instruction read aloud, long pauses)
    for l in next(x for x in timeline if x["id"] == sc["id"])["lines"]:
        rate = len(l["text"]) / max(.1, l["end"] - l["start"])
        if rate < 2.0: print(f"  SLOW {rate:.1f}字/s: {l['text'][:24]}")

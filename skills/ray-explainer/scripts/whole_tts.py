#!/usr/bin/env python3
"""Read every scene in ONE MiniMax request (Ray 2026-10-23: chill, like telling a friend a story; per-line requests
sound like isolated readings), join the scenes into raw/whole.wav, and cut it into per-line takes for tts.py's
continuous-recording mode. Cuts go in the longest pause between two lines (Whisper words aligned by toneless pinyin),
so the natural pauses stay and no gaps are added.

usage: python3 whole_tts.py <project> [--speed 1.0] [--eleven <voice_id> <model_id>] [--one] [--tag "[...]"]
       then: tts.py --allow-readings → qa_tts.py → splice_clips.py
  --one   the whole script in ONE request (Eleven v4 takes 10,000 chars; a ~6 min script is ~2,100); lines are still cut
          by Whisper + pinyin alignment, scene gaps are the voice's own pauses. Ray chose this for 国内AI产业链 (2026-10-25).
  --tag   a delivery direction prepended to the text; Eleven v4 follows it and does not read it aloud. Eleven v4 IGNORES
          voice_settings.speed (0.8–1.2 all came out the same length); "[fast-paced, crisp tech news anchor]" read ~9% faster.
Per-scene reads are cached in raw/scenes/<id>.<hash>.wav; change a line and only that scene is re-read
(with --one any change re-reads everything: ~1 credit per character on Eleven v4)."""
import hashlib, json, os, re, subprocess, sys
from difflib import SequenceMatcher
import wave
import numpy as np


class sf:
    @staticmethod
    def read(path):
        with wave.open(path) as w: return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768, w.getframerate()

    @staticmethod
    def write(path, x, rate, subtype=None):
        with wave.open(path, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
from pypinyin import lazy_pinyin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minimax_api

PROJ = os.path.abspath(sys.argv[1])
SPEED = float(sys.argv[sys.argv.index("--speed") + 1]) if "--speed" in sys.argv else 1.0
# --eleven <voice_id> <model_id>: read with ElevenLabs instead of MiniMax (Ray 2026-10-24: Eleven v4 beats MiniMax for his clone)
ELEVEN = tuple(sys.argv[sys.argv.index("--eleven") + 1:sys.argv.index("--eleven") + 3]) if "--eleven" in sys.argv else None
# --one: the whole script in ONE request (Ray 2026-10-25); --tag "[...]": delivery direction v4 follows but doesn't read aloud
ONE = "--one" in sys.argv
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
SP = os.path.join(PROJ, "script.json"); script = json.load(open(SP))
V = json.load(open(os.path.expanduser("~/.config/ray-explainer/voices.json")))[script.get("voice", "ray")]
RATE, LEAD, SCENE_GAP, TAIL = 24000, 0.4, 0.8, 1.6
HAN = re.compile(r"[一-鿿]")
os.makedirs(os.path.join(PROJ, "raw/scenes"), exist_ok=True)


def eleven_tts(text):
    import urllib.request
    key = os.environ["ELEVENLABS_API_KEY"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN[0]}?output_format=mp3_44100_128"
    req = urllib.request.Request(url, data=json.dumps({"text": (TAG + " " + text) if TAG else text, "model_id": ELEVEN[1]}).encode(),
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    for k in range(4):
        try: return urllib.request.urlopen(req, timeout=300).read()
        except Exception as e:
            print("  retry", k, e, flush=True); import time; time.sleep(5 * (k + 1))
    raise SystemExit("elevenlabs failed")


def read_scene(sc):
    text = sc.get("text") or "".join(sc["lines"])
    vid = f"eleven|{ELEVEN[0]}|{ELEVEN[1]}|{TAG}" if ELEVEN else f"{V['voice_id']}|{V.get('model')}|{SPEED}"
    h = hashlib.sha1(f"{vid}|{text}".encode()).hexdigest()[:10]
    out = os.path.join(PROJ, f"raw/scenes/{sc['id']}.{h}.wav")
    if not os.path.exists(out):
        mp3 = eleven_tts(text) if ELEVEN else minimax_api.tts(text, V["voice_id"], V.get("model", "speech-2.8-hd"), SPEED, None)[0]
        tmp = out + ".mp3"; open(tmp, "wb").write(mp3)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", out], check=True)
        os.unlink(tmp); print("read", sc["id"], flush=True)
    x, _ = sf.read(out)
    return x


def pauses(x):
    hop = int(.01 * RATE); fr = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same")[::hop])
    q = fr < 10 ** (-42 / 20); out, i = [], 0
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]: j += 1
            if j - i >= 8: out.append((i * .01, j * .01))
            i = j
        else: i += 1
    return out


def edges(x, lines):
    import mlx_whisper
    tmp = os.path.join(PROJ, "raw/scenes/_w.wav"); sf.write(tmp, x, RATE, subtype="PCM_16")
    r = mlx_whisper.transcribe(tmp, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="zh", word_timestamps=True,
                               initial_prompt="以下是普通话的句子，使用简体中文。")
    hyp, ht = [], []
    for s in r["segments"]:
        for w in s.get("words", []):
            cs = HAN.findall(w["word"])
            for i, c in enumerate(cs):
                hyp.append(c); ht.append((w["start"] + (w["end"] - w["start"]) * i / len(cs), w["start"] + (w["end"] - w["start"]) * (i + 1) / len(cs)))
    ref, owner = [], []
    for k, l in enumerate(lines):
        for c in HAN.findall(l): ref.append(c); owner.append(k)
    when = [None] * len(ref)
    for a, b, n in SequenceMatcher(None, lazy_pinyin(ref), lazy_pinyin(hyp), autojunk=False).get_matching_blocks():
        for i in range(n): when[a + i] = ht[b + i]
    P = pauses(x); cuts = []
    for k in range(len(lines) - 1):
        end = max((when[i][1] for i in range(len(ref)) if owner[i] == k and when[i]), default=None)
        nxt = min((when[i][0] for i in range(len(ref)) if owner[i] == k + 1 and when[i]), default=None)
        if end is None or nxt is None: raise SystemExit(f"cannot align line {k}/{k + 1}: {lines[k]} | {lines[k + 1]}")
        inside = [p for p in P if p[1] > end - .15 and p[0] < nxt + .15]
        if inside: p = max(inside, key=lambda p: p[1] - p[0]); cuts.append(round((p[0] + p[1]) / 2, 3))
        else: cuts.append(round((end + nxt) / 2, 3)); print("  no pause between", repr(lines[k][-8:]), repr(lines[k + 1][:8]))
    return cuts


parts, takes, t = [np.zeros(int(LEAD * RATE))], {}, 0.0
scenes = script["scenes"]
if ONE:
    x = read_scene({"id": "all", "text": "\n\n".join("".join(sc["lines"]) for sc in scenes)})
    keys = [f"{sc['id']}.{li}" for sc in scenes for li in range(len(sc["lines"]))]
    cuts = edges(x, [l for sc in scenes for l in sc["lines"]])
    bounds = [0.0] + [LEAD + c for c in cuts] + [LEAD + len(x) / RATE + TAIL]
    for k, key in enumerate(keys): takes[key] = [[round(bounds[k], 3), round(bounds[k + 1], 3)]]
    parts += [x, np.zeros(int(TAIL * RATE))]
else:
    for si, sc in enumerate(scenes):
        x = read_scene(sc)
        cuts = edges(x, sc["lines"])
        start = t if si else 0.0   # first take carries the lead-in
        seg_t = t + (LEAD if si == 0 else 0)
        bounds = [start] + [seg_t + c for c in cuts]
        gap = SCENE_GAP if si < len(scenes) - 1 else TAIL
        end = seg_t + len(x) / RATE + gap
        bounds.append(end)
        for li in range(len(sc["lines"])): takes[f"{sc['id']}.{li}"] = [[round(bounds[li], 3), round(bounds[li + 1], 3)]]
        parts += [x, np.zeros(int(gap * RATE))]
        t = end
whole = np.concatenate(parts)
sf.write(os.path.join(PROJ, "raw/whole.wav"), whole, RATE, subtype="PCM_16")
script["recording"] = {"src": os.path.join(PROJ, "raw/whole.wav"), "continuous": True, "takes": takes, "made_by": f"whole_tts.py ({'ElevenLabs ' + ELEVEN[1] if ELEVEN else 'MiniMax'}, " + ("one request" if ONE else "one request per scene") + ")"}
script["speed"] = SPEED
json.dump(script, open(SP, "w"), ensure_ascii=False, indent=2); open(SP, "a").write("\n")
print(f"whole.wav {len(whole) / RATE:.1f}s, {len(takes)} takes → script.json recording")

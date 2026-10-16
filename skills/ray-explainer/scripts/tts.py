"""Synthesize every script line, concat into narration.wav, write timeline.json/js.

usage: python3 tts.py <project_dir>

Voice is chosen by script.json "voice":
  - a name registered in ~/.config/ray-explainer/voices.json (clone_voice.py writes it) → that provider,
    e.g. MiniMax speech-2.8-hd with Ray's cloned voice_id (direct MiniMax API via minimax_api.py; a model
    starting with "fal-ai/" means a voice cloned through fal — fal-hosted only), or provider "voxcpm2": local VoxCPM2
    (MLX) cloning from a reference clip, run through voxcpm_worker.py in its own venv
  - otherwise a Gemini prebuilt voice name (Charon / Puck / Kore …)

Clips are cached by (provider, model, voice, speed, text) in <project>/audio/, so editing one line only
re-synthesizes that line. Per-clip usage goes to audio/usage.json for cost.py.

narration.wav is gain-matched (one linear gain, no compression, peak-limited) to script.json "loudness", default
−21 LUFS: the level of the MiniMax narration Ray approved against source clips cut at −17 (cut_clips.py). Every voice
lands there — local VoxCPM2 came out 7 dB hotter and drowned the clips before this existed.

Gemini TTS reads ANY text you send aloud — including "say this in a cheerful tone:" style
instructions, in Chinese or English. Send only the spoken line.
"""
import array, base64, math, datetime, hashlib, json, os, subprocess, sys, tempfile, time, urllib.request, wave
from concurrent.futures import ThreadPoolExecutor

PROJ = os.path.abspath(sys.argv[1])
script = json.load(open(os.path.join(PROJ, "script.json")))
RATE = 24000
gaps = script.get("gaps") or {}
LEAD, LINE_GAP, SCENE_GAP, TAIL = gaps.get("lead", .6), gaps.get("line", .32), gaps.get("scene", .8), gaps.get("tail", 1.6)
CONTINUOUS = bool((script.get("recording") or {}).get("continuous"))   # Ray's own edit is the soundtrack: lines tile it back to back, no gaps, no trimming
if CONTINUOUS: LEAD = LINE_GAP = SCENE_GAP = 0
VOICES_F = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "ray-explainer", "voices.json")
voices = json.load(open(VOICES_F)) if os.path.exists(VOICES_F) else {}
VOICE = script.get("voice", "Charon")
SPEED = float(script.get("speed", 1.0))
REC = script.get("recording")   # Ray's own recording as the voice: {"src": <video/audio>, "takes": {"<scene>.<line>": [[a, b], ...]}}
if REC:
    V = {"provider": "recorded", "model": "take", "voice_id": os.path.basename(REC["src"])}
elif VOICE in voices:
    V = {"provider": "minimax", **voices[VOICE]}
else:
    V = {"provider": "gemini", "voice_id": VOICE, "model": script.get("tts_model", "gemini-3.8-flash-tts")}
PROVIDER, MODEL, VOICE_ID = V["provider"], V["model"], V["voice_id"]
AUDIO = os.path.join(PROJ, "audio"); os.makedirs(AUDIO, exist_ok=True)
USAGE_F = os.path.join(AUDIO, "usage.json")
usage = json.load(open(USAGE_F)) if os.path.exists(USAGE_F) else {}
if script.get("style"):
    print("WARN: script.json 'style' is ignored — TTS would read it aloud.", file=sys.stderr)
if not REC:   # catch a16z / 23% / 2019 before paying for them; --allow-readings once the readings are known to be fine
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lint_readings
    _bad = lint_readings.lint(script)
    lint_readings.report(_bad, sys.stderr)
    if _bad and "--allow-readings" not in sys.argv:
        sys.exit("改稿后重跑；确认这些读法没问题就加 --allow-readings")


def zshrc_env(name):
    if os.environ.get(name): return os.environ[name]
    try:
        for line in open(os.path.expanduser("~/.zshrc")):
            line = line.strip()
            if line.startswith(f"export {name}="): return line.split("=", 1)[1].strip().strip('"\'')
    except OSError: pass
    sys.exit(f"{name} not set")


TAKES = {t: REC["takes"][f"{sc['id']}.{i}"] for sc in script["scenes"] for i, t in enumerate(sc["lines"])} if REC else {}


def cut_take(text, out):
    """Cut a line from the recording: its segments in order, 20 ms fades at each join, 24 kHz mono."""
    segs = TAKES[text]
    fade = lambda a, b: f",afade=t=in:d=0.02,afade=t=out:st={b - a - 0.02:.3f}:d=0.02" if len(segs) > 1 else ""   # one segment = a sample-exact slice, so back-to-back lines rejoin seamlessly
    f = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS{fade(a, b)}[s{i}];" for i, (a, b) in enumerate(segs))
    f += "".join(f"[s{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[o]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", REC["src"], "-filter_complex", f, "-map", "[o]", "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", out], check=True)
    return {"chars": 0}


def clip_key(text):
    if PROVIDER == "recorded": return hashlib.sha1(f"recorded|{REC['src']}|{TAKES[text]}|{text}".encode()).hexdigest()[:16]
    # Gemini at speed 1.0 keeps the original key format so existing caches stay valid
    tag = f"{MODEL}|{VOICE_ID}|{text}" if PROVIDER == "gemini" and SPEED == 1.0 else f"{PROVIDER}|{MODEL}|{VOICE_ID}|{SPEED}|{text}"
    return hashlib.sha1(tag.encode()).hexdigest()[:16]


def to_wav24k(src_bytes, out):
    """Any audio bytes → 24 kHz mono s16 WAV (ffmpeg), so every provider yields the same clip format."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f: f.write(src_bytes); tmp = f.name
    try: subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", out], check=True)
    finally: os.unlink(tmp)


def synth_gemini(text, out):
    key = zshrc_env("GEMINI_API_KEY")
    body = json.dumps({"contents": [{"parts": [{"text": text}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                           "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE_ID}}}}}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}"
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"}), timeout=120))
    to_wav24k(base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]), out)
    u = d.get("usageMetadata", {})
    return {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0)}


def synth_minimax(text, out):
    if not MODEL.startswith("fal-ai/"):   # direct MiniMax API
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import minimax_api
        mp3, info = minimax_api.tts(text, VOICE_ID, MODEL, SPEED, V.get("emotion"))
        to_wav24k(mp3, out)
        return {"chars": info.get("usage_characters", len(text)), "ms": info.get("audio_length", 0)}
    # legacy: voice cloned through fal lives in fal's MiniMax account, so it can only be used via fal
    os.environ["FAL_KEY"] = zshrc_env("FAL_KEY")
    import fal_client
    vs = {"voice_id": VOICE_ID, "speed": SPEED, "vol": 1, "pitch": 0}
    if V.get("emotion"): vs["emotion"] = V["emotion"]
    r = fal_client.subscribe(MODEL, arguments={"prompt": text, "voice_setting": vs, "language_boost": "Chinese",
                                               "audio_setting": {"format": "mp3", "sample_rate": 32000, "channel": 1}, "output_format": "url"})
    to_wav24k(urllib.request.urlopen(r["audio"]["url"], timeout=120).read(), out)
    return {"chars": len(text), "ms": r.get("duration_ms", 0)}


def synth_voxcpm_batch(texts):
    """Local VoxCPM2: one worker process loads the model once and synthesizes every uncached line (best of N takes)."""
    todo = [{"text": t, "out": os.path.join(AUDIO, clip_key(t) + ".wav")} for t in dict.fromkeys(texts)]
    todo = [it for it in todo if not os.path.exists(it["out"])]
    if not todo: return
    py = os.path.expanduser(V.get("python", "~/.local/share/ray-explainer/voxcpm-env/bin/python"))
    job = {"model": MODEL, "ref": os.path.expanduser(V["ref"]), "cfg": V.get("cfg", 3.0), "steps": V.get("steps", 10),
           "takes": V.get("takes", 3), "max_takes": V.get("max_takes", 6), "rate": RATE, "speed": round(SPEED / V.get("native_speed", 1.0), 3), "items": todo}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(job, f, ensure_ascii=False); jf = f.name
    print(f"VoxCPM2 local: {len(todo)} lines × up to {job['takes']} takes (≈{sum(len(it['text']) for it in todo) * .5 / 60:.0f} min on M4 Pro)")
    try:
        p = subprocess.Popen([py, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "voxcpm_worker.py"), jf],
                             stdout=subprocess.PIPE, text=True)
        for line in p.stdout:
            r = json.loads(line); usage[os.path.basename(r["out"])] = {"provider": PROVIDER, "model": MODEL, "chars": len(next(it["text"] for it in todo if it["out"] == r["out"])), "takes": r["takes"]}
            print(f"  {r['score']:.2f} ×{r['takes']} {r['wall']:5.1f}s  {os.path.basename(r['out'])}")
        if p.wait(): sys.exit("voxcpm_worker failed (see stderr above)")
    finally: os.unlink(jf)


def synth(text):
    out = os.path.join(AUDIO, clip_key(text) + ".wav")
    if os.path.exists(out):
        return out
    if PROVIDER == "voxcpm2":
        raise RuntimeError("VoxCPM2 clip missing after batch: " + text)
    if PROVIDER == "recorded":
        cut_take(text, out); return out
    for attempt in range(8):
        try:
            u = (synth_minimax if PROVIDER == "minimax" else synth_gemini)(text, out)
            usage[os.path.basename(out)] = {"provider": PROVIDER, "model": MODEL, **u}
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
    """Strip leading/trailing near-silence; return (pcm, seconds cut from the start) so word times can be shifted."""
    a = array.array("h", raw); s, e = 0, len(a)
    while s < e and abs(a[s]) < thresh: s += 1
    while e > s and abs(a[e - 1]) < thresh: e -= 1
    pad = int(.04 * RATE); s0 = max(0, s - pad)
    return a[s0:min(len(a), e + pad)].tobytes(), s0 / RATE


lines = [l for sc in script["scenes"] for l in sc["lines"]]
if PROVIDER == "voxcpm2": synth_voxcpm_batch(lines)
with ThreadPoolExecutor(2 if PROVIDER == "gemini" else 4) as ex:
    paths = dict(zip(lines, ex.map(synth, lines)))
json.dump(usage, open(USAGE_F, "w"), indent=1)
if PROVIDER == "minimax" and VOICE in voices:  # record use: MiniMax drops clones unused for 7 days after creation
    voices[VOICE]["last_used"] = datetime.date.today().isoformat(); json.dump(voices, open(VOICES_F, "w"), ensure_ascii=False, indent=1)

silence = lambda sec: b"\0\0" * int(sec * RATE)
buf, t, timeline = bytearray(silence(LEAD)), LEAD, []
for si, sc in enumerate(script["scenes"]):
    scene = {"id": sc["id"], "start": round(t, 3), "lines": []}
    if sc.get("grammar"): scene["grammar"] = sc["grammar"]
    for li, text in enumerate(sc["lines"]):
        clip, cut = (pcm(paths[text]), 0.0) if CONTINUOUS else trim(pcm(paths[text])); dur = len(clip) / 2 / RATE
        scene["lines"].append({"text": text, "start": round(t, 3), "end": round(t + dur, 3), "clip": os.path.basename(paths[text]), "cut": round(cut, 3)})
        buf += clip; t += dur
        gap = LINE_GAP if li < len(sc["lines"]) - 1 else (SCENE_GAP if si < len(script["scenes"]) - 1 else TAIL)
        buf += silence(gap); t += gap
    scene["end"] = round(t, 3); timeline.append(scene)



def lufs(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    vals = [float(l.split()[1]) for l in r.splitlines() if l.strip().startswith("I:") and "LUFS" in l]
    return vals[-1] if vals else None


def write_wav(path, data):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(bytes(data))


NAR = os.path.join(PROJ, "narration.wav")
write_wav(NAR, buf)
target = float(script.get("loudness", -21.0))
cur = lufs(NAR)
if cur is not None and abs(cur - target) > 0.3:
    a = array.array("h", bytes(buf)); peak = max(1, max(abs(min(a)), max(a)))
    g = 10 ** ((target - cur) / 20)
    if peak * g > 0.95 * 32767:
        g = 0.95 * 32767 / peak
        if target - (cur + 20 * math.log10(g)) > 1: print(f"WARN: peaks limit the gain — narration ends at {cur + 20 * math.log10(g):.1f} LUFS, not {target:.1f}")
    a = array.array("h", (int(round(s * g)) for s in a)); write_wav(NAR, a)
    print(f"loudness {cur:.1f} → {cur + 20 * math.log10(g):.1f} LUFS (target {target:.0f})")
tl = {"duration": round(t, 3), "voice": VOICE, "provider": PROVIDER, "scenes": timeline}
json.dump(tl, open(os.path.join(PROJ, "timeline.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(PROJ, "timeline.js"), "w").write("window.TIMELINE=" + json.dumps(tl, ensure_ascii=False) + ";")
print(f"voice {VOICE} ({PROVIDER} · {MODEL})  total {t:.1f}s")
for s in timeline:
    print(f"  {s['id']:12s} {s['start']:6.1f} → {s['end']:6.1f}  {s.get('grammar', 'kit')}")
for s in timeline:  # flag lines whose speech rate looks off (instruction read aloud, long pauses)
    for l in s["lines"]:
        rate = len(l["text"]) / max(.1, l["end"] - l["start"])
        if rate < 2.0: print(f"  SLOW {rate:.1f}字/s: {l['text'][:24]}")
print("next: python3 qa_tts.py <project>  (Whisper check + per-character timing)")

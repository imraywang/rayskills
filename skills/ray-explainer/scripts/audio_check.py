"""Listening check for a finished video: does the music actually come through, do clips stay clean, are sfx sparse?

usage: python3 audio_check.py <project> [video.mp4]      (default out.mp4; stdlib only, needs ffmpeg)

Reports, from timeline.json + the rendered audio:
  - voice level (median RMS over narration lines) vs music level in the narration gaps (≥ 0.4 s, clips excluded)
      gap − voice < −32 dB → music practically inaudible;  > −8 dB → music competes with the voice
  - music under each source clip (from hf/assets/audio/bgm.m4a × nothing else): should be ≤ −45 dBFS for clips meant
    to be silent and well under the clip itself otherwise
  - sfx count in hf/index.html (Ray's preference: a dozen or so for the whole film, only key moments)
Exit code 1 when something is out of range, so it can gate a render. It only measures; listening is still Ray's call.
"""
import array, json, math, os, re, statistics, subprocess, sys, tempfile, wave

PROJ = os.path.abspath(sys.argv[1]); VIDEO = os.path.join(PROJ, sys.argv[2] if len(sys.argv) > 2 else "out.mp4")
TL = json.load(open(os.path.join(PROJ, "timeline.json")))
RATE, bad = 16000, []


def load(path):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: tmp = f.name
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", tmp], check=True)
    with wave.open(tmp) as w: a = array.array("h", w.readframes(w.getnframes()))
    os.unlink(tmp); return a


def db(a, t0, t1):
    seg = a[int(t0 * RATE): int(t1 * RATE)]
    if len(seg) < RATE // 20: return None
    r = math.sqrt(sum(v * v for v in seg[::4]) / len(seg[::4])) / 32768
    return 20 * math.log10(r + 1e-9)


mix = load(VIDEO)
clips = TL.get("clips", [])
in_clip = lambda a, b: any(a < c["end"] + 0.3 and b > c["start"] - 0.3 for c in clips)
lines = [l for s in TL["scenes"] for l in s["lines"]]
voice = [d for l in lines if (d := db(mix, l["start"] + 0.1, l["end"] - 0.1)) is not None]
gaps = []
for l, n in zip(lines, lines[1:]):
    a, b = l["end"] + 0.12, n["start"] - 0.12
    if b - a >= 0.35 and not in_clip(a, b) and (d := db(mix, a, b)) is not None: gaps.append(d)
v, g = statistics.median(voice), (statistics.median(gaps) if gaps else None)
print(f"voice  median {v:6.1f} dBFS over {len(voice)} lines")
if g is None: print("gaps   none long enough to measure")
else:
    diff = g - v; verdict = "OK" if -32 <= diff <= -8 else ("TOO QUIET — music practically inaudible" if diff < -32 else "TOO LOUD — competes with the voice")
    print(f"music  in gaps {g:6.1f} dBFS  ({diff:+.1f} dB vs voice, {len(gaps)} gaps)  {verdict}")
    if verdict != "OK": bad.append("music level")

bgmf = os.path.join(PROJ, "hf", "assets", "audio", "bgm.m4a")
if clips and os.path.exists(bgmf):
    bgm = load(bgmf)
    for c in clips:
        m, cl = db(bgm, c["start"], c["end"]), db(mix, c["start"], c["end"])
        print(f"clip   {c['id']:4s} {c['start']:6.1f}–{c['end']:6.1f}s  clip {cl:6.1f} dBFS · music file under it {m:6.1f} dBFS")
elif clips: print("clip   (no hf/assets/audio/bgm.m4a — nothing under the clips)")

idx = os.path.join(PROJ, "hf", "index.html")
if os.path.exists(idx):
    names = re.findall(r'id="sfx\d+" src="assets/audio/([\w-]+)\.mp3"', open(idx).read())
    from collections import Counter
    print(f"sfx    {len(names)} cues  {dict(Counter(names).most_common(6))}" + ("  TOO MANY (>15)" if len(names) > 15 else ""))
    if len(names) > 15: bad.append("sfx count")
print("audio_check: " + ("OK" if not bad else "CHECK " + ", ".join(bad)))
sys.exit(1 if bad else 0)

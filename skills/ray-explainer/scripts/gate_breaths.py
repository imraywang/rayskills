"""Silence the inhale breaths between phrases in a recording of Ray talking. Timing is unchanged (nothing is cut out).

usage:
  python3 gate_breaths.py <video-or-audio> -o voice.wav            # writes the cleaned track + voice.cuts.json
  python3 gate_breaths.py <video-or-audio> -o voice.wav --verify   # also re-transcribes both and prints any word change

How a breath is found (tuned on Ray's 2026-10-20 course recording, 27 breaths / 7.4 s in 190 s):
  - 10 ms frames; a breath frame is noisy (zero-crossing >= 0.08), centred around 2.4–4.8 kHz, between -52 and -14 dBFS
  - a run of >= 120 ms such frames, with a pause (<= -24 dBFS) just before it -> an inhale between phrases.
    Runs without that pause are fricatives inside a word (sh/f/z) and are left alone.
  - the gate stops 30 ms before the next word's onset: first frame louder than -20 dBFS that is either voiced
    (zero-crossing < 0.07) or a fricative (centroid > 4.8 kHz), so 所以 / 先 / 从 / 前 / 写 keep their first consonant.
  - each breath is pulled down to -45 dB with 20 ms fades on both sides.
Output is 48 kHz stereo WAV, same length as the input. Use it in place of the footage's own sound
(HyperFrames: make the A-roll <video> muted and add <audio id="voice" src="voice.wav" ...> on the same timing).
"""
import argparse, difflib, json, os, subprocess, sys, tempfile, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("-o", "--out", required=True)
ap.add_argument("--floor-db", type=float, default=-45)
ap.add_argument("--verify", action="store_true", help="re-transcribe original and cleaned audio with mlx_whisper and diff")
a = ap.parse_args()

SR, HOP = 48000, 480
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.src, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
if raw.returncode:
    sys.exit(raw.stderr.decode())
st = np.frombuffer(raw.stdout, dtype=np.float32).reshape(-1, 2).copy()
x = st.mean(1)
n = len(x) // HOP
fr = x[:n * HOP].reshape(n, HOP)
rms = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
zcr = (np.abs(np.diff(np.sign(fr), axis=1)) > 0).mean(1)
spec = np.abs(np.fft.rfft(fr * np.hanning(HOP), axis=1))
cen = (spec * np.fft.rfftfreq(HOP, 1 / SR)).sum(1) / (spec.sum(1) + 1e-9)
k = np.ones(3) / 3
rs, zs, cs = (np.convolve(v, k, "same") for v in (rms, zcr, cen))
breathy = (zs >= 0.08) & (cs >= 2400) & (cs <= 4800) & (rs <= -14) & (rs >= -52)
onset = (rms > -20) & ((zcr < 0.07) | (cen > 4800))

cuts, i = [], 0
while i < n:
    if not breathy[i]:
        i += 1
        continue
    j = i
    while j < n and breathy[j]:
        j += 1
    if j - i >= 12 and rms[max(0, i - 8):i].min() <= -24:
        o = i
        while o < n and not onset[o]:
            o += 1
        start, end = i / 100 - 0.03, min(o / 100 - 0.03, j / 100 + 0.05)
        if end - start >= 0.08:
            cuts.append((round(start, 3), round(end, 3)))
    i = j

gain = np.ones(len(st), dtype=np.float32)
floor = 10 ** (a.floor_db / 20)
for s, e in cuts:
    s0, s1 = int(s * SR), int(e * SR)
    r = min(int(0.02 * SR), (s1 - s0) // 2)
    env = np.full(s1 - s0, floor, dtype=np.float32)
    env[:r] = np.linspace(1, floor, r)
    env[-r:] = np.linspace(floor, 1, r)
    gain[s0:s1] = np.minimum(gain[s0:s1], env)
out = st * gain[:, None]
with wave.open(a.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
report = os.path.splitext(a.out)[0] + ".cuts.json"
json.dump({"src": os.path.abspath(a.src), "cuts": cuts}, open(report, "w"), ensure_ascii=False, indent=1)
print(f"{len(cuts)} breaths silenced, {sum(e - s for s, e in cuts):.2f} s total -> {a.out}  (list: {report})")

if a.verify:
    tmp = tempfile.mkdtemp()
    def words(path, name):
        wav16 = os.path.join(tmp, name + ".wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", wav16], check=True)
        subprocess.run(["mlx_whisper", wav16, "--model", "mlx-community/whisper-large-v3-turbo", "--language", "zh",
                        "--output-format", "json", "--output-dir", tmp, "--output-name", name], check=True, capture_output=True)
        d = json.load(open(os.path.join(tmp, name + ".json")))
        return "".join(s["text"] for s in d["segments"])
    import re
    strip = lambda t: re.sub(r"[\s,，。、？?！!：:；;]", "", t)
    ta, tb = strip(words(a.src, "orig")), strip(words(a.out, "clean"))
    sm = difflib.SequenceMatcher(None, ta, tb)
    print(f"verify: text similarity {sm.ratio():.4f} (punctuation ignored)")
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            print(f"  {op}: …{ta[max(0, i1 - 6):i2 + 6]}… -> …{tb[max(0, j1 - 6):j2 + 6]}…")
    print("A dropped or changed syllable next to a cut means the gate clipped a word: check that spot by ear.")

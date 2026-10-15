"""Local VoxCPM2 synthesis for tts.py — runs inside its own MLX venv, never the system python.

usage: <venv>/bin/python -I voxcpm_worker.py <job.json>

job.json: {"model": <dir>, "ref": <wav>, "cfg": 3.0, "steps": 10, "takes": 3, "max_takes": 6, "rate": 24000, "speed": 1.0,
           "items": [{"text": ..., "out": ...}, ...]}

The model is loaded once for the whole batch. Each line is sampled `takes` times (VoxCPM2 output varies
run to run — mostly a mangled English word or a swallowed word or two), every take is transcribed
with Whisper, and the one closest to the script is written to `out` as 24 kHz mono s16 WAV. If even the
best take scores below GOOD, sampling continues up to `max_takes`: qa_tts.py passes anything above .8,
which still lets a dropped 4-character phrase through.
Prints one JSON line per item: {"out", "takes", "score", "wall", "dur"}.
"""
import difflib, json, os, re, subprocess, sys, tempfile, time
import numpy as np, soundfile as sf

job = json.load(open(sys.argv[1]))
if not os.path.isdir(job["model"]):
    sys.exit(f"VoxCPM2 model not found at {job['model']} — is the external drive mounted?")
from mlx_audio.tts.utils import load
import mlx_whisper
from pypinyin import lazy_pinyin

WHISPER = "mlx-community/whisper-large-v3-turbo"
DIG = "零一二三四五六七八九"


def cn_int(n):
    """Integer → spoken Chinese (Whisper writes 十月十二号 as 10月12号; compare both as 十月十二号)."""
    if n == 0 or n >= 10 ** 8: return "".join(DIG[int(c)] for c in str(n))
    out, zero = "", False
    for i, u in ((10 ** 7, "千"), (10 ** 6, "百"), (10 ** 5, "十"), (10 ** 4, "万"), (1000, "千"), (100, "百"), (10, "十"), (1, "")):
        d = n // i % 10
        if d: out += ("零" if zero and out else "") + DIG[d] + u; zero = False
        else: zero = True
        if i == 10 ** 4 and n >= 10 ** 4 and not out.endswith("万"): out += "万"
    return out[1:] if out.startswith("一十") else out


def norm(s):
    """Toneless pinyin of the speakable characters: homophones Whisper mixes up (暴雪/暴血, 捡/剪) don't count as errors."""
    s = re.sub(r"\d+", lambda m: cn_int(int(m.group())), s.lower())
    out = []
    for tok in re.findall(r"[一-鿿]|[a-z]", s):   # hanzi → toneless pinyin, Latin → single letters (joe ≈ jo)
        out += lazy_pinyin(tok) if tok >= "一" else [tok]
    return out


def score(text, wav):
    heard = mlx_whisper.transcribe(wav, path_or_hf_repo=WHISPER, language="zh", initial_prompt="以下是普通话的句子，使用简体中文。")["text"]
    return difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()


model = load(job["model"])
takes = max(1, int(job.get("takes", 3))); max_takes = max(takes, int(job.get("max_takes", 6)))
GOOD = .95
for it in job["items"]:
    t0 = time.perf_counter(); best = None
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(max_takes):
            audio = np.concatenate([np.array(r.audio) for r in model.generate(
                text=it["text"], ref_audio=job["ref"], cfg_value=float(job.get("cfg", 3.0)),
                inference_timesteps=int(job.get("steps", 10)))])
            raw = os.path.join(tmp, f"{k}.wav"); sf.write(raw, audio, model.sample_rate)
            s = score(it["text"], raw)
            if best is None or s > best[0]: best = (s, raw, len(audio) / model.sample_rate)
            if s >= .99 or (k + 1 >= takes and best[0] >= GOOD): break   # perfect early, or good enough after the base takes
        speed = float(job.get("speed", 1.0))   # VoxCPM2 has no speed control: time-stretch after the fact
        af = ["-af", f"atempo={speed}"] if speed != 1.0 else []
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", best[1], *af, "-ac", "1", "-ar", str(job.get("rate", 24000)),
                        "-sample_fmt", "s16", it["out"]], check=True)
    print(json.dumps({"out": it["out"], "takes": k + 1, "score": round(best[0], 3),
                      "wall": round(time.perf_counter() - t0, 1), "dur": round(best[2], 2)}), flush=True)

"""Bake a story-driven volume envelope into the chosen BGM → <project>/hf/assets/audio/bgm.m4a (loudnorm -20 LUFS).

usage: python3 mix_bgm.py <project> <bgm.wav>        (numpy + soundfile; re-execs in the ACE-Step venv if missing)

build.py then plays it at BGM_VOL (default 0.35) and carves it under the narration. Envelope, from script.json
"bgm" (all keys optional) and timeline.json (absolute seconds, after splice_clips.py):
  "silent_clips": ["c1"]          clips where the music drops out completely (the shout lands in silence)
  "duck": 0.12                    level under every other clip (default: all clips not listed as silent)
  "sections": [{"from": "evidence", "to": "doubt", "level": 0.6}, {"from": "confirmed", "to": "end", "level": 1.15}]
                                  scene ranges played quieter / louder than 1.0
  "end_at": {"scene": "end", "line": 0, "phrase": "那一毫秒"}    music fades out from this word to the end
                                  (default: the last 3 s)
"""
import json, os, subprocess, sys

try:
    import numpy as np, soundfile as sf
except ImportError:
    ACE = os.path.expanduser(os.environ.get("ACESTEP_DIR", "~/projects/ACE-Step-1.5"))
    os.execvp("uv", ["uv", "run", "--project", ACE, "python", os.path.abspath(__file__), *sys.argv[1:]])

PROJ, SRC = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
cfg = json.load(open(os.path.join(PROJ, "script.json"))).get("bgm") or {}
TL = json.load(open(os.path.join(PROJ, "timeline.json")))
SC = {s["id"]: s for s in TL["scenes"]}
TOTAL = TL["scenes"][-1]["end"] + 0.4          # same as make_beats.py "total"
x, sr = sf.read(SRC, always_2d=True)
if len(x) < TOTAL * sr: print(f"WARN: bgm {len(x) / sr:.1f}s shorter than film {TOTAL:.1f}s — set BGM_LEN in build.py or regenerate longer")
x = x[: int(TOTAL * sr)]
t = np.arange(len(x)) / sr
env = np.ones(len(x))


def shape(a, b, level, ramp=0.8):
    g = np.ones(len(x)); g[(t >= a) & (t <= b)] = level
    up = (t > a - ramp) & (t < a); g[up] = 1 + (level - 1) * (t[up] - (a - ramp)) / ramp
    dn = (t > b) & (t < b + ramp); g[dn] = level + (1 - level) * (t[dn] - b) / ramp
    return g


silent = set(cfg.get("silent_clips", []))
for c in TL.get("clips", []):
    env *= shape(c["start"] - 0.3, c["end"] + 0.2, 0.0, 0.6) if c["id"] in silent else shape(c["start"] - 0.2, c["end"] + 0.2, cfg.get("duck", 0.12))
for sec in cfg.get("sections", []):
    env *= shape(SC[sec["from"]]["start"], SC[sec["to"]]["end"] if sec["to"] != list(SC)[-1] else TOTAL, sec["level"], 1.5)
ea = cfg.get("end_at")
if ea:
    ln = SC[ea["scene"]]["lines"][ea.get("line", 0)]; i = max(0, ln["text"].find(ea.get("phrase", "")))
    fade_from = ln["chars"][min(i, len(ln["chars"]) - 1)]
else:
    fade_from = TOTAL - 3
fo = t > fade_from; env[fo] *= np.clip(1 - (t[fo] - fade_from) / max(0.5, TOTAL - fade_from - 0.3), 0, 1)
fi = t < 1.2; env[fi] *= t[fi] / 1.2

os.makedirs(os.path.join(PROJ, "bgm"), exist_ok=True)
tmp = os.path.join(PROJ, "bgm", "bgm_mixed.wav"); sf.write(tmp, x * env[:, None], sr)
out = os.path.join(PROJ, "hf", "assets", "audio", "bgm.m4a"); os.makedirs(os.path.dirname(out), exist_ok=True)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-20:TP=-2:LRA=14", "-c:a", "aac", "-b:a", "192k", out], check=True)
print(f"bgm.m4a {len(x) / sr:.1f}s · silent clips {sorted(silent) or '-'} · fades from {fade_from:.1f}s → set BGM_LEN = 0 in build.py, rebuild")

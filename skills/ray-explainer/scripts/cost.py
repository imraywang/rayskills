"""Report TTS usage and cost for a project. usage: python3 cost.py <project_dir>
Prices as listed 2026-10 — re-check before quoting budgets:
  gemini-3.8-flash-tts (standard tier): $0.50/M text-in tokens, $9/M audio-out tokens; free-tier AI Studio keys bill $0
  fal-ai/minimax/speech-2.8-hd: $0.10 per 1000 characters (voice-clone itself: $1.50 once per voice)"""
import json, os, sys
GEMINI = {"gemini-3.8-flash-tts": (0.50, 9.00), "gemini-3.8-flash-lite-tts": (0.25, 4.50)}
MINIMAX = {"fal-ai/minimax/speech-2.8-hd": 0.10, "fal-ai/minimax/speech-2.8-turbo": 0.06}
f = os.path.join(sys.argv[1], "audio", "usage.json")
if not os.path.exists(f): sys.exit("no audio/usage.json — clips were cached or made outside tts.py")
u = json.load(open(f))
if not u: sys.exit("usage.json is empty")
total = 0.0
g = [v for v in u.values() if v.get("provider", "gemini") == "gemini"]
if g:
    tin = sum(v.get("in", 0) for v in g); tout = sum(v.get("out", 0) for v in g)
    pi, po = GEMINI.get(g[0]["model"], GEMINI["gemini-3.8-flash-tts"]); c = tin * pi / 1e6 + tout * po / 1e6; total += c
    print(f"Gemini TTS  calls {len(g)}  text-in {tin} tok  audio-out {tout} tok (~{tout/25:.0f}s)  ≈ ${c:.3f} (standard tier; $0 on free tier)")
m = [v for v in u.values() if v.get("provider") == "minimax"]
if m:
    ch = sum(v.get("chars", 0) for v in m); sec = sum(v.get("ms", 0) for v in m) / 1000
    c = ch / 1000 * MINIMAX.get(m[0]["model"], 0.10); total += c
    print(f"MiniMax TTS calls {len(m)}  {ch} chars (~{sec:.0f}s)  ≈ ${c:.3f}")
print(f"TTS total ≈ ${total:.3f}  (includes re-synthesized clips; cached clips cost nothing)")

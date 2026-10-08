"""Report TTS token usage and cost for a project. usage: python3 cost.py <project_dir>
Prices: gemini-3.8-flash-tts standard tier, as listed 2026-10 ($0.50/M text in, $9/M audio out).
Free-tier AI Studio keys are billed $0. Re-check prices before quoting budgets."""
import json, os, sys
PRICE = {"gemini-3.8-flash-tts": (0.50, 9.00), "gemini-3.8-flash-lite-tts": (0.25, 4.50)}
f = os.path.join(sys.argv[1], "audio", "usage.json")
if not os.path.exists(f): sys.exit("no audio/usage.json — clips were cached or made outside tts.py")
u = json.load(open(f))
if not u: sys.exit("usage.json is empty")
tin = sum(v["in"] for v in u.values()); tout = sum(v["out"] for v in u.values())
pi, po = PRICE.get(next(iter(u.values()))["model"], PRICE["gemini-3.8-flash-tts"])
print(f"TTS calls {len(u)}  text-in {tin} tok  audio-out {tout} tok (~{tout/25:.0f}s audio)")
print(f"TTS cost ≈ ${tin*pi/1e6 + tout*po/1e6:.3f} (standard tier; $0 on free tier)")

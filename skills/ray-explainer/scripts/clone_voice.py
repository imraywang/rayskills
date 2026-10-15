"""Clone a voice with the MiniMax API (direct, see minimax_api.py) and register it for tts.py.

usage:
  python3 clone_voice.py <recording> [--name ray] [--start 0] [--max 180]          # prepare + inspect only
  python3 clone_voice.py <recording> [--name ray] ... --upload                     # upload, clone, register

<recording>: any audio or video file (m4a / wav / mp3 / mp4 …), ideally 1–3 min of one person speaking
in a quiet room, in the tone of the videos. The script extracts mono audio, removes rumble, normalizes
loudness and trims to --max seconds. Without --upload nothing leaves the machine — the voice is personal
biometric data; upload only after the owner has agreed in this conversation.

After cloning it immediately synthesizes one test sentence: MiniMax deletes a cloned voice that is not
used for TTS within 7 days. The registration goes to ~/.config/ray-explainer/voices.json (outside any
repo); then set "voice": "<name>" in script.json.
"""
import argparse, datetime, hashlib, json, os, subprocess, sys, urllib.request

CFG = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "ray-explainer")
VOICES_F, SAMPLES = os.path.join(CFG, "voices.json"), os.path.join(CFG, "samples")
TTS_MODEL = "speech-2.8-hd"
TEST = "大家好，这是我的复刻音色。我们今天来聊一个问题：AI 公司到底靠什么赢？"

ap = argparse.ArgumentParser()
ap.add_argument("recording"); ap.add_argument("--name", default="ray")
ap.add_argument("--start", type=float, default=0); ap.add_argument("--max", type=float, default=180)
ap.add_argument("--upload", action="store_true")
a = ap.parse_args()
os.makedirs(SAMPLES, exist_ok=True)

prepared = os.path.join(SAMPLES, f"{a.name}_sample.mp3")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(a.start), "-t", str(a.max), "-i", a.recording, "-vn", "-ac", "1", "-ar", "32000",
                "-af", "highpass=f=80,loudnorm=I=-18:TP=-1.5:LRA=11", "-b:a", "128k", prepared], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", prepared], capture_output=True, text=True).stdout)
sha = hashlib.sha256(open(prepared, "rb").read()).hexdigest()[:16]
print(f"prepared {prepared}  {dur:.1f}s  sha {sha}")
if dur < 10: sys.exit("too short: MiniMax needs at least 10 s of speech (1–3 min recommended)")
if dur < 30: print("WARN: under 30 s — clone quality improves a lot with 1–3 min")
if not a.upload:
    print("not uploaded. Listen to the prepared sample, then re-run with --upload once the owner agrees."); sys.exit(0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minimax_api

today = datetime.date.today().isoformat()
vid = f"{a.name.replace('-', '_')}_{today.replace('-', '')}_{sha[:6]}"   # must be unique per account, start with a letter
fid = minimax_api.upload(prepared, "voice_clone")
print(f"uploaded sample to MiniMax ({minimax_api.HOST}) file_id {fid}")
demo = minimax_api.clone(fid, vid, TEST, TTS_MODEL)
print("voice_id", vid)
if demo: urllib.request.urlretrieve(demo, os.path.join(SAMPLES, f"{a.name}_preview.mp3"))

# use it once with the production model right away (keeps the clone from expiring) and save the check clip
mp3, _ = minimax_api.tts(TEST, vid, TTS_MODEL)
check = os.path.join(SAMPLES, f"{a.name}_check.mp3"); open(check, "wb").write(mp3)

voices = json.load(open(VOICES_F)) if os.path.exists(VOICES_F) else {}
old = voices.get(a.name)
if old and old.get("model", "").startswith("fal-ai/"):   # keep the fal-hosted clone usable under another name
    voices[f"{a.name}-fal"] = old; print(f"previous fal clone kept as '{a.name}-fal'")
voices[a.name] = {"provider": "minimax", "model": TTS_MODEL, "voice_id": vid, "created": today, "last_used": today,
                  "sample": prepared, "sample_sha": sha, "sample_seconds": round(dur, 1)}
json.dump(voices, open(VOICES_F, "w"), ensure_ascii=False, indent=1)
os.chmod(VOICES_F, 0o600)
print(f"registered '{a.name}' in {VOICES_F}\ncheck clip: {check}\nset \"voice\": \"{a.name}\" in script.json, then rerun tts.py")

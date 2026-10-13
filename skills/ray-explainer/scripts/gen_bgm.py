"""Generate instrumental BGM candidates locally with ACE-Step 1.5 (MIT; outputs usable commercially).

usage: python3 gen_bgm.py <project> [--seeds 11 23 47] [--caption "..."] [--bpm 70] [--dur 180]

- Runs inside the ACE-Step venv: if `acestep` isn't importable it re-executes itself with
  `uv run --project $ACESTEP_DIR python ...` (ACESTEP_DIR defaults to ~/projects/ACE-Step-1.5).
- Caption / bpm default to script.json "bgm": {"caption": "...", "bpm": 70}; duration defaults to the film length
  (timeline.json duration + 6 s, so the tail can fade). Instrumental only.
- Writes <project>/bgm/<name>_<seed>.wav plus listen/<...>.m4a for Ray to audition. ~4 min for 3 × 3-minute tracks on an M4 Pro.
Install once: git clone https://github.com/ACE-Step/ACE-Step-1.5 ~/projects/ACE-Step-1.5 && cd there && uv sync;
models (~10 GB, HF ACE-Step/Ace-Step1.5) go in its checkpoints/ (Ray keeps them on the external drive 协作 via a symlink).
"""
import argparse, json, os, subprocess, sys, time

ACE = os.path.expanduser(os.environ.get("ACESTEP_DIR", "~/projects/ACE-Step-1.5"))
try:
    import acestep  # noqa: F401
except ImportError:
    if not os.path.isdir(ACE): sys.exit(f"ACE-Step not found at {ACE} (set ACESTEP_DIR or install it, see this file's docstring)")
    os.execvp("uv", ["uv", "run", "--project", ACE, "python", os.path.abspath(__file__), *sys.argv[1:]])

ap = argparse.ArgumentParser()
ap.add_argument("project"); ap.add_argument("--seeds", type=int, nargs="+", default=[11, 23, 47])
ap.add_argument("--caption"); ap.add_argument("--bpm", type=int); ap.add_argument("--dur", type=float); ap.add_argument("--name", default="bgm")
a = ap.parse_args()
PROJ = os.path.abspath(a.project)
cfgj = json.load(open(os.path.join(PROJ, "script.json"))).get("bgm") or {}
DEFAULT = ("Cinematic ambient documentary score, instrumental. Slow, sparse and contemplative. Warm analog synth pads and low drones, "
           "distant felt piano notes, soft airy textures. A subtle heartbeat-like pulse in the middle section, no drums, no vocals. "
           "Builds gently and opens up warmly toward the end, resolving on a single sustained note.")
caption = a.caption or cfgj.get("caption") or DEFAULT
bpm = a.bpm or cfgj.get("bpm") or 70
tlf = os.path.join(PROJ, "timeline.json")
dur = a.dur or (json.load(open(tlf))["duration"] + 6 if os.path.exists(tlf) else 180)
out = os.path.join(PROJ, "bgm"); os.makedirs(os.path.join(out, "listen"), exist_ok=True)

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false"); sys.path.insert(0, ACE)
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music

t0 = time.time()
dit, llm = AceStepHandler(), LLMHandler()
dit.initialize_service(project_root=ACE, config_path="acestep-v15-turbo", device="mps")
llm.initialize(checkpoint_dir=os.path.join(ACE, "checkpoints"), lm_model_path="acestep-5Hz-lm-1.7B", backend="mlx", device="mps")
params = GenerationParams(caption=caption[:512], lyrics="[Instrumental]", instrumental=True, bpm=bpm, duration=min(600, dur), inference_steps=8, shift=3.0)
res = generate_music(dit, llm, params, GenerationConfig(batch_size=len(a.seeds), use_random_seed=False, seeds=a.seeds, audio_format="wav"), save_dir=out)
if not res.success: sys.exit(f"ACE-Step failed: {res.error}")
for au in res.audios:
    seed = au["params"].get("seed"); dst = os.path.join(out, f"{a.name}_{seed}.wav")
    os.replace(au["path"], dst)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", dst, "-c:a", "aac", "-b:a", "128k", os.path.join(out, "listen", f"{a.name}_{seed}.m4a")], check=True)
    print(dst)
print(f"{len(res.audios)} tracks, {dur:.0f}s each, {time.time() - t0:.0f}s — send bgm/listen/*.m4a to Ray, then mix_bgm.py <project> bgm/<pick>.wav")

#!/usr/bin/env bash
# Verify the toolchain for ray-explainer; install puppeteer-core into ~/.cache/ray-explainer if missing.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"; ok=1
need(){ command -v "$1" >/dev/null && echo "ok   $1" || { echo "MISS $1 — $2"; ok=0; }; }
need node "brew install node"
need ffmpeg "brew install ffmpeg"
need python3 "brew install python"
if command -v yt-dlp >/dev/null; then YV=$(yt-dlp --version 2>/dev/null); [[ "$YV" < "2026.08" ]] && echo "WARN yt-dlp $YV is old — Bilibili answers 412; brew upgrade yt-dlp (or use uvx --from yt-dlp@latest yt-dlp)" || echo "ok   yt-dlp $YV"; else echo "WARN yt-dlp missing — brew install yt-dlp (or uvx --from yt-dlp@latest yt-dlp)"; fi
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
[ -x "$CHROME" ] && echo "ok   chrome" || { echo "MISS Google Chrome (or set CHROME=path)"; ok=0; }
# Python packages: the python3 on PATH, or the pipeline venv that scripts/_deps.py switches to. The venv is built here so a
# Homebrew Python upgrade (which drops user-site packages) can't take the pipeline down again (2026-11-12, new Mac).
PYENV="${RAY_EXPLAINER_PY:-$HOME/.local/share/ray-explainer/py-env}"; MODS="mlx_whisper pypinyin PIL numpy soundfile"
has(){ "$1" -c "import importlib.util,sys;sys.exit(any(importlib.util.find_spec(m) is None for m in sys.argv[1:]))" $MODS 2>/dev/null; }
if [ ! -x "$PYENV/bin/python" ] && command -v uv >/dev/null; then
  echo "...  building the pipeline Python env in $PYENV (once, a few minutes)"
  uv venv -q --python 3.13 "$PYENV" && uv pip install -q --python "$PYENV/bin/python" -r "$DIR/requirements.txt" || echo "WARN could not build $PYENV"
fi
if [ -x "$PYENV/bin/python" ] && has "$PYENV/bin/python"; then echo "ok   python packages ($MODS) in $PYENV"
elif has python3; then echo "ok   python packages ($MODS) — only in the python3 on PATH; install uv (brew install uv) and rerun to get the fallback env"
else echo "MISS python packages ($MODS) — brew install uv && rerun this script, or pip3 install -r $DIR/requirements.txt"; ok=0; fi
DEPS="${RAY_EXPLAINER_DEPS:-$HOME/.cache/ray-explainer}"
if [ ! -d "$DEPS/node_modules/puppeteer-core" ]; then
  echo "...  installing puppeteer-core into $DEPS"; mkdir -p "$DEPS"
  (cd "$DEPS" && { [ -f package.json ] || npm init -y >/dev/null; } && npm i --silent --no-audit --no-fund puppeteer-core@23.11.1 >/dev/null) && echo "ok   puppeteer-core" || { echo "MISS puppeteer-core"; ok=0; }
else echo "ok   puppeteer-core"; fi
python3 -c "import fal_client" 2>/dev/null && echo "ok   fal_client" || { echo "WARN fal_client missing — pip3 install fal-client (Kling digital host, fal-cloned voices)"; }
VOICES="${XDG_CONFIG_HOME:-$HOME/.config}/ray-explainer/voices.json"
[ -f "$VOICES" ] && echo "ok   voices: $(python3 -c "import json;print(', '.join(json.load(open('$VOICES'))))")" || echo "info no cloned voice yet (scripts/clone_voice.py) — Gemini prebuilt voices only"
VOX_PY="$HOME/.local/share/ray-explainer/voxcpm-env/bin/python"; VOX_MODEL=$([ -f "$VOICES" ] && python3 -c "import json;print(next((v['model'] for v in json.load(open('$VOICES')).values() if v.get('provider')=='voxcpm2'),''))"); if [ -x "$VOX_PY" ] && [ -n "$VOX_MODEL" ] && [ -d "$VOX_MODEL" ]; then echo "ok   VoxCPM2 local (voice ray-local)"; elif [ -x "$VOX_PY" ]; then echo "info VoxCPM2 env present but model not reachable — external drive unplugged? (only for voice ray-local)"; else echo "info VoxCPM2 not installed — only needed for voice ray-local"; fi
AV="${XDG_CONFIG_HOME:-$HOME/.config}/ray-explainer/avatars"; [ -d "$AV" ] && echo "info digital-host avatars: $(ls "$AV" | tr '\n' ' ')"
if [ -z "${FAL_KEY:-}" ]; then eval "$(grep -E '^\s*export\s+FAL_KEY=' ~/.zshrc 2>/dev/null)"; fi
ACE="${ACESTEP_DIR:-$HOME/projects/ACE-Step-1.5}"; if [ -d "$ACE/.venv" ] && [ -d "$ACE/checkpoints/acestep-v15-turbo" ]; then echo "ok   ACE-Step 1.5 (local BGM: gen_bgm.py)"; elif [ -d "$ACE/checkpoints/acestep-v15-turbo" ]; then echo "info ACE-Step at $ACE has no .venv yet — gen_bgm.py builds it on first run (uv)"; elif [ -d "$ACE" ]; then echo "info ACE-Step at $ACE but models not reachable — external drive unplugged? (only for gen_bgm.py)"; else echo "info ACE-Step not installed — only needed for local BGM (see scripts/gen_bgm.py)"; fi
if [ -z "${MINIMAX_API_KEY:-}" ]; then eval "$(grep -E '^\s*export\s+MINIMAX_API_KEY=' ~/.zshrc 2>/dev/null)"; fi
[ -n "${MINIMAX_API_KEY:-}" ] && echo "ok   MINIMAX_API_KEY present" || { echo "MISS MINIMAX_API_KEY — template default voice ray calls the MiniMax API directly"; ok=0; }
[ -n "${FAL_KEY:-}" ] && echo "ok   FAL_KEY present" || echo "WARN FAL_KEY missing — only for the Kling digital host (host.py) and voices cloned through fal"
# API key: shell env first, then ~/.zshrc export
if [ -z "${GEMINI_API_KEY:-}" ]; then eval "$(grep -E '^\s*export\s+GEMINI_API_KEY=' ~/.zshrc 2>/dev/null)"; fi
if [ -n "${GEMINI_API_KEY:-}" ]; then
  code=$(curl -s -o /dev/null -w '%{http_code}' "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts?key=$GEMINI_API_KEY")
  [ "$code" = 200 ] && echo "ok   GEMINI_API_KEY (gemini-3.8-flash-tts reachable)" || { echo "FAIL GEMINI_API_KEY → HTTP $code"; ok=0; }
else echo "MISS GEMINI_API_KEY — ask the user for a key"; ok=0; fi
[ $ok = 1 ] && echo "READY" || { echo "NOT READY"; exit 1; }

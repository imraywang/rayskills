#!/usr/bin/env bash
# Verify the toolchain for ray-explainer; install puppeteer-core into ~/.cache/ray-explainer if missing.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"; ok=1
need(){ command -v "$1" >/dev/null && echo "ok   $1" || { echo "MISS $1 — $2"; ok=0; }; }
need node "brew install node"
need ffmpeg "brew install ffmpeg"
need python3 "brew install python"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
[ -x "$CHROME" ] && echo "ok   chrome" || { echo "MISS Google Chrome (or set CHROME=path)"; ok=0; }
python3 -c "import mlx_whisper" 2>/dev/null && echo "ok   mlx_whisper" || { echo "MISS mlx_whisper — pip3 install mlx-whisper (TTS QA)"; ok=0; }
DEPS="${RAY_EXPLAINER_DEPS:-$HOME/.cache/ray-explainer}"
if [ ! -d "$DEPS/node_modules/puppeteer-core" ]; then
  echo "...  installing puppeteer-core into $DEPS"; mkdir -p "$DEPS"
  (cd "$DEPS" && { [ -f package.json ] || npm init -y >/dev/null; } && npm i --silent --no-audit --no-fund puppeteer-core@23.11.1 >/dev/null) && echo "ok   puppeteer-core" || { echo "MISS puppeteer-core"; ok=0; }
else echo "ok   puppeteer-core"; fi
system_profiler SPFontsDataType 2>/dev/null | grep -q "Hannotate SC" && echo "ok   font Hannotate SC" || echo "WARN font Hannotate SC missing — handwritten look falls back to PingFang"
command -v uv >/dev/null && echo "ok   uv (film_gate motion check)" || echo "WARN uv missing — brew install uv (only for the post-render film_gate report)"
python3 -c "import fal_client" 2>/dev/null && echo "ok   fal_client" || { echo "MISS fal_client — pip3 install fal-client (template default: voice ray via fal)"; ok=0; }
[ -d "$DIR/../assets/huashu/clips" ] && echo "ok   huashu grammars ($(ls "$DIR/../assets/huashu/clips" | wc -l | tr -d ' '))" || { echo "MISS assets/huashu (explainer grammars)"; ok=0; }
VOICES="${XDG_CONFIG_HOME:-$HOME/.config}/ray-explainer/voices.json"
[ -f "$VOICES" ] && echo "ok   voices: $(python3 -c "import json;print(', '.join(json.load(open('$VOICES'))))")" || echo "info no cloned voice yet (scripts/clone_voice.py) — Gemini prebuilt voices only"
AV="${XDG_CONFIG_HOME:-$HOME/.config}/ray-explainer/avatars"; [ -d "$AV" ] && echo "info digital-host avatars: $(ls "$AV" | tr '\n' ' ')"; python3 -c "import pypinyin" 2>/dev/null && echo "ok   pypinyin" || { echo "MISS pypinyin — pip3 install pypinyin (corner host lip-sync, template default)"; ok=0; }
if [ -z "${FAL_KEY:-}" ]; then eval "$(grep -E '^\s*export\s+FAL_KEY=' ~/.zshrc 2>/dev/null)"; fi
ACE="${ACESTEP_DIR:-$HOME/projects/ACE-Step-1.5}"; if [ -d "$ACE/.venv" ] && [ -d "$ACE/checkpoints/acestep-v15-turbo" ]; then echo "ok   ACE-Step 1.5 (local BGM: gen_bgm.py)"; elif [ -d "$ACE" ]; then echo "info ACE-Step at $ACE but models not reachable — external drive unplugged? (only for gen_bgm.py)"; else echo "info ACE-Step not installed — only needed for local BGM (see scripts/gen_bgm.py)"; fi
[ -n "${FAL_KEY:-}" ] && echo "ok   FAL_KEY present" || { echo "MISS FAL_KEY — template default voice ray needs it (fal MiniMax)"; ok=0; }
# API key: shell env first, then ~/.zshrc export
if [ -z "${GEMINI_API_KEY:-}" ]; then eval "$(grep -E '^\s*export\s+GEMINI_API_KEY=' ~/.zshrc 2>/dev/null)"; fi
if [ -n "${GEMINI_API_KEY:-}" ]; then
  code=$(curl -s -o /dev/null -w '%{http_code}' "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts?key=$GEMINI_API_KEY")
  [ "$code" = 200 ] && echo "ok   GEMINI_API_KEY (gemini-3.8-flash-tts reachable)" || { echo "FAIL GEMINI_API_KEY → HTTP $code"; ok=0; }
else echo "MISS GEMINI_API_KEY — ask the user for a key"; ok=0; fi
[ $ok = 1 ] && echo "READY" || { echo "NOT READY"; exit 1; }

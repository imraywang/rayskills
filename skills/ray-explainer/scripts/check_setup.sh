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
# API key: shell env first, then ~/.zshrc export
if [ -z "${GEMINI_API_KEY:-}" ]; then eval "$(grep -E '^\s*export\s+GEMINI_API_KEY=' ~/.zshrc 2>/dev/null)"; fi
if [ -n "${GEMINI_API_KEY:-}" ]; then
  code=$(curl -s -o /dev/null -w '%{http_code}' "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts?key=$GEMINI_API_KEY")
  [ "$code" = 200 ] && echo "ok   GEMINI_API_KEY (gemini-3.8-flash-tts reachable)" || { echo "FAIL GEMINI_API_KEY → HTTP $code"; ok=0; }
else echo "MISS GEMINI_API_KEY — ask the user for a key"; ok=0; fi
[ $ok = 1 ] && echo "READY" || { echo "NOT READY"; exit 1; }

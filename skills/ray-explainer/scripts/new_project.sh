#!/usr/bin/env bash
# Create a video project. usage: new_project.sh <slug> [parent_dir] [--landscape]
# --landscape: 1920×1080 (script.json "aspect": "landscape"); default is portrait 1080×1920
# The project starts with script.json only; the HyperFrames skeleton (hf/) is added later, see references/hyperframes.md.
set -eu
SK="$(cd "$(dirname "$0")/.." && pwd)"
land=0; args=()
for a in "$@"; do [ "$a" = "--landscape" ] && land=1 || args+=("$a"); done
slug="${args[0]}"; parent="${args[1]:-$HOME/Movies/ray-explainer}"
dir="$parent/$(date +%Y-%m-%d)-$slug"
[ -e "$dir" ] && { echo "exists: $dir" >&2; exit 1; }
mkdir -p "$dir"
tpl="$SK/assets/template/script.template.json"
[ -f "$SK/local/script.template.json" ] && tpl="$SK/local/script.template.json"   # the user's own defaults, kept out of git
cp "$tpl" "$dir/script.json"
if [ "$land" = 1 ]; then
  python3 - "$dir/script.json" <<'PY'
import json, sys
p = sys.argv[1]; s = json.load(open(p)); out = {}
for k, v in s.items():
    out[k] = v
    if k == "title": out["aspect"] = "landscape"
if out.get("host"): out["host"] = {**out["host"], "show": []}   # 横屏主持人只在关键句出现：分镜时在这里标 3–6 句
json.dump(out, open(p, "w"), ensure_ascii=False, indent=2); open(p, "a").write("\n")
PY
fi
echo "$dir"

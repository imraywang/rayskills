#!/usr/bin/env bash
# Create a video project from the template. usage: new_project.sh <slug> [parent_dir]
set -eu
SK="$(cd "$(dirname "$0")/.." && pwd)"
slug="$1"; parent="${2:-$HOME/Movies/ray-explainer}"
dir="$parent/$(date +%Y-%m-%d)-$slug"
[ -e "$dir" ] && { echo "exists: $dir" >&2; exit 1; }
mkdir -p "$dir"
cp "$SK/assets/template/video.html" "$SK/assets/template/kit.js" "$SK/assets/template/patterns.js" "$dir/"
cp "$SK/assets/template/script.template.json" "$dir/script.json"
printf "window.META = { header: '' };\n// S.<sceneId> = (t, sc) => { ... }  — see references/scene-patterns.md and assets/template/scenes.example.js\n" > "$dir/scenes.js"
echo "$dir"

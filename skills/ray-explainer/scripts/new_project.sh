#!/usr/bin/env bash
# Create a video project from the template. usage: new_project.sh <slug> [parent_dir] [--landscape]
# --landscape: 1920×1080 (script.json "aspect": "landscape"); default is portrait 1080×1920
set -eu
SK="$(cd "$(dirname "$0")/.." && pwd)"
land=0; args=()
for a in "$@"; do [ "$a" = "--landscape" ] && land=1 || args+=("$a"); done
slug="${args[0]}"; parent="${args[1]:-$HOME/Movies/ray-explainer}"
dir="$parent/$(date +%Y-%m-%d)-$slug"
[ -e "$dir" ] && { echo "exists: $dir" >&2; exit 1; }
mkdir -p "$dir"
cp "$SK/assets/template/video.html" "$SK/assets/template/kit.js" "$SK/assets/template/patterns.js" "$dir/"
cp "$SK/assets/template/script.template.json" "$dir/script.json"
printf "window.META = { header: '' };\n// S.<sceneId> = (t, sc) => { ... }  — see references/patterns.md and assets/template/scenes.example.js\n" > "$dir/scenes.js"
if [ "$land" = 1 ]; then   # 横屏：手绘套路只有竖屏版，模板里的手绘开场换成语法片段
  python3 - "$dir/script.json" <<'PY'
import json, sys
p = sys.argv[1]; s = json.load(open(p)); out = {}
for k, v in s.items():
    out[k] = v
    if k == "title": out["aspect"] = "landscape"
out["host"] = {**out.get("host", {}), "show": []}   # 横屏主持人只在关键句出现：分镜时在这里标 3–6 句
for sc in out["scenes"]:
    if not sc.get("grammar"): sc["grammar"] = "y5_kinetic_type"; sc.setdefault("cues", [{"at": 0, "kind": "title", "text": ""}])
json.dump(out, open(p, "w"), ensure_ascii=False, indent=2); open(p, "a").write("\n")
PY
fi
echo "$dir"

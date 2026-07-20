#!/usr/bin/env bash
# rayskills 构建脚本:校验成员完整性 + 跳过 beta 试验 skill,产物落 dist/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
DIST="$ROOT/dist/skills"
WORKBUDDY_DIST="$ROOT/dist/workbuddy"

rm -rf "$DIST" "$WORKBUDDY_DIST"
mkdir -p "$DIST" "$WORKBUDDY_DIST"

if ! command -v python3 >/dev/null 2>&1; then
  echo "FAIL: 缺少 python3,无法生成 WorkBuddy 导入包" >&2
  exit 1
fi

count=0
skipped=0
for dir in "$SKILLS_DIR"/*/; do
  name="$(basename "$dir")"

  # beta 门控:名字带 beta 的本地试验 skill 不进产物
  if [[ "$name" == *beta* ]]; then
    echo "skip (beta): $name"
    skipped=$((skipped+1))
    continue
  fi

  # 完整性校验:必须有 SKILL.md 且 frontmatter 的 name 与目录名一致
  skill_md="$dir/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then
    echo "FAIL: $name 缺 SKILL.md" >&2
    exit 1
  fi
  declared="$(grep -m1 '^name:' "$skill_md" | sed 's/^name:[[:space:]]*//')"
  if [[ "$declared" != "$name" ]]; then
    echo "FAIL: $name 的 frontmatter name='$declared' 与目录名不符" >&2
    exit 1
  fi

  cp -R "$dir" "$DIST/$name"
  python3 "$ROOT/tools/package_workbuddy.py" "$dir" "$WORKBUDDY_DIST/$name.zip"
  echo "ok: $name"
  count=$((count+1))
done

echo "---"
echo "构建完成:$count 个 skill 进产物,跳过 $skipped 个 beta。"
echo "目录产物:dist/skills/"
echo "WorkBuddy 导入包:dist/workbuddy/"

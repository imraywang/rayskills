#!/usr/bin/env bash
# Subset Noto Sans SC Bold / Medium to the glyphs build.py wrote into chars.txt.
# usage: bash make_fonts.sh <dir holding NotoSansSC-Bold.otf and NotoSansSC-Medium.otf>
# Fonts (OFL): https://github.com/notofonts/noto-cjk/tree/main/Sans/SubsetOTF/SC
set -euo pipefail
src="${1:?font directory}"
[ -f chars.txt ] || { echo "run python3 build.py first (it writes chars.txt)"; exit 1; }
mkdir -p assets/fonts
for pair in "Bold:700" "Medium:500"; do
  pyftsubset "$src/NotoSansSC-${pair%%:*}.otf" --text-file=chars.txt --unicodes="U+0020-007E" \
    --flavor=woff2 --output-file="assets/fonts/sans-${pair##*:}.woff2"
done
ls -la assets/fonts

#!/usr/bin/env bash
# Fonts for style xiaolin (all OFL). Run in the project root after python3 build.py (it writes brush.txt).
#   Noto Sans SC 500/700/900 as woff for the page; Noto Sans SC Black otf for make_stamps.py; Ma Shan Zheng for brush titles.
set -euo pipefail
mkdir -p fontdl assets/fonts
B=https://raw.githubusercontent.com
[ -f fontdl/NotoSansSC-Black.otf ] || curl -sL -o fontdl/NotoSansSC-Black.otf $B/notofonts/noto-cjk/main/Sans/SubsetOTF/SC/NotoSansSC-Black.otf
[ -f fontdl/MaShanZheng-Regular.ttf ] || curl -sL -o fontdl/MaShanZheng-Regular.ttf $B/google/fonts/main/ofl/mashanzheng/MaShanZheng-Regular.ttf
for w in Medium:500 Bold:700 Black:900; do
  f=fontdl/NotoSansSC-${w%%:*}.otf
  [ -f $f ] || curl -sL -o $f $B/notofonts/noto-cjk/main/Sans/SubsetOTF/SC/NotoSansSC-${w%%:*}.otf
  [ -f assets/fonts/NotoSansSC-${w##*:}.woff ] || pyftsubset $f --unicodes="*" --flavor=woff --output-file=assets/fonts/NotoSansSC-${w##*:}.woff
done
pyftsubset fontdl/MaShanZheng-Regular.ttf --text-file=brush.txt --text="？，" --flavor=woff2 --output-file=assets/fonts/brush.woff2
ls -la assets/fonts

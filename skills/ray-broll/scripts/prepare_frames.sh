#!/bin/bash
# 从 <item>/frames/last-frame-original.png 生成 Gate 3 首尾帧:
#   实测底色采样(4x4 均值) -> bg-hex.txt
#   last-frame.png (1080x1920 scale+crop)
#   first-frame.png (实测底色纯色空场)
# 用法: prepare_frames.sh <item-dir> [采样点x:y,默认 28:58]
set -euo pipefail

ITEM="${1:?用法: prepare_frames.sh <item-dir> [x:y]}"
XY="${2:-28:58}"
X="${XY%%:*}"; Y="${XY##*:}"
SRC="$ITEM/frames/last-frame-original.png"
[ -f "$SRC" ] || { echo "缺少 $SRC"; exit 1; }

PX=$(mktemp)
ffmpeg -y -v error -i "$SRC" -vf "crop=4:4:${X}:${Y},scale=1:1" \
  -frames:v 1 -f rawvideo -pix_fmt rgb24 "$PX"
HEX=$(xxd -p "$PX" | tr -d '\n')
rm -f "$PX"
echo "$HEX" > "$ITEM/frames/bg-hex.txt"

ffmpeg -y -v error -i "$SRC" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" \
  "$ITEM/frames/last-frame.png"
ffmpeg -y -v error -f lavfi -i "color=c=0x${HEX}:s=1080x1920" \
  -frames:v 1 "$ITEM/frames/first-frame.png"
echo "$(basename "$ITEM") bg=#$HEX frames ready"

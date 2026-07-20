#!/bin/bash
# 单条成片 QA 全家桶:无声版 + 逐秒 contact sheet + 首/尾帧 + 尾帧对照 + 客观分
# 用法: qa_video.sh <video.mp4> <confirmed-still.png> [out-dir=视频所在目录] [bg-hex]
set -euo pipefail

V="${1:?用法: qa_video.sh <video.mp4> <confirmed-still.png> [out-dir] [bg-hex]}"
STILL="${2:?缺少确认静帧参数}"
OUT="${3:-$(dirname "$V")}"
BGHEX="${4:-}"
mkdir -p "$OUT"

STEM="$(basename "${V%.*}")"; STEM="${STEM%-noaudio}"
BASE="$OUT/$STEM"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
TILES=$(python3 -c "print(min(10, max(3, int(float('$DUR')))))")

# 无声版(有音轨才剥)
if ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$V" | grep -q audio; then
  ffmpeg -y -v error -i "$V" -map 0:v:0 -c:v copy -an "${BASE}-noaudio.mp4"
else
  cp -f "$V" "${BASE}-noaudio.mp4"
fi

ffmpeg -y -v error -i "${BASE}-noaudio.mp4" \
  -vf "fps=1,scale=203:360,tile=${TILES}x1" -frames:v 1 "$OUT/contact-sheet.jpg"
ffmpeg -y -v error -i "${BASE}-noaudio.mp4" -frames:v 1 "$OUT/video-first-frame.jpg"
ffmpeg -y -v error -sseof -0.1 -i "${BASE}-noaudio.mp4" -frames:v 1 "$OUT/video-last-frame.jpg"
ffmpeg -y -v error -i "$STILL" -i "$OUT/video-last-frame.jpg" \
  -filter_complex "[0:v]scale=270:480[a];[1:v]scale=270:480[b];[a][b]hstack" \
  "$OUT/end-frame-comparison.jpg"

VENV_PY="${HYPERFRAMES_VENV:-$HOME/hyperframes-projects/.omni-venv}/bin/python"
[ -x "$VENV_PY" ] || VENV_PY=python3
HERE="$(cd "$(dirname "$0")" && pwd)"
ARGS=(--video "${BASE}-noaudio.mp4" --still "$STILL")
[ -n "$BGHEX" ] && ARGS+=(--bg-hex "$BGHEX")
"$VENV_PY" "$HERE/qa_score.py" "${ARGS[@]}" || echo "  (qa_score 需要 Pillow,分数缺省不阻塞)"
echo "QA assets -> $OUT"

#!/usr/bin/env bash
# 把一段视频切成语法片段能用的帧序列：<project>/media/<name>/0001.jpg…
# 用法：video_frames.sh <project> <name> <视频文件> <起点秒> <时长秒> [宽度=960] [fps=24]
# script.json 里这样引用：{"kind":"image","video":{"dir":"/media/<name>","fps":24}, "text":"…"}
# 只截要用的那几秒（3–6s 为宜）；帧数由 render.js 自动数。
set -euo pipefail
[ $# -ge 5 ] || { sed -n 2,5p "$0"; exit 2; }
proj=$1 name=$2 src=$3 ss=$4 dur=$5 w=${6:-960} fps=${7:-24}
out="$proj/media/$name"
rm -rf "$out"; mkdir -p "$out"
ffmpeg -loglevel error -y -ss "$ss" -t "$dur" -i "$src" -an -vf "fps=$fps,scale=$w:-2" -q:v 3 "$out/%04d.jpg"
echo "$out: $(ls "$out" | wc -l | tr -d ' ') frames @ ${fps}fps"

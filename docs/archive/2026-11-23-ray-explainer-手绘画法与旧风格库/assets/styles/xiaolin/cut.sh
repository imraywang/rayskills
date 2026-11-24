#!/bin/bash
# name src ss dur [mode]   mode: fill (default, 16:9 crop), blur (vertical/odd -> blurred fill), crop-ap (hide AP logo),
#   sub / deep / tight: zoom off burned-in subtitles, banners and corner logos (1.22x / 1.35x / centre 58%)
cut(){ n=$1; s=$2; ss=$3; d=$4; m=${5:-fill}
 case $m in
  fill) vf="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080";;
  blur) vf="split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=30:3,eq=brightness=-0.15[bg];[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0";;
  crop-ap) vf="crop=iw*0.86:ih*0.86:0:ih*0.14,scale=1920:1080";;
  sub) vf="crop=iw*0.82:ih*0.82:iw*0.09:ih*0.03,scale=1920:1080";;
  deep) vf="crop=iw*0.74:ih*0.74:iw*0.13:ih*0.03,scale=1920:1080";;
  tight) vf="crop=iw*0.58:ih*0.58:iw*0.21:ih*0.13,scale=1920:1080";;
  keep) vf="scale=-2:1080";;
 esac
 ffmpeg -v error -y -ss $ss -t $d -i "$s" -an -vf "$vf" -r 30 -c:v libx264 -crf 20 -pix_fmt yuv420p "assets/v/$n.mp4" && echo "$n ok"; }
R=raw; O=/Volumes/协作/ray-explainer/2026-10-20-spacex-share-every-kid/hf/assets/video
cut starship1 $R/starship.mp4 9.5 3.2
cut starship2 $R/starship.mp4 17 3
cut musk1 $R/musk.mp4 15 4
cut musk2 $R/musk.mp4 45.5 4
cut kids1 $R/bell.mp4 45 3.5
cut kids2 $R/bell.mp4 39.5 3.5
cut kids3 $R/bell.mp4 56.5 4.5
cut kids4 $R/bell.mp4 34 3.5
cut belltrump $R/bell.mp4 5.5 4.5
cut podium $R/bell.mp4 11 4.5
cut nyse1 $R/nyse.mp4 26 4
cut nyse2 $R/nyse.mp4 38 3.5
cut nyse3 $R/nyse.mp4 17.5 3.5
cut dario1 $R/dario.mp4 5 4
cut obbba $O/raw/obbba_raw.mp4 2 5 blur
cut ta $O/trumpaccounts.mp4 0 8.8 keep
cut tt1 $O/tavan-tolgoi-crop.mp4 0 8
cut tt2 $O/tavan-tolgoi-aerial-clean.mp4 0 8
cut mng1 $R/mongolia.mp4 72 4.5 crop-ap
cut mng2 $R/mongolia.mp4 0.5 4 crop-ap
cut rus1 $O/russia-crop.mp4 0 8 blur
cut dell1 $O/dell-crop.mp4 0 6
cut launch $O/launch.mp4 0 8

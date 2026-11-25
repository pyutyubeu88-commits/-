#!/usr/bin/env bash
# usage: ./build.sh [image.png] [voice.mp3] [bgm.mp3] [out.mp4]
set -euo pipefail
IMG=${1:-image.png}; VOICE=${2:-voice.mp3}; BGM=${3:-bgm.mp3}; OUT=${4:-output_shorts.mp4}
FPS=30; LEAD=0.6; TAIL=1.2
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VOICE")
DUR=$(python3 -c "print(round($VD+$LEAD+$TAIL,2))")
FRAMES=$(python3 -c "print(int($DUR*$FPS))")
ffmpeg -y -hide_banner -loglevel error -i "$IMG" -i "$VOICE" -stream_loop -1 -i "$BGM" \
-filter_complex "
[0:v]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,
 zoompan=z='1+0.15*on/${FRAMES}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${FRAMES}:s=1080x1920:fps=${FPS},
 colorlevels=rimax=0.85:gimax=0.85:bimax=0.85,fade=t=in:d=0.8,fade=t=out:st=$(python3 -c "print($DUR-1)"):d=1,format=yuv420p[v];
[1:a]adelay=$(python3 -c "print(int($LEAD*1000))")|$(python3 -c "print(int($LEAD*1000))"),apad=whole_dur=${DUR}[vo];
[2:a]volume=0.15,afade=t=in:d=1.5,afade=t=out:st=$(python3 -c "print($DUR-1.5)"):d=1.5[bg];
[vo][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]" \
-map "[v]" -map "[a]" -t "$DUR" -r $FPS -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "done: $OUT (${DUR}s)"

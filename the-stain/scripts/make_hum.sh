#!/bin/bash
# Make hum_<n>.wav from a fragment of the song.
# Usage: make_hum.sh <song.wav> <start_sec> <len_sec> <level 1-5> <out.wav> [total_sec]
# Level 1 = slowest/darkest/most distant; level 5 = nearly the original.
set -e
IN=$1; ST=$2; LEN=$3; LV=$4; OUT=$5; TOTAL=${6:-30}
# speed 0.30 -> 0.85, lowpass 600 -> 4000 Hz, reverb wet 0.9 -> 0.35
SPEED=$(python3 -c "print([0.30,0.40,0.55,0.70,0.85][$LV-1])")
LP=$(python3 -c "print([600,900,1500,2500,4000][$LV-1])")
WET=$(python3 -c "print([0.9,0.8,0.65,0.5,0.35][$LV-1])")
TMP=$(mktemp -d)
ffmpeg -y -loglevel error -ss $ST -t $LEN -i "$IN" -ac 2 -ar 48000 $TMP/frag.wav
# slow + pitch down together (tape-style): resample trick
ffmpeg -y -loglevel error -i $TMP/frag.wav -af "asetrate=48000*$SPEED,aresample=48000,lowpass=f=$LP,lowpass=f=$LP" $TMP/slow.wav
# long reverb via layered echoes, then crossfaded loop to TOTAL seconds
ffmpeg -y -loglevel error -i $TMP/slow.wav -af "aecho=0.8:$WET:120|340|780|1500:0.5|0.4|0.3|0.2,afade=t=in:d=1.5,afade=t=out:st=$(python3 -c "import subprocess;d=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','$TMP/slow.wav']));print(max(d-1.5,0.1))"):d=1.5" $TMP/rev.wav
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $TMP/rev.wav)
N=$(python3 -c "import math;print(max(1,math.ceil($TOTAL/max($D-1.5,0.5))))")
ARGS=""; FC=""; for i in $(seq 0 $((N-1))); do ARGS="$ARGS -i $TMP/rev.wav"; done
python3 - "$N" "$D" "$TMP" <<'PY'
import sys,subprocess
n,d,tmp=int(sys.argv[1]),float(sys.argv[2]),sys.argv[3]
cur=f"{tmp}/rev.wav"
for i in range(1,n):
    out=f"{tmp}/loop{i}.wav"
    subprocess.check_call(["ffmpeg","-y","-loglevel","error","-i",cur,"-i",f"{tmp}/rev.wav","-filter_complex","acrossfade=d=1.5",out]); cur=out
subprocess.check_call(["cp",cur,f"{tmp}/loop.wav"])
PY
ffmpeg -y -loglevel error -i $TMP/loop.wav -t $TOTAL -af "loudnorm=I=-26" "$OUT"
rm -rf $TMP

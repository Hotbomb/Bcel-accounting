#!/bin/bash
# hum_1..hum_6 from the song's hook (hookB section). Longer + clearer each time.
cd "$(dirname "$0")/.."
ST=$(python3 -c "import json;print(json.load(open('assets/song_markers.json'))['hookB'])")
for n in 1 2 3 4 5 6; do
  LEN=$(python3 -c "print([2.8,3.6,4.6,5.5,7.3,11.0][$n-1])")
  scripts/make_hum.sh assets/song.wav $ST $LEN $n audio/hum/hum_$n.wav 150
done

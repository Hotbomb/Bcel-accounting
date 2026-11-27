#!/bin/bash
# Re-render specific shots from scratch (after fixes), encode, commit, push.  Usage: rerender.sh SHOT...
cd "$(dirname "$0")/.."
for s in "$@"; do
  rm -rf renders/$s; mkdir -p renders/$s
  /opt/bpyenv/bin/python scripts/render_shot.py $s 2>&1 | grep -E "SHOT DONE|Error|Traceback" | tail -2
  F=$(python3 -c "import json;print([x['frames'] for x in json.load(open('timeline.json')) if x['id']=='$s'][0]//2)"); N=$(ls renders/$s/f_*.png | wc -l)
  [ "$N" -ge "$F" ] || { echo "INCOMPLETE $s"; exit 3; }
  ffmpeg -y -loglevel error -framerate 12 -pattern_type glob -i "renders/$s/f_*.png" -vf "fps=24" -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p clips/$s.mp4
  git add clips/$s.mp4 blender/shots_def.py && git commit -qm "re-render $s (clarity fix)" && (for i in 1 2 3 4; do git push -q origin ccr-35112457-trui8i 2>/dev/null && break; sleep $((2**i)); done)
  echo "RERENDERED $s"
done
echo "RERENDER DONE"

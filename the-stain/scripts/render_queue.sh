#!/bin/bash
# Render every Blender shot in film order (resumable). After each shot: encode clip, commit, push.
# Usage: render_queue.sh [max_seconds]
cd "$(dirname "$0")/.."; MAX=${1:-6600}; START=$(date +%s)
SHOTS=$(python3 -c "import json;print(' '.join(s['id'] for s in json.load(open('timeline.json')) if s['id'] not in ('0-0','0C','CREDITS')))")
for s in $SHOTS; do
  [ -f clips/$s.mp4 ] && continue
  LEFT=$(( MAX - ($(date +%s) - START) )); [ $LEFT -lt 120 ] && { echo "QUEUE TIME UP"; exit 3; }
  /opt/bpyenv/bin/python scripts/render_shot.py $s --max-seconds $LEFT 2>&1 | grep -E "FRAME|SHOT DONE|TIME LIMIT|Error|Traceback" | tail -3
  N=$(ls renders/$s/f_*.png 2>/dev/null | wc -l); F=$(python3 -c "import json;print([x['frames'] for x in json.load(open('timeline.json')) if x['id']=='$s'][0]//2)")
  if [ "$N" -ge "$F" ]; then
    ffmpeg -y -loglevel error -framerate 12 -pattern_type glob -i "renders/$s/f_*.png" -vf "fps=24" -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p clips/$s.mp4
    sed -i "s/^- \[ \] $s\b.*/- [x] $s (rendered $(date -u +%F))/" PROGRESS.md
    git add clips/$s.mp4 PROGRESS.md && git commit -qm "render: $s" && (for i in 1 2 3 4; do git push -q origin ccr-35112457-trui8i 2>/dev/null && break; sleep $((2**i)); done)
    echo "CLIP $s done"
  else echo "PARTIAL $s $N/$F"; exit 3; fi
done
echo "ALL SHOTS RENDERED"

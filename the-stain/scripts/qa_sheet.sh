#!/bin/bash
# Low-res stills (start / middle / end) for the given shots -> checkpoints/qa/<name>.jpg contact sheet
cd "$(dirname "$0")/.."; NAME=$1; shift
mkdir -p renders/qa checkpoints/qa
for s in "$@"; do
  D=$(python3 -c "import json;print([x['dur'] for x in json.load(open('timeline.json')) if x['id']=='$s'][0])")
  T=$(python3 -c "d=$D;print(','.join(f'{x:.2f}' for x in (0.3, d*0.5, d-0.3)))")
  /opt/bpyenv/bin/python scripts/render_shot.py $s --stills $T --pct 40 --samples 6 --out renders/qa/$s >/dev/null 2>&1 || echo "FAIL $s"
done
python3 - "$NAME" "$@" <<'PY'
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
name, shots = sys.argv[1], sys.argv[2:]
rows = []
for s in shots:
    fs = sorted(glob.glob(f"renders/qa/{s}/still_*.png"))[:3]
    if fs: rows.append((s, [Image.open(f).convert("RGB").resize((384, 216)) for f in fs]))
W, H = 60 + 3 * 388, len(rows) * 220
im = Image.new("RGB", (W, H), (30, 30, 30)); d = ImageDraw.Draw(im)
f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 20)
for i, (s, ims) in enumerate(rows):
    d.text((6, i * 220 + 95), s, font=f, fill=(255, 255, 255))
    for j, x in enumerate(ims): im.paste(x, (60 + j * 388, i * 220 + 2))
im.save(f"checkpoints/qa/{name}.jpg", quality=82); print("sheet", name, len(rows))
PY

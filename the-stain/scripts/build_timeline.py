# shots.json + voice durations -> timeline.json (shot lengths in frames at 24 fps, even numbers for "on twos").
import json, os, soundfile as sf, math
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FPS = 24
shots = json.load(open(os.path.join(ROOT, "shots.json")))
song_len = sf.info(os.path.join(ROOT, "assets", "song.wav")).duration
tl, cursor = [], 0
for s in shots:
    t, lines = 0.0, []
    for i, l in enumerate(s["lines"]):
        f = os.path.join(ROOT, "audio", "vo", f"{s['id']}_{l['char']}_{i}.wav")
        d = sf.info(f).duration
        t += l["pre"]
        lines.append({**l, "i": i, "file": os.path.relpath(f, ROOT), "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    dur = max(s["min"], t + s["post"]) if lines else s["min"]
    if s["id"] == "CREDITS": dur = song_len
    frames = int(math.ceil(dur * FPS / 2.0)) * 2
    sfx = []
    for name, at in s["sfx"]:
        if isinstance(at, str) and at.startswith("after:"):
            at = lines[int(at[6:])]["end"] + 0.05
        sfx.append({"name": name, "at": round(float(at), 3)})
    tl.append({**s, "lines": lines, "sfx": sfx, "frames": frames, "dur": frames / FPS,
               "start_frame": cursor, "start": cursor / FPS})
    cursor += frames
json.dump(tl, open(os.path.join(ROOT, "timeline.json"), "w"), ensure_ascii=False, indent=1)
body = sum(x["frames"] for x in tl if x["id"] != "CREDITS")
blender = sum(x["frames"] for x in tl if x["id"] not in ("0-0", "0C", "CREDITS"))
print(f"film (no credits): {body/FPS/60:.2f} min, total with credits {cursor/FPS/60:.2f} min")
print(f"Blender frames: {blender} -> unique on twos: {blender//2}")

# Render one shot on twos. Resumable: existing frames are skipped.
# Usage: render_shot.py <SHOT> [--preview] [--stills t1,t2,...] [--max-seconds N] [--samples N] [--out DIR]
import sys, os, time, math, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "blender"))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser(); ap.add_argument("shot"); ap.add_argument("--preview", action="store_true")
ap.add_argument("--stills", default=""); ap.add_argument("--max-seconds", type=float, default=1e9)
ap.add_argument("--samples", type=int, default=0); ap.add_argument("--out", default=""); ap.add_argument("--pct", type=int, default=0)
a = ap.parse_args(argv)
import bpy
import shots_def
t_start = time.time()
S = shots_def.build(a.shot)
sc = bpy.context.scene
ROOT = os.path.join(HERE, "..")
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = a.samples or (6 if a.preview else 10)
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.cycles.transparent_max_bounces = 8; sc.cycles.sample_clamp_indirect = 4; sc.cycles.blur_glossy = 1.0
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = S.exposure
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.resolution_percentage = a.pct or (50 if a.preview else 100)
sc.render.film_transparent = False
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"
# crop the render to the visible matte area (the black bars are added later)
m = S.tl["matte"]
if isinstance(m, (int, float)):
    if m > 1.78:
        h = 1280 / m / 720; sc.render.use_border = True; sc.render.use_crop_to_border = False
        sc.render.border_min_x, sc.render.border_max_x = 0, 1; sc.render.border_min_y, sc.render.border_max_y = (1 - h) / 2 - 0.01, (1 + h) / 2 + 0.01
    elif m < 1.7:
        w = 720 * m / 1280; sc.render.use_border = True; sc.render.use_crop_to_border = False
        sc.render.border_min_y, sc.render.border_max_y = 0, 1; sc.render.border_min_x, sc.render.border_max_x = (1 - w) / 2 - 0.01, (1 + w) / 2 + 0.01
out = a.out or os.path.join(ROOT, "renders", a.shot + ("_preview" if a.preview else ""))
os.makedirs(out, exist_ok=True)
print(f"BUILD {a.shot} {time.time()-t_start:.1f}s frames={S.frames}", flush=True)
if a.stills:
    for tt in a.stills.split(","):
        fr = S.f(float(tt)); fr += (fr + 1) % 2  # odd frames only
        sc.frame_set(fr); sc.render.filepath = os.path.join(out, f"still_{a.shot}_{fr:04d}.png")
        t0 = time.time(); bpy.ops.render.render(write_still=True); print(f"STILL {fr} {time.time()-t0:.1f}s", flush=True)
    sys.exit(0)
for fr in range(1, S.frames + 1, 2):
    p = os.path.join(out, f"f_{fr:04d}.png")
    if os.path.exists(p): continue
    if time.time() - t_start > a.max_seconds: print("TIME LIMIT", flush=True); sys.exit(3)
    sc.frame_set(fr); sc.render.filepath = p + ".tmp.png"
    t0 = time.time(); bpy.ops.render.render(write_still=True); os.replace(p + ".tmp.png", p)
    print(f"FRAME {a.shot} {fr}/{S.frames} {time.time()-t0:.1f}s", flush=True)
print("SHOT DONE", a.shot, flush=True)

# Look-dev stills. Usage: lookdev.py <view> <out.png> [samples] [scale%]
import sys, os, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
import bpy
from mathutils import Vector
import stain, characters as C
view, out = sys.argv[1], sys.argv[2]
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 16; pct = int(sys.argv[4]) if len(sys.argv) > 4 else 100
VIEWS = {  # view: (scene, shot, cam loc, look at, lens, fstop)
    "act1_wide": (1, "1C", (2.6, -2.4, 1.55), (-0.3, 0.6, 0.95), 24, 4.0),
    "act2_wide": (6, "6B", (2.6, -2.4, 1.55), (-0.3, 0.6, 0.95), 24, 2.8),
    "martin_cu": (1, "1C", (-0.45, 0.2, 1.3), (-0.55, 1.32, 1.22), 50, 2.8),
    "do_cu": (1, "1C", (0.45, 0.75, 1.25), (0.55, -0.52, 1.15), 50, 2.8),
    "act4_cu":   (9, "9E", (-0.55, -0.05, 1.22), (-0.55, 1.32, 1.22), 85, 1.8),
    "hall_empty":(0, "0A", (1.2, -1.2, 1.5), (1.2, -8, 1.15), 35, 4.0),
    "hall_body": (9, "9A", (1.2, -1.2, 1.5), (1.2, -8, 1.15), 35, 4.0),
    "overhead":  (0, "0B", (0, 0.42, 1.82), (0, 0.42, 0), 24, 4.0),
}
sn, shot, cl, ct, lens, fs = VIEWS[view]
stain.reset(); st = stain.continuity(sn, shot)
if view == "overhead": st["wine_stain"] = False; st["blood_drops"] = False
stain.build_set(st); stain.build_lights(st)
pups = {}
if view not in ("hall_empty", "hall_body", "overhead"):
    for n in ("martin", "dao", "andy", "do"):
        p = C.build(n, st); (x, y), f = stain.SEATS[n]
        p.arm.location = (x, y + (0.0), 0); p.arm.rotation_euler.z = math.atan2(f[0], -f[1])
        # seat: move puppet back so hips sit on the seat center
        C.apply_pose(p, C.spec_of("sit_lap" if n == "dao" else "sit"), 1); pups[n] = p
sc = bpy.context.scene
bpy.ops.object.camera_add(location=cl); cam = bpy.context.active_object; sc.camera = cam
d = Vector(ct) - Vector(cl); cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cam.data.lens = lens; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fs; cam.data.dof.focus_distance = d.length
cam.data.clip_start = 0.05
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 8
sc.cycles.sample_clamp_indirect = 4; sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -0.7
sc.render.resolution_x, sc.render.resolution_y = 1280, 720; sc.render.resolution_percentage = pct
sc.render.filepath = out; sc.frame_set(1)
t = time.time(); bpy.ops.render.render(write_still=True); print(f"RENDER {view} {time.time()-t:.1f}s")

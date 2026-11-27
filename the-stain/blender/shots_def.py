# Every shot of THE STAIN. build(shot_id) -> anim.Shot, fully keyed and ready to render.
import math, bpy
import numpy as np
from mathutils import Vector, Euler, Matrix
import stain, anim, characters as C
from anim import Shot, key_obj
from characters import D, DT, E

SHOTS = {}
def shot(sid):
    def deco(fn): SHOTS[sid] = fn; return fn
    return deco
def build(sid):
    S = SHOTS[sid]()
    if S.cam is None: S.bake(fstop=getattr(S, "fstop", 4.0))
    return S

TC = Vector((0, 0.4, 0.95))
WIDE = ((1.3, -2.65, 1.75), (-0.3, 0.6, 0.9))
OBJ = lambda n: bpy.data.objects[n]
SEAT = {k: Vector(v[0] + (0,)) for k, v in stain.SEATS.items()}
HALL0 = ((1.2, -1.2, 1.5), (1.2, -8.0, 0.45), 35)   # the hallway frame (0A = 9A)
OVER = ((0.0, 0.42, 1.80), (0.0, 0.40, 0.0), 24)    # overhead table (0B = 10E)

# ------------------------------------------------------------------ helpers
def fdir(ang): return Vector((math.sin(ang), -math.cos(ang), 0))
def setup(S, t0, t1, loc0, tg0, lens, loc1=None, tg1=None, lens1=None):
    """Camera setup from t0 (hard cut) moving to loc1/tg1 by t1."""
    S.camera(t0, loc0, tg0, lens, ease=0.0001)
    S.camera(t1, loc1 or loc0, tg1 if tg1 is not None else tg0, lens1 or lens, ease=1.0)
def blocked(S, n, a, b, t):
    """Is the line a->b blocked by another character (head sphere or body column)?"""
    from mathutils.geometry import intersect_point_line
    for m in S.p:
        if m == n or S.p[m].arm.hide_render: continue
        hm = S.head_pos(m, t); root = S.root_at(m, t)
        for c, r in ((hm, 0.24), (hm.lerp(root, 0.35), 0.24), (hm.lerp(root, 0.6), 0.22)):
            q, u = intersect_point_line(c, a, b)
            if 0.0 < u < 1.0 and (q - c).length < r: return True
    return False
def face_cam(S, n, t, ang=0.0, dist=1.5, dz=0.02, tdz=0.0, side=0.0, avoid=True):
    """Camera position looking at n's face from 'ang' degrees off their facing direction (dodges other people)."""
    h = S.head_pos(n, t); f = S.face[n].at(t, lambda a, b, u: anim.lerp(a, b, u)) or 0.0
    cands = [ang] + ([ang + s * k for k in (12, 24, 36, 48, 60) for s in (1, -1)] if avoid else [])
    for i, a in enumerate(cands):
        d = fdir(f + math.radians(a)); sidev = Vector((-d.y, d.x, 0))
        loc = h + d * dist + Vector((0, 0, dz)) + sidev * side
        if not avoid or not blocked(S, n, loc, h, t): break
    return loc, h + Vector((0, 0, tdz))
def cu(S, t0, t1, n, ang=0, dist=1.5, lens=85, dz=0.02, tdz=0.0, push=0.0, side=0.0):
    loc, tg = face_cam(S, n, t0, ang, dist, dz, tdz, side)
    loc1, _ = face_cam(S, n, t0, ang, dist - push, dz, tdz, side)
    setup(S, t0, t1, loc, n, lens, loc1, n)
def chair(n): return OBJ(f"chair_{n}")
def push_chair(S, n, t, amount=0.45, back=True):
    c = chair(n); (x, y), f = stain.SEATS[n]; d = Vector((f[0], f[1], 0))
    p0 = Vector((x, y, 0)); p1 = p0 - d * amount
    def ev(fr, a=p0, b=p1):
        key_obj(c, max(1, fr - 8), location=a if back else b); key_obj(c, fr, location=b if back else a)
    S.at(t, ev)
def stand_up(S, n, t, dur=0.5, pose="stand"):
    S.key(n, t, None); S.key(n, t + dur, pose, ease=0.8); push_chair(S, n, t + dur * 0.6)
def sit_down(S, n, t, dur=0.6, pose=None):
    S.key(n, t, "stand"); S.key(n, t + dur, pose or "sit", ease=0.8); S.key(n, t + dur, loc=tuple(SEAT[n]))
    push_chair(S, n, t + dur * 0.3, back=False)
def stand_at_seat(S, n, t=0.0, pose="stand"):
    S.key(n, t, pose); c = chair(n); (x, y), f = stain.SEATS[n]
    c.location = Vector((x, y, 0)) - Vector((f[0], f[1], 0)) * 0.45
def aim_pose(S, n, target, t, base="sit", hand="R", both=False):
    """Pose dict pointing an arm (or both) at a world target."""
    root = S.root_at(n, t); ang = S.face[n].at(t, lambda a, b, u: anim.lerp(a, b, u)) or 0.0
    sp = dict(C.POSES[base]); drop = sp.get("_hips_drop", 0)
    sh = Vector((-0.2 if hand == "R" else 0.2, 0, 1.36 - drop)) * C.LOOK[n]["scale"]
    R = Matrix.Rotation(ang, 3, "Z")
    d = R.inverted() @ (Vector(target) - (root + R @ sh)); d.normalize()
    for h in (("R", "L") if both else (hand,)):
        sp[f"upper_arm.{h}"] = ("d", d.copy()); sp[f"forearm.{h}"] = ("d", d.copy()); sp[f"hand.{h}"] = ("d", d.copy())
    return sp
def flicker(S, t0, t1, names=("key",), bulb="pendant_bulb", seed=1, depth=0.9):
    import random; r = random.Random(seed)
    lights = [S.lights[n] for n in names if n in S.lights]
    base = {l.name: l.data.energy for l in lights}
    bm = OBJ(bulb).active_material.node_tree.nodes.get("Emission") if bulb in bpy.data.objects else None
    b0 = bm.inputs["Strength"].default_value if bm else 0
    fr0, fr1 = S.f(t0), S.f(t1)
    for fr in range(1, S.frames + 1, 2):
        on = not (fr0 <= fr <= fr1 and r.random() < 0.5)
        k = 1.0 if on else 1 - depth * r.uniform(0.6, 1.0)
        for l in lights: l.data.energy = base[l.name] * k; l.data.keyframe_insert("energy", frame=fr)
        if bm: bm.inputs["Strength"].default_value = b0 * k; bm.inputs["Strength"].keyframe_insert("default_value", frame=fr)
def vis(o, t_on=None, t_off=None, S=None):
    if isinstance(o, str): o = OBJ(o)
    if t_on is not None:
        S.at(0, lambda fr: stain.key_vis(o, 1, False)); S.at(t_on, lambda fr: stain.key_vis(o, fr, True))
    if t_off is not None:
        S.at(t_off, lambda fr: stain.key_vis(o, fr, False))
def path_key(S, o, keys):
    """keys: [(t, loc, rot)]"""
    def ev(fr, o=o, keys=keys):
        for t, l, r in keys:
            f = S.f(t); o.location = l
            if r is not None: o.rotation_euler = r
            o.keyframe_insert("location", frame=f)
            if r is not None: o.keyframe_insert("rotation_euler", frame=f)
    S.at(0, ev)
def nose_spurt(S, t, n="martin", back=0.0):
    """Short blood spray from the nose at the moment of the hit, so the injury reads instantly."""
    m = stain.clay("blood_spray", (0.05, 0.0, 0.004), 0.3, 0)
    h = S.head_pos(n, t); ang = S.face[n].at(t, lambda a, b, u: anim.lerp(a, b, u)) or 0.0
    fwd = fdir(ang); side = Vector((-fwd.y, fwd.x, 0)); nose = h + fwd * 0.16 + Vector((0, 0, -0.06))
    for i in range(9):
        d = stain.sphere(f"spurt{i}", 0.011 + 0.003 * (i % 3), (0, 0, -5), m)
        v = fwd * (0.12 + 0.03 * (i % 4)) + side * (0.05 * ((i % 5) - 2)) + Vector((0, 0, 0.05 - 0.02 * (i % 3))) - fwd * back
        keys = [(0, Vector((0, 0, -5)), None), (t - 0.02, Vector((0, 0, -5)), None)]
        for k in range(1, 7):
            u = k * 0.06; keys.append((t + u, nose + v * (u / 0.18) + Vector((0, 0, -1.6 * u * u)), None))
        keys.append((t + 0.4, Vector((0, 0, -5)), None)); path_key(S, d, keys)

def laugh(S, names, t0, t1, amt=0.7):
    for n in names:
        if n in S.p: S.mouth(n, t0, t1, amt); S.set_expr(n, t0, 0, 0.5); S.set_expr(n, t1 + 0.3, 0, 0.0)

# ---- props
def purse(loc=(0, 0, 0)):
    m = stain.clay("purse", (0.04, 0.012, 0.015), 0.35, 0.03)
    root = bpy.data.objects.new("purse", None); stain.link(root); root.location = loc
    b = stain.box("purse_body", (0.24, 0.08, 0.16), (0, 0, 0.08), m, 0.025); b.parent = root
    s = stain.box("purse_clasp", (0.05, 0.085, 0.02), (0, 0, 0.15), stain.clay("brass", (0.55, 0.42, 0.2), 0.3, 0, 0.9)); s.parent = root
    return root
DAO_LAP = Vector((-0.55, -0.27, 0.6))
def ring_box(loc, open_t=None, S=None):
    m = stain.clay("ringbox", (0.35, 0.03, 0.06), 0.6, 0.05)
    root = bpy.data.objects.new("ringbox_held", None); stain.link(root); root.location = loc
    b = stain.box("rb_base", (0.06, 0.06, 0.03), (0, 0, 0.015), m, 0.006); b.parent = root
    lid_p = bpy.data.objects.new("rb_lidp", None); stain.link(lid_p); lid_p.parent = root; lid_p.location = (0, 0.03, 0.03)
    lid = stain.box("rb_lid", (0.06, 0.06, 0.018), (0, -0.03, 0.009), m, 0.006); lid.parent = lid_p
    ring = bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.003, location=(0, 0, 0.04), rotation=(math.pi / 2, 0, 0))
    rg = bpy.context.active_object; rg.data.materials.append(stain.clay("gold", (0.9, 0.65, 0.25), 0.2, 0, 1.0)); rg.parent = root
    gem = stain.sphere("rb_gem", 0.006, (0, 0, 0.054), stain.emission_only("gem", (0.8, 0.9, 1.0), 3)); gem.parent = root
    if open_t is not None:
        S.at(0, lambda fr: key_obj(lid_p, 1, rotation_euler=(0, 0, 0)))
        S.at(open_t, lambda fr: (key_obj(lid_p, fr - 2, rotation_euler=(0, 0, 0)), key_obj(lid_p, fr, rotation_euler=(-1.8, 0, 0))))
    return root
def champagne():
    m = stain.clay("champ", (0.08, 0.2, 0.1), 0.15, 0)
    root = bpy.data.objects.new("champ_held", None); stain.link(root)
    a = stain.cyl("ch_b", 0.04, 0.26, (0, 0, 0.0), m); a.parent = root
    b = stain.cyl("ch_n", 0.015, 0.1, (0, 0, 0.18), m); b.parent = root
    return root
def cake_candles(S, out_t=None):
    wax = stain.clay("wax2", (0.95, 0.85, 0.9), 0.5, 0); flames = []
    for i in range(5):
        a = i * 1.256; x, y = 0.55 + 0.07 * math.cos(a), 0.22 + 0.07 * math.sin(a); z = stain.TABLE_TOP + 0.122
        stain.cyl(f"cc{i}", 0.005, 0.06, (x, y, z + 0.03), wax)
        fl = stain.sphere(f"ccf{i}", 0.007, (x, y, z + 0.068), stain.emission_only("flame", stain.CANDLE_FLAME, 25), scale=(1, 1, 1.8)); fl.visible_shadow = False
        flames.append(fl)
    bpy.ops.object.light_add(type="POINT", location=(0.55, 0.22, stain.TABLE_TOP + 0.25)); L = bpy.context.active_object; L.name = "cake_light"
    L.data.energy = 9; L.data.color = stain.K1800; L.data.shadow_soft_size = 0.03
    if out_t is not None:
        for fl in flames: vis(fl, t_off=out_t, S=S)
        S.at(out_t, lambda fr: (L.data.keyframe_insert("energy", frame=fr - 2), setattr(L.data, "energy", 0), L.data.keyframe_insert("energy", frame=fr)))
def scratches(S, t_on=None):
    m = stain.clay("scratch", (0.3, 0.01, 0.02), 0.4, 0); objs = []
    pp = S.p["martin"]
    for k in range(3):
        o = stain.capsule(f"scr{k}", 0.004, 0.06, m, loc=(0.2 + (k - 1) * 0.014, -0.045, 0.9 + k * 0.012), rot=(0.0, 0.2, 0))
        o.parent = pp.arm; o.parent_type = "BONE"; o.parent_bone = "forearm.L"
        b = pp.arm.data.bones["forearm.L"]; o.matrix_parent_inverse = (b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()
        objs.append(o)
        if t_on is not None:
            S.at(0, lambda fr, o=o: key_obj(o, 1, scale=(1, 1, 0.01)))
            S.at(t_on + k * 0.25, lambda fr, o=o: (key_obj(o, fr - 2, scale=(1, 1, 0.01)), key_obj(o, fr + 8, scale=(1, 1, 1))))
    return objs
def palm_cut(S, t_on=None):
    pp = S.p["andy"]; m = stain.clay("cutm", (0.25, 0.0, 0.01), 0.3, 0)
    o = stain.capsule("palm_cut", 0.004, 0.055, m, loc=(-0.19, -0.0, 0.79), rot=(0, 0, 0))
    o.parent = pp.arm; o.parent_type = "BONE"; o.parent_bone = "hand.R"
    b = pp.arm.data.bones["hand.R"]; o.matrix_parent_inverse = (b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()
    bead = stain.sphere("palm_bead", 0.008, (-0.188, -0.0, 0.81), m); bead.parent = pp.arm; bead.parent_type = "BONE"; bead.parent_bone = "hand.R"
    bead.matrix_parent_inverse = o.matrix_parent_inverse.copy()
    if t_on is not None:
        S.at(0, lambda fr: (key_obj(o, 1, scale=(1, 1, 0.01)), key_obj(bead, 1, scale=(0.01,) * 3)))
        S.at(t_on, lambda fr: (key_obj(o, fr, scale=(1, 1, 0.01)), key_obj(o, fr + 24, scale=(1, 1, 1)), key_obj(bead, fr + 24, scale=(0.01,) * 3), key_obj(bead, fr + 48, scale=(1, 1, 1))))
    return o
def body(S):
    """The future: Do's body in the hallway, half covered by the white tablecloth."""
    if "do" not in C.LOOK: return
    b = C.build("do", {}, suffix="_body")
    spec = dict(C.POSES["lying"]); spec["upper_arm.L"] = D(0.55, 0.1, -1); spec["forearm.L"] = D(0.5, -0.3, -1); spec["upper_arm.R"] = D(-0.2, 0, -1)
    spec["head"] = E(0, 0, 25)
    C.apply_pose(b, spec, 1)
    root = stain.BODY_POS + Vector((0, 0.95, 0.0))
    b.arm.location = root + Vector((0, 0, 0.14)); b.arm.rotation_euler = (-math.pi / 2 * 0.98, 0, math.pi)
    for fc in []: pass
    for o in [b.arm] + [c for c in bpy.data.objects if c.name.startswith("do_body")]: pass
    bpy.context.view_layer.update()
    # drape: ray-cast the body from above, blur, cut a slot so the left hand sticks out
    nx, ny = 60, 90; x0, x1 = 0.98, 1.78; y0, y1 = stain.BODY_POS.y - 1.05, stain.BODY_POS.y + 0.7
    dg = bpy.context.evaluated_depsgraph_get(); H = np.zeros((ny + 1, nx + 1))
    hide = []
    for i in range(ny + 1):
        for j in range(nx + 1):
            x = x0 + (x1 - x0) * j / nx; y = y0 + (y1 - y0) * i / ny
            ok, loc, nrm, idx, ob, mtx = bpy.context.scene.ray_cast(dg, Vector((x, y, 0.9)), Vector((0, 0, -1)), distance=0.89)
            H[i, j] = loc.z if ok and ob.name.startswith("do_body") else 0.0
    from scipy.ndimage import gaussian_filter, maximum_filter
    H = gaussian_filter(maximum_filter(H, 7), 3) + 0.012
    edge = np.minimum(np.minimum(np.arange(nx + 1)[None, :], nx - np.arange(nx + 1)[None, :]), np.minimum(np.arange(ny + 1)[:, None], ny - np.arange(ny + 1)[:, None]))
    H = np.maximum(H * np.clip(edge / 6.0, 0.15, 1.0), 0.004)
    verts = [(x0 + (x1 - x0) * j / nx, y0 + (y1 - y0) * i / ny, H[i, j]) for i in range(ny + 1) for j in range(nx + 1)]
    faces = [(i * (nx + 1) + j, i * (nx + 1) + j + 1, (i + 1) * (nx + 1) + j + 1, (i + 1) * (nx + 1) + j) for i in range(ny) for j in range(nx)]
    cl = stain.mesh_obj("body_cloth", verts, faces, stain.tex_mat("bodycloth", "body_cloth.png", 0.85), smooth=True)
    uv = cl.data.uv_layers.new()
    for li, l in enumerate(cl.data.loops):
        v = verts[l.vertex_index]; uv.data[li].uv = ((v[0] - x0) / (x1 - x0), (v[1] - y0) / (y1 - y0))
    return b
def chest_point(): return Vector((1.37, stain.BODY_POS.y - 0.1, 0.3))

def act4(S):
    body(S)

# ================================================================== SCENE 0
@shot("0A")
def s_0A():
    S = Shot("0A", cast=("dao",)); S.key("dao", 0, "stand", loc=(-1.0, 1.6, 0)); S.p["dao"].arm.hide_render = True
    for o in bpy.data.objects:
        if o.name.startswith("dao_"): o.hide_render = True
    setup(S, 0, S.dur, *HALL0)
    flicker(S, 2.3, 2.9, names=("hall",), bulb="hall_bulb", seed=3)
    return S

@shot("0B")
def s_0B():
    S = Shot("0B", cast=("dao",)); S.fstop = 5.6; S.exposure = -3.0
    setup(S, 0, S.dur, *OVER)
    S.key("dao", 0, "stand", loc=(0.0, -1.0, 0), face=(0, 1))
    S.key("dao", 1.6, "stand", loc=(0.0, -0.42, 0)); S.key("dao", 2.4, {**C.POSES["stand_reach"], "upper_arm.L": D(0.1, -1, -0.3), "forearm.L": D(0, -1, -0.35)})
    S.key("dao", 4.0, {**C.POSES["stand_reach"], "spine": E(42, 0, 8), "upper_arm.L": D(0.2, -1, -0.25), "forearm.L": D(0.3, -1, -0.3), "upper_arm.R": D(-0.3, -1, -0.25), "forearm.R": D(-0.2, -1, -0.3)})
    S.key("dao", 5.6, {**C.POSES["stand_reach"], "spine": E(42, 0, -8), "upper_arm.L": D(0.4, -1, -0.25), "forearm.L": D(0.2, -1, -0.3), "upper_arm.R": D(0.0, -1, -0.25), "forearm.R": D(-0.4, -1, -0.3)})
    S.key("dao", 7.5, "stand", loc=(0.0, -0.9, 0))
    cl = OBJ("tablecloth")
    path_key(S, cl, [(0, cl.location + Vector((0.1, -0.05, 0.85)), (0.04, -0.03, 0.08)), (0.5, cl.location + Vector((0.05, 0, 0.45)), (-0.02, 0.02, 0.03)),
                     (0.9, cl.location + Vector((0, 0, 0.08)), (0, 0, 0.01)), (1.3, cl.location.copy(), (0, 0, 0))])
    for n in ("candle0", "candle1", "cholder0", "cholder1", "flame0", "flame1", "vase", "wine_bottle", "wine_neck", "champ", "champ_neck") + tuple(o.name for o in bpy.data.objects if o.name.startswith(("plate_", "glass_", "flower", "vase_"))):
        if n in bpy.data.objects: stain.set_vis(OBJ(n), False)
    for n in ("candle_light0", "candle_light1"):
        if n in bpy.data.objects: OBJ(n).data.energy = 0
    return S

# ================================================================== SCENE 1
@shot("1A")
def s_1A():
    S = Shot("1A"); S.fstop = 4.0
    setup(S, 0, S.dur, (-0.9, 3.15, 1.62), (0.45, -0.3, 0.95), 24, (-0.6, 2.55, 1.52), (0.4, -0.3, 0.95))
    laugh(S, ("martin", "dao", "andy", "do"), 0.0, 1.6, 0.5); laugh(S, ("martin", "dao", "andy", "do"), 6.4, 8.6, 0.7)
    S.key("do", 2.8, "sit"); S.key("do", 3.3, aim_pose(S, "do", (0.25, 0.1, 0.8), 3.3)); S.key("do", 4.0, "sit_glass")
    ph = stain.make_phone("do_skip_phone", (0.25, 0.1, stain.TABLE_TOP + 0.004), (0, 0, 0.3), screen="phone_meme.png")
    S.look("do", (0.25, 0.1, 0.8), 2.9, 3.5)
    return S

@shot("1B")
def s_1B():
    S = Shot("1B"); S.fstop = 2.0
    ph = stain.make_phone("meme_phone", (-0.5, -0.05, 1.02), (math.radians(62), 0, math.radians(180)), screen="phone_meme.png")
    setup(S, 0, S.dur, (-0.5, 0.2, 1.24), (-0.5, -0.05, 1.03), 50, (-0.5, 0.16, 1.2), (-0.5, -0.05, 1.03))
    S.focus_on(0, (-0.5, -0.05, 1.03))
    S.key("dao", 0, {**C.POSES["sit"], "upper_arm.R": D(-0.1, -0.6, -0.8), "forearm.R": D(0.2, -1, 0.6), "upper_arm.L": D(0.1, -0.6, -0.8), "forearm.L": D(-0.2, -1, 0.6)})
    laugh(S, ("dao",), 0.5, 3.5, 0.6)
    return S

@shot("1C")
def s_1C():
    S = Shot("1C")
    setup(S, 0, S.dur, (-2.55, 0.35, 1.5), (0.35, 0.4, 1.05), 35, (-2.4, 0.35, 1.48))
    ph = stain.make_phone("dao_phone", (0, 0, 0), (0, 0, 0), screen="phone_meme.png")
    S.key("dao", 0, "sit_glass"); S.hold(ph, "dao", "R", 0, 2.2)
    S.key("dao", 2.0, "sit_point"); S.key("do", 2.2, "sit_point"); S.hold(ph, "do", "R", 2.3, S.dur)
    S.key("do", 3.0, "sit_glass")
    for n in ("martin", "dao", "andy", "do"):
        S.mouth(n, 0.1, 0.75, 0.5 if n != "do" else 0.9); S.set_expr(n, 0, 0, 0.6); S.set_expr(n, 2.5, 0, 0.2)
    S.mouth("do", 5.0, 7.5, 0.9); S.mouth("martin", 5.1, 7.0, 0.6); S.mouth("andy", 5.2, 6.8, 0.5)
    S.look("dao", "do", 0, 2.2); S.look("martin", "do", 0, 0.7)
    return S

@shot("1D")
def s_1D():
    S = Shot("1D"); S.fstop = 2.8
    ch = champagne(); S.key("do", 0, {**C.POSES["sit"], "upper_arm.R": D(-0.2, -0.6, -0.6), "forearm.R": D(-0.3, -0.4, 0.9), "upper_arm.L": D(0.2, -0.7, -0.5), "forearm.L": D(-0.4, -0.6, 0.6)})
    S.hold(ch, "do", "R", 0, S.dur, offset=(0, -0.05, 0), rot=(0, 0, 0))
    for n in ("champ", "champ_neck"): stain.set_vis(OBJ(n), False)
    cork = stain.cyl("cork", 0.011, 0.025, (0, 0, -5), stain.clay("corkm", (0.55, 0.4, 0.25), 0.8, 0.05))
    head = S.head_pos("martin", 1.1) + Vector((0.22, -0.05, 0.12))
    start = S.head_pos("do", 1.0) + Vector((-0.05, 0.25, 0.12))
    path_key(S, cork, [(0.95, Vector((0, 0, -5)), None), (1.0, start, None), (1.1, start.lerp(head, 0.55), None), (1.18, head, None), (1.25, stain.CORK_SPOT + Vector((0, -0.02, 0)), None), (1.4, stain.CORK_SPOT + Vector((0.05, -0.25, -0.6)), None), (1.6, Vector((-1.2, 3.0, 0.02)), None)])
    vis("cork_scuff", t_on=1.25, S=S)
    setup(S, 0, 1.12, *face_cam(S, "do", 0, 25, 1.4, 0.0), 50)
    S.camera(1.12, (-1.0, 2.75, 1.4), stain.CORK_SPOT, 50, ease=0.0001); S.camera(2.3, (-1.08, 2.95, 1.41), stain.CORK_SPOT, 50, ease=1.0)
    S.focus_on(1.12, stain.CORK_SPOT); S.focus_on(2.3, "dao")
    setup(S, 2.3, S.dur, (1.9, 1.9, 1.5), (-0.4, -0.1, 1.0), 35)
    laugh(S, ("martin", "andy", "do"), 1.6, 2.5, 0.6); S.look("martin", stain.CORK_SPOT, 1.3, 3.6); S.look("dao", stain.CORK_SPOT, 1.3, 2.5)
    S.key("martin", 1.15, {**C.POSES["sit"], "spine": E(-12, 0, 0), "head": E(-10, 0, 0)}, ease=0.2); S.key("martin", 1.8, "sit")
    return S

@shot("1E")
def s_1E():
    S = Shot("1E"); S.fstop = 2.8
    stand_at_seat(S, "do", 0, "stand")
    gl = stain.make_wineglass("toast_glass", (0, 0, 0), stain.clay("wineglass", (0.85, 0.9, 0.95), 0.05, 0), stain.clay("wine", (0.3, 0.02, 0.05), 0.1, 0))
    S.key("do", 0, "stand_toast"); S.hold(gl, "do", "R", 0, S.dur, offset=(0, 0.02, 0))
    if "glass_do" in bpy.data.objects: stain.set_vis(OBJ("glass_do"), False)
    L = S.lines
    loc, tg = face_cam(S, "do", 0, 15, 2.2, -0.35, 0); setup(S, 0, L[0]["end"], loc, "do", 35)
    S.look("do", "martin", 1.8, 2.8); S.look("do", "dao", 3.0, 5.3); S.look("do", "andy", 7.7, 10.4)
    cu(S, 5.35, 6.5, "martin", 0, 1.6, 85); S.set_expr("martin", 5.3, 0, 0); S.set_expr("martin", 5.6, 0.9, 0, 0.1); S.set_expr("martin", 6.6, 0.2, 0)
    S.look("martin", "do", 5.3, 6.5)
    cu(S, 6.5, 7.65, "dao", 0, 1.5, 85); S.look("dao", (-0.55, 0.3, 0.78), 6.6, 7.6); S.set_expr("dao", 6.6, -0.5, 0)
    loc, tg = face_cam(S, "do", 7.7, 15, 2.2, -0.35, 0); setup(S, 7.65, 10.6, loc, "do", 35)
    setup(S, 10.6, 12.2, WIDE[0], WIDE[1], 24)
    for n in ("martin", "dao", "andy"):
        S.key(n, 10.5, "sit_glass"); S.key(n, 12.0, "sit")
    laugh(S, ("martin", "dao", "do"), 11.3, 13.0, 0.6)
    cu(S, 12.2, S.dur, "andy", 0, 1.6, 85, push=0.15); S.set_expr("andy", 12.0, 0.4, 0); S.look("andy", "do", 11.4, 20)
    S.gesture["andy"] = 0.0
    return S

@shot("1F")
def s_1F():
    S = Shot("1F"); S.fstop = 2.8
    pu = purse()
    path_key(S, pu, [(0, Vector((-0.33, -0.8, 0.55)), (0.2, 0, 0)), (0.6, Vector((-0.33, -0.8, 0.55)), (0.2, 0, 0)), (0.8, Vector((-0.36, -0.82, 0.0)), (1.4, 0, 0.3)),
                     (2.9, Vector((-0.36, -0.82, 0.0)), (1.4, 0, 0.3)), (3.5, Vector((-0.4, -0.55, 0.35)), (0.3, 0, 0)), (4.0, DAO_LAP, (0, 0, 0))])
    S.key("dao", 2.6, "sit"); S.key("dao", 3.2, {**C.POSES["sit"], "spine": E(25, 0, 25), "upper_arm.L": D(0.3, 0.2, -1), "forearm.L": D(0.2, 0.3, -1)}); S.key("dao", 4.1, "sit_lap")
    S.look("dao", (-0.36, -0.82, 0.0), 0.8, 1.5); S.look("andy", "dao", 0.8, 3.5)
    loc, tg = face_cam(S, "dao", 0, -25, 1.9, -0.1); setup(S, 0, S.dur, loc, "dao", 50, loc + Vector((0, -0.15, 0)))
    laugh(S, ("dao",), 3.8, 5.0, 0.3)
    return S

@shot("1G")
def s_1G():
    S = Shot("1G"); S.fstop = 2.0
    S.key("martin", 0, "sit"); S.key("martin", 0.4, "sit_pocket", ease=0.6)
    tg = ("bone", "martin", "hand.R", (0, 0, 0.05))
    h = S.head_pos("martin", 0) + Vector((0, 0, -0.4))
    setup(S, 0, S.dur, h + Vector((-0.5, -1.9, 0.1)), tg, 85, h + Vector((-0.45, -1.75, 0.1))); S.focus_on(0, tg)
    S.look("martin", "dao", 0, 2)
    return S

@shot("1H")
def s_1H():
    S = Shot("1H"); S.fstop = 2.0
    st = OBJ("wine_stain").location
    setup(S, 0, 1.6, st + Vector((0.12, -0.5, 0.35)), st, 50, st + Vector((0.1, -0.42, 0.3)))
    S.key("martin", 0.6, "sit"); S.key("martin", 1.2, aim_pose(S, "martin", st, 1.2, base="sit"), ease=0.6)
    S.key("martin", 1.25, None); S.key("martin", 1.5, {**C.POSES["sit"], "spine": E(30, 0, 0), **{k: v for k, v in aim_pose(S, "martin", st, 1.2).items() if "arm" in k or "hand" in k}})
    S.key("martin", 2.2, "sit_glass"); S.key("martin", 4.0, "sit")
    S.set_expr("martin", 1.4, 0.7, 0)
    S.look("martin", st, 0.5, 2.0)
    cu(S, 1.6, 7.0, "martin", -20, 1.8, 50); S.focus_on(1.6, "martin"); S.focus_on(3.8, "andy")
    bot = OBJ("wine_bottle"); neck = OBJ("wine_neck")
    S.key("andy", 0, {**C.POSES["sit"], "upper_arm.R": D(-0.3, -0.6, -0.7), "forearm.R": D(0.1, -1, 0.3), "upper_arm.L": D(0.2, -0.6, -0.7), "forearm.L": D(-0.2, -1, 0.3)})
    S.look("andy", "martin", 3.9, 4.9)
    setup(S, 7.0, S.dur, (1.9, 1.9, 1.5), (-0.2, 0.3, 1.0), 35)
    S.look("dao", st, 6.5, 10); S.look("martin", st, 7.5, 10)
    return S

@shot("1I")
def s_1I():
    S = Shot("1I"); S.fstop = 2.8
    cake_candles(S, out_t=6.1)
    setup(S, 0, 3.0, (-2.2, 2.6, 1.7), (0.4, -0.2, 0.95), 28, (-2.0, 2.4, 1.65))
    for n in ("martin", "dao", "andy"): S.mouth(n, 0.8, 2.7, 0.7); S.look(n, "do", 0, 4.5)
    S.mouth("do", 0.8, 2.7, 0.35); S.set_expr("do", 0.5, -0.2, 0.4)
    loc, tg = face_cam(S, "do", 3.0, 0, 1.35, -0.05); setup(S, 3.0, 8.6, loc, "do", 85, loc + (tg - loc) * 0.12)
    S.eyes_closed("do", 3.5, 6.0); S.look("do", (0.55, 0.22, 0.88), 3.2, 6.6)
    S.key("do", 5.8, "sit"); S.key("do", 6.0, {**C.POSES["sit"], "spine": E(18, 0, 0)}, ease=0.5); S.key("do", 6.6, "sit")
    S.mouth("do", 6.0, 6.3, 0.4)
    setup(S, 8.6, S.dur, (2.6, 1.9, 1.5), (-0.3, -0.2, 0.95), 35); S.look("andy", "do", 7.3, 9)
    S.set_expr("andy", 7.3, 0.3, 0)
    laugh(S, ("martin", "dao", "do"), 8.5, 10.5, 0.6)
    return S

@shot("1J")
def s_1J():
    S = Shot("1J")
    setup(S, 0, S.dur, (-2.55, 0.35, 1.5), (0.35, 0.4, 1.05), 35, (-2.35, 0.35, 1.48))
    L = S.lines
    for n in ("martin", "dao", "andy"):
        S.key(n, L[1]["start"], None); S.key(n, L[1]["end"] + 0.05, aim_pose(S, n, S.head_pos("do", 7), 7.0), ease=0.3)
        S.key(n, L[2]["start"] + 0.5, "sit"); S.look(n, "do", L[1]["start"], L[2]["end"] + 1)
    laugh(S, ("martin", "dao", "andy", "do"), L[1]["end"] + 0.1, L[2]["start"] - 0.1, 0.8)
    S.key("do", L[2]["start"] - 0.3, "sit_glass"); laugh(S, ("martin", "dao", "andy", "do"), L[2]["end"] + 0.1, S.dur, 0.6)
    return S

@shot("1K")
def s_1K():
    S = Shot("1K"); S.fstop = 2.8
    # FIX: the knock, the fall and the spill are all on screen now (owner note: "we don't see a glass falling")
    laugh(S, ("andy", "do"), 0.3, 1.8, 0.9)
    sit_lean = lambda sp, **k: {**C.POSES["sit"], "spine": E(sp, 0, 0), **k}
    S.key("andy", 0, "sit"); S.key("andy", 0.9, sit_lean(-15), ease=0.5)
    S.key("andy", 1.3, sit_lean(-10, **{"upper_arm.R": D(-0.9, -0.3, 0.35), "forearm.R": D(-0.8, -0.5, 0.5)}), ease=0.4)   # big laughing fling
    S.key("andy", 1.6, sit_lean(28, **{"upper_arm.R": D(0.15, -1, -0.35), "forearm.R": D(0.45, -1, -0.3)}), ease=0.25)    # swipe hits the glass
    S.key("andy", 2.2, sit_lean(20, **{"upper_arm.R": D(0.15, -1, -0.35), "forearm.R": D(0.45, -1, -0.3)}))
    S.key("andy", 2.6, "sit", ease=0.6)
    S.set_expr("andy", 1.65, -0.5, 0.7, 0.1)
    g = OBJ("glass_andy"); g0 = g.location.copy(); st = OBJ("wine_stain").location
    wine = stain.clay("wine_spill", (0.16, 0.004, 0.015), 0.2, 0)
    inglass = stain.cyl("glass_andy_wine", 0.036, 0.03, (0, 0, 0.115), wine); inglass.parent = g; inglass.location = (0, 0, 0.115)
    vis(inglass, t_off=1.8, S=S)
    lie = g0.copy(); lie.z = stain.TABLE_TOP + 0.04
    path_key(S, g, [(0, g0, (0, 0, 0)), (1.6, g0, (0, 0, 0)), (1.7, g0 + Vector((-0.02, 0, 0.005)), (0, -0.55, 0.1)),
                    (1.82, lie + Vector((0, 0, 0.012)), (0, -1.6, 0.25)), (1.9, lie + Vector((0, 0, 0.02)), (0, -1.45, 0.3)), (2.0, lie, (0, -1.5708, 0.35))])
    # the wine: a slow-motion ribbon from the glass mouth to the old stain, then a splash and a fresh puddle on top of it
    mouth = lie + Vector((-0.2, 0.0, 0.0)); b = st + Vector((0, 0, 0.012))
    # continuous ribbon: head and tail of the stream travel along the arc; drops are spread evenly between them, keyed every frame
    N = 70; drops = [stain.sphere(f"wdrop{i}", 0.013, (0, 0, -5), wine, scale=(1.6, 1, 1), seg=12) for i in range(N)]
    arc = lambda u: mouth.lerp(b, u) + Vector((0, 0, 0.14 * math.sin(math.pi * u)))
    cl = lambda x: max(0.0, min(1.0, x))
    def ribbon(fr, drops=drops):
        for d in drops: d.location = (0, 0, -5); d.keyframe_insert("location", frame=1)
        for f in range(S.f(2.05), S.f(3.3) + 1):
            t = f / 24.0; hd = cl((t - 2.1) / 0.6); tl = cl((t - 2.55) / 0.6)
            for i, d in enumerate(drops):
                if hd <= 0 or tl >= 1: d.location = (0, 0, -5)
                else:
                    u = tl + (hd - tl) * i / (N - 1); d.location = arc(u) + Vector((0, 0.004 * math.sin(i * 2.3), 0.003 * math.cos(i * 1.7)))
                d.keyframe_insert("location", frame=f)
    S.at(0, ribbon)
    splash = [stain.sphere(f"wsplash{i}", 0.009, (0, 0, -5), wine) for i in range(10)]
    for i, d in enumerate(splash):
        a = i * 0.628 + 0.2; out = Vector((math.cos(a), math.sin(a), 0)) * (0.08 + 0.03 * (i % 3))
        path_key(S, d, [(0, Vector((0, 0, -5)), None), (2.68, Vector((0, 0, -5)), None), (2.7, b, None),
                        (2.85, b + out * 0.6 + Vector((0, 0, 0.07 + 0.02 * (i % 2))), None), (3.0, b + out, None), (3.02, Vector((0, 0, -5)), None)])
    pud = stain.decal("wine_puddle", "stain_dark.png", 0.36, 0.36, b + Vector((0, 0, 0.001)), rot=(0, 0, 0.4), rough=0.15)
    path_key(S, pud, [(0, Vector((0, 0, -5)), None), (2.68, Vector((0, 0, -5)), None), (2.7, b, None)])
    S.at(0, lambda fr: key_obj(pud, 1, scale=(0.2, 0.2, 1)))
    S.at(2.7, lambda fr: (key_obj(pud, fr, scale=(0.2, 0.2, 1)), key_obj(pud, S.f(3.1), scale=(1.25, 1.15, 1))))
    # cameras: medium on Andy + glass (knock and fall) -> slow-mo side view of the arc -> top-down on the stain -> wide
    setup(S, 0, 2.05, (0.35, 1.15, 1.15), (1.25, 0.35, 1.02), 32, (0.4, 1.1, 1.13), (1.2, 0.35, 0.98)); S.focus_on(0, g0)
    side = (0.5, 1.6, 1.08); setup(S, 2.05, 3.05, side, (0.5, 0.48, 0.84), 32, (0.45, 1.5, 1.04), (0.45, 0.5, 0.82))
    S.focus_on(2.05, (0.5, 0.5, 0.82))
    setup(S, 3.05, 3.7, b + Vector((0.06, -0.45, 0.6)), b, 35, b + Vector((0.05, -0.38, 0.5)), b); S.focus_on(3.05, b)
    setup(S, 3.7, S.dur, (-2.4, 0.4, 1.5), (0.3, 0.4, 1.0), 35, (-2.3, 0.4, 1.48))
    laugh(S, ("martin", "andy", "do"), 3.2, 4.8, 0.7); S.look("dao", b, 3.0, S.dur); S.set_expr("dao", 3.5, 0.2, 0.0)
    return S

# ================================================================== SCENE 2
@shot("2A")
def s_2A():
    S = Shot("2A")
    setup(S, 0, S.dur, WIDE[0], WIDE[1], 24)
    flicker(S, 1.0, 4.6, names=("key", "bounce"), seed=7)
    for n in ("martin", "dao", "andy", "do"):
        S.look(n, (0, 0.4, 1.9), 1.2, 4.8); S.gesture[n] = 0; S.set_expr(n, 1.0, -0.3, 0.6)
    return S

@shot("2B")
def s_2B():
    S = Shot("2B"); S.handheld = 1.0; S.fstop = 2.0
    # FIX: the invisible punch reads as a hit now: wider framing keeps the head in shot, a hard snap on the thud, a blood spray
    cu(S, 0, S.dur, "martin", 8, 2.3, 65, dz=0.05, tdz=0.03)
    S.key("martin", 0, "sit"); S.key("martin", 0.3, "sit")
    S.key("martin", 0.38, {**C.POSES["recoil"], "head": E(-45, 0, 8)}, ease=0.1)
    S.key("martin", 0.7, "recoil", ease=0.5); S.key("martin", 1.4, "sit_napkin", ease=0.4)
    S.set_expr("martin", 0, 0, 0); S.set_expr("martin", 0.38, -0.6, 0.9, 0.1); S.set_expr("martin", 1.3, 0.8, 0.0)
    vis("martin_noseblood", t_on=0.38, S=S); nose_spurt(S, 0.36)
    return S

@shot("2C")
def s_2C():
    S = Shot("2C"); S.handheld = 1.3; S.fstop = 2.8
    eye = S.head_pos("martin", 0) + Vector((0.05, -0.25, 0))
    S.camera(0, eye, "andy", 50, ease=0.0001); S.camera(0.25, eye, "andy", 50, ease=0.3)
    S.camera(S.lines[0]["end"] + 0.1, eye, "andy", 50, ease=0.0001); S.camera(S.lines[0]["end"] + 0.35, eye, "do", 50, ease=1.0)
    S.camera(S.lines[1]["end"] + 0.3, eye, "do", 50, ease=0.0001); S.camera(S.lines[1]["end"] + 0.6, eye, "dao", 50, ease=1.0); S.camera(S.dur, eye, "dao", 50, ease=0.0001)
    S.key("martin", 0, "sit_napkin"); vis("martin_noseblood", t_on=0, S=S)
    for n in ("dao", "andy", "do"): S.set_expr(n, 0, 0.0, 0.5)
    return S

@shot("2D")
def s_2D():
    S = Shot("2D"); S.handheld = 0.8; S.fstop = 2.8
    S.key("martin", 0, "sit_napkin"); S.key("martin", 4.6, "sit_napkin"); S.key("martin", 5.2, "sit_pocket"); S.key("martin", 6.8, "sit_napkin")
    vis("martin_noseblood", t_on=0, S=S); vis("blood_drops", t_on=2.2, S=S)
    loc, tg = face_cam(S, "martin", 0, 15, 2.0, 0.0); setup(S, 0, 2.0, loc, "martin", 50)
    bd = OBJ("blood_drops").location; setup(S, 2.0, 3.6, bd + Vector((0.15, -0.35, 0.3)), bd, 50); S.focus_on(2.0, bd)
    h = S.head_pos("martin", 5) + Vector((0, 0, -0.38)); setup(S, 3.6, 5.6, h + Vector((-0.3, -1.3, 0.05)), h, 85); S.focus_on(3.6, h)
    setup(S, 5.6, S.dur, (-2.5, 0.3, 1.45), (0.3, -0.2, 1.1), 50); S.focus_on(5.6, "dao")
    S.look("dao", "do", 0, S.dur); S.look("do", "martin", 0, S.dur); S.look("andy", "martin", 0, S.dur)
    S.set_expr("martin", 0, 0.6, 0)
    return S

# ================================================================== SCENE 3
@shot("3A")
def s_3A():
    S = Shot("3A"); S.fstop = 2.8
    m = S.head_pos("martin", 0); d = S.head_pos("do", 0)
    back = (m - d).normalized(); side = Vector((-back.y, back.x, 0))
    loc = m + back * 0.6 + side * 0.42 + Vector((0, 0, 0.1)); setup(S, 0, S.dur, loc, "do", 50); S.focus_on(0, "do")
    S.key("martin", 0, "sit_napkin"); vis("martin_noseblood", t_on=0, S=S)
    S.set_expr("do", 0, -0.2, 0.3); S.key("do", 0, {**C.POSES["sit"], "spine": E(-10, 0, 0)})
    return S

@shot("3B")
def s_3B():
    S = Shot("3B"); S.fstop = 2.0
    cu(S, 0, S.dur, "martin", -5, 1.6, 85, dz=-0.12, push=0.15)
    S.key("martin", 0, "sit"); S.set_expr("martin", 0, 0.9, 0); vis("martin_noseblood", t_on=0, S=S); S.look("martin", "do", 0, 2.6)
    S.look("martin", "dao", 2.8, 5)
    return S

@shot("3C")
def s_3C():
    # FIX (owner note: "we don't see the elbow connecting to Martin's nose"): both men lean in over the table corner,
    # Do half-rises and throws his elbow up; we see the contact frame at 1.3 s, then cut to Martin reeling back.
    S = Shot("3C"); S.handheld = 0.9; S.fstop = 4.0
    push_chair(S, "martin", 0.2)
    S.key("martin", 0, "sit"); S.key("martin", 0.45, "stand", ease=0.8)
    S.key("martin", 0.5, loc=tuple(SEAT["martin"]))
    S.key("martin", 1.25, {**C.POSES["lunge"], "spine": E(MS, 0, 0), "head": E(MH, 0, 0)}, loc=ML, face=MF, ease=0.7)
    S.key("martin", 1.36, {**C.POSES["lunge"], "spine": E(MS, 0, 0), "head": E(MH, 0, 0)})
    S.key("martin", 1.4, {**C.POSES["lunge"], "spine": E(MS - 25, 0, 0), "head": E(-45, 0, 0)}, ease=0.2)
    S.key("martin", 1.6, {**C.POSES["recoil"], "head": E(-40, 0, 0)}, loc=(-0.25, 1.4, 0), ease=0.35)
    S.key("martin", 2.4, "recoil", loc=(-0.35, 1.45, 0), ease=0.6)
    S.key("do", 0, "sit"); S.key("do", 0.7, "sit")
    elbow = {**C.POSES["stand"], "spine": E(DS, 0, DY), "upper_arm.L": D(*DU), "forearm.L": D(*DFA), "hand.L": D(*DFA)}
    S.key("do", 1.05, {**C.POSES["stand"], "spine": E(15, 0, 0)}, loc=DL0, face=DF, ease=0.6)
    S.key("do", 1.3, elbow, loc=DL, face=DF, ease=0.25)
    S.key("do", 1.7, {**C.POSES["stand"], "spine": E(5, 0, 0), "upper_arm.L": D(0.4, -0.4, -1)}, ease=0.6)
    S.look("martin", "do", 0, 1.3); S.look("do", "martin", 0.6, 1.1)
    # camera: side-on to the table corner so both bodies and the contact point read in one frame, then cut to Martin
    setup(S, 0, 1.55, CAM0, CT0, 30, CAM1, CT1)
    S.focus_on(0, CT1)
    S.camera(1.55, (-0.9, 0.55, 1.45), "martin", 40, ease=0.0001); S.camera(S.dur, (-0.95, 0.5, 1.45), "martin", 40, ease=1.0)
    S.focus_on(1.55, "martin")
    vis("martin_noseblood", t_on=1.37, S=S); nose_spurt(S, 1.37, back=0.25); S.set_expr("martin", 1.33, -0.7, 0.8, 0.1); S.set_expr("do", 1.0, -0.6, 0.6)
    for n in ("dao", "andy"): S.set_expr(n, 1.0, -0.3, 0.8)
    return S

MS, MH, ML, MF = 76, 15, (0.03, 0.93, 0), (0.35, -1)
DS, DY, DL0, DL, DF = 38, 25, (0.66, -0.3, 0), (0.68, -0.06, 0), (-0.35, 1)
DU, DFA = (0.3, -1, 0.55), (-0.7, 0.8, 0.2)
CAM0, CT0, CAM1, CT1 = (-1.6, -0.75, 1.9), (0.2, 0.45, 1.2), (-1.5, -0.68, 1.86), (0.35, 0.3, 1.25)

@shot("3D")
def s_3D():
    S = Shot("3D")
    S.key("martin", 0, "recoil", loc=(-0.35, 1.45, 0)); stand_at_seat(S, "martin", 0, "recoil"); S.key("martin", 0, loc=(-0.35, 1.45, 0))
    S.key("do", 0, {**C.POSES["sit"], "spine": E(-15, 0, 0)})
    vis("martin_noseblood", t_on=0, S=S)
    setup(S, 0, S.dur, WIDE[0], WIDE[1], 24)
    for n in S.p: S.gesture[n] = 0; S.set_expr(n, 0, -0.3, 0.6)
    S.look("dao", "martin", 0, 3); S.look("andy", "martin", 0, 3); S.look("do", "martin", 0, 3); S.look("martin", "do", 0, 3)
    return S

@shot("3E")
def s_3E():
    S = Shot("3E"); S.fstop = 2.8
    S.key("martin", 0, "stand", loc=(-0.35, 1.45, 0)); stand_at_seat(S, "martin", 0); S.key("martin", 0, loc=(-0.35, 1.45, 0)); vis("martin_noseblood", t_on=0, S=S)
    loc, tg = face_cam(S, "dao", 0, 10, 2.6, 0.0); loc1, _ = face_cam(S, "dao", 0, 10, 1.6, 0.0)
    setup(S, 0, S.dur, loc, "dao", 50, loc1)
    S.set_expr("dao", 0, -0.4, 0.3); S.look("dao", (-0.3, 0.55, 0.78), 0.5, 3.4)
    return S

@shot("3F")
def s_3F():
    S = Shot("3F"); S.fstop = 2.8
    stand_at_seat(S, "martin", 0); S.key("martin", 0, "stand", loc=(-0.35, 1.45, 0)); vis("martin_noseblood", t_on=0, S=S)
    S.key("martin", 0.3, "stand_pocket")
    S.walk_to("martin", 1.4, 3.0, (0.0, 1.35), (0.6, 0.0))
    setup(S, 0, S.dur, (-1.9, -0.8, 1.55), (-0.3, 1.3, 1.4), 35, (-1.9, -0.8, 1.55), (0.4, 0.4, 1.4))
    S.set_expr("martin", 0, 0.9, 0)
    return S

# ================================================================== SCENE 4
MARTIN_HALL = (0.85, -1.9, 0)
@shot("4A")
def s_4A():
    S = Shot("4A", extra_state={"curtains": "open"}); S.fstop = 2.8
    stand_at_seat(S, "martin", 0); S.key("martin", 0, "stand", loc=MARTIN_HALL, face=(0, -1)); S.key("martin", 0.8, face=(0, 1)); vis("martin_noseblood", t_on=0, S=S)
    S.key("andy", 0, "sit"); S.key("andy", 0.5, aim_pose(S, "andy", stain.CORK_SPOT, 0.5), ease=0.4)
    cu(S, 0, 1.9, "andy", 25, 2.2, 50)
    S.camera(1.9, (-1.25, 1.9, 1.45), stain.CORK_SPOT, 50, ease=0.0001); S.camera(S.dur, (-1.28, 2.85, 1.43), stain.CORK_SPOT, 50, ease=1.0)
    S.focus_on(1.9, stain.CORK_SPOT)
    return S

@shot("4B")
def s_4B():
    S = Shot("4B"); S.fstop = 2.0
    stand_at_seat(S, "martin", 0); S.key("martin", 0, "stand", loc=MARTIN_HALL, face=(0, 1)); vis("martin_noseblood", t_on=0, S=S)
    for i, n in enumerate(("martin", "dao", "do", "andy")):
        S.look(n, stain.CORK_SPOT, 0, 4); S.set_expr(n, 0, -0.4, 0.9); S.gesture[n] = 0
        cu(S, i * 1.0, (i + 1) * 1.0, n, 0, 1.5, 85)
    return S

@shot("4C")
def s_4C():
    S = Shot("4C", extra_state={"floorlamp": "up", "floorlamp_emit": 6.0}); S.handheld = 1.0
    stand_at_seat(S, "martin", 0); S.key("martin", 0, "stand", loc=MARTIN_HALL, face=(0, 1)); vis("martin_noseblood", t_on=0, S=S)
    push_chair(S, "do", 0.05)
    S.key("do", 0, "sit"); S.key("do", 0.3, "stand_arms_out", loc=(0.9, -0.95, 0), face=(1, -0.5), ease=0.8)
    S.key("do", 0.9, face=(-0.3, 1), ease=0.6); S.key("do", 2.6, "stand_arms_out", face=(-0.8, 1), ease=0.5)
    fl = OBJ("floorlamp")
    path_key(S, fl, [(0.42, Vector((2.1, -1.35, 0)), (0, 0, 0)), (0.6, Vector((2.1, -1.35, 0.05)), (0, -0.9, -0.5)), (0.75, Vector((2.1, -1.35, 0.2)), (0, -math.pi / 2 * 0.97, -0.5))])
    if "fill_lamp" in S.lights:
        L = S.lights["fill_lamp"]; S.at(0.6, lambda fr: (L.data.keyframe_insert("energy", frame=fr - 2), setattr(L.data, "energy", 0), L.data.keyframe_insert("energy", frame=fr)))
        sh = OBJ("fl_shade").active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        S.at(0.6, lambda fr: (sh.keyframe_insert("default_value", frame=fr - 2), setattr(sh, "default_value", 0), sh.keyframe_insert("default_value", frame=fr)))
    setup(S, 0, 3.9, (-1.8, 2.3, 1.6), (1.0, -0.8, 1.2), 28)
    pu = purse(DAO_LAP); S.key("dao", 0, "sit_lap"); S.key("dao", 4.3, {**C.POSES["sit_lap"], "forearm.L": D(-0.5, -0.8, -0.1), "forearm.R": D(0.5, -0.8, -0.1)}, ease=0.3)
    # FIX: high side angle on Dao's lap so the purse and her tightening hands read (was blocked by the tablecloth)
    setup(S, 3.9, S.dur, DAO_LAP + Vector((-0.6, -0.5, 0.55)), DAO_LAP + Vector((0, 0, 0.06)), 50, DAO_LAP + Vector((-0.5, -0.42, 0.48))); S.focus_on(3.9, DAO_LAP + Vector((0, 0, 0.06)))
    for n in ("martin", "dao", "andy"): S.look(n, "do", 1.0, 3.9); S.set_expr(n, 1, -0.3, 0.6)
    S.set_expr("do", 0.5, 0.6, 0.6)
    return S

@shot("4D")
def s_4D():
    S = Shot("4D", cast=("martin",)); S.fstop = 2.8
    S.key("martin", 0, "stand", loc=(1.2, -4.0, 0), face=(0, -1)); vis("martin_noseblood", t_on=0, S=S)
    S.walk_to("martin", 0.0, 2.1, (1.25, -7.45), face_end=(0, -1), pose_end="door")
    S.key("martin", 2.7, "stand_pocket", ease=0.5); S.key("martin", 3.0, face=(0, 1), ease=0.5)
    setup(S, 0, 3.0, (1.2, -3.1, 1.55), (1.2, -8.0, 1.2), 35, (1.2, -4.6, 1.5), (1.2, -8.0, 1.15))
    loc = Vector((1.2, -5.6, 1.45)); setup(S, 3.0, S.dur, loc, "martin", 35, loc + Vector((0, -0.25, 0))); S.focus_on(3.0, "martin")
    S.set_expr("martin", 3.0, 0.5, 0.2)
    return S

@shot("4E")
def s_4E():
    S = Shot("4E", extra_state={"curtains": "open", "curtain_hole": True, "beam": True}); S.fstop = 2.8
    stain.curtain_anim(S.f(0.6), S.f(2.2))
    vis("curtain_hole", t_on=2.2, S=S); vis("beam_shaft", t_on=4.0, S=S)
    bs = S.lights["beam"]; S.at(0, lambda fr: (setattr(bs.data, "energy", 0), bs.data.keyframe_insert("energy", frame=1)))
    S.at(4.0, lambda fr: (bs.data.keyframe_insert("energy", frame=fr - 2), setattr(bs.data, "energy", 60), bs.data.keyframe_insert("energy", frame=fr)))
    rim = S.lights.get("rim_city")
    if rim: S.at(2.2, lambda fr: (rim.data.keyframe_insert("energy", frame=fr - 6), setattr(rim.data, "energy", 0), rim.data.keyframe_insert("energy", frame=fr)))
    stand_at_seat(S, "dao", 0)
    S.key("dao", 0, "stand_arms_out", loc=(-1.0, 2.8, 0), face=(0, 1)); S.key("dao", 0.6, {"upper_arm.L": D(0.6, 0.4, 0.6), "upper_arm.R": D(-0.6, 0.4, 0.6), "forearm.L": D(0.6, 0.6, 0.2), "forearm.R": D(-0.6, 0.6, 0.2)})
    S.key("dao", 2.2, {"upper_arm.L": D(0.1, 0.8, 0.4), "upper_arm.R": D(-0.1, 0.8, 0.4), "forearm.L": D(0.0, 1, 0.1), "forearm.R": D(0, 1, 0.1)}, ease=0.8)
    S.key("dao", 2.8, "stand", loc=(-1.6, 2.9, 0))
    hole = stain.HOLE_SPOT
    S.key("dao", 3.4, aim_pose(S, "dao", hole, 3.4, base="stand", hand="R"), ease=0.6); S.key("dao", 4.4, "stand", ease=0.5)
    S.look("dao", hole, 2.6, 9.4)
    setup(S, 0, 2.9, (-0.2, 0.9, 1.55), (-1.2, 3.0, 1.45), 35, (-0.3, 1.1, 1.55))
    setup(S, 2.9, 4.6, hole + Vector((0.5, -0.35, -0.05)), hole, 85, hole + Vector((0.45, -0.3, -0.05)))
    S.focus_on(2.9, hole)
    setup(S, 4.6, 9.5, (-0.6, 1.4, 1.45), "dao", 50, (-0.7, 1.7, 1.45)); S.focus_on(4.6, "dao")
    S.key("dao", 9.4, face=(0.2, -1), ease=0.6)
    cu(S, 9.5, S.dur, "dao", 0, 1.7, 85); S.set_expr("dao", 9.4, -0.6, 0.2)
    for n in ("martin", "andy", "do"): stain.set_vis(S.p[n].arm, False)
    return S

def act2_standing(S):
    stand_at_seat(S, "martin", 0); stand_at_seat(S, "dao", 0); stand_at_seat(S, "do", 0); stand_at_seat(S, "andy", 0)
    S.key("dao", 0, "stand", loc=(-1.6, 2.45, 0), face=(0.8, -0.2)); S.key("martin", 0, "stand", loc=(-0.9, 2.0, 0), face=(0.6, 0.4))
    S.key("andy", 0, "stand", loc=(-1.9, 1.75, 0), face=(0.8, 0.3)); S.key("do", 0, "stand", loc=(-3.0, 0.3, 0), face=(1, 0.6))
    vis("martin_noseblood", t_on=0, S=S)

@shot("4F")
def s_4F():
    S = Shot("4F"); S.fstop = 2.0
    act2_standing(S)
    ph = stain.make_phone("mphone", (0, 0, 0), (0, 0, 0), screen=None); S.key("martin", 0.3, "stand_point"); S.hold(ph, "martin", "R", 0, S.dur)
    S.key("dao", 1.6, aim_pose(S, "dao", S.head_pos("martin", 1.6) + Vector((0.05, -0.4, -0.5)), 1.6, base="stand", hand="L"), ease=0.4)
    S.key("martin", 2.0, {**C.POSES["stand"], "upper_arm.R": D(-0.2, -0.6, -0.6), "forearm.R": D(0.2, -1, 0.0)}, ease=0.4)
    setup(S, 0, S.dur, (0.55, 2.65, 1.48), (-1.35, 2.05, 1.38), 35, (0.45, 2.6, 1.46))
    S.focus_on(0, "martin"); S.look("do", "dao", 5.5, 7.5); S.look("do", "andy", 7.5, 10)
    S.set_expr("dao", 1.5, 0.4, 0); S.set_expr("do", 5.6, 0.5, 0.2)
    return S

# ================================================================== SCENE 5
@shot("5A")
def s_5A():
    S = Shot("5A", extra_state={"vase": "none"}); S.fstop = 2.8
    v = stain.make_vase((0, 0, 0), stain.clay("vase", (0.2, 0.32, 0.36), 0.25, 0))
    vf = stain.VASE_FLOOR + Vector((0, 0, 0.075)); vt = Vector((-0.32, 0.55, stain.TABLE_TOP))
    path_key(S, v, [(0, vf, (math.pi / 2, 0, 0.7)), (2.2, vf, (math.pi / 2, 0, 0.7))])
    S.hold(v, "dao", "L", 2.3, 3.3, offset=(0, 0.02, -0.06), rot=(math.pi, 0, 0))
    path_key(S, v, [(3.35, vt, (0, 0, 0)), (S.dur, vt, (0, 0, 0))])
    stand_at_seat(S, "dao", 0); S.key("dao", 0, "stand", loc=(-0.85, -0.6, 0), face=(-1, 0.2))
    S.key("dao", 1.3, "crouch", loc=(-0.95, -0.4, 0), ease=0.6); S.key("dao", 2.5, "stand", ease=0.6)
    S.key("dao", 3.0, face=(0.4, 1), loc=(-0.55, -0.45, 0)); S.key("dao", 3.3, aim_pose(S, "dao", vt + Vector((0, 0, 0.2)), 3.3, base="stand", hand="L"), ease=0.6)
    S.key("dao", 3.8, "stand"); S.look("dao", vf, 0.5, 2.6); S.look("dao", vt, 3.0, 3.8)
    for n in ("martin", "andy", "do"): S.look(n, "dao", 0, S.dur); S.set_expr(n, 0, -0.2, 0.4)
    vis("martin_noseblood", t_on=0, S=S)
    setup(S, 0, 1.2, WIDE[0], (-0.6, 0.1, 0.8), 28)
    # FIX: vase insert from the side away from Dao, so her body doesn't cover it
    away = (vf - Vector((-0.95, -0.4, vf.z))); away.z = 0; away.normalize()
    setup(S, 1.2, 2.5, vf + away * 0.65 + Vector((0, 0, 0.35)), vf, 40, vf + away * 0.55 + Vector((0, 0, 0.3))); S.focus_on(1.2, vf)
    setup(S, 2.5, S.dur, (-1.7, 1.7, 1.45), "dao", 50); S.focus_on(2.5, "dao")
    return S

@shot("5B")
def s_5B():
    S = Shot("5B"); S.fstop = 2.0
    palm_cut(S, t_on=0.4)
    S.key("andy", 0, {**C.POSES["sit"], "upper_arm.R": D(-0.25, -0.6, -0.7), "forearm.R": D(0.25, -0.7, 0.7), "hand.R": DT(0.25, -0.6, 0.8, 90)})
    S.key("andy", 2.3, "sit_hands_under", ease=0.5)
    hand = ("bone", "andy", "hand.R", (0, 0, 0)); h = S.head_pos("andy", 0)
    setup(S, 0, 2.3, h + Vector((-0.85, -0.55, -0.2)), hand, 85, h + Vector((-0.75, -0.5, -0.2))); S.focus_on(0, hand)
    S.look("andy", h + Vector((-0.35, -0.05, -0.3)), 0, 2.3); S.set_expr("andy", 0.8, -0.5, 0.5)
    cu(S, 2.3, S.dur, "andy", 10, 1.8, 85); S.focus_on(2.3, "andy")
    vis("martin_noseblood", t_on=0, S=S)
    return S

@shot("5C")
def s_5C():
    S = Shot("5C"); S.fstop = 2.0
    scratches(S, t_on=0.5)
    S.key("martin", 0, "sit"); vis("martin_noseblood", t_on=0, S=S)
    w = ("bone", "martin", "forearm.L", (0, 0, 0)); r = S.root_at("martin", 0)
    setup(S, 0, S.dur, r + Vector((0.95, -0.75, 1.15)), w, 85, r + Vector((0.88, -0.7, 1.1))); S.focus_on(0, w)
    return S

@shot("5D")
def s_5D():
    S = Shot("5D"); S.fstop = 2.8
    c = Vector((0.15, 0.38, 1.28))
    S.camera(0, c, "andy", 35, ease=0.0001); S.camera(1.0, c, "andy", 35)
    S.camera(2.0, c, "martin", 35, ease=0.8); S.camera(3.0, c, "do", 35, ease=0.8); S.camera(4.6, c, "dao", 35, ease=0.7); S.camera(S.dur, c, "dao", 35)
    palm_cut(S); scratches(S); vis("martin_noseblood", t_on=0, S=S)
    S.key("andy", 0, "sit_hands_under"); S.look("do", "dao", 2.8, S.dur)
    for n in ("martin", "andy"): S.look(n, "dao", 3.8, S.dur)
    S.set_expr("do", 3.0, 0.6, 0)
    return S

# ================================================================== SCENE 6 (the trial: 360° orbit)
T6 = sum(anim.TL[s]["dur"] for s in ("6A", "6B", "6C", "6D", "6E"))
def orbit(S, t0, t1, target, height=1.45, r=2.45, lens=50):
    st = anim.TL[S.id]["start"] - anim.TL["6A"]["start"]
    def pos(t):
        a = 2 * math.pi * (st + t) / T6 + 2.8
        return Vector((math.cos(a) * r, 0.4 + math.sin(a) * r * 0.82, height))
    def pick(t, prev):
        if target != "auto": return target
        best, bs = prev, -9
        for m in S.p:
            h = S.head_pos(m, t); f = S.face[m].at(t, lambda a, b, u: anim.lerp(a, b, u)) or 0.0
            v = (pos(t) - h); v.z = 0; v.normalize(); sc_ = fdir(f).dot(v) + (0.7 if S.speaker_at(t) == m else 0) + (0.25 if m == prev else 0)
            if blocked(S, m, pos(t), h, t): sc_ -= 2
            if sc_ > bs: best, bs = m, sc_
        return best
    tg = pick(t0, None); S.camera(t0, pos(t0), tg, lens, ease=0.0001); S.focus_on(t0, None)
    n = max(1, int((t1 - t0) / 0.5)); last = t0
    for i in range(1, n + 1):
        t = t0 + (t1 - t0) * i / n
        nt = pick(t, tg)
        if nt != tg and t - last > 2.0: tg = nt; last = t
        S.camera(t, pos(t), tg, lens, ease=1.0)
def act2_props(S):
    palm_cut(S); scratches(S); vis("martin_noseblood", t_on=0, S=S)
    S.key("andy", 0, "sit")

@shot("6A")
def s_6A():
    S = Shot("6A"); S.fstop = 2.8; act2_props(S)
    stand_up(S, "andy", 0.2, 0.6)
    S.key("andy", 4.2, aim_pose(S, "andy", S.head_pos("do", 4), 4.2, base="stand"), ease=0.3)
    orbit(S, 0, S.dur, "andy", height=1.05)
    S.set_expr("andy", 0, 0.3, 0); S.look("andy", "do", 4.0, S.dur)
    return S

@shot("6B")
def s_6B():
    S = Shot("6B"); S.fstop = 2.8; act2_props(S)
    stand_at_seat(S, "andy", 0); S.key("andy", 0, "stand", loc=SEAT["andy"]); S.walk_to("andy", 0.1, 0.8, (1.15, -0.55), face_end="do")
    ph = stain.make_phone("do_phone_h", (0, 0, 0), (0, 0, 0), screen="phone_chat.png")
    S.key("do", 0, "sit_glass"); S.hold(ph, "do", "R", 0, 0.9)
    S.key("andy", 0.85, aim_pose(S, "andy", S.head_pos("do", 0.9) + Vector((0, 0, -0.25)), 0.85, base="stand")); S.key("andy", 1.3, "stand_point")
    S.hold(ph, "andy", "R", 0.95, S.dur)
    S.key("do", 1.4, aim_pose(S, "do", S.head_pos("andy", 1.4), 1.4), ease=0.4); S.key("do", 2.4, "sit")
    orbit(S, 0, 2.3, "auto")
    # insert: the chat
    ins = stain.make_phone("chat_insert", (2.4, -2.4, 1.2), (math.radians(80), 0, math.radians(45)), screen="phone_chat.png")
    setup(S, 2.3, 3.4, Vector((2.4, -2.4, 1.2)) + Vector((-0.17, 0.17, 0.05)), (2.4, -2.4, 1.2), 50); S.focus_on(2.3, (2.4, -2.4, 1.2))
    orbit(S, 3.4, 7.8, "auto")
    cu(S, 7.8, 9.9, "dao", 0, 1.6, 85, push=0.1); S.focus_on(7.8, "dao"); S.set_expr("dao", 7.0, -0.8, 0.3)
    orbit(S, 9.9, S.dur, "auto")
    S.set_expr("martin", 3.4, -0.2, 0); S.gesture["martin"] = 0.2
    for n in ("dao",): S.look(n, "martin", 3.5, S.dur)
    return S

@shot("6C")
def s_6C():
    S = Shot("6C"); S.fstop = 2.8; act2_props(S)
    stand_at_seat(S, "andy", 0); S.key("andy", 0, "stand", loc=(1.15, -0.55, 0), face="do")
    push_chair(S, "do", 0.1); S.key("do", 0, "sit"); S.key("do", 0.5, "stand", ease=0.7)
    S.walk_to("do", 0.6, 2.0, (0.2, 1.6), (-0.25, 1.55), face_end="martin")
    S.key("do", 2.2, aim_pose(S, "do", S.head_pos("martin", 2.2) + Vector((0, 0, -0.35)), 2.2, base="stand")); S.key("do", 2.9, "stand_toast")
    rb = ring_box((0, 0, 0), open_t=2.6, S=S); S.hold(rb, "do", "R", 2.3, S.dur, offset=(0, 0.03, 0), rot=(math.pi / 2, 0, 0))
    S.key("martin", 0, "sit"); S.key("martin", 2.4, {**C.POSES["sit"], "spine": E(-12, 0, -15)})
    S.key("martin", 6.6, aim_pose(S, "martin", S.head_pos("dao", 6.6), 6.6), ease=0.4); S.key("martin", 8.6, "sit")
    orbit(S, 0, 3.0, "auto")
    setup(S, 3.0, 6.6, S.head_pos("do", 3) + Vector((0.65, -0.95, -0.1)), "do", 50); S.focus_on(3.0, "do")
    cu(S, 6.6, 8.6, "martin", 10, 1.7, 85); S.focus_on(6.6, "martin")
    cu(S, 8.6, 10.1, "dao", 0, 1.7, 85); S.focus_on(8.6, "dao"); S.mouth("dao", 9.0, 9.6, 0.25)
    orbit(S, 10.1, S.dur, "auto")
    S.mouth("do", 5.9, 6.6, 0.8); S.set_expr("do", 3.4, -0.2, 0.3); S.set_expr("martin", 6.5, -0.8, 0.4)
    S.look("dao", "do", 10.0, S.dur); S.look("martin", "do", 10.0, S.dur)
    return S

@shot("6D")
def s_6D():
    S = Shot("6D"); S.fstop = 2.8; act2_props(S)
    stand_at_seat(S, "do", 0); S.key("do", 0, "stand", loc=(-0.25, 1.55, 0), face="martin")
    stand_at_seat(S, "andy", 0); S.key("andy", 0, "stand", loc=(1.15, -0.55, 0), face=(1, 0.8))
    S.walk_to("andy", 0.2, 1.0, (SEAT["andy"].x, SEAT["andy"].y), face_end=(-1, 0)); S.key("andy", 1.2, "crouch", ease=0.5)
    S.walk_to("do", 1.0, 2.2, (1.0, 1.2), (1.25, 0.8), face_end="andy"); S.key("andy", 2.2, "stand", ease=0.5)
    ph = stain.make_phone("andy_phone_h", (0, 0, 0), (0, 0, 0), screen="phone_threats.png")
    S.key("do", 2.4, aim_pose(S, "do", S.head_pos("andy", 2.4) + Vector((0, 0, -0.4)), 2.4, base="stand")); S.key("do", 2.9, "stand_point")
    S.hold(ph, "do", "R", 2.5, S.dur)
    ring_box(Vector((-0.15, 0.62, stain.TABLE_TOP)))
    orbit(S, 0, 3.1, "auto")
    ins = stain.make_phone("threat_insert", (2.4, -2.4, 1.2), (math.radians(80), 0, math.radians(45)), screen="phone_threats.png")
    p = Vector((2.4, -2.4, 1.2))
    setup(S, 3.1, 7.5, p + Vector((-0.18, 0.18, 0.12)), p + Vector((0, 0, 0.04)), 50, p + Vector((-0.16, 0.16, 0.0)), p + Vector((0, 0, -0.04))); S.focus_on(3.1, p)
    cu(S, 7.5, 9.1, "do", 20, 1.8, 85); S.focus_on(7.5, "do")
    cu(S, 9.1, S.dur, "andy", -15, 1.8, 85, push=0.1); S.focus_on(9.1, "andy"); S.gesture["andy"] = 0
    S.set_expr("do", 7.4, 0.5, 0.3); S.set_expr("andy", 9.0, 0.0, 0.0)
    return S

@shot("6E")
def s_6E():
    S = Shot("6E"); S.fstop = 4.0; act2_props(S)
    for n in ("martin", "andy", "do"): stand_at_seat(S, n, 0)
    S.key("martin", 0, "stand", loc=(-0.25, 1.55, 0)); S.key("do", 0, "stand", loc=(1.25, 0.8, 0)); S.key("andy", 0, "stand", loc=(1.15, 0.2, 0))
    S.walk_to("martin", 0.3, 2.0, (-1.2, 0.5), (-1.15, -0.25), face_end="dao")
    S.walk_to("andy", 0.5, 2.4, (0.8, -0.85), (0.05, -1.0), face_end="dao")
    S.walk_to("do", 0.4, 2.6, (1.2, -1.2), (-0.6, -1.35), face_end="dao")
    pu = purse(DAO_LAP); S.key("dao", 0, "sit_lap"); S.key("dao", 1.5, {**C.POSES["sit_lap"], "forearm.L": D(-0.5, -0.8, 0.1), "forearm.R": D(0.5, -0.8, 0.1), "spine": E(8, 0, 0)}, ease=0.4)
    setup(S, 0, 4.8, (-1.6, -2.3, 2.6), (-0.55, -0.4, 0.8), 28, (-1.5, -2.1, 2.55))
    cu(S, 4.8, 7.6, "dao", 35, 1.7, 85, dz=0.1); S.focus_on(4.8, "dao")
    cu(S, 7.6, S.dur, "andy", 0, 1.9, 85, dz=-0.15); S.focus_on(7.6, "andy")
    S.look("dao", "andy", 3.4, 7.7); S.set_expr("dao", 1.5, -0.7, 0.3); S.set_expr("andy", 5.0, 0.0, 0.0); S.gesture["andy"] = 0
    S.look("andy", "dao", 2.4, S.dur); S.look("martin", "dao", 2.0, S.dur); S.look("do", "dao", 2.6, S.dur)
    return S

# ================================================================== ACT 3
def act3_base(S, standing=True):
    palm_cut(S); scratches(S); vis("martin_noseblood", t_on=0, S=S)
    for n in ("martin", "andy", "do"): stand_at_seat(S, n, 0)
    S.key("martin", 0, "stand", loc=(-1.15, -0.25, 0), face="dao"); S.key("andy", 0, "stand", loc=(0.05, -1.0, 0), face="dao"); S.key("do", 0, "stand", loc=(-0.6, -1.35, 0), face="dao")
    ring_box(Vector((-0.15, 0.62, stain.TABLE_TOP)))

@shot("7A")
def s_7A():
    S = Shot("7A", extra_state={"gun": "hidden"}); S.fstop = 2.0; act3_base(S)
    pu = purse(DAO_LAP); S.key("andy", 0, "stand"); S.key("andy", 0.25, aim_pose(S, "andy", DAO_LAP + Vector((0, 0, 0.1)), 0.25, base="stand"), ease=0.4)
    S.hold(pu, "andy", "R", 0.35, S.dur, offset=(0, 0.02, -0.08)); S.key("andy", 0.8, "stand_point", ease=0.4); S.key("andy", 1.5, "stand")
    g = stain.make_gun("gun", (-0.45, -0.05, stain.TABLE_TOP + 0.02), (0, 0, 0.6))
    gt = Vector((-0.2, 0.25, stain.TABLE_TOP + 0.02))
    path_key(S, g, [(0, Vector((0, 0, -3)), None), (0.6, Vector((-0.42, -0.08, 0.85)), (math.pi / 2, 0, 0.2)), (0.85, Vector((-0.4, 0.0, stain.TABLE_TOP + 0.02)), (math.pi / 2, 0, 0.4)), (1.3, gt, (math.pi / 2, 0, 0.9))])
    # FIX: clear view of the rip (no one's back in the way), then a long, bright close-up of the gun on the white cloth
    setup(S, 0, 1.0, (0.65, 0.45, 1.55), (-0.4, -0.6, 0.9), 30, (0.6, 0.4, 1.5), (-0.4, -0.45, 0.85)); S.focus_on(0, (-0.45, -0.55, 0.9))
    dark = stain.clay("gun_matte", (0.012, 0.012, 0.014), 0.45, 0.02, 0.1)   # matte black so it pops on the white cloth
    for c in g.children: c.data.materials.clear(); c.data.materials.append(dark)
    vs = bpy.context.scene.view_settings; e0 = S.exposure
    def expo(fr):   # the white cloth under the pendant blows out in close-up: drop exposure only for the gun insert
        for f, v in ((1, e0), (S.f(1.0) - 1, e0), (S.f(1.0), -2.2), (S.f(2.6) - 1, -2.2), (S.f(2.6), e0)):
            vs.exposure = v; vs.keyframe_insert("exposure", frame=f)
    S.at(0, expo)
    setup(S, 1.0, 2.6, gt + Vector((0.45, -0.42, 0.3)), gt, 50, gt + Vector((0.3, -0.28, 0.18)), gt); S.focus_on(1.0, gt)
    cu(S, 2.6, 4.6, "dao", 20, 1.7, 85); S.focus_on(2.6, "dao")
    cu(S, 4.6, 6.6, "dao", 20, 1.7, 85); S.look("dao", "do", 4.6, 7.0)
    cu(S, 6.6, S.dur, "do", 0, 1.8, 85, push=0.15); S.focus_on(6.6, "do"); S.set_expr("do", 7.0, -0.7, 0.8, 0.5); S.look("do", "dao", 6.6, S.dur)
    S.set_expr("dao", 0.4, -0.6, 0.5)
    for n in S.p: S.look(n, gt, 1.0, 2.6) if n != "dao" else None
    return S

@shot("7B")
def s_7B():
    S = Shot("7B", extra_state={"vase": "none", "gun": "hidden"}); S.handheld = 1.6; S.fstop = 2.8; act3_base(S)
    S.dutch.add(0, 12); S.dutch.add(S.dur, 14)
    gt = Vector((-0.2, 0.25, stain.TABLE_TOP + 0.02))
    g = stain.make_gun("gun", tuple(gt), (0, 0, 0.9))
    path_key(S, g, [(0, gt, (math.pi / 2, 0, 0.9)), (2.9, gt, (math.pi / 2, 0, 0.9)), (3.05, gt + Vector((-0.6, 0.2, 0.1)), (math.pi / 2, 0.5, 2.0)),
                    (3.3, Vector((-1.4, 0.6, 0.03)), (math.pi / 2, 0, 2.2)), (3.7, stain.GUN_RUG, (math.pi / 2, 0, 2.3))])
    v = stain.make_vase((-0.32, 0.55, stain.TABLE_TOP), stain.clay("vase", (0.2, 0.32, 0.36), 0.25, 0))
    vf = stain.VASE_FLOOR + Vector((0, 0, 0.075))
    path_key(S, v, [(0, Vector((-0.32, 0.55, stain.TABLE_TOP)), (0, 0, 0)), (1.9, Vector((-0.32, 0.55, stain.TABLE_TOP)), (0, 0, 0)), (2.05, Vector((-0.5, 0.2, 0.85)), (0.8, 0, 0.3)),
                    (2.2, Vector((-0.9, -0.15, 0.3)), (1.4, 0, 0.6)), (2.3, vf, (math.pi / 2, 0, 0.7))])
    S.walk_to("martin", 0.0, 0.6, (-0.75, 0.0)); S.key("martin", 0.9, "stand_reach", ease=0.4)
    S.walk_to("andy", 0.2, 0.8, (-0.35, -0.6)); S.key("andy", 1.0, aim_pose(S, "andy", S.head_pos("martin", 1) + Vector((0.2, 0, -0.4)), 1.0, base="stand", both=True), ease=0.4)
    S.key("martin", 2.0, {**C.POSES["stand_reach"], "spine": E(20, 0, 25)}, ease=0.5); S.key("andy", 2.0, "stand_arms_out", ease=0.4); S.key("martin", 3.2, "stand_arms_out")
    push_chair(S, "dao", 0.6); S.key("dao", 0.6, "stand", ease=0.6)
    # FIX: shoot from the lit table side so faces, the vase and the gun read (was all silhouettes)
    S.exposure += 0.5
    setup(S, 0, 2.9, (0.75, 0.95, 1.75), (-0.6, -0.1, 1.0), 28, (0.65, 0.85, 1.7), (-0.6, -0.05, 0.95))
    # FIX 2: follow the gun off the table edge from high up, clear of the table, so it lands in plain view on the rug
    S.camera(2.9, (-0.7, 1.9, 1.7), (-1.0, 0.45, 0.7), 30, ease=0.0001); S.camera(3.75, (-1.05, 1.85, 1.45), stain.GUN_RUG, 35, ease=0.7)
    S.camera(S.dur, (-1.15, 1.75, 1.3), stain.GUN_RUG, 40, ease=1.0)
    S.focus_on(0, (-0.55, -0.2, 1.1)); S.focus_on(2.9, gt); S.focus_on(3.6, stain.GUN_RUG)
    for n in S.p: S.look(n, g.location, 2.9, S.dur)
    return S

@shot("7C")
def s_7C():
    S = Shot("7C", extra_state={"gun": "rug", "vase": "floor"}); S.fstop = 2.0; act3_base(S)
    for n in S.p: S.gesture[n] = 0; S.look(n, stain.GUN_RUG, 0, S.dur)
    S.key("martin", 0, "stand_arms_out", loc=(-0.75, 0.0, 0)); S.key("andy", 0, "stand_arms_out", loc=(-0.35, -0.6, 0)); stand_at_seat(S, "dao", 0)
    g = stain.GUN_RUG
    S.camera(0, g + Vector((0.9, -0.55, 0.06)), g + Vector((0, 0, 0.03)), 24, ease=0.0001)
    S.camera(4.5, g + Vector((0.45, -0.28, 0.06)), g + Vector((0, 0, 0.03)), 24, ease=1.0)
    S.camera(7.6, g + Vector((0.42, -0.26, 0.08)), stain.HOLE_SPOT, 24, ease=1.0); S.camera(S.dur, g + Vector((0.42, -0.26, 0.08)), stain.HOLE_SPOT, 24)
    S.focus_on(0, g); S.focus_on(5.6, stain.HOLE_SPOT)
    return S

@shot("8A")
def s_8A():
    S = Shot("8A", extra_state={"gun": "none"}); S.fstop = 2.8; act3_base(S); S.handheld = 1.2
    S.key("martin", 0, "stand_arms_out", loc=(-0.75, 0.0, 0)); S.key("andy", 0, "stand_arms_out", loc=(-0.35, -0.6, 0)); stand_at_seat(S, "dao", 0)
    g = stain.make_gun("gun_h", tuple(stain.GUN_RUG), (0, 0, 2.3)); g.rotation_euler = (math.pi / 2, 0, 2.3)
    S.key("andy", 0.2, "crouch", loc=(-1.6, 0.55, 0), face=(-0.3, 1), ease=0.7)
    S.hold(g, "andy", "R", 0.6, S.dur, offset=(0, 0.02, 0), rot=(0, 0, -math.pi / 2))
    S.key("andy", 1.2, "kneel", ease=0.5)
    S.key("andy", 1.6, {**C.POSES["kneel"], **{k: v for k, v in aim_pose(S, "andy", stain.HOLE_SPOT, 1.6, base="kneel", both=True).items() if "arm" in k or "hand" in k}}, ease=0.4)
    S.look("andy", stain.HOLE_SPOT, 1.4, S.dur)
    # FIX: low camera beside Andy: we see the dive, the gun in his hands and where he aims
    S.exposure += 0.5
    setup(S, 0, S.dur, (-0.45, 1.75, 1.1), (-1.4, 0.45, 0.85), 28, (-0.55, 1.8, 1.0), (-1.55, 0.6, 0.85)); S.focus_on(0, "andy")
    for n in ("martin", "dao", "do"): S.look(n, "andy", 0.3, S.dur); S.set_expr(n, 0.5, -0.4, 0.7)
    return S

@shot("8B")
def s_8B():
    S = Shot("8B", extra_state={"gun": "none"}); S.handheld = 1.8; S.fstop = 2.8; act3_base(S)
    S.dutch.add(0, -10); S.dutch.add(S.dur, -14)
    S.key("martin", 0, "stand_arms_out", loc=(-0.75, 0.0, 0)); stand_at_seat(S, "dao", 0)
    g = stain.make_gun("gun_h", (0, 0, 0), (0, 0, 0))
    S.key("andy", 0, C.POSES["kneel"], loc=(-1.6, 0.55, 0), face=(-0.3, 1)); S.hold(g, "andy", "R", 0, S.dur, rot=(0, 0, -math.pi / 2))
    S.key("andy", 0.0, {**C.POSES["kneel"], **{k: v for k, v in aim_pose(S, "andy", stain.HOLE_SPOT, 0.0, base="kneel", both=True).items() if "arm" in k or "hand" in k}})
    S.key("do", 0, "stand", loc=(-0.6, -1.35, 0)); S.key("do", 0.5, "lunge", loc=(-1.3, 0.2, 0), face="andy", ease=0.8)
    S.key("do", 0.9, "lying", loc=(-1.45, 0.85, 0), face=(-0.6, 1), ease=0.4); S.key("andy", 0.95, "floor_gun", ease=0.4)
    S.key("andy", 2.0, "floor_sit", ease=0.6); S.key("andy", 3.0, "floor_gun", ease=0.5); S.key("do", 2.5, "floor_sit", ease=0.6); S.key("do", 3.6, "lunge", ease=0.5)
    # FIX: same low side camera as 8A, so the tackle and the floor wrestle are in frame
    S.exposure += 0.5
    setup(S, 0, S.dur, (-0.35, 1.9, 1.15), (-1.35, 0.45, 0.55), 24, (-0.4, 1.95, 1.05), (-1.45, 0.75, 0.4)); S.focus_on(0, (-1.45, 0.7, 0.5))
    S.set_expr("do", 0, 0.8, 0.6); S.set_expr("andy", 0.8, 0.8, 0.4)
    return S

@shot("8C")
def s_8C():
    S = Shot("8C", extra_state={"gun": "none"}); S.fstop = 2.8; act3_base(S)
    S.key("andy", 0, "floor_gun", loc=(-1.6, 0.55, 0), face=(-0.3, 1)); S.key("do", 0, "floor_sit", loc=(-1.4, 0.85, 0), face=(0.3, -1))
    hole = stain.HOLE_SPOT
    setup(S, 0, S.dur, hole + Vector((0.6, -1.4, -0.35)), hole, 50, hole + Vector((0.55, -1.3, -0.33))); S.focus_on(0, hole)
    def blackout(fr):  # 3 frames of black: a card in front of the lens
        cam = bpy.context.scene.camera
        card = stain.plane("black_card", 1, 1, (0, 0, -0.06), stain.emission_only("blk", (0, 0, 0), 0)); card.parent = cam
        stain.key_vis(card, 1, True); stain.key_vis(card, 5, False)
    S.at(0, blackout)
    bs = S.lights["beam"]
    def fl(fr):
        for k, e in enumerate([60, 5, 120, 10, 90, 60]):
            bs.data.energy = e; bs.data.keyframe_insert("energy", frame=fr + k * 2)
    S.at(0.15, fl)
    for side in ("L",):
        cl = OBJ("curtain_L")
        S.at(0.15, lambda fr, cl=cl: [key_obj(cl, fr + k * 2, location=(0, 0.02 * ((-1) ** k) * (1 - k / 5), 0)) for k in range(6)])
    for n in S.p: S.gesture[n] = 0
    return S

@shot("8D")
def s_8D():
    S = Shot("8D", extra_state={"gun": "none"}); S.fstop = 4.0; act3_base(S)
    g = stain.make_gun("gun_h", (0, 0, 0), (0, 0, 0))
    S.key("andy", 0, "floor_gun", loc=(-1.6, 0.55, 0), face=(-0.3, 1)); S.key("andy", 0.3, "floor_sit", ease=0.6)
    S.hold(g, "andy", "R", 0, 9.6, rot=(0, 0, -math.pi / 2)); path_key(S, g, [(9.7, stain.GUN_RUG + Vector((0, 0, 0.0)), (math.pi / 2, 0, 2.3)), (S.dur, stain.GUN_RUG, (math.pi / 2, 0, 2.3))])
    S.key("do", 0, "floor_sit", loc=(-1.35, 0.95, 0), face=(0.4, -1))
    S.key("martin", 0, "stand", loc=(-0.75, 0.0, 0), face="andy"); stand_at_seat(S, "dao", 0)
    S.mouth("dao", 2.0, 3.4, 0.4); S.mouth("martin", 2.6, 3.6, 0.5); S.set_expr("dao", 2, -0.5, 0.2)
    S.key("andy", 9.0, "stand", loc=(-1.5, 0.3, 0), ease=0.5); S.key("do", 10.0, "stand", ease=0.5)
    S.walk_to("martin", 9.0, S.dur, (0.4, -1.4), (0.9, -2.2)); S.walk_to("dao", 9.4, S.dur, (0.2, -1.6), (1.4, -2.3))
    S.walk_to("andy", 10.2, S.dur, (0.0, -1.2), (1.1, -2.0)); S.walk_to("do", 10.8, S.dur, (0.2, -1.0), (1.2, -1.8))
    setup(S, 0, S.dur, WIDE[0], (-0.8, 0.4, 0.6), 24)
    for n in S.p: S.gesture[n] = 0.3
    return S

# ================================================================== ACT 4
HALL_GROUP = {"martin": (0.85, -2.55), "dao": (1.55, -2.5), "andy": (1.25, -2.25), "do": (1.15, -2.75)}
def act4_base(S, at_hall=True):
    palm_cut(S); scratches(S); vis("martin_noseblood", t_on=0, S=S)
    for n in ("martin", "dao", "andy", "do"): stand_at_seat(S, n, 0)
    if at_hall:
        for n, (x, y) in HALL_GROUP.items(): S.key(n, 0, "stand", loc=(x, y, 0), face=(0, -1))
    ring_box(Vector((-0.15, 0.62, stain.TABLE_TOP))); act4(S)

@shot("9A")
def s_9A():
    S = Shot("9A", cast=("dao",)); stain.set_vis(S.p["dao"].arm, False)
    for o in bpy.data.objects:
        if o.name.startswith("dao_"): o.hide_render = True
    act4(S); setup(S, 0, S.dur, *HALL0)
    flicker(S, 1.4, 2.0, names=("hall",), bulb="hall_bulb", seed=5); flicker(S, 5.4, 5.9, names=("hall",), bulb="hall_bulb", seed=6)
    return S

@shot("9B")
def s_9B():
    S = Shot("9B"); S.fstop = 2.8; act4_base(S)
    S.key("do", 1.5, "stand", loc=(1.2, -3.3, 0), ease=0.6)
    setup(S, 0, S.dur, (1.2, -4.4, 1.35), (1.2, -2.6, 1.55), 50, (1.2, -4.3, 1.35))
    for n in S.p: S.look(n, stain.BODY_POS + Vector((0, 0, 0.2)), 0, S.dur); S.set_expr(n, 0, -0.6, 0.6); S.gesture[n] = 0
    S.focus_on(0, "do")
    return S

@shot("9C")
def s_9C():
    S = Shot("9C"); S.fstop = 4.0; act4_base(S); S.key("do", 0, "stand", loc=(1.2, -3.3, 0)); S.exposure += 0.6
    cp = chest_point()
    # FIX: sharper, brighter, closer look at the cloth over the chest so the small round hole reads
    setup(S, 0, 2.6, cp + Vector((0.12, 0.3, 0.5)), cp, 50, cp + Vector((0.1, 0.25, 0.42))); S.focus_on(0, cp)
    cu(S, 2.6, S.dur, "dao", 0, 1.7, 85); S.focus_on(2.6, "dao"); S.set_expr("dao", 2.6, -0.7, 0.3)
    S.look("dao", cp, 2.6, 3.0); S.look("dao", stain.GUN_RUG, 3.0, S.dur)
    stain.make_gun("gun", stain.GUN_RUG, (0, 0, 2.3))
    return S

@shot("9D")
def s_9D():
    S = Shot("9D", extra_state={"gun": "none"}); S.fstop = 2.8; act4_base(S); S.key("do", 0, "stand", loc=(1.2, -3.3, 0))
    g = stain.make_gun("gun_h", tuple(stain.GUN_RUG), (0, 0, 2.3)); g.rotation_euler = (math.pi / 2, 0, 2.3)
    for n in S.p: S.key(n, 0.3, face=(-0.5, 1), ease=0.5); S.look(n, stain.GUN_RUG, 0.3, 1.4)
    S.walk_to("do", 1.2, 2.1, (-1.6, 0.5)); S.key("do", 2.2, "crouch", ease=0.4)
    S.hold(g, "do", "R", 2.3, S.dur, rot=(0, 0, -math.pi / 2))
    S.key("do", 2.6, "floor_gun", loc=(-1.0, -0.25, 0), face=(0.5, -1), ease=0.6)
    for n, p in (("martin", (0.1, -1.6)), ("andy", (0.6, -1.3)), ("dao", (-0.4, -1.9))):
        S.walk_to(n, 1.6, 2.8, p, face_end="do")
    S.look("do", "andy", 5.4, 7.2); S.look("do", "martin", 7.6, 9.4); S.look("do", "dao", 10.0, S.dur)
    S.set_expr("do", 2.4, 0.4, 0.7)
    for n in ("martin", "andy", "dao"): S.look(n, "do", 2.8, S.dur)
    setup(S, 0, 2.6, (1.45, -3.6, 2.3), (-0.7, 0.4, 0.6), 24)
    cu(S, 2.6, 5.4, "do", 0, 2.2, 50, dz=-0.1); S.focus_on(2.6, "do")
    cu(S, 5.4, 7.6, "andy", 10, 1.8, 85); S.focus_on(5.4, "andy")
    setup(S, 7.6, 10.0, (-0.35, -1.25, 1.05), "do", 50); S.focus_on(7.6, "do")
    cu(S, 10.0, S.dur, "do", -20, 1.6, 85, dz=-0.05); S.focus_on(10.0, "do")
    S.handheld = 0.8
    return S

DO_TABLE = (-1.0, -0.25, 0)
def act4_standoff(S):
    act4_base(S, at_hall=False)
    S.key("do", 0, "floor_gun", loc=DO_TABLE, face=(0.5, -1))
    for n, p in (("martin", (0.1, -1.6)), ("andy", (0.6, -1.3)), ("dao", (-0.4, -1.9))): S.key(n, 0, "stand", loc=p, face="do")
    g = stain.make_gun("gun_h", (0, 0, 0), (0, 0, 0)); S.hold(g, "do", "R", 0, 1e9, rot=(0, 0, -math.pi / 2))

@shot("9E")
def s_9E():
    S = Shot("9E"); S.fstop = 2.0; act4_standoff(S)
    S.key("andy", 0, "stand"); S.key("andy", 1.0, {"upper_arm.R": D(-0.1, -0.4, -1), "forearm.R": D(0.4, -0.8, 0.0)}, ease=0.5)
    cu(S, 0, 3.3, "andy", 0, 1.7, 85); S.focus_on(0, "andy")
    S.key("martin", 3.3, "stand"); S.key("martin", 4.3, {"upper_arm.R": D(-0.1, -0.4, -1), "forearm.R": D(0.6, -0.6, 0.2), "upper_arm.L": D(0.1, -0.3, -1), "forearm.L": D(-0.4, -0.8, 0.1)}, ease=0.5)
    cu(S, 3.3, 6.6, "martin", 0, 1.7, 85); S.focus_on(3.3, "martin")
    cu(S, 6.6, S.dur, "dao", 0, 1.6, 85, push=0.15); S.focus_on(6.6, "dao"); S.look("dao", "do", 0, S.dur)
    S.look("andy", (0.6, -0.9, 0.3), 0.5, 3.3); S.look("martin", (0.1, -1.3, 0.2), 3.6, 6.6)
    for n in S.p: S.gesture[n] = 0
    S.set_expr("dao", 6.6, 0.3, 0.0)
    return S

@shot("10A")
def s_10A():
    S = Shot("10A", extra_state={"door_open": False}); S.fstop = 4.0; act4_standoff(S)
    S.key("martin", 0, "stand", loc=(0.9, -2.2, 0), face=(0, -1))
    S.walk_to("martin", 0.5, 2.8, (1.05, -4.0))
    S.key("martin", 3.1, "step_over", loc=(1.05, -4.55, 0), ease=0.6); S.key("martin", 3.6, "stand", loc=(1.05, -5.4, 0), ease=0.6); S.key("martin", 3.9, "step_over", loc=(1.05, -5.9, 0), ease=0.6)
    S.walk_to("martin", 4.2, 6.2, (1.25, -7.45), face_end=(0, -1), pose_end="door")
    dr = OBJ("front_door"); path_key(S, dr, [(7.5, dr.location, (0, 0, 0)), (8.6, dr.location, (0, 0, -0.5))])
    S.key("martin", 8.8, "stand", loc=(1.62, -7.55, 0), face=(-0.3, 1), ease=0.6)
    S.look("martin", "cam", 9.5, S.dur)
    setup(S, 0, S.dur, (1.2, -2.0, 1.55), (1.2, -7.0, 1.2), 35, (1.2, -2.2, 1.55))
    S.focus_on(0, "martin")
    return S

@shot("10B")
def s_10B():
    S = Shot("10B", extra_state={"door_open": True}); S.fstop = 1.8; act4_standoff(S)
    S.key("do", 0, "stand_gun", loc=(-0.2, -0.95, 0), face=(0.5, -1)); stain.set_vis(S.p["martin"].arm, False)
    S.look("do", (1.4, -7.8, 1.3), 0, 3.5); S.look("do", stain.BODY_POS, 4.0, 6.5); S.look("do", (1.4, -7.8, 1.3), 6.8, S.dur)
    S.gesture["do"] = 0; S.set_expr("do", 0, -0.7, 0.4)
    cu(S, 0, S.dur, "do", 15, 1.6, 85, push=0.2)
    return S

@shot("10C")
def s_10C():
    S = Shot("10C", extra_state={"door_open": True, "chair_fallen": "andy"}); S.fstop = 2.8; act4_standoff(S)
    S.key("do", 0, "stand_gun", loc=(-0.2, -0.95, 0), face=(0.5, -1)); stain.set_vis(S.p["martin"].arm, False)
    S.key("andy", 0, "stand", loc=(1.9, 0.2, 0), face=(-1, 0.2)); S.key("andy", 0.6, "crouch", ease=0.5); S.key("andy", 1.5, "stand", ease=0.5)
    ch = OBJ("chair_andy"); (x, y), f = stain.SEATS["andy"]
    path_key(S, ch, [(0.6, Vector((x + 0.2, y, 0.02)), (math.pi / 2 * 0.98, 0, ch.rotation_euler.z)), (1.5, Vector((x, y, 0)), (0, 0, ch.rotation_euler.z))])
    S.key("andy", 2.0, "sit", loc=tuple(SEAT["andy"]), ease=0.6)
    bot = OBJ("wine_bottle"); neck = OBJ("wine_neck")
    for i, n in enumerate(("martin", "dao", "andy", "do")):
        S.key("andy", 3.0 + i * 0.8, aim_pose(S, "andy", OBJ(f"glass_{n}").location + Vector((0, 0, 0.25)), 3.0 + i * 0.8), ease=0.5)
    S.key("andy", 6.2, "sit")
    S.look("andy", (0.3, 0.4, 0.8), 2.5, 6.0); S.look("andy", "do", 6.0, S.dur)
    setup(S, 0, S.dur, (0.35, 1.75, 1.55), (1.5, 0.3, 0.9), 35, (0.45, 1.7, 1.52)); S.focus_on(0, "andy")
    return S

@shot("10D")
def s_10D():
    S = Shot("10D", extra_state={"door_open": True}); S.fstop = 4.0; act4_standoff(S)
    S.key("do", 0, "stand_gun", loc=(-0.2, -0.95, 0), face=(0.5, -1)); S.key("andy", 0, "sit")
    S.key("martin", 0, "stand", loc=(1.25, -7.0, 0), face=(0, 1))
    S.walk_to("martin", 0.3, 2.5, (1.05, -6.0)); S.key("martin", 2.8, "step_over", loc=(1.05, -5.4, 0), ease=0.6); S.key("martin", 3.2, "stand", loc=(1.05, -4.6, 0), ease=0.6)
    S.walk_to("martin", 3.4, 6.5, (1.0, -2.2), (-0.3, 1.0), (-0.55, 1.32), face_end=(0, -1)); sit_down(S, "martin", 6.6)
    S.walk_to("dao", 0.5, 2.2, (-0.55, -0.1), (-0.55, -0.52), face_end=(0, 1)); sit_down(S, "dao", 2.3)
    S.look("do", "martin", 2.5, S.dur)
    setup(S, 0, S.dur, (2.2, 2.6, 1.8), (0.4, -1.2, 0.9), 24)
    return S

@shot("10E")
def s_10E():
    S = Shot("10E", extra_state={"new_stain": True, "door_open": True}); S.fstop = 5.6; act4_standoff(S); S.exposure = -3.0
    for n in ("martin", "dao", "andy"): S.seat(n)
    S.key("do", 0, "stand_gun", loc=(-0.2, -0.95, 0), face=(0.5, -1))
    ns = OBJ("new_stain")
    S.at(0, lambda fr: key_obj(ns, 1, scale=(0.02, 0.02, 1)))
    S.at(2.0, lambda fr: [key_obj(ns, fr + k * 12, scale=((0.02 + 0.98 * ((k / 14) ** 0.6)),) * 2 + (1,)) for k in range(15)])
    setup(S, 0, S.dur, *OVER)
    flicker(S, 1.0, 1.5, names=("key", "bounce"), seed=11)
    scr = OBJ("do_phone_screen").active_material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    S.at(0, lambda fr: (setattr(scr, "default_value", 0.0), scr.keyframe_insert("default_value", frame=1)))
    S.at(8.0, lambda fr: (scr.keyframe_insert("default_value", frame=fr - 2), setattr(scr, "default_value", 1.4), scr.keyframe_insert("default_value", frame=fr)))
    return S

@shot("10F")
def s_10F():
    S = Shot("10F", extra_state={"new_stain": True, "door_open": True}); S.fstop = 5.6; act4_standoff(S); S.exposure = -3.5
    for n in ("martin", "dao", "andy"): S.seat(n)
    S.key("do", 0, "stand_gun", loc=(-0.2, -0.95, 0), face=(0.5, -1))
    for n in ("ceiling", "hall_ceiling", "pendant_cord"): OBJ(n).visible_camera = False
    vs = bpy.context.scene.view_settings
    S.at(0, lambda fr: (setattr(vs, "exposure", -3.0), vs.keyframe_insert("exposure", frame=1), setattr(vs, "exposure", -0.8), vs.keyframe_insert("exposure", frame=S.f(3.5))))
    S.camera(0, Vector(OVER[0]), Vector(OVER[1]), 24, ease=0.0001)
    S.camera(S.dur, Vector((0.9, -1.0, 6.2)), Vector((0.8, -2.0, 0.0)), 24, ease=1.0)
    return S

# ---- shots built in post (not Blender): 0-0, 0C, CREDITS

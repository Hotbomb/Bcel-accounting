# THE STAIN — set, characters, lights. Import from scripts run with /opt/bpyenv/bin/python.
# World: meters, Z up. Window wall at y=+3.5 (north), hallway opens from the south wall (y=-3) at x 0.6..1.8.
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler, Quaternion

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TEX = os.path.join(ROOT, "assets", "tex")

# ------------------------------------------------------------------ helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear(); PROP_POS.clear()

def link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o); return o

_mats = {}
PROP_POS = {}
def clay(name, rgb, rough=0.6, bump=0.04, metal=0.0, emit=0.0, emit_rgb=None):
    key = (name, tuple(rgb), rough, bump, metal, emit)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = 0.25 if not metal else 0.5
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_rgb or rgb), 1); b.inputs["Emission Strength"].default_value = emit
    if bump:
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 60; n.inputs["Detail"].default_value = 3
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    _mats[key] = m; return m

def img(name):
    p = os.path.join(TEX, name)
    for i in bpy.data.images:
        if i.filepath == p: return i
    return bpy.data.images.load(p)

def tex_mat(name, image, rough=0.7, emit=0.0, alpha=False, scale=(1, 1), bump=0.0, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(image)
    if scale != (1, 1):
        mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord")
        mp.inputs["Scale"].default_value = (scale[0], scale[1], 1)
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    col = t.outputs["Color"]
    if tint:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
        mx.inputs[7].default_value = (*tint, 1); nt.links.new(col, mx.inputs[6]); col = mx.outputs[2]
    nt.links.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(col, b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    if alpha:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"]); b.inputs["Specular IOR Level"].default_value = 0.05; b.inputs["Roughness"].default_value = 0.9
    if bump:
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(t.outputs["Color"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def emission_only(name, rgb, strength, camera_only=False, transparent_mix=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1); em.inputs["Strength"].default_value = strength
    shader = em.outputs[0]
    if camera_only:  # soft edges: fade where the surface turns away from the camera
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = strength
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0
        nt.links.new(lw.outputs["Facing"], inv.inputs[1]); nt.links.new(inv.outputs[0], pw.inputs[0]); nt.links.new(pw.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], em.inputs["Strength"])
    if transparent_mix or camera_only:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ad = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); shader = ad.outputs[0]
        if camera_only:
            lp = nt.nodes.new("ShaderNodeLightPath"); mx = nt.nodes.new("ShaderNodeMixShader")
            tr2 = nt.nodes.new("ShaderNodeBsdfTransparent")
            nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(tr2.outputs[0], mx.inputs[1]); nt.links.new(shader, mx.inputs[2])
            shader = mx.outputs[0]
    nt.links.new(shader, out.inputs["Surface"]); return m

def mesh_obj(name, verts, faces, mat=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); link(o)
    if mat: me.materials.append(mat)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return o

def box(name, size, loc, mat, bevel=0.0, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); o.location = loc; o.rotation_euler = rot
    me.materials.append(mat)
    if bevel:
        md = o.modifiers.new("bev", "BEVEL"); md.width = bevel; md.segments = 3; md.limit_method = "NONE"
    return o

def capsule(name, radius, length, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), seg=16):
    """Capsule along local Z from 0 to length (base at origin)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=radius)
    for v in bm.verts:
        if v.co.z > 0: v.co.z += max(length - 2 * radius, 0)
        v.co.z += radius
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); link(o); o.location = loc; o.rotation_euler = rot; o.scale = scale
    me.materials.append(mat); return o

def sphere(name, r, loc, mat, scale=(1, 1, 1), seg=24):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); link(o); o.location = loc; o.scale = scale; me.materials.append(mat); return o

def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), seg=24, r2=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = abs(p.normal.z) < 0.9
    o = bpy.data.objects.new(name, me); link(o); o.location = loc; o.rotation_euler = rot; me.materials.append(mat); return o

def plane(name, w, h, loc, mat, rot=(0, 0, 0)):
    v = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
    o = mesh_obj(name, v, [(0, 1, 2, 3)], mat); o.location = loc; o.rotation_euler = rot
    uv = o.data.uv_layers.new();
    for i, l in enumerate(o.data.loops): uv.data[i].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][l.vertex_index]
    return o

def decal(name, image, w, h, loc, rot=(0, 0, 0), rough=0.5, emit=0.0):
    return plane(name, w, h, loc, tex_mat(name, image, rough, emit=emit, alpha=True), rot)

def set_vis(o, visible):
    o.hide_render = not visible; o.hide_viewport = not visible
    for c in o.children: set_vis(c, visible)

def key_vis(o, frame, visible):
    o.hide_render = not visible; o.keyframe_insert("hide_render", frame=frame)
    for c in o.children: key_vis(c, frame, visible)

# ------------------------------------------------------------------ colors
K2700 = (1.0, 0.66, 0.38); K1800 = (1.0, 0.45, 0.14); K4000 = (1.0, 0.83, 0.66); CITY = (0.55, 0.7, 1.0)
CANDLE_FLAME = (1.0, 0.55, 0.18)

# ------------------------------------------------------------------ the set
SEATS = {  # seat center (x,y), facing vector
    "martin": ((-0.55, 1.32), (0, -1)),
    "dao":    ((-0.55, -0.52), (0, 1)),
    "do":     ((0.55, -0.52), (0, 1)),
    "andy":   ((1.58, 0.40), (-1, 0)),
    "empty":  ((0.55, 1.32), (0, -1)),
}
TABLE_C = Vector((0, 0.4, 0)); TABLE_TOP = 0.775
CORK_SPOT = Vector((-1.3, 3.49, 1.42))       # cork hit = bullet hole (window)
CURTAIN_Y = 3.30
HOLE_SPOT = Vector((-1.3, CURTAIN_Y - 0.06, 1.42))
BEAM_END = Vector((-1.95, 0.75, 0.0))          # where the pin of light lands (the rug, where the gun will lie)
VASE_FLOOR = Vector((-1.15, -0.35, 0.0))         # 5A / 7B exact vase floor position
GUN_RUG = Vector((-1.85, 0.85, 0.012))           # gun rests in the pin of light
BODY_POS = Vector((1.2, -5.2, 0.0))              # body in the hallway

def build_set(st):
    """st: continuity state dict (see continuity())."""
    sc = bpy.context.scene
    wood = tex_mat("wood", "wood.png", 0.45, scale=(3, 3), bump=0.02)
    wall = clay("wall", (0.78, 0.75, 0.69), 0.85, 0.02)
    accent = clay("accent", (0.42, 0.33, 0.27), 0.8, 0.12)
    dark_wood = clay("darkwood", (0.16, 0.09, 0.05), 0.5, 0.03)
    # floor + rug
    fl = plane("floor", 8.4, 7.0, (0, 0.25, 0), wood)
    fl.data.uv_layers[0].data.foreach_set("uv", [c for l in fl.data.loops for c in [(0, 0), (4, 0), (4, 3.5), (0, 3.5)][l.vertex_index]])
    rug = box("rug", (3.8, 2.9, 0.01), (-0.2, 0.4, 0.005), clay("rug", (0.32, 0.12, 0.09), 0.95, 0.3))
    plane("ceiling", 8.4, 7.0, (0, 0.25, 2.8), clay("ceil", (0.8, 0.78, 0.74), 0.9, 0), rot=(math.pi, 0, 0))
    # walls (north wall has the window opening x -3.2..1.2)
    box("wall_W", (0.1, 7.0, 2.8), (-4.05, 0.25, 1.4), wall)
    box("wall_E", (0.1, 7.0, 2.8), (4.05, 0.25, 1.4), accent)
    box("wall_N_l", (0.8, 0.1, 2.8), (-3.6, 3.55, 1.4), wall)
    box("wall_N_r", (2.8, 0.1, 2.8), (2.6, 3.55, 1.4), wall)
    box("wall_N_t", (4.4, 0.1, 0.12), (-1.0, 3.55, 2.74), wall)
    box("wall_N_b", (4.4, 0.1, 0.06), (-1.0, 3.55, 0.03), wall)
    box("wall_S_l", (4.6, 0.1, 2.8), (-1.7, -3.05, 1.4), wall)
    box("wall_S_r", (2.2, 0.1, 2.8), (2.9, -3.05, 1.4), wall)
    box("wall_S_t", (1.2, 0.1, 0.25), (1.2, -3.05, 2.675), wall)
    # window frame + glass + city
    fr = clay("frame", (0.1, 0.1, 0.11), 0.4, 0)
    for x in (-3.2, -2.1, 0.1, 1.2):
        box(f"mull_{x}", (0.06, 0.12, 2.6), (x, 3.52, 1.35), fr)
    box("sill", (4.5, 0.14, 0.06), (-1.0, 3.5, 0.06), fr)
    box("head", (4.5, 0.14, 0.06), (-1.0, 3.5, 2.66), fr)
    gm = bpy.data.materials.new("glass"); gm.use_nodes = True; nt = gm.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o = nt.nodes.new("ShaderNodeOutputMaterial"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.05; mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.07
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
    glass = plane("glass", 4.4, 2.6, (-1.0, 3.5, 1.35), gm, rot=(math.pi / 2, 0, 0))
    glass.visible_shadow = False
    city = plane("city", 34, 14, (-1.0, 14.0, 3.0), tex_mat("city", "city.png", emit=1.6), rot=(math.pi / 2, 0, 0))
    city.visible_shadow = False; city.visible_diffuse = False
    if st["window"] == "scuff":
        decal("cork_scuff", "cork_scuff.png", 0.06, 0.06, CORK_SPOT + Vector((0, -0.012, 0)), rot=(math.pi / 2, 0, 0))
    elif st["window"] == "hole":
        decal("bullet_hole", "bullet_hole.png", 0.55, 0.55, CORK_SPOT + Vector((0, -0.012, 0)), rot=(math.pi / 2, 0, 0), rough=0.2, emit=0.15)
    # curtains
    build_curtains(st)
    # table + cloth
    tw, td = 2.2, 1.0
    box("table_top", (tw, td, 0.04), (TABLE_C.x, TABLE_C.y, 0.74), dark_wood, 0.005)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"tleg{sx}{sy}", (0.06, 0.06, 0.72), (TABLE_C.x + sx * (tw / 2 - 0.08), TABLE_C.y + sy * (td / 2 - 0.08), 0.36), dark_wood)
    if st["cloth_on_table"]:
        build_tablecloth(st)
    # chairs
    for k, ((x, y), f) in SEATS.items():
        if st.get("chair_fallen") == k: build_chair(k, x, y, f, dark_wood, fallen=True)
        else: build_chair(k, x, y, f, dark_wood)
    build_props(st)
    build_furniture(st, wall, dark_wood)
    build_hallway(st, wall)

def build_curtains(st):
    fab = clay("curtain", (0.36, 0.30, 0.26), 0.9, 0.25)
    rod = cyl("rod", 0.015, 5.4, (-1.0, CURTAIN_Y, 2.66), clay("rod", (0.15, 0.15, 0.15), 0.3, 0, 0.8), rot=(0, math.pi / 2, 0))
    nx, nz = 64, 2
    def panel(name, anchor, sign):
        v, f = [], []
        for i in range(nx + 1):
            for j in range(nz + 1):
                v.append((i / nx, 0, j / nz))
        for i in range(nx):
            for j in range(nz):
                a = i * (nz + 1) + j; f.append((a, a + nz + 1, a + nz + 2, a + 1))
        o = mesh_obj(name, v, f, fab, smooth=True)
        me = o.data
        o.shape_key_add(name="open"); closed = o.shape_key_add(name="closed")
        for i in range(nx + 1):
            for j in range(nz + 1):
                idx = i * (nz + 1) + j; u = i / nx; z = 0.06 + j / nz * 2.56
                # open: bunched, deep folds, 0.62 wide; closed: 2.62 wide, gentle folds
                wo, wc = 0.62, 2.62
                o.data.shape_keys.key_blocks["open"].data[idx].co = (anchor + sign * u * wo, CURTAIN_Y - 0.06 * math.sin(u * 40) - 0.02, z)
                closed.data[idx].co = (anchor + sign * u * wc, CURTAIN_Y - 0.03 * math.sin(u * 26) - 0.03, z)
        return o
    L = panel("curtain_L", -3.62, 1); R = panel("curtain_R", 1.62, -1)
    for p in (L, R):
        p.data.shape_keys.key_blocks["closed"].value = 1.0 if st["curtains"] == "closed" else 0.0
    if st["curtain_hole"]:
        # where u = (-1.3+3.62)/2.62 on the left panel: fold offset
        u = (HOLE_SPOT.x + 3.62) / 2.62; yy = CURTAIN_Y - 0.03 * math.sin(u * 26) - 0.03 - 0.008
        h = decal("curtain_hole", "curtain_hole.png", 0.05, 0.05, (HOLE_SPOT.x, yy, HOLE_SPOT.z), rot=(math.pi / 2, 0, 0))
        h.visible_shadow = False
    return L, R

def curtain_anim(frame_open, frame_closed):
    for n in ("curtain_L", "curtain_R"):
        kb = bpy.data.objects[n].data.shape_keys.key_blocks["closed"]
        kb.value = 0.0; kb.keyframe_insert("value", frame=frame_open)
        kb.value = 1.0; kb.keyframe_insert("value", frame=frame_closed)

def build_tablecloth(st):
    lin = tex_mat("linen", "linen.png", 0.85, scale=(4, 2), tint=(0.96, 0.95, 0.92))
    w, d, drop = 2.5, 1.3, 0.28; z = TABLE_TOP
    cx, cy = TABLE_C.x, TABLE_C.y
    v = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
         (-w / 2, -d / 2, -drop), (w / 2, -d / 2, -drop), (w / 2, d / 2, -drop), (-w / 2, d / 2, -drop)]
    f = [(0, 1, 2, 3), (4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)]
    o = mesh_obj("tablecloth", v, f, lin); o.location = (cx, cy, z)
    uv = o.data.uv_layers.new()
    for i, l in enumerate(o.data.loops):
        x, y, zz = v[l.vertex_index]; uv.data[i].uv = ((x + w / 2) / w, (y + d / 2) / d + zz)
    md = o.modifiers.new("bev", "BEVEL"); md.width = 0.02; md.segments = 3
    # stains on the cloth (top surface)
    zt = z + 0.002
    if st["wine_stain"]:
        decal("wine_stain", "stain_wine.png", 0.34, 0.34, (0.02, 0.64, zt), rot=(0, 0, 0.4))
    if st["blood_drops"]:
        decal("blood_drops", "blood_drops.png", 0.22, 0.22, (-0.5, 0.75, zt + 0.0005))
    if st.get("new_stain"):
        decal("new_stain", "stain_dark.png", 0.55, 0.55, (0.0, 0.42, zt + 0.001), rot=(0, 0, 1.1))
    return o

def build_chair(k, x, y, f, mat, fallen=False):
    root = bpy.data.objects.new(f"chair_{k}", None); link(root)
    root.location = (x, y, 0); root.rotation_euler = (0, 0, math.atan2(f[0], -f[1]))
    parts = [box(f"cseat_{k}", (0.44, 0.44, 0.05), (0, 0, 0.45), mat, 0.01),
             box(f"cback_{k}", (0.44, 0.04, 0.5), (0, 0.21, 0.72), mat, 0.01)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(f"cleg_{k}{sx}{sy}", (0.04, 0.04, 0.45), (sx * 0.19, sy * 0.19, 0.225), mat))
    for p in parts: p.parent = root
    if fallen:
        root.rotation_euler = (math.pi / 2 * 0.98, 0, root.rotation_euler.z + 0.4); root.location.z = 0.02
    return root

PROP_POS = {}
def build_props(st):
    glass_m = clay("wineglass", (0.85, 0.9, 0.95), 0.05, 0)
    wine_m = clay("wine", (0.3, 0.02, 0.05), 0.1, 0)
    z = TABLE_TOP
    # place settings
    places = {"martin": (-0.55, 0.72), "dao": (-0.55, 0.08), "do": (0.55, 0.08), "andy": (0.92, 0.4)}
    plate_m = clay("plate", (0.93, 0.92, 0.88), 0.3, 0)
    for k, (x, y) in places.items():
        cyl(f"plate_{k}", 0.12, 0.015, (x, y, z + 0.008), plate_m, seg=32)
        if st["glasses"].get(k, "up") == "up":
            g = make_wineglass(f"glass_{k}", (x + 0.17, y + (0.1 if y < 0.4 else -0.1), z), glass_m, wine_m if st["wine_in_glass"].get(k) else None)
        elif st["glasses"].get(k) == "down":
            g = make_wineglass(f"glass_{k}", (x + 0.17, y, z + 0.04), glass_m, None); g.rotation_euler = (math.pi / 2, 0, 0.6)
        PROP_POS[k] = (x, y)
    # candles
    if st["candles"] != "none":
        wax = clay("wax", (0.92, 0.88, 0.8), 0.5, 0); holder = clay("brass", (0.55, 0.42, 0.2), 0.3, 0, 0.9)
        h = {"tall": 0.26, "low": 0.1, "out": 0.08}.get(st["candles"], 0.26) if st["candles"] != "lit" else 0.26
        for i, x in enumerate((-0.15, 0.2)):
            cyl(f"cholder{i}", 0.035, 0.03, (x, 0.42, z + 0.015), holder)
            cyl(f"candle{i}", 0.014, h, (x, 0.42, z + 0.03 + h / 2), wax)
            lit = st["candles"] in ("lit", "low", "tall") and not (st["candles_out"] and i == 1)
            if st.get("candles_all_out"): lit = False
            if lit:
                fl = sphere(f"flame{i}", 0.011, (x, 0.42, z + 0.03 + h + 0.018), emission_only("flame", CANDLE_FLAME, 25), scale=(1, 1, 2))
                fl.visible_shadow = False
                bpy.ops.object.light_add(type="POINT", location=(x, 0.42, z + 0.03 + h + 0.03))
                L = bpy.context.active_object; L.name = f"candle_light{i}"; L.data.energy = 3.5 * st["candle_mult"]
                L.data.color = K1800; L.data.shadow_soft_size = 0.01
    # vase (center-left) or on the floor
    vm = clay("vase", (0.2, 0.32, 0.36), 0.25, 0)
    if st["vase"] == "table":
        make_vase((-0.32, 0.55, z), vm)
    elif st["vase"] == "floor":
        v = make_vase((0, 0, 0), vm); v.location = VASE_FLOOR + Vector((0, 0, 0.075)); v.rotation_euler = (math.pi / 2, 0, 0.7)
    # wine bottles
    bot = clay("bottle", (0.06, 0.12, 0.06), 0.15, 0)
    if st["wine_bottle"]:
        cyl("wine_bottle", 0.038, 0.24, (0.35, 0.62, z + 0.12), bot); cyl("wine_neck", 0.014, 0.1, (0.35, 0.62, z + 0.29), bot)
    if st["champagne"]:
        cyl("champ", 0.04, 0.26, (0.8, 0.15, z + 0.13), clay("champ", (0.08, 0.2, 0.1), 0.15, 0))
        cyl("champ_neck", 0.015, 0.1, (0.8, 0.15, z + 0.31), clay("champ", (0.08, 0.2, 0.1), 0.15, 0))
    if st["cake"]:
        cyl("cake", 0.13, 0.11, (0.55, 0.22, z + 0.055), clay("cake", (0.95, 0.9, 0.85), 0.5, 0.05))
        cyl("cake_top", 0.13, 0.015, (0.55, 0.22, z + 0.115), clay("cakeberry", (0.6, 0.1, 0.15), 0.5, 0.05))
    if st["ring_box_on_table"]:
        box("ring_box", (0.06, 0.06, 0.045), (-0.15, 0.62, z + 0.0225), clay("ringbox", (0.35, 0.03, 0.06), 0.6, 0.05), 0.008)
    if st["gun"] == "table":
        make_gun("gun", (-0.2, 0.25, z + 0.01), (0, 0, 0.6))
    elif st["gun"] == "rug":
        make_gun("gun", GUN_RUG, (0, 0, 2.3))
    if st["do_phone_on_table"]:
        make_phone("do_phone", (0.25, 0.08, z + 0.005), (0, 0, 0.15), screen=st["do_phone_on_table"], lit=False)

def make_wineglass(name, loc, glass_m, wine_m):
    root = bpy.data.objects.new(name, None); link(root); root.location = loc
    parts = [cyl(name + "_foot", 0.035, 0.006, (0, 0, 0.003), glass_m), cyl(name + "_stem", 0.005, 0.09, (0, 0, 0.05), glass_m),
             cyl(name + "_bowl", 0.04, 0.09, (0, 0, 0.14), glass_m, r2=0.034)]
    if wine_m: parts.append(cyl(name + "_wine", 0.036, 0.03, (0, 0, 0.115), wine_m))
    for p in parts: p.parent = root
    return root

def make_vase(loc, mat):
    root = bpy.data.objects.new("vase", None); link(root); root.location = loc
    v = cyl("vase_body", 0.06, 0.2, (0, 0, 0.1), mat, r2=0.035); v.parent = root
    fm = [clay("flower_w", (0.95, 0.93, 0.88), 0.6, 0), clay("flower_r", (0.7, 0.08, 0.12), 0.6, 0)]
    for i in range(5):
        a = i * 1.26
        s = sphere(f"flower{i}", 0.035, (0.04 * math.cos(a), 0.04 * math.sin(a), 0.27 + 0.02 * (i % 2)), fm[i % 2]); s.parent = root
    return root

def make_gun(name, loc, rot):
    gm = clay("gun", (0.04, 0.04, 0.045), 0.35, 0.02, 0.6)
    root = bpy.data.objects.new(name, None); link(root); root.location = loc; root.rotation_euler = rot
    for p in [box(name + "_slide", (0.17, 0.03, 0.035), (0.02, 0, 0.03), gm, 0.004),
              box(name + "_grip", (0.04, 0.028, 0.11), (-0.05, 0, -0.02), gm, 0.006),
              box(name + "_guard", (0.04, 0.01, 0.025), (0.0, 0, -0.005), gm, 0.003)]:
        p.parent = root
    root.rotation_euler = (math.pi / 2 if loc[2] < 0.5 or loc[2] > 0.7 else math.pi / 2, rot[1], rot[2])
    return root

def make_phone(name, loc, rot, screen=None, lit=True):
    root = bpy.data.objects.new(name, None); link(root); root.location = loc; root.rotation_euler = rot
    b = box(name + "_body", (0.075, 0.155, 0.008), (0, 0, 0.004), clay("phone", (0.05, 0.05, 0.06), 0.3, 0), 0.003); b.parent = root
    if screen:
        s = plane(name + "_screen", 0.068, 0.147, (0, 0, 0.0085), tex_mat(name + "_scr", screen, 0.2, emit=1.2 if lit else 0.0)); s.parent = root
        s.visible_shadow = False
    return root

def build_furniture(st, wall, dark_wood):
    sofa_m = clay("sofa", (0.33, 0.35, 0.32), 0.9, 0.15)
    box("sofa_base", (0.9, 2.0, 0.42), (-3.4, 1.9, 0.21), sofa_m, 0.05); box("sofa_back", (0.25, 2.0, 0.45), (-3.78, 1.9, 0.6), sofa_m, 0.08)
    box("sofa_arm1", (0.9, 0.2, 0.25), (-3.4, 0.95, 0.5), sofa_m, 0.08); box("sofa_arm2", (0.9, 0.2, 0.25), (-3.4, 2.85, 0.5), sofa_m, 0.08)
    # bookshelf on the west wall (south part), with the Huis Clos spine
    box("shelf", (0.35, 1.4, 2.0), (-3.82, -1.3, 1.0), dark_wood)
    import random; r = random.Random(3)
    cols = [(0.5, 0.15, 0.1), (0.15, 0.25, 0.4), (0.7, 0.6, 0.4), (0.2, 0.3, 0.2), (0.6, 0.55, 0.5), (0.1, 0.1, 0.1)]
    for row, zz in enumerate((0.25, 0.7, 1.15, 1.6)):
        yy = -1.95
        while yy < -0.7:
            w = r.uniform(0.025, 0.05); h = r.uniform(0.25, 0.34)
            name = f"book_{row}_{yy:.2f}"
            if row == 2 and -1.45 < yy < -1.38 and "huis" not in st.get("_done", ""):
                st["_done"] = "huis"
                b = box("book_huis_clos", (0.22, 0.05, 0.32), (-3.7, yy + 0.025, zz + 0.16), clay("huis", (0.75, 0.68, 0.5), 0.6, 0))
                lab = plane("huis_label", 0.3, 0.045, (-3.588, yy + 0.025, zz + 0.16), tex_mat("huis_lab", "huis_clos.png", 0.6), rot=(math.pi / 2, -math.pi / 2, math.pi / 2))
                yy += 0.05; continue
            box(name, (0.22, w, h), (-3.7, yy + w / 2, zz + h / 2), clay("book", cols[r.randrange(len(cols))], 0.7, 0)); yy += w + 0.002
    # sideboard (south wall, west) with speaker, Martin's phone, table lamp
    box("sideboard", (1.6, 0.45, 0.8), (-2.2, -2.75, 0.4), dark_wood, 0.01)
    box("speaker", (0.18, 0.12, 0.26), (-2.7, -2.75, 0.93), clay("spk", (0.08, 0.08, 0.08), 0.6, 0.05), 0.02)
    make_phone("martin_phone", (-2.3, -2.7, 0.81), (0, 0, 0.3), screen=None)
    cyl("tlamp_base", 0.08, 0.35, (-1.7, -2.75, 0.975), clay("lampbase", (0.6, 0.55, 0.45), 0.4, 0))
    cyl("tlamp_shade", 0.18, 0.25, (-1.7, -2.75, 1.27), clay("shade", (0.95, 0.88, 0.75), 0.9, 0, emit=st["lamp_emit"], emit_rgb=K2700), r2=0.13)
    # floor lamp (south-east, behind Do) – can be knocked over
    fl = bpy.data.objects.new("floorlamp", None); link(fl); fl.location = (2.1, -1.35, 0)
    parts = [cyl("fl_base", 0.16, 0.03, (0, 0, 0.015), clay("flbase", (0.1, 0.1, 0.1), 0.4, 0, 0.6)),
             cyl("fl_pole", 0.012, 1.5, (0, 0, 0.75), clay("flbase", (0.1, 0.1, 0.1), 0.4, 0, 0.6)),
             cyl("fl_shade", 0.22, 0.3, (0, 0, 1.55), clay("shade", (0.95, 0.88, 0.75), 0.9, 0, emit=st["floorlamp_emit"], emit_rgb=K2700), r2=0.16)]
    for p in parts: p.parent = fl
    if st["floorlamp"] == "fallen":
        fl.rotation_euler = (0, -math.pi / 2 * 0.97, -0.5); fl.location = (2.1, -1.35, 0.2)
    # wall clock (south wall, east)
    cyl("clock", 0.17, 0.04, (2.8, -2.98, 2.0), clay("clockface", (0.92, 0.9, 0.85), 0.4, 0), rot=(math.pi / 2, 0, 0))
    cyl("clock_rim", 0.18, 0.03, (2.8, -2.99, 2.0), clay("rim", (0.1, 0.1, 0.1), 0.3, 0), rot=(math.pi / 2, 0, 0))
    hm = clay("hand", (0.05, 0.05, 0.05), 0.4, 0)
    box("clock_h", (0.012, 0.004, 0.09), (2.8, -2.955, 2.04), hm, rot=(0, 0.8, 0)); box("clock_m", (0.008, 0.004, 0.14), (2.8, -2.953, 2.06), hm, rot=(0, -0.4, 0))
    # dark TV on the accent wall
    box("tv", (0.04, 1.3, 0.75), (3.98, 0.4, 1.45), clay("tv", (0.01, 0.01, 0.012), 0.08, 0))
    # pendant over the table
    cyl("pendant_cord", 0.004, 0.75, (0, 0.4, 2.42), clay("cord", (0.05, 0.05, 0.05), 0.5, 0))
    cyl("pendant_shade", 0.06, 0.2, (0, 0.4, 1.95), clay("pshade", (0.12, 0.1, 0.08), 0.35, 0, 0.7), r2=0.24, seg=40)
    pb = cyl("pendant_bulb", 0.22, 0.005, (0, 0.4, 1.853), emission_only("pbulb", K2700, st["pendant_emit"]), seg=40)
    pb.visible_shadow = False

def build_hallway(st, wall):
    tile = tex_mat("tile", "tile.png", 0.35, scale=(3, 12))
    f = plane("hall_floor", 1.2, 5.0, (1.2, -5.5, 0.001), tile)
    plane("hall_ceiling", 1.2, 5.0, (1.2, -5.5, 2.6), clay("ceil", (0.8, 0.78, 0.74), 0.9, 0), rot=(math.pi, 0, 0))
    box("hall_wall_W", (0.1, 5.0, 2.6), (0.55, -5.5, 1.3), wall)
    box("hall_wall_E", (0.1, 5.0, 2.6), (1.85, -5.5, 1.3), wall)
    # front door at y=-8
    dm = clay("door", (0.25, 0.17, 0.11), 0.5, 0.03)
    box("door_frame_t", (1.2, 0.12, 0.2), (1.2, -8.0, 2.5), wall)
    pivot = bpy.data.objects.new("front_door", None); link(pivot); pivot.location = (0.66, -7.98, 0)
    d = box("door_slab", (0.86, 0.05, 2.1), (0.45, 0, 1.05), dm, 0.005); d.parent = pivot
    k = sphere("door_knob", 0.03, (0.8, 0.04, 1.0), clay("brass", (0.55, 0.42, 0.2), 0.3, 0, 0.9)); k.parent = pivot
    box("door_wall_l", (0.08, 0.1, 2.4), (0.6, -8.0, 1.2), wall); box("door_wall_r", (0.25, 0.1, 2.4), (1.72, -8.0, 1.2), wall)
    plane("outside_dark", 3, 3, (1.2, -8.6, 1.3), clay("void", (0, 0, 0), 1, 0), rot=(math.pi / 2, 0, 0))
    if st["door_open"]: pivot.rotation_euler.z = -0.5
    # hallway ceiling fixture + bulb
    cyl("hall_fixture", 0.07, 0.04, (1.2, -5.0, 2.58), clay("fix", (0.85, 0.85, 0.82), 0.5, 0))
    hb = sphere("hall_bulb", 0.045, (1.2, -5.0, 2.52), emission_only("hbulb", K4000, 12)); hb.visible_shadow = False

# ------------------------------------------------------------------ lights
def build_lights(st):
    sc = bpy.context.scene
    L = {}
    def area(name, loc, rot, energy, size, color, spread=None, shape="DISK"):
        bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot); o = bpy.context.active_object; o.name = name
        o.data.energy = energy; o.data.size = size; o.data.color = color; o.data.shape = shape
        if spread: o.data.spread = spread
        o.visible_camera = False
        L[name] = o; return o
    def point(name, loc, energy, color, radius=0.05):
        bpy.ops.object.light_add(type="POINT", location=loc); o = bpy.context.active_object; o.name = name
        o.data.energy = energy; o.data.color = color; o.data.shadow_soft_size = radius; L[name] = o; return o
    s = st["light"]
    if s in ("act1", "candles"):
        k = 1.0 if s == "act1" else 0.25
        area("key", (0, 0.4, 1.84), (0, 0, 0), 140 * k, 0.6, K2700)
        point("fill_lamp", (2.1, -1.35, 1.5), 60 * k, K2700, 0.2)
        point("fill_side", (-1.7, -2.75, 1.25), 40 * k, K2700, 0.15)
        area("bounce", (0, 0.4, 2.75), (math.pi, 0, 0), 45 * k, 3.0, K2700)
        area("rim_city", (-1.0, 3.9, 1.6), (math.radians(80), 0, math.pi), 240 * (1 if s == "act1" else 0.6), 4.0, CITY, shape="RECTANGLE")
        L["rim_city"].data.size_y = 2.4
        bpy.ops.object.light_add(type="AREA", location=(1.2, -5.0, 2.5)); h = bpy.context.active_object; h.name = "hall_bulb_light"
        h.data.energy = 25; h.data.size = 0.1; h.data.color = K4000; L["hall"] = h
    elif s == "act2":
        area("key", (0, 0.4, 1.84), (0, 0, 0), 150, 0.3, K2700, spread=math.radians(110))
        if st["curtains"] == "open":
            area("rim_city", (-1.0, 3.9, 1.6), (math.radians(80), 0, math.pi), 240, 4.0, CITY, shape="RECTANGLE"); L["rim_city"].data.size_y = 2.4
        if st["floorlamp"] != "fallen": point("fill_lamp", (2.1, -1.35, 1.5), 50, K2700, 0.2)
        point("fill_side", (-1.7, -2.75, 1.25), 18, K2700, 0.15)
        area("bounce", (0, 0.4, 2.75), (math.pi, 0, 0), 25, 3.0, K2700)
        bpy.ops.object.light_add(type="AREA", location=(1.2, -5.0, 2.5)); h = bpy.context.active_object; h.name = "hall_bulb_light"
        h.data.energy = 22; h.data.size = 0.1; h.data.color = K4000; L["hall"] = h
    elif s == "act3":
        area("key", (0, 0.4, 1.84), (0, 0, 0), 150, 0.18, K2700, spread=math.radians(80))
        area("bounce", (0, 0.4, 2.75), (math.pi, 0, 0), 8, 3.0, K2700)
        bpy.ops.object.light_add(type="AREA", location=(1.2, -5.0, 2.5)); h = bpy.context.active_object; h.name = "hall_bulb_light"
        h.data.energy = 22; h.data.size = 0.1; h.data.color = K4000; L["hall"] = h
        bpy.ops.object.light_add(type="AREA", location=(1.2, -2.7, 2.3), rotation=(math.radians(-55), 0, 0)); fc = bpy.context.active_object; fc.name = "fill_cold"
        fc.data.energy = 30; fc.data.size = 1.5; fc.data.color = (0.75, 0.82, 1.0); fc.visible_camera = False; L["fill_cold"] = fc
    elif s == "act34":
        area("key", (0, 0.4, 1.84), (0, 0, 0), 150, 0.15, K2700, spread=math.radians(70))
        area("bounce", (0, 0.4, 2.75), (math.pi, 0, 0), 5, 3.0, K2700)
        bpy.ops.object.light_add(type="AREA", location=(1.2, -5.0, 2.5)); h = bpy.context.active_object; h.name = "hall_bulb_light"
        h.data.energy = 30; h.data.size = 0.1; h.data.color = (1.0, 0.86, 0.62); L["hall"] = h
        bpy.ops.object.light_add(type="AREA", location=(1.2, -2.7, 2.3), rotation=(math.radians(-55), 0, 0)); fc = bpy.context.active_object; fc.name = "fill_cold"
        fc.data.energy = 30; fc.data.size = 1.5; fc.data.color = (0.75, 0.82, 1.0); fc.visible_camera = False; L["fill_cold"] = fc
    if st["beam"]:
        build_beam(L)
    w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.005, 0.008, 1)
    return L

def build_beam(L):
    d = (BEAM_END - HOLE_SPOT); length = d.length; dn = d.normalized()
    # visible shaft (camera rays only)
    c = cyl("beam_shaft", 0.012, length, (0, 0, 0), emission_only("beam", (0.6, 0.75, 1.0), 0.06, camera_only=True, transparent_mix=1), r2=0.09, seg=16)
    q = Vector((0, 0, -1)).rotation_difference(dn)
    c.rotation_mode = "QUATERNION"; c.rotation_quaternion = q; c.location = HOLE_SPOT + dn * length / 2
    c.visible_shadow = False; c.visible_diffuse = False; c.visible_glossy = False
    # real light: narrow spot just inside the curtain
    bpy.ops.object.light_add(type="SPOT", location=HOLE_SPOT + dn * 0.03); s = bpy.context.active_object; s.name = "beam_spot"
    s.rotation_mode = "QUATERNION"; s.rotation_quaternion = q
    s.data.energy = 60; s.data.spot_size = math.radians(1.6); s.data.spot_blend = 0.3; s.data.color = (0.7, 0.82, 1.0); s.data.shadow_soft_size = 0.0
    L["beam"] = s; L["beam_shaft"] = c

# ------------------------------------------------------------------ continuity
def continuity(scene_no, shot=None):
    """Prop states from the brief's continuity table (section 4)."""
    sn = scene_no
    st = dict(
        window="clean", curtains="open", curtain_hole=False, vase="table", gun="hidden", ring_box_on_table=False,
        candles="lit", candles_out=False, candles_all_out=False, candle_mult=1.0, door_open=False,
        cloth_on_table=True, wine_stain=False, blood_drops=False, new_stain=False, beam=False,
        glasses={}, wine_in_glass={"martin": False, "dao": True, "andy": False, "do": True}, wine_bottle=True, champagne=True,
        cake=False, do_phone_on_table=None, floorlamp="up", floorlamp_emit=6.0, lamp_emit=5.0, pendant_emit=8.0,
        martin_nose=False, martin_nose_dry=False, andy_cut=False, martin_scratches=False, chair_fallen=None,
        body=False, light="act1",
    )
    if sn >= 1 and shot not in ("1A", "1B", "1C", "1D", "1E", "1F", "1G"): st["wine_stain"] = True
    if sn == 1 and shot in ("1H",): st["wine_stain"] = True
    if sn >= 1 and shot in ("1D",): st["window"] = "clean"
    if (sn == 1 and shot in ("1D", "1E", "1F", "1G", "1H", "1I", "1J", "1K")) or sn in (2, 3): st["window"] = "scuff"
    if shot == "1I": st["cake"] = True; st["light"] = "candles"; st["candle_mult"] = 3.0
    if sn >= 2: st["blood_drops"] = True; st["glasses"] = {"andy": "down"}
    if shot in ("2B",) or (sn == 2 and shot != "2A") or sn == 3: st["martin_nose"] = shot not in ("2A",)
    if sn >= 4:
        st["window"] = "hole"; st["martin_nose"] = True; st["martin_nose_dry"] = True; st["light"] = "act2"
        st["candles"] = "low"; st["champagne"] = False
    if sn >= 4 and shot not in ("4A", "4B", "4C", "4D", "4E"): st["curtains"] = "closed"; st["curtain_hole"] = True; st["beam"] = True
    if shot == "4E": st["curtain_hole"] = True
    if sn >= 4 and shot not in ("4A", "4B"): st["floorlamp"] = "fallen"; st["floorlamp_emit"] = 0.0
    if sn == 5 and shot == "5A": st["vase"] = "floor"
    if sn >= 5 and shot not in ("5A",): st["andy_cut"] = shot not in ("5A",)
    if sn >= 5 and shot not in ("5A", "5B"): st["martin_scratches"] = True
    if sn >= 6 and shot not in ("6A", "6B", "6C"): st["ring_box_on_table"] = True
    if sn >= 7:
        st["light"] = "act3"; st["candles_out"] = True; st["lamp_emit"] = 0.0; st["fill"] = False
        st["gun"] = "table" if shot == "7A" else ("floor" if shot in ("7B",) else "rug")
    if sn >= 7 and shot not in ("7A",): st["vase"] = "floor"
    if sn >= 8: st["gun"] = "held" if shot in ("8A", "8B", "8C") else "rug"
    if sn >= 9:
        st["light"] = "act34"; st["candles_all_out"] = True; st["body"] = True; st["chair_fallen"] = "andy"
        st["gun"] = "rug" if shot in ("9A", "9B", "9C") else "held"
        st["do_phone_on_table"] = "phone_meme.png"
    if shot in ("10C", "10D", "10E", "10F"): st["chair_fallen"] = None; st["wine_in_glass"] = {k: True for k in ("martin", "dao", "andy", "do")}
    if shot in ("10A",) or (sn == 10 and shot not in ()): st["door_open"] = shot != "10A"
    if shot == "10E": st["do_phone_on_table"] = "phone_rip.png"
    if sn >= 9: st["cloth_on_table"] = True  # the table keeps its cloth; the hallway has the "future copy"
    return st

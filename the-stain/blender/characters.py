# Stylized clay puppets with a simple bone rig. Character space: feet at z=0, facing -Y, character's left = +X.
import bpy, math
from mathutils import Vector, Matrix, Euler, Quaternion
from stain import clay, capsule, sphere, box, cyl, link, emission_only, tex_mat, plane

# joint positions for a 1.75 m puppet (big head)
J = {
    "hips": (0, 0, 0.92), "chest": (0, 0, 1.38), "neck": (0, 0, 1.47), "headtop": (0, 0, 1.86),
    "shoulder.L": (0.2, 0, 1.36), "elbow.L": (0.22, 0, 1.09), "wrist.L": (0.23, 0, 0.85), "hand.L": (0.23, 0, 0.75),
    "hip.L": (0.095, 0, 0.9), "knee.L": (0.095, 0, 0.5), "ankle.L": (0.095, 0, 0.08), "toe.L": (0.095, -0.15, 0.03),
}
def jp(n):
    if n.endswith(".R"): x, y, z = J[n[:-2] + ".L"]; return Vector((-x, y, z))
    return Vector(J[n])
BONES = [  # name, head joint, tail joint, parent
    ("root", None, None, None), ("hips", "hips", None, "root"), ("spine", "hips", "chest", "hips"),
    ("neck", "chest", "neck", "spine"), ("head", "neck", "headtop", "neck"),
]
for s in ("L", "R"):
    BONES += [(f"upper_arm.{s}", f"shoulder.{s}", f"elbow.{s}", "spine"), (f"forearm.{s}", f"elbow.{s}", f"wrist.{s}", f"upper_arm.{s}"),
              (f"hand.{s}", f"wrist.{s}", f"hand.{s}", f"forearm.{s}"),
              (f"thigh.{s}", f"hip.{s}", f"knee.{s}", "hips"), (f"shin.{s}", f"knee.{s}", f"ankle.{s}", f"thigh.{s}"),
              (f"foot.{s}", f"ankle.{s}", f"toe.{s}", f"shin.{s}")]
ORDER = [b[0] for b in BONES]

LOOK = {  # signature colors etc.
    "martin": dict(scale=1.06, width=1.15, skin=(0.33, 0.17, 0.1), top=(0.004, 0.008, 0.04), sleeve=(0.004, 0.008, 0.04), forearm=(0.004, 0.008, 0.04),
                   pants=(0.08, 0.08, 0.1), shoe=(0.05, 0.03, 0.02), hair=(0.01, 0.007, 0.006), hair_style="neat", collar=(0.9, 0.9, 0.88)),
    "dao": dict(scale=0.95, width=0.86, skin=(0.42, 0.23, 0.15), top=(0.2, 0.006, 0.025), sleeve=(0.2, 0.006, 0.025), forearm=None,
                pants=(0.2, 0.006, 0.025), shoe=(0.12, 0.02, 0.03), hair=(0.009, 0.006, 0.005), hair_style="shoulder", dress=True),
    "andy": dict(scale=1.0, width=1.0, skin=(0.29, 0.15, 0.085), top=(0.13, 0.14, 0.08), sleeve=(0.13, 0.14, 0.08), forearm=(0.13, 0.14, 0.08),
                 pants=(0.14, 0.13, 0.12), shoe=(0.09, 0.06, 0.04), hair=(0.012, 0.009, 0.007), hair_style="side", glasses=True, watch=True),
    "do": dict(scale=0.98, width=0.88, skin=(0.37, 0.2, 0.12), top=(0.8, 0.8, 0.78), sleeve=(0.8, 0.8, 0.78), forearm=None,
               pants=(0.12, 0.14, 0.22), shoe=(0.7, 0.68, 0.65), hair=(0.014, 0.009, 0.006), hair_style="messy", watch=True),
}

class Puppet:
    def __init__(self, name, arm, parts, face):
        self.name, self.arm, self.parts, self.face = name, arm, parts, face
        self.rest_q = {b.name: b.matrix_local.to_quaternion() for b in arm.data.bones}

def build(name, st=None, suffix=""):
    st = st or {}
    lk = LOOK[name]; nm = name + suffix
    ad = bpy.data.armatures.new(nm + "_rig"); arm = bpy.data.objects.new(nm, ad); link(arm)
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for bn, h, t, p in BONES:
        b = ad.edit_bones.new(bn)
        if bn == "root": b.head, b.tail = (0, 0, 0), (0, 0.25, 0)
        elif bn == "hips": b.head, b.tail = jp("hips"), jp("hips") + Vector((0, 0, 0.08))
        else: b.head, b.tail = jp(h), jp(t)
        b.roll = 0
        if p: b.parent = eb[p]; b.use_connect = False
        eb[bn] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones: pb.rotation_mode = "QUATERNION"
    W = lk["width"]
    skin = clay(name + "_skin", lk["skin"], 0.55, 0.03); top = clay(name + "_top", lk["top"], 0.75, 0.06)
    sleeve = clay(name + "_sleeve", lk["sleeve"], 0.75, 0.06); pants = clay(name + "_pants", lk["pants"], 0.8, 0.06)
    shoe = clay(name + "_shoe", lk["shoe"], 0.45, 0.02); hairm = clay(name + "_hair", lk["hair"], 0.5, 0.15)
    fore = clay(name + "_fore", lk["forearm"], 0.75, 0.06) if lk["forearm"] else skin
    parts = {}
    def attach(o, bone):
        o.parent = arm; o.parent_type = "BONE"; o.parent_bone = bone
        b = arm.data.bones[bone]
        M = b.matrix_local @ Matrix.Translation((0, b.length, 0))
        o.matrix_parent_inverse = M.inverted()
        parts.setdefault(bone, []).append(o); return o
    # torso / pelvis
    attach(capsule(nm + "_torso", 0.15, 0.56, top, loc=(0, 0, 0.86), scale=(1.22 * W, 0.82, 1)), "spine")
    attach(capsule(nm + "_pelvis", 0.15, 0.28, pants if not lk.get("dress") else top, loc=(0, 0, 0.8), scale=(1.15 * W, 0.85, 1)), "hips")
    attach(capsule(nm + "_neck", 0.05, 0.14, skin, loc=(0, 0, 1.36)), "neck")
    if lk.get("collar"):
        attach(cyl(nm + "_collar", 0.07, 0.04, (0, 0, 1.43), clay("collar", lk["collar"], 0.6, 0), r2=0.06), "spine")
        for sx in (-1, 1):  # jacket lapels
            attach(box(nm + f"_lapel{sx}", (0.06, 0.02, 0.2), (sx * 0.06, -0.125, 1.28), clay(name + "_lapel", (0.006, 0.012, 0.05), 0.7, 0.05), 0.008, rot=(0.1, 0, sx * 0.3)), "spine")
    # arms / legs
    for s, sx in (("L", 1), ("R", -1)):
        sh, el, wr, hd = jp(f"shoulder.{s}"), jp(f"elbow.{s}"), jp(f"wrist.{s}"), jp(f"hand.{s}")
        attach(capsule(nm + f"_uarm{s}", 0.055, 0.32, sleeve, loc=sh + Vector((0, 0, 0.04)), rot=(math.pi, 0, 0)), f"upper_arm.{s}")
        attach(capsule(nm + f"_farm{s}", 0.047, 0.28, fore, loc=el + Vector((0, 0, 0.02)), rot=(math.pi, 0, 0)), f"forearm.{s}")
        attach(sphere(nm + f"_hand{s}", 0.055, wr + Vector((0, -0.005, -0.06)), skin, scale=(0.75, 0.95, 1.15)), f"hand.{s}")
        attach(sphere(nm + f"_thumb{s}", 0.022, wr + Vector((-sx * 0.0 - 0.0, -0.04, -0.04)), skin), f"hand.{s}")
        if lk.get("watch") and s == "L":
            attach(cyl(nm + "_watch", 0.05, 0.03, wr + Vector((0, 0, 0.04)), clay("watch", (0.6, 0.6, 0.62), 0.25, 0, 0.9)), f"forearm.{s}")
            attach(cyl(nm + "_watchface", 0.022, 0.01, wr + Vector((0, -0.05, 0.04)), clay("watchface", (0.05, 0.05, 0.08), 0.1, 0), rot=(math.pi / 2, 0, 0)), f"forearm.{s}")
        hp, kn, an = jp(f"hip.{s}"), jp(f"knee.{s}"), jp(f"ankle.{s}")
        thick = 0.085 if lk.get("dress") else 0.075
        attach(capsule(nm + f"_thigh{s}", thick, 0.46, pants, loc=hp + Vector((0, 0, 0.04)), rot=(math.pi, 0, 0)), f"thigh.{s}")
        attach(capsule(nm + f"_shin{s}", 0.06, 0.46, skin if lk.get("dress") else pants, loc=kn + Vector((0, 0, 0.03)), rot=(math.pi, 0, 0)), f"shin.{s}")
        attach(box(nm + f"_shoe{s}", (0.1, 0.22, 0.08), an + Vector((0, -0.06, -0.04)), shoe, 0.03), f"foot.{s}")
    if lk.get("dress"):
        attach(cyl(nm + "_skirt", 0.2, 0.22, (0, 0, 0.78), top, r2=0.17), "hips")
    face = build_head(nm, name, lk, skin, hairm, attach, st)
    arm.scale = (lk["scale"],) * 3
    return Puppet(nm, arm, parts, face)

def build_head(nm, name, lk, skin, hairm, attach, st):
    hc = Vector((0, 0, 1.64)); f = {}
    head = attach(sphere(nm + "_head", 0.17, hc, skin, scale=(1.0, 0.95, 1.1), seg=32), "head")
    attach(sphere(nm + "_nose", 0.03, hc + Vector((0, -0.165, -0.02)), skin, scale=(0.9, 1.0, 1.1)), "head")
    for sx in (-1, 1): attach(sphere(nm + f"_ear{sx}", 0.035, hc + Vector((sx * 0.168, 0, -0.01)), skin, scale=(0.5, 1, 1.2)), "head")
    white = clay("eyewhite", (0.95, 0.94, 0.92), 0.25, 0); pupil = clay("pupil", (0.02, 0.015, 0.012), 0.08, 0)
    for s, sx in (("L", 1), ("R", -1)):
        ec = hc + Vector((sx * 0.062, -0.135, 0.035))
        eye = bpy.data.objects.new(nm + f"_eye{s}", None); link(eye); eye.location = ec
        w = sphere(nm + f"_eyew{s}", 0.04, (0, 0, 0), white); w.parent = eye
        p = sphere(nm + f"_pupil{s}", 0.021, (0, -0.031, 0), pupil, scale=(1, 0.5, 1)); p.parent = eye
        hl = sphere(nm + f"_glint{s}", 0.006, (0.008, -0.04, 0.01), emission_only("glint", (1, 1, 1), 2.0)); hl.parent = eye
        eye.rotation_mode = "XYZ"; attach(eye, "head"); f[f"eye{s}"] = eye
        # upper eyelid: half sphere slightly larger than the eye, scale z animates the blink
        lid = sphere(nm + f"_lid{s}", 0.043, (0, 0, 0), skin, seg=24)
        bm_cut_lower_half(lid)
        lid.location = ec; lid.rotation_euler = (math.radians(-35), 0, 0)
        attach(lid, "head"); f[f"lid{s}"] = lid
        brow = capsule(nm + f"_brow{s}", 0.011, 0.07, hairm, loc=(0, 0, 0), rot=(0, math.pi / 2, 0))
        brow.location = ec + Vector((-0.035, -0.01, 0.068)); brow.rotation_mode = "XYZ"
        attach(brow, "head"); f[f"brow{s}"] = brow
    mouth = sphere(nm + "_mouth", 0.04, hc + Vector((0, -0.143, -0.085)), clay("mouth", (0.12, 0.02, 0.03), 0.5, 0), scale=(1.0, 0.22, 0.18))
    attach(mouth, "head"); f["mouth"] = mouth
    # hair
    hs = lk["hair_style"]
    if hs == "neat":
        attach(sphere(nm + "_hair", 0.18, hc + Vector((0, 0.015, 0.04)), hairm, scale=(1.0, 0.98, 0.95)), "head")
        cut_front(bpy.data.objects[nm + "_hair"], hc, -0.06)
    elif hs == "side":
        attach(sphere(nm + "_hair", 0.18, hc + Vector((0, 0.015, 0.045)), hairm, scale=(1.0, 0.97, 0.95)), "head")
        cut_front(bpy.data.objects[nm + "_hair"], hc, -0.05)
        attach(capsule(nm + "_part", 0.04, 0.2, hairm, loc=hc + Vector((0.1, -0.1, 0.12)), rot=(0, math.pi / 2, 0.0), scale=(1, 1, 1)), "head")
    elif hs == "shoulder":
        attach(sphere(nm + "_hair", 0.185, hc + Vector((0, 0.02, 0.03)), hairm, scale=(1.05, 1.0, 1.0)), "head")
        cut_front(bpy.data.objects[nm + "_hair"], hc, -0.03)
        for sx in (-1, 1):
            attach(capsule(nm + f"_lock{sx}", 0.065, 0.32, hairm, loc=hc + Vector((sx * 0.13, 0.0, -0.26)), scale=(0.8, 1.2, 1)), "head")
        attach(capsule(nm + "_back", 0.12, 0.3, hairm, loc=hc + Vector((0, 0.07, -0.25)), scale=(1.3, 0.7, 1)), "head")
    elif hs == "messy":
        attach(sphere(nm + "_hair", 0.18, hc + Vector((0, 0.01, 0.05)), hairm), "head")
        cut_front(bpy.data.objects[nm + "_hair"], hc, -0.05)
        import random; r = random.Random(9)
        for i in range(11):
            a = r.uniform(-2.6, 2.6); el = r.uniform(0.2, 1.2)
            d = Vector((math.sin(a) * math.cos(el), -math.cos(a) * math.cos(el) * 0.6 + 0.2, math.sin(el)))
            attach(sphere(nm + f"_tuft{i}", 0.06, hc + d.normalized() * 0.17 + Vector((0, 0, 0.03)), hairm, scale=(0.8, 0.8, 1.4)), "head")
    if lk.get("glasses"):
        gm = clay("glassesframe", (0.05, 0.04, 0.03), 0.3, 0)
        for sx in (-1, 1):
            t = bpy.data.objects.new(nm + f"_lens{sx}", None)
            bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.006, location=hc + Vector((sx * 0.062, -0.17, 0.035)), rotation=(math.pi / 2, 0, 0))
            g = bpy.context.active_object; g.name = nm + f"_glass{sx}"; g.data.materials.append(gm); attach(g, "head")
        attach(box(nm + "_bridge", (0.03, 0.008, 0.008), hc + Vector((0, -0.172, 0.04)), gm), "head")
    # blood / marks (continuity)
    blood = clay("blood", (0.07, 0.0, 0.006), 0.2, 0)
    f["nose_blood"] = attach(capsule(nm + "_noseblood", 0.008, 0.075, blood, loc=hc + Vector((0.01, -0.153, -0.115)), scale=(1.1, 0.5, 1)), "head")
    f["nose_blood"].hide_render = (not st.get("martin_nose", False)) or name != "martin"
    return f

def bm_cut_lower_half(o):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.002], context="VERTS")
    bm.to_mesh(o.data); bm.free()

def cut_front(o, hc, zcut):
    """Remove the face area from a hair cap: delete verts in front and below the brow line."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = [v for v in bm.verts if (v.co.y < -0.06 and v.co.z < 0.07) or v.co.z < zcut]
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(o.data); bm.free()
    md = o.modifiers.new("solid", "SOLIDIFY"); md.thickness = 0.02

# ------------------------------------------------------------------ posing (absolute directions in character space)
def D(x, y, z): return ("d", Vector((x, y, z)).normalized())
def E(p, r, y): return ("e", Euler((math.radians(p), math.radians(r), math.radians(y)), "XYZ").to_quaternion())

POSES = {
    "stand": {},
    "sit": {"thigh.L": D(0.08, -1, 0.02), "thigh.R": D(-0.08, -1, 0.02), "shin.L": D(0, -0.15, -1), "shin.R": D(0, -0.15, -1),
            "upper_arm.L": D(0.1, -0.45, -1), "upper_arm.R": D(-0.1, -0.45, -1), "forearm.L": D(-0.15, -1, 0.05), "forearm.R": D(0.15, -1, 0.05),
            "hand.L": D(-0.1, -1, -0.1), "hand.R": D(0.1, -1, -0.1), "_hips_drop": 0.37},
    "sit_lap": {"thigh.L": D(0.08, -1, 0.02), "thigh.R": D(-0.08, -1, 0.02), "shin.L": D(0, -0.15, -1), "shin.R": D(0, -0.15, -1),
                "upper_arm.L": D(0.05, -0.25, -1), "upper_arm.R": D(-0.05, -0.25, -1), "forearm.L": D(-0.35, -0.9, -0.15), "forearm.R": D(0.35, -0.9, -0.15),
                "_hips_drop": 0.37},
    "sit_glass": {"thigh.L": D(0.08, -1, 0.02), "thigh.R": D(-0.08, -1, 0.02), "shin.L": D(0, -0.15, -1), "shin.R": D(0, -0.15, -1),
                  "upper_arm.L": D(0.1, -0.45, -1), "upper_arm.R": D(-0.25, -0.6, -0.7), "forearm.L": D(-0.15, -1, 0.05), "forearm.R": D(0.25, -0.35, 0.95),
                  "hand.L": D(-0.1, -1, -0.1), "_hips_drop": 0.37},
    "stand_toast": {"upper_arm.R": D(-0.3, -0.7, 0.3), "forearm.R": D(-0.1, -0.5, 1), "upper_arm.L": D(0.1, 0, -1)},
    "stand_point": {"upper_arm.R": D(-0.05, -1, 0.05), "forearm.R": D(0, -1, 0.05), "hand.R": D(0, -1, 0)},
    "sit_point": {"thigh.L": D(0.08, -1, 0.02), "thigh.R": D(-0.08, -1, 0.02), "shin.L": D(0, -0.15, -1), "shin.R": D(0, -0.15, -1),
                  "upper_arm.R": D(-0.05, -1, 0.1), "forearm.R": D(0, -1, 0.1), "hand.R": D(0, -1, 0), "upper_arm.L": D(0.1, -0.45, -1), "forearm.L": D(-0.15, -1, 0.05),
                  "_hips_drop": 0.37},
    "sit_napkin": {"thigh.L": D(0.08, -1, 0.02), "thigh.R": D(-0.08, -1, 0.02), "shin.L": D(0, -0.15, -1), "shin.R": D(0, -0.15, -1),
                   "upper_arm.R": D(-0.2, -0.7, -0.6), "forearm.R": D(0.45, -0.5, 0.75), "upper_arm.L": D(0.1, -0.45, -1), "forearm.L": D(-0.15, -1, 0.05),
                   "_hips_drop": 0.37},
    "sit_pocket": {"thigh.L": D(0.08, -1, 0.02), "thigh.R": D(-0.08, -1, 0.02), "shin.L": D(0, -0.15, -1), "shin.R": D(0, -0.15, -1),
                   "upper_arm.R": D(-0.1, -0.35, -1), "forearm.R": D(0.75, -0.6, 0.5), "upper_arm.L": D(0.1, -0.45, -1), "forearm.L": D(-0.15, -1, 0.05),
                   "_hips_drop": 0.37},
    "sit_hands_under": {"thigh.L": D(0.08, -1, 0.02), "thigh.R": D(-0.08, -1, 0.02), "shin.L": D(0, -0.15, -1), "shin.R": D(0, -0.15, -1),
                        "upper_arm.L": D(0.05, 0.0, -1), "upper_arm.R": D(-0.05, 0.0, -1), "forearm.L": D(-0.2, -0.95, -0.2), "forearm.R": D(0.2, -0.95, -0.2),
                        "_hips_drop": 0.37},
    "stand_pocket": {"upper_arm.R": D(-0.1, -0.35, -1), "forearm.R": D(0.75, -0.6, 0.5)},
    "stand_arms_out": {"upper_arm.L": D(0.6, -0.6, -0.5), "upper_arm.R": D(-0.6, -0.6, -0.5), "forearm.L": D(0.3, -1, 0), "forearm.R": D(-0.3, -1, 0)},
    "stand_gun": {"upper_arm.L": D(0.15, -1, 0.0), "upper_arm.R": D(-0.15, -1, 0.0), "forearm.L": D(-0.15, -1, 0.05), "forearm.R": D(0.15, -1, 0.05),
                  "hand.L": D(-0.1, -1, 0), "hand.R": D(0.1, -1, 0)},
    "stand_reach": {"spine": E(30, 0, 0), "upper_arm.R": D(-0.05, -1, -0.3), "forearm.R": D(0, -1, -0.35), "upper_arm.L": D(0.1, -0.3, -1)},
    "lunge": {"spine": E(38, 0, 0), "upper_arm.R": D(-0.1, -1, 0.0), "forearm.R": D(0, -1, 0.1), "upper_arm.L": D(0.2, -0.8, -0.3), "forearm.L": D(0, -1, 0.2),
              "thigh.L": D(0.05, -0.6, -1), "shin.L": D(0, 0.1, -1), "thigh.R": D(-0.05, 0.4, -1), "shin.R": D(0, 0.6, -1)},
    "recoil": {"spine": E(-18, 0, 0), "head": E(-25, 0, 0), "upper_arm.L": D(0.4, 0.1, -1), "upper_arm.R": D(-0.4, 0.1, -1)},
    "kneel": {"thigh.L": D(0.1, -0.9, -0.4), "shin.L": D(0, 0.2, -1), "thigh.R": D(-0.1, 0.0, -1), "shin.R": D(0, 1, -0.05), "_hips_drop": 0.42, "spine": E(15, 0, 0)},
    "crouch": {"thigh.L": D(0.15, -1, -0.15), "thigh.R": D(-0.15, -1, -0.15), "shin.L": D(0, 0.35, -1), "shin.R": D(0, 0.35, -1), "_hips_drop": 0.5, "spine": E(25, 0, 0),
               "upper_arm.L": D(0.2, -0.8, -0.6), "upper_arm.R": D(-0.2, -0.8, -0.6), "forearm.L": D(0, -1, -0.2), "forearm.R": D(0, -1, -0.2)},
    "floor_sit": {"thigh.L": D(0.2, -1, 0.05), "thigh.R": D(-0.2, -1, 0.05), "shin.L": D(0.05, -0.5, -1), "shin.R": D(-0.05, -0.5, -1), "_hips_drop": 0.78,
                  "spine": E(-10, 0, 0), "upper_arm.L": D(0.3, 0.4, -1), "upper_arm.R": D(-0.3, 0.4, -1), "forearm.L": D(0.1, 0.3, -1), "forearm.R": D(-0.1, 0.3, -1)},
    "floor_gun": {"thigh.L": D(0.2, -1, 0.05), "thigh.R": D(-0.2, -1, 0.05), "shin.L": D(0.05, -0.5, -1), "shin.R": D(-0.05, -0.5, -1), "_hips_drop": 0.78,
                  "spine": E(-5, 0, 0), "upper_arm.L": D(0.15, -1, 0.15), "upper_arm.R": D(-0.15, -1, 0.15), "forearm.L": D(-0.15, -1, 0.2), "forearm.R": D(0.15, -1, 0.2)},
    "lying": {"_lying": 1, "upper_arm.L": D(0.3, 0, -1), "upper_arm.R": D(-0.3, 0, -1)},
    "walk_a": {"thigh.L": D(0, -0.45, -1), "shin.L": D(0, -0.1, -1), "thigh.R": D(0, 0.35, -1), "shin.R": D(0, 0.7, -1),
               "upper_arm.L": D(0.1, 0.35, -1), "upper_arm.R": D(-0.1, -0.35, -1), "forearm.R": D(0, -0.6, -1)},
    "walk_b": {"thigh.R": D(0, -0.45, -1), "shin.R": D(0, -0.1, -1), "thigh.L": D(0, 0.35, -1), "shin.L": D(0, 0.7, -1),
               "upper_arm.R": D(-0.1, 0.35, -1), "upper_arm.L": D(0.1, -0.35, -1), "forearm.L": D(0, -0.6, -1)},
    "step_over": {"thigh.L": D(0, -1, -0.3), "shin.L": D(0, -0.3, -1), "thigh.R": D(0, 0.2, -1), "shin.R": D(0, 0.3, -1), "upper_arm.L": D(0.5, 0, -1), "upper_arm.R": D(-0.5, 0, -1)},
    "door": {"upper_arm.R": D(-0.1, -1, -0.2), "forearm.R": D(0, -1, 0.0)},
}

def pose_quats(p, spec):
    """Return local quaternions for every bone from an absolute pose spec (dict)."""
    absq = {}; out = {}
    for bn, h, t, par in BONES:
        if bn == "root": absq[bn] = Quaternion(); out[bn] = Quaternion(); continue
        rest = p.rest_q[bn]
        if bn in spec:
            kind, v = spec[bn]
            if kind == "d":
                rest_dir = (rest @ Vector((0, 1, 0)))
                A = rest_dir.rotation_difference(v)
            else: A = v
        else:
            A = absq.get(par, Quaternion()) if bn in ("hand.L", "hand.R", "foot.L", "foot.R", "neck") else Quaternion()
            if bn in ("head",): A = absq["neck"]
            if bn in ("neck",): A = absq["spine"].slerp(Quaternion(), 0.4)
        absq[bn] = A
        Ap = absq.get(par, Quaternion())
        out[bn] = rest.inverted() @ Ap.inverted() @ A @ rest
    return out

def blend_spec(a, b, t):
    """Blend two absolute specs (t 0..1)."""
    out = {}
    for k in set(a) | set(b):
        if k.startswith("_"):
            out[k] = (a.get(k, 0) or 0) * (1 - t) + (b.get(k, 0) or 0) * t; continue
        qa = to_q(a.get(k)); qb = to_q(b.get(k))
        out[k] = ("e", qa.slerp(qb, t))
    return out

def to_q(v):
    if v is None: return Quaternion()
    if v[0] == "e": return v[1]
    return None  # direction specs are converted per-bone below

def apply_pose(p, spec, frame, extra=None):
    """Key all bones at frame. spec: absolute pose; extra: dict bone->Quaternion added on top (abs) e.g. head look."""
    # convert direction specs to abs quaternions first
    absspec = dir_spec_to_abs(p, spec)
    if extra:
        for k, q in extra.items():
            base = absspec.get(k, ("e", Quaternion()))[1]
            absspec[k] = ("e", q @ base)
    qs = pose_quats(p, absspec)
    for bn, q in qs.items():
        pb = p.arm.pose.bones[bn]; pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=frame)
    drop = absspec.get("_hips_drop", 0) or 0
    hp = p.arm.pose.bones["hips"]
    # hips bone points up: local Y = world Z
    hp.location = (0, -drop, 0); hp.keyframe_insert("location", frame=frame)

def spec_of(name):
    return {k: v for k, v in POSES[name].items()}

def DT(x, y, z, twist): return ("dt", Vector((x, y, z)).normalized(), math.radians(twist))

def dir_spec_to_abs(p, spec):
    out = {}
    for k, v in spec.items():
        if k.startswith("_"): out[k] = v; continue
        if v[0] == "d": out[k] = ("e", (p.rest_q[k] @ Vector((0, 1, 0))).rotation_difference(v[1]))
        elif v[0] == "dt": out[k] = ("e", Quaternion(v[1], v[2]) @ (p.rest_q[k] @ Vector((0, 1, 0))).rotation_difference(v[1]))
        else: out[k] = v
    return out

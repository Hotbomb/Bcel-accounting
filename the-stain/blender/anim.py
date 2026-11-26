# Shot animation engine: evaluates characters on twos (stop-motion style), auto looks, blinks, lip sync, gestures, camera.
import bpy, math, json, os, random
import numpy as np, soundfile as sf
from mathutils import Vector, Quaternion, Euler, Matrix
import stain, characters as C

ROOT = stain.ROOT
FPS = 24
TL = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "timeline.json")))}
CAST = ("martin", "dao", "andy", "do")

def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def facing_angle(f): return math.atan2(f[0], -f[1])

class Track:
    """Piecewise keys (t, value) with smoothstep blending; value can be anything a blend fn handles."""
    def __init__(self): self.k = []
    def add(self, t, v, ease=0.35):
        self.k = [k for k in self.k if abs(k[0] - t) > 1e-6]; self.k.append((t, v, ease)); self.k.sort(key=lambda x: x[0])
    def at(self, t, blend):
        if not self.k: return None
        if t <= self.k[0][0]: return self.k[0][1]
        for (t0, v0, _), (t1, v1, e) in zip(self.k, self.k[1:]):
            if t0 <= t <= t1:
                dur = t1 - t0
                if dur <= 1e-6: return v1
                # 'ease' = fraction of the segment spent moving (the rest holds v0): snappy puppet moves
                u = (t - t0) / dur; mv = max(e, 1e-3)
                u = (u - (1 - mv)) / mv if u > 1 - mv else 0.0
                return blend(v0, v1, smooth(u))
        return self.k[-1][1]

class Shot:
    def __init__(self, sid, cast=CAST, extra_state=None):
        self.id = sid; self.tl = TL[sid]; self.frames = self.tl["frames"]; self.dur = self.tl["dur"]
        stain.reset()
        self.st = stain.continuity(self.tl["scene"], sid)
        if extra_state: self.st.update(extra_state)
        stain.build_set(self.st); self.lights = stain.build_lights(self.st)
        self.sc = bpy.context.scene; self.sc.render.fps = FPS
        self.sc.frame_start = 1; self.sc.frame_end = self.frames
        self.p = {}; self.pose = {}; self.loc = {}; self.face = {}; self.looks = {}; self.expr = {}
        self.gesture = {}; self.walk = {}; self.holds = []; self.mouth_extra = {}; self.closed = {}
        for n in cast:
            pp = C.build(n, self.st); self.p[n] = pp
            for d in (self.pose, self.loc, self.face, self.expr): d[n] = Track()
            self.looks[n] = []; self.gesture[n] = 1.0; self.walk[n] = []
            if n in stain.SEATS: self.seat(n)
        self.rng = random.Random(hash(sid) & 0xffff)
        self.cam = None; self.camtrack = Track(); self.handheld = 0.0; self.dutch = Track(); self.focus = Track()
        self.events = []
        self.lines = self.tl["lines"]
        self.env = {}
        self.exposure = {"act1": -0.7, "candles": -0.4, "act2": -0.45, "act3": -0.1, "act34": -0.1}.get(self.st["light"], -0.7)

    # ---------------- character direction ----------------
    def seat(self, n, t=0.0, pose=None):
        (x, y), f = stain.SEATS[n]
        self.loc[n].add(t, Vector((x, y, 0))); self.face[n].add(t, facing_angle(f))
        self.pose[n].add(t, pose or ("sit_lap" if n == "dao" else "sit"))
    def key(self, n, t, pose=None, loc=None, face=None, ease=0.35):
        """face: angle (radians), a facing vector (x,y), or a character/point to face. No args = hold everything at t."""
        if pose is None and loc is None and face is None:
            for tr in (self.pose[n], self.loc[n], self.face[n]):
                prev = [k for k in tr.k if k[0] <= t]
                if prev: tr.add(t, prev[-1][1], 0.0001)
            return
        if pose is not None: self.pose[n].add(t, pose, ease)
        if loc is not None: self.loc[n].add(t, Vector((loc[0], loc[1], loc[2] if len(loc) > 2 else 0)), ease)
        if face is not None: self.face[n].add(t, self._face(n, face, t), ease)
    def _face(self, n, face, t):
        if isinstance(face, (int, float)): return float(face)
        if isinstance(face, str): face = self.head_pos(face, t)
        if len(face) == 2 and not isinstance(face, Vector): return facing_angle(face)
        here = self.loc[n].at(t, lambda a, b, u: a.lerp(b, u)) or Vector()
        d = Vector(face) - here; return facing_angle((d.x, d.y))
    def look(self, n, target, t0, t1=None):
        """target: character name, 'speaker', 'cam', or a world point."""
        self.looks[n].append((t0, t1 if t1 is not None else 1e9, target))
    def set_expr(self, n, t, brows=0.0, raise_=0.0, ease=0.3):
        """brows: +1 angry (inner down) .. -1 sad/worried (inner up); raise_: 0..1 surprise."""
        self.expr[n].add(t, (brows, raise_), ease)
    def walk_to(self, n, t0, t1, *pts, face_end=None, pose_end="stand"):
        """Walk through points between t0 and t1 with a stepping cycle."""
        here = self.loc[n].at(t0, lambda a, b, u: a.lerp(b, u))
        path = [here] + [Vector((p[0], p[1], 0)) for p in pts]
        L = sum((b - a).length for a, b in zip(path, path[1:])) or 1e-6
        acc = 0.0; self.key(n, t0, "stand", here, ease=0.2)
        for a, b in zip(path, path[1:]):
            acc += (b - a).length; tt = t0 + (t1 - t0) * acc / L
            self.loc[n].add(tt, b, 1.0); self.face[n].add(t0 + (t1 - t0) * (acc - (b - a).length) / L + 0.05, facing_angle(((b - a).x, (b - a).y)), 0.3)
        self.walk[n].append((t0, t1))
        self.pose[n].add(t1 + 0.01, pose_end, 0.3)
        if face_end is not None: self.face[n].add(t1 + 0.25, self._face(n, face_end, t1), 0.6)

    # ---------------- positions ----------------
    def root_at(self, n, t):
        return self.loc[n].at(t, lambda a, b, u: a.lerp(b, u)) or Vector()
    def head_pos(self, n, t):
        if n not in self.p: return Vector(stain.SEATS[n][0] + (1.25,))
        pv = self.pose[n].at(t, lambda a, b, u: b if u > 0.5 else a) or "sit"
        spec = pv if isinstance(pv, dict) else C.POSES.get(pv, {})
        drop = spec.get("_hips_drop", 0); s = C.LOOK[n]["scale"]
        if spec.get("_lying"): return self.root_at(n, t) + Vector((0, 0, 0.25))
        lean = 0.0
        if "spine" in spec and spec["spine"][0] == "e": lean = spec["spine"][1].to_euler().x
        f = self.face[n].at(t, lambda a, b, u: lerp(a, b, u)) or 0.0
        fwd = Vector((math.sin(f), -math.cos(f), 0))
        return self.root_at(n, t) + Vector((0, 0, (1.64 - drop) * s - 0.45 * (1 - math.cos(lean)) * s)) + fwd * 0.45 * math.sin(lean) * s

    # ---------------- speaking ----------------
    def speaker_at(self, t):
        for l in self.lines:
            if l["start"] - 0.15 <= t <= l["end"] + 0.25 and l["char"] != "all" and "os" not in l["flags"]: return l["char"]
        return None
    def envelope(self, l):
        key = l["file"]
        if key not in self.env:
            x, sr = sf.read(os.path.join(ROOT, l["file"]))
            if x.ndim > 1: x = x.mean(1)
            hop = sr // 12; n = len(x) // hop + 1
            e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(x) else 0 for i in range(n)])
            e = e / (np.percentile(e, 95) + 1e-9); self.env[key] = np.clip(e, 0, 1.2)
        return self.env[key]
    def mouth_open(self, n, t):
        v = 0.0
        for l in self.lines:
            if (l["char"] == n or l["char"] == "all") and l["start"] <= t <= l["end"]:
                e = self.envelope(l); i = int((t - l["start"]) * 12)
                if 0 <= i < len(e): v = max(v, float(e[i]))
        for (t0, t1, amt) in self.mouth_extra.get(n, []):
            if t0 <= t <= t1: v = max(v, amt * (0.6 + 0.4 * math.sin(t * 19)))
        return v
    def eyes_closed(self, n, t0, t1): self.closed.setdefault(n, []).append((t0, t1))
    def mouth(self, n, t0, t1, amt=0.6):
        """Extra mouth motion (laughing, gasping)."""
        self.mouth_extra.setdefault(n, []).append((t0, t1, amt))

    # ---------------- camera ----------------
    def camera(self, t, loc, target, lens=35, ease=1.0):
        self.camtrack.add(t, (Vector(loc), target, lens), ease)
    def focus_on(self, t, target): self.focus.add(t, target, 0.0001)
    def _target_pos(self, target, t):
        if isinstance(target, tuple) and target and target[0] == "bone":
            _, n, bone, off = target
            bpy.context.view_layer.update()
            arm = self.p[n].arm; pb = arm.pose.bones[bone]
            return arm.matrix_world @ pb.matrix @ Vector((0, pb.length * 0.6, 0)) + Vector(off)
        if isinstance(target, str):
            if target in self.p: return self.head_pos(target, t)
            return Vector(stain.SEATS.get(target, ((0, 0), 0))[0] + (1.2,))
        return Vector(target)

    # ---------------- events ----------------
    def at(self, t, fn): self.events.append((t, fn))
    def f(self, t): return int(round(t * FPS)) + 1

    # ---------------- bake ----------------
    def bake(self, fstop=4.0, eyelight=True):
        sc = self.sc
        cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); stain.link(cam); sc.camera = cam
        cam_d.clip_start = 0.03; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = fstop; cam_d.sensor_width = 36
        self.cam = cam
        if eyelight:  # faint catch light that follows the camera (glossy only)
            bpy.ops.object.light_add(type="POINT"); el = bpy.context.active_object; el.name = "eyelight"
            el.data.energy = 6.0; el.data.color = (1, 0.95, 0.9); el.data.shadow_soft_size = 0.05
            el.visible_diffuse = False; el.visible_volume_scatter = False
            el.parent = cam; el.location = (0.15, 0.1, 0)
        blinks = {n: self._blink_times(n) for n in self.p}
        for fr in range(1, self.frames + 1, 2):
            t = (fr - 1) / FPS
            for n, pp in self.p.items(): self._bake_char(n, pp, t, fr, blinks[n])
            self._bake_cam(t, fr)
        for t, fn in self.events: fn(self.f(t))
        # held props: second pass after the rigs are keyed
        if self.holds: self._bake_holds()
        for o in bpy.data.objects:
            ad = o.animation_data
            if ad and ad.action: set_constant(ad.action)
            if o.type == "MESH" and o.data.shape_keys and o.data.shape_keys.animation_data and o.data.shape_keys.animation_data.action:
                pass
        return cam

    def _blink_times(self, n):
        r = random.Random(hash((self.id, n)) & 0xffff); out = []; t = r.uniform(0.3, 2.5)
        while t < self.dur: out.append(t); t += r.uniform(2.0, 5.5)
        return out

    def _bake_char(self, n, pp, t, fr, blinks):
        # pose (absolute spec), blended
        def bl(a, b, u):
            if a == b or u <= 0: return a
            if u >= 1: return b
            return ("__blend", a, b, u)
        pv = self.pose[n].at(t, bl) or "sit"
        if isinstance(pv, tuple) and pv[0] == "__blend":
            spec = C.blend_spec(C.dir_spec_to_abs(pp, resolve(pv[1])), C.dir_spec_to_abs(pp, resolve(pv[2])), pv[3])
        else:
            spec = C.dir_spec_to_abs(pp, resolve(pv))
        # walking cycle overlay
        for (t0, t1) in self.walk[n]:
            if t0 <= t <= t1:
                ph = math.sin((t - t0) * math.pi * 2 / 0.9)
                w = C.blend_spec(C.dir_spec_to_abs(pp, resolve("walk_a")), C.dir_spec_to_abs(pp, resolve("walk_b")), (ph + 1) / 2)
                spec = {**spec, **{k: v for k, v in w.items() if not k.startswith("_")}}; spec["_hips_drop"] = 0.02 * abs(ph)
        loc = self.root_at(n, t); ang = self.face[n].at(t, lambda a, b, u: lerp(a, b, u)) or 0.0
        lying = spec.get("_lying", 0)
        arm = pp.arm
        arm.location = loc; arm.rotation_euler = (lying * -math.pi / 2 * 0.98, 0, ang)
        if lying: arm.location = loc + Vector((0, 0, 0.16))
        arm.keyframe_insert("location", frame=fr); arm.keyframe_insert("rotation_euler", frame=fr)
        # look
        extra = {}
        target = None
        for (t0, t1, tg) in self.looks[n]:
            if t0 <= t <= t1: target = tg
        if target is None or target == "speaker":
            sp = self.speaker_at(t)
            if sp and sp != n: target = sp
            elif sp == n:  # speaker looks at the last person they addressed / previous speaker
                target = self._addressee(n, t)
        if target is not None and not lying:
            tp = self.cam.matrix_world.translation if target == "cam" else self._target_pos(target, t)
            hp = self.head_pos(n, t)
            d = tp - hp
            yaw = math.atan2(d.x, -d.y) - ang; yaw = (yaw + math.pi) % (2 * math.pi) - math.pi
            pitch = -math.atan2(d.z, math.hypot(d.x, d.y))
            hy = max(-1.2, min(1.2, yaw)); hpch = max(-0.6, min(0.6, pitch))
            extra["head"] = Euler((hpch * 0.8, 0, hy * 0.75), "XYZ").to_quaternion()
            extra["spine"] = Euler((0, 0, hy * 0.2), "XYZ").to_quaternion()
            ey, ep = (yaw - hy * 0.95) + hy * 0.25, (pitch - hpch * 0.8)
        else:
            ey = ep = 0.0
        # talking: nods + gestures
        mo = self.mouth_open(n, t)
        speaking = any(l["char"] in (n, "all") and l["start"] <= t <= l["end"] for l in self.lines)
        if speaking and self.gesture[n] > 0:
            g = self.gesture[n]; r = self.rng
            nod = Euler((0.12 * mo * g, 0, 0.05 * math.sin(t * 3.1) * g), "XYZ").to_quaternion()
            extra["head"] = nod @ extra.get("head", Quaternion())
            if int(t * 1.5) % 3 == 0:
                extra["forearm.R"] = Euler((0.0, 0.25 * g * math.sin(t * 2.3), 0.3 * g * math.sin(t * 1.7)), "XYZ").to_quaternion()
            if int(t * 1.5) % 3 == 1:
                extra["forearm.L"] = Euler((0.0, -0.2 * g * math.sin(t * 2.1), -0.3 * g * math.sin(t * 1.3)), "XYZ").to_quaternion()
        # breathing
        extra["spine"] = Euler((0.012 * math.sin(t * 2 * math.pi / 4.2 + hash(n) % 7), 0, 0), "XYZ").to_quaternion() @ extra.get("spine", Quaternion())
        C.apply_pose(pp, spec, fr, extra)
        # face
        f = pp.face
        for s in ("L", "R"):
            e = f[f"eye{s}"]; e.rotation_euler = (max(-0.5, min(0.5, ep)), 0, max(-0.7, min(0.7, ey))); e.keyframe_insert("rotation_euler", frame=fr)
            closed = any(0 <= t - b < 0.13 for b in blinks) or any(a <= t <= b for a, b in self.closed.get(n, []))
            lid = f[f"lid{s}"]; lid.rotation_euler = (math.radians(75 if closed else -38) + max(0, ep) * 0.6, 0, max(-0.7, min(0.7, ey)) * 0.5)
            lid.keyframe_insert("rotation_euler", frame=fr)
        br, rs = self.expr[n].at(t, lambda a, b, u: (lerp(a[0], b[0], u), lerp(a[1], b[1], u))) or (0.0, 0.0)
        for s, sgn in (("L", -1), ("R", 1)):
            b = f[f"brow{s}"]; b.rotation_euler = (0, math.pi / 2 + sgn * 0.35 * br, 0)
            if not hasattr(b, "_base"): pass
            b.location.z = b.get("z0", None) or b.location.z
            if "z0" not in b: b["z0"] = b.location.z
            b.location.z = b["z0"] + 0.018 * rs - 0.006 * max(0, br)
            b.keyframe_insert("rotation_euler", frame=fr); b.keyframe_insert("location", frame=fr)
        m = f["mouth"]; m.scale = (1.0 - 0.15 * mo, 0.22, 0.18 + 0.55 * min(mo, 1.0)); m.keyframe_insert("scale", frame=fr)

    def _addressee(self, n, t):
        idx = [i for i, l in enumerate(self.lines) if l["char"] == n and l["start"] - 0.15 <= t <= l["end"] + 0.25]
        if idx:
            i = idx[0]
            for j in list(range(i - 1, -1, -1)) + list(range(i + 1, len(self.lines))):
                c = self.lines[j]["char"]
                if c not in (n, "all") and c in self.p: return c
        others = [c for c in self.p if c != n]
        return others[0] if others else None

    def _bake_cam(self, t, fr):
        k = self.camtrack.at(t, lambda a, b, u: (a[0].lerp(b[0], u), ("__tb", a[1], b[1], u), lerp(a[2], b[2], u)))
        if k is None: return
        loc, tg, lens = k
        if isinstance(tg, tuple) and tg and tg[0] == "__tb":
            tp = self._target_pos(tg[1], t).lerp(self._target_pos(tg[2], t), tg[3])
        else: tp = self._target_pos(tg, t)
        cam = self.cam; cam.location = loc
        q = (tp - loc).to_track_quat("-Z", "Y")
        hh = self.handheld
        if hh:
            nx = hh * (math.sin(t * 1.3 + 1) * 0.6 + math.sin(t * 3.7) * 0.25 + math.sin(t * 7.9 + 2) * 0.1)
            ny = hh * (math.sin(t * 1.1 + 4) * 0.6 + math.sin(t * 4.3 + 1) * 0.25)
            q = q @ Euler((ny * 0.02, nx * 0.02, 0), "XYZ").to_quaternion()
        dt = self.dutch.at(t, lambda a, b, u: lerp(a, b, u)) or 0.0
        if dt: q = q @ Euler((0, 0, math.radians(dt)), "XYZ").to_quaternion()
        cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = q
        cam.data.lens = lens
        cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_quaternion", frame=fr)
        cam.data.keyframe_insert("lens", frame=fr)
        fo = self.focus.at(t, lambda a, b, u: b if u > 0.5 else a)
        fp = self._target_pos(fo, t) if fo is not None else tp
        cam.data.dof.focus_distance = max(0.1, (fp - loc).length); cam.data.dof.keyframe_insert("focus_distance", frame=fr)

    # ---------------- props in hands ----------------
    def hold(self, obj, n, hand, t0, t1, offset=(0, 0, 0), rot=(0, 0, 0)):
        """Keep obj in a character's hand from t0 to t1 (outside that range the object's own keys apply)."""
        self.holds.append((obj, n, hand, t0, t1, Matrix.Translation(offset) @ Euler(rot).to_matrix().to_4x4()))
    def _bake_holds(self):
        sc = self.sc
        for fr in range(1, self.frames + 1, 2):
            t = (fr - 1) / FPS; sc.frame_set(fr)
            for obj, n, hand, t0, t1, off in self.holds:
                if t0 <= t <= t1:
                    pp = self.p[n]; pb = pp.arm.pose.bones[f"hand.{hand}"]
                    M = pp.arm.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length * 0.6, 0)) @ off
                    obj.matrix_world = M
                    obj.keyframe_insert("location", frame=fr); obj.keyframe_insert("rotation_euler", frame=fr); obj.keyframe_insert("scale", frame=fr)

def resolve(p):
    if isinstance(p, dict): return p
    return C.POSES[p]

def set_constant(action):
    try:
        curves = action.fcurves
    except AttributeError:  # Blender 5 layered actions
        curves = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in curves:
        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

def key_obj(o, fr, **props):
    for k, v in props.items():
        setattr(o, k, v); o.keyframe_insert(k, frame=fr)

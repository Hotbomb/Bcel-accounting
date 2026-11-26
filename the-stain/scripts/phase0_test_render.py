# Phase 0 timing test: simple room + one stylized clay figure.
# Usage: python scripts/phase0_test_render.py <engine> <samples> <out.png>
import bpy, sys, time, math
engine, samples, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def mat(name, rgb, rough=0.6, emit=0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    return m
def add(op, mt, **kw):
    op(**kw); o = bpy.context.active_object; o.data.materials.append(mt); return o
wood, wall, cloth, navy, skin = (mat("wood",(0.35,0.18,0.08)), mat("wall",(0.8,0.77,0.7)),
    mat("cloth",(0.92,0.92,0.9)), mat("navy",(0.05,0.08,0.25)), mat("skin",(0.75,0.52,0.4),0.5))
add(bpy.ops.mesh.primitive_plane_add, wood, size=12)
for loc, rot in [((0,4,1.5),(math.pi/2,0,0)), ((-4,0,1.5),(math.pi/2,0,math.pi/2))]:
    add(bpy.ops.mesh.primitive_plane_add, wall, size=8, location=loc, rotation=rot)
t = add(bpy.ops.mesh.primitive_cube_add, cloth, location=(0.8,0.5,0.75)); t.scale=(1.1,0.5,0.02)
# clay figure: capsule body, round head, big eyes
body = add(bpy.ops.mesh.primitive_cylinder_add, navy, radius=0.22, depth=0.7, location=(-0.6,0.5,0.95))
bpy.ops.object.modifier_add(type='BEVEL'); body.modifiers[-1].width=0.15; body.modifiers[-1].segments=6
head = add(bpy.ops.mesh.primitive_uv_sphere_add, skin, radius=0.2, location=(-0.6,0.5,1.5)); bpy.ops.object.shade_smooth()
for dx in (-0.07, 0.07):
    e = add(bpy.ops.mesh.primitive_uv_sphere_add, mat("eye",(0.95,0.95,0.95),0.2), radius=0.045, location=(-0.6+dx,0.33,1.54))
    add(bpy.ops.mesh.primitive_uv_sphere_add, mat("pupil",(0.02,0.02,0.02),0.1), radius=0.022, location=(-0.6+dx,0.29,1.54))
for x in (0.4, 1.2):
    add(bpy.ops.mesh.primitive_cylinder_add, mat("flame",(1,0.55,0.15),0,8), radius=0.012, depth=0.04, location=(x,0.5,0.95))
# warm pendant key
bpy.ops.object.light_add(type='AREA', location=(0.3,0.5,2.4)); k = bpy.context.active_object
k.data.energy=250; k.data.size=0.8; k.data.color=(1,0.78,0.55)
bpy.ops.object.light_add(type='AREA', location=(3,-2,2), rotation=(1.1,0,0.9)); r = bpy.context.active_object
r.data.energy=80; r.data.size=2; r.data.color=(0.6,0.75,1)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.01,0.012,0.02,1)
bpy.ops.object.camera_add(location=(1.2,-3.2,1.6)); cam = bpy.context.active_object; sc.camera = cam
cam.data.lens = 35
c = cam.constraints.new('TRACK_TO'); c.target = head
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = 'AgX'
if engine == 'CYCLES':
    sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=samples
    sc.cycles.use_denoising=True; sc.cycles.max_bounces=4; sc.cycles.sample_clamp_indirect=5
elif engine == 'EEVEE':
    sc.render.engine='BLENDER_EEVEE'; sc.eevee.taa_render_samples=samples
else:
    sc.render.engine='BLENDER_WORKBENCH'
sc.render.filepath = out
t0=time.time(); bpy.ops.render.render(write_still=True)
print(f"RESULT {engine} {samples} {time.time()-t0:.1f}s")

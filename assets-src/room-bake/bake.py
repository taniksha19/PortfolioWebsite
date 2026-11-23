# Blender lightmap bake for the 3D room.
# usage: blender -b --factory-startup -P bake.py -- room.glb lights.json outdir RES SAMPLES [day|night|both]
import bpy, json, sys, math, os, time
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, LJ, OUT, RES, SAMPLES = argv[0], argv[1], argv[2], int(argv[3]), int(argv[4])
MODES = ["day", "night"] if len(argv) < 6 or argv[5] == "both" else [argv[5]]
L = json.load(open(LJ))
os.makedirs(OUT, exist_ok=True)
def B(p): return Vector((p[0], -p[2], p[1]))          # three.js (y-up) -> blender (z-up)
def hexcol(h): h = h.lstrip("#"); return tuple(((int(h[i:i+2], 16) / 255) ** 2.2) for i in (0, 2, 4))

t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
for o in list(bpy.data.objects):
    if o.type in ("LIGHT", "CAMERA") or o.name.startswith("nb_"):
        bpy.data.objects.remove(o, do_unlink=True)
vl = bpy.context.view_layer
for o in bpy.data.objects: o.select_set(o.type == "MESH")
vl.objects.active = next(o for o in bpy.data.objects if o.type == "MESH")
bpy.ops.object.make_single_user(object=True, obdata=True, material=False)
bake = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("bk_")]
print("bake targets:", len(bake), "occluders:", sum(1 for o in bpy.data.objects if o.type == "MESH") - len(bake))

# close the room (ceiling, right and front walls) so light bounces like a real room; never visible in the page
def closer(col):
    m = bpy.data.materials.new("closer"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*hexcol(col), 1); return m
CEIL, WALLS = closer("#f6f1ea"), closer("#d4e6c8")   # warm white ceiling, walls match the room's sage
def plane(name, loc, rot, sx, sy, m):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); p = bpy.context.active_object
    p.name = name; p.scale = (sx, sy, 1); p.data.materials.append(m); return p
plane("ceiling", (0.2, 0.0, 3.4), (0, 0, 0), 7.0, 5.4, CEIL)
plane("rightwall", (3.5, 0.0, 1.7), (0, math.pi / 2, 0), 3.4, 5.4, WALLS)
plane("frontwall", (0.2, -2.6, 1.7), (math.pi / 2, 0, 0), 7.0, 3.4, WALLS)

import bmesh
center = Vector((0.2, 0.0, 1.5)); removed = 0
for o in bake:
    d = o.dimensions
    if min(d) > 0.13 or sorted(d)[1] < 0.9: continue          # only thin, large slabs (walls, skirting)
    bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world; nm = mw.to_3x3().inverted().transposed()
    kill = [f for f in bm.faces if (nm @ f.normal).normalized().dot((center - mw @ f.calc_center_median()).normalized()) < -0.2]
    removed += len(kill); bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(o.data); bm.free()
print("outer faces removed:", removed)

# lightmap UVs, packed for all bake targets into one atlas
for o in bpy.data.objects: o.select_set(False)
for o in bake:
    me = o.data
    if "lm" not in me.uv_layers: me.uv_layers.new(name="lm")
    me.uv_layers.active = me.uv_layers["lm"]
    o.select_set(True)
vl.objects.active = bake[0]
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.003)
bpy.ops.object.mode_set(mode="OBJECT")
print("uv done", round(time.time() - t0, 1), "s")

# bake image hooked into every material used by the targets
img = bpy.data.images.new("lm", RES, RES, float_buffer=True)
for o in bake:
    for slot in o.material_slots:
        m = slot.material
        if not m: continue
        m.use_nodes = True
        nt = m.node_tree
        n = nt.nodes.get("LM_BAKE") or nt.nodes.new("ShaderNodeTexImage"); n.name = "LM_BAKE"; n.image = img
        nt.nodes.active = n

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 1
sc.render.bake.margin = 6; sc.render.bake.use_clear = True
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]

def light(name, kind, loc, power, color, **kw):
    d = bpy.data.lights.new(name, kind); d.energy = power; d.color = hexcol(color)
    for k, v in kw.items(): setattr(d, k, v)
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc; return o
def aim(o, target): o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()

lamp0 = B(L["lamp"]); lampT = B(L["lampTarget"]); lamp = lamp0 + (lampT - lamp0).normalized() * 0.06;   # step out of the bulb mesh, below the shade rim
scr = B(L["screen"]); scrN = B(L["screenNormal"]).normalized()
sunP, sunT = B(L["sun"]), B(L["sunTarget"])
# window opening: three x[-2,-0.85] y[1.05,2.35] at z -2.55  ->  blender
win_c = Vector((-1.425, 2.55 - 0.02, 1.7))

FILL = {"ceil": {"day": 45, "night": 3}, "front": {"day": 40, "night": 2.5}}
def setup(mode):
    for o in list(bpy.data.objects):
        if o.type == "LIGHT": bpy.data.objects.remove(o, do_unlink=True)
    portal = light("portal", "AREA", win_c, 0, "#ffffff", shape="RECTANGLE", size=1.15, size_y=1.3)
    portal.data.cycles.is_portal = True; portal.rotation_euler = (math.radians(-90), 0, 0)   # emits along -y, into the room
    ceil = light("ceilfill", "AREA", Vector((0.2, 0.3, 3.3)), FILL["ceil"][mode], "#fff4ea", shape="RECTANGLE", size=4.0, size_y=3.0)
    front = light("frontfill", "AREA", Vector((0.0, -2.3, 1.8)), FILL["front"][mode], "#fff2e8" if mode == "day" else "#ffd9b0", shape="RECTANGLE", size=3.5, size_y=1.6)
    aim(front, Vector((0.0, 2.4, 1.2)))
    if mode == "day":
        bg.inputs[0].default_value = (*hexcol("#f4dccd"), 1); bg.inputs[1].default_value = 2.2
        s = light("sun", "SUN", sunP, 7.0, "#ffd2c2", angle=math.radians(3)); aim(s, sunT)
        sp = light("lamp", "SPOT", lamp, 35, "#ffd79a", spot_size=math.radians(110), spot_blend=0.6, shadow_soft_size=0.03); aim(sp, lampT)
    else:
        bg.inputs[0].default_value = (*hexcol("#2a2060"), 1); bg.inputs[1].default_value = 0.35
        sp = light("lamp", "SPOT", lamp, 45, "#ffcf8a", spot_size=math.radians(115), spot_blend=0.7, shadow_soft_size=0.03); aim(sp, lampT)
        light("lampglow", "POINT", lamp, 2.5, "#ffcf8a", shadow_soft_size=0.04)
        for i, b in enumerate(L["bulbs"]):
            light("fairy%d" % i, "POINT", B(b) + Vector((0, -0.07, 0)), 0.09, "#ffe3a0", shadow_soft_size=0.03)
        sc_l = light("screen", "AREA", scr + scrN * 0.01, 2.5, "#d9c8ff", shape="RECTANGLE", size=0.56, size_y=0.35)
        sc_l.rotation_euler = scrN.to_track_quat("-Z", "Y").to_euler()   # emit out of the screen

def save(mode):
    a = np.array(img.pixels[:], dtype=np.float32).reshape(RES, RES, 4)[:, :, :3]
    lit = a[a.sum(axis=2) > 0]
    print(mode, "lightmap mean", lit.mean(axis=0).round(3), "p50", np.percentile(lit, 50).round(3), "p95", np.percentile(lit, 95).round(3))
    np.save(os.path.join(OUT, "lm-%s.npy" % mode), a[::-1].astype(np.float16))   # flip to top-down image rows

for o in bpy.data.objects: o.select_set(o in bake)
vl.objects.active = bake[0]
try:
    sc.cycles.samples = 1; t1 = time.time()
    bpy.ops.object.bake(type="POSITION", margin=6, use_clear=True)
    np.save(os.path.join(OUT, "pos.npy"), np.array(img.pixels[:], dtype=np.float32).reshape(RES, RES, 4)[::-1, :, :3].astype(np.float16))
    print("position bake", round(time.time() - t1, 1), "s")
except Exception as e:
    print("position bake failed:", e)
sc.cycles.samples = SAMPLES

for mode in MODES:
    sc.cycles.samples = SAMPLES * (2 if mode == "night" else 1)
    setup(mode)
    for o in bpy.data.objects: o.select_set(o in bake)
    vl.objects.active = bake[0]
    t1 = time.time()
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=6, use_clear=True)
    print(mode, "bake", round(time.time() - t1, 1), "s")
    save(mode)

# export just the bake targets: same local geometry, plus the lightmap UVs as TEXCOORD_1
for o in bpy.data.objects: o.select_set(o in bake)
for o in bake: o.data.uv_layers.active = o.data.uv_layers[0]
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "baked.glb"), export_format="GLB", use_selection=True, export_materials="NONE",
                          export_texcoords=True, export_normals=True, export_yup=True, export_apply=False)
print("total", round(time.time() - t0, 1), "s")

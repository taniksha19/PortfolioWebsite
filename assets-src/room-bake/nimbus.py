# Sculpts Nimbus's cloud body from metaballs, fits it to the face the room draws on top, exports GLB.
# Coordinates: three (x, y-up, z-front) == blender (x, -y, z).  Face sits at three z ~ .06 around y .07-.09.
# usage: blender -b --factory-startup -P nimbus.py -- out.glb [preview.png]
import bpy, bmesh, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; PREVIEW = argv[1] if len(argv) > 1 else None
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

mb = bpy.data.metaballs.new("cloud"); mb.resolution = 0.006; mb.render_resolution = 0.006; mb.threshold = 0.6
def ball(x, y, z, r, sz=1.0):
    e = mb.elements.new(); e.co = (x, -z, y); e.radius = r
    if sz != 1.0: e.type = "ELLIPSOID"; e.size_x = 1; e.size_y = sz; e.size_z = 1
# (three coords) a big belly, side puffs, a crown of lobes, and a little back to give it depth
for args in [(-.1, .05, 0, .052), (-.042, .046, .01, .064), (.025, .048, .01, .066), (.095, .052, 0, .056),
             (-.05, .105, 0, .06), (.035, .11, 0, .07), (-.005, .155, -.008, .046), (0, .08, -.03, .07)]:
    ball(*args)
obj = bpy.data.objects.new("cloud", mb); bpy.context.scene.collection.objects.link(obj)
dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
bpy.data.objects.remove(obj, do_unlink=True)

bm = bmesh.new(); bm.from_mesh(me)
xs = [v.co.x for v in bm.verts]; width = max(xs) - min(xs); s = 0.27 / width
for v in bm.verts: v.co *= s
zmin = min(v.co.z for v in bm.verts)
for v in bm.verts: v.co.z -= zmin
for v in bm.verts:   # flat little base so it sits on the sill
    if v.co.z < 0.012: v.co.z = 0.012 - (0.012 - v.co.z) * 0.15
for v in bm.verts: v.co.z -= 0.004
# fit depth: the front of the face area must sit just under the face (three z ~ .058)
front = max(-v.co.y for v in bm.verts if abs(v.co.x) < 0.015 and 0.065 < v.co.z < 0.095)
k = 0.058 / front
for v in bm.verts: v.co.y *= k
print("scale", round(s, 4), "front", round(front, 4), "depth k", round(k, 3), "height", round(max(v.co.z for v in bm.verts), 4))
bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.2, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
m = bpy.data.materials.new("cloud"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9; me.materials.append(m)
ob = bpy.data.objects.new("nimbus_body", me); bpy.context.scene.collection.objects.link(ob)
print("tris", sum(len(p.vertices) - 2 for p in me.polygons))

if PREVIEW:
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.render.resolution_x = sc.render.resolution_y = 500
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.55, 0.62, 0.5, 1)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0.15, -0.5, 0.18); cam.rotation_euler = (Vector((0, 0, 0.08)) - cam.location).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = 60
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.energy = 3; sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    sc.render.filepath = PREVIEW; bpy.ops.render.render(write_still=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_apply=True)
print("exported", OUT)

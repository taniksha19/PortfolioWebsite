# Models over-ear headphones in Blender and exports GLB (+ optional preview).
# Same local frame as the three.js placeholder: band arcs over +Z (three +Y), cups sit on the X axis.
# usage: blender -b --factory-startup -P headphones.py -- out.glb [preview.png]
import bpy, math, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; PREVIEW = argv[1] if len(argv) > 1 else None
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

def hexcol(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c] + [1]
def material(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = hexcol(color)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal; return m
M = {"shell": material("shell", "#f0a9c3", 0.38), "band": material("band", "#f7eff2", 0.45), "pad": material("pad", "#3b3046", 0.85),
     "metal": material("metal", "#dcd6e0", 0.25, 0.8), "accent": material("accent", "#b04d77", 0.3)}
parts = {}
def add(mat, verts, faces):
    p = parts.setdefault(mat, ([], [])); o = len(p[0]); p[0].extend(verts); p[1].extend(tuple(i + o for i in f) for f in faces)

def ring_faces(rows, seg, closed=True):
    f = []
    for k in range(rows - 1):
        for s in range(seg if closed else seg - 1): f.append((k * seg + s, k * seg + (s + 1) % seg, (k + 1) * seg + (s + 1) % seg, (k + 1) * seg + s))
    return f

def sweep(points, rx_fn, ry_fn, mat, seg=16, up=Vector((0, 1, 0))):
    """Elliptical cross-section swept along points; rx is across `up`, ry along the curve normal."""
    v = []
    for k, p in enumerate(points):
        d = (points[min(k + 1, len(points) - 1)] - points[max(k - 1, 0)]).normalized(); n = d.cross(up).normalized(); t = k / (len(points) - 1)
        for s in range(seg):
            a = s / seg * math.tau; v.append(p + up * math.cos(a) * rx_fn(t) + n * math.sin(a) * ry_fn(t))
    f = ring_faces(len(points), seg)
    c0, c1 = len(v), len(v) + 1; v += [points[0], points[-1]]
    f += [(c0, (s + 1) % seg, s) for s in range(seg)] + [(c1, (len(points) - 1) * seg + s, (len(points) - 1) * seg + (s + 1) % seg) for s in range(seg)]
    add(mat, v, f)

def lathe_x(profile, center, mat, seg=48, sign=1):
    """Revolve (r, x) profile around the X axis at `center`."""
    v = []
    for (r, x) in profile:
        for s in range(seg): a = s / seg * math.tau; v.append(center + Vector((x * sign, r * math.cos(a), r * math.sin(a))))
    add(mat, v, ring_faces(len(profile), seg))

R = 0.068
arc = [Vector((R * math.cos(a), 0, R * math.sin(a))) for a in (math.pi * k / 40 for k in range(41))]
# headband: a flat, slightly wider strip; a padded cushion under the crown
sweep(arc, lambda t: 0.0085, lambda t: 0.0032, "band")
crown = [Vector(((R - 0.006) * math.cos(a), 0, (R - 0.006) * math.sin(a))) for a in (math.pi * (0.22 + 0.56 * k / 24) for k in range(25))]
sweep(crown, lambda t: 0.0075, lambda t: 0.0035 * math.sin(math.pi * t) ** 0.5 + 0.0008, "pad")
for side in (-1, 1):
    x = side * R
    # sliders: metal bars running down into the yokes
    sweep([Vector((x, 0, 0.004)), Vector((x * 1.02, 0, -0.012))], lambda t: 0.0035, lambda t: 0.0016, "metal", seg=10)
    # yoke: a fork that wraps the cup
    yoke = [Vector((x * 1.02 + side * 0.006 * math.sin(a), 0.0, -0.012 - 0.033 * (1 - math.cos(a)) / 2)) for a in (math.pi * k / 16 for k in range(17))]
    cc = Vector((x * 1.06, 0, -0.045))
    for sgn in (-1, 1):   # yoke arms arc around the cup instead of through it
        sweep([cc + Vector((0, sgn * 0.037 * math.sin(a), 0.037 * math.cos(a))) for a in (math.pi / 2 * k / 12 for k in range(13))], lambda t: 0.0022, lambda t: 0.0022, "accent", seg=10, up=Vector((1, 0, 0)))
    c = Vector((x * 1.06, 0, -0.045))
    # ear cup shell: rounded puck, outer face slightly domed
    lathe_x([(0.0, 0.016), (0.012, 0.0158), (0.022, 0.0148), (0.029, 0.012), (0.0315, 0.006), (0.032, 0.0), (0.0305, -0.006), (0.028, -0.009), (0.0, -0.009)], c, "shell", sign=side)
    lathe_x([(0.0105, 0.0163), (0.0125, 0.0166), (0.0125, 0.0162), (0.0105, 0.016)], c, "accent", sign=side)   # little logo ring
    # cushion: a plush torus on the inner face
    prof = [(0.021 + 0.0075 * math.cos(a), -0.012 - 0.0065 * math.sin(a)) for a in (math.tau * k / 20 for k in range(21))]
    lathe_x(prof, c, "pad", sign=side)
    lathe_x([(0.0, -0.0095), (0.0215, -0.0095)], c, "pad", sign=side)   # speaker cloth

for mat, (v, f) in parts.items():
    me = bpy.data.meshes.new(mat); me.from_pydata([tuple(x) for x in v], [], f); me.update()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(M[mat]); ob = bpy.data.objects.new(mat, me); bpy.context.scene.collection.objects.link(ob)

if PREVIEW:
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.render.resolution_x = sc.render.resolution_y = 600
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = hexcol("#d4e6c8")
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0.12, -0.3, 0.08); cam.rotation_euler = (Vector((0, 0, 0.0)) - cam.location).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = 50
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.energy = 3.5; sun.rotation_euler = (math.radians(45), 0, math.radians(30))
    sc.render.filepath = PREVIEW; bpy.ops.render.render(write_still=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_apply=True)
print("exported", OUT)

# Procedurally models a pot of lilies in Blender and exports it as GLB (+ an optional preview render).
# usage: blender -b --factory-startup -P lilies.py -- out.glb [preview.png]
import bpy, bmesh, math, sys, random
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; PREVIEW = argv[1] if len(argv) > 1 else None
random.seed(7)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

def hexcol(h, a=1.0):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c] + [a]

def material(name, color, rough=0.5, use_vc=False, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.use_backface_culling = False
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hexcol(color); bsdf.inputs["Roughness"].default_value = rough
    if use_vc:
        a = m.node_tree.nodes.new("ShaderNodeVertexColor"); a.layer_name = "Col"
        m.node_tree.links.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    return m

M = {
    "petal": material("petal", "#ffffff", 0.45, use_vc=True),
    "bud": material("bud", "#ffffff", 0.5, use_vc=True),
    "stem": material("stem", "#5f9e86", 0.6),
    "leaf": material("leaf", "#6fae8f", 0.55),
    "anther": material("anther", "#b8652e", 0.7),
    "filament": material("filament", "#eaf2d8", 0.6),
    "pot": material("pot", "#f4ece6", 0.3),
    "rim": material("rim", "#b04d77", 0.25),
    "soil": material("soil", "#5a4038", 0.95),
}

class Builder:
    """Collects geometry per material, then emits one object per material."""
    def __init__(self): self.parts = {}
    def add(self, mat, verts, faces, cols=None):
        p = self.parts.setdefault(mat, {"v": [], "f": [], "c": []}); o = len(p["v"])
        p["v"] += verts; p["f"] += [tuple(i + o for i in f) for f in faces]
        p["c"] += cols if cols else [(1, 1, 1, 1)] * len(verts)
    def emit(self):
        for mat, p in self.parts.items():
            me = bpy.data.meshes.new(mat); me.from_pydata([tuple(v) for v in p["v"]], [], p["f"]); me.update()
            ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
            for i, c in enumerate(p["c"]): ca.data[i].color = c
            for poly in me.polygons: poly.use_smooth = True
            me.materials.append(M[mat])
            ob = bpy.data.objects.new(mat, me); bpy.context.scene.collection.objects.link(ob)
B = Builder()

def grid_faces(nu, nv):
    return [(j * (nu + 1) + i, j * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i) for j in range(nv) for i in range(nu)]

def mix(a, b, t): return [a[i] + (b[i] - a[i]) * t for i in range(4)]
def smooth(e0, e1, x): t = max(0, min(1, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

def blade(xf, length, width, th0, th1, cup, mat, col_fn=None, nu=10, nv=22, tipcurl=0.0, wavy=0.0):
    """A petal or leaf: a strip whose centreline bends from angle th0 to th1 (radians from the local +Z axis),
    cupped across its width. Built along local +X (radial) / +Z (up), then placed by matrix xf."""
    verts, cols = [], []
    r = z = 0.0; ds = length / nv; pts = []
    for j in range(nv + 1):
        t = j / nv; th = th0 + (th1 - th0) * t ** 1.6 + tipcurl * t ** 4
        pts.append((r, z, th)); r += math.sin(th) * ds; z += math.cos(th) * ds
    for j, (r, z, th) in enumerate(pts):
        t = j / nv
        w = width * (0.16 + 0.84 * math.sin(math.pi * min(1.0, t ** 0.8))) * (1 - t) ** 0.35 if t < 1 else 0.0
        n = Vector((-math.cos(th), 0, math.sin(th)))   # inward/up normal of the centreline in the (x, z) plane
        for i in range(nu + 1):
            u = i / nu * 2 - 1
            p = Vector((r, u * w / 2, z)) + n * (cup * w * u * u) + n * (wavy * w * math.sin(u * 3 + t * 9) * t)
            verts.append(xf @ p); cols.append(col_fn(t, u) if col_fn else (1, 1, 1, 1))
    B.add(mat, verts, grid_faces(nu, nv), cols)

def tube(points, radius, mat, seg=8, r_end=None):
    verts, faces = [], []
    for k, p in enumerate(points):
        d = (points[min(k + 1, len(points) - 1)] - points[max(k - 1, 0)]).normalized()
        a = d.orthogonal().normalized(); b = d.cross(a)
        rr = radius if r_end is None else radius + (r_end - radius) * k / (len(points) - 1)
        for s in range(seg):
            ang = s / seg * math.tau; verts.append(p + (a * math.cos(ang) + b * math.sin(ang)) * rr)
    for k in range(len(points) - 1):
        for s in range(seg): faces.append((k * seg + s, k * seg + (s + 1) % seg, (k + 1) * seg + (s + 1) % seg, (k + 1) * seg + s))
    B.add(mat, verts, faces)

def ellipsoid(c, rx, ry, rz, mat, xf=Matrix.Identity(4), col_fn=None, nu=14, nv=10):
    verts, cols = [], []
    for j in range(nv + 1):
        v = j / nv; phi = math.pi * v
        for i in range(nu + 1):
            th = i / nu * math.tau
            p = Vector((rx * math.sin(phi) * math.cos(th), ry * math.sin(phi) * math.sin(th), rz * math.cos(phi)))
            verts.append(xf @ p + c); cols.append(col_fn(1 - v) if col_fn else (1, 1, 1, 1))
    B.add(mat, verts, grid_faces(nu, nv), cols)

def bezier(p0, p1, p2, n=14): return [p0 * (1 - t) ** 2 + p1 * 2 * (1 - t) * t + p2 * t * t for t in (k / n for k in range(n + 1))]

def lathe(profile, mat, seg=56, col=None):
    verts, faces = [], []
    for (r, z) in profile:
        for s in range(seg): a = s / seg * math.tau; verts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    for k in range(len(profile) - 1):
        for s in range(seg): faces.append((k * seg + s, k * seg + (s + 1) % seg, (k + 1) * seg + (s + 1) % seg, (k + 1) * seg + s))
    B.add(mat, verts, faces)

PINK, BLUSH, WHITE = hexcol("#e07aa0"), hexcol("#f7c6d6"), hexcol("#fffaf8")
def petal_col(t, u):
    base = mix(PINK, BLUSH, smooth(0.05, 0.45, t)); c = mix(base, WHITE, smooth(0.35, 0.85, t))
    stripe = (1 - smooth(0.1, 0.35, abs(u))) * (1 - smooth(0.55, 0.9, t)) * 0.55   # pink midrib, like a stargazer
    return mix(c, PINK, stripe)

def axis_matrix(axis, spin):
    """Rotation taking +Z to `axis`, with a spin about it."""
    q = Vector((0, 0, 1)).rotation_difference(axis.normalized())
    return q.to_matrix().to_4x4() @ Matrix.Rotation(spin, 4, "Z")

def flower(tip, axis, scale=1.0, spin=0.0):
    R = axis_matrix(axis, spin)
    for k in range(6):
        outer = k % 2 == 0
        az = k * math.pi / 3 + (0.08 if outer else 0)
        xf = Matrix.Translation(tip) @ R @ Matrix.Rotation(az, 4, "Z") @ Matrix.Scale(scale, 4)
        blade(xf, 0.052 if outer else 0.049, 0.025 if outer else 0.028, math.radians(28), math.radians(112), 0.28, "petal",
              col_fn=petal_col, tipcurl=0.35, wavy=0.04 if not outer else 0.0)
    for k in range(6):   # filaments + anthers
        az = k * math.pi / 3 + 0.5; d = Vector((math.cos(az) * 0.35, math.sin(az) * 0.35, 1)).normalized()
        local = [Vector((0, 0, 0)) + (Vector((math.cos(az), math.sin(az), 0)) * 0.012 * (s / 6) ** 1.5 + Vector((0, 0, 0.042 * s / 6))) * scale for s in range(7)]
        pts = [Matrix.Translation(tip) @ R @ p for p in local]; tube(pts, 0.0011 * scale, "filament", seg=6)
        ellipsoid(pts[-1], 0.0016 * scale, 0.0016 * scale, 0.0048 * scale, "anther", xf=R @ Matrix.Rotation(az, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    pts = [Matrix.Translation(tip) @ R @ Vector((0, 0, 0.048 * scale * s / 6)) for s in range(7)]; tube(pts, 0.0014 * scale, "filament", seg=6)
    ellipsoid(pts[-1], 0.0028 * scale, 0.0028 * scale, 0.0022 * scale, "stem")

GREEN_W, GREEN = hexcol("#eef5e2"), hexcol("#a9cf9f")
def bud(tip, axis, length):
    R = axis_matrix(axis, random.random() * 6)
    ellipsoid(tip + axis.normalized() * length * 0.5, 0.0075, 0.0075, length * 0.5, "bud", xf=R,
              col_fn=lambda t: mix(GREEN, mix(GREEN_W, BLUSH, 0.35), smooth(0.3, 0.95, t)))

# pot: a glazed cream planter with a berry rim
lathe([(0.0, 0.0), (0.044, 0.0), (0.047, 0.006), (0.056, 0.07), (0.06, 0.092), (0.063, 0.1), (0.057, 0.102), (0.053, 0.093)], "pot")
lathe([(0.0615, 0.094), (0.0645, 0.1005), (0.0635, 0.104), (0.058, 0.1035)], "rim")
lathe([(0.0, 0.093), (0.053, 0.093)], "soil", seg=40)

# stems with flowers and buds
SOIL = 0.093
heads = [((-0.012, 0.006), (-0.06, 0.02, 0.215), 1.35, 0.3), ((0.016, -0.004), (0.07, -0.014, 0.255), 1.45, 1.2), ((0.002, 0.016), (0.004, 0.065, 0.175), 1.25, 2.6)]
for (bx, by), (tx, ty, tz), sc, sp in heads:
    p0 = Vector((bx, by, SOIL)); p2 = Vector((tx, ty, tz)); p1 = Vector((bx * 1.2, by * 1.2, SOIL + (tz - SOIL) * 0.6))
    pts = bezier(p0, p1, p2); tube(pts, 0.0034, "stem", r_end=0.0026)
    axis = (p2 - p1).normalized() + Vector((p2.x, p2.y, 0)).normalized() * 0.55
    flower(p2, axis, sc, sp)
for (bx, by), (tx, ty, tz), ln in [((0.008, 0.01), (0.03, 0.035, 0.235), 0.05), ((-0.01, -0.01), (-0.028, -0.04, 0.2), 0.042)]:
    p0 = Vector((bx, by, SOIL)); p2 = Vector((tx, ty, tz)); p1 = Vector((bx, by, SOIL + (tz - SOIL) * 0.65))
    pts = bezier(p0, p1, p2); tube(pts, 0.0028, "stem", r_end=0.0022); bud(p2, p2 - p1, ln)

# long arching leaves from the soil
for k in range(9):
    az = k / 9 * math.tau + random.uniform(-0.2, 0.2)
    xf = Matrix.Translation(Vector((math.cos(az) * 0.008, math.sin(az) * 0.008, SOIL - 0.002))) @ Matrix.Rotation(az, 4, "Z")
    blade(xf, random.uniform(0.11, 0.16), random.uniform(0.011, 0.015), math.radians(random.uniform(6, 16)), math.radians(random.uniform(55, 85)), 0.18, "leaf", nu=6, nv=18)

B.emit()

if PREVIEW:
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.render.resolution_x = sc.render.resolution_y = 700
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = hexcol("#d4e6c8"); w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0.42, -0.42, 0.3); cam.rotation_euler = (Vector((0, 0, 0.14)) - cam.location).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = 60
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA")); sc.collection.objects.link(fill); fill.data.energy = 25; fill.data.size = 0.6; fill.location = (-0.4, -0.3, 0.4)
    fill.rotation_euler = (Vector((0, 0, 0.12)) - fill.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = PREVIEW; bpy.ops.render.render(write_still=True)

kw = dict(filepath=OUT, export_format="GLB", export_apply=True)
try: bpy.ops.export_scene.gltf(**kw, export_vertex_color="ACTIVE")
except TypeError: bpy.ops.export_scene.gltf(**kw)
tris = sum(len(o.data.loop_triangles) if o.data.calc_loop_triangles() is None else 0 for o in bpy.data.objects if o.type == "MESH")
print("exported", OUT, "triangles", tris)

# Film-quality still of the room from the visitor's camera.
# usage: blender -b --factory-startup -P render.py -- room.glb lights.json camera.json out_prefix SAMPLES [day|night]
import bpy, json, sys, math
from mathutils import Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, LJ, CJ, OUT, SAMPLES = argv[0], argv[1], argv[2], argv[3], int(argv[4])
MODE = argv[5] if len(argv) > 5 else "day"
L, C = json.load(open(LJ)), json.load(open(CJ))
def B(p): return Vector((p[0], -p[2], p[1]))
def hexcol(h): h = h.lstrip("#"); return tuple(((int(h[i:i+2], 16) / 255) ** 2.2) for i in (0, 2, 4))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
for o in list(bpy.data.objects):
    if o.type in ("LIGHT", "CAMERA") or o.name.startswith("nb_"): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
# tiny light clips on the window corners export as see-through unlit boxes and render black; they are hidden in the page anyway
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.active_material and not o.active_material.node_tree.nodes.get("Principled BSDF") and max(o.dimensions) < 0.035 and min(o.dimensions) > 0.025:
        bpy.data.objects.remove(o, do_unlink=True)
# a soft sunset sky behind the window (the page's skyline lives outside the exported room)
def sky_plane(day):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-1.425, 3.3, 1.75), rotation=(math.pi / 2, 0, 0)); p = bpy.context.active_object; p.scale = (2.6, 2.4, 1)
    m = bpy.data.materials.new("sky"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 2.2 if day else 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    stops = [(0.0, "#ffd9b0"), (0.45, "#efb9c6"), (1.0, "#8eb4e0")] if day else [(0.0, "#6a3f7a"), (0.6, "#3a2766"), (1.0, "#14123a")]
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = stops[0][0], (*hexcol(stops[0][1]), 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = stops[-1][0], (*hexcol(stops[-1][1]), 1)
    e = ramp.color_ramp.elements.new(stops[1][0]); e.color = (*hexcol(stops[1][1]), 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Y"], ramp.inputs[0]); nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs[0])
    p.data.materials.append(m)
    p.visible_shadow = p.visible_diffuse = p.visible_glossy = p.visible_transmission = False   # seen by the camera only; never blocks the window light

def closer(col):
    m = bpy.data.materials.new("closer"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*hexcol(col), 1); return m
CEIL, WALLS = closer("#f6f1ea"), closer("#d4e6c8")
def plane(loc, rot, sx, sy, m):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); p = bpy.context.active_object; p.scale = (sx, sy, 1); p.data.materials.append(m)
plane((0.2, 0.0, 3.4), (0, 0, 0), 7.0, 5.4, CEIL); plane((3.5, 0.0, 1.7), (0, math.pi / 2, 0), 3.4, 5.4, WALLS)
# (no front wall: the camera sits there)

world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; bg = world.node_tree.nodes["Background"]
def light(name, kind, loc, power, color, **kw):
    d = bpy.data.lights.new(name, kind); d.energy = power; d.color = hexcol(color)
    for k, v in kw.items(): setattr(d, k, v)
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc; return o
def aim(o, target): o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()
sky_plane(MODE == "day")
lamp0, lampT = B(L["lamp"]), B(L["lampTarget"]); lamp = lamp0 + (lampT - lamp0).normalized() * 0.06
win_c = Vector((-1.425, 2.55 - 0.02, 1.7))
portal = light("portal", "AREA", win_c, 0, "#ffffff", shape="RECTANGLE", size=1.15, size_y=1.3); portal.data.cycles.is_portal = True; portal.rotation_euler = (math.radians(-90), 0, 0)
if MODE == "day":
    light("ceilfill", "AREA", Vector((0.2, 0.3, 3.3)), 45, "#fff4ea", shape="RECTANGLE", size=4.0, size_y=3.0)
    f = light("frontfill", "AREA", Vector((0.0, -2.3, 1.8)), 40, "#fff2e8", shape="RECTANGLE", size=3.5, size_y=1.6); aim(f, Vector((0.0, 2.4, 1.2)))
    bg.inputs[0].default_value = (*hexcol("#f4dccd"), 1); bg.inputs[1].default_value = 2.2
    s = light("sun", "SUN", B(L["sun"]), 7.0, "#ffd2c2", angle=math.radians(3)); aim(s, B(L["sunTarget"]))
    sp = light("lamp", "SPOT", lamp, 35, "#ffd79a", spot_size=math.radians(110), spot_blend=0.6, shadow_soft_size=0.03); aim(sp, lampT)
else:
    light("ceilfill", "AREA", Vector((0.2, 0.3, 3.3)), 3, "#fff4ea", shape="RECTANGLE", size=4.0, size_y=3.0)
    bg.inputs[0].default_value = (*hexcol("#2a2060"), 1); bg.inputs[1].default_value = 0.35
    sp = light("lamp", "SPOT", lamp, 45, "#ffcf8a", spot_size=math.radians(115), spot_blend=0.7, shadow_soft_size=0.03); aim(sp, lampT)
    light("lampglow", "POINT", lamp, 2.5, "#ffcf8a", shadow_soft_size=0.04)
    for i, b in enumerate(L["bulbs"]): light("fairy%d" % i, "POINT", B(b) + Vector((0, -0.07, 0)), 0.09, "#ffe3a0", shadow_soft_size=0.03)

# camera: three.js pose -> blender (y-up to z-up is +90 deg about X)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = B(C["pos"]); qx, qy, qz, qw = C["quat"]
cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = Quaternion((1, 0, 0), math.radians(90)) @ Quaternion((qw, qx, qy, qz))
cam.data.sensor_fit = "VERTICAL"; cam.data.angle_y = math.radians(C["fov"]); cam.data.clip_start = 0.05

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 4
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in [i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items] else "None"
sc.render.image_settings.file_format = "PNG"
for (w, h, tag) in [(1920, 1200, "hero"), (1200, 630, "og")]:
    sc.render.resolution_x, sc.render.resolution_y = w, h
    # the og crop is wider, so widen the vertical fov a touch less to keep the desk framed
    cam.data.angle_y = math.radians(C["fov"] * (1.0 if tag == "hero" else 0.86))
    sc.render.filepath = f"{OUT}-{MODE}-{tag}.png"; bpy.ops.render.render(write_still=True); print("saved", sc.render.filepath)

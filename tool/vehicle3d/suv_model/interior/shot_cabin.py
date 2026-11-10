"""The cabin from one of the photos' cameras (cabin.CAMERAS), beside the photo and blended over it.
shot_cabin.py <cabin.blend> <dash_front|driver_pov|rear_bench> <out.png> [car.blend to add the body and glass]"""
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import masks as M, cabin as C
from mathutils import Vector
blend, name, out = sys.argv[1:4]; bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend)); a = M.rgb(name); H, W = a.shape[:2]
if len(sys.argv) > 4:
    with bpy.data.libraries.load(os.path.abspath(sys.argv[4])) as (src, dst): dst.objects = [n for n in src.objects if n in ('body',)]
    for o in dst.objects: bpy.context.collection.objects.link(o)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.film_transparent = True
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.9, 0.9, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
pos, look, fov, col0, hide = C.CAMERAS[name]; cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'HORIZONTAL'; cam.data.angle = np.radians(fov); cam.data.clip_start = 0.02; cam.location = pos
for o in bpy.data.objects:
    if hide and o.name.startswith(tuple(hide)): o.hide_render = True
if col0 is not None: cam.data.shift_x = -(col0 - W / 2) / W          # the car's centre line is not at the photo's middle column
cam.rotation_euler = (Vector(look) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
lamp = bpy.data.objects.new('lamp', bpy.data.lights.new('lamp', 'POINT')); lamp.data.energy = 60; lamp.location = (pos[0], pos[1], min(pos[2] + 0.2, C.HEAD_Z - 0.05))      # (under the headliner: above it the roof shades it); sc.collection.objects.link(lamp)
for o in bpy.data.objects:
    if o.type == 'MESH': o.shadow_terminator_shading_offset = 0.35; o.shadow_terminator_geometry_offset = 0.4
sc.view_settings.view_transform = 'Standard'; sc.render.filepath = os.path.abspath(out); bpy.ops.render.render(write_still=True)
from PIL import Image
r = np.asarray(Image.open(out).convert('RGBA')).astype(float); obj = r[..., 3:4] / 255.0
comp = (r[..., :3] * obj + np.array([255, 0, 255.0]) * (1 - obj)); side = np.hstack([a, comp]).astype(np.uint8)
Image.fromarray(side).resize((side.shape[1] // 2, side.shape[0] // 2)).save(out.replace('.png', '_side.jpg'), quality=88)
Image.fromarray((0.5 * a + 0.5 * comp).astype(np.uint8)).resize((W * 3 // 4, H * 3 // 4)).save(out.replace('.png', '_blend.jpg'), quality=88)

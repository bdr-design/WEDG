"""An outside look at the assembled cabin (no body), to check how the parts stand together: over.py <cabin.blend> <out.png> [camx,camy,camz lookx,looky,lookz lens]"""
import bpy, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); sc = bpy.context.scene
pos = [float(v) for v in a[2].split(',')] if len(a) > 2 else (2.6, -2.9, 2.9); look = [float(v) for v in a[3].split(',')] if len(a) > 3 else (-0.4, 0.0, 1.0)
if len(a) > 5:
    for o in bpy.data.objects:
        if o.name.startswith(tuple(a[5].split(','))): o.hide_render = True
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'; sc.render.resolution_x, sc.render.resolution_y = 1200, 760
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.85, 0.87, 0.9, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = float(a[4]) if len(a) > 4 else 35; cam.data.clip_start = 0.02
cam.location = pos; cam.rotation_euler = (Vector(look) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 2.0; sun.rotation_euler = (0.7, 0.0, 0.6); sc.collection.objects.link(sun)
for o in bpy.data.objects:
    if o.type == 'MESH': o.shadow_terminator_shading_offset = 0.35; o.shadow_terminator_geometry_offset = 0.4
sc.view_settings.view_transform = 'Standard'; sc.render.filepath = os.path.abspath(a[1]); bpy.ops.render.render(write_still=True)

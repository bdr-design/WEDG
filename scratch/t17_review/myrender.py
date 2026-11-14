# T11 reviewer's own renders (Workbench, textured, studio light): one shot per call.
# usage: blendenv/bin/python myrender.py out.png view ortho_size cx cy cz glb[@dx,dy,dz] ...
#   view: side (camera at -Z looking +Z... see below) | front | below | top | tq (three-quarter) | head
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
out, view, size = a[0], a[1], float(a[2]); c = Vector(map(float, a[3:6])); files = a[6:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in files:
    p, _, off = f.partition('@')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    if off:
        d = Vector(map(float, off.split(',')))
        for o in set(bpy.data.objects) - before:
            if o.parent is None: o.location += d
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True
sh.show_cavity = False; sc.display_settings.display_device = 'sRGB'; sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 1000, 750
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.45, 0.45, 0.47)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO' if view != 'tq' else 'PERSP'; cam.data.ortho_scale = size; cam.data.lens = 85
# Blender Z up; birds face +X; their left is +Y
dirs = {'side': Vector((0, -1, 0)), 'other': Vector((0, 1, 0)), 'front': Vector((1, 0, 0)), 'below': Vector((0, 0, -1)),
        'top': Vector((0, 0, 1)), 'tq': Vector((0.8, -1, 0.35)).normalized(), 'head': Vector((0.15, -1, 0.05)).normalized(),
        'back': Vector((-1, 0, 0))}
d = dirs[view]; dist = size * 4 if view == 'tq' else 10
cam.location = c + d * dist
cam.rotation_euler = (-d).to_track_quat('-Z', 'Z' if view not in ('below', 'top') else 'X').to_euler()
if view == 'tq': cam.data.lens = 85; cam.location = c + d * size * 3.2
sc.render.filepath = out; bpy.ops.render.render(write_still=True)

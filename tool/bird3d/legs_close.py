"""Close renders of a rigged bird's legs from its built file: where the feathered shank (the trousers) meets the bare
tarsus, in the perched and landing poses, from four sides. The review's own check, kept: the tarsus's top once stood
out behind the trousers in every perched pose.

    python legs_close.py FILE.glb OUT.jpg [clip:frame ...]      (Blender's Python; default the saker's poses)
"""
import os
import sys

import bpy
from mathutils import Vector as V3

GLB, OUT = sys.argv[1], sys.argv[2]
POSES = [tuple((a.split(':')[0], int(a.split(':')[1]))) for a in sys.argv[3:]] or \
    [('perch_idle', 0), ('fist_idle', 0), ('land_cuff', 26), ('land_cuff', 45), ('mantle', 45), ('bind', 8)]
RES = 320
SIDES = [(0, 1, 0.1), (1, 0.6, 0.1), (-1, 0.6, 0.1), (0.3, 1, -0.6)]      # side, front, back, from below

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for name, o in meshes.items():
    o.hide_render = 'far' in name or 'hood' in name
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 16
sc.render.resolution_x = sc.render.resolution_y = RES
w = bpy.data.worlds.new('w')
w.color = (0.9, 0.9, 0.92)
sc.world = w
for rot, e in (((0.7, 0.2, 0.5), 4.0), ((2.2, 0.0, -2.0), 1.5)):
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sc.collection.objects.link(sun)
    sun.data.energy = e
    sun.rotation_euler = rot
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 50

from PIL import Image, ImageDraw  # noqa: E402

tiles = []
tmp = OUT + '.tile.png'
for clip, f in POSES:
    act = [a for a in bpy.data.actions if a.name == clip]
    if not act:
        print('no clip', clip)
        continue
    arm.animation_data.action = act[0]
    for o in meshes.values():      # the morph targets' own clip of the same name
        sk = o.data.shape_keys
        if sk is not None:
            if sk.animation_data is None:
                sk.animation_data_create()
            sk.animation_data.action = act[0]      # one action a clip, a slot for each animated thing (Blender 4.4 on)
            slots = [sl for sl in act[0].slots if sl.target_id_type == 'KEY']
            mine = [sl for sl in slots if sl.name_display.split('.')[0] == o.name.split('.')[0]] or slots
            if mine:
                sk.animation_data.action_slot = mine[0]
    sc.frame_set(f)
    bpy.context.view_layer.update()
    # (the mesh the clip does not show gathers to a point inside the body by its keyed morph target `hidden`)
    c = arm.matrix_world @ arm.pose.bones['tarsus.L'].head
    for dx, dy, dz in SIDES:
        cam.location = c + V3((dx, dy, dz)).normalized() * 0.22
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        im = Image.open(tmp).convert('RGB')
        ImageDraw.Draw(im).text((6, 6), f'{clip} {f}', fill=(0, 0, 0))
        tiles.append(im)
os.remove(tmp)
cols = len(SIDES)
sheet = Image.new('RGB', (RES * cols, RES * ((len(tiles) + cols - 1) // cols)), 'white')
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % cols) * RES, (i // cols) * RES))
sheet.save(OUT, quality=88)
print('wrote', OUT)

"""The rigged bird on the fist beside the approved static one, its legs close, from the same cameras in the world:
the look held, not only the cover (the review: a fix for the tarsus's top once made the trousers a thick bent sleeve).

    python legs_vs_static.py STATIC.glb RIG.glb OUT.jpg [clip frame]      (Blender's Python; default fist_idle 0)
Rows: the static, the rig; columns: side, front, three-quarter, back. Prints each pair's silhouette overlap in a
box round the legs (from the belly's bottom to the feet).
"""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector as V3

STATIC, RIGF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CLIP = sys.argv[4] if len(sys.argv) > 4 else 'fist_idle'
FRAME = int(sys.argv[5]) if len(sys.argv) > 5 else 0
RES = 360
AIM = V3((0.0, 0.0, 0.075))      # the legs on the fist (the cuff's top at about 0.04 m)
VIEWS = {'side': (0, 1, 0.05), 'front': (1, 0, 0.05), 'tq': (0.8, 0.8, 0.25), 'back': (-1, 0.15, 0.05)}


def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 16
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = True
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
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 0.2
    return sc, cam


def load(path, clip=None):
    bpy.ops.import_scene.gltf(filepath=path)
    for o in bpy.data.objects:
        if o.type == 'MESH' and ('far' in o.name or 'hood' in o.name or 'lod' in o.name or o.name.startswith('Ico')):
            o.hide_render = True
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if clip and arms:
        act = bpy.data.actions[clip]
        arms[0].animation_data.action = act
        for o in bpy.data.objects:
            sk = o.data.shape_keys if o.type == 'MESH' else None
            if sk is not None:
                if sk.animation_data is None:
                    sk.animation_data_create()
                sk.animation_data.action = act
                mine = [sl for sl in act.slots if sl.target_id_type == 'KEY' and sl.name_display.split('.')[0] == o.name.split('.')[0]]
                if mine:
                    sk.animation_data.action_slot = mine[0]
        bpy.context.scene.frame_set(FRAME)
    bpy.context.view_layer.update()


from PIL import Image, ImageDraw  # noqa: E402

rows = []
for label, path, clip in (('approved static', STATIC, None), (f'rig {CLIP} {FRAME}', RIGF, CLIP)):
    sc, cam = scene()
    load(path, clip)
    row = []
    for vn, d in VIEWS.items():
        cam.location = AIM + V3(d).normalized() * 1.0
        cam.rotation_euler = (AIM - cam.location).to_track_quat('-Z', 'Y').to_euler()
        tmp = OUT + f'.{vn}.png'
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        row.append((vn, Image.open(tmp).convert('RGBA')))
        os.remove(tmp)
    rows.append((label, row))
sheet = Image.new('RGB', (RES * len(VIEWS), RES * 2), (230, 230, 234))
for r, (label, row) in enumerate(rows):
    for c, (vn, im) in enumerate(row):
        sheet.paste(im, (c * RES, r * RES), im)
        ImageDraw.Draw(sheet).text((c * RES + 6, r * RES + 6), f'{label}: {vn}', fill=(0, 0, 0))
sheet.save(OUT, quality=88)
for c, vn in enumerate(VIEWS):
    a = np.array(rows[0][1][c][1])[..., 3] > 128
    b = np.array(rows[1][1][c][1])[..., 3] > 128
    lo = RES // 2      # the box: the lower half of the frame (below the aim point's line and the feet)
    a, b = a[lo - 60:], b[lo - 60:]
    print(f'{vn}: the legs\' silhouette overlap with the approved static {(a & b).sum() / max(1, (a | b).sum()):.3f}')
print('wrote', OUT)

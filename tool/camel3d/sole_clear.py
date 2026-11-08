"""Lowest point of each foot's mesh per frame (sole clearance in swing, penetration in stance)."""
import os, json
import bpy
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
arm = bpy.data.objects['CamelRig']
for tr in arm.animation_data.nla_tracks:
    tr.mute = True
arm.animation_data.action = bpy.data.actions['walk']
ob = bpy.data.objects['Camel']
vg = {g.name: g.index for g in ob.vertex_groups}
sel = {}
for leg, names in (('fore.L', ('ffoot.L', 'fpastern.L')), ('hind.L', ('hfoot.L', 'hpastern.L'))):
    ids = []
    for v in ob.data.vertices:
        w = sum(g.weight for g in v.groups if g.group in [vg[n] for n in names])
        if w > 0.5:
            ids.append(v.index)
    sel[leg] = np.array(ids)
sc = bpy.context.scene
out = {k: [] for k in sel}
for f in range(1, 45):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
    for k, ids in sel.items():
        out[k].append(round(float(co[ids, 2].min()) * 1000))
    ob.evaluated_get(dg).to_mesh_clear()
for k, v in out.items():
    print(k, 'min z per frame (mm):', v)
    print(k, 'max sole height', max(v), 'lowest', min(v))

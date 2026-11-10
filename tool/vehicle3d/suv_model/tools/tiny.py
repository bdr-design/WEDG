"""Faces under 0.01 mm2 in every mesh: tiny.py <blend>"""
import sys, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    t = [(p.area, tuple(round(c, 3) for c in o.matrix_world @ p.center)) for p in o.data.polygons if p.area < 1e-8]
    if t: print(o.name, len(t), 'faces under 0.01 mm2; smallest %.1e m2 at' % min(t)[0], min(t)[1], '; under 1e-10:', sum(a < 1e-10 for a, _ in t))

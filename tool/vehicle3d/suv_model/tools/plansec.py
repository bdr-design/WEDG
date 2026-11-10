"""A level cut through the tail: the surface met from behind at half-widths y (depth ahead of the car's rear end, mm),
and the surface met from the side at depths d (half-width, mm). Run: blendenv/bin/python plansec.py <blend> z [z ...]"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
ob = bpy.data.objects['body']; xe = min((ob.matrix_world @ Vector(c)).x for c in ob.bound_box)
for z in (float(v) for v in a[1:]):
    r = []
    for y in np.arange(0, 1.0001, 0.05):
        h, loc, n, i, o, m = sc.ray_cast(dg, Vector((-3.5, y, z)), Vector((1, 0, 0))); r.append('%4.0f' % ((loc.x - xe) * 1000) if h else '   .')
    print('z %.2f from behind, y 0..1.0 by 0.05: ' % z + ' '.join(r))
    r = []
    for d in np.arange(0.05, 0.6001, 0.05):
        h, loc, n, i, o, m = sc.ray_cast(dg, Vector((xe + d, 1.5, z)), Vector((0, -1, 0))); r.append('%4.0f' % (loc.y * 1000) if h else '   .')
    print('       from the side, d 0.05..0.60 by 0.05:  ' + ' '.join(r))

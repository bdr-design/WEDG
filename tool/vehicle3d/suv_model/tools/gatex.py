"""Tailgate depth: x of the first surface met from behind on a (y, z) grid, in mm behind x = -2.3 (bigger = further back).
Run: blendenv/bin/python gatex.py <blend> [y0 y1 z0 z1 ny nz]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
y0, y1, z0, z1 = (float(v) for v in a[1:5]) if len(a) > 4 else (-0.8, 0.8, 0.60, 1.10)
ny, nz = (int(v) for v in a[5:7]) if len(a) > 6 else (17, 11)
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
print('      ' + ' '.join('%5.2f' % (y0 + (y1 - y0) * i / (ny - 1)) for i in range(ny)))
for k in range(nz):
    z = z1 - (z1 - z0) * k / (nz - 1); row = []
    for i in range(ny):
        y = y0 + (y1 - y0) * i / (ny - 1)
        hit, loc, nor, fi, ob, mw = sc.ray_cast(dg, Vector((-3.5, y, z)), Vector((1, 0, 0)))
        row.append('%4.0f%s' % ((-2.3 - loc.x) * 1000, ob.name[0]) if hit else '   . ')
    print('%5.2f ' % z + ' '.join(row))

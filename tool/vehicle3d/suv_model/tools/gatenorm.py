"""Tailgate normals: for a grid of (y, z) a ray from behind; prints the up-tilt of the shading normal in tenths of a
degree (interpolated vertex normals, what the renderer shades with) and the face it hits.
Run: blendenv/bin/python gatenorm.py <blend> [y0 y1 z0 z1 ny nz]"""
import bpy, sys, math
from mathutils import Vector
from mathutils.interpolate import poly_3d_calc
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
y0, y1, z0, z1 = (float(v) for v in a[1:5]) if len(a) > 4 else (-0.8, 0.8, 0.60, 1.10)
ny, nz = (int(v) for v in a[5:7]) if len(a) > 6 else (17, 11)
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
print('      ' + ' '.join('%6.2f' % (y0 + (y1 - y0) * i / (ny - 1)) for i in range(ny)))
for k in range(nz):
    z = z1 - (z1 - z0) * k / (nz - 1); row = []
    for i in range(ny):
        y = y0 + (y1 - y0) * i / (ny - 1)
        hit, loc, nor, fi, ob, mw = sc.ray_cast(dg, Vector((-3.5, y, z)), Vector((1, 0, 0)))
        if not hit: row.append('   .  '); continue
        me = ob.evaluated_get(dg).data; p = me.polygons[fi]
        cn = [me.corner_normals[l].vector for l in p.loop_indices]; vs = [me.vertices[v].co for v in p.vertices]
        w = poly_3d_calc(vs, loc); n = sum((c * wi for c, wi in zip(cn, w)), Vector()).normalized()
        row.append('%5.0f%s' % (math.degrees(math.asin(n.z)) * 10, ob.name[0]))
    print('%5.2f ' % z + ' '.join(row))

"""What a ray from ahead of the car meets first, on a grid of (y, z): the object's first letter and its material's.
Run: blendenv/bin/python tools/fronthit.py <blend> y0 y1 z0 z1 ny nz"""
import bpy, sys
from mathutils import Vector
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); y0, y1, z0, z1 = (float(v) for v in a[1:5]); ny, nz = int(a[5]), int(a[6])
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
for k in range(nz):
    z = z1 - (z1 - z0) * k / (nz - 1); row = ''
    for i in range(ny):
        y = y0 + (y1 - y0) * i / (ny - 1); h, loc, n, fi, ob, m = sc.ray_cast(dg, Vector((4.0, y, z)), Vector((-1, 0, 0)))
        if not h: row += ' ..'; continue
        me = ob.evaluated_get(dg).data; mat = me.materials[me.polygons[fi].material_index]; row += ' ' + ob.name[0] + (mat.name[0] if mat else '?')
    print('%.3f%s' % (z, row))

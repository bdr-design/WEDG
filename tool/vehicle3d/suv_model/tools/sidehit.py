"""What a ray from the car's left meets first, on a grid of (x, z): the object's first letter and its material's.
Run: blendenv/bin/python sidehit.py <blend> x0 x1 z0 z1 nx nz"""
import bpy, sys
from mathutils import Vector
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); x0, x1, z0, z1 = (float(v) for v in a[1:5]); nx, nz = int(a[5]), int(a[6])
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
for k in range(nz):
    z = z1 - (z1 - z0) * k / (nz - 1); row = ''
    for i in range(nx):
        x = x0 + (x1 - x0) * i / (nx - 1); h, loc, n, fi, ob, m = sc.ray_cast(dg, Vector((x, 2.0, z)), Vector((0, -1, 0)))
        if not h: row += ' ..'; continue
        me = ob.evaluated_get(dg).data; mat = me.materials[me.polygons[fi].material_index]
        row += ' ' + ob.name[0] + (mat.name[0] if mat else '?')
    print('%.3f%s' % (z, row))

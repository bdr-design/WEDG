"""Open and non-manifold edges of an object, listed by where they are.
   openedges.py <blend> [object] [x0 x1]"""
import bpy, bmesh, sys
from collections import Counter
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects[a[1] if len(a) > 1 else 'body']
x0, x1 = (float(a[2]), float(a[3])) if len(a) > 3 else (-9, 9)
bm = bmesh.new(); bm.from_mesh(ob.data); M = ob.matrix_world
C = Counter(); rows = []
for e in bm.edges:
    n = len(e.link_faces)
    if n == 2: continue
    p = M @ ((e.verts[0].co + e.verts[1].co) / 2)
    if not x0 <= p.x <= x1: continue
    key = (round(p.x, 1), round(abs(p.y) * 5) / 5, round(p.z * 5) / 5, n)
    C[key] += 1; rows.append((n, p, e.calc_length()))
for k, v in sorted(C.items()): print('x %+.1f |y| %.1f z %.1f faces %d : %d' % (*k, v))
for n, p, l in rows:
    if n != 1: print('  %d-face edge at %+.3f %+.3f %.3f len %.4f' % (n, p.x, p.y, p.z, l))
z = [f for f in bm.faces if f.calc_area() < 1e-10]
for f in z: c = M @ f.calc_center_median(); print('  zero face at %+.3f %+.3f %.3f' % (c.x, c.y, c.z))

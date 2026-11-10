"""Hollow (concave) folds in the body's paint inside a box (real frame): hollow.py <blend> x0,x1,z0,z1 [min degrees]"""
import sys, bpy, bmesh, math
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); ob = bpy.data.objects['body']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update(); pi = [i for i, m in enumerate(ob.data.materials) if m.name == 'paint']
x0, x1, z0, z1 = (float(v) for v in sys.argv[2].split(',')); lim = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
for sgn in (1, -1):
    rows = []
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.is_convex: continue
        c = (e.verts[0].co + e.verts[1].co) / 2
        if not (x0 < c.x < x1 and z0 < c.z < z1 and c.y * sgn > 0.6) or any(f.material_index not in pi for f in e.link_faces): continue
        a = math.degrees(e.calc_face_angle(0.0))
        if a >= lim: rows.append((a, c.x, c.z))
    rows.sort(reverse=True)
    print('side %+d: %d hollow edges of %.0f degrees or more, %d over 5; worst %s' % (sgn, len(rows), lim, sum(r[0] > 5 for r in rows), ' '.join('%.1f@(%.2f,%.2f)' % r for r in rows[:5])))

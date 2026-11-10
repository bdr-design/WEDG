"""Edges of the body's paint that fold by 6 degrees or more inside a box (real frame): foldedges.py <blend> name:x0,x1,z0,z1 ..."""
import sys, bpy, bmesh, math
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); ob = bpy.data.objects['body']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update(); pi = [i for i, m in enumerate(ob.data.materials) if m.name == 'paint']
for spec in sys.argv[2:]:
    name, box = spec.split(':'); x0, x1, z0, z1 = (float(v) for v in box.split(','))
    for sgn in (1, -1):
        n = 0; worst = (0, None); tot = 0
        for e in bm.edges:
            if len(e.link_faces) != 2: continue
            c = (e.verts[0].co + e.verts[1].co) / 2
            if not (x0 < c.x < x1 and z0 < c.z < z1 and c.y * sgn > 0.6): continue
            if any(f.material_index not in pi for f in e.link_faces): continue
            tot += 1; a = math.degrees(e.calc_face_angle(0.0))
            if a >= 6: n += 1
            if a > worst[0]: worst = (a, tuple(round(v, 3) for v in c))
        print('%s side %+d: %d edges of 6 degrees or more out of %d, worst %.0f at %s' % (name, sgn, n, tot, worst[0], worst[1]))

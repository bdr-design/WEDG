"""The body's open-edge loops, smallest first: where each is, how many edges, how long. A window opening is a long
loop; a crack left by a cut is a short one. Also edges shared by more than two faces.
Run: blendenv/bin/python loops.py <blend> [object] [how many]"""
import bpy, bmesh, sys
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); ob = bpy.data.objects[a[1] if len(a) > 1 else 'body']
bm = bmesh.new(); bm.from_mesh(ob.data); M = ob.matrix_world
op = {e for e in bm.edges if len(e.link_faces) == 1}; seen = set(); loops = []
for e in op:
    if e in seen: continue
    grp = []; stack = [e]; seen.add(e)
    while stack:
        c = stack.pop(); grp.append(c)
        for v in c.verts:
            for n in v.link_edges:
                if n in op and n not in seen: seen.add(n); stack.append(n)
    loops.append(grp)
loops.sort(key=lambda g: sum(e.calc_length() for e in g))
print('open edges', len(op), 'in', len(loops), 'loops;  edges with 3+ faces', sum(1 for e in bm.edges if len(e.link_faces) > 2))
for g in loops[:int(a[2]) if len(a) > 2 else 12]:
    c = sum(((M @ ((e.verts[0].co + e.verts[1].co) / 2)) for e in g), M.to_translation() * 0) / len(g)
    print('  %4d edges, %.4f m, about %+.3f %+.3f %.3f' % (len(g), sum(e.calc_length() for e in g), c.x, c.y, c.z))

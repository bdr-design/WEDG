"""Does the cabin stay inside the hull? inhull.py <cabin.blend> <car.blend>
For each cabin object: how many of its points (vertices, and each triangle's middle and edges' middles) lie outside
the body's skin or the glass, and the worst of them.
A point is inside when a ray from it to the cabin's middle crosses neither; how far outside is its distance to the
nearest face of body or glass."""
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
cab, car = sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=os.path.abspath(cab)); names = [o.name for o in bpy.data.objects if o.type == 'MESH']
with bpy.data.libraries.load(os.path.abspath(car)) as (src, dst): dst.objects = [n for n in src.objects if n in ('body', 'glass', 'roof_glass')]
for o in dst.objects: bpy.context.collection.objects.link(o)
dg = bpy.context.evaluated_depsgraph_get(); trees = [BVHTree.FromObject(o, dg) for o in dst.objects]; mid = [Vector((x, 0.0, 1.25)) for x in (0.3, -0.5, -1.3)]
tot = 0
for n in names:
    o = bpy.data.objects[n]; mw = o.matrix_world; out = []
    me = o.data; me.calc_loop_triangles(); co = [mw @ v.co for v in me.vertices]; pts = list(co)
    for t in me.loop_triangles:
        a, b, c = (co[i] for i in t.vertices); pts += [(a + b + c) / 3, (a + b) / 2, (b + c) / 2, (c + a) / 2]
    for p in pts:
        m = min(mid, key=lambda q: abs(q.x - p.x)); d = m - p; L = d.length
        if L < 1e-6: continue
        if any((h := t.ray_cast(p, d / L, L))[0] is not None for t in trees):
            out.append((min(t.find_nearest(p)[3] for t in trees), tuple(round(c, 3) for c in p)))
    if out:
        out.sort(reverse=True); tot += len(out)
        if os.environ.get('LIST') == n: print('\n'.join('   %.0f mm %s' % (d * 1e3, p) for d, p in out[::max(1, len(out) // 16)]))
        print('%-16s %5d of %6d points outside; worst %.1f mm at %s' % (n, len(out), len(pts), out[0][0] * 1e3, out[0][1]))
print('outside in all: %d' % tot)

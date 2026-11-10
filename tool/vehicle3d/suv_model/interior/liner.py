"""The trim that lines the hull wherever no other part covers it: the strips between the doors' trims and the glass,
the sills, the gap round the rear wells' arches, the footwells' sides, the rear quarters and D pillars, the
tailgate's inside and the roof's edges. No photo shows these; the rule is the hull's own shape: rays from inside
the cabin find the body (not the glass) and the liner lies LINER_IN inside it, so it follows every fold of the skin
and leaves the glass clear. Black below the windows, beige above (as the pillars' and roof's trims are)."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import imats, cabin as C

LINER_IN = 0.020          # how far inside the skin
STEP = 0.05               # the grid's spacing
BEIGE_Z = 1.40            # beige above, black below
# (kind, the grid's two ranges, extra): 'side' casts across the car from its middle line at (x, z); 'rear' casts back
# from x -1.50 at (y, z); 'front' casts forward from x 0 at (y, z)
REGIONS = [('side', (-2.42, 0.95), (1.12, 1.86)),         # above the doors' trims: the belt strips, pillars, roof rails, quarters
           ('side', (-0.95, 1.05), (0.57, 0.68)),         # the sills (further back the floor steps up over the axle)
           ('side', (-0.18, -0.09), (0.57, 1.30)),        # between the front and rear doors' trims (the B pillar's foot)
           ('side', (-1.25, -0.72), (0.64, 1.15)),        # round the rear wells' arches, where the rear doors' trims are cut
           ('side', (0.75, 1.10), (0.57, 1.15)),          # the footwells' sides
           ('side', (-2.42, -1.80), (0.72, 1.15)),        # (beside the wells their trims and the cargo trims are enough)        # the cargo room's sides, behind the trims there
           ('rear', (-0.80, 0.80), (0.60, 1.86)),         # the tailgate and the roof's rear edge
           ('front', (-0.80, 0.80), (1.66, 1.86))]        # the windshield's header


def _hull(path):
    with bpy.data.libraries.load(path) as (src, dst): dst.objects = [n for n in src.objects if n in ('body', 'glass', 'roof_glass')]
    for o in dst.objects: bpy.context.collection.objects.link(o)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); trees = {o.name: BVHTree.FromObject(o, dg) for o in dst.objects}
    for o in dst.objects: bpy.data.objects.remove(o)
    return trees


def _cast(trees, p, d):
    best = None
    for nm, t in trees.items():
        h = t.ray_cast(Vector(p), Vector(d), 3.0)
        if h[0] is not None and (best is None or h[3] < best[1]): best = (nm, h[3], h[0], h[1])
    return best


def build(hull_path, cover=(), name='cabin_liner'):
    """cover: the cabin's other objects; where one of them already stands in front of the hull, no liner is laid."""
    trees = _hull(hull_path); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); covers = [BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons]) for o in cover]  # (in the car's frame)
    bm = bmesh.new(); mats = [imats.m('cabin_black'), imats.m('trim_leather')]
    for kind, (a0, a1), (b0, b1) in REGIONS:
        A = np.arange(a0, a1 + 1e-6, STEP); B = np.arange(b0, b1 + 1e-6, STEP)
        sides = (1, -1) if kind == 'side' else (1,)
        for s in sides:
            grid = {}
            for i, a in enumerate(A):
                for j, b in enumerate(B):
                    if kind == 'side': p, d = (a, 0.0, b), (0.0, s, 0.0)
                    elif kind == 'rear': p, d = (-1.50, a, b), (-1.0, 0.0, 0.0)
                    else: p, d = (0.0, a, b), (1.0, 0.0, 0.0)
                    h = _cast(trees, p, d)
                    if not h or h[0] != 'body': continue
                    q = h[2]
                    if (kind == 'side' and abs(q.y) < 0.55) or (kind == 'rear' and q.x > -2.0) or (kind == 'front' and q.x < 0.4): continue      # not the wall this pass is for
                    if any((c := t.ray_cast(Vector(p), Vector(d), h[1]))[0] is not None and c[3] > h[1] - 0.05 for t in covers): continue      # already covered
                    n = h[3] if h[3].dot(Vector(d)) < 0 else -h[3]
                    if -n.dot(Vector(d)) < 0.5: continue          # met edge-on (a flange, an arch's lip): no liner there
                    grid[i, j] = (h[1], q + n * (LINER_IN if kind == 'side' else 0.025), n)      # (off the skin along its own normal: where it curves, along the ray was not enough)
            verts = {}
            for (i, j), (dist, q, n) in grid.items(): verts[i, j] = (dist, bm.verts.new(q), n)
            for i in range(len(A) - 1):
                for j in range(len(B) - 1):
                    k = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                    if not all(c in verts for c in k): continue
                    ds = [verts[c][0] for c in k]
                    if max(ds) - min(ds) > 0.06: continue          # a jump from one wall to another: no face across it
                    ns = [verts[c][2] for c in k]
                    if min(ns[a].dot(ns[b]) for a in range(4) for b in range(a)) < 0.93: continue      # a tight fold: a flat face would cut through it
                    vs = [verts[c][1] for c in k]
                    if s < 0 and kind == 'side': vs = vs[::-1]
                    f = bm.faces.new(vs); f.smooth = True; f.material_index = 1 if f.calc_center_median().z > BEIGE_Z else 0
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

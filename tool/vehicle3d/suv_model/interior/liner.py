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
# Each pass: a fan of rays and how its hits are used. 'side' casts across the car from its middle line at (x, z);
# 'rear' casts back from x -1.50 at (y, z); 'front' casts forward from x 0 at (y, z); 'radial' casts every way from a
# point (azimuth, elevation in degrees), for the corners the others meet edge-on. step: the grid's spacing in each of
# its two ranges ('near': skip only where a part stands within the liner's own depth of the skin); fold: the least cosine between a cell's corner normals (a flat face across a sharper fold would cut
# through the skin; small cells and deep insets allow more); cover: skip where another cabin part already stands within 5 cm of the hull; inset: how far inside
# the skin (the passes that overlap others sit deeper, so no two layers lie on one another).
def R(kind, a, b, step=(0.05, 0.05), cover=True, inset=0.020, centre=None, fold=0.93):
    return dict(kind=kind, a=a, b=b, step=step, cover=cover, inset=inset, centre=centre, fold=fold)
REGIONS = [R('side', (-2.42, 0.95), (1.12, 1.86)),                       # above the doors' trims: pillars, roof rails, quarters
           R('side', (-1.18, 0.95), (1.18, 1.40), step=(0.04, 0.02), cover='near', inset=0.024, fold=0.5),     # the belt strips, finer, laid behind the trims' top edges
           R('side', (-0.95, 1.05), (0.57, 0.68)),                       # the sills (further back the floor steps up over the axle)
           R('side', (-0.18, -0.09), (0.57, 1.20), cover='near'),                      # between the front and rear doors' trims (the B pillar's foot)
           R('side', (-1.25, -0.72), (0.64, 1.15), step=(0.03, 0.03), inset=0.026, fold=0.7),                      # round the rear wells' arches, where the rear doors' trims are cut
           R('side', (0.75, 1.10), (0.57, 1.15)),                        # the footwells' sides
           R('side', (-2.42, -1.80), (0.72, 1.15)),                      # the cargo room's sides (beside the wells their trims and the cargo trims are enough)
           R('rear', (-0.80, 0.80), (0.60, 1.86), inset=0.032),                     # the tailgate and the roof's rear edge
           R('front', (-0.80, 0.80), (1.66, 1.86)),                      # the windshield's header
           R('radial', (0.0, 360.0), (-35.0, 70.0), step=(3.0, 3.0), inset=0.040, centre=(-1.90, 0.0, 1.25), fold=0.6),     # the cargo room's corners, the tailgate's surround, the D pillars
           R('radial', (-100.0, 100.0), (-40.0, 40.0), step=(3.0, 3.0), inset=0.034, centre=(0.30, 0.0, 1.15), fold=0.6)]   # the cowl, the A pillars' edges, the dashboard's ends and the footwells


def _hull(path):
    with bpy.data.libraries.load(path) as (src, dst): dst.objects = [n for n in src.objects if n in ('body', 'glass', 'roof_glass')]
    for o in dst.objects: bpy.context.collection.objects.link(o)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); trees = {o.name: BVHTree.FromObject(o, dg) for o in dst.objects}
    global GLASS_EDGES; GLASS_EDGES = []
    for o in dst.objects:          # the glass's free edges, with the normal of the pane each bounds and that pane's middle (car's frame)
        if not o.name.endswith('glass'): continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        for e in bm.edges:
            if e.is_boundary and e.link_faces:
                f = e.link_faces[0]; GLASS_EDGES.append((e.verts[0].co.copy(), e.verts[1].co.copy(), f.normal.copy(), f.calc_center_median()))
        bm.free()
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
    for rg in REGIONS:
        kind = rg['kind']; A = np.arange(rg['a'][0], rg['a'][1] + 1e-6, rg['step'][0]); B = np.arange(rg['b'][0], rg['b'][1] + 1e-6, rg['step'][1])
        for s in ((1, -1) if kind == 'side' else (1,)):
            grid = {}
            for i, a in enumerate(A):
                for j, b in enumerate(B):
                    if kind == 'side': p, d = (a, 0.0, b), (0.0, s, 0.0)
                    elif kind == 'rear': p, d = (-1.50, a, b), (-1.0, 0.0, 0.0)
                    elif kind == 'front': p, d = (0.0, a, b), (1.0, 0.0, 0.0)
                    else:
                        az, el = math.radians(a), math.radians(b); p = rg['centre']; d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
                    h = _cast(trees, p, d)
                    if not h or h[0] != 'body': continue
                    q = h[2]
                    if (kind == 'side' and abs(q.y) < 0.55) or (kind == 'rear' and q.x > -2.0) or (kind == 'front' and q.x < 0.4) or (kind == 'radial' and q.z < C.FLOOR_Z + 0.03): continue      # not the wall this pass is for
                    if rg['cover'] == 'near' and any(t.ray_cast(h[2] - Vector(d) * 0.001, -Vector(d), rg['inset'] + 0.06)[0] is not None for t in covers): continue      # (a part within the liner's own depth of the skin, or just in front of it: the liner would pass through it, or lie hidden behind it; the trims have no backs)
                    if rg['cover'] is True and any((c := t.ray_cast(Vector(p), Vector(d), h[1]))[0] is not None and c[3] > h[1] - 0.05 for t in covers): continue      # already covered
                    if kind == 'radial' and any((c := t.ray_cast(Vector(p), Vector(d), h[1]))[0] is not None for t in covers): continue      # (a fan: only what it sees past every part)
                    n = h[3] if h[3].dot(Vector(d)) < 0 else -h[3]
                    if -n.dot(Vector(d)) < (0.25 if kind == 'radial' else 0.5): continue          # met edge-on (a flange, an arch's lip): no liner there
                    grid[i, j] = (h[1], q + n * rg['inset'], n)      # (off the skin along its own normal: where it curves, along the ray was not enough)
            verts = {}
            for (i, j), (dist, q, n) in grid.items(): verts[i, j] = (dist, bm.verts.new(q), n)
            for i in range(len(A) - 1):
                for j in range(len(B) - 1):
                    k = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                    if not all(c in verts for c in k): continue
                    ds = [verts[c][0] for c in k]
                    if max(ds) - min(ds) > (0.10 if kind == 'radial' else 0.06): continue          # a jump from one wall to another: no face across it
                    ns = [verts[c][2] for c in k]
                    if min(ns[a].dot(ns[b]) for a in range(4) for b in range(a)) < rg['fold']: continue      # a tight fold: a flat face would cut through it
                    vs = [verts[c][1] for c in k]
                    f = bm.faces.new(vs); f.smooth = True; f.material_index = 1 if f.calc_center_median().z > BEIGE_Z else 0
                    c0 = f.calc_center_median()
                    o = {'side': (c0.x, 0.0, c0.z), 'rear': (-1.50, c0.y, c0.z), 'front': (0.0, c0.y, c0.z)}.get(kind, p)
                    if f.normal.dot(Vector(o) - c0) < 0: f.normal_flip()     # facing into the cabin (toward where its rays came from)
    # (seals along the glass's edges were tried: where the skin turns in at the glass's edge a band in the glass's plane
    # leaves the hull. The slivers of skin they were to cover, between the glass and the liner, are left: 0.5 to 0.9 % of the view.)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

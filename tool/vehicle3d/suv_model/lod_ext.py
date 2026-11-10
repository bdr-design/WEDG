"""The car's outside in game layers (the owner's decision of 10 Nov: layered detail). lod_ext.py <suv.blend> <out.blend> <target>
1. Faces nobody sees are dropped: a face stays if a point of it is in plain view, facing it, from one of the eyes:
   a ring round the car at several heights and distances (a player standing, crouching, on a camel, the camera
   behind the car), from above, and from the seats inside (the bonnet, the mirrors and the wipers through the glass,
   which is clear from inside in the game). The underbody, the wells' insides and the hull's inner faces go.
2. What is left is thinned toward the target (Blender's collapse decimation, which keeps the outline best), object by
   object in proportion to its share; small objects (under SMALL triangles) are kept whole, and sharp edges and
   material borders are kept."""
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SMALL = 600


def eyes():
    E = []
    for r in (3.5, 7.0):
        for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            for z in (0.5, 1.2, 1.7, 2.6):
                E.append(Vector((r * 1.2 * math.cos(a), r * math.sin(a), z)))
    for x in (-2.0, 0.0, 2.0):
        for y in (-1.5, 0.0, 1.5): E.append(Vector((x, y, 5.0)))
    for p in ((-0.09, 0.43, 1.57), (-0.09, -0.43, 1.57), (-1.0, 0.44, 1.52), (-1.0, -0.44, 1.52)): E.append(Vector(p))
    return E


def visible(obs, E):
    V, P, owner = [], [], []
    for k, o in enumerate(obs):
        mw = o.matrix_world; n0 = len(V); V += [mw @ v.co for v in o.data.vertices]; flip = mw.determinant() < 0
        for p in o.data.polygons: P.append([n0 + i for i in (p.vertices[::-1] if flip else p.vertices)]); owner.append((k, p.index))
    tree = BVHTree.FromPolygons(V, P, epsilon=0.0); seen = [set() for _ in obs]
    for fi, (verts, (k, pi)) in enumerate(zip(P, owner)):
        pts = [Vector(V[i]) for i in verts]; c = sum(pts, Vector()) / len(pts); n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        if n.length < 1e-14: continue
        n.normalize(); probes = [c] + [q + (c - q) * 0.1 for q in pts]; ok = False
        for e in E:
            for q in probes:
                d = q - e; L = d.length
                if n.dot(-d) <= 0: continue
                h = tree.ray_cast(e, d / L, L + 1e-4)
                if h[2] == fi or (h[0] is not None and (h[0] - q).length < 2e-4): ok = True; break
            if ok: break
        if ok: seen[k].add(pi)
    return seen


if __name__ == '__main__':
    src, out, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); obs = [o for o in bpy.data.objects if o.type == 'MESH']
    tri = lambda o: (o.data.calc_loop_triangles(), len(o.data.loop_triangles))[1]
    before = sum(tri(o) for o in obs)
    for o in obs:
        bpy.context.view_layer.objects.active = o; m = o.modifiers.new('tri', 'TRIANGULATE'); m.keep_custom_normals = True; bpy.ops.object.modifier_apply(modifier='tri')
    seen = visible(obs, eyes())
    for o, s in zip(obs, seen):
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in s], context='FACES'); bm.to_mesh(o.data); bm.free()
    culled = {o.name: tri(o) for o in obs}; total = sum(culled.values()); small = sum(v for v in culled.values() if v < SMALL)
    r = max(0.05, (target - small) / max(1, total - small))
    for o in obs:
        if culled[o.name] >= SMALL and r < 1:
            bpy.context.view_layer.objects.active = o; m = o.modifiers.new('lod', 'DECIMATE'); m.ratio = r; m.use_collapse_triangulate = True
            m.delimit = {'MATERIAL', 'SHARP', 'SEAM', 'UV'} if hasattr(m, 'delimit') else m.delimit; bpy.ops.object.modifier_apply(modifier='lod')
    print('outside: %d -> seen %d -> %d triangles (ratio %.3f on the large objects)' % (before, total, sum(tri(o) for o in obs), r))
    for o in sorted(obs, key=lambda o: -culled[o.name])[:8]: print('  %-16s seen %6d -> %6d' % (o.name, culled[o.name], tri(o)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

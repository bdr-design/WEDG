"""The cabin's game layer (the owner's decision of 10 Nov: layered detail; the interior is loaded only while the player
is inside, about 40k triangles). lod_cabin.py <cabin.blend> <out.blend> [target]
1. Faces no occupant can see are dropped: a face stays if one of its points (its middle or a corner pulled 5 % in)
   is in plain view, facing it, from one of the eyes in EYES (a box of positions round each seat's eye, so that a
   head turning and leaning is allowed for). The glass is opaque from outside, so nothing inside is seen from there.
Nothing else is done to the faces kept: a collapse decimation spoiled the small parts' shading and shapes, and
merging flat stretches changed the shading of the lofted surfaces and opened holes in the door's wood. What is left
over the owner's 40k is to be taken at the source (fewer sections in the wheel's rim, the seats' and the bench's lofts)."""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def eyes():
    import cabin as C
    out = []
    for cx, cy, cz in (C.SEATED_EYE, (C.SEATED_EYE[0], -C.SEATED_EYE[1], C.SEATED_EYE[2]), (-0.20, 0.0, 1.52), (-1.0, 0.44, 1.52), (-1.0, 0.0, 1.50), (-1.0, -0.44, 1.52)):      # (and between the front seats: a head leaning in)
        for dx in (-0.12, 0.0, 0.12):
            for dy in (-0.15, 0.0, 0.15):
                for dz in (-0.08, 0.06):
                    out.append(Vector((cx + dx, cy + dy, cz + dz)))
    return out


def visible_faces(obs, E):
    """For each object, the set of its polygon indices seen from some eye."""
    V, P, owner = [], [], []
    for k, o in enumerate(obs):
        mw = o.matrix_world; n0 = len(V); V += [mw @ v.co for v in o.data.vertices]
        flip = mw.determinant() < 0                      # a mirrored object: its faces wind the other way in the car's frame
        for p in o.data.polygons: P.append([n0 + i for i in (p.vertices[::-1] if flip else p.vertices)]); owner.append((k, p.index))
    tree = BVHTree.FromPolygons(V, P, epsilon=0.0); seen = [set() for _ in obs]
    for fi, (verts, (k, pi)) in enumerate(zip(P, owner)):
        pts = [Vector(V[i]) for i in verts]; c = sum(pts, Vector()) / len(pts); probes = [c] + [q + (c - q) * 0.05 for q in pts[:4]] + [(pts[i] + pts[(i + 1) % len(pts)]) * 0.5 * 0.95 + c * 0.05 for i in range(min(4, len(pts)))]
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0]);
        if n.length < 1e-12: continue
        n.normalize(); hit = False
        for e in E:
            for q in probes:
                d = q - e; L = d.length
                if L < 1e-6 or n.dot(-d) <= 0: continue          # seen from behind: does not count (back faces are culled in the game)
                h = tree.ray_cast(e, d / L, L + 1e-4)
                if h[2] == fi or (h[0] is not None and (h[0] - q).length < 1e-4): hit = True; break
            if hit: break
        if hit: seen[k].add(pi)
    return seen


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; target = int(sys.argv[3]) if len(sys.argv) > 3 else 40000
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); obs = [o for o in bpy.data.objects if o.type == 'MESH']
    tri = lambda o: (o.data.calc_loop_triangles(), len(o.data.loop_triangles))[1]
    before = {o.name: tri(o) for o in obs}
    for o in obs:          # triangles first: a long curved face (the door's wood) can have every test point outside it
        bpy.context.view_layer.objects.active = o; m = o.modifiers.new('tri', 'TRIANGULATE'); m.keep_custom_normals = True; m.quad_method = 'BEAUTY'; m.ngon_method = 'BEAUTY'
        bpy.ops.object.modifier_apply(modifier='tri')
    seen = visible_faces(obs, eyes())
    for o, s in zip(obs, seen):
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in s], context='FACES'); bm.to_mesh(o.data); bm.free()
    culled = {o.name: tri(o) for o in obs}; total = sum(culled.values())
    for o in obs: print('%-16s %6d -> seen %6d -> %6d' % (o.name, before[o.name], culled[o.name], tri(o)))
    print('cabin: %d -> %d seen -> %d triangles' % (sum(before.values()), total, sum(tri(o) for o in obs)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

"""The interior of an outside model, set in our hull (private use only: see thirdparty/README.md).
thirdparty_cabin.py <model_in_car_frame.blend> <our suv.blend> <out.blend>
The model is first put in our car's frame (its axles on ours, scaled by the wheelbase: see the commit). Here: the
badges and name-plates go (thirdparty_car.py's lists); the faces of its outside materials (paint, glass, lamps,
tyres) are dropped; of the rest, an object is kept when most of it stands inside the model's own outside
(model_hull()). What is kept is joined into one object, tp_cabin, but for the driver's door's own trim (the parts under
the model's FrontLeft_Door), joined apart as tp_doorcard: it swings open with the door."""
import bpy, bmesh, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUTSIDE = {'CarPaint', 'ClearGlass', 'Light_Red_Back_Lower', 'Light_White_Back', 'Light_Red_Back', 'Light_glass', 'Front_Light',
           'GlassRed', 'BackSpotLight', 'SpotLight', 'Wheel', 'Mirror'}
KEEP_SHARE = 0.6
LAMPS = (((-2.45, -1.95), (0.42, 0.92), (1.0, 1.35)), ((-2.45, -1.95), (-0.92, -0.42), (1.0, 1.35)))     # the tail lamps' pockets (housings, reflectors, the red bars): outside, whatever the hull test says
EMBLEM_PARTS = ('polySurface469',)        # the steering wheel's emblem (chrome, 64 x 42 mm, on the pad): dropped by the model's own name, not by place
CABIN_X, CABIN_Z = (-2.45, 1.10), 0.50          # an object's middle must be between the tailgate and the firewall, and over the floor


def model_hull():
    """inside(p): no face of the model's own outside (its paint, glass and lamps: OUTSIDE) between p and the cabin's
    middle line. (Our code-built hull was used first: its shape is not this model's, and the tail lamps' housings, in
    the body's pockets, read as inside it and were lost from both files.)"""
    V, F = [], []
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        mats = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name.split('.')[0] in OUTSIDE]
        if not mats: continue
        mw = o.matrix_world; n0 = len(V); V += [mw @ v.co for v in o.data.vertices]
        F += [[n0 + i for i in p.vertices] for p in o.data.polygons if p.material_index in mats]
    tree = BVHTree.FromPolygons(V, F); mids = [Vector((x, 0.0, 1.20)) for x in (0.4, -0.4, -1.3, -2.0)]
    def inside(p):
        m = min(mids, key=lambda q: abs(q.x - p.x)); dv = m - p; L = dv.length
        return L < 0.003 or tree.ray_cast(p + dv / L * 0.002, dv / L, L - 0.002)[0] is None      # (from 2 mm off: a part of an outside material would meet its own face)
    return inside


def in_lamps(c):
    return any(x[0] < c.x < x[1] and y[0] < c.y < y[1] and z[0] < c.z < z[1] for x, y, z in LAMPS)


def inner_small(o, inside):
    """A small part (under 30 cm) standing inside the model's own outside belongs to the interior whatever its
    material: the inside mirror's glass (Mirror), the overhead console's lamps and lens (outside materials, which
    otherwise sent them to the outside file, where the dark windscreen hid them, so they were in neither)."""
    mw = o.matrix_world; P = [mw @ v.co for v in o.data.vertices]
    if not P: return False
    lo = Vector((min(p.x for p in P), min(p.y for p in P), min(p.z for p in P))); hi = Vector((max(p.x for p in P), max(p.y for p in P), max(p.z for p in P)))
    c = (lo + hi) / 2
    if max(hi - lo) > 0.3 or not (-1.5 < c.x < 1.0 and c.z > 1.4 and abs(c.y) < 0.5): return False      # (by the roof's middle only: the lamps' reflectors at the corners read as inside too)
    sample = P[::max(1, len(P) // 20)]
    return sum(inside(p) for p in sample) / len(sample) >= KEEP_SHARE


def main(src, car, out):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); bpy.context.view_layer.update()
    import thirdparty_car as TCAR
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('_')[0] in TCAR.BADGES + list(TCAR.PLATES.values())]: bpy.data.objects.remove(o)      # (the badges and the name-plates: none in this file either)
   
    inside = model_hull()
    def under(o, name):
        p = o.parent
        while p:
            if p.name == name: return True
            p = p.parent
        return False
    kept = []
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('_')[0] in EMBLEM_PARTS]: bpy.data.objects.remove(o)
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        me = o.data; bad = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name.split('.')[0] in OUTSIDE]
        if bad and inner_small(o, inside): bad = []                         # (an interior part of an outside material: the inside mirror's glass, the overhead lamps)
        if bad:
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in bad], context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(me); bm.free()
        if not len(me.polygons): continue
        mw = o.matrix_world; pts = [mw @ v.co for v in me.vertices]; sample = pts[::max(1, len(pts) // 40)]
        c = sum(pts, Vector()) / len(pts)
        if not (CABIN_X[0] < c.x < CABIN_X[1] and c.z > CABIN_Z) or in_lamps(c): continue          # the cabin only: not the engine's bay, the chassis, the wheels or the tail lamps
        if sum(inside(p) for p in sample) / len(sample) >= KEEP_SHARE: kept.append(o)
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o not in kept]: bpy.data.objects.remove(o)
    door = [o for o in kept if under(o, 'FrontLeft_Door')]
    for o in kept: mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in [o for o in bpy.data.objects if o.type != 'MESH']: bpy.data.objects.remove(o)
    def join(group, name):
        bpy.ops.object.select_all(action='DESELECT')
        for o in group: o.data = o.data.copy() if o.data.users > 1 else o.data; o.select_set(True)
        bpy.context.view_layer.objects.active = group[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active; ob.name = ob.data.name = name; ob.data.calc_loop_triangles(); return ob
    dc = join(door, 'tp_doorcard'); print('tp_doorcard: %d objects, %d triangles' % (len(door), len(dc.data.loop_triangles)))
    ob = join([o for o in kept if o not in door], 'tp_cabin')
    V = np.array([v.co for v in ob.data.vertices])
    print('tp_cabin: %d objects joined, %d triangles, %d materials; x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (len(kept), len(ob.data.loop_triangles), len(ob.data.materials), V[:,0].min(), V[:,0].max(), V[:,1].min(), V[:,1].max(), V[:,2].min(), V[:,2].max()))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    main(*sys.argv[-3:])

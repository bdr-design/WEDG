"""The interior of an outside model, set in our hull (private use only: see thirdparty/README.md).
thirdparty_cabin.py <model_in_car_frame.blend> <our suv.blend> <out.blend>
The model is first put in our car's frame (its axles on ours, scaled by the wheelbase: see the commit). Here: the
faces of its outside materials (paint, glass, lamps, tyres) are dropped; of the rest, an object is kept when most of
it stands inside our hull (a point is inside when a ray from it to the cabin's middle crosses neither our body nor
our glass). What is kept is joined into one object, tp_cabin."""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUTSIDE = {'CarPaint', 'ClearGlass', 'Light_Red_Back_Lower', 'Light_White_Back', 'Light_Red_Back', 'Light_glass', 'Front_Light',
           'GlassRed', 'BackSpotLight', 'SpotLight', 'Wheel', 'Mirror'}
KEEP_SHARE = 0.6
CABIN_X, CABIN_Z = (-2.45, 1.10), 0.50          # an object's middle must be between the tailgate and the firewall, and over the floor


def main(src, car, out):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); bpy.context.view_layer.update()
    with bpy.data.libraries.load(os.path.abspath(car)) as (s, d): d.objects = [n for n in s.objects if n in ('body', 'glass', 'roof_glass')]
    for o in d.objects: bpy.context.collection.objects.link(o)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hull = [BVHTree.FromObject(o, dg) for o in d.objects]; mids = [Vector((x, 0.0, 1.20)) for x in (0.4, -0.4, -1.3, -2.0)]
    def inside(p):
        m = min(mids, key=lambda q: abs(q.x - p.x)); dv = m - p; L = dv.length
        return L < 1e-6 or not any(t.ray_cast(p, dv / L, L)[0] is not None for t in hull)
    kept = []
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o not in d.objects]:
        me = o.data; bad = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name.split('.')[0] in OUTSIDE]
        if bad:
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in bad], context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(me); bm.free()
        if not len(me.polygons): continue
        mw = o.matrix_world; pts = [mw @ v.co for v in me.vertices]; sample = pts[::max(1, len(pts) // 40)]
        c = sum(pts, Vector()) / len(pts)
        if not (CABIN_X[0] < c.x < CABIN_X[1] and c.z > CABIN_Z): continue          # the cabin only: not the engine's bay, the chassis or the wheels
        if sum(inside(p) for p in sample) / len(sample) >= KEEP_SHARE: kept.append(o)
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and o not in kept]: bpy.data.objects.remove(o)
    for o in [o for o in bpy.data.objects if o.type != 'MESH']: bpy.data.objects.remove(o)
    for o in kept: o.matrix_world = o.matrix_world.copy()
    bpy.ops.object.select_all(action='DESELECT')
    for o in kept: o.select_set(True)
    bpy.context.view_layer.objects.active = kept[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = 'tp_cabin'; ob.data.calc_loop_triangles()
    V = np.array([v.co for v in ob.data.vertices])
    print('tp_cabin: %d objects joined, %d triangles, %d materials; x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (len(kept), len(ob.data.loop_triangles), len(ob.data.materials), V[:,0].min(), V[:,0].max(), V[:,1].min(), V[:,1].max(), V[:,2].min(), V[:,2].max()))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    main(*sys.argv[-3:])

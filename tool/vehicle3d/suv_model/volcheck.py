"""Signed volume and open edges of every mesh object: volcheck.py <blend>. A negative volume means the faces look inward."""
import bpy, bmesh, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type != 'MESH': continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    v = bm.calc_volume(signed=True); ob = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
    z = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    c = sum((f.calc_center_median() for f in bm.faces), start=__import__('mathutils').Vector()) / max(1, len(bm.faces))
    flag = '  <-- NEGATIVE' if v < -1e-7 else ''
    print(f'{o.name:26s} vol {v:+.5f} open {ob:5d} nonman {nm:4d} zero {z:3d} y {c.y:+.3f}{flag}')
    bm.free()

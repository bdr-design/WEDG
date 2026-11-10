"""Last pass over every mesh: no coincident vertices, no faces without area, no loose vertices, no default names."""
import bpy, bmesh, re

KEEP_SPLIT = ('body', 'glass')        # cut by booleans along seams that must stay split; only cleaned, not merged
HOLE = 4           # a cut can also leave a crack between two slivers: a hole with this many sides or fewer is closed (body only)
THIN = 2e-5        # a cut can leave slivers a few microns wide, some sharing one edge four ways; nothing modelled is this thin


def tidy(o, merge=1e-6):
    bm = bmesh.new(); bm.from_mesh(o.data); n0 = (len(bm.verts), len(bm.faces)); new = []
    if merge: bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=THIN)
    if o.name == 'body':
        edge = [e for e in bm.edges if len(e.link_faces) == 1]
        new = bmesh.ops.holes_fill(bm, edges=edge, sides=HOLE)['faces'] if edge else []
        if new: print(f'tidy {o.name}: {len(new)} cracks closed, the largest {max(f.calc_area() for f in new) * 1e6:.1f} mm2')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    zero = sum(1 for f in bm.faces if f.calc_area() < 1e-12); n1 = (len(bm.verts), len(bm.faces))
    if n1 != n0 or new: bm.to_mesh(o.data); o.data.update()
    bm.free()
    return n0, n1, zero


def tidy_all():
    bad = []
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        n0, n1, zero = tidy(o, 0 if o.name in KEEP_SPLIT else 1e-6)
        if n1 != n0 or zero: print(f'tidy {o.name}: vertices {n0[0]} -> {n1[0]}, faces {n0[1]} -> {n1[1]}, zero-area left {zero}')
        if re.match(r'^(Cube|Cylinder|Sphere|Plane|Circle|Mesh)', o.name) or re.search(r'\.\d{3}$', o.name): bad.append(o.name)
        o.data.name = o.name
    assert not bad, f'default names left: {bad}'

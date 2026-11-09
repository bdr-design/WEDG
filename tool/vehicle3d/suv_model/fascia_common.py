"""Shared helpers for the front and rear parts (steps 3-4): the front and the rear, modelled as parts laid on the body's end faces at the positions measured on the
front and rear photos (a 10 cm grid over each photo, out/02_front_grid.jpg and out/03_rear_grid.jpg).

Each part is a shape in (y, z) placed on the shell: a ray from in front (or behind) finds the surface, the part
follows it, standing proud by its offset and given a thickness. Rounded rectangles for lamps, panels and frames,
thin bars for the chrome."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector

def rrect(y0, y1, z0, z1, r, n=6):
    """A rounded rectangle as a polygon in (y, z)."""
    r = min(r, (y1 - y0) / 2, (z1 - z0) / 2); pts = []
    for cy, cz, a0 in ((y1 - r, z1 - r, 0), (y0 + r, z1 - r, 90), (y0 + r, z0 + r, 180), (y1 - r, z0 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    return np.array(pts)

def inside(poly, P):
    x, y = P[:, 0], P[:, 1]; c = np.zeros(len(P), bool); j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        hit = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi); c ^= hit; j = i
    return c

class Placer:
    def __init__(self, shell, end):
        self.shell = shell; self.end = end            # +1: the front face (rays from +x), -1: the rear face
    def hit(self, y, z):
        o = Vector((self.end * 6.0, y, z)); d = Vector((-self.end, 0, 0))
        r = self.shell.ray_cast(o, d)
        if not r[0]: return None, None
        # only the end face: a ray past the rounded corner would run on and hit the flank far along the car
        if (self.end > 0 and r[1].x < 2.05) or (self.end < 0 and r[1].x > -2.10): return None, None
        return r[1], r[2]

def part(placer, name, poly, mat, offset=0.004, thick=0.01, step=0.012, hole=None):
    """A slab over the polygon (minus an optional hole polygon), following the surface, `offset` out from it."""
    y0, z0 = poly.min(0); y1, z1 = poly.max(0)
    ys = np.arange(y0, y1 + step, step); zs = np.arange(z0, z1 + step, step)
    Y, Z = np.meshgrid(ys, zs, indexing='ij'); P = np.stack([Y.ravel(), Z.ravel()], 1)
    keep = inside(poly, P)
    if hole is not None: keep &= ~inside(hole, P)
    keep = keep.reshape(Y.shape)
    idx = -np.ones(Y.shape, int); V = []
    for i in range(len(ys)):
        for j in range(len(zs)):
            if not keep[i, j]: continue
            loc, nrm = placer.hit(ys[i], zs[j])
            if loc is None: continue
            idx[i, j] = len(V); V.append(tuple(loc + nrm * offset))
    F = []
    for i in range(len(ys) - 1):
        for j in range(len(zs) - 1):
            q = [idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]]
            if min(q) >= 0: F.append(q if placer.end > 0 else q[::-1])
    if not F: return None
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    if thick:
        for x in bpy.context.selected_objects: x.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        m = o.modifiers.new('sol', 'SOLIDIFY'); m.thickness = thick; m.offset = -1; m.use_even_offset = True
        bpy.ops.object.modifier_apply(modifier='sol')
    return o

def bar(placer, name, y0, y1, z, mat, h=0.012, offset=0.012, n=40, zcurve=None):
    """A chrome bar across the face at height z (zcurve(y) bends it), standing `offset` proud."""
    V, F = [], []
    ys = np.linspace(y0, y1, n)
    for y in ys:
        zz = z + (zcurve(y) if zcurve else 0)
        loc, nrm = placer.hit(y, zz)
        if loc is None: loc, nrm = Vector((placer.end * 2.4, y, zz)), Vector((placer.end, 0, 0))
        b = loc + nrm * offset
        for dz, dx in ((-h / 2, -0.004), (-h / 2, 0.004), (h / 2, 0.004), (h / 2, -0.004)):
            V.append(tuple(b + Vector((0, 0, dz)) + nrm * dx))
    for i in range(n - 1):
        for j in range(4):
            a = i * 4 + j; F.append([a, i * 4 + (j + 1) % 4, (i + 1) * 4 + (j + 1) % 4, (i + 1) * 4 + j])
    F.append([3, 2, 1, 0]); k = (n - 1) * 4; F.append([k, k + 1, k + 2, k + 3])
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return o


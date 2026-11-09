"""Parts laid on the body's end surface with clean outlines and real depth.

The body's surface round one end is taken as a function of (u, z): u is the arc on a cylinder about a vertical axis on
the centre line, so u = 0 is the centre and the surface carries on round the corner onto the flank. A part is a polygon
in (u, z). It is triangulated with its outline kept exact (a constrained Delaunay triangulation), every vertex is put
on the surface, and the patch is given a front and a back at chosen distances out from the surface. The same solid is
used as a cutter (an exact boolean cut that leaves a real recess in the shell) or as a part standing in or on it.

Outlines are measured on the photos: front-photo points (y, z) and side-photo points (x, z) are both turned into
(u, z) through the surface itself."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt


def activate(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o


def join(objs, name):
    objs = [o for o in objs if o]
    for x in bpy.context.selected_objects: x.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o


class Surf:
    """The shell's outer surface round one end (+1 the front, -1 the rear), frozen as it is when this is made, so
    later cuts do not move the parts placed after them."""
    R0 = 1.25                                    # u is an arc at about the nose's distance from the axis, so it reads in metres

    def __init__(self, shell, end=1, xa=1.2, z_ref=1.0, ease=(0.60, 0.75)):
        self.end, self.xa = end, end * xa
        me = shell.data
        self.bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])

        self._normals(z_ref, ease)

    def dir(self, u):
        a = u / self.R0; return Vector((self.end * math.cos(a), math.sin(a), 0.0))

    def _normals(self, z, ease):
        """The angle of the surface normal (seen from above) along u at height z, smoothed. Parts round the corner go
        in along it; near the middle it is eased to straight back (0 inside ease[0], the full angle past ease[1]) so
        their walls stay parallel to the walls of the middle parts, which go straight back."""
        U, Pn = [], []
        for u in np.arange(0.0, 1.9, 0.01):
            p = self.at(u, z)
            if p is None: break
            U.append(u); Pn.append((p.x, p.y))
        U = np.array(U); Pn = np.array(Pn); t = np.gradient(Pn, axis=0)
        A = np.arctan2(-self.end * t[:, 0], t[:, 1]); A[0] = 0.0
        A = np.convolve(np.r_[A[5:0:-1] * -1, A, np.full(5, A[-1])], np.ones(11) / 11, 'valid')
        A = np.maximum.accumulate(np.clip(A, 0.0, None))
        k = np.clip((U - ease[0]) / (ease[1] - ease[0]), 0, 1); self._U, self._A = U, A * k * k * (3 - 2 * k)

    def ndir(self, u):
        a = math.copysign(float(np.interp(abs(u), self._U, self._A)), u)
        return Vector((self.end * math.cos(a), math.sin(a), 0.0))

    def at(self, u, z):
        """The surface point at (u, z), or None where the body does not reach."""
        d = self.dir(u); r = self.bvh.ray_cast(Vector((self.xa, 0.0, z)) + d * 4.0, -d)
        return r[0]

    def u_of(self, p): return math.atan2(p.y, self.end * (p.x - self.xa)) * self.R0

    def F(self, y, z):
        """A point seen in the end view at (y, z) -> (u, z)."""
        r = self.bvh.ray_cast(Vector((self.end * 6.0, y, z)), Vector((-self.end, 0, 0)))
        if r[0] is None: raise ValueError(f'no surface in the end view at y {y:.3f}, z {z:.3f}')
        return np.array([self.u_of(r[0]), z])

    def S(self, x, z, s=1):
        """A point seen in the side view at (x, z) on side s -> (u, z)."""
        r = self.bvh.ray_cast(Vector((x, s * 6.0, z)), Vector((0, -s, 0)))
        if r[0] is None: raise ValueError(f'no surface in the side view at x {x:.3f}, z {z:.3f}')
        return np.array([self.u_of(r[0]), z])

    def Fpoly(self, pts, seg=0.012):
        """A polygon drawn in the end view (y, z), every edge cut into short pieces, in (u, z)."""
        return np.array([self.F(y, z) for y, z in resample(np.asarray(pts, float), seg)])


def resample(poly, seg, closed=True):
    """Cut every edge into pieces no longer than seg."""
    out = []; n = len(poly)
    for i in range(n if closed else n - 1):
        a, b = poly[i], poly[(i + 1) % n]; k = max(1, int(math.ceil(np.linalg.norm(b - a) / seg)))
        for j in range(k): out.append(a + (b - a) * j / k)
    if not closed: out.append(poly[-1])
    return np.array(out)


def fillet(poly, r, n=5):
    """Round the corners of a polygon. r is one radius or one per corner (0 keeps the corner sharp)."""
    poly = np.asarray(poly, float); m = len(poly); rs = [r] * m if np.isscalar(r) else list(r); out = []
    for i in range(m):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % m]
        ua, uc = a - b, c - b; la, lc = np.linalg.norm(ua), np.linalg.norm(uc); ua, uc = ua / la, uc / lc
        ang = math.acos(float(np.clip(ua @ uc, -1, 1)))
        if rs[i] <= 0 or ang > math.pi - 1e-3: out.append(b); continue
        t = min(rs[i] / math.tan(ang / 2), 0.45 * la, 0.45 * lc); rr = t * math.tan(ang / 2)
        bis = ua + uc; bis /= np.linalg.norm(bis); ctr = b + bis * (rr / math.sin(ang / 2))
        p0, p1 = b + ua * t, b + uc * t
        a0 = math.atan2(*(p0 - ctr)[::-1]); a1 = math.atan2(*(p1 - ctr)[::-1]); da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(n + 1):
            aa = a0 + da * k / n; out.append(ctr + rr * np.array([math.cos(aa), math.sin(aa)]))
    return np.array(out)


def rrect(y0, y1, z0, z1, r, n=5):
    return fillet(np.array([(y0, z0), (y1, z0), (y1, z1), (y0, z1)]), r, n)


def inside(poly, P):
    x, y = P[:, 0], P[:, 1]; c = np.zeros(len(P), bool); j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        c ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi); j = i
    return c


def mesh2d(poly, grid, hole=None, seg=0.012, extra=None, chains=None):
    """Triangles filling a polygon in (u, z): its outline kept exactly, plus inner points on a grid. extra are free
    inner points; chains are inner polylines whose edges are kept (a ridge or a crease that no triangle may cross)."""
    poly = resample(np.asarray(poly, float), seg)
    keep = np.r_[True, np.linalg.norm(np.diff(poly, axis=0), axis=1) > 1e-5]; poly = poly[keep]
    if np.linalg.norm(poly[0] - poly[-1]) < 1e-5: poly = poly[:-1]
    x, y = poly[:, 0], poly[:, 1]
    if (x * np.roll(y, -1) - np.roll(x, -1) * y).sum() < 0: poly = poly[::-1]
    lo, hi = poly.min(0), poly.max(0)
    if grid:
        gu = np.arange(lo[0] + grid / 2, hi[0], grid); gz = np.arange(lo[1] + grid / 2, hi[1], grid)
        G = np.array([(a, b) for a in gu for b in gz]).reshape(-1, 2)
    else: G = np.zeros((0, 2))
    edge_pts = poly
    faces = [list(range(len(poly)))]; coords = [Vector(p) for p in poly]
    if hole is not None:
        hole = resample(np.asarray(hole, float), seg)
        faces.append(list(range(len(coords), len(coords) + len(hole)))); coords += [Vector(p) for p in hole]
        edge_pts = np.vstack([poly, hole])
    if len(G):
        ok = inside(poly, G)
        if hole is not None: ok &= ~inside(hole, G)
        d = np.sqrt(((G[:, None, :] - edge_pts[None, :, :]) ** 2).sum(-1)).min(1); ok &= d > 0.45 * grid
        coords += [Vector(p) for p in G[ok]]
    if extra is not None: coords += [Vector(p) for p in np.asarray(extra, float)]
    edges = []
    for ch in (chains or ()):
        o = len(coords); coords += [Vector(p) for p in np.asarray(ch, float)]
        edges += [(o + i, o + i + 1) for i in range(len(ch) - 1)]
    res = delaunay_2d_cdt(coords, edges, faces, 1, 1e-7)
    P = np.array([v[:] for v in res[0]]); T = [list(f) for f in res[2]]
    if hole is not None:
        ctr = np.array([P[t].mean(0) for t in T]); T = [t for t, h in zip(T, inside(hole, ctr)) if not h]
    return P, T


def _place(S, P, mode):
    pts, dirs, miss = [], [], 0
    for u, z in P:
        p = S.at(u, z)
        if p is None:                                 # just past the body's edge: take the surface a little nearer its middle
            miss += 1
            for k in range(1, 40):
                p = S.at(u, z + (0.004 * k if z < 0.8 else -0.004 * k))
                if p is not None: p = Vector((p.x, p.y, z)); break
            if p is None: raise ValueError(f'no surface at u {u:.3f}, z {z:.3f}')
        pts.append(p); dirs.append(Vector((S.end, 0, 0)) if mode == 'x' else S.ndir(u) if mode == 'n' else S.dir(u))
    return pts, dirs, miss


def _val(v, p, u, z): return v(p, u, z) if callable(v) else v


def solid(S, name, poly, mat, front, back=None, mode='n', grid=0.03, seg=0.012, hole=None, bevel=0.0, sym=False,
          sharp=40.0, cap=True, extra=None, chains=None):
    """A part over a polygon in (u, z). Its front face is `front` metres out from the surface and its back `back`
    (negative: behind the surface), measured straight back for mode 'x', along the surface normal for 'n' (see
    Surf._normals) and out from the axis for 'radial'. front and back are numbers or functions of (surface point,
    u, z). back None gives an open sheet; cap False leaves the back face out (a part that stands in the body).
    sym adds the mirror image on the other side. bevel chamfers the front rim."""
    P, T = mesh2d(poly, grid, hole, seg, extra, chains)
    V, Fc = [], []
    for sgn in ((1, -1) if sym else (1,)):
        Q = P * np.array([sgn, 1.0]); pts, dirs, miss = _place(S, Q, mode); o = len(V); n = len(Q)
        V += [tuple(p + d * _val(front, p, u, z)) for p, d, (u, z) in zip(pts, dirs, Q)]
        if back is not None: V += [tuple(p + d * _val(back, p, u, z)) for p, d, (u, z) in zip(pts, dirs, Q)]
        tris = []
        for t in T:                                   # every triangle is turned to face outward
            a, b, c = (Vector(V[o + i]) for i in t)
            tris.append(t if (b - a).cross(c - a).dot(dirs[t[0]]) > 0 else t[::-1])
        Fc += [[o + i for i in t] for t in tris]
        if back is not None:
            if cap: Fc += [[o + n + i for i in t[::-1]] for t in tris]
            E = {(t[i], t[(i + 1) % 3]) for t in tris for i in range(3)}
            Fc += [[o + a, o + n + a, o + n + b, o + b] for a, b in E if (b, a) not in E]      # the walls
        if miss: print(f'  {name}: {miss} of {n} points were past the body edge')
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], Fc); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    if mat: me.materials.append(mat)
    if bevel:
        activate(ob); m = ob.modifiers.new('bv', 'BEVEL'); m.width = bevel; m.segments = 1; m.limit_method = 'ANGLE'
        m.angle_limit = math.radians(50); bpy.ops.object.modifier_apply(modifier='bv')
    for p in ob.data.polygons: p.use_smooth = True
    ob.data.set_sharp_from_angle(angle=math.radians(sharp))
    return ob


def cut(shell, cutters, mat, name='recess'):
    """Cut the cutters out of the shell; the new walls and floors take `mat`."""
    c = join(cutters, name + '_cutter'); c.data.materials.clear(); c.data.materials.append(mat)
    for p in c.data.polygons: p.material_index = 0
    if mat.name not in shell.data.materials: shell.data.materials.append(mat)
    activate(shell)
    mo = shell.modifiers.new(name, 'BOOLEAN'); mo.operation = 'DIFFERENCE'; mo.object = c; mo.solver = 'EXACT'
    mo.material_mode = 'TRANSFER'
    n0 = len(shell.data.polygons)
    bpy.ops.object.modifier_apply(modifier=name); bpy.data.objects.remove(c)
    print(f'  cut {name}: shell faces {n0} -> {len(shell.data.polygons)}')

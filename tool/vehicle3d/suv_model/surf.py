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
from mathutils.interpolate import poly_3d_calc


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
        self._co = [v.co.copy() for v in me.vertices]; self._vn = [v.normal.copy() for v in me.vertices]
        self._pv = [p.vertices[:] for p in me.polygons]
        self.bvh = BVHTree.FromPolygons([c[:] for c in self._co], self._pv)

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

    def atn(self, u, z):
        """The surface point at (u, z) and the surface's smooth normal there, turned to face outward."""
        d = self.dir(u); r = self.bvh.ray_cast(Vector((self.xa, 0.0, z)) + d * 4.0, -d)
        if r[0] is None: return None, None
        # the normal is blended from the face's corners: the face's own normal jumps from one face to the next, and
        # parts pushed out along it come out stepped
        vs = self._pv[r[2]]; w = poly_3d_calc([self._co[i] for i in vs], r[0])
        n = sum((self._vn[i] * k for i, k in zip(vs, w)), Vector())
        n = n.normalized() if n.length > 1e-6 else r[1]
        return r[0], (n if n.dot(d) >= 0 else -n)

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


def clip(poly, axis, lo=None, hi=None):
    """The part of a polygon between lo and hi along one axis (0 across, 1 up)."""
    poly = [np.asarray(p, float) for p in poly]
    for bound, sign in ((lo, 1.0), (hi, -1.0)):
        if bound is None: continue
        out = []
        for i, b in enumerate(poly):
            a = poly[i - 1]; da, db = sign * (a[axis] - bound), sign * (b[axis] - bound)
            if (da >= 0) != (db >= 0): out.append(a + (b - a) * da / (da - db))
            if db >= 0: out.append(b)
        poly = out
    return np.array(poly)


def ribbon(chain, w, off=0.0):
    """A thin closed polygon along an open chain. w is its width (one number or one per point); off moves it sideways
    (to the left of the direction the chain runs in)."""
    c = np.asarray(chain, float); ws = np.full(len(c), w, float) if np.isscalar(w) else np.asarray(w, float)
    t = np.gradient(c, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; nm = np.c_[-t[:, 1], t[:, 0]]
    return np.vstack([c + nm * (off + ws / 2)[:, None], (c + nm * (off - ws / 2)[:, None])[::-1]])


def arc(ctr, r, a0, a1, n=6):
    """Points on a circle from angle a0 to a1 (degrees)."""
    return [(ctr[0] + r * math.cos(math.radians(a)), ctr[1] + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n + 1)]


def inside(poly, P):
    x, y = P[:, 0], P[:, 1]; c = np.zeros(len(P), bool); j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        c ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi); j = i
    return c


def mesh2d(poly, grid, hole=None, seg=0.012, extra=None, chains=None, kept=None):
    """Triangles filling a polygon in (u, z): its outline kept exactly, plus inner points on a grid (one spacing, or
    (across, up) where the surface needs closer rows than columns). extra are free
    inner points; chains are inner polylines whose edges are kept (a ridge or a crease that no triangle may cross).
    kept, a set, is filled with the edges that were asked for (outlines and chains), as pairs of point numbers."""
    poly = resample(np.asarray(poly, float), seg)
    keep = np.r_[True, np.linalg.norm(np.diff(poly, axis=0), axis=1) > 1e-5]; poly = poly[keep]
    if np.linalg.norm(poly[0] - poly[-1]) < 1e-5: poly = poly[:-1]
    x, y = poly[:, 0], poly[:, 1]
    if (x * np.roll(y, -1) - np.roll(x, -1) * y).sum() < 0: poly = poly[::-1]
    lo, hi = poly.min(0), poly.max(0)
    if grid:
        du, dz = grid if isinstance(grid, tuple) else (grid, grid); grid = min(du, dz)
        gu = np.arange(lo[0] + du / 2, hi[0], du); gz = np.arange(lo[1] + dz / 2, hi[1], dz)
        G = np.array([(a, b) for a in gu for b in gz]).reshape(-1, 2)
    else: G = np.zeros((0, 2))
    edge_pts = poly
    faces = [list(range(len(poly)))]; coords = [Vector(p) for p in poly]
    holes = [] if hole is None else [resample(np.asarray(h, float), seg) for h in (hole if isinstance(hole, list) else [hole])]
    for h in holes:
        faces.append(list(range(len(coords), len(coords) + len(h)))); coords += [Vector(p) for p in h]
        edge_pts = np.vstack([edge_pts, h])
    if len(G):
        ok = inside(poly, G)
        for h in holes: ok &= ~inside(h, G)
        d = np.sqrt(((G[:, None, :] - edge_pts[None, :, :]) ** 2).sum(-1)).min(1); ok &= d > 0.45 * grid
        coords += [Vector(p) for p in G[ok]]
    if extra is not None: coords += [Vector(p) for p in np.asarray(extra, float)]
    edges = []
    for ch in (chains or ()):
        o = len(coords); coords += [Vector(p) for p in np.asarray(ch, float)]
        edges += [(o + i, o + i + 1) for i in range(len(ch) - 1)]
    res = delaunay_2d_cdt(coords, edges, faces, 1, 1e-7)
    if kept is not None: kept.update(frozenset(e) for e, o in zip(res[1], res[4]) if o)
    P = np.array([v[:] for v in res[0]]); T = [list(f) for f in res[2]]
    for h in holes:
        ctr = np.array([P[t].mean(0) for t in T]); T = [t for t, i in zip(T, inside(h, ctr)) if not i]
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
        n = S.atn(u, z)[1] if mode == 'surf' else None
        pts.append(p); dirs.append(Vector((S.end, 0, 0)) if mode == 'x' else S.dir(u) if mode == 'radial' else n or S.ndir(u))
    return pts, dirs, miss


def _val(v, p, u, z): return v(p, u, z) if callable(v) else v


def _relax(pts, tris, kept):
    """The same triangles, paired again by their shape in space. They were paired in (u, z), and where the surface
    leans far over a short step in z is a long one along it: the pairing then leaves long triangles lying across the
    curve, which fold against their neighbours by 40 degrees and more. Edges in kept stay as they are."""
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts]
    for t in tris: bm.faces.new([vs[i] for i in t])
    bm.verts.index_update()
    ed = [e for e in bm.edges if len(e.link_faces) == 2 and frozenset((e.verts[0].index, e.verts[1].index)) not in kept]
    bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=ed, method='ANGLE')
    out = [tuple(v.index for v in f.verts) for f in bm.faces]; bm.free(); return out


def solid(S, name, poly, mat, front, back=None, mode='n', grid=0.03, seg=0.012, hole=None, bevel=0.0, sym=False,
          sharp=40.0, cap=True, extra=None, chains=None, relax=None):
    """A part over a polygon in (u, z). Its front face is `front` metres out from the surface and its back `back`
    (negative: behind the surface), measured straight back for mode 'x', along the surface normal seen from above
    for 'n' (see Surf._normals), out from the axis for 'radial', and along the surface's own normal for 'surf' (for
    parts on faces that lean, like the bumper's underside). hole is one polygon or a list of them. front and back are numbers or functions of (surface point,
    u, z). back None gives an open sheet; cap False leaves the back face out (a part that stands in the body).
    sym adds the mirror image on the other side. bevel chamfers the front rim. relax pairs the triangles again by
    their shape in space (see _relax); it is on for mode 'surf' unless told otherwise."""
    K = set(); P, T = mesh2d(poly, grid, hole, seg, extra, chains, K)
    if relax is None: relax = mode == 'surf'
    V, Fc = [], []
    for sgn in ((1, -1) if sym else (1,)):
        Q = P * np.array([sgn, 1.0]); pts, dirs, miss = _place(S, Q, mode); o = len(V); n = len(Q)
        V += [tuple(p + d * _val(front, p, u, z)) for p, d, (u, z) in zip(pts, dirs, Q)]
        if back is not None: V += [tuple(p + d * _val(back, p, u, z)) for p, d, (u, z) in zip(pts, dirs, Q)]
        # all triangles are wound one way in (u, z), then the whole patch is turned to face outward: winding each
        # by its own look in space goes wrong where the surface leans far over, and leaves walls inside the solid
        tris = [t if (Q[t[1], 0] - Q[t[0], 0]) * (Q[t[2], 1] - Q[t[0], 1]) > (Q[t[2], 0] - Q[t[0], 0]) * (Q[t[1], 1] - Q[t[0], 1])
                else t[::-1] for t in (tuple(t) for t in T)]
        out = 0
        for t in tris:
            a, b, c = (Vector(V[o + i]) for i in t); out += 1 if (b - a).cross(c - a).dot(dirs[t[0]]) > 0 else -1
        if out < 0: tris = [t[::-1] for t in tris]
        if relax: tris = _relax(pts, tris, K)
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
    if back is not None and cap and _loose_edges(ob.data): print(f'  {name}: NOT a closed solid, {_loose_edges(ob.data)} loose edges')
    return ob


STRAY = 0.004      # a face wholly this far outside the old body is a stray (bent faces sit up to 2 mm off their own triangles)


def _loose_edges(me):
    bm = bmesh.new(); bm.from_mesh(me); n = sum(1 for e in bm.edges if len(e.link_faces) != 2); bm.free(); return n


def _outside(tree, q):
    """How far q stands outside the surface in tree; negative inside. Beside an inside corner the nearest point is on
    the corner's edge and one face alone gives the wrong side, so every face that near is asked."""
    loc, nor, i, d = tree.find_nearest(q)
    if d < 1e-6: return 0.0
    n = {j: m for p, m, j, e in tree.find_nearest_range(q, d * 1.02 + 1e-5)}
    return d if (q - loc).dot(sum(n.values(), Vector())) > 0 else -d


def cut(shell, cutters, mat, name='recess'):
    """Cut the cutters out of the shell; the new walls and floors take `mat`.

    What a cut leaves lies on or inside the old body. The exact solver can leave a piece of a cutter's wall standing
    outside it where the body is not one clean closed volume, so anything found outside afterwards is removed, and
    the count of edges not shared by exactly two faces is printed before and after: a clean cut does not raise it."""
    c = join(cutters, name + '_cutter'); c.data.materials.clear(); c.data.materials.append(mat)
    for p in c.data.polygons: p.material_index = 0
    if mat.name not in shell.data.materials: shell.data.materials.append(mat)
    me = shell.data
    old = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])
    n0, e0 = len(me.polygons), _loose_edges(me)
    activate(shell)
    mo = shell.modifiers.new(name, 'BOOLEAN'); mo.operation = 'DIFFERENCE'; mo.object = c; mo.solver = 'EXACT'
    mo.material_mode = 'TRANSFER'
    bpy.ops.object.modifier_apply(modifier=name); bpy.data.objects.remove(c)
    me = shell.data; bm = bmesh.new(); bm.from_mesh(me); out = {}
    for tri in bm.calc_loop_triangles():          # a cut face can be a bent strip round a hole, with its middle
        q = (tri[0].vert.co + tri[1].vert.co + tri[2].vert.co) / 3        # off the surface: judge it by its triangles
        f = tri[0].face; out[f] = min(out.get(f, 1.0), _outside(old, q))
    stray = [f for f, d in out.items() if d > STRAY]
    if stray:
        bmesh.ops.delete(bm, geom=stray, context='FACES'); bm.to_mesh(me); me.update()
    bm.free()
    print(f'  cut {name}: shell faces {n0} -> {len(me.polygons)}, loose edges {e0} -> {_loose_edges(me)}'
          + (f', {len(stray)} stray faces removed' if stray else ''))

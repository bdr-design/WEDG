"""The glass roof of the owner's top photo: one long dark glass panel with a divider across it, set in the roof.

The real LC300 ZX has a small tilt-and-slide moonroof over the front seats. The owner's photo shows a panoramic panel,
and the photo is followed here (a choice for the owner to confirm, see DIMENSIONS.md).

Measured on 04_top.png (v down the image = along the car, u across; the centres of the panel's thin bright outline,
to a tenth of a pixel; one pixel is 2.75 mm along and 3.05 mm across):
  front edge   v 854.8 on the centre line, 855.9 / 856.0 at u 350 / 450, 858.9 / 859.3 at u 300 / 500
  rear edge    v 1444.1 on the centre line, 1443.6 / 1443.5 at u 350 / 450, 1441.8 / 1441.6 at u 300 / 500
  divider      v 1171.2, straight within 0.2 px from u 300 to u 500
  side edges   half the distance between them, by v: 143.50 (920), 143.78 (960), 143.86 (1000, 1040), 143.67 (1080),
               143.55 (1120), 143.39 (1160), 143.08 (1200), 142.59 (1240), 142.17 (1280), 141.50 (1320),
               140.65 (1360), 139.95 (1400); their middle is u 397.0, half a pixel off the car's middle (396.5)
  corners      CORNER_PTS below
  outline      about 3 px wide (8 mm), the divider about 2 px (5 mm)
  windshield header (the bright line where the roof starts)  v 780.4 on the centre line, 785 at u 300 and u 490

The top photo draws the roof further forward than the side photo does: its header is at x +0.578 where the body's
(side photo) is at +0.440, and its rails are 0.2 to 0.3 m further forward, while its antenna is where the side photo
has it (front of the base at x -1.60). So positions along the car are placed by proportion between the header and the
antenna's front; widths are taken as measured."""
import bpy, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import surf as SF, realframe as RF

V0, S_TOP, L_PHOTO = 80.0, 0.002747797, 4.99          # views.json, top view
M_PER_PX_Y = S_TOP * 1.0804876 * 1.026                # across: s * k * TOP_K (the top photo is 1.980 m across its flares)
V_FRONT, BOW_FRONT = 854.8, 4.3                       # front edge on the centre line; how far back it is at |u| 98.5 px (0.30 m)
V_REAR, BOW_REAR = 1444.1, 2.4
V_DIV = 1171.2
U_BOW = 98.5
HALF0, V_HALF0, HALF_DROP, V_HALF_SPAN = 143.86, 1020.0, 3.91, 380.0     # the side edges: a shallow parabola
R_FRONT, R_REAR = 30.7, 26.1                          # corner radii in pixels (fitted to CORNER_PTS, see __main__)
V_HEADER = 780.4
ANT_FRONT = -1.60                                     # the antenna base's front, the same in the side and top photos
GAP, DIV_GAP = 0.007, 0.005                           # the seam round the panel and across it
SEAL_DEPTH, SEAL_W = 0.005, 0.014                     # game choice: the seal's depth below the roof and its width
GLASS_DOWN, GLASS_EDGE = 0.001, 0.002                 # game choice: glass 1 mm under the roof line, a 2 mm rounded edge
# corner points of the outline (|u - 397.0|, v): front, then rear
CORNER_PTS = {'front': [(122.8, 862), (130.6, 866), (135.3, 870), (137.9, 874), (139.9, 878), (141.0, 882), (142.0, 886),
                        (139.0, 875.9), (135.0, 869.7), (131.0, 866.3), (127.0, 863.1), (123.0, 861.8),
                        (140.2, 878), (141.7, 882), (142.7, 886), (143.3, 890)],
              'rear': [(137.8, 1424), (136.0, 1428), (133.1, 1432), (128.7, 1436), (119.9, 1440),
                       (138.0, 1424), (136.5, 1428), (133.5, 1432), (127.9, 1436), (118.9, 1440)]}


def _front(u): return V_FRONT + BOW_FRONT * (u / U_BOW) ** 2
def _rear(u): return V_REAR - BOW_REAR * (u / U_BOW) ** 2
def _half(v): return HALF0 - HALF_DROP * ((v - V_HALF0) / V_HALF_SPAN) ** 2


def _corner(edge, d_edge, r, sgn):
    """The circle of radius r touching an end edge v = edge(u) and the side edge u = _half(v), on the right half.
    sgn +1 for the front corner (the panel is at larger v), -1 for the rear. Returns centre, the two touch points."""
    from scipy.optimize import fsolve
    def pts(p):
        ua, vb = p
        m = d_edge(ua); na = np.array([-m, 1.0]) * sgn / math.hypot(m, 1)            # the end edge's normal, into the panel
        pa = np.array([ua, edge(ua)])
        k = -2 * HALF_DROP * (vb - V_HALF0) / V_HALF_SPAN ** 2; nb = np.array([-1.0, k]) / math.hypot(1, k)
        pb = np.array([_half(vb), vb])
        return pa, na, pb, nb
    def f(p): pa, na, pb, nb = pts(p); return (pa + r * na) - (pb + r * nb)
    sol = fsolve(f, (HALF0 - r, (V_FRONT + r) if sgn > 0 else (V_REAR - r)), xtol=1e-12)
    pa, na, pb, nb = pts(sol); return pa + r * na, pa, pb


def outline_px(n_arc=12, step=12.0):
    """The panel's outline in pixels (u from the panel's middle, v), anticlockwise seen from above with x forward
    and y to the left: front edge from the right corner to the left, down the left side, the rear edge, up the right."""
    cf, fa, fb = _corner(_front, lambda u: 2 * BOW_FRONT * u / U_BOW ** 2, R_FRONT, 1)
    cr, ra, rb = _corner(_rear, lambda u: -2 * BOW_REAR * u / U_BOW ** 2, R_REAR, -1)
    def arc(c, p0, p1, r):
        a0 = math.atan2(*(p0 - c)[::-1]); a1 = math.atan2(*(p1 - c)[::-1]); da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        return [c + r * np.array([math.cos(a0 + da * k / n_arc), math.sin(a0 + da * k / n_arc)]) for k in range(n_arc + 1)]
    # the right half, from the middle of the front edge round to the middle of the rear edge
    n = max(2, int(fa[0] / step)); us = np.linspace(0, fa[0], n + 1)[:-1]
    R = [np.array([u, _front(u)]) for u in us] + arc(cf, fa, fb, R_FRONT)
    n = max(2, int((rb[1] - fb[1]) / step)); R += [np.array([_half(v), v]) for v in np.linspace(fb[1], rb[1], n + 1)[1:-1]]
    R += arc(cr, rb, ra, R_REAR)
    n = max(2, int(ra[0] / step)); R += [np.array([u, _rear(u)]) for u in np.linspace(ra[0], 0, n + 1)[1:]]
    R = np.array(R)                                    # u >= 0: the car's right side is image right in a top view with the nose up
    Lh = R[-2:0:-1] * np.array([-1.0, 1.0])            # the mirrored half, back up to the front
    return np.vstack([R, Lh])


def x_top(v):
    """The top photo's own mapping (views.json), then the photo frame's length warp."""
    return float(RF.x_real(L_PHOTO / 2 - (v - V0) * S_TOP))


def _c2(a, b): return a[0] * b[1] - a[1] * b[0]


def _offset(P, d):
    """A closed anticlockwise polyline moved inward by d (to the left of its direction)."""
    t = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    return P + d * np.c_[-t[:, 1], t[:, 0]]


def _clip(P, x0, keep_front):
    """Cut a closed polyline by the line x = x0 and keep the part ahead of it (or behind it)."""
    out = []; n = len(P); s = 1.0 if keep_front else -1.0
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]; da, db = s * (a[0] - x0), s * (b[0] - x0)
        if da >= 0: out.append(a)
        if (da > 0) != (db > 0) and da != db: out.append(a + (b - a) * da / (da - db))
    return np.array(out)


def _loop(T):
    """The boundary of a triangle set as one ordered ring of vertex numbers, in the triangles' own direction."""
    E = {(t[i], t[(i + 1) % 3]) for t in T for i in range(3)}
    nxt = {a: b for a, b in E if (b, a) not in E}
    start = next(iter(nxt)); ring = [start]
    while nxt[ring[-1]] != start: ring.append(nxt[ring[-1]])
    assert len(ring) == len(nxt), 'the pane outline is not one ring'
    return ring


def _mesh(name, V, F, mat, sharp=35.0):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(sharp))
    return ob


def header_x(bvh):
    """Where the body's roof ends at the windshield, on the centre line."""
    lo, hi = 0.0, 1.2
    for _ in range(40):
        m = (lo + hi) / 2; h = bvh.ray_cast(Vector((m, 0.0, 3.0)), Vector((0, 0, -1)))
        if h[0] is not None and h[0].z > 1.5: lo = m
        else: hi = m
    return lo


def glass_roof(shell, glass_mat, seal_mat):
    """Cut the opening in the shell (real frame) and set the two panes and their seal in it."""
    me = shell.data
    bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])
    def zr(x, y):
        h = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)))
        if h[0] is None or h[0].z < 1.5: raise ValueError(f'no roof at x {x:.3f}, y {y:.3f}')
        return h[0].z
    xh = header_x(bvh); kx = (xh - ANT_FRONT) / (x_top(V_HEADER) - ANT_FRONT)
    X = lambda v: ANT_FRONT + (x_top(v) - ANT_FRONT) * kx
    px = outline_px()
    A = np.array([(X(v), -u * M_PER_PX_Y) for u, v in px])          # image right is the car's right side: y negative
    if (A[:, 0] * np.roll(A[:, 1], -1) - np.roll(A[:, 0], -1) * A[:, 1]).sum() < 0: A = A[::-1]
    xd = X(V_DIV)
    info = dict(header=xh, front=X(V_FRONT), divider=xd, rear=X(V_REAR), half_max=HALF0 * M_PER_PX_Y,
                half_rear=float(np.abs(A[A[:, 0] < X(V_REAR) + 0.12][:, 1]).max()))

    # the seal: a wall down from the opening's edge and a floor under the seam, and a strip under the divider
    n = len(A); B = _offset(A, SEAL_W)
    V = [(x, y, zr(x, y)) for x, y in A] + [(x, y, zr(x, y) - SEAL_DEPTH) for x, y in A] + [(x, y, zr(x, y) - SEAL_DEPTH) for x, y in B]
    F = []
    for i in range(n):
        j = (i + 1) % n; F += [[i, j, n + j, n + i], [n + i, n + j, 2 * n + j, 2 * n + i]]
    hy = float(np.abs(B[np.argsort(np.abs(B[:, 0] - xd))[:4]][:, 1]).min())
    ys = np.linspace(-hy, hy, 21); o = len(V)
    for y in ys: V += [(xd - 0.010, y, zr(xd - 0.010, y) - SEAL_DEPTH), (xd + 0.010, y, zr(xd + 0.010, y) - SEAL_DEPTH)]
    for i in range(len(ys) - 1): a = o + 2 * i; F.append([a, a + 1, a + 3, a + 2])      # facing up: it is seen from above, through the gap
    seal = _mesh('roof_glass_seal', V, F, seal_mat)

    # the panes: the top face, a rounded edge and a skirt down to the seal
    inner = _offset(A, GAP + GLASS_EDGE); panes = []
    for nm, poly in (('front', _clip(inner, xd + DIV_GAP / 2 + GLASS_EDGE, True)), ('rear', _clip(inner, xd - DIV_GAP / 2 - GLASS_EDGE, False))):
        P, T = SF.mesh2d(poly, 0.065, seg=0.03)
        T = [list(t) if _c2(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]]) > 0 else list(t)[::-1] for t in T]
        ring = _loop(T); R = P[ring]; O = _offset(R, -GLASS_EDGE)
        V = [(x, y, zr(x, y) - GLASS_DOWN) for x, y in P]; m = len(V); k = len(ring)
        V += [(x, y, zr(x, y) - GLASS_DOWN - GLASS_EDGE) for x, y in O] + [(x, y, zr(x, y) - SEAL_DEPTH) for x, y in O]
        F = [list(t) for t in T]
        for i in range(k):
            j = (i + 1) % k; a, b = ring[i], ring[j]
            F += [[a, m + i, m + j, b], [m + i, m + k + i, m + k + j, m + j]]
        panes.append(_mesh('roof_glass_' + nm, V, F, glass_mat, sharp=60.0))
    glass = SF.join(panes, 'roof_glass')

    # the opening: an exact cut straight down through the roof; the cut's own walls and floor are thrown away
    lo, hi = min(zr(x, y) for x, y in A) - 0.10, max(zr(x, y) for x, y in A) + 0.10
    cv = [(x, y, hi) for x, y in A] + [(x, y, lo) for x, y in A]
    cf = [list(range(n)), list(range(2 * n - 1, n - 1, -1))] + [[i, n + i, n + (i + 1) % n, (i + 1) % n] for i in range(n)]
    cme = bpy.data.meshes.new('roof_cut'); cme.from_pydata(cv, [], cf); cme.update()
    cutter = bpy.data.objects.new('roof_cut', cme); bpy.context.collection.objects.link(cutter)
    mark = bpy.data.materials.new('_roof_cut'); SF.cut(shell, [cutter], mark, 'roof_opening')
    import bmesh
    mi = shell.data.materials.find(mark.name)
    bm = bmesh.new(); bm.from_mesh(shell.data)
    dead = [f for f in bm.faces if f.material_index == mi]; info['cut_faces_removed'] = len(dead)
    bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(shell.data); bm.free()
    shell.data.materials.pop(index=mi); bpy.data.materials.remove(mark)
    # check: nothing of the shell is left inside the opening
    left = sum(1 for p in shell.data.polygons if p.center.z > lo and SF.inside(A, np.array([[p.center.x, p.center.y]]))[0])
    info['shell_faces_left_inside'] = left
    print('  glass roof:', ', '.join(f'{k} {v:.4f}' if isinstance(v, float) else f'{k} {v}' for k, v in info.items()))
    return glass, seal, info


if __name__ == '__main__':
    # fit the corner radii to the measured corner points, and print the outline's key numbers
    for nm, edge, d, sgn in (('front', _front, lambda u: 2 * BOW_FRONT * u / U_BOW ** 2, 1), ('rear', _rear, lambda u: -2 * BOW_REAR * u / U_BOW ** 2, -1)):
        pts = np.array(CORNER_PTS[nm], float); best = None
        for r in np.arange(20.0, 45.01, 0.1):
            c, pa, pb = _corner(edge, d, r, sgn)
            # only the points on the arc itself (between the two touch points)
            on = (pts[:, 0] > pa[0]) & ((pts[:, 1] < pb[1]) if sgn > 0 else (pts[:, 1] > pb[1]))
            if on.sum() < 5: continue
            e = np.hypot(*(pts[on] - c).T) - r; rms = float(np.sqrt((e ** 2).mean()))
            if best is None or rms < best[1]: best = (r, rms, int(on.sum()), pa, pb)
        print(f'{nm} corner: best radius {best[0]:.1f} px, rms {best[1]:.2f} px over {best[2]} points; touches the end edge at u {best[3][0]:.1f}, the side at v {best[4][1]:.1f}')
    P = outline_px(); print('outline points', len(P), 'u', P[:, 0].min(), P[:, 0].max(), 'v', P[:, 1].min(), P[:, 1].max())
    for v in (V_HEADER, V_FRONT, V_DIV, V_REAR): print('v %.1f -> top photo x %.4f' % (v, x_top(v)))
    print('half width max %.4f m, at v 1400 %.4f m' % (HALF0 * M_PER_PX_Y, _half(1400) * M_PER_PX_Y))

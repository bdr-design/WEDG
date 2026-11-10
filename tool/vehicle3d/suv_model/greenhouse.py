"""Step 2: the greenhouse. The window outline (measured on the side, front and rear photos, as in suv_complete.py) is
cut into the shell as planes; the glass is lifted out as its own panes, set 8 mm in, with a black lip back to the
opening; the B and C pillars are gloss black; a black surround frames each opening; chrome strips run along the
foot and the head of the side windows."""
import bpy, bmesh, math, os, sys, numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import body as _B

XF = 2.498; K = 1.034
def interp(t, d): ds, vs = zip(*t); return float(np.interp(d, ds, vs))
TOP = [(0.0, 1.13), (0.40, 1.215), (1.00, 1.245), (1.46, 1.26), (2.00, 1.27), (3.50, 1.285), (4.40, 1.30), (4.90, 1.30)]
belt = lambda d: interp(TOP, d) * K
# The belt: the chrome line under the side glass on 01_left (its brightest row): z 1.336 at d 2.30, 1.356 at 3.10,
# 1.371 at 3.50, 1.380 at 3.80 (d metres behind the nose, photo frame), a straight line within 2 mm. Up to r19 the
# belt was 2 to 4.5 cm lower and rose half as fast. Behind d 3.88 the line kicks up under the quarter glass: 1.389 at
# d 3.90, 1.409 at 4.00, 1.436 at 4.10, 1.462 at 4.20, 1.498 at 4.30, 1.518 at 4.33, where the glass ends (Q below, one
# straight cut from the belt at d 3.88 to that corner: up to 13 mm over the photo's curve in the middle).
BELT = (2.298, 1.336, 0.0293)
def bplane(d): return BELT[1] + (d - BELT[0]) * BELT[2]
Q_D = (3.878, 4.328)                    # the kick-up's foot on the belt, and the quarter glass's rear edge
Q_TOP = 1.518
def zlow(d): return max(bplane(d), bplane(Q_D[0]) + (d - Q_D[0]) / (Q_D[1] - Q_D[0]) * (Q_TOP - bplane(Q_D[0])))
ZTOP, ZDOOR = 1.79 * K, 1.835 * K
ZWS0, ZWS1 = 1.405 * K, 1.81 * K
# The rear window, measured row by row on the rear photo (rearwork/seal.py, colrun.py; y on the front photo's scale):
# the glass's foot at z 1.401 over a 6 mm dark seal, its side edge leaning in and curving (half-width 0.7397 at the
# foot, 0.7241 at 1.52, 0.7009 at 1.64, 0.6718 at 1.76; both sides agree within 2 mm), the same 6 mm seal outside it,
# then painted pillar. The glass runs up to the corner of the notch under the roof spoiler (body.notch_corner), and
# from z 1.774 up it is black (the band the photo shows under the spoiler, 1.774 ... 1.865 with the underside).
ZRG0, ZFRIT, RG_SEAL = 1.401, 1.774, 0.006
ZRG_C = _B.notch_corner(); ZRG1 = ZRG_C - 0.004      # the glass stops 4 mm short of the corner (a top seal)
RG_EDGE = [(ZRG0, 0.7397), (1.52, 0.7241), (1.64, 0.7009), (1.76, 0.6718), (ZRG_C, 0.656)]
RG_UNDER = _B.NOTCH_Z[3] + 0.012               # the spoiler's underside and the tip's lower edge end below this
def rg_half(z): return interp(RG_EDGE, min(max(z, ZRG0), ZRG_C))
# The windshield's half-width by height (z / K, y / K). On 02_front the glass ends at a dark line 1 cm wide (the gap to
# the A pillar), the same on both sides: 0.75 m out at z 1.50, 0.73 at 1.58, 0.71 at 1.66, 0.69 at 1.74, 0.66 at 1.82
# (photo frame). The pane runs to 5 mm short of that line and the surround beside it is WS_SUR wide. (Up to r15 the
# pane was 4 to 7 cm narrower: 0.682 at 1.50 and 0.617 at 1.82.)
WS_SUR = 0.012
def ws_half(z): return interp([(1.405, 0.733), (1.60, 0.684), (1.81, 0.625)], z / K) * K
def line_plane(p0, p1):
    p0, p1 = Vector(p0), Vector(p1); return p0, (p1 - p0).cross(Vector((0, 1, 0))).normalized()
A_CO, A_NO = line_plane((XF - 1.55, 0, 1.27 * K), (XF - 2.39, 0, 1.86 * K))
Q_CO, Q_NO = line_plane((XF - Q_D[0], 0, bplane(Q_D[0])), (XF - Q_D[1], 0, Q_TOP))
def plane_sign(co, no, ref):
    sg = 1 if (Vector(ref) - co).dot(no) > 0 else -1
    return lambda p: (Vector(p) - co).dot(no) * sg
behind_A = plane_sign(A_CO, A_NO, (XF - 2.6, 0, 1.6 * K))
above_Q = plane_sign(Q_CO, Q_NO, (XF - 4.0, 0, 1.6 * K))
B_PILLAR, C_PILLAR = (2.70, 2.80), (3.66, 3.74)
SURROUND = 0.03                        # the black surround's width
BL0, BL1 = Vector((XF - 1.5, 0, bplane(1.5))), Vector((XF - 4.4, 0, bplane(4.4)))       # the belt line
NB = (BL1 - BL0).cross(Vector((0, 1, 0))).normalized(); NB = NB if NB.z > 0 else -NB
def _out(co, no, ref): return co - no * (SURROUND if (Vector(ref) - co).dot(no) > 0 else -SURROUND)
A_OUT, Q_OUT = _out(A_CO, A_NO, (XF - 2.6, 0, 1.6 * K)), _out(Q_CO, Q_NO, (XF - 4.0, 0, 1.6 * K))
# The belt and the A pillar's edge meet at 35 degrees, and a band 3 cm outside both would run 9 cm past the glass's
# corner to a point. It is cut off square to the corner, 1.3 widths out.
def _a_foot():
    da, db = (A_OUT - A_CO), BL1 - BL0; ua = Vector((-A_NO.z, 0, A_NO.x))          # along the A edge
    t = ((BL0.x - A_CO.x) * db.z - (BL0.z - A_CO.z) * db.x) / (ua.x * db.z - ua.z * db.x); p = A_CO + ua * t
    b = -(NB + (A_CO - A_OUT).normalized()).normalized(); return p, b
A_FOOT, A_BEV = _a_foot()

def cut_outline(bm):
    def geom_of(fs): return fs + list({e for f in fs for e in f.edges}) + list({v for f in fs for v in f.verts})
    def faces(test): return [f for f in bm.faces if test(f.calc_center_median(), XF - f.calc_center_median().x)]
    def bis(g, co, no):
        bmesh.ops.bisect_plane(bm, geom=g, plane_co=co, plane_no=no, dist=1e-6)
    side = lambda lo, hi: geom_of(faces(lambda c, d: abs(c.y) > 0.45 and c.z > 1.0 * K and lo < d < hi))
    bis(side(1.3, 4.6), BL0, NB); bis(side(1.3, 4.6), BL0 - NB * SURROUND, NB)      # the belt, and the surround's edge under it
    for zc in (ZTOP, ZTOP + SURROUND, ZDOOR): bis(side(1.4, 4.75), (0, 0, zc), (0, 0, 1))
    bis(side(1.3, 2.8), A_CO, A_NO); bis(side(1.3, 2.8), A_OUT, A_NO)      # the pane's edge, and the surround's
    bis(side(1.3, 2.0), A_FOOT + A_BEV * 1.3 * SURROUND, A_BEV)
    for dc in (*B_PILLAR, *C_PILLAR, Q_D[1], Q_D[1] + SURROUND, 1.565, 2.735, 2.775, 3.715): bis(side(dc - 0.6, dc + 0.6), (XF - dc, 0, 0), (1, 0, 0))
    bis(side(3.9, 4.75), Q_CO, Q_NO); bis(side(3.9, 4.75), Q_OUT, Q_NO)
    # The windshield's side edge leans, with a knee at z 1.60 K (ws_half): one plane per band of height, and the
    # surround's edge 3 cm outside each. (One plane from foot to head cut the chord across the knee, and the faces
    # between chord and knee were taken whole: a pane edge 2 to 3 cm out of line, in steps.)
    ws = lambda z0=1.2 * K, z1=9.0: geom_of(faces(lambda c, d: d < 2.6 and z0 < c.z < z1))
    zk = 1.60 * K
    for zc in (ZWS0, zk, ZWS1): bis(ws(), (0, 0, zc), (0, 0, 1))
    for za, zb in ((ZWS0, zk), (zk, ZWS1)):
        for s in (1, -1):
            p0 = Vector((0, s * ws_half(za), za)); p1 = Vector((0, s * ws_half(zb), zb)); n = (p1 - p0).cross(Vector((1, 0, 0))).normalized()
            bis(ws(za, zb), p0, n); bis(ws(za, zb), p0 + Vector((0, s * WS_SUR, 0)), n)
    rg = lambda z0=1.1 * K, z1=9.0: geom_of(faces(lambda c, d: d > 4.4 and z0 < c.z < z1))
    for zc in (ZRG0 - RG_SEAL, ZRG0, *[z for z, _ in RG_EDGE[1:-1]], ZFRIT, ZRG1): bis(rg(), (0, 0, zc), (0, 0, 1))
    # the leaning side edge, one plane per band of height, and the seal's outer edge 6 mm outside it; the lowest band
    # takes the seal under the foot, the highest carries the edge on across the spoiler's underside
    last = len(RG_EDGE) - 2
    for i, ((za, ya), (zb, yb)) in enumerate(zip(RG_EDGE, RG_EDGE[1:])):
        lo = za - RG_SEAL if i == 0 else za; hi = RG_UNDER if i == last else zb
        for s in (1, -1):
            for off in (0.0, RG_SEAL):
                p0 = Vector((0, s * (ya + off), za)); p1 = Vector((0, s * (yb + off), zb))
                bis(rg(lo, hi), p0, (p1 - p0).cross(Vector((1, 0, 0))).normalized())
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])

def kind(c, n):
    d = XF - c.x; ay = abs(c.y); E = 1e-4
    if 1.47 < d < 2.5 and n.x > -0.2 and ZWS0 + E < c.z < ZWS1 - E and ay < ws_half(c.z) - E: return 'glass'
    if d > 4.5 and n.x < 0.2:
        if ZRG0 + E < c.z < ZRG1 - E and ay < rg_half(c.z) - E: return 'glass'
        if ay < rg_half(c.z) + RG_SEAL - E:
            if ZRG0 - RG_SEAL + E < c.z < ZRG_C + E: return 'seal'
            if ZRG_C - E < c.z < RG_UNDER and n.z < -0.3: return 'seal'      # the spoiler's underside
    if ws_half(c.z) + 0.03 < ay < 0.95 and 1.4 < d < 4.5 and bplane(d) + E < c.z < ZTOP - E and behind_A(c) > E and d < Q_D[1] - E and above_Q(c) > E:
        if B_PILLAR[0] - E <= d <= B_PILLAR[1] + E or C_PILLAR[0] - E <= d <= C_PILLAR[1] + E: return 'pillar'
        return 'glass'
    return None

def build(shell, glass_mat, black_gloss, trim, chrome):
    me = shell.data
    for m in (glass_mat, black_gloss, trim): me.materials.append(m)
    gi, pi, ti = len(me.materials) - 3, len(me.materials) - 2, len(me.materials) - 1
    bm = bmesh.new(); bm.from_mesh(me); cut_outline(bm)
    glass_faces = []
    for f in bm.faces:
        k = kind(f.calc_center_median(), f.normal)
        if k == 'glass': f.material_index = gi; glass_faces.append(f)
        elif k == 'pillar': f.material_index = pi
        elif k == 'seal': f.material_index = ti
    # A black surround, 3 cm wide. Round the side glass it is the band between the pane's five edges and the same five
    # set 3 cm out, all of them cut into the shell (cut_outline): taking whole faces near an edge instead left a
    # staircase wherever the edge leans across the shell's rows. The windshield's leaning side edges are done the same
    # way; above and below it the surround is still the faces within 3 cm of the glass's edge, which run along the
    # shell's rows. The rear window has its own measured seal.
    def side_out(c):
        """How far outside the side glass's outline the point is, the farthest of its five edges; negative inside."""
        return -min((c - BL0).dot(NB), ZTOP - c.z, behind_A(c), c.x - (XF - Q_D[1]), above_Q(c))
    gverts = {v for f in glass_faces for v in f.verts}
    edge_v = [v for v in gverts if any(f.material_index != gi for f in v.link_faces)]
    from mathutils.kdtree import KDTree
    kd = KDTree(len(edge_v))
    for i, v in enumerate(edge_v): kd.insert(v.co, i)
    kd.balance()
    for f in bm.faces:
        if f.material_index != 0: continue
        c = f.calc_center_median(); d = XF - c.x
        if abs(c.y) > 0.45 and abs(f.normal.y) > 0.6 and 1.3 < d < 4.6 and c.z > 1.0 * K:      # the body side
            if 0 < side_out(c) < SURROUND and (c - A_FOOT).dot(A_BEV) < 1.3 * SURROUND: f.material_index = ti
        elif edge_v and d < 2.7:      # round the windshield: a band beside its leaning side edges, whole faces above and below
            out = abs(c.y) - ws_half(c.z)
            if (0 < out < WS_SUR) if ZWS0 < c.z < ZWS1 and out > 0 else kd.find(c)[2] < SURROUND: f.material_index = ti
    bm.to_mesh(me); bm.free()
    # lift the glass out into its own object and set it 8 mm in, with a lip back to the opening
    for o in bpy.context.selected_objects: o.select_set(False)
    shell.select_set(True); bpy.context.view_layer.objects.active = shell
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons: p.select = p.material_index == gi
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    glass = [o for o in bpy.context.selected_objects if o is not shell][0]; glass.name = 'glass'
    bm = bmesh.new(); bm.from_mesh(glass.data); bm.normal_update()
    edges = [e for e in bm.edges if e.is_boundary]
    ret = bmesh.ops.extrude_edge_only(bm, edges=edges)
    lip_verts = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
    lip_faces = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
    # move the original pane in; the extruded copies stay at the opening, so the lip spans the 8 mm
    lipset = set(lip_verts)
    for v in bm.verts:
        if v not in lipset: v.co -= v.normal * 0.008
    for f in lip_faces: f.material_index = glass.data.materials.find(trim.name) if trim.name in glass.data.materials else 0
    bm.to_mesh(glass.data); bm.free()
    if trim.name not in glass.data.materials: glass.data.materials.append(trim)
    ti_g = glass.data.materials.find(trim.name)
    # the black band across the top of the rear glass
    glass.data.materials.append(black_gloss); bi = len(glass.data.materials) - 1; gi_g = glass.data.materials.find(glass_mat.name)
    for p in glass.data.polygons:
        if p.material_index == gi_g and XF - p.center.x > 4.5 and p.center.z > ZFRIT and p.normal.x < -0.3: p.material_index = bi
    # chrome strips along the foot and the head of the side windows
    strips = []
    for s in (1, -1):
        for nm, zf, d0, d1 in (('low', lambda d: zlow(d) - 0.004, 1.62, Q_D[1]), ('top', lambda d: ZTOP + 0.012, 2.40, Q_D[1] + 0.03)):
            V, F = [], []
            ds = np.linspace(d0, d1, 60)
            for d in ds:
                z = zf(d)
                hit = shell.ray_cast(Vector((XF - d, s * 1.5, z)), Vector((0, -s, 0)))
                y = hit[1].y + s * 0.004 if hit[0] else s * 0.94
                V += [(XF - d, y, z - 0.006), (XF - d, y + s * 0.006, z), (XF - d, y, z + 0.006)]
            # a closed three-sided bar, wound to look outward on the right side and turned over for the left
            for i in range(len(ds) - 1):
                a = 3 * i; F += [[a, a + 1, a + 4, a + 3], [a + 1, a + 2, a + 5, a + 4], [a + 2, a, a + 3, a + 5]]
            n = 3 * (len(ds) - 1); F += [[0, 2, 1], [n, n + 1, n + 2]]
            if s > 0: F = [f[::-1] for f in F]
            name = f"window_chrome_{nm}_{'L' if s > 0 else 'R'}"
            mesh = bpy.data.meshes.new(name); mesh.from_pydata(V, [], F); mesh.update()
            o = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(o); mesh.materials.append(chrome)
            for p in mesh.polygons: p.use_smooth = True
            mesh.set_sharp_from_angle(angle=math.radians(40))
            strips.append(o)
    return glass, strips

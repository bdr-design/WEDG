"""A front seat in three dimensions, from seat_side.png read through its own camera (seatcam.py).
The first pass (seat.py) took the photo as square-on and gave each region a width; the photo is a perspective one
from above the cushion, so that seat's cushion stood 9 cm too high. Here the lines of the photo that lie on the
seat's near side (the piping along the cushion's edge, the base's outline, the backrest's side panel) are laid on
upright planes at their own distance across the seat, and the cushion and the backrest are lofted from them.
The seat faces +x; the photo's side is -y, the seat's right: the photo is of a right-hand seat (its controls are on
its right). build(mirror=True) gives the left one.
Across the seat nothing is measured (none of the six photos shows a front seat from the front): the widths, the
bolsters' height and the edges' rounding in SHAPE are a CHOICE."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seatcam as SC, seat_measure as SM, seat_features as F, relief as R, imats

SHAPE = dict(cushion_w=0.550, back_w=0.530, head_w=0.285, base_w=0.560,
             bolster=0.045,            # how far the cushion's and backrest's side bolsters stand over the seating surface
             bolster_in=(0.145, 0.218),   # across the seat: where a bolster starts to rise, and where it is at full height
             edge=0.045,               # the rounding of the cushion's and backrest's outer edges
             post_y=0.090, post_d=0.013, rail_y=0.200, rail_w=0.045)
# lines read on the photo, (col, row), each lying at one distance across the seat (y)
PIPING = [(499, 915), (676, 891), (852, 874), (941, 879), (1002, 903)]            # the cushion's near edge piping (y -0.24): the near bolster's top
CUSHION_FOOT = [(441, 891), (499, 929), (547, 950), (617, 962), (735, 959), (852, 953), (941, 950), (1003, 953)]      # where the cushion meets the base, near side (y -0.255)
BACK_BOLSTER = [(540, 860), (519, 816), (508, 743), (477, 648), (419, 564), (387, 500), (350, 395), (319, 322)]       # the backrest's near bolster: the seam between its side and its face (y -0.21), foot to top
BUCKLE = ((607, 776), (672, 732), 24)      # the buckle on the photo: its axis from where it leaves the cushion to its end, and its breadth (px)
FADE = (800, 920)             # the photo's columns between which the cushion's upper outline passes from the far bolster to the cushion's middle
BOW = 0.05                    # how far the nose's corners stand behind its middle, in plan
NOSE = (0.055, 0.50)
# the photo's lines drawn on the seat as seams (seat_side.png, read off its enlargements to about 3 px): each is sent
# through the photo's camera onto the built surface and repeated on the seat's other side
SEAMS = [PIPING, [(x, y + 9) for x, y in PIPING],                                   # the cushion's piping and the stitched line under it
         BACK_BOLSTER,                                                               # the seam between the backrest's side and its face
         [(179, 342), (200, 418), (239, 489), (282, 553), (318, 647), (350, 747), (355, 853)],      # the side panel's rear seam
         [(282, 552), (340, 548), (397, 546)],                                       # the seam across the side panel
         [(916, 886), (925, 909), (998, 950)]]                                       # the nose's side seam, past the piping's end
# (the seating panel's own seams are not drawn yet: on the dished top their hits and their mirror images cross)
TOP_R = 0.035                 # the backrest's top: the height of its rounding
BACK_FRONT = [(540, 795), (572, 753), (582, 679), (561, 606), (508, 500), (435, 390), (372, 316)]       # the backrest's outline on the photo's right: the far bolster's crest (y +0.19), foot to top


def _line(pts, y):
    """A photo line laid on the plane at y: (x, z) points."""
    p = np.asarray(pts, float); x, z = SC.on_plane(y)(p[:, 1], p[:, 0]); return x, z


def _sstep(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def _loft(bm, stations, mat, closed=True, caps=True):
    """Stations are rings of points (the same number in each); quads join each ring to the next."""
    rings = [[bm.verts.new(p) for p in st] for st in stations]; n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for k in range(n if closed else n - 1):
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])); f.material_index = mat; f.smooth = True
    if caps:
        for r in (rings[0], rings[-1]):
            f = bm.faces.new(r); f.material_index = mat; f.smooth = True
    return rings


def _section(half_w, top, bottom, n=13, foot=0.012):
    """A cushion-like section across the seat: points (y, height) round it. top(|y|) is the upper surface's height
    over the section's own datum; the outer edges are rounded by SHAPE['edge']; bottom is the lower surface's height."""
    e = SHAPE['edge']; ys = np.linspace(-half_w + e, half_w - e, n); up = [(y, top(abs(y))) for y in ys]
    arc = [(half_w - e + e * math.sin(a), top(half_w - e) - e * (1 - math.cos(a))) for a in np.linspace(0.3, math.pi / 2, 4)]
    right = arc + [(half_w, bottom + foot), (half_w - foot * 0.3, bottom + foot * 0.3), (half_w - foot, bottom)]; left = [(-y, h) for y, h in right][::-1]
    return left + up + right          # from the left foot, over the top, to the right foot (open underneath; the loft closes it)


def _block(bm, pts, y0, y1, mat):
    """A closed prism across the seat: pts are (x, z), its faces at y0 and y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in pts]; b = [bm.verts.new((x, y1, z)) for x, z in pts]; n = len(pts)
    for f in [bm.faces.new(a), bm.faces.new(b[::-1])] + [bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n])) for k in range(n)]: f.material_index = mat; f.smooth = False


def _skew(mask, y_near, y_far):
    """For a rounded body, whose photo region is its silhouette: of two opposite edges, the one further from the
    camera's axis is drawn by the body's near side and the other by its far side (both by the near side when the
    region straddles the axis). (row, column) -> (x, z) with the depth running between them across the region."""
    r, c = np.where(mask); c0, c1, r0, r1 = c.min(), c.max(), r.min(), r.max()
    def depth(v, lo, hi, axis):
        if lo < axis < hi: return np.full(v.shape, float(y_near))
        outer, inner = (lo, hi) if hi <= axis else (hi, lo)
        return y_near + (y_far - y_near) * np.clip((v - outer) / (inner - outer), 0, 1)
    def f(rr, cc):
        rr = np.atleast_1d(np.asarray(rr, float)); cc = np.atleast_1d(np.asarray(cc, float)); d = SC._ray(rr, cc)
        tx = (depth(cc, c0, c1, SC.COL0) - SC.POS[1]) / d[:, 1]; tz = (depth(rr, r0, r1, SC.ROW_H) - SC.POS[1]) / d[:, 1]
        return SC.POS[0] + tx * d[:, 0], SC.POS[2] + tz * d[:, 2]
    return f


def _seams(bm, lines, mat, width=0.003, lift=0.0012, both=True, step=10.0):
    """Lines of the photo ((col, row) points) drawn on the built seat: each point is sent through the photo's camera
    onto the surface it meets first, and a narrow band is laid along the hits, standing just off the surface. With
    both, the band is repeated on the seat's other side."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromBMesh(bm); src = Vector(SC.POS)
    for line in lines:
        p = np.asarray(line, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; t = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
        rays = SC._ray(np.interp(t, d, p[:, 1]), np.interp(t, d, p[:, 0])); hits = []
        for r in rays:
            h = tree.ray_cast(src, Vector(r).normalized())
            if h[0] is not None: hits.append((np.array(h[0]), np.array(h[1])))
        if len(hits) < 2: continue
        P = np.array([h[0] for h in hits]); N = np.array([h[1] for h in hits]); N[(N * (np.array(SC.POS) - P)).sum(1) < 0] *= -1; T = np.gradient(P, axis=0); S = np.cross(N, T); S /= np.linalg.norm(S, axis=1)[:, None] + 1e-12
        for sgn in ((1, -1) if both else (1,)):
            m = np.array((1, sgn, 1.0)); a = [bm.verts.new(tuple((P[i] + N[i] * lift + S[i] * width / 2) * m)) for i in range(len(P))]; b = [bm.verts.new(tuple((P[i] + N[i] * lift - S[i] * width / 2) * m)) for i in range(len(P))]
            for i in range(len(P) - 1):
                if np.linalg.norm(P[i + 1] - P[i]) > 0.06: continue          # (a jump from one surface to another: no band across it)
                f = bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]) if sgn > 0 else (b[i], b[i + 1], a[i + 1], a[i])); f.material_index = mat; f.smooth = True


def risers(ob, h):
    """Blocks under the rails' feet, h tall (the brackets that stand a seat on the floor's mounts)."""
    if h < 0.002: return
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me); V = np.array([v.co for v in bm.verts]); z0 = V[:, 2].min()
    low = V[V[:, 2] < z0 + 0.01]; idx = list(me.materials).index(bpy.data.materials['cabin_black']) if 'cabin_black' in bpy.data.materials else 0
    for sy in (-1, 1):
        q = low[np.sign(low[:, 1]) == sy]
        if not len(q): continue
        for xc in (q[:, 0].min() + 0.04, q[:, 0].max() - 0.04):
            yc = float(np.median(q[:, 1])); vs = [bm.verts.new((xc + dx, yc + dy, z)) for z in (z0 - h + 0.001, z0 + 0.002) for dx, dy in ((-0.03, -0.022), (0.03, -0.022), (0.03, 0.022), (-0.03, 0.022))]
            for k in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                f = bm.faces.new([vs[i] for i in k]); f.material_index = idx; f.smooth = False
    bm.to_mesh(me); bm.free()


def hpoint(ob):
    """The seat's H-point in its own frame (x, z), estimated on the built seat's middle plane: 135 mm ahead of the
    backrest's front face and 25 mm over the cushion's (uncompressed) top there; the SAE J826 manikin's hip joint
    sits about so (its 97 mm over the cushion it presses down about 70)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me); t = BVHTree.FromBMesh(bm); bm.free()
    top = lambda x: t.ray_cast(Vector((x, 0.0, 1.5)), Vector((0, 0, -1)))[0].z           # the cushion's top on the middle plane
    x0 = 0.45
    z = top(x0) + 0.06
    for _ in range(8):           # the backrest's front, by a ray back from over the cushion's middle; then the cushion's top there
        hb = t.ray_cast(Vector((x0, 0.0, z)), Vector((-1, 0, 0))); x = hb[0].x + 0.135; z = top(x) + 0.025
    return x, z


def build(name='seat_front', mirror=False):
    S = SHAPE; M = {k: imats.m(v) for k, v in (('leather', 'seat_leather'), ('plastic', 'cabin_beige'), ('black', 'cabin_black'), ('chrome', 'cabin_chrome'), ('red', 'cabin_red'), ('seam', 'seat_seam'))}
    idx = {k: i for i, k in enumerate(M)}; bm = bmesh.new(); lay = bm.verts.layers.float_vector.new('relief_n')
    lab = SM.labels(); mpp = SC.DIST / SC.F
    # --- the cushion: sections across the seat, from its rear (under the backrest) to its nose ---------------------------
    px, pz = _line(PIPING, -0.24); fx, fz = _line(CUSHION_FOOT, -S['cushion_w'] / 2); ye = S['cushion_w'] / 2 - S['edge']
    # the cushion's upper outline on the photo: behind FADE's first column it is the FAR bolster's crest, which with the near
    # piping gives the bolsters' height (the two agree within 2 cm; their mean is used); ahead of its second it is the
    # cushion's middle, where the perforated panel runs over the nose (the bolsters fade out there and the piping turns down)
    cush = lab == SM.PARTS.index('cushion'); nose_col = int(np.where(cush.any(0))[0].max()); nose_row = float(np.where(cush[:, nose_col])[0].mean())
    cols = np.arange(700, nose_col - 12, 8); top_row = np.array([np.where(cush[:, c])[0].min() for c in cols], float); bf = 1 - _sstep((cols - FADE[0]) / (FADE[1] - FADE[0]))
    q = np.array([[v[0] for v in SC.on_plane(ye * f)(np.array([r]), np.array([float(c)]))] for r, c, f in zip(top_row, cols, bf)]); o = np.argsort(q[:, 0]); qx, qz, bf = q[o, 0], q[o, 1], bf[o]
    # the nose is bowed in plan (BOW, a choice): its foremost point is the one whose outline is the photo's right end
    bow = lambda y, hw: BOW * (np.abs(y) / hw) ** 2; yy = np.linspace(-ye, ye, 41)
    x1 = float(min(SC.on_plane(y)(np.array([nose_row]), np.array([float(nose_col)]))[0][0] + bow(y, S['cushion_w'] / 2) for y in yy))
    x0 = float(fx.min()) - 0.02; xs = np.r_[np.linspace(x0, x1 - NOSE[0], 16), x1 - NOSE[0] + NOSE[0] * np.sin(np.linspace(0, 1, 11)[1:] * math.pi / 2)]; b0, b1 = S['bolster_in']
    stations = []
    for i, x in enumerate(xs):
        z_out = float(np.interp(x, qx, qz)); z_pip = float(np.interp(x, px, pz)); f = float(np.interp(x, qx, bf)); zf = float(np.interp(x, fx, fz))
        zc = f * (z_pip + z_out) / 2 + (1 - f) * z_out; crown = (1 - f) * max(0.0, z_out - z_pip)
        t = min(max((x - (x1 - NOSE[0])) / NOSE[0], 0.0), 1.0); nose = 1 - NOSE[1] * (1 - math.sqrt(max(0.0, 1 - t * t)))            # the nose rolls down, a quarter round
        hw = S['cushion_w'] / 2 - 0.02 * _sstep((x - (x1 - 0.06)) / 0.06)
        top = lambda ay, zc=zc, f=f, crown=crown, zf=zf, nose=nose, hw=hw: zf + (zc - S['bolster'] * f * (1 - _sstep((ay - b0) / (b1 - b0))) - crown * (ay / hw) ** 2 - zf) * nose
        w = _sstep((x - (x1 - 0.25)) / 0.25); stations.append([(x - float(bow(y, hw)) * w, y, h) for y, h in _section(hw, top, zf - 0.035)])
    _loft(bm, stations, idx['leather'])
    # --- the backrest: sections across the seat at each height, from the cushion to its top -------------------------------
    from scipy import ndimage
    back = (lab == SM.PARTS.index('back')) & ~ndimage.binary_dilation(lab == SM.PARTS.index('bracket'), iterations=4); rows = np.arange(330, 850, 6); rear_col = np.array([np.where(back[r])[0].min() if back[r].any() else np.nan for r in rows], float)
    # the photo's left outline is the backrest's rear face at its NEAR edge (the camera stands ahead of the backrest, so the
    # near edge is drawn furthest out): laid on the seat's middle plane it put the rear face 5 cm too far back
    ok = ~np.isnan(rear_col); rx, rz = SC.on_plane(-(S['back_w'] / 2 - 0.006))(rows[ok], rear_col[ok]); bx, bz = _line(BACK_FRONT, S['back_w'] / 2 - S['edge'])
    o = np.argsort(rz); rz, rx = rz[o], rx[o]; o = np.argsort(bz); bz, bx = bz[o], bx[o]
    top_r = float(np.where(back[:, 230:320].any(1))[0].min()); z_top = float(SC.on_plane(0.0)(np.array([top_r]), np.array([270.0]))[1][0])
    z_lo, z_hi = max(rz.min(), bz.min()) - 0.10, z_top; zs = np.r_[np.linspace(z_lo, z_hi - TOP_R, 22), z_hi - TOP_R + TOP_R * np.sin(np.linspace(0.15, 1.0, 7) * math.pi / 2)]; z_foot = float(rz.min()); ring = None
    stations = []
    for z in zs:
        xr = float(np.interp(z, rz, rx)); xb = float(np.interp(z, bz, bx)); u = max(0.0, (z - (z_hi - TOP_R)) / TOP_R); inset = TOP_R * (1 - math.sqrt(max(0.0, 1 - u * u)))
        xr += max(0.0, z_foot - z) * 0.9                                   # below the photo's rear line the backrest's foot turns forward, into the base
        hw = S['back_w'] / 2 - 1.5 * inset; depth = max(0.03, xb - xr - 2 * inset); xr += inset           # the top's corners are rounded in profile and across
        top = lambda ay, depth=depth, fb=float(_sstep((z_hi - z) / 0.16)): depth - min(S['bolster'] * 1.4, depth * 0.5) * fb * (1 - _sstep((ay - b0) / (b1 - b0)))      # (the bolsters fade out toward the shoulders)
        # the section's 'height' is the backrest's thickness forward of its rear face
        ring = [(xr + h, y, z) for y, h in _section(hw, top, 0.0)]; stations.append(ring)
    c = np.mean(ring, axis=0)                                              # the top itself: a low crown
    for k, dz in ((0.80, 0.004), (0.45, 0.007), (0.12, 0.008)): stations.append([(c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k, p[2] + dz) for p in ring])
    _loft(bm, stations, idx['leather'])
    # --- the parts that keep the photo's own outline, each on its plane ----------------------------------------------------
    def region(part, y_face, y_mid, width, rad, mat, rings=5, to=None):
        R.solid(bm, lab == SM.PARTS.index(part), to or SC.on_plane(y_face), (SC.DIST + y_face) / SC.F, width, rad, y0=y_mid, mat=idx[mat], rings=rings, spacing=0.012)
    # the base's region is its near face (a little inside it: the rounded edge draws the outline from there)
    n0 = len(bm.verts); region('base', -S['base_w'] / 2 + 0.008, 0.0, S['base_w'], 0.022, 'plastic'); bm.verts.ensure_lookup_table()
    for v in bm.verts[n0:]:                                                 # its front follows the nose's bow
        w = float(_sstep((v.co.x - (x1 - 0.25)) / 0.25)); hwb = S['base_w'] / 2; n = v[lay]
        v[lay] = (n[0], n[1] + 2 * BOW * v.co.y / hwb ** 2 * w * n[0], n[2]); v.co.x -= (float(bow(v.co.y, hwb)) - BOW) * w       # (the photo's outline is its near edge's)
    region('headrest', 0.0, 0.0, S['head_w'], 0.06, 'leather', rings=6, to=_skew(lab == SM.PARTS.index('headrest'), -0.108, 0.075))      # (where its rounded sides draw its outline: fitted)
    ry = S['rail_y'] + S['rail_w'] / 2; rail_to = _skew(lab == SM.PARTS.index('rail'), -ry, -ry + S['rail_w'])
    for sy in (-1, 1): region('rail', -ry, sy * S['rail_y'], S['rail_w'], 0.004, 'black', rings=1, to=rail_to)
    region('bracket', -S['back_w'] / 2, 0.0, S['back_w'], 0.003, 'black', rings=1)     # the black plate across the backrest's upper rear (the photo shows its near end)      # (the photo shows the near rail; the far one is its copy)
    # the controls on the base's near face, each standing out of it
    yb = -S['base_w'] / 2; P = lambda pts, y=yb: [tuple(q) for q in np.c_[_line(pts, y)]]
    oval = lambda box, n=20, k=4.0: [((box[0] + box[2]) / 2 + (box[2] - box[0]) / 2 * np.sign(math.cos(t)) * abs(math.cos(t)) ** (2 / k), (box[1] + box[3]) / 2 + (box[3] - box[1]) / 2 * np.sign(math.sin(t)) * abs(math.sin(t)) ** (2 / k)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    grow = lambda box, d: (box[0] - d, box[1] - d, box[2] + d, box[3] + d); disc = lambda c, r, n=18: [(c[0] + r * math.cos(t), c[1] + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    nf = len(bm.faces); R.ring(bm, np.array(P(oval(grow(F.CONTROL_WELL, 5), 32))), np.array(P(oval(grow(F.CONTROL_WELL, -3), 32))), yb - 0.0025, idx['plastic'], y_back=yb + 0.004)      # the well's rim (the well itself is not sunk: an approximation)
    bm.faces.ensure_lookup_table(); rim = list(bm.faces[nf:])
    x0, y0, xl, y1 = F.RECLINE_LEVER; _block(bm, P([(x0, y0), (x0 + 26, y0), (xl, y1 - 4), (xl - 4, y1), (x0 + 20, y1)]), yb - 0.012, yb, idx['plastic'])
    _block(bm, P(oval(F.SLIDE_SWITCH, 16, 6.0)), yb - 0.010, yb, idx['plastic'])
    cx, cy, cr = F.LUMBAR_KNOB; _block(bm, P(disc((cx, cy), cr)), yb - 0.004, yb, idx['black']); _block(bm, P(disc((cx, cy), cr - 4)), yb - 0.011, yb, idx['plastic'])
    # the belt's buckle, inboard of the cushion (the photo shows it over the far bolster): its stalk and its head with the red button
    yk = S['cushion_w'] / 2 + 0.012; A, B = np.array(BUCKLE[0], float), np.array(BUCKLE[1], float); u = (B - A) / np.linalg.norm(B - A); n = np.array((-u[1], u[0])) * BUCKLE[2] / 2
    box = lambda t0, t1, k=1.0: [tuple(A + (B - A) * t + n * sg * k) for t, sg in ((t0, -1), (t1, -1), (t1, 1), (t0, 1))]
    _block(bm, P(box(0.0, 0.84), yk), yk - 0.015, yk + 0.015, idx['leather']); _block(bm, P(box(0.84, 1.0, 0.8), yk), yk - 0.012, yk + 0.012, idx['red'])
    # the headrest's posts: the photo shows both (the further one 3.5 px lower and 32 px to the right, as the camera has them); upright rods under the headrest
    hz = SC.on_plane(0.0)(np.array([283.0]), np.array([285.0])); bz_top = float(z_hi)
    for sy in (-1, 1):
        cx = float(hz[0][0]) - 0.01; ring = [(cx + S['post_d'] / 2 * math.cos(a), sy * S['post_y'] + S['post_d'] / 2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)]
        _loft(bm, [[(x, y, z) for x, y in ring] for z in (bz_top - 0.03, float(hz[1][0]) + 0.03)], idx['chrome'])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _seams(bm, SEAMS, idx['seam'])
    rim = [f for f in rim if f.is_valid]; flat = [f for f in rim if abs(f.normal.y) > 0.9]            # (the rim is an open shell: its face must look out of the base)
    if flat and flat[0].normal.y > 0: bmesh.ops.reverse_faces(bm, faces=rim)
    if mirror:
        bmesh.ops.scale(bm, vec=(1, -1, 1), verts=bm.verts); bmesh.ops.reverse_faces(bm, faces=bm.faces)
        for v in bm.verts: v[lay] = (v[lay][0], -v[lay][1], v[lay][2])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in M.values(): me.materials.append(m)
    R.shade(me); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build(); me = ob.data; me.calc_loop_triangles()
    V = np.array([v.co for v in me.vertices]); print('seat: %d triangles; x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f' % (len(me.loop_triangles), V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

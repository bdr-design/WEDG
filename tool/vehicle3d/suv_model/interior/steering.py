"""The steering wheel, from wheel.png (square-on). Built on its own plane: x right and z up as the photo has them,
the driver at -y (so the photo's right is +x), the rim's centre at the origin; steering.build() returns one object to be set on the column.

What the photo gives (wheel_measure.py): the rim's outer outline, the four openings (over the pad, either side of
the lower spoke, and the keyhole in it) and the silver bezels round the switch pods, all as contours. What it does
not give is depth, because it is square-on; the depths below are a game choice until the two cabin photos are
measured (DISH, PLATE, PAD_RISE)."""
import bpy, bmesh, math, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wheel_measure as WM, wheel_features as F
from scipy import ndimage

DISH = 0.012          # the spokes' face is this far behind the rim's middle plane
PLATE = 0.024         # the spokes' thickness
PAD_RISE = 0.014      # the pad's face stands this far out of the spokes'
SEG, RING = 132, 12   # the rim: stations round it, points round its section
SEAMS = (44.0, 136.0, 270.0)          # where the rim's leather is joined, degrees from the photo's right, anticlockwise
STITCH = (8.0, 172.0, math.pi + 0.30)        # the stitching: from, to (degrees round the rim) and where on the tube's section (pi is the inner edge; more is toward the driver)
# The wood: an inlay on the rim's lower sides, on its inner part only (the outer part stays leather), pointed at both
# ends. Read on the photo as the part of the rim that is warm (red over blue by 3 or more of 255) and grained: how
# far across the rim's width it reaches (0 the inner edge, 1 the outer), by angle from the photo's right,
# anticlockwise; the right side mirrors the left within the reading.
WOOD = ((182.0, 0.10), (190.0, 0.50), (196.0, 0.63), (232.0, 0.60), (238.0, 0.45), (244.0, 0.27), (252.0, 0.10))


def _mat(name, *args, **kw):
    import imats
    return imats.m(name)


def materials():
    return {'leather': _mat('wheel_leather', (0.035, 0.035, 0.036), rough=0.62), 'plastic': _mat('cabin_black', (0.03, 0.03, 0.031), rough=0.5),
            'silver': _mat('cabin_silver', (0.50, 0.50, 0.50), metal=1.0, rough=0.38), 'wood': _mat('cabin_wood_grey', (0.075, 0.062, 0.052), rough=0.4, coat=0.5),
            'gloss': _mat('cabin_black_gloss', (0.012, 0.012, 0.013), rough=0.12, coat=1.0),
            'seam': _mat('cabin_seam', (0.006, 0.006, 0.006), rough=0.9), 'thread': _mat('wheel_thread', (0.50, 0.50, 0.47), rough=0.7)}


def _closed(c, n):
    """A contour resampled to n points evenly along its length, smoothed over about 1.5 mm."""
    c = np.asarray(c, float)
    if np.allclose(c[0], c[-1]): c = c[:-1]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(np.r_[c, c[:1]], axis=0).T))]; t = np.linspace(0, d[-1], n, endpoint=False)
    cc = np.r_[c, c[:1]]; p = np.c_[np.interp(t, d, cc[:, 0]), np.interp(t, d, cc[:, 1])]
    k = max(1, int(0.0015 / (d[-1] / n)))
    return np.c_[ndimage.gaussian_filter1d(p[:, 0], k, mode='wrap'), ndimage.gaussian_filter1d(p[:, 1], k, mode='wrap')]


def rim_inner(m):
    """The rim's inner radius by angle (degrees, anticlockwise from the photo's right): the far side of whichever
    opening lies on that ray, carried across the three spokes."""
    R = WM.DIAMETER / 2; ang = np.arange(360.0); rin = np.full(360, np.nan)
    for h in m['holes']:
        a = np.degrees(np.arctan2(h[:, 1], h[:, 0])) % 360; r = np.hypot(h[:, 0], h[:, 1])
        for i in range(360):
            k = np.abs((a - i + 180) % 360 - 180) < 0.75
            if k.any() and r[k].max() > 0.70 * R: rin[i] = np.nanmax([rin[i], r[k].max()])
    ok = ~np.isnan(rin); x = np.r_[ang[ok] - 360, ang[ok], ang[ok] + 360]; y = np.r_[rin[ok], rin[ok], rin[ok]]
    rin = np.interp(ang, x, y)
    return ang, ndimage.gaussian_filter1d(rin, 2, mode='wrap')


def build(name='steering_wheel'):
    m = WM.read(); R = WM.DIAMETER / 2; M = materials(); mats = list(M.values()); idx = {k: i for i, k in enumerate(M)}
    bm = bmesh.new()
    # --- the rim: a tube whose thickness follows the photo -----------------------------------------------------------
    ang, rin = rim_inner(m); th = np.linspace(0, 360, SEG, endpoint=False); ri = np.interp(th, ang, rin, period=360)
    t = (R - ri) / 2; rc = R - t; ring = []
    for a, tt, c in zip(np.radians(th), t, rc):
        row = []
        for j in range(RING):
            p = 2 * math.pi * j / RING; rr = c + tt * math.cos(p); row.append(bm.verts.new((rr * math.cos(a), 1.10 * tt * math.sin(p), rr * math.sin(a))))
        ring.append(row)
    for i in range(SEG):
        for j in range(RING):
            f = bm.faces.new((ring[i][j], ring[(i + 1) % SEG][j], ring[(i + 1) % SEG][(j + 1) % RING], ring[i][(j + 1) % RING]))
            f.material_index = idx['leather']; f.smooth = True
    # the leather's joins: across the rim at 44 and 136 degrees and at the foot (the photo: from (210, 226) on the outer
    # edge to (273, 291) on the inner, and the same mirrored; a line down the middle of the lower spoke's foot), as
    # dark bands 1.2 mm wide round the tube; and the stitching, a pale thread along the rim's inner edge from pod to
    # pod over the top (the photo shows it right on the inner outline)
    def tube(a_deg, p, extra):
        tt = float(np.interp(a_deg % 360, th, t, period=360)) + extra; c = float(np.interp(a_deg % 360, th, rc, period=360)); ar = math.radians(a_deg); rr = c + tt * math.cos(p)
        return (rr * math.cos(ar), 1.10 * tt * math.sin(p), rr * math.sin(ar))
    for a_deg in SEAMS:
        r0 = [bm.verts.new(tube(a_deg - 0.18, 2 * math.pi * k / 24, 0.0004)) for k in range(24)]; r1 = [bm.verts.new(tube(a_deg + 0.18, 2 * math.pi * k / 24, 0.0004)) for k in range(24)]
        for k in range(24):
            f = bm.faces.new((r0[k], r1[k], r1[(k + 1) % 24], r0[(k + 1) % 24])); f.material_index = idx['seam']
    rows = [[bm.verts.new(tube(a_deg, STITCH[2] + dp, 0.0006)) for dp in (-0.035, 0.035)] for a_deg in np.arange(STITCH[0], STITCH[1] + 0.01, 1.0)]
    for r0, r1 in zip(rows, rows[1:]):
        f = bm.faces.new((r0[0], r1[0], r1[1], r0[1])); f.material_index = idx['thread']
    # the wood inlays: thin shells 0.5 mm over the tube, from a little way round the inner side to the inlay's edge
    wa, wf = zip(*WOOD)
    for side in (1, -1):
        rows = []
        for a in np.arange(wa[0], wa[-1] + 0.01, 2.0):
            f = float(np.interp(a, wa, wf)); aa = a if side > 0 else 540.0 - a; tt = float(np.interp(aa % 360, th, t, period=360)); c = float(np.interp(aa % 360, th, rc, period=360))
            pb = 2 * math.pi - math.acos(2 * f - 1); ar = math.radians(aa); row = []
            for p in np.linspace(math.pi - 0.5, pb, 7):
                rr = c + (tt + 0.0005) * math.cos(p); row.append(bm.verts.new((rr * math.cos(ar), 1.10 * (tt + 0.0005) * math.sin(p), rr * math.sin(ar))))
            rows.append(row)
        for r0, r1 in zip(rows, rows[1:]):
            for k in range(6):
                f = bm.faces.new((r0[k], r1[k], r1[k + 1], r0[k + 1])); f.material_index = idx['wood']; f.smooth = True
    # --- the spokes: the disc inside the rim with the four openings cut out, as one plate -------------------------------
    outer = [bm.verts.new((c * math.cos(a), DISH, c * math.sin(a))) for a, c in zip(np.radians(th), rc - 0.25 * t)]
    edges = [bm.edges.new((outer[i], outer[(i + 1) % SEG])) for i in range(SEG)]
    for h in m['holes']:
        p = _closed(h, max(40, int(len(h) / 12))); vs = [bm.verts.new((u, DISH, v)) for u, v in p]
        edges += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    fill = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    front = [g for g in fill['geom'] if isinstance(g, bmesh.types.BMFace)]
    # triangle_fill fills the openings too: drop the faces whose middle is in the photo's backdrop
    from skimage.measure import points_in_poly
    cen = np.array([(f.calc_center_median().x, f.calc_center_median().z) for f in front]); inside = np.zeros(len(front), bool)
    for h in m['holes']: inside |= points_in_poly(cen, _closed(h, max(40, int(len(h) / 12))))
    drop = [f for f, k in zip(front, inside) if k]
    bmesh.ops.delete(bm, geom=drop, context='FACES'); front = [f for f in front if f.is_valid]
    for f in front:
        f.material_index = idx['plastic']
        if f.normal.y > 0: f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=front); back = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
    for v in back: v.co.y += PLATE
    for f in front:
        if f.is_valid: f.normal_flip()          # the copy left at the face looks back; turn the originals to the driver
    # --- the pad and the two switch pods, from wheel_features ----------------------------------------------------------
    cx, cy = m['centre']; su, sv = m['scale'], m['scale_v']
    def uv(p): p = np.asarray(p, float); return np.c_[(p[:, 0] - cx) * su, (cy - p[:, 1]) * sv]
    def ngon(pts, y, mat):
        vs = [bm.verts.new((u, y, v)) for u, v in pts]; f = bm.faces.new(vs); f.material_index = idx[mat]
        if f.normal.y > 0: f.normal_flip()
        return vs
    def prism(pts, y_front, y_back, mat, top=None):
        """A raised part: its face at y_front (toward the driver) and a skirt back to y_back."""
        a = ngon(pts, y_front, top or mat); b = [bm.verts.new((v.co.x, y_back, v.co.z)) for v in a]; n = len(a)
        for k in range(n):
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])); f.material_index = idx[mat]
    # the pad: from its outline on the spokes' face up over a rounded shoulder to the seam, then a shallow crown
    po = uv(F.snap(F.PAD, reach=8)); c0 = po.mean(0); st = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wheel_seam.npy'))
    seam = uv(st[:, ::-1]); phi = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    def polar(c):
        a = np.arctan2(c[:, 1] - c0[1], c[:, 0] - c0[0]); r = np.hypot(c[:, 0] - c0[0], c[:, 1] - c0[1]); o = np.argsort(a)
        return ndimage.gaussian_filter1d(np.interp(phi, a[o], r[o], period=2 * math.pi), 1.5, mode='wrap')
    r_out, r_seam = polar(_closed(po, 240)), polar(seam); rings = []
    for t, rise in ((0.0, 0.0), (0.25, 0.42), (0.55, 0.78), (0.85, 0.96), (1.0, 1.0), (1.35, 1.06), (2.2, 1.12), (4.0, 1.16)):
        r = r_out + (r_seam - r_out) * t if t <= 1 else r_seam / t
        rings.append([bm.verts.new((c0[0] + rr * math.cos(p), DISH - PAD_RISE * rise, c0[1] + rr * math.sin(p))) for rr, p in zip(r, phi)])
    for a, b in zip(rings, rings[1:]):
        for k in range(96):
            f = bm.faces.new((a[k], a[(k + 1) % 96], b[(k + 1) % 96], b[k])); f.material_index = idx['leather']; f.smooth = True
    f = bm.faces.new(rings[-1]); f.material_index = idx['leather']; f.smooth = True
    # the pods: a silver bezel round a dark window, the buttons standing in it
    for side in (1, -1):
        mir = (lambda p: p) if side > 0 else (lambda p: F.mirror(p, cx))
        bz, wn = uv(mir(F.snap(F.BEZEL, reach=4))), uv(mir(F.snap(F.WINDOW, reach=4)))
        vb = [bm.verts.new((u, DISH - 0.003, v)) for u, v in bz]; vw = [bm.verts.new((u, DISH - 0.003, v)) for u, v in wn]
        eb = [bm.edges.new((vb[k], vb[(k + 1) % len(vb)])) for k in range(len(vb))] + [bm.edges.new((vw[k], vw[(k + 1) % len(vw)])) for k in range(len(vw))]
        fl = [g for g in bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=eb)['geom'] if isinstance(g, bmesh.types.BMFace)]
        from skimage.measure import points_in_poly
        cen = np.array([(f.calc_center_median().x, f.calc_center_median().z) for f in fl]); inside = points_in_poly(cen, wn)
        bmesh.ops.delete(bm, geom=[f for f, k in zip(fl, inside) if k], context='FACES')
        for f in fl:
            if f.is_valid:
                f.material_index = idx['silver']
                if f.normal.y > 0: f.normal_flip()
        sk = [bm.verts.new((v.co.x, DISH + 0.001, v.co.z)) for v in vb]      # the bezel's outer wall, back into the spokes' face
        for k in range(len(vb)):
            f = bm.faces.new((vb[k], vb[(k + 1) % len(vb)], sk[(k + 1) % len(vb)], sk[k])); f.material_index = idx['silver']
        ngon(wn, DISH - 0.0005, 'gloss')                                     # the window's floor, 2.5 mm behind the bezel's face
        for poly, mat, proud in F.BUTTONS:
            prism(uv(mir(F.snap(poly, reach=3))), DISH - 0.0005 - proud * 1e-3, DISH - 0.0005, mat)
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for mt in mats: me.materials.append(mt)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = build(); print('steering wheel: %d faces' % len(ob.data.polygons))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

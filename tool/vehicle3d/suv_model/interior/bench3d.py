"""The second row's bench in three dimensions, in the car's frame (it faces +x).
Where it stands and its main sizes are cabin.BENCH: its backs' rear end the official cabin length (1955 mm) behind
the instrument panel's top lip (cabin.IP_REAR), and its cushion RISE over the first fit, which the LX 600's
second-row headroom asks for. Across, rear_bench.png gives it through the one camera that fits what it shows of the
bench (cabin.REAR_CAM, 1.06 m ahead of the cushion's front edge and 0.53 m over its top, 11.5 degrees down):
  the cushion's front edge 1475 px wide (columns 105 to 1580): 1.45 m;
  the backs between y 0.148 and 0.734 (the car's left, the photo's right), +-0.14 (middle) and -0.15 and -0.727;
  the outer headrests 0.25 m wide at y +-0.465, the middle one 0.26.
What neither gives is a CHOICE: the cushion's depth, the backs' lean and thickness, every rounding, the belts'
guides (on the C pillars' rear edge: the hull has no other place for them).
The hull rules where they meet: the rear wheels' wells stand 0.665 m out from x -0.85 back, up to 0.95 m, so the
cushion's rear corners and the outer backs' feet are narrower there than the photo's 1.45 m (WELL)."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imats, cabin as C, seat3d as S3
_sstep, _loft = S3._sstep, S3._loft

DEPTH, RISE, TOP_Z, LEAN, THICK, BACK_TOP, FRONT_X = C.BENCH      # where the bench stands and its main sizes: cabin.py says why
HALF_W = 0.725
WELL = (0.650, -0.78, 0.06, 1.06, 0.06)          # beside the wheels' wells: the bench's half width there; the wells' front (x) and the taper's length; their top (z) and the taper's height
BACKS = {'L': (0.148, 0.734), 'C': (-0.140, 0.140), 'R': (-0.727, -0.150)}      # each back's edges across the car
HEADS = {k: (y, w, a + RISE, b + RISE) for k, (y, w, a, b) in {'L': (0.465, 0.25, 1.385, 1.575), 'C': (0.0, 0.26, 1.355, 1.475), 'R': (-0.465, 0.25, 1.385, 1.575)}.items()}      # each headrest: y, width, foot, top
HEAD_T = 0.11                                    # the headrests' thickness
SPLIT_Y = 0.175                                  # the cushion's 60:40 split (the photo's column 1007; the camera looks back, so the photo's right is the car's left, +y)
BUCKLES = (-0.197, 0.21)                         # the belt buckles at the cushion's rear (the photo's columns 690 and 995)
NOSE = (0.07, 0.55)
BELT = (0.655, -0.175, 1.07 + RISE, 0.047)                # the belts: the outer ones' y on the backs, the middle one's, the height their tongues hang at, the webbing's width
LIP_Z = 0.68 + RISE                                     # the foot of the cushion's front face (the photo's row 862 through the camera); the base is under it


def _sec(a, b, top, bottom, ra, rb, n=17):
    """A section across the car between y a and b: from a's foot over the top to b's foot, the edges rounded by ra and rb. top(y) is the upper surface's height."""
    up = [(y, top(y)) for y in np.linspace(a + ra, b - rb, n)]
    arc_b = [(b - rb + rb * math.sin(t), top(b - rb) - rb * (1 - math.cos(t))) for t in np.linspace(0.3, math.pi / 2, 4)] + [(b, bottom)]
    arc_a = [(a + ra - ra * math.sin(t), top(a + ra) - ra * (1 - math.cos(t))) for t in np.linspace(0.3, math.pi / 2, 4)] + [(a, bottom)]
    return arc_a[::-1] + up + arc_b


def _blob(bm, c, half, mat, n=18, rings=9, power=3.5):
    """A cushioned block: a rounded box about c with the half sizes half (x, y, z)."""
    st = []
    for t in np.linspace(-1, 1, rings) * 0.985:
        k = (1 - abs(t) ** power) ** (1 / power)
        st.append([(c[0] + half[0] * k * np.sign(math.cos(a)) * abs(math.cos(a)) ** (2 / power), c[1] + half[1] * k * np.sign(math.sin(a)) * abs(math.sin(a)) ** (2 / power), c[2] + half[2] * t) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)])
    _loft(bm, st, mat)


def build(name='seat_bench_2'):
    M = {k: imats.m(v) for k, v in (('leather', 'seat_leather'), ('black', 'cabin_black'), ('red', 'cabin_red'), ('plastic', 'cabin_beige'), ('belt', 'seat_belt'), ('chrome', 'cabin_chrome'))}; idx = {k: i for i, k in enumerate(M)}; bm = bmesh.new(); z0 = C.FLOOR_Z
    # --- the cushion: sections across the car from under the backs to its nose ----------------------------------------------
    x_r, x_f = FRONT_X - DEPTH - 0.06, FRONT_X; xs = np.r_[np.linspace(x_r, x_f - NOSE[0], 18), x_f - NOSE[0] + NOSE[0] * np.sin(np.linspace(0, 1, 9)[1:] * math.pi / 2)]
    for side in (1, -1):                                                    # its two parts either side of the split
        st = []
        for x in xs:
            hw = WELL[0] + (HALF_W - WELL[0]) * _sstep((x - WELL[1]) / WELL[2]); u = (x - (x_f - DEPTH)) / DEPTH; zt = TOP_Z[0] + (TOP_Z[1] - TOP_Z[0]) * min(max(u, 0), 1); zf = LIP_Z
            t = min(max((x - (x_f - NOSE[0])) / NOSE[0], 0.0), 1.0); nose = 1 - NOSE[1] * (1 - math.sqrt(max(0.0, 1 - t * t)))
            # the outer places are dished a little between low bolsters; the middle one stands a little proud
            top = lambda y, zt=zt, hw=hw, zf=zf, nose=nose: zf + (zt - 0.012 * (1 - _sstep((abs(y) - (hw - 0.17)) / 0.09)) * _sstep((abs(y) - 0.13) / 0.06) - zf) * nose
            a_, b_ = (SPLIT_Y + 0.003, hw) if side > 0 else (-hw, SPLIT_Y - 0.003)           # (the right part is the wider: it carries the middle place)
            st.append([(x, y, h) for y, h in _sec(a_, b_, top, LIP_Z - 0.03, 0.012 if side > 0 else 0.045, 0.045 if side > 0 else 0.012)])
        _loft(bm, st, idx['leather'])
    # the base under the cushion, set back from its lip (the photo shows its covers; plain here)
    hb = WELL[0] - 0.01; vs = [bm.verts.new((x, y, z)) for z in (z0 + 0.003, LIP_Z - 0.01) for x, y in ((x_f - 0.07, -hb), (x_f - 0.07, hb), (C.REAR_FLOOR[0] + 0.01, hb), (C.REAR_FLOOR[0] + 0.01, -hb))]
    for k in range(4): f = bm.faces.new((vs[k], vs[(k + 1) % 4], vs[4 + (k + 1) % 4], vs[4 + k])); f.material_index = idx['plastic']
    # --- the backs: sections across the car at each height ------------------------------------------------------------------
    x_foot = FRONT_X - DEPTH; tl = math.tan(math.radians(LEAN)); TOP_R = 0.03
    for nm, (ya, yb) in BACKS.items():
        z_hi = BACK_TOP[1 if nm == 'C' else 0]; z_lo = TOP_Z[0] - 0.05; zs = np.r_[np.linspace(z_lo, z_hi - TOP_R, 14), z_hi - TOP_R + TOP_R * np.sin(np.linspace(0.15, 1.0, 6) * math.pi / 2)]; st = []; ring = None
        for z in zs:
            lim = WELL[0] + (HALF_W + 0.01 - WELL[0]) * _sstep((z - WELL[3]) / WELL[4]); a, b = max(ya, -lim), min(yb, lim)          # the outer backs' feet clear the wells
            u = max(0.0, (z - (z_hi - TOP_R)) / TOP_R); inset = TOP_R * (1 - math.sqrt(max(0.0, 1 - u * u))); hw = (b - a) / 2 - 0.004 - 1.2 * inset; yc = (a + b) / 2
            xf = x_foot - (z - TOP_Z[0]) * tl; bol = 0.0 if nm == 'C' else 0.028 * _sstep((z_hi - z) / 0.15)
            top = lambda ay, hw=hw, bol=bol, inset=inset: THICK - 2 * inset - bol * (1 - _sstep((ay - (hw - 0.15)) / 0.08))
            ring = [(xf - THICK + inset + h, yc + y, z) for y, h in S3._section(hw, top, 0.0, n=15)]; st.append(ring)
        c = np.mean(ring, axis=0)
        for k, dz in ((0.80, 0.004), (0.45, 0.007), (0.12, 0.008)): st.append([(c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k, p[2] + dz) for p in ring])
        _loft(bm, st, idx['leather'])
    # --- the headrests, each on two posts -----------------------------------------------------------------------------------
    for nm, (y, w, zf, zt) in HEADS.items():
        zb = BACK_TOP[1 if nm == 'C' else 0]; xc = x_foot - (zb - TOP_Z[0]) * tl - THICK / 2 + 0.01
        _blob(bm, (xc - (zf + zt - 2 * zb) / 2 * tl * 0.5, y, (zf + zt) / 2), (HEAD_T / 2, w / 2, (zt - zf) / 2), idx['leather'])
        for sy in (-1, 1):
            ring = [(xc + 0.006 * math.cos(a), y + sy * w * 0.27 + 0.006 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
            _loft(bm, [[(px, py, z) for px, py in ring] for z in (zb - 0.02, zf + 0.03)], idx['black'])
    # --- the buckles at the cushion's rear, their red buttons up -------------------------------------------------------------
    for y in BUCKLES:
        _blob(bm, (x_foot + 0.035, y, TOP_Z[0] + 0.012), (0.022, 0.026, 0.030), idx['black'], n=10, rings=5); _blob(bm, (x_foot + 0.035, y, TOP_Z[0] + 0.043), (0.014, 0.018, 0.004), idx['red'], n=10, rings=3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # --- the belts, as the photo has them at rest: the outer ones from the C pillars over the backs' shoulders and down their
    # outer bolsters to the tongues; the middle one down the right back's inner edge (the photo's left of the middle) ------------
    face = lambda z, proud: x_foot - (z - TOP_Z[0]) * tl + proud
    def strap(pts, w, mat, flat=(0.0, 1.0, 0.0)):
        a = [bm.verts.new((p[0] - flat[0] * w / 2, p[1] - flat[1] * w / 2, p[2] - flat[2] * w / 2)) for p in pts]; b = [bm.verts.new((p[0] + flat[0] * w / 2, p[1] + flat[1] * w / 2, p[2] + flat[2] * w / 2)) for p in pts]
        for k in range(len(pts) - 1):
            f = bm.faces.new((a[k], a[k + 1], b[k + 1], b[k])); f.material_index = mat
            if f.normal.x < 0: f.normal_flip()
    for sy in (1, -1):
        y = sy * BELT[0]; zs = np.linspace(BACK_TOP[0] - 0.035, BELT[2], 6)
        strap([(-1.15, sy * 0.655, 1.60), (face(BACK_TOP[0], -THICK * 0.45), y + sy * 0.03, BACK_TOP[0] + 0.012), (face(BACK_TOP[0] - 0.02, 0.012), y, BACK_TOP[0] - 0.015)] + [(face(z, 0.008), y, z) for z in zs], BELT[3], idx['belt'])
        _blob(bm, (face(BELT[2] - 0.035, 0.014), y, BELT[2] - 0.035), (0.006, 0.024, 0.040), idx['black'], n=10, rings=5); _blob(bm, (face(BELT[2] - 0.085, 0.014), y, BELT[2] - 0.085), (0.002, 0.014, 0.022), idx['chrome'], n=8, rings=3)
    y = BELT[1]; zs = np.linspace(BACK_TOP[0] - 0.01, BELT[2] - 0.08, 6); strap([(face(z, 0.008), y, z) for z in zs], BELT[3], idx['belt'])
    _blob(bm, (face(BELT[2] - 0.115, 0.014), y, BELT[2] - 0.115), (0.006, 0.024, 0.040), idx['black'], n=10, rings=5); _blob(bm, (face(BELT[2] - 0.165, 0.014), y, BELT[2] - 0.165), (0.002, 0.014, 0.022), idx['chrome'], n=8, rings=3)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in M.values(): me.materials.append(m)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); me.calc_loop_triangles()
    V = np.array([v.co for v in me.vertices]); print('bench: %d triangles; x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f' % (len(me.loop_triangles), V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
    return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build(); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

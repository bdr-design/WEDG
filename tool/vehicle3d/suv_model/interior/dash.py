"""The dashboard and what else dash_front.png shows of the cabin's front (console, A pillars, mirror), in the car's
frame. Each part is a region of the photo laid, through that photo's camera (cabin.CAMERAS), on a plane that stands
somewhere in the car, and given thickness behind the plane (relief.solid); smaller things (dash_features) are flat
shapes and blocks on those planes.
Where each plane stands is not in the photo: one photo fixes a direction from the camera, not a distance. The
stations and heights in PARTS are a CHOICE, taken from the hull where the hull gives them (the windshield's foot, the
pillars) and from the screen's assumed place otherwise, until driver_pov is measured."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import masks as M, relief as R, cabin as C, dash_features as DF
C_ = C
from seat import _mat
from scipy import ndimage
from skimage.draw import polygon as _poly
from mathutils import Matrix, Vector

import photocam as PC
CAM = PC.Camera('dash_front'); upright, level, ceiling = CAM.upright, CAM.level, CAM.ceiling
def pillar(foot, head, side):
    """The cabin's side of an A pillar: the plane through its foot and its head that faces the cabin's middle."""
    foot, head = np.array(foot, float), np.array(head, float); mid = (foot + head) / 2
    return CAM.plane(foot, mid - np.array((mid[0] - 0.6, 0.0, mid[2])), head - foot)

# Where the planes stand. dash_front and driver_pov are two views of the same dashboard (twoview.py: fifteen things
# read on both fit one scene to 9 px on average, 25 at worst), so the things both show have a place in the car:
#   the screen's display: its middle 0.53 m ahead of the car's middle and 1.295 m up, leaning back 27 degrees;
#   the hazard switch at (0.473, 0, 1.195), the silver frame's lower corners near (0.42, +-0.15, 1.12) and the big
#     knob at (0.387, 0.125, 1.057): one face leaning 28 degrees through (0.45, 0, 1.165);
#   the glovebox's latch at (0.474, -0.268, 1.170): the beige face, 2 cm ahead of that one and as steep;
#   the round switch at (0.538, 0.199, 1.253) and the left vent at (0.543, 0.679, 1.245): the upper face, upright;
#   the left cup holder at (0.178, 0.045, 0.989): the console's top, 0.99 m up.
# These rest on dash_front's own camera (cabin.CAMERAS) and on the display being 0.292 m wide. The instruments'
# place behind the wheel is a CHOICE.
def leaning(x, z, deg):
    """A face across the car through (x, 0, z) whose top leans forward by deg."""
    t = math.radians(deg); return CAM.plane((x, 0, z), (math.cos(t), 0, -math.sin(t)), (math.sin(t), 0, math.cos(t)))

LIP_ROW = 370
# name: (plane, thickness behind it, edge rounding, material, region: a box (col0, row0, col1, row1), corners [(col, row)...] or None)
A_FOOT, A_HEAD = (1.00, 0.74, 1.27), (0.47, 0.60, 1.74)                 # the hull's A pillar inside the glass (hullspace.py): its foot and head, left side
PARTS = {'upper': (upright(0.54), 0.12, 0.02, 'black', None), 'dash_top': (level(1.275), 0.12, 0.02, 'black', None), 'lower': (leaning(0.474, 1.170, 28.0), 0.30, 0.045, 'beige', None),
         'stack': (leaning(0.45, 1.165, 28.0), 0.30, 0.012, 'black', (688, 428, 1029, 572)), 'stack_low': (leaning(0.45, 1.165, 28.0), 0.30, 0.012, 'black', (703, 572, 983, 748)),
         'screen': (leaning(0.531, 1.295, 27.0), 0.022, 0.004, 'gloss', (689, 283, 1023, 407)), 'cluster': (upright(0.62), 0.02, 0.004, 'black', (300, 350, 590, 480)),
         'console_body': (level(0.985), 0.40, 0.02, 'beige', [(660, 748), (1060, 748), (1085, 941), (640, 941)]),
         'console': (level(0.99), 0.02, 0.008, 'wood', [(699, 748), (1031, 748), (1060, 917), (1060, 941), (681, 941), (681, 917)]),
         'mirror': (upright(0.52), 0.03, 0.012, 'black', (716, 118, 990, 208))}      # (the headliner is shell.py's: seen this flat, a region of it cannot be laid on its plane)


# The dashboard's own body is one surface, not a slab per face: sections along the car (x, z), the same across the
# car but behind the wheel, where the instruments' binnacle stands. The sections' corners are where the photo's
# edges fall on the faces' planes at the car's middle (the top's lip, row 370; the black band's foot and the beige
# face's top, row 440; the beige face's foot, row 665). Behind the wheel the photo is hidden by the wheel itself
# but for the hood's line (its top at row 300, 1.345 m up if it stands at x 0.50) and the instruments' window:
# the binnacle's depths, the sill under the instruments and the underside are a CHOICE.
BODY = ('upper', 'dash_top', 'lower', 'cluster')          # the faces the body carries (their planes stay, for the things on them)
Y_END = 0.79
BIN_Y, BIN_W, BIN_H = 0.430, (0.185, 0.225), 0.070       # the binnacle: its middle across the car, where it is whole and where it has ended, and its hood's height
#            the car's body of the dashboard                 behind the wheel
SECTION = [((1.000, 1.262), (1.000, 1.262), 0.0, 'black'),       # the windshield's foot
           ((0.800, 1.275), (0.860, 1.275), 0.0, 'black'),       # the top
           ((0.548, 1.275), (0.500, 1.275), 0.012, 'black'),     # the top's lip / the hood's lip (raised by the hood's height)
           ((0.540, 1.267), (0.508, 1.252), 0.006, 'black'),     # the black band's head / the lip's underside
           ((0.540, 1.213), (0.620, 1.285), 0.004, 'beige'),     # the band's foot / the instruments' head
           ((0.520, 1.213), (0.620, 1.125), 0.0, 'beige'),       # the ledge / the instruments' foot
           ((0.497, 1.213), (0.470, 1.105), 0.012, 'beige'),     # the beige face's head / the sill's edge
           ((0.396, 1.023), (0.405, 1.023), 0.030, 'beige'),     # the beige face's foot
           ((0.430, 0.985), (0.435, 0.985), 0.030, 'black'),     # the roll under it
           ((0.800, 0.960), (0.800, 0.960), 0.0, 'black')]       # the underside, to the firewall
BIN_MAT = {3: 'black', 4: 'dark', 5: 'black'}             # behind the wheel the hood's underside, the instruments' face and the sill are black


def _sstep(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)


def _section(y):
    """The body's section at y: (x, z) points with every corner rounded, and each stretch's material."""
    d = abs(y - BIN_Y); w = 1 - _sstep((d - BIN_W[0]) / (BIN_W[1] - BIN_W[0])); h = BIN_H * math.cos(min(d / BIN_W[1], 1.0) * math.pi / 2) ** 2
    C = [np.array(a) * (1 - w) + np.array(b) * w + (np.array((0, h)) * w if k in (2, 3) else 0) for k, (a, b, _, _) in enumerate(SECTION)]
    pts, mats = [C[0]], []
    for k in range(1, len(C) - 1):
        r = SECTION[k][2]; d0, d1 = C[k] - C[k - 1], C[k + 1] - C[k]; l0, l1 = np.linalg.norm(d0), np.linalg.norm(d1); t = min(r, 0.4 * l0, 0.4 * l1); e = min(0.002, 0.1 * l0, 0.1 * l1)
        T0, T1 = C[k] - d0 / l0 * t, C[k] + d1 / l1 * t; m0 = SECTION[k - 1][3] if not (w > 0.5 and k - 1 in BIN_MAT) else BIN_MAT[k - 1]
        pts += [T0 - d0 / l0 * e, T0] + [(1 - u) ** 2 * T0 + 2 * u * (1 - u) * C[k] + u * u * T1 for u in (1 / 3, 2 / 3)] + [T1, T1 + d1 / l1 * e]; mats += [m0] * 6
    pts.append(C[-1]); mats.append(SECTION[-2][3]); return pts, mats


def _body(bm, idx):
    ys = np.unique(np.r_[np.linspace(-Y_END, BIN_Y - BIN_W[1] - 0.01, 5), np.linspace(BIN_Y - BIN_W[1], BIN_Y + BIN_W[1], 41), Y_END]); rows, mats = [], []
    for y in ys:
        p, m = _section(float(y)); rows.append([bm.verts.new((q[0], y, q[1])) for q in p]); mats.append(m)
    fs = []
    for i in range(len(rows) - 1):
        for k in range(len(rows[0]) - 1):
            f = bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1])); f.material_index = idx[mats[i if abs(ys[i] - BIN_Y) > abs(ys[i + 1] - BIN_Y) else i + 1][k]]; f.smooth = True; fs.append(f)
    for r in (rows[0], rows[-1]):                                     # its ends, behind the doors' trims
        ed = [bm.edges.get((r[k], r[k + 1])) for k in range(len(r) - 1)] + [bm.edges.new((r[-1], r[0]))]
        fs += [g for g in bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=ed)['geom'] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    # the steering column's shroud, from behind the wheel's hub into the binnacle's sill
    x0, y0, z0, rake = C_.WHEEL; ax = np.array((math.cos(math.radians(rake)), 0.0, -math.sin(math.radians(rake)))); up = np.array((ax[2], 0.0, -ax[0])) * -1; fs = []; rings = []
    for t, (hw, hh) in ((0.045, (0.050, 0.040)), (0.10, (0.062, 0.050)), (0.26, (0.070, 0.058))):
        c = np.array((x0, y0, z0)) + ax * t; rings.append([bm.verts.new(tuple(c + np.array((0, 1.0, 0)) * hw * math.cos(a) + up * hh * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)])
    for a, b in zip(rings, rings[1:]):
        for k in range(12): f = bm.faces.new((a[k], a[(k + 1) % 12], b[(k + 1) % 12], b[k])); f.material_index = idx['black']; f.smooth = True; fs.append(f)
    fs.append(bm.faces.new(rings[0])); fs[-1].material_index = idx['black']; bmesh.ops.recalc_face_normals(bm, faces=fs)


def regions():
    a = M.rgb('dash_front'); H, W = a.shape[:2]; mag = M.backdrop(a); vv, uu = np.mgrid[0:H, 0:W]
    lab, k = ndimage.label(mag); ws = lab == lab[200, 400]                  # the windshield's opening (a point clear of the mirror)
    has = ws.any(0); cols = np.where(has)[0]; last = (H - 1 - np.argmax(ws[::-1], axis=0)).astype(float)      # its lower edge by column
    wbot = ndimage.gaussian_filter1d(np.interp(np.arange(W), cols, last[cols]), 4); reg = {}
    for name, (_, _, _, _, shape) in PARTS.items():
        if shape is None: continue
        m = np.zeros((H, W), bool)
        if not isinstance(shape[0], tuple): m[shape[1]:shape[3], shape[0]:shape[2]] = True
        else:
            r, c = _poly([p[1] for p in shape], [p[0] for p in shape], m.shape); m[r, c] = True
        reg[name] = m
    centre = (uu > 687) & (uu < 1030) & (vv > 427) & (vv < 748)
    # the upper face (the vents' band) and, above its lip, the dashboard's top, which runs level from the lip to the
    # windshield's foot: through dash_front's camera a top 1.275 m up spans rows 303 (x 1.0) to 370 (x 0.54), and the
    # outer vents' upper edge is at row 370
    reg['upper'] = (vv >= LIP_ROW) & (vv < 440) & (uu > 150) & (uu < 1560)
    # (only where the camera looks down onto that height: beside the windshield, where its edge climbs the pillars,
    # the photo's rows are above the top's own horizon and would be thrown behind the camera)
    reg['dash_top'] = (vv > np.maximum(wbot[None, :], 294)) & (vv < LIP_ROW + 2) & (uu > 150) & (uu < 1560)
    reg['lower'] = (vv >= 440) & (vv < 665) & (uu > 113) & (uu < 1590) & ~centre
    return reg, mag


def materials():
    return {'black': _mat('cabin_black', (0.03, 0.03, 0.031), rough=0.5), 'beige': _mat('trim_leather'),
            'gloss': _mat('cabin_black_gloss', (0.012, 0.012, 0.013), rough=0.12, coat=1.0), 'silver': _mat('cabin_silver', (0.50, 0.50, 0.50), metal=1.0, rough=0.38),
            'wood': _mat('cabin_wood_grey', (0.075, 0.072, 0.07), rough=0.4, coat=0.5), 'dark': _mat('cabin_shadow', (0.008, 0.008, 0.008), rough=0.8),
            'red': _mat('cabin_red', (0.55, 0.03, 0.02), rough=0.4), 'display': _mat('cabin_display', (0.004, 0.006, 0.012), rough=0.05, coat=1.0)}


def build(name='dashboard'):
    reg, mag = regions(); Mt = materials(); idx = {k: i for i, k in enumerate(Mt)}; bm = bmesh.new()
    lay = bm.verts.layers.float_vector.new('relief_n')
    _body(bm, idx)
    for part, (pl, thick, rad, mat, _) in PARTS.items():
        if part in BODY: continue
        n0 = len(bm.verts); r, c = np.where(reg[part]); mpp = pl.metres_per_px(r.mean(), c.mean())
        R.solid(bm, reg[part], pl.to_ab, mpp, thick, min(rad, thick / 2), y0=thick / 2, mat=idx[mat], rings=4 if rad > 0.02 else 2, spacing=0.014, fill=0.07)
        bm.verts.ensure_lookup_table()
        for v in bm.verts[n0:]: v.co = pl.to_car(v.co); v[lay] = pl.mx @ Vector(v[lay])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # the things on those faces (dash_features), each on its part's plane and standing out of it toward the camera
    for kind, part, mat, proud, shape in DF.STACK + DF.CONSOLE + DF.DASH:
        pl = PARTS[part][0]; n0 = len(bm.verts); nf = len(bm.faces)
        pts = lambda s: np.c_[pl.to_ab(np.array([p[1] for p in s], float), np.array([p[0] for p in s], float))]
        y = -proud * 1e-3
        if kind == 'flat': R.ngon(bm, pts(shape), y, idx[mat])
        elif kind == 'prism': R.prism(bm, pts(shape), y, 0.0, idx[mat])
        elif kind == 'ring': R.ring(bm, pts(shape[0]), pts(shape[1]), y, idx[mat], y_back=0.0)
        bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        for v in bm.verts[n0:]: v.co = pl.to_car(v.co)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[nf:])
    # the shifter: a leather boot and a knob standing on the console where the photo has its foot
    pl = PARTS['console'][0]; a, b = pl.to_ab(np.array([DF.SHIFTER['foot'][1]], float), np.array([DF.SHIFTER['foot'][0]], float)); foot = pl.to_car(Vector((float(a[0]), 0.0, float(b[0]))))
    cx, cy, z0 = foot.x, foot.y, foot.z
    def frustum(z_lo, z_hi, half_lo, half_hi, lean, mat):
        lo = [bm.verts.new((cx + sx * half_lo[0], cy + sy * half_lo[1], z_lo)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        hi = [bm.verts.new((cx - lean + sx * half_hi[0], cy + sy * half_hi[1], z_hi)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        fs = [bm.faces.new((lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k])) for k in range(4)] + [bm.faces.new(hi)]
        for f in fs: f.material_index = idx[mat]; f.smooth = False
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    # (the two-view fit has the knob's top 0.105 m over the console's top, and the knob is 78 by 61 px on dash_front: 66 by 51 mm)
    frustum(z0, z0 + 0.055, (0.046, 0.044), (0.020, 0.019), 0.012, 'black'); frustum(z0 + 0.055, z0 + 0.062, (0.022, 0.024), (0.023, 0.026), 0.012, 'silver')
    frustum(z0 + 0.062, z0 + 0.105, (0.024, 0.030), (0.027, 0.033), 0.020, 'black')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in Mt.values(): me.materials.append(m)
    R.shade(me); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build()
    ob.data.calc_loop_triangles(); print('dashboard: %d triangles' % len(ob.data.loop_triangles)); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

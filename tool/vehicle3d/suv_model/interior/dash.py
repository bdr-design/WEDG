"""The dashboard, from dash_front.png, which is nearly an elevation (cabin.CAMERAS). First pass: its main masses
as the photo's own regions, each set at a depth along the car and given thickness (relief.solid).
Built in its own frame, the photo's: x to the photo's right (the car's right), z up, y along the car with the
cabin at -y; build() turns it into the car's frame. Depths along the car are not in this photo: DEPTH is a game
choice until driver_pov is measured."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import masks as M, relief as R, cabin as C, dash_features as DF
from seat import _mat
from scipy import ndimage
from skimage.draw import polygon as _poly

(CAM_X, _, CAM_Z), _look, _fov, COL0, _ = C.CAMERAS['dash_front']; ROW0 = 470.5
F_PX = 836.0 / math.tan(math.radians(_fov) / 2); PITCH = math.atan2(CAM_Z - _look[2], _look[0] - CAM_X)      # looking down is positive

def _ray(rr, cc):
    """The photo's pixels as rays from the camera: how far up and to the photo's right each goes per metre forward (car x)."""
    a = (ROW0 - np.asarray(rr, float)) / F_PX; b = (np.asarray(cc, float) - COL0) / F_PX
    fx = math.cos(PITCH) + math.sin(PITCH) * a; fz = -math.sin(PITCH) + math.cos(PITCH) * a
    return b / fx, fz / fx
def scale(x): return F_PX / ((x - CAM_X) / math.cos(PITCH))        # pixels per metre at car station x, near the photo's middle
def to_xz_at(x):
    """(row, column) on the photo to the dashboard's own (x across to the photo's right, z up), for things at car station x."""
    def f(rr, cc):
        right, up = _ray(rr, cc); return right * (x - CAM_X), CAM_Z + up * (x - CAM_X)
    return f

def to_xy_at(z):
    """(row, column) to (x across to the photo's right, the car's x), for things lying level at height z (the console's top)."""
    def f(rr, cc):
        right, up = _ray(rr, cc); lam = (z - CAM_Z) / np.minimum(up, -1e-3); return right * lam, CAM_X + lam
    return f

# The main masses. Each is a region of the photo standing at one station along the car ('x': an upright face, with
# thickness behind it) or lying at one height ('z': a level top, with thickness under it). Where each stands is a
# CHOICE: one photo cannot give it. With the screen 0.55 m ahead of the car's middle (cabin.CAMERAS), the shifter's
# foot and the cup holders, taken as lying 0.80 m up, come out 0.55 and 0.37 m ahead of the middle.
# name: (plane, where, thickness, edge rounding, material, region as (col0, row0, col1, row1) or a list of (col, row))
PARTS = {'upper': ('x', 0.66, 0.30, 0.035, 'black', None), 'lower': ('x', 0.62, 0.30, 0.045, 'beige', None),
         'stack': ('x', 0.60, 0.30, 0.012, 'black', (688, 428, 1029, 572)), 'stack_low': ('x', 0.57, 0.30, 0.012, 'black', (703, 572, 983, 748)),
         'screen': ('x', 0.55, 0.022, 0.004, 'gloss', (689, 283, 1023, 407)),
         'console': ('z', 0.80, 0.30, 0.015, 'wood', [(699, 748), (1031, 748), (1060, 917), (1060, 941), (681, 941), (681, 917)])}


def regions():
    a = M.rgb('dash_front'); H, W = a.shape[:2]; mag = M.backdrop(a); vv, uu = np.mgrid[0:H, 0:W]
    lab, k = ndimage.label(mag); ws = lab == lab[200, 400]                  # the windshield's opening (a point clear of the mirror)
    has = ws.any(0); cols = np.where(has)[0]; last = (H - 1 - np.argmax(ws[::-1], axis=0)).astype(float)      # its lower edge by column
    wbot = ndimage.gaussian_filter1d(np.interp(np.arange(W), cols, last[cols]), 4); reg = {}
    for name, (_, _, _, _, _, shape) in PARTS.items():
        m = np.zeros((H, W), bool)
        if shape is None: continue
        if len(shape) == 4 and not isinstance(shape[0], tuple): m[shape[1]:shape[3], shape[0]:shape[2]] = True
        else:
            r, c = _poly([p[1] for p in shape], [p[0] for p in shape], m.shape); m[r, c] = True
        reg[name] = m
    centre = (uu > 687) & (uu < 1030) & (vv > 427) & (vv < 748)
    reg['upper'] = (vv > wbot[None, :]) & (vv < 440) & (uu > 150) & (uu < 1560) & ~reg['screen']
    reg['lower'] = (vv >= 440) & (vv < 665) & (uu > 113) & (uu < 1590) & ~centre
    return reg, mag


def materials():
    return {'black': _mat('cabin_black', (0.03, 0.03, 0.031), rough=0.5), 'beige': _mat('seat_leather', (0.60, 0.49, 0.34), rough=0.55),
            'gloss': _mat('cabin_black_gloss', (0.012, 0.012, 0.013), rough=0.12, coat=1.0), 'silver': _mat('cabin_silver', (0.50, 0.50, 0.50), metal=1.0, rough=0.38),
            'wood': _mat('cabin_wood_grey', (0.075, 0.072, 0.07), rough=0.4, coat=0.5), 'dark': _mat('cabin_shadow', (0.008, 0.008, 0.008), rough=0.8),
            'red': _mat('cabin_red', (0.55, 0.03, 0.02), rough=0.4)}


def build(name='dashboard'):
    from mathutils import Matrix
    reg, mag = regions(); Mt = materials(); idx = {k: i for i, k in enumerate(Mt)}; bm = bmesh.new()
    lay = bm.verts.layers.float_vector.new('relief_n')
    # relief's own frame (x right, y away from the camera, z up in the photo's plane) to the car's
    upright = Matrix(((0, 1, 0), (-1, 0, 0), (0, 0, 1)))        # x car = y, y car = -x, z car = z
    level = Matrix(((0, 0, 1), (-1, 0, 0), (0, -1, 0)))         # the photo's plane is the level one: x car = z, y car = -x, z car = -y
    for part, (plane, where, thick, rad, mat, _) in PARTS.items():
        n0 = len(bm.verts)
        if plane == 'x':
            R.solid(bm, reg[part], to_xz_at(where), 1.0 / scale(where), thick, min(rad, thick / 2), y0=where + thick / 2, mat=idx[mat], rings=4 if rad > 0.02 else 2, spacing=0.014, fill=0.07)
            mx = upright
        else:
            sc_ = F_PX / math.hypot(CAM_Z - where, (CAM_Z - where) / 0.96)        # pixels per metre along the level top, roughly
            R.solid(bm, reg[part], to_xy_at(where), 1.0 / sc_, thick, min(rad, thick / 2), y0=-where + thick / 2, mat=idx[mat], rings=2, spacing=0.014, fill=0.07)
            mx = level
        bm.verts.ensure_lookup_table()
        for v in bm.verts[n0:]: v.co = mx @ v.co; v[lay] = mx @ v[lay]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # the things on those faces (dash_features), each on its part's plane and standing out of it toward the camera
    for kind, part, mat, proud, shape in DF.STACK + DF.CONSOLE:
        plane, where = PARTS[part][0], PARTS[part][1]; n0 = len(bm.verts); nf = len(bm.faces)
        if plane == 'x': f, mx, y_face = to_xz_at(where), upright, where
        else: f, mx, y_face = to_xy_at(where), level, -where
        pts = lambda s: np.c_[f(np.array([p[1] for p in s], float), np.array([p[0] for p in s], float))]
        y = y_face - proud * 1e-3
        if kind == 'flat': R.ngon(bm, pts(shape), y, idx[mat])
        elif kind == 'prism': R.prism(bm, pts(shape), y, y_face, idx[mat])
        elif kind == 'ring': R.ring(bm, pts(shape[0]), pts(shape[1]), y, idx[mat], y_back=y_face)
        bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        for v in bm.verts[n0:]: v.co = mx @ v.co
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[nf:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in Mt.values(): me.materials.append(m)
    R.shade(me); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build()
    ob.data.calc_loop_triangles(); print('dashboard: %d triangles' % len(ob.data.loop_triangles)); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

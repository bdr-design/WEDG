"""Clean outlines of the owner's photos, as functions in metres (model frame: x forward centred, y left, z up).
side_top(x), side_bottom(x): the body's upper and lower lines from the side photo (roof rails and wheels taken out).
front_half(z): the body's half-width at height z from the front photo (mirrors and tyres taken out).
top_half(x): the body's half-width along its length from the top photo (mirrors taken out)."""
import numpy as np, json, os, sys
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import realframe as RF
HERE = os.path.dirname(os.path.abspath(__file__))
# The owner's photos: assets_src/vehicles/Black_SUV_Views in the repository (SUV_VIEWS overrides); png or webp.
VIEWS = next(d for d in (os.environ.get('SUV_VIEWS'), os.path.join(HERE, '..', '..', '..', 'assets_src', 'vehicles', 'Black_SUV_Views'),
                         os.path.join(HERE, '..', 'vehicles', 'Black_SUV_Views')) if d and os.path.isdir(d))
def photo(name): return next(p for p in (os.path.join(VIEWS, name + e) for e in ('.png', '.webp')) if os.path.exists(p))
CFG = json.load(open(os.path.join(HERE, 'views.json'))); L = CFG['L']
def _mask(name, fill=True):
    a = np.asarray(Image.open(photo(name)).convert('RGB')).astype(int)
    m = ~((a[..., 0] > 180) & (a[..., 2] > 180) & (a[..., 1] < 110))
    lab, n = ndimage.label(m); sizes = ndimage.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))
    return ndimage.binary_fill_holes(m) if fill else m
def roof_centre(xr):
    """The roof's centre line in the real frame, where the rails and the antenna hide it in the side photo (real x
    -0.01 ... -1.93). A quartic through the silhouette either side: it meets the photo's line within 0.6 mm and with
    the same slope at both ends (-0.093 at x 0, +0.096 at x -1.9), and peaks at 1.868 at x -0.87; the front photo's
    roof peaks at 1.871 and the rear photo's at 1.854."""
    u = np.asarray(xr, dtype=float) + 0.95
    return 1.868 + 0.0015 * u - 0.0098 * u ** 2 - 0.0222 * u ** 4
ROOF_BRIDGE = (0.02, -0.04, -1.90, -1.96)      # real x: the photo's line down to the arc, and back up to the photo's line
_side = _mask('01_left'); c = CFG['side']; s = c['s']
_cols = np.arange(_side.shape[1]); _xs = L / 2 - (_cols - c['u0']) * s
_zt = np.full(len(_cols), np.nan); _zb = np.full(len(_cols), np.nan)
for i in _cols:
    r = np.where(_side[:, i])[0]
    if len(r): _zt[i] = (c['v0'] - r.min()) * s; _zb[i] = (c['v0'] - r.max()) * s
ok = ~np.isnan(_zt); X_FRONT, X_REAR = _xs[ok].max(), _xs[ok].min()
_xs_ok = _xs[ok][::-1]; _zt_ok = _zt[ok][::-1]; _zb_ok = _zb[ok][::-1]
# wheels out of the lower line: where it drops below 0.2 m the tyre is there; bridge with the line either side
AXLES_X = (L / 2 - 0.941, L / 2 - 3.901)          # the hubs measured on the side photo (suv/hubs.json)
low = np.zeros(len(_zb_ok), bool)
for ax in AXLES_X: low |= np.abs(_xs_ok - ax) < 0.52
idx = np.arange(len(_zb_ok)); _zb_ok = _zb_ok.copy(); _zb_ok[low] = np.interp(idx[low], idx[~low], _zb_ok[~low])
_zt_s = ndimage.gaussian_filter1d(_zt_ok, 3); _zb_s = ndimage.gaussian_filter1d(_zb_ok, 4)
def _step(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
_xr = RF.x_real(_xs_ok); _b = ROOF_BRIDGE
_k = _step((_b[0] - _xr) / (_b[0] - _b[1])) * _step((_xr - _b[3]) / (_b[2] - _b[3]))
_zt_s = _zt_s * (1 - _k) + RF.z_photo(roof_centre(_xr)) * _k
def side_top(x): return np.interp(x, _xs_ok, _zt_s)
def side_bottom(x): return np.interp(x, _xs_ok, _zb_s)
# the tail, row by row: the rear-most body point at each height (the middle of the last pixel). side_top gives one
# height per column, so it cannot follow the notch under the roof spoiler; this does.
_rows = np.arange(_side.shape[0]); _zr_rows = (c['v0'] - _rows) * c['s']; _xr_rows = np.full(len(_rows), np.nan)
for j in _rows:
    q = np.where(_side[j])[0]
    if len(q): _xr_rows[j] = L / 2 - (q.max() + 0.5 - c['u0']) * c['s']
_okr = ~np.isnan(_xr_rows); _zr_ok = _zr_rows[_okr][::-1]; _xr_ok = _xr_rows[_okr][::-1]
def side_rear(z): return np.interp(z, _zr_ok, _xr_ok)
def tail_contour(z0=0.66, z1=1.62):
    """The car's rear line in the side photo to a fraction of a pixel: points (x, z) going up from the bumper's rear face
    to the rear glass. A pixel on the car's edge is part car and part magenta background; how magenta it is says how
    much of it is car, and the line runs where the car covers half. (side_rear above counts whole pixels: 2.9 mm.)"""
    from skimage import measure
    a = np.asarray(Image.open(photo('01_left')).convert('RGB')).astype(float); cs = CFG['side']
    cov = 1 - np.clip((np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) / 255.0, 0, 1)
    cov *= ndimage.binary_dilation(_side, iterations=3)
    q = max(measure.find_contours(cov, 0.5), key=len)
    x = L / 2 - (q[:, 1] - cs['u0']) * cs['s']; z = (cs['v0'] - q[:, 0]) * cs['s']
    k = np.flatnonzero((x < -2.0) & (z > z0) & (z < z1)); assert np.all(np.diff(k) == 1), 'the tail line is in pieces'
    P = np.c_[x[k], z[k]]
    return P if P[0, 1] < P[-1, 1] else P[::-1]
_front = _mask('02_front'); cf = CFG['front']
_zf, _wf = [], []
for v in range(_front.shape[0]):
    u = np.where(_front[v])[0]
    if len(u): _zf.append((cf['v0'] - v) * cf['s']); _wf.append(((u.max() - u.min()) / 2) * cf['s'] * cf['k'])
_zf = np.array(_zf[::-1]); _wf = np.array(_wf[::-1])
# mirrors: a bulge of more than 4 cm over the line between the rows either side of it
mirror = (_zf > 1.30) & (_zf < 1.62)
base = np.interp(_zf, _zf[~mirror], _wf[~mirror]); _wf = np.where(mirror & (_wf > base + 0.01), base, _wf)
_wf = np.where(_zf < 1.0, np.minimum(_wf, 0.985), _wf)      # below the fenders the tyres set the width: the body is 1.97 m
_wf_s = ndimage.gaussian_filter1d(_wf, 3)
def front_half(z): return np.interp(z, _zf, _wf_s)
_top = _mask('04_top'); ct = CFG['top']
_xt, _wt = [], []
for v in range(_top.shape[0]):
    u = np.where(_top[v])[0]
    if len(u): _xt.append(L / 2 - (v - ct['v0']) * ct['s']); _wt.append(((u.max() - u.min()) / 2) * ct['s'] * ct['k'])
_xt = np.array(_xt[::-1]); _wt = np.array(_wt[::-1])
mir = (_xt > 0.35) & (_xt < 1.05)
bt = np.interp(_xt, _xt[~mir], _wt[~mir]); _wt = np.where(mir & (_wt > bt + 0.008), bt, _wt)
_wt_s = ndimage.gaussian_filter1d(_wt, 3)
def top_half(x): return np.interp(x, _xt, _wt_s)
def top_tail_plan(reach=0.32):
    """The tail's plan in the top photo to a fraction of a pixel: half-widths (on the top photo's own scale, k applied)
    from the centre line outward, and how far ahead of the car's rear end the outline is at each (the two sides
    averaged, never falling). top_half above counts whole rows of 2.7 mm, so it is blind to the plan's first
    millimetres: it makes the car's end dead flat out to 0.27 m a side, where the photo is 3 to 5 mm ahead."""
    from skimage import measure
    a = np.asarray(Image.open(photo('04_top')).convert('RGB')).astype(float); c = CFG['top']
    cov = 1 - np.clip((np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) / 255.0, 0, 1)
    cov *= ndimage.binary_dilation(_top, iterations=3)
    q = max(measure.find_contours(cov, 0.5), key=len); v, u = q[:, 0], q[:, 1]
    d = (v.max() - v) * c['s']; y = (u - c['uc']) * c['s'] * c['k']; k = d < reach
    ys = np.arange(0.0, np.abs(y[k]).max() - 0.005, 0.0025); out = np.zeros(len(ys))
    for sgn in (1, -1):
        j = k & (y * sgn >= -0.01); o = np.argsort(y[j] * sgn); out += np.interp(ys, (y[j] * sgn)[o], d[j][o]) / 2
    out = ndimage.gaussian_filter1d(out, 3, mode='nearest'); out = np.maximum.accumulate(out - out[0])
    return ys, out
if __name__ == '__main__':
    print('length', X_REAR, X_FRONT)
    for xr in (0.3, 0.1, 0.02, -0.01, -0.04, -0.5, -0.95, -1.5, -1.9, -1.93, -1.96, -2.1):
        print('real x %5.2f roof %.4f' % (xr, float(RF.z_real(side_top(RF.x_photo(xr))))))
    for x in (2.45, 2.3, 1.5, 0.7, 0.0, -1.5, -2.3, -2.45): print('x %5.2f top %.3f bottom %.3f half %.3f' % (x, side_top(x), side_bottom(x), top_half(x)))
    for z in (1.95, 1.8, 1.6, 1.45, 1.3, 1.0, 0.6, 0.35): print('z %.2f half %.3f' % (z, front_half(z)))

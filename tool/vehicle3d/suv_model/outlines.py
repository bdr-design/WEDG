"""Clean outlines of the owner's photos, as functions in metres (model frame: x forward centred, y left, z up).
side_top(x), side_bottom(x): the body's upper and lower lines from the side photo (roof rails and wheels taken out).
front_half(z): the body's half-width at height z from the front photo (mirrors and tyres taken out).
top_half(x): the body's half-width along its length from the top photo (mirrors taken out)."""
import numpy as np, json, os, sys
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import realframe as RF
V = '/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/vehicles'
CFG = json.load(open(f'{V}/suv2/views.json')); L = CFG['L']
def _mask(name, fill=True):
    a = np.asarray(Image.open(f'{V}/Black_SUV_Views/{name}.png').convert('RGB')).astype(int)
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
if __name__ == '__main__':
    print('length', X_REAR, X_FRONT)
    for xr in (0.3, 0.1, 0.02, -0.01, -0.04, -0.5, -0.95, -1.5, -1.9, -1.93, -1.96, -2.1):
        print('real x %5.2f roof %.4f' % (xr, float(RF.z_real(side_top(RF.x_photo(xr))))))
    for x in (2.45, 2.3, 1.5, 0.7, 0.0, -1.5, -2.3, -2.45): print('x %5.2f top %.3f bottom %.3f half %.3f' % (x, side_top(x), side_bottom(x), top_half(x)))
    for z in (1.95, 1.8, 1.6, 1.45, 1.3, 1.0, 0.6, 0.35): print('z %.2f half %.3f' % (z, front_half(z)))

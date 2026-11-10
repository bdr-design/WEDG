"""Clean outlines of the owner's photos, as functions in metres (model frame: x forward centred, y left, z up).
side_top(x), side_bottom(x): the body's upper and lower lines from the side photo (roof rails and wheels taken out).
front_half(z, x): the body's half-width at height z at station x: the front photo's outline ahead of the cowl (mirrors and
    tyres taken out), and behind it side_half, which adds what the top and side photos show of the doors and the shoulder.
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
# The outlines to a fraction of a pixel. A pixel on the car's edge is part car, part magenta background, and how
# magenta it is says how much. Counting whole pixels (2 to 3 mm each) puts stairs in every gentle line: on the hood
# they were folds of 2 to 9 degrees from one station of the loft to the next, which showed as bands in the paint's
# reflections. Each line's fractions are centred on zero, so the whole-pixel calibration (views.json, realframe)
# stands as it was.
def _cov(name, m):
    a = np.asarray(Image.open(photo(name)).convert('RGB')).astype(float)
    return (1 - np.clip((np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) / 255.0, 0, 1)) * ndimage.binary_dilation(m, iterations=3)
def _frac(line, i, sign):
    """How far past pixel i (the car's last whole-counted pixel on this line, going sign) the car's edge is, in pixels."""
    k = np.arange(i - sign, i + 4 * sign, sign); k = k[(k >= 0) & (k < len(line))]; return float(np.clip(line[k].sum() - 2.0, -1.5, 1.5))
def _centred(f): f = np.asarray(f, dtype=float); return f - np.nanmean(f)
IRON = (10, 0.0004, 0.0004)      # pixels, metres, metres
def _iron(v, sig=3):
    """Smooth a line: over 3 pixels everywhere, and over 10 where that moves it less than 0.4 mm (fading out by
    0.8 mm). What is left of the pixel steps on a gentle line is under half a millimetre and goes; a real corner or
    crease moves more than that under the wide filter and stays as it was."""
    a = ndimage.gaussian_filter1d(v, sig); b = ndimage.gaussian_filter1d(v, IRON[0])
    w = np.clip(1 - (np.abs(b - a) - IRON[1]) / IRON[2], 0, 1); w = ndimage.gaussian_filter1d(ndimage.minimum_filter1d(w, 2 * IRON[0] + 1), IRON[0] / 2)
    return a * (1 - w) + b * w
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
_cs = _cov('01_left', _side); _ft = np.full(len(_cols), np.nan); _fb = np.full(len(_cols), np.nan)
for i in _cols:
    r = np.where(_side[:, i])[0]
    if len(r): _zt[i] = (c['v0'] - r.min()) * s; _zb[i] = (c['v0'] - r.max()) * s; _ft[i] = _frac(_cs[:, i], r.min(), -1); _fb[i] = _frac(_cs[:, i], r.max(), 1)
_zt = _zt + _centred(_ft) * s; _zb = _zb - _centred(_fb) * s
ok = ~np.isnan(_zt); X_FRONT, X_REAR = _xs[ok].max(), _xs[ok].min()
_xs_ok = _xs[ok][::-1]; _zt_ok = _zt[ok][::-1]; _zb_ok = _zb[ok][::-1]
# wheels out of the lower line: where it drops below 0.2 m the tyre is there; bridge with the line either side
AXLES_X = (L / 2 - 0.941, L / 2 - 3.901)          # the hubs measured on the side photo (suv/hubs.json)
low = np.zeros(len(_zb_ok), bool)
for ax in AXLES_X: low |= np.abs(_xs_ok - ax) < 0.52
idx = np.arange(len(_zb_ok)); _zb_ok = _zb_ok.copy(); _zb_ok[low] = np.interp(idx[low], idx[~low], _zb_ok[~low])
_zt_s = _iron(_zt_ok); _zb_s = ndimage.gaussian_filter1d(_zb_ok, 4)
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
_cf = _cov('02_front', _front); _ff = []
for v in range(_front.shape[0]):
    u = np.where(_front[v])[0]
    if len(u): _zf.append((cf['v0'] - v) * cf['s']); _wf.append(((u.max() - u.min()) / 2) * cf['s'] * cf['k']); _ff.append((_frac(_cf[v], u.max(), 1) + _frac(_cf[v], u.min(), -1)) / 2)
_zf = np.array(_zf[::-1]); _wf = np.array(_wf[::-1]) + _centred(_ff[::-1]) * cf['s'] * cf['k']
# mirrors: a bulge of more than 4 cm over the line between the rows either side of it
mirror = (_zf > 1.30) & (_zf < 1.62)
base = np.interp(_zf, _zf[~mirror], _wf[~mirror]); _wf = np.where(mirror & (_wf > base + 0.01), base, _wf)
# --- the body side between the cowl and the tail ------------------------------------------------------------------
# The front and rear photos show the side only where nothing stands out past it: the glass above the mirrors
# (z over 1.63) and the fenders' tops (up to z 1.28; the two photos agree within 7 mm there). Between those heights
# the mirrors hide it, and the doors, which are narrower than the fenders, are hidden at every height. What is in
# between comes from 04_top and 01_left (tools/topbelt.py, DIMENSIONS.md 8):
#   the chrome line under the side glass, in plan: 0.8036 m from the centre line at d 2.55 (top photo's scale; d is
#     metres behind the nose), bowed in ahead and behind (CHROME_PLAN, both sides within 3 mm of their mean);
#   the doors' widest line, where the side step comes out from under them: 0.895 (d 1.8 to 3.3), sweeping out to the
#     rear fender between d 3.3 and 3.66;
#   a crease along the doors 0.860 out, which 01_left shows as a highlight 65 to 70 mm under the chrome line.
# So, from the top down: the glass keeps the front photo's line above the mirrors and carries on down as an arc (a
# side glass is barrel-shaped: 16 degrees off plumb at z 1.63, 9 at its foot, radius 2.4 m) to the chrome line's
# place; under the belt a shoulder runs down and out to the crease, 65 mm below the belt at every station, and the
# door skin bulges from there to its widest at z 1.0. Over the rear wheel the fender's top (the photos' outline up
# to z 1.28) carries on up to the belt as one arc. Ahead of the cowl there is no glass and the front photo's outline
# is used whole (a straight line across the mirrors' heights).
#   The photos disagree: 04_top draws the whole cabin 25 to 37 mm narrower at the glass's head than 02_front and
# 03_rear do, and its quarter glass 43 mm further in at the rear end than the rear photo's back window allows. The
# front and rear photos keep the head, and the plan's taper to the rear is held at TAPER_MAX (a game choice).
XF = 2.498
TOP_TO_FRONT = 1.026 / RF.Y_SCALE       # top-photo widths to the hull's (the front photo's scale); see body.py
BELT = (2.298, 1.336, 0.0293)           # the chrome line on 01_left: z at d, and its slope (greenhouse.py)
def bplane(d): return BELT[1] + (d - BELT[0]) * BELT[2]
Q_D = (3.878, 4.328)                    # the kick-up's foot on the belt, and the quarter glass's rear edge
Q_TOP = 1.518
def zlow(d): return max(bplane(d), bplane(Q_D[0]) + (d - Q_D[0]) / (Q_D[1] - Q_D[0]) * (Q_TOP - bplane(Q_D[0])))
# 04_top draws the cabin shorter than 01_left does: the seams that cross the chrome line are at d 1.547, 2.570 and
# 3.484 on it (the door's front edge, the B pillar, the rear door's rear edge) and the quarter glass ends at 4.262,
# where 01_left has 1.544, 2.668, 3.760 and 4.328. The cabin's readings from 04_top (the chrome line) are moved to
# 01_left's stations by those four; what belongs to the wheels (the fender's sweep, the flares, the step) is not,
# because the two photos have the wheels at the same stations.
TOP_CABIN = ((1.547, 2.570, 3.484, 4.262), (1.544, 2.668, 3.760, 4.328))
CHROME_Z = ((3.90, 1.389), (4.00, 1.409), (4.10, 1.435), (4.20, 1.463), (4.30, 1.498))      # the chrome line on 01_left behind the kick-up's foot
CHROME_PLAN = ((1.80, 0.7940), (1.90, 0.7967), (2.00, 0.7985), (2.10, 0.7996), (2.20, 0.8006), (2.30, 0.8010), (2.40, 0.8016),
               (2.50, 0.8038), (2.60, 0.8034), (2.70, 0.8011), (2.80, 0.8006), (2.90, 0.7993), (3.00, 0.7983), (3.10, 0.7969),
               (3.20, 0.7954), (3.30, 0.7931), (3.40, 0.7911), (3.50, 0.7890), (3.60, 0.7833), (3.70, 0.7798), (3.80, 0.7751),
               (3.90, 0.7682), (4.00, 0.7574), (4.10, 0.7414), (4.20, 0.7329))      # d on 04_top
D_REF, TAPER_MAX = 2.65, 0.018
STRIP_OUT = 0.003                       # the chrome strip's middle stands this far outside the glass's foot (hull scale)
MIRROR_Z, COWL_D = (1.26, 1.63), (1.15, 1.60)
# Where the door's skin goes out to the rear fender. 04_top's own line (the door's widest, where the step comes out
# from under it) is straight to d 3.3 and sweeps out over the next 0.36 m, but behind d 3.4 that line is the flare,
# not the door; it has the rear handle as far out as the front one, and 01_left has the rear handle over d 3.39 to
# 3.68. No photo shows the surface's depth there. The owner's decisions (10 Nov, on r24's pictures): the sweep is a
# gentle one, and the rear flare's front leg stands about 2.5 cm out of the door, not the 4 to 6 cm that 04_top's
# outline gives. The flare cannot come in (it has to cover the tyre), so the door goes out to it, as a swelling
# round the wheel: full fender within REAR_BULGE[0] of the hub (seen from the side, heights shortened by
# REAR_BULGE[2] to follow the opening), none beyond REAR_BULGE[1], and the fender's top carried up to the belt over
# REAR_HAUNCH along the car. So the skin under the flare's band is within 28 mm of the flare's face, the door's
# widest line is up to 3 cm outside 04_top's at d 3.2 to 3.3, and under the rear handle the skin is 16 mm out at
# the bar's rear end (the bar is turned to lie along it). (r24: a sweep over d 3.30 to 3.66 that started 0.40 m
# later between z 0.95 and 1.17; the skin ran out 48 mm in 9 cm of height at the door's rear seam and read as a
# diagonal crease from behind.)
REAR_BULGE, REAR_HAUNCH = (0.45, 0.85, 0.9), (3.55, 4.00)
HUB_D, HUB_ZP = XF - float(RF.x_photo(RF.AXLE_X[1])), float(RF.z_photo(RF.HUB_Z))      # the rear hub in the photo frame
FRONT_D, FENDER_W, FENDER_CREASE = (1.48, 1.82), 0.985, 0.940      # the front fender's width fades into the door (hidden under the mirror on 04_top)
DOOR_W, DOOR_ZW, CREASE_Y, CREASE_DROP, CREASE_R = 0.895 * TOP_TO_FRONT, 1.00, 0.860 * TOP_TO_FRONT, 0.065, 0.012
FENDER_Z = 1.28                         # the fenders' tops are in the photos up to here
_wf_line = _wf.copy()
# below the fenders the tyres set the photo's width: the body is 1.97 m. The limit comes in over z 0.96 to 1.06 (a
# hard limit at z 1.0 left a step of 6 mm in the fenders there, a level hollow line of 9 degrees)
_t = np.clip((_zf - 0.96) / 0.10, 0, 1); _wf_line = np.minimum(_wf_line, 0.985 + 0.02 * _t * _t * (3 - 2 * _t))
_wf_line_s = _iron(_wf_line)
def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
def _sstep(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
_Z1 = MIRROR_Z[1]
_ba = (_zf > _Z1) & (_zf < _Z1 + 0.07); _M1 = float(np.polyfit(_zf[_ba], _wf_line[_ba], 1)[0]); _W1 = float(np.interp(_Z1, _zf, _wf_line_s))
_zr = bplane(D_REF) - _Z1
def _cabin(d): return np.interp(d, *TOP_CABIN)
_C1 = (float(np.interp(D_REF, _cabin([d for d, _ in CHROME_PLAN]), [y for _, y in CHROME_PLAN])) * TOP_TO_FRONT - STRIP_OUT - _W1 - _M1 * _zr) / _zr ** 2
def glass_half(z):
    """The side glass's half-width at height z, at the widest station (D_REF): the front outline above the mirrors,
    an arc below."""
    z = np.asarray(z, dtype=float); dz = np.minimum(z - _Z1, 0.0)
    return np.where(z >= _Z1, np.interp(z, _zf, _wf_line_s), _W1 + _M1 * dz + _C1 * dz * dz)
def _taper_table():
    d = np.arange(1.60, 4.41, 0.02); dp, yp = zip(*CHROME_PLAN); dp = _cabin(dp)
    y = np.interp(d, dp, yp); y = np.where(d < dp[0], yp[0] + (d - dp[0]) * (yp[1] - yp[0]) / (dp[1] - dp[0]), y)
    zc = np.where(d < CHROME_Z[0][0] - 0.02, [bplane(v) for v in d], np.interp(d, *zip(*((Q_D[0], bplane(Q_D[0])),) + CHROME_Z)))
    t = glass_half(zc) - (y * TOP_TO_FRONT - STRIP_OUT)
    t = np.where(d > D_REF, _smin(t, np.full_like(t, TAPER_MAX), 0.006), t)
    t = np.where(d > dp[-1], t[d <= dp[-1]][-1], t)
    return d, np.maximum(ndimage.gaussian_filter1d(t, 4, mode='nearest'), 0.0)
_TAPER = _taper_table()
def taper(d):
    """How far the greenhouse is inside its widest station's, at d behind the nose (the plan's bow, from CHROME_PLAN)."""
    return float(np.interp(d, *_TAPER))
_ka = (_zf > FENDER_Z - 0.04) & (_zf < FENDER_Z); _MS = float(np.polyfit(_zf[_ka], _wf_line[_ka], 1)[0]); _WS = float(np.interp(FENDER_Z, _zf, _wf_line_s))
def side_half(z, d):
    """The body's half-width at height z, d metres behind the nose, between the cowl and the tail."""
    z = np.asarray(z, dtype=float); zb = bplane(min(max(d, 1.50), 4.40)); t = taper(d)
    fade = 1 - _sstep((z - 1.862) / 0.07)                        # the roof's edge stays; the fade starts above the glass's head (1.851)
    up = glass_half(z) - t * fade; yf = float(glass_half(zb)) - t
    # the doors: a shoulder from the belt to the crease, rolled into the door skin's bulge
    # (04_top's outline is still the fender's at d 1.5, 0.939, and the door's own line is 0.893 at d 1.8)
    rf = float(_sstep((FRONT_D[1] - d) / (FRONT_D[1] - FRONT_D[0]))); dw = DOOR_W + (FENDER_W - DOOR_W) * rf; cy = CREASE_Y + (FENDER_CREASE - CREASE_Y) * rf
    zc = zb - CREASE_DROP; a = (dw - cy) / (zc - DOOR_ZW) ** 2
    door = _smin(yf + (zb - z) * (cy - yf) / CREASE_DROP, dw - a * np.clip(z - DOOR_ZW, 0, None) ** 2, CREASE_R)
    # over the rear wheel: the fender's top carried up to the belt in one arc
    h = zb - FENDER_Z; c = (yf - _WS - _MS * h) / h ** 2; dz = z - FENDER_Z
    fender = np.where(z <= FENDER_Z, np.interp(z, _zf, _wf_line_s), _WS + _MS * dz + c * dz * dz)
    rho = np.hypot(d - HUB_D, (z - HUB_ZP) * REAR_BULGE[2])
    # the larger of the two, taken softly: a hard maximum left a hollow line where they cross (8 to 13 degrees, from
    # over the opening's crown up to the rear handle; the review of r25's first build)
    r = np.clip(-_smin(-(1 - _sstep((rho - REAR_BULGE[0]) / (REAR_BULGE[1] - REAR_BULGE[0]))), -np.full_like(rho, float(_sstep((d - REAR_HAUNCH[0]) / (REAR_HAUNCH[1] - REAR_HAUNCH[0])))), 0.35), 0, 1)
    return np.where(z >= zb, up, door * (1 - r) + fender * r)
def front_half(z, x=None):
    """The body's half-width at height z at station x (photo frame). Ahead of the cowl it is the front photo's
    outline, behind it side_half; without x, the tail's (the last station's)."""
    line = np.interp(z, _zf, _wf_line_s)
    if x is None: return side_half(z, 9.0)
    d = XF - x; t = float(_sstep((COWL_D[1] - d) / (COWL_D[1] - COWL_D[0])))
    return line if t >= 1 else side_half(z, d) * (1 - t) + line * t
_top = _mask('04_top'); ct = CFG['top']
_xt, _wt = [], []
_cq = _cov('04_top', _top); _fq = []
for v in range(_top.shape[0]):
    u = np.where(_top[v])[0]
    if len(u): _xt.append(L / 2 - (v - ct['v0']) * ct['s']); _wt.append(((u.max() - u.min()) / 2) * ct['s'] * ct['k']); _fq.append((_frac(_cq[v], u.max(), 1) + _frac(_cq[v], u.min(), -1)) / 2)
_xt = np.array(_xt[::-1]); _wt = np.array(_wt[::-1]) + _centred(_fq[::-1]) * ct['s'] * ct['k']
mir = (_xt > 0.35) & (_xt < 1.05)
bt = np.interp(_xt, _xt[~mir], _wt[~mir]); _wt = np.where(mir & (_wt > bt + 0.008), bt, _wt)
_wt_s = _iron(_wt)
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

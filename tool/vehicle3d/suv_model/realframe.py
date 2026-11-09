"""The real frame: official LC300 ZX dimensions, and the map from the photo frame to it.

The owner's four photos are AI renders. Measured against the official figures and a real ZX/GR Sport side photo
(Wikimedia Commons, see DIMENSIONS.md) they are right along the body from the nose back to the B pillar, but:
- the rear wheel, the rear door's rear edge and the rear handle sit about 115 mm too far back (photo wheelbase
  2.969 m, real 2.850 m), while the tail is in the right place (photo length 4.990 m on the knots below, 4.993
  measured on the silhouette; real 4.985 m);
- the wheels are about 9 % too big (tyre 0.870 m across, real 265/55R20 is 0.800 m) and the whole car is drawn about
  5 % too tall: the rails top out at 2.023 m, against the official 1.925 m (which is the height over the roof rails);
- the front photo is 2.0125 m across its flares on its assumed scale, the spec sheet says 1.980 m.
So everything measured on the photos is built in the photo frame and then mapped here: x through a piecewise-linear
warp fitted to five features, z through a piecewise-linear map fitted to the ground, the door bottoms, the window
foot and the rail tops, y by 1980/2012.5. The wheels, the arches and the roof rails are built in the real frame."""

import numpy as np

# Official (toyota.jp ZX spec): 4985 x 1980 x 1925 mm, wheelbase 2850, track 1665/1665, 265/55R20, clearance 225.
L, W, H = 4.985, 1.980, 1.925
WHEELBASE, TRACK = 2.850, 1.665
FRONT_OVERHANG = 0.937                       # the photo's own (937 mm); the real side photo agrees from the hub to the door
X_NOSE = L / 2
AXLE_X = (X_NOSE - FRONT_OVERHANG, X_NOSE - FRONT_OVERHANG - WHEELBASE)
TYRE_D = (20 * 25.4 + 2 * 0.55 * 265) / 1000  # 265/55R20 -> 0.7995 m
HUB_Z = 0.370                                # loaded radius on the real photo: hub 88.4 px over the ground at 4.19 mm/px
                                             # (the free radius, hub to tyre top, is 95.6 px = 0.401 m); a rigid tyre
                                             # on this hub sinks 30 mm into the ground, which reads as a loaded tyre

# The photo frame (views.json, s 2.9422 mm/px): front hub at u 357.5 -> x 1.5609, rear hub at u 1366.5 -> x -1.4078.
# (An independent re-measure reads the hubs at u 356.7 and 1366.6: 2 mm and 0.3 mm from these.)
PHOTO_FRONT_HUB = 1.5609
# Distance behind the front hub, photo -> real: nose, front hub, B-pillar door seam, rear hub, tail.
_DP = np.array([-0.937, 0.0, 1.714, 2.969, 4.053])
_DR = np.array([-0.937, 0.0, 1.692, 2.850, 4.048])
# The front photo (views.json scale, which assumed a 2.2 m mirror-to-mirror width) is 2.0125 m across its flares
# (1095 px); the spec sheet's 1.980 m is the widest point, so the photo frame's y is scaled by 1.980 / 2.0125.
Y_SCALE = 1.980 / 2.0125
# The same for the other photos, used to score against them: the rear photo is 2.076 m across its flares on its
# views.json scale; the top photo at TOP_K 1.026 is already 1.980.
PHOTO_Y_SCALE = {'side': 1.0, 'front': Y_SCALE, 'rear': 1.980 / 2.076, 'top': 1.0}
# Heights, photo -> real. The real photo is scaled by its tyre (hub to tyre top 95.6 px = the free radius 0.401 m of
# its 265/65R18, so 4.19 mm/px; 4.17 is used, the mean with the wheelbase scale corrected for yaw). Knots: the ground,
# the door-bottom shut line (photo v 666.25 -> 0.455; real 102.8 px -> 0.429), the window foot at the front door
# (photo 1.340; real 300.5 px -> 1.253) and the rail tops (photo 2.0226; the official overall height 1.925, which the
# real photo confirms: rail tops 459.7 px -> 1.92). It puts the roof (photo 1.955-1.964) at 1.86-1.87, as on the
# real photo (roof at the rail foot 445.8 px -> 1.86). Under the rails and the antenna the side photo hides the roof
# line, so there it is an arc that peaks at 1.868 (outlines.roof_centre), with a crown across the car (body.crown).
_ZP = np.array([0.0, 0.455, 1.340, 2.0226])
_ZR = np.array([0.0, 0.429, 1.253, 1.925])

def _interp_ext(v, xs, ys):
    """Linear interpolation that keeps the end slopes outside the knots."""
    v = np.asarray(v, dtype=float)
    out = np.interp(v, xs, ys)
    lo, hi = v < xs[0], v > xs[-1]
    out = np.where(lo, ys[0] + (v - xs[0]) * (ys[1] - ys[0]) / (xs[1] - xs[0]), out)
    out = np.where(hi, ys[-1] + (v - xs[-1]) * (ys[-1] - ys[-2]) / (xs[-1] - xs[-2]), out)
    return out

def x_real(xp):
    return AXLE_X[0] - _interp_ext(PHOTO_FRONT_HUB - np.asarray(xp, dtype=float), _DP, _DR)

def x_photo(xr):
    return PHOTO_FRONT_HUB - _interp_ext(AXLE_X[0] - np.asarray(xr, dtype=float), _DR, _DP)

def y_real(yp): return np.asarray(yp, dtype=float) * Y_SCALE
def y_photo(yr): return np.asarray(yr, dtype=float) / Y_SCALE
def z_real(zp): return _interp_ext(zp, _ZP, _ZR)
def z_photo(zr): return _interp_ext(zr, _ZR, _ZP)

def warp_object(o):
    """Map a mesh object from the photo frame to the real frame (vertices in world space)."""
    import bpy
    from mathutils import Matrix
    me = o.data
    if o.type != 'MESH' or len(me.vertices) == 0: return
    mw = o.matrix_world.copy()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    w = (np.c_[co, np.ones(len(co))] @ np.array(mw).T)[:, :3]
    w[:, 0] = x_real(w[:, 0]); w[:, 1] = y_real(w[:, 1]); w[:, 2] = z_real(w[:, 2])
    inv = np.array(mw.inverted())
    local = (np.c_[w, np.ones(len(w))] @ inv.T)[:, :3]
    me.vertices.foreach_set('co', local.ravel()); me.update()

if __name__ == '__main__':
    for xp in (2.498, 1.5609, 0.933, -0.153, -1.4078, -2.492):
        print(f'{xp:7.3f} -> {float(x_real(xp)):7.3f}   back {float(x_photo(x_real(xp))):7.3f}')
    print('axles', AXLE_X, 'tyre', TYRE_D, 'roof', float(z_real(1.955)), 'belt', float(z_real(1.340)), 'hub', float(z_real(0.4369)),
          'round trip', float(z_photo(z_real(1.7))))

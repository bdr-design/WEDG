"""Build a dromedary mesh from the owner's side photo.

Body, neck and head: the photo silhouette "inflated" sideways with
anatomical widths. Legs, feet, ears, chest pad and tail: tapered tubes
and ellipsoids at real camel proportions. All parts are blended with a
smooth union and meshed with marching cubes.

Coordinates (metres): x forward (toward the head), y left, z up.
Image -> world: x = (U0 - u) / PX, z = (GROUND - v) / PX.
"""
import json
import numpy as np
import cv2
from scipy import ndimage
from skimage import measure

PX = 443.0          # pixels per metre (hump top 2.05 m above the ground)
GROUND = 1032.0     # image row of the ground under the feet
U0 = 700.0          # image column of x = 0 (about the elbows)


def w(u, v):
    return np.array([(U0 - u) / PX, 0.0, (GROUND - v) / PX])


# ---------------------------------------------------------------- silhouette
m = cv2.imread('mask.png', 0)
m = (m > 127).astype(np.uint8)
m[612:, :] = 0                                     # legs are built separately
# the ear: cut it off along the poll-to-neck line (two ears are added in 3D)
for uu_ in range(326, 380):
    cut = 58 + (uu_ - 326) * (106 - 58) / (380 - 326)
    m[40:int(cut), uu_] = 0
    m[int(cut):int(cut) + 14, uu_] = 1
flank = np.array([[1085, 545], [1162, 410], [1168, 612], [1095, 600]], np.int32)
cv2.fillPoly(m, [flank], 1)                        # flank fold hidden by shadow
# smooth belly line: lowest body pixel per column, smoothed, then refilled
cols = np.arange(560, 1175)
low = np.array([np.max(np.nonzero(m[:612, c])[0]) if m[:612, c].any() else 600 for c in cols], float)
low = ndimage.gaussian_filter1d(ndimage.median_filter(low, 41), 18)
for c, lv in zip(cols, low):
    top = np.min(np.nonzero(m[:, c])[0])
    m[top:int(lv), c] = 1
    m[int(lv):, c] = 0
m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3) > 0.5
m = m.astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
cv2.imwrite('mask_body.png', m * 255)

D = ndimage.distance_transform_edt(m) / PX       # metres to the outline
# local radius of the part: wide window on the barrel, narrow on neck and head
H0, W0 = m.shape
uu0, vv0 = np.meshgrid(np.arange(W0), np.arange(H0))
thin = ((uu0 < 600) & (vv0 < 520)).astype(np.float32)
thin = cv2.GaussianBlur(thin, (0, 0), 30)
R = (1 - thin) * ndimage.maximum_filter(D, size=441) + thin * ndimage.maximum_filter(D, size=61)   # wider than the half-depth: round, not lemon-shaped
R = ndimage.gaussian_filter(R, 22)
R = np.maximum(R, D)
inside = np.sqrt(np.clip(D * (2 * R - D), 0, None))
outside = ndimage.distance_transform_edt(1 - m) / PX

# lateral scale by region (blurred so parts flow into each other)
H, W = m.shape
S = np.full((H, W), 0.645, np.float32)             # barrel (about 58 cm wide)
uu, vv = np.meshgrid(np.arange(W), np.arange(H))
neck = (uu < 640) & (vv > 150)
head = (uu < 330) & (vv < 230)
S[neck] = 0.58
S[head] = 0.62
S[(uu < 175) & (vv < 230)] = 0.50                  # muzzle
S[(vv < 250) & (uu > 760) & (uu < 1080)] = 0.62    # hump
S[(uu > 1160)] = 0.555                             # rump and thighs are narrow
S = cv2.GaussianBlur(S, (0, 0), 28)
T = np.where(m > 0, inside * S, -outside)          # half-width; negative outside
T = ndimage.gaussian_filter(T, 1.5)

# ---------------------------------------------------------------- grid
VOX = 0.008
xs = np.arange(-1.45, 1.42, VOX)
ys = np.arange(-0.46, 0.46 + VOX, VOX)
zs = np.arange(-0.02, 2.24, VOX)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
U = U0 - X * PX
V = GROUND - Z * PX
t = ndimage.map_coordinates(T, [V.ravel(), U.ravel()], order=1, mode='constant', cval=-1.0).reshape(X.shape)
body = np.abs(Y) - t


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def round_cone(p, a, b, r1, r2):
    """iq's exact SDF of a cone with rounded ends between a and b."""
    ba = b - a
    l2 = ba @ ba
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - y[:, None] * ba
    x2 = (xv * xv).sum(1)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    out = np.empty_like(y)
    c1 = np.sign(z) * a2 * z2 > k
    c2 = np.sign(y) * a2 * y2 < k
    c3 = ~(c1 | c2)
    out[c1] = np.sqrt(x2[c1] + z2[c1]) * il2 - r2
    out[c2] = np.sqrt(x2[c2] + y2[c2]) * il2 - r1
    out[c3] = (np.sqrt(x2[c3] * a2 * il2) + y[c3] * rr) * il2 - r1
    return out


def ellipsoid(p, c, r):
    q = (p - c) / r
    k0 = np.linalg.norm(q, axis=1)
    k1 = np.linalg.norm(q / r, axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
F = body.ravel().copy()


def add(sdf_fn, box_min, box_max, k):
    global F
    sel = np.all((P >= box_min) & (P <= box_max), axis=1)
    F[sel] = smin(F[sel], sdf_fn(P[sel]), k)


def flat_cone(q, a, b, r1, r2, flat):
    """Round cone squeezed sideways by `flat` about its own axis (legs are deeper than wide)."""
    if flat == 1.0:
        return round_cone(q, a, b, r1, r2)
    yc = 0.5 * (a[1] + b[1])
    q2 = q.copy()
    q2[:, 1] = yc + (q[:, 1] - yc) * flat
    a2, b2 = a.copy(), b.copy()
    a2[1] = yc + (a[1] - yc) * flat
    b2[1] = yc + (b[1] - yc) * flat
    return round_cone(q2, a2, b2, r1, r2) / flat


def chain(points, radii, k_body, side, flats=None):
    pts = [np.array(p) for p in points]
    for i in range(len(pts) - 1):
        a, b = pts[i].copy(), pts[i + 1].copy()
        a[1] *= side
        b[1] *= side
        r1, r2 = radii[i], radii[i + 1]
        fl = flats[i] if flats else 1.0
        lo = np.minimum(a, b) - max(r1, r2) - 0.1
        hi = np.maximum(a, b) + max(r1, r2) + 0.1
        add(lambda q, a=a, b=b, r1=r1, r2=r2, fl=fl: flat_cone(q, a, b, r1, r2, fl), lo, hi, k_body if i == 0 else 0.03)


def j(u, v, y):
    p = w(u, v)
    p[1] = y
    return p


# joints in image space for the bind pose (both legs of a pair side by side)
FRONT = [j(700, 520, 0.17), j(702, 590, 0.17), j(706, 700, 0.165), j(704, 800, 0.155),
         j(698, 885, 0.15), j(694, 955, 0.15), j(688, 995, 0.15)]
FRONT_R = [0.12, 0.088, 0.066, 0.066, 0.046, 0.054, 0.05]
HIND = [j(1210, 430, 0.135), j(1180, 560, 0.175), j(1205, 665, 0.15), j(1224, 765, 0.125),
        j(1214, 870, 0.13), j(1204, 955, 0.14), j(1196, 995, 0.14)]
HIND_R = [0.16, 0.12, 0.085, 0.062, 0.043, 0.05, 0.047]
joints = {'front': FRONT, 'hind': HIND}

def smax(a, b, k):
    return -smin(-a, -b, k)


def foot(c, s, side, sx=1.0):
    """Pad, two toes with nails, pastern and fetlock below the fetlock point c.

    A camel stands on a broad cushion: the pastern runs forward and down from
    the fetlock into the pad, the two toes lie side by side at the front with
    a cleft between them and a nail on top of each, and the sole is flat.
    """
    o = np.array([c[0], c[1], 0.0])                    # ground under the fetlock
    loc = lambda x, y, z: o + np.array([x * s * sx, y * s * side, z * s])
    L = np.array([sx, 1.0, 1.0])                        # foot length scale
    lo, hi = o - np.array([0.16, 0.16, 0.05]), o + np.array([0.30, 0.16, 0.26])

    def sdf(q):
        d = ellipsoid(q, loc(0.05, 0, 0.032), np.array([0.12, 0.094, 0.058]) * s * L)       # the cushion
        for t in (-1, 1):
            d = smin(d, ellipsoid(q, loc(0.12, t * 0.044, 0.026), np.array([0.085, 0.05, 0.03]) * s * L), 0.02)
        # cleft between the toes, deeper toward the front
        d = smax(d, -ellipsoid(q, loc(0.21, 0, 0.04), np.array([0.11, 0.008, 0.07]) * s * L), 0.005)
        d = smax(d, -ellipsoid(q, loc(0.20, 0, 0.095), np.array([0.07, 0.02, 0.045]) * s * L), 0.012)
        # nails: caps over the front and top of each toe
        for t in (-1, 1):
            d = smin(d, ellipsoid(q, loc(0.178, t * 0.044, 0.03), np.array([0.04, 0.027, 0.032]) * s * L), 0.006)
        # pastern into the pad, fetlock knob and the rounded back of the fetlock
        d = smin(d, round_cone(q, loc(0.0, 0, c[2] / s), loc(0.055, 0, 0.088), 0.05 * s, 0.058 * s), 0.03)
        d = smin(d, ellipsoid(q, loc(-0.004, 0, c[2] / s), np.array([0.064, 0.052, 0.055]) * s * L), 0.025)
        d = smin(d, ellipsoid(q, loc(-0.045, 0, c[2] / s - 0.05), np.array([0.045, 0.042, 0.07]) * s * L), 0.025)
        return smax(d, -q[:, 2], 0.01)                  # flat sole on the ground
    add(sdf, lo, hi, 0.02)
    return [list(loc(0.178, t * 0.044, 0.03)) + [s] for t in (-1, 1)]


def cannon(top, fet, r_top, r_bot, side):
    """Slim cannon bone with the flexor tendons behind it: deeper than wide."""
    a, b = top.copy(), fet.copy()
    a[1] *= side
    b[1] *= side
    fw = np.array([1.0, 0, 0])
    for off, r1, r2 in ((0.012, r_top, r_bot), (-0.02, r_top * 0.72, r_bot * 0.75)):
        aa, bb = a + fw * off, b + fw * off
        if off < 0:
            aa = aa + np.array([0, 0, -0.05])
        add(lambda q, aa=aa, bb=bb, r1=r1, r2=r2: round_cone(q, aa, bb, r1, r2),
            np.minimum(aa, bb) - 0.12, np.maximum(aa, bb) + 0.12, 0.03)


nails = []
for side in (1, -1):
    chain(FRONT[:4], FRONT_R[:4], 0.06, side, flats=[1.25, 1.5, 1.4])
    chain(HIND[:4], HIND_R[:4], 0.08, side, flats=[1.45, 1.55, 1.35])
    cannon(FRONT[3], FRONT[5], 0.031, 0.028, side)
    cannon(HIND[3], HIND[5], 0.029, 0.026, side)
    for fet, scale, sx in ((FRONT[5], 1.0, 0.91), (HIND[5], 0.92, 0.90)):
        c = fet.copy()
        c[1] *= side
        nails += foot(c, scale, side, sx)
    # bony knees (carpus) and hocks
    for (u, v, r, y) in ((707, 798, np.array([0.06, 0.05, 0.07]), 0.155), (1222, 765, np.array([0.06, 0.045, 0.065]), 0.125)):
        c = j(u, v, y * side)
        c[0] += 0.012
        add(lambda q, c=c, r=r: ellipsoid(q, c, r), c - 0.2, c + 0.2, 0.03)
    hk = np.array([-0.97, 0.19 * side, 1.60])
    add(lambda q, c=hk: ellipsoid(q, c, np.array([0.07, 0.05, 0.05])), hk - 0.15, hk + 0.15, 0.04)
    # ears: short, set back and to the side
    e0 = w(340, 96)
    e0[1] = 0.055 * side
    e1 = w(362, 60)
    e1[1] = 0.12 * side
    add(lambda q, a=e0, b=e1: flat_cone(q, a, b, 0.036, 0.024, 2.0), np.minimum(e0, e1) - 0.1, np.maximum(e0, e1) + 0.1, 0.035)

# fuller drooping lower lip
lp = w(124, 176)
add(lambda q: ellipsoid(q, lp, np.array([0.04, 0.034, 0.055])), lp - 0.15, lp + 0.15, 0.03)
# chest pad (sternal callosity) under the brisket
cp = w(675, 590)
add(lambda q: smax(ellipsoid(q, cp, np.array([0.12, 0.09, 0.055])), 0.93 - q[:, 2], 0.02), cp - 0.3, cp + 0.3, 0.05)
# the thighs part below the vulva (about 1.36 m), so the hind legs are not one block
hg = 0.10 * np.clip((1.36 - P[:, 2]) / 0.36, 0, 1)
gap = np.maximum.reduce([np.abs(P[:, 1]) - hg, P[:, 2] - 1.36, P[:, 0] + 1.0, -P[:, 2] + 0.2])
F = smax(F, -gap, 0.03)
# udder between the thighs (Wadh she-camel: about 25 cm long), four teats about 5 cm
ud = np.array([-1.0, 0.0, 1.05])
add(lambda q: ellipsoid(q, ud, np.array([0.12, 0.09, 0.08])), ud - 0.25, ud + 0.25, 0.04)
for tx in (-0.045, 0.045):
    for ty in (-0.035, 0.035):
        ta, tb = ud + np.array([tx, ty, -0.06]), ud + np.array([tx, ty, -0.125])
        add(lambda q, a=ta, b=tb: round_cone(q, a, b, 0.012, 0.009), np.minimum(ta, tb) - 0.05, np.maximum(ta, tb) + 0.05, 0.01)
# tail with the hair tuft
tail = [w(1292, 420), w(1300, 520), w(1306, 610), w(1310, 700)]
for i, r in enumerate([(0.035, 0.03), (0.03, 0.026), (0.03, 0.038)]):
    a, b = tail[i], tail[i + 1]
    a[1] = b[1] = 0
    add(lambda q, a=a, b=b, r=r: round_cone(q, a, b, r[0], r[1]), np.minimum(a, b) - 0.12, np.maximum(a, b) + 0.12, 0.02)

F = F.reshape(X.shape)
F = ndimage.gaussian_filter(F, 0.7)
verts, faces, normals, _ = measure.marching_cubes(F, 0.0, spacing=(VOX, VOX, VOX))
verts += np.array([xs[0], ys[0], zs[0]])
np.savez_compressed('camel_hi.npz', verts=verts.astype(np.float32), faces=faces.astype(np.int32))
json.dump({k: [list(map(float, p)) for p in v] for k, v in joints.items()}, open('joints.json', 'w'))
json.dump({'nails': [list(map(float, p)) for p in nails], 'nail_r': [0.033, 0.028, 0.038]}, open('feet.json', 'w'))
print('verts', len(verts), 'faces', len(faces), 'bbox', verts.min(0).round(3), verts.max(0).round(3))

"""Build a textured game model of a vehicle from four orthographic photos.

Shape: the visual hull, i.e. the space inside the side, front and top
silhouettes at once, meshed with marching cubes.
Texture: each photo is projected onto the surfaces facing its camera and
baked into one texture. Magenta around the vehicle is first filled with
the nearest vehicle colour so misalignment never shows background.

Axes: x forward, y to the vehicle's left, z up; metres.
Usage: python build_vehicle.py <folder> <name> <length_m> <voxel_m> <tris> <rough> <clearcoat> <width_m incl. mirrors>
The AI views disagree slightly on width, so each view is stretched sideways to the real width.
"""
import sys, os, json
import numpy as np
import cv2
from scipy import ndimage
from skimage import measure

folder, name = sys.argv[1], sys.argv[2]
LENGTH, VOX, TRIS = float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
ROUGH, COAT = float(sys.argv[6]), float(sys.argv[7])
WREAL = float(sys.argv[8])
out = os.path.abspath(name)
os.makedirs(out, exist_ok=True)


def load(view):
    path = next(p for p in (os.path.join(folder, f'{view}.{e}') for e in ('png', 'webp')) if os.path.exists(p))
    img = cv2.imread(path)
    b, g, r = [img[:, :, i].astype(int) for i in range(3)]
    bg = (r > 200) & (b > 200) & (g < 90) | ((r - g > 120) & (b - g > 120))
    m = (~bg).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    big = st[1:, cv2.CC_STAT_AREA].max()
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > 0.002 * big:
            keep[lab == i] = 1
    keep = ndimage.binary_fill_holes(keep).astype(np.uint8)
    # fill the background with nearby vehicle colour (push-pull) for safe projection
    f = img.astype(np.float32)
    # background showing through windows or chassis gaps inside the outline: dark glass / shadow
    f[keep.astype(bool) & bg] = (40, 36, 32)
    known = keep.astype(bool).copy()
    for _ in range(300):
        if known.all():
            break
        s = cv2.blur(f * known[..., None], (7, 7))
        c = cv2.blur(known.astype(np.float32), (7, 7))
        new = (c > 0.02) & ~known
        f[new] = s[new] / c[new, None]
        known |= new
    filled = f.clip(0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(out, f'{view}_fill.png'), filled)
    x, y, w, h = cv2.boundingRect(keep)
    return keep, (x, y, w, h), img.shape[1], img.shape[0]


side, sb, sW, sH = load('01_left')
front, fb, fW, fH = load('02_front')
rear, rb, rW, rH = load('03_rear')
top, tb, tW, tH = load('04_top')

ss = LENGTH / sb[2]                       # metres per pixel in the side view
HEIGHT = sb[3] * ss
fs = HEIGHT / fb[3]                       # front and rear scaled to the same height
rs = HEIGHT / rb[3]
ts = LENGTH / tb[3]                       # top view scaled to the same length
print(f'{name}: L {LENGTH:.2f} H {HEIGHT:.2f} W(front) {fb[2] * fs:.2f} W(rear) {rb[2] * rs:.2f} W(top) {tb[2] * ts:.2f} -> {WREAL}')
kf, kr, kt = WREAL / (fb[2] * fs), WREAL / (rb[2] * rs), WREAL / (tb[2] * ts)
WIDTH = WREAL

# mapping world -> pixel for each view
cfg = {
    'side': dict(u0=sb[0], v0=sb[1] + sb[3], s=ss, W=sW, H=sH),
    'front': dict(uc=fb[0] + fb[2] / 2, v0=fb[1] + fb[3], s=fs, k=kf, W=fW, H=fH),
    'rear': dict(uc=rb[0] + rb[2] / 2, v0=rb[1] + rb[3], s=rs, k=kr, W=rW, H=rH),
    'top': dict(uc=tb[0] + tb[2] / 2, v0=tb[1], s=ts, k=kt, W=tW, H=tH),
    'L': LENGTH, 'Hm': HEIGHT, 'Wm': WIDTH,
}
json.dump(cfg, open(os.path.join(out, 'views.json'), 'w'), indent=1)

xs = np.arange(-LENGTH / 2 - VOX, LENGTH / 2 + VOX, VOX)
ys = np.arange(-WIDTH / 2 - VOX, WIDTH / 2 + VOX, VOX)
zs = np.arange(-VOX, HEIGHT + VOX, VOX)


def sample(mask, u, v):
    u = np.round(u).astype(int)
    v = np.round(v).astype(int)
    ok = (u >= 0) & (u < mask.shape[1]) & (v >= 0) & (v < mask.shape[0])
    outv = np.zeros(u.shape, bool)
    outv[ok] = mask[v[ok], u[ok]] > 0
    return outv


X, Z = np.meshgrid(xs, zs, indexing='ij')
Y, Z2 = np.meshgrid(ys, zs, indexing='ij')
X3, Y3 = np.meshgrid(xs, ys, indexing='ij')
side_uv = (cfg['side']['u0'] + (LENGTH / 2 - X) / ss, cfg['side']['v0'] - Z / ss)                  # (x, z)
front_uv = (cfg['front']['uc'] + Y / (fs * kf), cfg['front']['v0'] - Z2 / fs)                      # (y, z)
rear_uv = (cfg['rear']['uc'] - Y / (rs * kr), cfg['rear']['v0'] - Z2 / rs)
top_uv = (cfg['top']['uc'] - Y3 / (ts * kt), cfg['top']['v0'] + (LENGTH / 2 - X3) / ts)           # (x, y)
use_rear = os.environ.get('USE_REAR', '1') == '1'

if os.environ.get('HULL', 'sdf') == 'sdf':
    # Each silhouette becomes a signed distance in metres (negative inside), sampled smoothly between pixels, and the
    # hull is where all of them are negative. This follows the photo outlines to a fraction of a pixel: no voxel
    # terraces on the long, nearly flat bonnet and roof, which the binary grid left as stripes in the paint.
    CLOSE = int(os.environ.get('CLOSE', '13'))      # px: notches narrower than this in an outline are keying noise
    SDF_SIGMA = float(os.environ.get('SDF_SIGMA', '3.0'))

    LEN_SIGMA = float(os.environ.get('LEN_SIGMA', '20'))   # px, extra smoothing along the car's length

    def sdf2d(mask, scale, sigma=None):
        m = mask.astype(np.uint8)
        if CLOSE > 1:
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (CLOSE, CLOSE)))
        m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0) > 0.5
        d = ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m)
        return ndimage.gaussian_filter(d.astype(np.float32), sigma or SDF_SIGMA) * scale

    def sample_f(f, uv):
        return ndimage.map_coordinates(f, [uv[1], uv[0]], order=1, mode='nearest')

    def smax(a, b, k):         # a rounded intersection: the edges where two views meet are softened by about k
        h = np.clip(0.5 - 0.5 * (b - a) / k, 0, 1)
        return b * (1 - h) + a * h + k * h * (1 - h)

    K_ROUND = float(os.environ.get('ROUND', '0.012'))
    # smoothing along the length keeps the nose and tail in place but irons the long lines and the sides flat
    S2 = sample_f(sdf2d(side, ss, (SDF_SIGMA, LEN_SIGMA * 0.6)), side_uv)
    # the front and rear outlines set the roof and bonnet across the car: smoothing them across the width irons out
    # the ribs a straight pull along the length would print on the roof
    F2 = sample_f(sdf2d(front, fs, (SDF_SIGMA, LEN_SIGMA * 0.6)), front_uv)
    if use_rear:
        F2 = smax(F2, sample_f(sdf2d(rear, rs, (SDF_SIGMA, LEN_SIGMA * 0.6)), rear_uv), K_ROUND)
    T2 = sample_f(sdf2d(top, ts, (LEN_SIGMA, SDF_SIGMA)), top_uv)
    field = smax(smax(S2[:, None, :], F2[None, :, :], K_ROUND), T2[:, :, None], K_ROUND).astype(np.float32)
    field[0], field[-1], field[:, 0], field[:, -1], field[:, :, 0], field[:, :, -1] = 1, 1, 1, 1, 1, 1
    print('sdf grid', field.shape)
    verts, faces, _, _ = measure.marching_cubes(field, 0.0, spacing=(VOX, VOX, VOX))
    verts += np.array([xs[0], ys[0], zs[0]])
    # negative inside: marching cubes already winds the faces outwards
else:
    S2 = sample(side, *side_uv)
    F2 = sample(front, *front_uv)
    R2 = sample(rear, *rear_uv)
    FR = F2 & R2 if use_rear else F2
    T2 = sample(top, *top_uv)
    occ = S2[:, None, :] & FR[None, :, :] & T2[:, :, None]
    print('voxels', occ.shape, int(occ.sum()))
    field = ndimage.gaussian_filter(occ.astype(np.float32), float(os.environ.get('SIGMA', '0.9')))
    verts, faces, _, _ = measure.marching_cubes(field, 0.5, spacing=(VOX, VOX, VOX))
    verts += np.array([xs[0], ys[0], zs[0]])
    faces = faces[:, ::-1]      # occupancy field: flip so normals face outward
# Taubin smoothing removes the voxel steps (visible in paint reflections) without shrinking the body
from scipy import sparse
n = len(verts)
rows = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2], faces[:, 1], faces[:, 2], faces[:, 0]])
cols = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0], faces[:, 0], faces[:, 1], faces[:, 2]])
A = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
A.data[:] = 1.0
deg = np.asarray(A.sum(1)).ravel()
Wm = sparse.diags(1.0 / np.maximum(deg, 1)) @ A
for _ in range(int(os.environ.get('TAUBIN', '12'))):
    verts = verts + 0.5 * (Wm @ verts - verts)
    verts = verts - 0.53 * (Wm @ verts - verts)
verts[:, 2] -= verts[:, 2].min()
# a calm normal field decides which photo paints which surface (raw normals are too noisy)
fn = np.cross(verts[faces[:, 1]] - verts[faces[:, 0]], verts[faces[:, 2]] - verts[faces[:, 0]])
vn = np.zeros_like(verts)
for k in range(3):
    np.add.at(vn, faces[:, k], fn)
for _ in range(40):
    vn = Wm @ vn
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)
np.savez_compressed(os.path.join(out, 'hull.npz'), verts=verts.astype(np.float32), faces=faces.astype(np.int32), wn=((vn + 1) / 2).astype(np.float32))
json.dump({'tris': TRIS, 'rough': ROUGH, 'coat': COAT}, open(os.path.join(out, 'mat.json'), 'w'))
print('mesh', len(verts), len(faces))

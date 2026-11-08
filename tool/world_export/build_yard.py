"""Turn the prototype dump (export.json) into engine-neutral files:
yard.glb (fixed objects merged into 5 materials), scatter GLBs + yard_scatter.json, vehicles.json.
Frame: x east, y up, z south, metres (the prototype's and terrain.glb's)."""
import sys, os, io, json, base64, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import GLBWriter
from terrain_surface import TerrainSurface

EXP, OUT, TERRAIN = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(EXP))
T = TerrainSurface(TERRAIN)
LAYOUT = d['layout']
ROADZ = LAYOUT['roadZ']

NEAREST, LINEAR, LIN_MIP = 9728, 9729, 9987
REPEAT, CLAMP = 10497, 33071


def srgb8(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.round(np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055) * 255).astype(np.uint8)


def img(name):
    u = d['textures'][name]['png']
    return Image.open(io.BytesIO(base64.b64decode(u.split(',', 1)[1]))).convert('RGBA')


def png_bytes(im):
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True); return b.getvalue()


def jpg_bytes(im, q=92):
    b = io.BytesIO(); im.convert('RGB').save(b, 'JPEG', quality=q, subsampling=0, optimize=True); return b.getvalue()


# ------------------------------------------------------------------ triangle soups
class Soup:
    def __init__(self, tp, tn, tuv=None):
        self.tp, self.tn = np.asarray(tp, float), np.asarray(tn, float)
        self.tuv = None if tuv is None else np.asarray(tuv, float)

    @staticmethod
    def from_part(p, index=None):
        P = np.array(p['pos'], float).reshape(-1, 3); N = np.array(p['nor'], float).reshape(-1, 3)
        UV = None if p.get('uv') is None else np.array(p['uv'], float).reshape(-1, 2)
        I = np.array(p['idx'] if index is None else index, int).reshape(-1, 3)
        return Soup(P[I], N[I], None if UV is None else UV[I])

    def __len__(self): return len(self.tp)

    def flipped(self):
        o = [0, 2, 1]
        return Soup(self.tp[:, o], -self.tn[:, o], None if self.tuv is None else self.tuv[:, o])

    def keep(self, m):
        return Soup(self.tp[m], self.tn[m], None if self.tuv is None else self.tuv[m])

    def drop_ground_bottoms(self):
        """faces that lie on the ground and face down are never seen (the camera stays above ground)"""
        fn = np.cross(self.tp[:, 1] - self.tp[:, 0], self.tp[:, 2] - self.tp[:, 0])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        hidden = (fn[:, 1] < -0.9) & (self.tp[:, :, 1].max(axis=1) < 0.01)
        return self.keep(~hidden), int(hidden.sum())

    def clip_grid(self, axis):
        """split triangles along integer lines of uv[axis] so every piece lies in one tile; returns (soup, tile index per tri)"""
        out_p, out_n, out_uv, out_k = [], [], [], []
        for t in range(len(self)):
            P, N, UV = self.tp[t], self.tn[t], self.tuv[t]
            lo, hi = UV[:, axis].min(), UV[:, axis].max()
            k0, k1 = int(math.floor(lo + 1e-9)), int(math.ceil(hi - 1e-9))
            for k in range(k0, max(k1, k0 + 1)):
                poly = [(P[i], N[i], UV[i]) for i in range(3)]
                for bound, sign in ((k, 1), (k + 1, -1)):
                    res = []
                    for i in range(len(poly)):
                        a, b = poly[i], poly[(i + 1) % len(poly)]
                        da, db = sign * (a[2][axis] - bound), sign * (b[2][axis] - bound)
                        if da >= -1e-12: res.append(a)
                        if (da >= -1e-12) != (db >= -1e-12):
                            s = da / (da - db)
                            res.append(tuple(a[j] + (b[j] - a[j]) * s for j in range(3)))
                    poly = res
                    if len(poly) < 3: break
                if len(poly) < 3: continue
                for i in range(1, len(poly) - 1):
                    tri = [poly[0], poly[i], poly[i + 1]]
                    area = np.linalg.norm(np.cross(tri[1][0] - tri[0][0], tri[2][0] - tri[0][0]))
                    if area < 1e-10: continue
                    out_p.append([v[0] for v in tri]); out_n.append([v[1] for v in tri]); out_uv.append([v[2] for v in tri]); out_k.append(k)
        return Soup(out_p, out_n, out_uv), np.array(out_k)


def cat(soups):
    soups = [s for s in soups if len(s)]
    tp = np.concatenate([s.tp for s in soups]); tn = np.concatenate([s.tn for s in soups])
    tuv = None if soups[0].tuv is None else np.concatenate([s.tuv for s in soups])
    return Soup(tp, tn, tuv)


def to_indexed(s):
    P = s.tp.reshape(-1, 3); N = s.tn.reshape(-1, 3)
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    cols = [P, N] + ([s.tuv.reshape(-1, 2)] if s.tuv is not None else [])
    A = np.concatenate(cols, axis=1)
    key = np.round(A * 1e5).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    # keep vertices in first-use order so the index buffer stays local
    order = np.argsort(first); remap = np.empty_like(order); remap[order] = np.arange(len(order))
    V = A[first[order]]
    idx = remap[inv.reshape(-1)].reshape(-1, 3)
    idx = idx[(idx[:, 0] != idx[:, 1]) & (idx[:, 1] != idx[:, 2]) & (idx[:, 0] != idx[:, 2])].reshape(-1)   # drop triangles collapsed at poles
    out = {'position': V[:, 0:3], 'normal': V[:, 3:6], 'index': idx}
    if s.tuv is not None: out['uv'] = V[:, 6:8]
    return out


# ------------------------------------------------------------------ classify the fixed parts
TEXTILE = {'carpet', 'rug0', 'rug1', 'rug2', 'sadu', 'curtain', 'hay', 'cushion'}
WALLS = {'wool', 'blocks', 'sheet'}


def target(p):
    m = p['mat']
    if m['map'] in ('penFloor', 'track'): return 'decal'
    if m['transparent'] and m['map'] is None and abs(m['opacity'] - 0.16) < 1e-6: return 'decal'
    if m['transparent'] and abs(m['opacity'] - 0.32) < 1e-6: return 'glass'
    if m['map'] in TEXTILE: return 'textiles'
    if m['map'] in WALLS: return 'walls'
    if m['map'] == 'mesh': return 'panels'
    assert m['map'] is None, m['map']
    return 'palette'


def region(p): return 'camp' if p['cx'] < -120 and p['cz'] > 150 else 'yard'


stats = {'ground_faces_removed': 0, 'rail_cap_tris_removed': 0, 'backfaces_added': 0}
groups = {}            # (region, target) -> list of (soup, extra)
palette_keys = {}      # key -> cell
palette_cells = []


def pal_cell(color, rough, metal, emis):
    key = (tuple(np.round(color, 4)), round(rough, 3), round(metal, 3), tuple(np.round(emis, 4)))
    if key not in palette_keys:
        palette_keys[key] = len(palette_cells); palette_cells.append(key)
    return palette_keys[key]


def add(reg, tgt, soup, **extra):
    groups.setdefault((reg, tgt), []).append((soup, extra))


for p in d['parts']:
    tgt, reg, m = target(p), region(p), p['mat']
    index = None
    prm = p.get('params') or {}
    if p['geoType'] == 'CylinderGeometry' and prm.get('radiusTop') == 0.028 and prm.get('radialSegments') == 6:
        g0 = p['groups'][0]; index = p['idx'][g0['start']:g0['start'] + g0['count']]   # pen rails: the end caps sit inside the posts
        stats['rail_cap_tris_removed'] += (len(p['idx']) - len(index)) // 3
    s = Soup.from_part(p, index)
    if tgt in ('palette', 'textiles', 'walls'):
        s, n = s.drop_ground_bottoms(); stats['ground_faces_removed'] += n
        if m['side'] == 2:                     # double-sided cloth/curtain/tent: give it real back faces
            stats['backfaces_added'] += len(s); s = cat([s, s.flipped()])
    if tgt == 'palette':
        emis = np.minimum(np.array(m['emissive']) * m['emissiveIntensity'], 1.0)
        add(reg, tgt, s, cell=pal_cell(m['color'], m['roughness'], m['metalness'], emis), name=p['name'])
    elif tgt == 'decal':
        kind = m['map'] or 'dirt'
        add('ground', 'decal', s, kind=kind)
    elif tgt == 'glass':
        add('ground', 'decal', s, kind='glass', mat=m)
    else:
        add(reg, tgt, s, tex=m['map'])

# tent ropes (1-px lines in the prototype): thin 3-sided cords
rope_cell = pal_cell(d['lines']['color'], 1.0, 0.0, [0, 0, 0])
L = np.array(d['lines']['pos']).reshape(-1, 2, 3)
for a, b in L:
    dvec = b - a; ln = np.linalg.norm(dvec); dd = dvec / ln
    t = np.cross(dd, [0, 1, 0]); t /= np.linalg.norm(t); w = np.cross(dd, t)
    k = 3; r = 0.012
    dirs = [math.cos(2 * math.pi * i / k) * t + math.sin(2 * math.pi * i / k) * w for i in range(k)]
    tp, tn = [], []
    for i in range(k):
        j = (i + 1) % k
        A, B, C, D = a + r * dirs[i], b + r * dirs[i], b + r * dirs[j], a + r * dirs[j]
        for tri, nn in (([A, B, C], [dirs[i], dirs[i], dirs[j]]), ([A, C, D], [dirs[i], dirs[j], dirs[j]])):
            fn = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            if np.dot(fn, (dirs[i] + dirs[j])) < 0: tri = [tri[0], tri[2], tri[1]]; nn = [nn[0], nn[2], nn[1]]
            tp.append(tri); tn.append(nn)
    add('yard', 'palette', Soup(tp, tn), cell=rope_cell, name='rope')
# hay on the feed pickup (a child of the vehicle in the prototype; static here)
hay_cell = pal_cell(d['hayColor'], 1.0, 0.0, [0, 0, 0])
for g in d['hayBales']:
    add('yard', 'palette', Soup.from_part(g), cell=hay_cell, name='pickup_hay')

# ------------------------------------------------------------------ palette textures (4 px cells)
ncell = len(palette_cells); per_row = 8; cs = 4
rows = math.ceil(ncell / per_row); PW, PH = per_row * cs, max(1, rows) * cs
PH = 1 << (PH - 1).bit_length()
pal_base = np.zeros((PH, PW, 4), np.uint8); pal_base[..., 3] = 255
pal_mr = np.zeros((PH, PW, 4), np.uint8); pal_mr[..., 0] = 255; pal_mr[..., 3] = 255
pal_em = np.zeros((PH, PW, 4), np.uint8); pal_em[..., 3] = 255
for i, (col, rough, metal, emis) in enumerate(palette_cells):
    x, y = (i % per_row) * cs, (i // per_row) * cs
    pal_base[y:y + cs, x:x + cs, :3] = srgb8(col)
    pal_mr[y:y + cs, x:x + cs, 1] = round(rough * 255); pal_mr[y:y + cs, x:x + cs, 2] = round(metal * 255)
    pal_em[y:y + cs, x:x + cs, :3] = srgb8(emis)
pal_has_emissive = bool(pal_em[..., :3].any())


def pal_uv(cell):
    return ((cell % per_row) * cs + cs / 2) / PW, ((cell // per_row) * cs + cs / 2) / PH


# ------------------------------------------------------------------ textiles atlas (non-repeating, 8 px clamped gutters)
G = 8
TEX_RECTS = {'rug0': (G, G), 'rug1': (272 + G, G), 'rug2': (544 + G, G), 'carpet': (816 + G, G),
             'sadu': (G, 144 + G), 'curtain': (272 + G, 144 + G), 'hay': (544 + G, 144 + G), 'cushion': (G, 288 + G)}
TW, TH = 1024, 336


def padded(im, g, mode_x='clamp', mode_y='clamp'):
    a = np.array(im)
    a = np.pad(a, ((g, g), (0, 0), (0, 0)), mode='edge' if mode_y == 'clamp' else 'wrap')
    a = np.pad(a, ((0, 0), (g, g), (0, 0)), mode='edge' if mode_x == 'clamp' else 'wrap')
    return a


tex_atlas = np.zeros((TH, TW, 4), np.uint8); tex_atlas[..., 3] = 255
tex_size = {}
for name, (x, y) in TEX_RECTS.items():
    im = img(name)
    if name == 'cushion': im = Image.fromarray(np.tile(np.array(im), (1, 6, 1)))   # its 6x repeat, unrolled
    a = padded(im, G, 'wrap' if name == 'cushion' else 'clamp', 'clamp')
    h, w = a.shape[:2]
    tex_atlas[y - G:y - G + h, x - G:x - G + w] = a
    tex_size[name] = (im.width, im.height)


def textile_uv(name, uv):
    x, y = TEX_RECTS[name]; w, h = tex_size[name]
    u, v = uv[..., 0], uv[..., 1]
    if name == 'cushion': u = u / 6.0
    if u.min() < -1e-3 or u.max() > 1 + 1e-3 or v.min() < -1e-3 or v.max() > 1 + 1e-3:
        print('WARN textile uv out of tile', name, u.min(), u.max(), v.min(), v.max())
    u, v = np.clip(u, 0, 1), np.clip(v, 0, 1)
    return np.stack([(x + u * w) / TW, (y + (1 - v) * h) / TH], axis=-1)


# ------------------------------------------------------------------ walls atlas: full-width bands, u wraps in hardware
WW = 256
BANDS = {'wool': (G, 256, 'wrap'), 'blocks': (272 + G, 128, 'wrap'), 'sheet': (416 + G, 64, 'clamp')}
WH = 512   # bands use 496 rows; the rest repeats the sheet's last row
WALL_MR = {'wool': (1.0, 0.0), 'blocks': (0.92, 0.0), 'sheet': (0.55, 0.35)}
walls_atlas = np.zeros((WH, WW, 4), np.uint8); walls_atlas[..., 3] = 255
walls_mr = np.zeros((WH // 16, WW // 16, 4), np.uint8); walls_mr[..., 0] = 255; walls_mr[..., 3] = 255
for name, (y, h, mode) in BANDS.items():
    im = img(name); assert im.width == WW and im.height == h, (name, im.size)
    a = np.array(im); a = np.pad(a, ((G, G), (0, 0), (0, 0)), mode='wrap' if mode == 'wrap' else 'edge')
    walls_atlas[y - G:y - G + h + 2 * G] = a
    r, mtl = WALL_MR[name]
    walls_mr[(y - G) // 16:(y + h + G) // 16, :, 1] = round(r * 255); walls_mr[(y - G) // 16:(y + h + G) // 16, :, 2] = round(mtl * 255)
walls_mr[31:] = walls_mr[30]; walls_atlas[496:] = walls_atlas[495]


def walls_soup(s, name):
    y, h, mode = BANDS[name]
    if mode == 'wrap':
        s, k = s.clip_grid(1); vloc = s.tuv[..., 1] - k[:, None]
    else:
        vloc = s.tuv[..., 1]
        assert vloc.min() > -1e-3 and vloc.max() < 1 + 1e-3
    vloc = np.clip(vloc, 0, 1)
    uv = np.stack([s.tuv[..., 0], (y + (1 - vloc) * h) / WH], axis=-1)
    return Soup(s.tp, s.tn, uv)


# ------------------------------------------------------------------ ground decals atlas (512 x 512, v wraps in hardware)
DW = DH = 512
DCOL = {'asphalt': 0, 'track': 80, 'penFloor': 160, 'dirt': 432, 'shoulder': 448, 'glass': 464}
dec = np.zeros((DH, DW, 4), np.uint8)
a = np.array(img('asphalt')); assert a.shape[:2] == (512, 64)
dec[:, 0:80] = np.pad(a, ((0, 0), (G, G), (0, 0)), mode='edge')
a = np.array(img('track')); a = np.tile(a, (2, 1, 1)); dec[:, 80:160] = np.pad(a, ((0, 0), (G, G), (0, 0)), mode='edge')
a = np.array(img('penFloor')); a = np.tile(a, (2, 1, 1)); dec[:, 160:432] = np.pad(a, ((0, 0), (G, G), (0, 0)), mode='wrap')
dirt_mat = [p['mat'] for p in d['parts'] if target(p) == 'decal' and p['mat']['map'] is None][0]
glass_mat = [p['mat'] for p in d['parts'] if target(p) == 'glass'][0]
SHOULDER = {'color': '#a98463', 'opacity': 0.35}   # world.js: the road shoulder (draped, regenerated here)
def hex_lin(h):
    c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
for name, col, alpha in (('dirt', dirt_mat['color'], dirt_mat['opacity']), ('shoulder', hex_lin(SHOULDER['color']), SHOULDER['opacity']),
                         ('glass', glass_mat['color'], glass_mat['opacity'])):
    x = DCOL[name]; dec[:, x:x + 16, :3] = srgb8(col); dec[:, x:x + 16, 3] = round(alpha * 255)
dec_mr = np.zeros((DH // 16, DW // 16, 4), np.uint8); dec_mr[..., 0] = 255; dec_mr[..., 1] = 255; dec_mr[..., 3] = 255
dec_mr[:, 0:5, 1] = round(0.92 * 255)                                   # asphalt
dec_mr[:, DCOL['glass'] // 16, 1] = round(glass_mat['roughness'] * 255); dec_mr[:, DCOL['glass'] // 16, 2] = round(glass_mat['metalness'] * 255)


def solid_uv(name, n):
    return np.tile([[(DCOL[name] + 8) / DW, 0.5]], (n, 3, 1))


def drape_rect(x0, x1, z0, z1, off):
    """the rectangle cut into the facets of the finest terrain ring under it, raised by off"""
    tp, tn = [], []
    for ring, xa, xb in ((T.mid, x0, -2000.0), (T.near, -2000.0, 2000.0), (T.mid, 2000.0, x1)):
        xa, xb = max(xa, x0), min(xb, x1)
        if xb <= xa: continue
        i0, i1 = int((xa - ring.x0) // ring.dx), int(math.ceil((xb - ring.x0) / ring.dx))
        j0, j1 = int((z0 - ring.z0) // ring.dz), int(math.ceil((z1 - ring.z0) / ring.dz))
        for j in range(j0, j1):
            for i in range(i0, i1):
                for tri in ring.tri_by_cell[j * ring.nx + i]:
                    A = ring.P[tri]; NA = ring.Nrm[tri]
                    poly = [(xa, z0), (xb, z0), (xb, z1), (xa, z1)]
                    tri2 = A[:, [0, 2]]
                    e1, e2 = tri2[1] - tri2[0], tri2[2] - tri2[0]; sgn = np.sign(e1[0] * e2[1] - e1[1] * e2[0])
                    for e in range(3):
                        p, q = tri2[e], tri2[(e + 1) % 3]
                        f = lambda v: sgn * ((q[0] - p[0]) * (v[1] - p[1]) - (q[1] - p[1]) * (v[0] - p[0]))
                        res = []
                        for k in range(len(poly)):
                            a_, b_ = poly[k], poly[(k + 1) % len(poly)]
                            fa, fb = f(a_), f(b_)
                            if fa >= -1e-9: res.append(a_)
                            if (fa >= -1e-9) != (fb >= -1e-9):
                                s = fa / (fa - fb); res.append((a_[0] + (b_[0] - a_[0]) * s, a_[1] + (b_[1] - a_[1]) * s))
                        poly = res
                        if len(poly) < 3: break
                    if len(poly) < 3: continue
                    # barycentric height and normal from the facet
                    M = np.array([[tri2[1][0] - tri2[0][0], tri2[2][0] - tri2[0][0]], [tri2[1][1] - tri2[0][1], tri2[2][1] - tri2[0][1]]])
                    Minv = np.linalg.inv(M)
                    def lift(v):
                        bu, bv = Minv @ (np.array(v) - tri2[0]); bw = 1 - bu - bv
                        y = bw * A[0, 1] + bu * A[1, 1] + bv * A[2, 1]
                        n = bw * NA[0] + bu * NA[1] + bv * NA[2]
                        return np.array([v[0], y + off, v[1]]), n / np.linalg.norm(n)
                    L_ = [lift(v) for v in poly]
                    for k in range(1, len(L_) - 1):
                        t3 = [L_[0], L_[k], L_[k + 1]]
                        P3 = np.array([t[0] for t in t3]); N3 = np.array([t[1] for t in t3])
                        fn = np.cross(P3[1] - P3[0], P3[2] - P3[0])
                        if np.linalg.norm(fn) < 1e-8: continue
                        if fn[1] < 0: P3 = P3[[0, 2, 1]]; N3 = N3[[0, 2, 1]]
                        tp.append(P3); tn.append(N3)
    return Soup(tp, tn)


decal_soups = []
by_kind = {}
for s, ex in groups.pop(('ground', 'decal')):
    by_kind.setdefault(ex['kind'], []).append(s)
lift_y = lambda s, y: Soup(np.concatenate([s.tp[..., :1], (np.full(s.tp.shape[:2], y) + T.near.height(s.tp[..., 0].ravel(), s.tp[..., 2].ravel()).reshape(s.tp.shape[:2]))[..., None], s.tp[..., 2:]], axis=-1), s.tn, s.tuv)
# 1 compound dirt (0.02)
for s in by_kind['dirt']:
    s = lift_y(s, 0.02); decal_soups.append(Soup(s.tp, s.tn, solid_uv('dirt', len(s))))
# 2 pen floors (0.03): unroll the 6 m repeat across u, v wraps in hardware
for s in by_kind['penFloor']:
    s = lift_y(s, 0.03); s, k = s.clip_grid(0)
    u = s.tuv[..., 0] - k[:, None]
    uv = np.stack([(DCOL['penFloor'] + G + np.clip(u, 0, 1) * 256) / DW, (1 - s.tuv[..., 1]) * 0.5], axis=-1)
    decal_soups.append(Soup(s.tp, s.tn, uv))
# 3 road shoulder (draped, 0.05)
sh = drape_rect(-3000, 3000, ROADZ - 7.5, ROADZ + 7.5, 0.05)
decal_soups.append(Soup(sh.tp, sh.tn, solid_uv('shoulder', len(sh))))
n_shoulder = len(sh)
# 4 tracks (0.06, above the shoulder they cross)
for s in by_kind['track']:
    s = lift_y(s, 0.06)
    uv = np.stack([(DCOL['track'] + G + np.clip(s.tuv[..., 0], 0, 1) * 64) / DW, (1 - s.tuv[..., 1]) * 0.5], axis=-1)
    decal_soups.append(Soup(s.tp, s.tn, uv))
# 5 asphalt road (draped, 0.08): u across 9 m, the 40 m texture repeat along x
rd = drape_rect(-3000, 3000, ROADZ - 4.5, ROADZ + 4.5, 0.08)
u = (ROADZ + 4.5 - rd.tp[..., 2]) / 9.0; v = (3000 - rd.tp[..., 0]) / 40.0
decal_soups.append(Soup(rd.tp, rd.tn, np.stack([(G + np.clip(u, 0, 1) * 64) / DW, 1 - v], axis=-1)))
n_road = len(rd)
# 6 the room's glass front, last
for s in by_kind['glass']:
    decal_soups.append(Soup(s.tp, s.tn, solid_uv('glass', len(s))))

# ------------------------------------------------------------------ assemble per region
prims = {}
for (reg, tgt), lst in sorted(groups.items()):
    soups = []
    for s, ex in lst:
        if tgt == 'palette':
            soups.append(Soup(s.tp, s.tn, np.tile([pal_uv(ex['cell'])], (len(s), 3, 1))))
        elif tgt == 'textiles':
            soups.append(Soup(s.tp, s.tn, textile_uv(ex['tex'], s.tuv)))
        elif tgt == 'walls':
            soups.append(walls_soup(s, ex['tex']))
        elif tgt == 'panels':
            soups.append(Soup(s.tp, s.tn, np.stack([s.tuv[..., 0], 1 - s.tuv[..., 1]], axis=-1)))
    prims[(reg, tgt)] = cat(soups)
prims[('ground', 'decal')] = cat(decal_soups)

# ------------------------------------------------------------------ write yard.glb
W = GLBWriter()
tex_report = []


def texture(arr_or_img, mime, sampler, label, mip=True):
    im = arr_or_img if isinstance(arr_or_img, Image.Image) else Image.fromarray(arr_or_img)
    data = png_bytes(im) if mime == 'image/png' else jpg_bytes(im)
    i = W.add_image(data, mime); W.js['images'][i]['name'] = label
    tex_report.append((label, im.width, im.height, len(data), im.width * im.height * 4 * (4 / 3 if mip else 1)))
    return W.add_texture(i, sampler)


S_PAL = {'magFilter': NEAREST, 'minFilter': NEAREST, 'wrapS': CLAMP, 'wrapT': CLAMP}
S_ATLAS = {'magFilter': LINEAR, 'minFilter': LIN_MIP, 'wrapS': CLAMP, 'wrapT': CLAMP}
S_WALLS = {'magFilter': LINEAR, 'minFilter': LIN_MIP, 'wrapS': REPEAT, 'wrapT': CLAMP}
S_REP = {'magFilter': LINEAR, 'minFilter': LIN_MIP, 'wrapS': REPEAT, 'wrapT': REPEAT}
S_DEC = {'magFilter': LINEAR, 'minFilter': LIN_MIP, 'wrapS': CLAMP, 'wrapT': REPEAT}
S_LOWMR = {'magFilter': LINEAR, 'minFilter': LINEAR, 'wrapS': CLAMP, 'wrapT': REPEAT}
S_LOWMR_W = {'magFilter': LINEAR, 'minFilter': LINEAR, 'wrapS': REPEAT, 'wrapT': CLAMP}

mat = {}
pal = {'name': 'yard_palette', 'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(pal_base, 'image/png', S_PAL, 'palette_base', False)},
       'metallicRoughnessTexture': {'index': texture(pal_mr, 'image/png', S_PAL, 'palette_mr', False)}, 'metallicFactor': 1, 'roughnessFactor': 1},
       'extras': {'note': 'every untextured object; each samples one 4 px palette cell'}}
if pal_has_emissive:
    pal['emissiveTexture'] = {'index': texture(pal_em, 'image/png', S_PAL, 'palette_emissive', False)}; pal['emissiveFactor'] = [1, 1, 1]
mat['palette'] = W.add_material(pal)
mat['textiles'] = W.add_material({'name': 'yard_textiles', 'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(tex_atlas, 'image/jpeg', S_ATLAS, 'textiles_atlas')},
                                  'metallicFactor': 0, 'roughnessFactor': 1}})
mat['walls'] = W.add_material({'name': 'yard_walls', 'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(walls_atlas, 'image/jpeg', S_WALLS, 'walls_atlas')},
                               'metallicRoughnessTexture': {'index': texture(walls_mr, 'image/png', S_LOWMR_W, 'walls_mr', False)}, 'metallicFactor': 1, 'roughnessFactor': 1}})
mesh_im = img('mesh')
mat['panels'] = W.add_material({'name': 'yard_mesh_panels', 'alphaMode': 'MASK', 'alphaCutoff': 0.4, 'doubleSided': True,
                                'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(mesh_im, 'image/png', S_REP, 'mesh_panel')}, 'metallicFactor': 0.7, 'roughnessFactor': 0.45}})
mat['decal'] = W.add_material({'name': 'ground_decals', 'alphaMode': 'BLEND',
                               'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(dec, 'image/png', S_DEC, 'decals_atlas')},
                                                        'metallicRoughnessTexture': {'index': texture(dec_mr, 'image/png', S_LOWMR, 'decals_mr', False)}, 'metallicFactor': 1, 'roughnessFactor': 1},
                               'extras': {'depthWrite': False, 'depthLayer': 1, 'drawOrder': 'triangles are ordered bottom to top: compound dirt, pen floors, road shoulder, tracks, asphalt, the room glass',
                                          'note': 'lies 2-8 cm above terrain.glb; give it a depth bias / depthLayer over the terrain (the prototype used polygonOffset)'}})

report = {'primitives': []}
node_specs = [('yard', 'yard', ['palette', 'textiles', 'walls', 'panels'], True),
              ('ground_decals', 'ground', ['decal'], False),
              ('camp', 'camp', ['palette', 'textiles', 'walls', 'panels'], True)]
for node_name, reg, tgts, cast in node_specs:
    plist = []
    for tgt in tgts:
        if (reg, tgt) not in prims: continue
        ix = to_indexed(prims[(reg, tgt)])
        plist.append({'position': ix['position'], 'normal': ix['normal'], 'uv': ix['uv'], 'index': ix['index'], 'material': mat[tgt]})
        report['primitives'].append({'node': node_name, 'material': W.js['materials'][mat[tgt]]['name'], 'triangles': len(ix['index']) // 3, 'vertices': len(ix['position'])})
    mi = W.add_mesh(node_name, plist)
    W.add_node({'name': node_name, 'mesh': mi, 'extras': {'castShadow': cast, 'receiveShadow': True}})
W.js['asset']['extras'] = {'frame': 'x east, y up, z south, metres from the yard (same as terrain.glb)', 'source': 'prototype world.js buildWorld(), fixed objects only'}
size = W.write(os.path.join(OUT, 'yard.glb'))
report['file_bytes'] = size
report['materials'] = len(W.js['materials'])
report['triangles'] = sum(p['triangles'] for p in report['primitives'])
report['vertices'] = sum(p['vertices'] for p in report['primitives'])
report['textures'] = [{'name': n, 'w': w, 'h': h, 'bytes': b, 'gpu_bytes': int(g)} for n, w, h, b, g in tex_report]
report['texture_gpu_mib'] = round(sum(t[4] for t in tex_report) / 2 ** 20, 2)
report['palette_cells'] = ncell
report['stats'] = stats
report['decal_tris'] = {'shoulder': n_shoulder, 'road': n_road}

# ------------------------------------------------------------------ scatter: one small GLB per kind + compact instances
SC = d['scatter']
scatter_tex = {'grass': SC['grass']['mat']['map'], 'bush': SC['bush']['mat']['map'], 'tamarisk_clump': SC['tamarisk_clump']['mat']['map']}
GLB_NAME = {'grass': 'grass_tuft.glb', 'bush': 'bush.glb', 'stone': 'stone.glb', 'tamarisk_clump': 'tamarisk_clump.glb', 'tamarisk_trunk': 'tamarisk_trunk.glb'}
scatter_report = {}
for kind, fname in GLB_NAME.items():
    g, m = SC[kind]['geo'], SC[kind]['mat']
    w = GLBWriter()
    P = np.array(g['pos'], float).reshape(-1, 3); N = np.array(g['nor'], float).reshape(-1, 3)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    UV = np.array(g['uv'], float).reshape(-1, 2) if g['uv'] is not None else None
    I = np.array(g['idx'], int)
    material = {'name': kind, 'pbrMetallicRoughness': {'metallicFactor': float(m['metalness']), 'roughnessFactor': float(m['roughness'])}}
    gpu = 0
    if m['map']:
        im = img(m['map']); data = png_bytes(im)
        ii = w.add_image(data, 'image/png'); w.js['images'][ii]['name'] = kind
        material['pbrMetallicRoughness']['baseColorTexture'] = {'index': w.add_texture(ii, S_REP)}
        material.update({'alphaMode': 'MASK', 'alphaCutoff': float(m['alphaTest']), 'doubleSided': True})
        UV = np.stack([UV[:, 0], 1 - UV[:, 1]], axis=1)
        gpu = im.width * im.height * 4 * 4 / 3
    else:
        material['pbrMetallicRoughness']['baseColorFactor'] = [float(c) for c in m['color']] + [1.0]
        UV = None
    material['extras'] = {'instanceTint': 'multiply baseColor by the per-instance tint in yard_scatter.json'} if kind != 'tamarisk_trunk' else {}
    mi = w.add_material(material)
    msh = w.add_mesh(kind, [{'position': P, 'normal': N, 'uv': UV, 'index': I, 'material': mi}])
    w.add_node({'name': kind, 'mesh': msh})
    w.js['asset']['extras'] = {'frame': 'x east, y up, z south, metres; origin at the base of the instance'}
    sz = w.write(os.path.join(OUT, fname))
    scatter_report[kind] = {'glb': fname, 'bytes': sz, 'triangles': len(I) // 3, 'texture_gpu_bytes': int(gpu)}

r2 = lambda v: round(float(v), 2)
r3 = lambda v: round(float(v), 3)
wrap = lambda a: (a + math.pi) % (2 * math.pi) - math.pi
out = {'frame': 'x east, y up, z south, metres from the yard; yaw = rotation about +y in radians (glTF/three.js sense: +yaw turns +x toward -z)',
       'tint': 'linear RGB multiplier of the base colour (texture x tint), as glTF baseColorFactor',
       'distance': 'd = hypot(cam.x - cell.x, cam.z - cell.z, cam.y * 0.5); draw the first round(n * share) instances of a cell, share = the first band with d < band distance, none past the last band',
       'kinds': {}}
for kind in ('grass', 'bush', 'stone'):
    K = SC[kind]
    ys = {round(i[1], 4) for c in K['cells'] for i in c['inst']}
    assert len(ys) == 1, (kind, ys)
    rows, cells, start = [], [], 0
    for c in K['cells']:
        cells.append([r2(c['x']), r2(c['z']), start, c['n']]); start += c['n']
        for (x, y, z, yaw, sx, sy, sz, qx, qy, qz, qw, cr, cg, cb) in c['inst']:
            assert abs(sx - sz) < 1e-4
            if kind == 'stone':
                assert abs(sx - sy) < 1e-4
                rows += [r2(x), r2(z), r3(wrap(yaw)), r3(sx), r3(cr), r3(cg), r3(cb)]
            else:
                rows += [r2(x), r2(z), r3(wrap(yaw)), r3(sx), r3(sy), r3(cr), r3(cg), r3(cb)]
    fields = ['x', 'z', 'yaw', 'scale', 'r', 'g', 'b'] if kind == 'stone' else ['x', 'z', 'yaw', 'scale_xz', 'scale_y', 'r', 'g', 'b']
    out['kinds'][kind] = {'glb': GLB_NAME[kind], 'count': start, 'y': ys.pop(), 'fields': fields, 'cell_size': {'grass': 25, 'bush': 80, 'stone': 25}[kind],
                          'cells_fields': ['x', 'z', 'first', 'count'], 'cells': cells, 'bands': K['bands'],
                          'cast_shadow': ('when d < %g' % K['shadowDist']) if K['cast'] else False, 'data': rows}
for kind in ('tamarisk_trunk', 'tamarisk_clump'):
    K = SC[kind]; rows = []
    for inst in K['inst']:
        x, y, z, qx, qy, qz, qw, sx, sy, sz = inst[:10]
        assert abs(sx - sz) < 1e-4
        rows += [r2(x), r2(y), r2(z), round(qx, 4), round(qy, 4), round(qz, 4), round(qw, 4), r3(sx), r3(sy)]
        if kind == 'tamarisk_clump': rows += [r3(v) for v in inst[10:13]]
    fields = ['x', 'y', 'z', 'qx', 'qy', 'qz', 'qw', 'scale_xz', 'scale_y'] + (['r', 'g', 'b'] if kind == 'tamarisk_clump' else [])
    out['kinds'][kind] = {'glb': GLB_NAME[kind], 'count': len(K['inst']), 'fields': fields, 'always_drawn': True, 'cast_shadow': True, 'data': rows}
js = json.dumps(out, separators=(',', ':'))
open(os.path.join(OUT, 'yard_scatter.json'), 'w').write(js)
report['scatter'] = scatter_report
report['scatter_json_bytes'] = len(js)

# ------------------------------------------------------------------ vehicles.json
models = {m: 'assets_src/vehicles/%s_mobile.glb' % m for m in ('shas', 'suv', 'tractor', 'caravan')}
veh = []
names = {0: 'shas_car_shade', 1: 'suv_car_shade', 2: 'shas_feed'}
for i, v in enumerate(d['vehicles']):
    e = {'id': names.get(i, 'vehicle%d' % i), 'model': v['model'], 'position': [v['x'], 0.0, v['z']], 'yaw': round(v['yaw'], 6)}
    e['tint'] = {'srgb': v['tint'], 'linear': v['tintLinear']} if v['tint'] else None
    if v['hay']: e['cargo'] = '3 hay bales on the bed, baked into yard.glb (node yard, palette)'
    veh.append(e)
R = d['rig']
for k in ('caravan', 'tractor'):
    veh.append({'id': k + '_camp', 'model': k, 'position': [round(R[k]['x'], 4), 0.0, round(R[k]['z'], 4)], 'yaw': round(R[k]['yaw'], 6), 'tint': None, 'rig': 'camp_rig'})
vj = {'frame': out['frame'], 'models': models,
      'model_note': 'paths are relative to the repository root; the prototype loads the same bytes (veh_<model>.json)',
      'tint': 'when set, replaces the base colour factor of every material of that model instance (the textures stay)',
      'vehicles': veh,
      'rigs': {'camp_rig': {'note': 'the shepherd caravan on its flatbed coupled to the tractor unit, at the grazing camp', 'position': [R['rig']['x'], 0.0, R['rig']['z']], 'yaw': R['rig']['yaw'],
                            'children': [{'model': 'caravan', 'local_position': [0, 0, 0]}, {'model': 'tractor', 'local_position': R['tractorLocal']}]}},
      'not_here': 'the water tanker by the tank (37.2, 0, -30) is procedural and is part of yard.glb'}
open(os.path.join(OUT, 'vehicles.json'), 'w').write(json.dumps(vj, indent=1))
json.dump(report, open(os.path.join(os.path.dirname(EXP), 'report.json'), 'w'), indent=1)
print(json.dumps(report, indent=1))

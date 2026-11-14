#!/usr/bin/env python3
"""T12 reviewer: measure a canid GLB (wolf / guard dog / stray) without Blender. numpy + scipy (blendenv python).

usage: blendenv/bin/python -I canid_check.py file.glb [more.glb ...] [--ref wolf|guard|stray] [--pose stand|stalk|lie|bark|other]
                                              [--json out.json]

Per file
  - draws (primitives), triangles, vertices, materials (one-sided? alpha? count), textures (size, memory RGBA8+mips),
    flags per primitive: open edges, non-manifold, zero-area, double-sided, alpha, UV outside 0..1, no normals,
    skins/animations/morphs (none expected now), external URIs, extensions.
  - frame: glTF Y up; forward = the horizontal axis with the larger extent, signed so the nose point (or the end with
    the head) is +; lateral = the other horizontal axis.
  - named points present vs the brief's list (feet x4, hips, shoulders, neck base, head, jaw, tail base, collar ring
    for the guard dog), by regex, with their world positions.
  - ground: lowest vertex overall, and the lowest vertex near each foot point (within 60 mm horizontally): each must
    be 0 +- 2 mm for a standing pose (all four on the ground) -- 'lie' checks body contact instead.
  - sizes (mm): overall height (ear tip), withers height (top of the mesh in a 30 mm slab at the withers/shoulder
    point's forward place; also the top-line profile every 50 mm), nose-to-tail-base length (forward extent from the
    tail base point to the nose tip), tail length (tail base point to the farthest tail vertex), chest depth and the
    leg clearance (bottom of the body in a slab behind the elbows, 25 % of the way from the fore to the hind feet),
    chest width at the same slab, head length (nose tip to the occiput ~ the ear bases' rear), muzzle (nose tip to eye),
    ear height (ear base point to the highest vertex near it).
  - ratios that tell a wolf from a dog/jackal (see REF and NOTES.md for each figure's source).
  - mirror symmetry: each vertex mirrored across the sagittal plane (fitted as the lateral midpoint of the feet and
    points), nearest-neighbour distance to the mesh's vertices: median / p95 / max mm, split front/back half.
Checks against REF print 'ok' / 'OUT' / 'n/a'.
"""
import sys, os, re, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb, accessor, png_size
from bird_check import world_nodes, closed_check

# ---------------------------------------------------------------------------------------------------- reference
# (low, high) pass bands, mm or ratio. Sources and how sure: NOTES.md / the phase-1 report.
REF = {
    'wolf': dict(
        withers=(600, 700),          # 64-66 cm avg (en.wp citing UKWCT, opened); ar.wp ~66; Indian wolf 57-72 (CZA)
        body_len=(850, 1100),        # nose to tail base: NO arabs figure found. Indian wolf nose-to-tail-tip 103-145 cm
                                     # minus tail 29-40 => ~75-110; general wolf 105-160 total (Heptner). Reviewer band.
        tail=(290, 480),             # general wolf 29-50 cm (Heptner); photo Al Ain 2 (winter, with hair) 0.72 x withers
        skull_or_head=(180, 260),    # skull ~20 cm (Walker 2008 via en.wp); the head with skin a little longer
        ear=(85, 130),               # northern 90-110 mm (Heptner); arabs 'proportionally larger' (Mills 1945): same or
                                     # a little larger in mm on a smaller head
        leg_over_chest=(0.9, 1.25),  # reviewer-measured on 3 side photos: 1.08 (TAzooAnimal11), 1.08 (Al Ain 2), 1.03 (Dhofar)
        len_over_withers=(1.4, 1.75),# nose to tail base / withers: 1.62 (Al Ain 2, head out), ~1.5 (TAzooAnimal11, 3/4 view)
        depth_over_withers=(0.42, 0.55),  # chest depth / withers: 0.48 (Al Ain 2), 0.48 (TAzoo11), 0.49 (Dhofar)
        ear_over_head=(0.40, 0.65),  # northern ~0.38-0.45 (90-110 / 230-280 mm); arabs larger
        tail_tip_vs_hock=(-120, 80), # tail hangs to about the hock (tip height minus hock height, mm), straight, not curled
    ),
    'guard': dict(
        withers=(450, 650),          # local pariah/Canaan type 45-60 cm (en.wp Canaan, opened); a Kangal type would be
                                     # 63-80 (FCI via en.wp) -- the band follows the type the worker proposes; re-set then
        leg_over_chest=(0.8, 1.25),
    ),
    'stray': dict(withers=(420, 620), leg_over_chest=(0.8, 1.3)),
}
POINTS = {
    'foot_fl': r'(paw|foot|sole).*(f|fore).*l|(fl|lf).*(paw|foot)|paw_fl|foot_fl|fore.*paw.*l',
    'foot_fr': r'(paw|foot|sole).*(f|fore).*r|(fr|rf).*(paw|foot)|paw_fr|foot_fr|fore.*paw.*r',
    'foot_hl': r'(paw|foot|sole).*(h|hind).*l|(hl|lh).*(paw|foot)|paw_hl|foot_hl|hind.*paw.*l',
    'foot_hr': r'(paw|foot|sole).*(h|hind).*r|(hr|rh).*(paw|foot)|paw_hr|foot_hr|hind.*paw.*r',
    'hips': r'^hips?$|pelvis|hip_[lr]', 'shoulders': r'shoulder|withers', 'neck_base': r'neck', 'head': r'^head',
    'jaw': r'jaw', 'tail_base': r'tail.*base|tail_0|tail_root|^tail$', 'collar_ring': r'collar|ring',
}

def load(path):
    js, b = read_glb(path); nodes, world, parent = world_nodes(js); meshes = js.get('meshes', [])
    prims, pts, V = [], {}, []
    for i, n in enumerate(nodes):
        if i not in world: continue
        W = world[i]
        if 'mesh' not in n:
            pts[n.get('name', f'#{i}')] = W[:3, 3].copy(); continue
        for p in meshes[n['mesh']]['primitives']:
            P = accessor(js, b, p['attributes']['POSITION']).astype(float); P = (W[:3, :3] @ P.T).T + W[:3, 3]
            I = accessor(js, b, p['indices']).ravel() if 'indices' in p else np.arange(len(P))
            uv = accessor(js, b, p['attributes']['TEXCOORD_0']).astype(float) if 'TEXCOORD_0' in p['attributes'] else None
            bd, nm, deg, zero = closed_check(P, I)
            prims.append(dict(node=n.get('name', ''), mesh=meshes[n['mesh']].get('name', ''), P=P, I=I.reshape(-1, 3),
                              tris=len(I) // 3, verts=len(P), mat=p.get('material'), attrs=sorted(p['attributes']),
                              boundary=bd, nonman=nm, zero=zero, targets=len(p.get('targets', [])), skin='skin' in n,
                              uvbad=None if uv is None else float(((uv < -1e-4) | (uv > 1 + 1e-4)).any(1).mean())))
            V.append(P)
    tex, mem = [], 0
    for k, im in enumerate(js.get('images', [])):
        sz = None
        if 'bufferView' in im:
            bv = js['bufferViews'][im['bufferView']]; sz = png_size(b[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
        if sz: mem += sz[0] * sz[1] * 4 * 4 / 3
        tex.append(dict(i=k, name=im.get('name'), mime=im.get('mimeType'), size=sz, uri='uri' in im))
    return js, prims, pts, np.vstack(V), tex, mem

def shells(P, I):
    """Connected pieces after welding by position; each piece's signed volume (mm3): negative = wound inside out."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    key = np.round(P / 1e-5).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    T = inv[I]; n = inv.max() + 1
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    tl = lab[T[:, 0]]
    vol = np.einsum('ij,ij->i', P[I[:, 0]], np.cross(P[I[:, 1]], P[I[:, 2]])) / 6 * 1e9
    return [(int(k), int((tl == k).sum()), float(vol[tl == k].sum())) for k in np.unique(tl)]

def find(pts, key):
    rx = re.compile(POINTS[key], re.I)
    return {k: v for k, v in pts.items() if rx.search(k)}

def slab(V, f, c, half):
    return V[np.abs(V[:, f] - c) <= half]

def report(path, ref=None, pose='stand'):
    js, prims, pts, V, tex, mem = load(path)
    out = dict(file=path, kib=os.path.getsize(path) / 1024)
    print(f'\n=== {path}  ({out["kib"]:.0f} KiB)  generator {js.get("asset", {}).get("generator")}')
    print(f'extensionsUsed {js.get("extensionsUsed", [])}  skins {len(js.get("skins", []))}  animations {len(js.get("animations", []))}')
    mats = js.get('materials', [])
    out.update(draws=len(prims), tris=sum(p['tris'] for p in prims), verts=sum(p['verts'] for p in prims), materials=len(mats),
               tex=[t['size'] for t in tex], texmem_mib=mem / 2**20)
    print(f'draws {out["draws"]}  triangles {out["tris"]}  vertices {out["verts"]}  materials {len(mats)}  '
          f'textures {[(t["name"], t["mime"], t["size"]) for t in tex]}  memory {out["texmem_mib"]:.2f} MiB (RGBA8+mips)')
    for p in prims:
        m = mats[p['mat']] if p['mat'] is not None else {}
        fl = []
        if p['boundary']: fl.append(f'OPEN {p["boundary"]}')
        if p['nonman']: fl.append(f'NONMANIFOLD {p["nonman"]}')
        if p['zero']: fl.append(f'zero-area {p["zero"]}')
        if m.get('doubleSided'): fl.append('DOUBLE-SIDED')
        if m.get('alphaMode', 'OPAQUE') != 'OPAQUE': fl.append('ALPHA ' + m['alphaMode'])
        if p['uvbad'] is None: fl.append('no UV')
        elif p['uvbad'] > 0: fl.append(f'UV out {p["uvbad"]*100:.1f}%')
        if 'NORMAL' not in p['attrs']: fl.append('no normals')
        if p['targets'] or p['skin']: fl.append('morph/skin')
        try:
            sh = shells(p['P'], p['I']); neg = [x for x in sh if x[2] < 0]
            fl.append(f'{len(sh)} shells' + (f', {len(neg)} INSIDE-OUT (tris {[x[1] for x in neg][:6]})' if neg else ''))
        except ImportError: pass
        print(f'  {p["node"][:24]:24s} tris {p["tris"]:6d} mat {m.get("name")!s:12s} {"; ".join(fl)}')
    for m in mats:
        pb = m.get('pbrMetallicRoughness', {})
        print(f'  material {m.get("name")}: baseTex {"baseColorTexture" in pb} mrTex {"metallicRoughnessTexture" in pb} '
              f'normal {"normalTexture" in m} occl {"occlusionTexture" in m} metal {pb.get("metallicFactor", 1)} '
              f'rough {pb.get("roughnessFactor", 1)} ext {list(m.get("extensions", {}))}')
        if pb.get('metallicFactor', 1) > 0.05 and 'metallicRoughnessTexture' not in pb: print('    !! fur material metallic (glTF default 1)')
    if any(t['uri'] for t in tex): print('  !! external image uri')
    # ---------------- frame
    ext = V.max(0) - V.min(0)
    f = 0 if ext[0] >= ext[2] else 2; l = 2 - f
    nose = next((v for k, v in pts.items() if re.search(r'nose|muzzle_tip|snout', k, re.I)), None)
    head = next((v for k, v in pts.items() if re.match(r'head', k, re.I)), nose)
    sgn = 1.0
    if head is not None and head[f] < V[:, f].mean(): sgn = -1.0
    Fw = V[:, f] * sgn; Up = V[:, 1]; Lt = V[:, l]
    F = lambda p: p[f] * sgn
    print(f'frame: forward = {"+-"[sgn < 0]}{"XYZ"[f]}, lateral {"XYZ"[l]}; extents mm fwd {ext[f]*1000:.0f} up {ext[1]*1000:.0f} lat {ext[l]*1000:.0f}')
    # ---------------- named points
    print('named points:', ', '.join(sorted(pts)) or '(none)')
    for key in POINTS:
        hit = find(pts, key)
        if key == 'collar_ring' and ref != 'guard': continue
        print(f'  {"have" if hit else "MISSING":7s} {key:12s} {list(hit)[:4]}')
    # ---------------- ground
    lo = V[:, 1].min() * 1000; print(f'lowest vertex {lo:+.2f} mm  ({"ok" if abs(lo) <= 2 else "OUT: not on the ground plane"})')
    feet = {}
    for key in ('foot_fl', 'foot_fr', 'foot_hl', 'foot_hr'):
        for name, p in find(pts, key).items():
            nb = V[np.hypot(V[:, f] - p[f], V[:, l] - p[l]) < 0.06]
            if len(nb): feet[name] = (nb[:, 1].min() * 1000, p)
    for name, (y, p) in feet.items():
        print(f'  foot {name:16s} lowest {y:+7.2f} mm  point at ({F(p)*1000:.0f} fwd, {p[1]*1000:.1f} up, {p[l]*1000:.0f} lat)'
              f'  {"ok" if abs(y) <= 2 or pose not in ("stand", "bark") else "OUT"}')
    # ---------------- sizes
    S = {}
    S['height'] = (V[:, 1].max() - V[:, 1].min()) * 1000
    wp = next((v for k, v in pts.items() if re.search(r'withers', k, re.I)), None)
    if wp is None:
        sh = find(pts, 'shoulders'); wp = np.mean(list(sh.values()), 0) if sh else None
    if wp is not None:
        s = slab(V, f, wp[f], 0.015); S['withers'] = (s[:, 1].max() - V[:, 1].min()) * 1000 if len(s) else None
    tb = next((v for k, v in pts.items() if re.search(POINTS['tail_base'], k, re.I)), None)
    tipF = Fw.max()
    if tb is not None:
        S['body_len'] = (tipF - F(tb)) * 1000
        behind = V[Fw < F(tb) - 0.01]
        if len(behind):
            d = np.linalg.norm(behind - tb, axis=1); S['tail'] = d.max() * 1000; tt = behind[d.argmax()]
            S['tail_tip_up'] = tt[1] * 1000
    hk = [v for k, v in pts.items() if re.search('hock', k, re.I)]
    if S.get('withers') and S.get('body_len'): S['len_over_withers'] = S['body_len'] / S['withers']
    if hk and 'tail_tip_up' in S: S['tail_tip_vs_hock'] = S['tail_tip_up'] - np.mean([h[1] for h in hk]) * 1000
    ff = [p for k in ('foot_fl', 'foot_fr') for p in find(pts, k).values()]; hf = [p for k in ('foot_hl', 'foot_hr') for p in find(pts, k).values()]
    if ff and hf:
        xf, xh = np.mean([F(p) for p in ff]), np.mean([F(p) for p in hf])
        el = [v for k, v in pts.items() if re.search('elbow', k, re.I)]
        xg = (np.mean([F(e) for e in el]) - 0.04) if el else xf + 0.25 * (xh - xf)
        s = V[np.abs(Fw - xg) <= 0.012]
        # the trunk only: drop leg vertices (lower 45 % of the slab spread laterally far out is not the trunk) --
        # take the vertices above the gap between the legs: the lowest vertex nearer the midline than 35 mm
        mid = np.median(Lt)
        trunk = s[np.abs(s[:, l] - mid) < 0.035]
        if len(trunk):
            top, bot = s[:, 1].max(), trunk[:, 1].min()
            S['chest_depth'] = (top - bot) * 1000; S['clearance'] = (bot - V[:, 1].min()) * 1000
            S['leg_over_chest'] = S['clearance'] / S['chest_depth']
            if S.get('withers'): S['depth_over_withers'] = S['chest_depth'] / S['withers']
            body = s[s[:, 1] > bot + 0.3 * (top - bot)]
            S['chest_width'] = (body[:, l].max() - body[:, l].min()) * 1000 if len(body) else None
            S['width_over_depth'] = S['chest_width'] / S['chest_depth'] if S.get('chest_width') else None
    ears = [v for k, v in pts.items() if re.search(r'ear', k, re.I) and not re.search('year', k, re.I)]
    if ears:
        hs = []
        for e in ears:
            nb = V[np.linalg.norm(V - e, axis=1) < 0.16]
            hs.append((nb[:, 1].max() - e[1]) * 1000)
        S['ear'] = float(np.mean(hs))
    eyes = [v for k, v in pts.items() if re.search(r'eye', k, re.I)]
    if eyes: S['muzzle'] = (tipF - np.mean([F(e) for e in eyes])) * 1000
    if ears: S['head_len'] = (tipF - min(F(e) for e in ears)) * 1000 + 30  # nose to ear base, + ~30 mm to the occiput (approx)
    if 'ear' in S and 'head_len' in S: S['ear_over_head'] = S['ear'] / S['head_len']
    if 'muzzle' in S and 'head_len' in S: S['muzzle_over_head'] = S['muzzle'] / S['head_len']
    print('sizes (mm / ratio):', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in S.items()})
    # top line every 50 mm
    edges = np.arange(Fw.min(), Fw.max(), 0.05)
    prof = [(round((e - Fw.min()) * 1000), round(Up[(Fw >= e) & (Fw < e + 0.05)].max() * 1000)) for e in edges if ((Fw >= e) & (Fw < e + 0.05)).any()]
    print('top line (mm from the tail end: top):', prof)
    if ref:
        for k, (a, b) in REF[ref].items():
            v = S.get('skull_or_head' == k and 'head_len' or k)
            print(f'  CHECK {k:18s} model {("%.2f" % v) if v is not None else "n/a":>8s}  ref {a}..{b}  '
                  f'{"n/a" if v is None else ("ok" if a <= v <= b else "OUT")}')
    # ---------------- symmetry
    try:
        from scipy.spatial import cKDTree
        cand = [p[l] for p in pts.values()]
        mid = np.median(cand) if cand else np.median(Lt)
        M = V.copy(); M[:, l] = 2 * mid - M[:, l]
        d, _ = cKDTree(V).query(M); d *= 1000
        half = Fw > np.median(Fw)
        print(f'mirror symmetry about lat={mid*1000:.1f} mm: median {np.median(d):.2f}  p95 {np.percentile(d, 95):.2f}  '
              f'max {d.max():.1f} mm   (front half p95 {np.percentile(d[half], 95):.2f}, back half p95 {np.percentile(d[~half], 95):.2f})')
        out['sym_p95'] = float(np.percentile(d, 95))
    except ImportError:
        print('(scipy missing: symmetry skipped)')
    out['sizes'] = S
    return out

if __name__ == '__main__':
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    files = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or not a[i - 1].startswith('--'))]
    res = [report(x, opt('--ref'), opt('--pose', 'stand')) for x in files]
    if opt('--json'): json.dump(res, open(opt('--json'), 'w'), default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o), indent=1)

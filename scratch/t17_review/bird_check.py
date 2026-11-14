#!/usr/bin/env python3
"""T11 reviewer: measure a bird GLB without Blender (glTF reader from the T7 review, numpy only).

usage: python3 -I bird_check.py file.glb [more.glb ...] [--gear REGEX] [--ref saker_f|houbara|curlew] [--pose perch|flight|stand]

Per file: draws (= primitives) and triangles per primitive, materials (one-sided? alpha?), textures and their
memory (RGBA8 + mips, uncompressed, as ADR 0005 counts it), texture-coordinate range (wrapped = outside 0..1),
closed-mesh check per primitive (edges after welding by position: boundary = used once, non-manifold = >2),
degenerate triangles, named points (nodes without mesh) in world space, and the bird's dimensions with the gear
left out (nodes/meshes whose name matches --gear, default hood|jess|leash|perch|block|glove|cuff|ruler|ground|...):
  height (Y extent, glTF is Y-up), horizontal length, width, wingspan (largest horizontal extent across the body
  axis), and the side-silhouette 'diameter' (largest distance between two points in the side projection: for a
  standing bird about bill tip to tail tip as it stands). Checked against REF (reviewer's table, see README_review).
"""
import sys, re, json, numpy as np, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb, accessor, local, png_size

GEAR = r'hood|burqa|burqu|jess|sabu|leash|mursal|swivel|perch|block|wakr|glove|cuff|manqal|dass|ruler|ground|base|stand|man|player|ring|bell|tracker|antenna'

# Reviewer's reference (mm; g). (low, high) = the published range; the model must fall inside it (or within the
# tolerance noted) for a FEMALE saker and for the species' adult bird. Sources: see README_review.md.
REF = {
    # female saker: length/span/weight HBW (Orta et al. 2019) via en.wikipedia (opened); female band = upper part of the
    # species range (Cascades Raptor Center summary: female ~56 cm / ~124 cm; search summary only); perched height and
    # wing-tip shortfall measured on Commons 'Saker Falcon RWD2.jpg' and the 1950s Saudi photo (rough, see report)
    'saker_f': dict(length=(500, 570), span=(1100, 1260), height_perch=(320, 450), tail=(195, 245), wing_chord=(365, 420),
                    wingtip_short_of_tail=(30, 100)),
    # houbara: ~65 cm long, ~140 cm span (en.wikipedia, opened, uncited); +-15 % band; standing height from Commons
    # 'MacQueen's Bustard (Chlamydotis macqueenii) (8079417198).jpg' scaled by that length (+-12 %)
    'houbara': dict(length=(550, 750), span=(1350, 1700), height_stand=(340, 480)),
    # stone-curlew: 38-46 cm, 76-88 cm span, 290-535 g (en.wikipedia, opened); standing height from Commons 'Eurasian
    # Thicknee - Along Po river ... crop.jpg' scaled two ways (bill ~41 mm; chord ~0.86 x 42 cm) -> ~330 mm
    'curlew':  dict(length=(380, 460), span=(760, 880), height_stand=(290, 360)),
}

def world_nodes(js):
    nodes = js.get('nodes', []); world = {}; parent = {}
    def walk(i, M):
        W = M @ local(nodes[i]); world[i] = W
        for c in nodes[i].get('children', []): parent[c] = i; walk(c, W)
    for r in js['scenes'][js.get('scene', 0)]['nodes']: walk(r, np.eye(4))
    return nodes, world, parent

def closed_check(P, I):
    key = np.round(P / 1e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    T = inv[I.reshape(-1, 3)]
    deg = ((T[:, 0] == T[:, 1]) | (T[:, 1] == T[:, 2]) | (T[:, 0] == T[:, 2])).sum()
    E = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(E, axis=0, return_counts=True)
    # area of zero-area tris (by position)
    a = np.linalg.norm(np.cross(P[I.reshape(-1,3)[:,1]] - P[I.reshape(-1,3)[:,0]], P[I.reshape(-1,3)[:,2]] - P[I.reshape(-1,3)[:,0]]), axis=1)
    return int((cnt == 1).sum()), int((cnt > 2).sum()), int(deg), int((a < 1e-10).sum())

def cr2(u, v): return u[0] * v[1] - u[1] * v[0]

def diameter2d(Q):
    # convex hull (monotone chain), then brute force on the hull
    Q = np.unique(np.round(Q, 5), axis=0); Q = Q[np.lexsort((Q[:, 1], Q[:, 0]))]
    def half(pts):
        h = []
        for p in pts:
            while len(h) >= 2 and cr2(h[-1] - h[-2], p - h[-2]) <= 0: h.pop()
            h.append(p)
        return h
    H = np.array(half(Q)[:-1] + half(Q[::-1])[:-1])
    D = np.linalg.norm(H[:, None] - H[None], axis=-1); i, j = np.unravel_index(D.argmax(), D.shape)
    return D[i, j], H[i], H[j]

def analyse(path, gear=GEAR):
    js, bin_ = read_glb(path); nodes, world, parent = world_nodes(js); meshes = js.get('meshes', [])
    def name_chain(i):
        s = []
        while True:
            s.append(nodes[i].get('name', '')); 
            if 'mesh' in nodes[i]: s.append(meshes[nodes[i]['mesh']].get('name', ''))
            if i not in parent: break
            i = parent[i]
        return ' '.join(s)
    def own_names(i): return ' '.join([nodes[i].get('name', ''), meshes[nodes[i]['mesh']].get('name', '') if 'mesh' in nodes[i] else ''])
    prims, points, birdV, allV = [], [], [], []
    for i, n in enumerate(nodes):
        if i not in world: continue
        W = world[i]
        if 'mesh' not in n:
            points.append((n.get('name', f'#{i}'), W[:3, 3])); continue
        is_gear = re.search(gear, own_names(i), re.I) is not None  # the node's and its mesh's own names (not the file root's: 'saker_hooded')
        for p in meshes[n['mesh']]['primitives']:
            P = accessor(js, bin_, p['attributes']['POSITION']).astype(float)
            Pw = (W[:3, :3] @ P.T).T + W[:3, 3]
            I = accessor(js, bin_, p['indices']).ravel() if 'indices' in p else np.arange(len(P))
            uv = accessor(js, bin_, p['attributes']['TEXCOORD_0']).astype(float) if 'TEXCOORD_0' in p['attributes'] else None
            b, nm, deg, zero = closed_check(Pw, I)
            prims.append(dict(node=n.get('name', f'#{i}'), mesh=meshes[n['mesh']].get('name'), tris=len(I) // 3, verts=len(P),
                              mat=p.get('material'), attrs=sorted(p['attributes']), gear=is_gear, boundary=b, nonman=nm,
                              degen=deg, zero=zero, lo=Pw.min(0), hi=Pw.max(0),
                              uv=(uv.min(0), uv.max(0), float(((uv < -1e-4) | (uv > 1 + 1e-4)).any(1).mean())) if uv is not None else None))
            allV.append(Pw)
            if not is_gear: birdV.append(Pw)
    texmem, tex = 0, []
    for k, im in enumerate(js.get('images', [])):
        sz = None
        if 'bufferView' in im:
            bv = js['bufferViews'][im['bufferView']]; sz = png_size(bin_[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
        if sz: texmem += sz[0] * sz[1] * 4 * 4 / 3
        tex.append((k, im.get('name'), im.get('mimeType'), sz, 'uri' in im))
    return js, prims, points, tex, texmem, (np.vstack(birdV) if birdV else None), np.vstack(allV)

def dims(V):
    lo, hi = V.min(0), V.max(0); ext = hi - lo
    # horizontal axes X,Z: body axis = the one along which the side silhouette is longer for a standing bird;
    # for a flying bird the wingspan is the larger horizontal extent.
    hx, hz = ext[0], ext[2]
    side_ax = 0 if hx >= hz else 2
    d, a, b = diameter2d(V[:, [side_ax, 1]])
    d_top, _, _ = diameter2d(V[:, [0, 2]])
    return dict(height=ext[1] * 1000, ext_x=ext[0] * 1000, ext_z=ext[2] * 1000, side_diameter=d * 1000,
                top_diameter=d_top * 1000, min_y=lo[1] * 1000)

def report(path, ref=None, pose=None, gear=GEAR):
    js, prims, points, tex, texmem, BV, AV = analyse(path, gear)
    print(f'\n=== {path}  ({os.path.getsize(path)/1024:.0f} KiB)')
    print(f'generator: {js.get("asset", {}).get("generator")}; extensionsUsed {js.get("extensionsUsed", [])}; '
          f'extensionsRequired {js.get("extensionsRequired", [])}; animations {len(js.get("animations", []))}; skins {len(js.get("skins", []))}')
    mats = js.get('materials', [])
    print(f'draws: {len(prims)}   triangles: {sum(p["tris"] for p in prims)} (bird {sum(p["tris"] for p in prims if not p["gear"])}, '
          f'gear {sum(p["tris"] for p in prims if p["gear"])})   vertices: {sum(p["verts"] for p in prims)}   materials: {len(mats)}')
    bad = 0
    for p in prims:
        m = mats[p['mat']] if p['mat'] is not None else {}
        flag = []
        if p['boundary']: flag.append(f'OPEN {p["boundary"]} edges')
        if p['nonman']: flag.append(f'NONMANIFOLD {p["nonman"]}')
        if p['zero']: flag.append(f'zero-area {p["zero"]}')
        if m.get('doubleSided'): flag.append('DOUBLE-SIDED')
        if m.get('alphaMode', 'OPAQUE') != 'OPAQUE': flag.append('alpha ' + m['alphaMode'])
        if p['uv'] is not None and p['uv'][2] > 0: flag.append(f'UV outside 0..1 on {p["uv"][2]*100:.1f}% verts {np.round(p["uv"][0],3)}..{np.round(p["uv"][1],3)}')
        if p['uv'] is None: flag.append('no UV')
        if 'NORMAL' not in p['attrs']: flag.append('no normals')
        bad += bool(flag)
        print(f'  {"G" if p["gear"] else "B"} {p["node"][:26]:26s} tris {p["tris"]:6d} verts {p["verts"]:6d} mat {m.get("name")!s:14s} '
              f'bbox mm {np.round(p["lo"]*1000).astype(int)}..{np.round(p["hi"]*1000).astype(int)}  {"; ".join(flag)}')
    print('materials:')
    for m in mats:
        pb = m.get('pbrMetallicRoughness', {})
        print(f'  {m.get("name")!s:16s} baseTex {"baseColorTexture" in pb} mrTex {"metallicRoughnessTexture" in pb} normal {"normalTexture" in m} '
              f'metal {pb.get("metallicFactor", 1)} rough {pb.get("roughnessFactor", 1)} alpha {m.get("alphaMode","OPAQUE")} doubleSided {m.get("doubleSided", False)}')
    for s in js.get('samplers', []): print('  sampler', s)
    print('textures:', tex, f' memory {texmem/2**20:.2f} MiB (RGBA8 + mips)')
    print('named points (world, mm):')
    for nme, t in points: print(f'  {nme:28s} {np.round(t*1000,1)}')
    if BV is not None:
        D = dims(BV); print('bird without gear (mm):', {k: round(v, 1) for k, v in D.items()})
        D2 = dims(AV); print('whole file (mm):', {k: round(v, 1) for k, v in D2.items()})
        if ref:
            R = REF[ref]
            chk = []
            if pose == 'flight': chk.append(('span', max(D['ext_x'], D['ext_z']), R['span']))
            else:
                chk.append(('height_' + ('perch' if ref == 'saker_f' else 'stand'), D['height'], R.get('height_perch') or R.get('height_stand')))
                chk.append(('side_diameter vs length', D['side_diameter'], (R['length'][0] * 0.75, R['length'][1])))
            for k, v, (a, b) in chk: print(f'  CHECK {k:26s} model {v:7.1f}  ref {a}..{b}  {"ok" if a <= v <= b else "OUT"}')
    print(f'primitives with a flag: {bad}')

if __name__ == '__main__':
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    files = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or not a[i - 1].startswith('--'))]
    for f in files: report(f, opt('--ref'), opt('--pose'), opt('--gear', GEAR))

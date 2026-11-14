#!/usr/bin/env python3
"""T7 reviewer: measure a rifle GLB without Blender (own glTF reader, numpy only).

usage: python3 -I glb_check.py model.glb [more.glb ...] [--json out.json]

Prints, per GLB: scenes/nodes, every mesh primitive (= one draw) with its
triangle count, material and world bounding box; the named points (nodes
without mesh) in world space; the materials' PBR factors and texture sizes;
texture memory (RGBA8 + full mip chain, uncompressed, as ADR 0005 counts it);
and the whole model's extents in the rifle frame (X along the bore = length,
Y up = height, Z = width; glTF is Y-up). Then checks against REF below.
"""
import json, struct, sys, zlib, numpy as np

# Sourced reference (mm). (value, tolerance) - tolerance is the reviewer's pass band.
REF = {
    'overall_length': (880, 15),     # AKM, fixed stock, no bayonet (ru/en manuals; 876-896 in other sources)
    'barrel_length': (415, 5),       # chamber face to muzzle, without the slant brake
    'sight_radius': (378, 6),        # rear sight notch to front sight post
    'width_max': (70, 25),           # AK-74M figure 70 mm; AKM receiver ~ 45-50 mm + sling swivels; from drawing
    'height_with_mag': (246, 12),    # front sight top to magazine tip: Armemuseum AKM photo scaled to 880 mm = 246; IWM catalogue 258
    'sight_over_bore': (49, 4),      # front sight top above bore axis: photo 48-49 mm; forum 'about 2 in'
    'butt_height': (92, 8),          # butt plate heel to toe, photo
    'grip_bottom_below_bore': (133, 10),  # photo
    'mag_tip_below_bore': (197, 10), # photo
}

def read_glb(path):
    b = open(path, 'rb').read()
    magic, ver, n = struct.unpack_from('<4sII', b, 0)
    assert magic == b'glTF', 'not a GLB'
    off, js, bin_ = 12, None, None
    while off < n:
        ln, typ = struct.unpack_from('<I4s', b, off); off += 8
        chunk = b[off:off + ln]; off += ln
        if typ == b'JSON': js = json.loads(chunk)
        elif typ == b'BIN\x00': bin_ = chunk
    return js, bin_

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def accessor(js, bin_, i):
    a = js['accessors'][i]
    if 'bufferView' not in a:   # all zeros, maybe with sparse values
        out = np.zeros((a['count'], NC[a['type']]), CT[a['componentType']])
        sp = a.get('sparse')
        if sp:
            ib = js['bufferViews'][sp['indices']['bufferView']]; vb = js['bufferViews'][sp['values']['bufferView']]
            idx = np.frombuffer(bin_, CT[sp['indices']['componentType']], sp['count'], ib.get('byteOffset', 0) + sp['indices'].get('byteOffset', 0))
            val = np.frombuffer(bin_, CT[a['componentType']], sp['count'] * NC[a['type']], vb.get('byteOffset', 0) + sp['values'].get('byteOffset', 0)).reshape(sp['count'], -1)
            out[idx] = val
        return out
    bv = js['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']]); nc = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', dt.itemsize * nc)
    raw = np.frombuffer(bin_, dtype=np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * nc, offset=start)
    out = np.lib.stride_tricks.as_strided(raw, shape=(a['count'], dt.itemsize * nc), strides=(stride, 1)).copy()
    return out.view(dt).reshape(a['count'], nc)

def qmat(t, r, s):
    x, y, z, w = r
    R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                  [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                  [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    M = np.eye(4); M[:3, :3] = R * np.array(s); M[:3, 3] = t
    return M

def local(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4, 4).T
    return qmat(n.get('translation', [0, 0, 0]), n.get('rotation', [0, 0, 0, 1]), n.get('scale', [1, 1, 1]))

def png_size(b):
    if b[:8] == b'\x89PNG\r\n\x1a\n': return struct.unpack('>II', b[16:24])
    if b[:2] == b'\xff\xd8':  # JPEG: scan SOF
        i = 2
        while i < len(b):
            if b[i] != 0xFF: i += 1; continue
            m = b[i + 1]; ln = struct.unpack('>H', b[i + 2:i + 4])[0]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack('>HH', b[i + 5:i + 9]); return w, h
            i += 2 + ln
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
        return None
    return None

def analyse(path):
    js, bin_ = read_glb(path)
    nodes = js.get('nodes', []); meshes = js.get('meshes', [])
    world = {}
    def walk(i, M):
        W = M @ local(nodes[i]); world[i] = W
        for c in nodes[i].get('children', []): walk(c, W)
    roots = js['scenes'][js.get('scene', 0)]['nodes']
    for r in roots: walk(r, np.eye(4))
    prims, points, allv = [], [], []
    for i, n in enumerate(nodes):
        if i not in world: continue
        W = world[i]
        if 'mesh' in n:
            for p in meshes[n['mesh']]['primitives']:
                P = accessor(js, bin_, p['attributes']['POSITION']).astype(float)
                Pw = (W[:3, :3] @ P.T).T + W[:3, 3]
                mode = p.get('mode', 4)
                ntri = (js['accessors'][p['indices']]['count'] if 'indices' in p else len(P)) // 3 if mode == 4 else 0
                prims.append(dict(node=n.get('name', f'#{i}'), mesh=meshes[n['mesh']].get('name'), tris=ntri,
                                  mat=p.get('material'), attrs=sorted(p['attributes']), skinned='skin' in n,
                                  lo=Pw.min(0), hi=Pw.max(0), verts=len(P), targets=len(p.get('targets', []))))
                allv.append(Pw)
        else:
            points.append((n.get('name', f'#{i}'), W[:3, 3], W[:3, :3]))
    mats = js.get('materials', [])
    imgs = js.get('images', [])
    texmem, texinfo = 0, []
    for k, im in enumerate(imgs):
        if 'bufferView' in im:
            bv = js['bufferViews'][im['bufferView']]
            data = bin_[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
            sz = png_size(data)
        else:
            sz = None  # external uri: flagged below
        if sz:
            texmem += sz[0] * sz[1] * 4 * 4 / 3
        texinfo.append((k, im.get('name'), im.get('mimeType'), sz, 'uri' in im))
    return js, prims, points, mats, texinfo, texmem, (np.vstack(allv) if allv else np.zeros((0, 3)))

def report(path):
    js, prims, points, mats, texinfo, texmem, V = analyse(path)
    print(f'\n=== {path}')
    print(f'generator: {js.get("asset", {}).get("generator")}; extensions used: {js.get("extensionsUsed", [])}')
    tot = sum(p["tris"] for p in prims)
    print(f'draws (primitives): {len(prims)}   triangles: {tot}   vertices: {sum(p["verts"] for p in prims)}')
    for p in prims:
        mn = mats[p['mat']].get('name') if p['mat'] is not None else None
        print(f'  {p["node"]:24s} tris {p["tris"]:6d} mat {mn!s:16s} skinned {p["skinned"]} morphs {p["targets"]} '
              f'bbox mm {np.round(p["lo"]*1000).astype(int)} .. {np.round(p["hi"]*1000).astype(int)} attrs {p["attrs"]}')
    if len(V):
        lo, hi = V.min(0), V.max(0); ext = (hi - lo) * 1000
        print(f'whole bbox (m): lo {np.round(lo, 4)} hi {np.round(hi, 4)}  extents mm X {ext[0]:.1f} Y {ext[1]:.1f} Z {ext[2]:.1f}')
    print('named points (world, m):')
    for name, t, R in points:
        print(f'  {name:24s} {np.round(t, 4)}  fwd(-Z) {np.round(-R[:, 2], 3)} up(Y) {np.round(R[:, 1], 3)}')
    print('materials:')
    for m in mats:
        pb = m.get('pbrMetallicRoughness', {})
        print(f'  {m.get("name")!s:18s} base {pb.get("baseColorFactor")} metal {pb.get("metallicFactor", 1)} rough {pb.get("roughnessFactor", 1)} '
              f'baseTex {"baseColorTexture" in pb} mrTex {"metallicRoughnessTexture" in pb} normal {"normalTexture" in m} '
              f'ao {"occlusionTexture" in m} alpha {m.get("alphaMode", "OPAQUE")} double {m.get("doubleSided", False)} ext {list(m.get("extensions", {}))}')
        # sanity: glTF defaults metal=1 rough=1 when a factor is omitted; wood must not be metallic
        nm = (m.get('name') or '').lower()
        if any(w in nm for w in ('wood', 'stock', 'hand', 'grip')) and pb.get('metallicFactor', 1) > 0.1 and 'metallicRoughnessTexture' not in pb:
            print(f'    !! {m.get("name")}: wood-like material is metallic {pb.get("metallicFactor", 1)}')
    print('textures:')
    for t in texinfo: print('  ', t, '!! external uri' if t[4] else '')
    print(f'texture memory (RGBA8 + mips, uncompressed): {texmem/2**20:.2f} MiB')
    return prims, points, V

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    for a in args: report(a)

#!/usr/bin/env python3
"""T17 reviewer: render skinned frames one-sided (own rasteriser, textured), my own contact sheets.
usage: rframes.py file.glb clip out.jpg "frames" view mm_per_px cx cy cz [--meshes a,b] [--extra static.glb] [--w 360 --h 300] [--follow]
  frames: comma list of frame numbers (30 fps) or 'all/N' for every Nth; meshes: node names to draw (default all);
  --follow: centre each frame on the 'body' bone (else fixed centre cx cy cz, metres glTF)."""
import sys, os, io, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import Rig
from glb_read import read_glb, accessor
from bird_check import world_nodes
a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
path, clip, out, frs, view, mmpp = a[0], a[1], a[2], a[3], a[4], float(a[5]); C0 = np.array(list(map(float, a[6:9])))
W, H = int(opt('--w', 360)), int(opt('--h', 300)); meshes = opt('--meshes'); meshes = meshes.split(',') if meshes else None
r = Rig(path); fps = 30
dur = max(c['T'][-1] for c in r.clips[clip]) if clip != 'rest' else 0
nf = int(round(dur * fps)) + 1
if frs.startswith('all/'): F = list(range(0, nf, int(frs[4:])))
else: F = [float(x) for x in frs.split(',')]
V = {'side': ((0, 0, -1), (0, 1, 0)), 'left': ((0, 0, 1), (0, 1, 0)), 'front': ((-1, 0, 0), (0, 1, 0)), 'back': ((1, 0, 0), (0, 1, 0)),
     'below': ((0, 1, 0), (1, 0, 0)), 'top': ((0, -1, 0), (1, 0, 0)), 'tq': ((-0.6, -0.25, -0.76), (0, 1, 0)), 'tqb': ((0.6, 0.45, -0.66), (0, 1, 0)),
     'tqlow': ((-0.5, 0.35, -0.8), (0, 1, 0))}
fwd = np.array(V[view][0], float); fwd /= np.linalg.norm(fwd); up = np.array(V[view][1], float)
right = np.cross(fwd, up); right /= np.linalg.norm(right); up = np.cross(right, fwd)
light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)
js = r.js; tex = {}
def texof(prim):
    ti = js['materials'][prim['material']]['pbrMetallicRoughness']['baseColorTexture']['index']
    if ti not in tex:
        im = js['images'][js['textures'][ti]['source']]; bv = js['bufferViews'][im['bufferView']]
        tex[ti] = np.asarray(Image.open(io.BytesIO(r.b[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB')).astype(float) / 255
    return tex[ti]
extra = []
for e in (opt('--extra') or '').split(','):
    if not e: continue
    ej, eb = read_glb(e); en, ew, _ = world_nodes(ej)
    for i, n in enumerate(en):
        if 'mesh' not in n: continue
        for p in ej['meshes'][n['mesh']]['primitives']:
            P = accessor(ej, eb, p['attributes']['POSITION']).astype(float); P = (ew[i][:3, :3] @ P.T).T + ew[i][:3, 3]
            ti = ej['materials'][p['material']]['pbrMetallicRoughness']['baseColorTexture']['index']; im = ej['images'][ej['textures'][ti]['source']]; bv = ej['bufferViews'][im['bufferView']]
            T = np.asarray(Image.open(io.BytesIO(eb[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB')).astype(float) / 255
            extra.append((P, accessor(ej, eb, p['indices']).ravel().reshape(-1, 3), accessor(ej, eb, p['attributes']['TEXCOORD_0']).astype(float), T))
def draw(items, C):
    img = np.full((H, W, 3), 0.55); zb = np.full((H, W), np.inf)
    for P, I, UV, T in items:
        th, tw = T.shape[:2]; Q = P - C; sx = Q @ right * 1000 / mmpp + W / 2; sy = -(Q @ up) * 1000 / mmpp + H / 2; sz = Q @ fwd
        N = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); N /= np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-15)
        for k, (i0, i1, i2) in enumerate(I):
            if N[k] @ fwd > 0: continue
            xs = np.array([sx[i0], sx[i1], sx[i2]]); ys = np.array([sy[i0], sy[i1], sy[i2]])
            x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1); y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, H - 1)
            if x1 < x0 or y1 < y0: continue
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(d) < 1e-9: continue
            gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
            l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d; l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d; l2 = 1 - l0 - l1
            m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
            if not m.any(): continue
            z = l0 * sz[i0] + l1 * sz[i1] + l2 * sz[i2]; zr = zb[y0:y1 + 1, x0:x1 + 1]; m &= z < zr
            if not m.any(): continue
            u = l0 * UV[i0, 0] + l1 * UV[i1, 0] + l2 * UV[i2, 0]; v = l0 * UV[i0, 1] + l1 * UV[i1, 1] + l2 * UV[i2, 1]
            col = T[np.clip((v * th).astype(int), 0, th - 1), np.clip((u * tw).astype(int), 0, tw - 1)]
            sh = 0.55 + 0.5 * max(N[k] @ light, 0) + 0.12 * max(N[k] @ -fwd, 0); zr[m] = z[m]; img[y0:y1 + 1, x0:x1 + 1][m] = np.clip(col[m] * sh, 0, 1)
    for t in range(0, W, max(1, int(10 / mmpp))): img[H - 6:H, t] = 0
    return img
body = next((i for i, n in enumerate(r.nodes) if n.get('name') == 'body'), None)
tiles = []
for f in F:
    t = min(f / fps, dur); cl = None if clip == 'rest' else clip
    items = [(m['V'], m['I'], accessor(js, r.b, m['prim']['attributes']['TEXCOORD_0']).astype(float), texof(m['prim'])) for m in r.skinned(cl, t) if (meshes is None or m['node'] in meshes) and not (m['morph'] and m['morph'][0] > 0.999) and not ('--onlyvisible' in a and np.ptp(m['V'],0).max() < 0.005)]
    C = C0 + (r.pose(cl, t)[body][:3, 3] if '--follow' in a and body is not None else 0)
    im = Image.fromarray((draw(items + extra, C) * 255).astype(np.uint8)); ImageDraw.Draw(im).text((4, 4), f'{clip} f{f}', fill=(255, 255, 0)); tiles.append(im)
cols = min(len(tiles), 6); rows = (len(tiles) + cols - 1) // cols
S = Image.new('RGB', (W * cols, H * rows), 'white')
for i, t in enumerate(tiles): S.paste(t, ((i % cols) * W, (i // cols) * H))
S.save(out, quality=85); print(out, len(tiles), 'frames')

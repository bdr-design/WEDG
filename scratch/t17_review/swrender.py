#!/usr/bin/env python3
"""T11 reviewer: a software renderer for GLBs (numpy only, no Blender, no GPU): orthographic, z-buffered, the base
colour texture sampled per pixel, simple key + fill lighting on face normals. Independent of the worker's pictures.
usage: swrender.py out.png view mm_per_px cx cy cz file.glb[@dx,dy,dz] ... [--w 900 --h 700]
  coordinates in glTF metres (Y up); birds face +X, their left is -Z.
  view: side (from the bird's right, +Z... looking -Z) | left | front | back | below | top | tq | tqb"""
import sys, os, io, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb, accessor
from bird_check import world_nodes
a = [x for x in sys.argv[1:]]
W = int(a[a.index('--w') + 1]) if '--w' in a else 900; H = int(a[a.index('--h') + 1]) if '--h' in a else 700
a = [x for i, x in enumerate(a) if not (x in ('--w', '--h') or (i and a[i - 1] in ('--w', '--h')))]
out, view, mmpp = a[0], a[1], float(a[2]); C = np.array(list(map(float, a[3:6]))); files = a[6:]
V = {'side': ((0, 0, -1), (0, 1, 0)), 'left': ((0, 0, 1), (0, 1, 0)), 'front': ((-1, 0, 0), (0, 1, 0)),
     'back': ((1, 0, 0), (0, 1, 0)), 'below': ((0, 1, 0), (1, 0, 0)), 'top': ((0, -1, 0), (1, 0, 0)),
     'tq': ((-0.6, -0.25, -0.76), (0, 1, 0)), 'tqb': ((0.6, 0.45, -0.66), (0, 1, 0))}
fwd = np.array(V[view][0], float); fwd /= np.linalg.norm(fwd); up = np.array(V[view][1], float)
right = np.cross(fwd, up); right /= np.linalg.norm(right); up = np.cross(right, fwd)
light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)
img = np.full((H, W, 3), 0.55); zb = np.full((H, W), np.inf)
for f in files:
    p, _, off = f.partition('@'); off = np.array(list(map(float, off.split(',')))) if off else np.zeros(3)
    js, b = read_glb(p); nodes, world, _ = world_nodes(js)
    texs = {}
    for i, n in enumerate(nodes):
        if 'mesh' not in n or i not in world: continue
        Wm = world[i]
        for pr in js['meshes'][n['mesh']]['primitives']:
            P = accessor(js, b, pr['attributes']['POSITION']).astype(float); P = (Wm[:3, :3] @ P.T).T + Wm[:3, 3] + off
            UV = accessor(js, b, pr['attributes']['TEXCOORD_0']).astype(float)
            I = accessor(js, b, pr['indices']).ravel().reshape(-1, 3)
            m = js['materials'][pr['material']]; ti = m['pbrMetallicRoughness']['baseColorTexture']['index']
            if ti not in texs:
                im = js['images'][js['textures'][ti]['source']]; bv = js['bufferViews'][im['bufferView']]
                texs[ti] = np.asarray(Image.open(io.BytesIO(b[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB')).astype(float) / 255
            T = texs[ti]; th, tw = T.shape[:2]
            Q = P - C; sx = Q @ right * 1000 / mmpp + W / 2; sy = -(Q @ up) * 1000 / mmpp + H / 2; sz = Q @ fwd
            N = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); nl = np.linalg.norm(N, axis=1); N /= np.maximum(nl[:, None], 1e-12)
            for k, (i0, i1, i2) in enumerate(I):
                if N[k] @ fwd > 0 and not os.environ.get("NOCULL"): continue          # back face (closed one-sided meshes)
                xs = np.array([sx[i0], sx[i1], sx[i2]]); ys = np.array([sy[i0], sy[i1], sy[i2]])
                x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1); y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, H - 1)
                if x1 < x0 or y1 < y0: continue
                d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
                if abs(d) < 1e-9: continue
                gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
                l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
                l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d; l2 = 1 - l0 - l1
                msk = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
                if not msk.any(): continue
                z = l0 * sz[i0] + l1 * sz[i1] + l2 * sz[i2]
                zr = zb[y0:y1 + 1, x0:x1 + 1]; msk &= z < zr
                if not msk.any(): continue
                u = l0 * UV[i0, 0] + l1 * UV[i1, 0] + l2 * UV[i2, 0]; v = l0 * UV[i0, 1] + l1 * UV[i1, 1] + l2 * UV[i2, 1]
                col = T[np.clip((v * th).astype(int), 0, th - 1), np.clip((u * tw).astype(int), 0, tw - 1)]
                sh = 0.55 + 0.5 * max(N[k] @ light, 0) + 0.12 * max(N[k] @ -fwd, 0)
                zr[msk] = z[msk]; img[y0:y1 + 1, x0:x1 + 1][msk] = np.clip(col[msk] * sh, 0, 1)
# 1 cm ruler ticks along the bottom
for t in range(0, W, max(1, int(10 / mmpp))): img[H - 12:H, t] = 0
Image.fromarray((img * 255).astype(np.uint8)).save(out); print(out)

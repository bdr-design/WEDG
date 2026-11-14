#!/usr/bin/env python3
"""T11 reviewer: a bird GLB's silhouette laid over a reference outline traced from a photograph.

usage: python3 -I bird_sil.py model.glb outline.json out_prefix [--view side|below|front] [--axis x|z] [--gear REGEX]
  outline.json: {"image": path, "outline": [[x,y],...] (photo pixels), "holes": [[[x,y],...]],
                 "scale": {"p1": [x,y], "p2": [x,y], "mm": 520, "what": "bill tip to tail tip"}}
  The photo outline is scaled to real size by the scale pair (a published measure), the model is at its own size.
  Both are rasterised at 1 mm per pixel; the model is mirrored if that fits better, and slid to the best overlap.
Prints: IoU at real size (shape and size together), IoU with the reference rescaled to the model's height (shape
alone), heights and widths of both, and the column profile differences every 20 mm.
Writes out_prefix_overlay.png: grey both, green model only, magenta reference only, ticks every 100 mm.
"""
import sys, os, re, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bird_check import analyse, GEAR

PX = 0.001

def raster(V, F, w, h):
    img = np.zeros((h, w), bool)
    for a, b, c in F:
        p = V[[a, b, c]]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, w - 1), min(y1, h - 1)
        if x1 < x0 or y1 < y0: continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-12: continue
        l1 = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0]) + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / d
        l2 = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0]) + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / d
        img[y0:y1 + 1, x0:x1 + 1] |= (l1 >= -1e-6) & (l2 >= -1e-6) & (1 - l1 - l2 >= -1e-6)
    return img

def model_mask(path, view, axis, gear):
    from glb_read import read_glb, accessor
    from bird_check import world_nodes
    js, bin_ = read_glb(path); nodes, world, parent = world_nodes(js); meshes = js['meshes']
    Vs, Fs, off = [], [], 0
    for i, n in enumerate(nodes):
        if 'mesh' not in n or i not in world: continue
        if re.search(gear, nodes[i].get('name', '') + ' ' + meshes[n['mesh']].get('name', ''), re.I): continue  # own names only
        for p in meshes[n['mesh']]['primitives']:
            P = accessor(js, bin_, p['attributes']['POSITION']).astype(float)
            P = (world[i][:3, :3] @ P.T).T + world[i][:3, 3]
            I = accessor(js, bin_, p['indices']).ravel() if 'indices' in p else np.arange(len(P))
            Vs.append(P); Fs.append(I.reshape(-1, 3) + off); off += len(P)
    V = np.vstack(Vs); F = np.vstack(Fs); ext = V.max(0) - V.min(0)
    if view == 'below':
        a, b = (0, 2) if ext[0] >= ext[2] else (2, 0)   # span across the image
    else:
        h = {'x': 0, 'z': 2}.get(axis, 0 if ext[0] >= ext[2] else 2)
        if view == 'front': h = 2 if h == 0 else 0
        a, b = h, 1
    x = (V[:, a] - V[:, a].min()) / PX
    y = ((V[:, b].max() - V[:, b]) if b == 1 else (V[:, b] - V[:, b].min())) / PX
    w, hh = int(np.ceil(x.max())) + 2, int(np.ceil(y.max())) + 2
    return raster(np.c_[x, y], F, w, hh)

def ref_mask(spec):
    im = Image.open(spec['image']); W, H = im.size
    if 'mask' in spec:  # a binary mask of the photo (white = bird), e.g. from skymask.py
        m = np.asarray(Image.open(spec['mask']).convert('L')) > 127
    else:
        m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
        d.polygon([tuple(p) for p in spec['outline']], fill=255)
        for hole in spec.get('holes', []): d.polygon([tuple(p) for p in hole], fill=0)
        m = np.asarray(m) > 127
    sc = spec['scale']; dpx = np.hypot(*(np.subtract(sc['p2'], sc['p1'])))
    mm_per_px = sc['mm'] / dpx
    ys, xs = np.where(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = mm_per_px * 0.001 / PX
    im2 = Image.fromarray(m.astype(np.uint8) * 255).resize((max(1, int(m.shape[1] * s)), max(1, int(m.shape[0] * s))), Image.BILINEAR)
    return np.asarray(im2) > 127, mm_per_px

def inter_at(A, R, dy, dx):
    """|A & R| with R's top-left placed at (dy, dx) in A's frame."""
    y0, x0 = max(0, dy), max(0, dx); y1, x1 = min(A.shape[0], dy + R.shape[0]), min(A.shape[1], dx + R.shape[1])
    if y1 <= y0 or x1 <= x0: return 0
    return int((A[y0:y1, x0:x1] & R[y0 - dy:y1 - dy, x0 - dx:x1 - dx]).sum())

def best_overlap(M, R, reach=120, flips=(0, 1)):
    """Best IoU of R slid over M (and over M mirrored); returns (iou, flip, A, B) as full canvases for drawing."""
    sa, sr = int(M.sum()), int(R.sum()); best = None
    for flip in flips:
        A0 = M[::-1 if flip & 2 else 1, ::-1 if flip & 1 else 1]
        cy, cx = (A0.shape[0] - R.shape[0]) // 2, (A0.shape[1] - R.shape[1]) // 2
        cand = []
        for dy in range(cy - reach, cy + reach + 1, 4):
            for dx in range(cx - reach, cx + reach + 1, 4):
                i = inter_at(A0, R, dy, dx); cand.append((i / (sa + sr - i), dy, dx))
        _, dy0, dx0 = max(cand)
        for dy in range(dy0 - 4, dy0 + 5):
            for dx in range(dx0 - 4, dx0 + 5):
                i = inter_at(A0, R, dy, dx); v = i / (sa + sr - i)
                if best is None or v > best[0]: best = (v, flip, dy, dx)
    v, flip, dy, dx = best; A0 = M[::-1 if flip & 2 else 1, ::-1 if flip & 1 else 1]
    oy, ox = max(0, -dy), max(0, -dx); H = max(A0.shape[0] + oy, dy + oy + R.shape[0]); W = max(A0.shape[1] + ox, dx + ox + R.shape[1])
    A = np.zeros((H, W), bool); B = np.zeros((H, W), bool)
    A[oy:oy + A0.shape[0], ox:ox + A0.shape[1]] = A0; B[dy + oy:dy + oy + R.shape[0], dx + ox:dx + ox + R.shape[1]] = R
    return v, flip, A, B

def crop(A, B):
    U = A | B; ys, xs = np.where(U); return A[ys.min():ys.max() + 1, xs.min():xs.max() + 1], B[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

if __name__ == '__main__':
    a = sys.argv[1:]; opt = lambda k, d=None: (a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) and not a[a.index(k) + 1].startswith('--') else (True if k in a else d))
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or not a[i - 1].startswith('--'))]
    spec = json.load(open(pos[1]))
    M = model_mask(pos[0], opt('--view', 'side'), opt('--axis'), opt('--gear', GEAR))
    FL = (0, 1, 2, 3) if opt('--view') == 'below' else (0, 1)   # a side view is never turned upside down
    R, mmpp = ref_mask(spec)
    iou, flip, A, B = best_overlap(M, R, flips=FL); A, B = crop(A, B)
    hm, hr = A.any(1).sum(), B.any(1).sum(); wm, wr = A.any(0).sum(), B.any(0).sum()
    print(f'reference: {spec["image"]}  scale {spec["scale"]["what"]} = {spec["scale"]["mm"]} mm ({mmpp:.3f} mm/px)')
    print(f'real size: IoU {iou:.3f} (model mirrored: {['no','left-right','up-down','both'][flip]}); model {wm}x{hm} mm, reference {wr}x{hr} mm (width x height)')
    # shape alone: reference rescaled to the model's height
    k = M.shape[1] / R.shape[1] if opt('--fit') == 'width' else M.shape[0] / R.shape[0]
    Rs = np.asarray(Image.fromarray(R.astype(np.uint8) * 255).resize((max(1, int(R.shape[1] * k)), max(1, int(R.shape[0] * k))), Image.BILINEAR)) > 127
    iou2, flip2, A2, B2 = best_overlap(M, Rs, flips=FL)
    print(f'shape alone (reference scaled to model {opt("--fit") or "height"}, x{k:.3f}): IoU {iou2:.3f}')
    o2 = np.full(A2.shape + (3,), 255, np.uint8); o2[A2 & B2] = (150, 150, 150); o2[A2 & ~B2] = (0, 170, 0); o2[B2 & ~A2] = (220, 0, 200)
    Image.fromarray(o2).save(pos[2] + '_shape_overlay.png')
    # pose-tolerant: the reference turned by -30..30 degrees (a bird leaning more or less), at real size
    rb = (iou, 0)
    for ang in range(-30, 31, 5):
        if ang == 0: continue
        Rr = np.asarray(Image.fromarray(R.astype(np.uint8) * 255).rotate(ang, resample=Image.BILINEAR, expand=True)) > 127
        ys, xs = np.where(Rr); Rr = Rr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        if opt('--turn-shape'):   # turned, then fitted to the model's height (shape alone)
            k2 = M.shape[0] / Rr.shape[0]
            Rr = np.asarray(Image.fromarray(Rr.astype(np.uint8) * 255).resize((max(1, int(Rr.shape[1] * k2)), M.shape[0]), Image.BILINEAR)) > 127
        v = best_overlap(M, Rr, flips=FL)[0]
        if v > rb[0]: rb = (v, ang)
    print(f'turned (pose lean): best IoU {rb[0]:.3f} with the reference turned {rb[1]} deg')
    out = np.full(A.shape + (3,), 255, np.uint8)
    out[A & B] = (150, 150, 150); out[A & ~B] = (0, 170, 0); out[B & ~A] = (220, 0, 200)
    for st in range(0, A.shape[1], 100): out[:10, st] = 0
    for st in range(0, A.shape[0], 100): out[st, :10] = 0
    Image.fromarray(out).save(pos[2] + '_overlay.png'); print('wrote', pos[2] + '_overlay.png')

import sys, numpy as np
sys.path.insert(0, '.')
from glb_read import read_glb, accessor
from PIL import Image
for f in sys.argv[1:]:
    js, b = read_glb(f); pr = js['meshes'][0]['primitives'][0]
    UV = accessor(js, b, pr['attributes']['TEXCOORD_0']); I = accessor(js, b, pr['indices']).reshape(-1, 3)
    P = accessor(js, b, pr['attributes']['POSITION']) * 1000
    S = 2048; cnt = np.zeros((S, S), np.int32); owner = np.full((S, S), -1)
    bad = set()
    for t, tri in enumerate(I):
        p = UV[tri] * S
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, S - 1), min(y1, S - 1)
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-12: continue
        l1 = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0]) + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / d
        l2 = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0]) + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / d
        m = (l1 > 0.02) & (l2 > 0.02) & (1 - l1 - l2 > 0.02)
        sub = cnt[y0:y1 + 1, x0:x1 + 1]; ow = owner[y0:y1 + 1, x0:x1 + 1]
        clash = m & (sub > 0)
        if clash.any():
            for o in np.unique(ow[clash]): bad.add((int(o), t))
        sub[m] += 1; ow[m] = t
    faces = sorted({x for pr_ in bad for x in pr_})
    c = P[I[faces]].mean(1) if faces else np.zeros((0, 3))
    print(f'{f.split("/")[-1]}: overlapping UV face pairs {len(bad)}, faces {len(faces)}; texels (at 2048) covered twice {int((cnt>1).sum())}')
    for k in range(min(12, len(faces))): print('   face', faces[k], 'at mm', np.round(c[k]).astype(int))

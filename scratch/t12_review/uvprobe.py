import sys, io, numpy as np
sys.path.insert(0, '.')
from glb_read import read_glb, accessor
from PIL import Image
js, b = read_glb(sys.argv[1]); pr = js['meshes'][0]['primitives'][0]
P = accessor(js, b, pr['attributes']['POSITION']) * 1000; UV = accessor(js, b, pr['attributes']['TEXCOORD_0']); I = accessor(js, b, pr['indices']).reshape(-1, 3)
def img(name):
    for im in js['images']:
        if im['name'].endswith(name):
            bv = js['bufferViews'][im['bufferView']]; return Image.open(io.BytesIO(b[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB')
col = img('color'); C = np.asarray(col).astype(int); H, W = C.shape[:2]
col.save(sys.argv[2] + '_color.png'); img('normal').save(sys.argv[2] + '_normal.png')
# glTF Y-up: model x fwd, y up, z lateral (both sides)
for (x, y) in [tuple(map(float, s.split(','))) for s in sys.argv[3:]]:
    for side in (-1, 1):
        cen = P[I].mean(1); d = np.hypot(cen[:, 0] - x, cen[:, 1] - y); m = (np.sign(cen[:, 2]) == side) & (d < 25)
        # outermost faces only (largest |z|)
        if not m.any(): continue
        idx = np.where(m)[0]; idx = idx[np.argsort(-np.abs(cen[idx, 2]))][:6]
        for t in idx:
            uv = UV[I[t]].mean(0); px = (int(uv[0] * W), int(uv[1] * H))
            print(f'pt ({x:.0f},{y:.0f}) side {side:+d} face {t} centre {np.round(cen[t]).astype(int)} uv {np.round(uv,3)} texel {px} colour {C[min(px[1],H-1), min(px[0],W-1)]}  uv spread {np.round(np.ptp(UV[I[t]],0)*W,1)} px')

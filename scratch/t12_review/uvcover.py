import sys, numpy as np
sys.path.insert(0, '.')
from glb_read import read_glb, accessor
from PIL import Image, ImageDraw
for f in sys.argv[1:]:
    js, b = read_glb(f); pr = js['meshes'][0]['primitives'][0]
    UV = accessor(js, b, pr['attributes']['TEXCOORD_0']); I = accessor(js, b, pr['indices']).reshape(-1, 3)
    S = 1024; im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    for t in I: d.polygon([tuple(p) for p in UV[t] * S], fill=255)
    print(f.split('/')[-1], f'UV coverage {np.asarray(im).astype(bool).mean()*100:.1f}%')

#!/usr/bin/env python3
"""Cut task T11's bird renders (design/birds/*.jpg, awaiting the owner's approval) out of their backdrop, for the
storyboard frames that show a bird large (outing.cjs, camp.cjs). The backdrop is smooth: it is flooded from the
picture's edges, pixel to pixel while the colour changes by less than 9 (sum of RGB), and what the flood never reaches
is the bird; the result is cropped to the bird. These are T11's pictures composited, not the game's models in the page.
Usage: python3 -I design/hunt/cut_bird.py <birds folder> <out folder>   (default design/birds -> design/hunt/birds)"""
import os, sys
from collections import deque
from PIL import Image, ImageFilter
import numpy as np
SRC = sys.argv[1] if len(sys.argv) > 1 else 'design/birds'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'design/hunt/birds'
# picture -> (crop box before the cut: x0, y0, x1, y1, keeping rulers and labels out)
JOBS = {
    'saker_hooded_three_quarter.jpg': (440, 130, 760, 585),      # on the glove: above the perch's top
    'saker_hooded_perch.jpg': None,                               # (made below from the same render, with its perch)
    'saker_flight_below.jpg': (0, 0, 1200, 880),
    'saker_alert_side.jpg': (0, 0, 1200, 840),
    'curlew_alert_side.jpg': (0, 0, 1200, 840),
    'curlew_flight_three_quarter.jpg': (0, 0, 1200, 880),
}
def cut(path, box, out):
    img = Image.open(path).convert('RGB')
    if box: img = img.crop(box)
    im = np.asarray(img).astype(int); H, W, _ = im.shape
    bg = np.zeros((H, W), bool); q = deque()
    for x in range(W): q += [(0, x), (H - 1, x)]
    for y in range(H): q += [(y, 0), (y, W - 1)]
    for y, x in q: bg[y, x] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and not bg[ny, nx] and abs(im[ny, nx] - im[y, x]).sum() < 9:
                bg[ny, nx] = True; q.append((ny, nx))
    m = Image.fromarray(((~bg) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    rgba = img.convert('RGBA'); rgba.putalpha(m)
    rgba = rgba.crop(m.point(lambda v: 255 if v > 40 else 0).getbbox())
    rgba.save(out); print('wrote', out, rgba.size)
os.makedirs(OUT, exist_ok=True)
for name, box in JOBS.items():
    if box is None: continue
    cut(os.path.join(SRC, name), box, os.path.join(OUT, name.replace('.jpg', '.png')))
cut(os.path.join(SRC, 'saker_hooded_three_quarter.jpg'), (420, 120, 780, 900), os.path.join(OUT, 'saker_hooded_perch.png'))

#!/usr/bin/env python3
"""Cut task T11's hooded saker out of its render, for the storyboard's frames 5 and 8 (outing.cjs), where the bird is
seen large. The render's backdrop is a smooth gradient: it is flooded from the picture's edges, pixel to pixel while the
colour changes by less than 9 (sum of RGB), and what the flood never reaches is the bird. Crop above the perch's top.
Usage: python3 -I design/hunt/cut_bird.py [<T11's saker_hooded_three_quarter.jpg>] [<out png>]
(default: design/birds/saker_hooded_three_quarter.jpg -> design/hunt/t11_saker_hooded.png)."""
import sys
from collections import deque
from PIL import Image, ImageFilter
import numpy as np
src = sys.argv[1] if len(sys.argv) > 1 else 'design/birds/saker_hooded_three_quarter.jpg'
out = sys.argv[2] if len(sys.argv) > 2 else 'design/hunt/t11_saker_hooded.png'
img = Image.open(src).convert('RGB').crop((440, 130, 760, 585))
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
rgba = img.convert('RGBA'); rgba.putalpha(m); rgba.save(out)
print('wrote', out, rgba.size)

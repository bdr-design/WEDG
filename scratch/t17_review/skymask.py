#!/usr/bin/env python3
"""T11 reviewer: mask of a bird against plain sky in a box of a photo (colour distance from the box's border colour,
largest connected part kept, small holes filled). usage: skymask.py img x0 y0 x1 y1 thresh out.png"""
import sys, numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float); x0, y0, x1, y1, th = map(int, sys.argv[2:7])
c = im[y0:y1, x0:x1]; border = np.vstack([c[0], c[-1], c[:, 0], c[:, -1]]); sky = np.median(border, 0)
m = np.linalg.norm(c - sky, axis=-1) > th
def largest(m):
    lab = np.zeros(m.shape, int); cur = 0; sizes = {}
    for y, x in zip(*np.where(m)):
        if lab[y, x]: continue
        cur += 1; st = [(y, x)]; lab[y, x] = cur; n = 0
        while st:
            a, b = st.pop(); n += 1
            for p, q in ((a+1, b), (a-1, b), (a, b+1), (a, b-1)):
                if 0 <= p < m.shape[0] and 0 <= q < m.shape[1] and m[p, q] and not lab[p, q]: lab[p, q] = cur; st.append((p, q))
        sizes[cur] = n
    return lab == max(sizes, key=sizes.get)
m = largest(m); bg = largest(~m)  # background = the largest part of the rest; everything else is a hole -> fill
m = ~bg
full = np.zeros(im.shape[:2], np.uint8); full[y0:y1, x0:x1] = m * 255
Image.fromarray(full).save(sys.argv[7]); print('pixels', m.sum(), 'bbox', np.where(m.any(0))[0][[0, -1]] + x0, np.where(m.any(1))[0][[0, -1]] + y0)

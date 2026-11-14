#!/usr/bin/env python3
"""T11 reviewer: for each picture, size, file size, and how much is burnt out (all channels >= 250) or crushed
(all <= 5), over the whole frame and over the non-background part (pixels that differ from the corner colour).
usage: pic_check.py picture.jpg [...]"""
import sys, os, numpy as np
from PIL import Image
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert('RGB')).astype(int)
    corner = np.median(np.vstack([a[:8, :8].reshape(-1, 3), a[:8, -8:].reshape(-1, 3)]), 0)
    fg = np.abs(a - corner).sum(-1) > 40
    hi = (a >= 250).all(-1); lo = (a <= 5).all(-1)
    print(f'{os.path.basename(f):40s} {a.shape[1]}x{a.shape[0]} {os.path.getsize(f)/1024:6.0f} KiB  burnt {hi.mean()*100:5.2f}% '
          f'(subject {hi[fg].mean()*100 if fg.any() else 0:5.2f}%)  crushed {lo.mean()*100:5.2f}%  subject share {fg.mean()*100:4.1f}%')

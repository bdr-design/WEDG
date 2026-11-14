#!/usr/bin/env python3
"""T11 reviewer: a GLB's side (or below) silhouette at 1 mm/px with a labelled 10 mm grid, to read proportions by eye.
usage: model_grid.py model.glb out.png [--view side|below] [--axis x|z] [--all]   (--all keeps the gear)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bird_sil import model_mask
from bird_check import GEAR
from PIL import Image, ImageDraw, ImageFont
a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
M = model_mask(a[0], opt('--view', 'side'), opt('--axis', 'x'), 'zzzz' if '--all' in a else GEAR)
s = 2; im = Image.fromarray((~M).astype(np.uint8) * 255).convert('RGB').resize((M.shape[1] * s, M.shape[0] * s)); d = ImageDraw.Draw(im)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
for x in range(0, M.shape[1], 10): d.line([(x * s, 0), (x * s, im.size[1])], fill=(255, 0, 0) if x % 50 == 0 else (200, 200, 255)); (x % 50 == 0) and d.text((x * s + 2, 2), str(x), fill=(255, 0, 0), font=f)
for y in range(0, M.shape[0], 10): d.line([(0, y * s), (im.size[0], y * s)], fill=(255, 0, 0) if y % 50 == 0 else (200, 200, 255)); (y % 50 == 0) and d.text((2, y * s + 2), str(y), fill=(255, 0, 0), font=f)
im.save(a[1]); print(M.shape)

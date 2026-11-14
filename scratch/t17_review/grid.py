#!/usr/bin/env python3
"""T11 reviewer: draw a labelled pixel grid over (a crop of) a photo, and optionally an outline polygon, to trace by eye.
usage: grid.py img x0 y0 x1 y1 step out.jpg [outline.json]"""
import sys, json
from PIL import Image, ImageDraw, ImageFont
im = Image.open(sys.argv[1]).convert('RGB'); x0, y0, x1, y1, st = map(int, sys.argv[2:7])
c = im.crop((x0, y0, x1, y1)); s = 1000 / max(c.size)
c = c.resize((int(c.size[0] * s), int(c.size[1] * s)), Image.LANCZOS); d = ImageDraw.Draw(c)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
for x in range((x0 // st + 1) * st, x1, st):
    X = (x - x0) * s; d.line([(X, 0), (X, c.size[1])], fill=(255, 255, 0) if x % (st * 5) else (255, 0, 0)); d.text((X + 2, 2), str(x), fill=(255, 255, 0), font=f)
for y in range((y0 // st + 1) * st, y1, st):
    Y = (y - y0) * s; d.line([(0, Y), (c.size[0], Y)], fill=(0, 255, 255) if y % (st * 5) else (255, 0, 0)); d.text((2, Y + 2), str(y), fill=(0, 255, 255), font=f)
if len(sys.argv) > 8:
    sp = json.load(open(sys.argv[8])); P = [((x - x0) * s, (y - y0) * s) for x, y in sp['outline']]
    d.line(P + [P[0]], fill=(255, 0, 255), width=2)
    for k in ('p1', 'p2'):
        x, y = sp['scale'][k]; d.ellipse([((x - x0) * s - 4, (y - y0) * s - 4), ((x - x0) * s + 4, (y - y0) * s + 4)], outline=(0, 255, 0), width=2)
c.save(sys.argv[7], quality=85); print(c.size, 'scale', s)

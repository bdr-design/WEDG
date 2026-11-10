"""A gridded enlargement of part of a photo, to read coordinates off: zoom.py <photo> x0 y0 x1 y1 <out.png> [zoom] [gain] [step]"""
import sys, numpy as np, masks as M
from PIL import Image, ImageDraw
n, x0, y0, x1, y1, out = sys.argv[1], *(int(v) for v in sys.argv[2:6]), sys.argv[6]
z = float(sys.argv[7]) if len(sys.argv) > 7 else 3.0; gain = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0; step = int(sys.argv[9]) if len(sys.argv) > 9 else 20
a = np.clip(M.rgb(n)[y0:y1, x0:x1] * gain, 0, 255).astype(np.uint8); im = Image.fromarray(a).resize((int((x1 - x0) * z), int((y1 - y0) * z)), Image.LANCZOS); d = ImageDraw.Draw(im)
for x in range((x0 // step + 1) * step, x1, step):
    d.line([((x - x0) * z, 0), ((x - x0) * z, im.height)], fill=(0, 255, 255) if x % (5 * step) else (255, 255, 0), width=1)
    if x % (5 * step) == 0: d.text(((x - x0) * z + 2, 2), str(x), fill=(255, 255, 0))
for y in range((y0 // step + 1) * step, y1, step):
    d.line([(0, (y - y0) * z), (im.width, (y - y0) * z)], fill=(0, 255, 255) if y % (5 * step) else (255, 255, 0), width=1)
    if y % (5 * step) == 0: d.text((2, (y - y0) * z + 2), str(y), fill=(255, 255, 0))
im.save(out); print(im.size)

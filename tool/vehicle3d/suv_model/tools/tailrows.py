"""The tail's line in the side photo, row by row, to a fraction of a pixel: the car's last column, plus how much of the
edge pixels is car (blue channel: the background is magenta, the car has little blue). Saves tailrows.npy (z photo, d metres
from the car's rear end) and prints a few rows. Run: blendenv/bin/python tailrows.py"""
import numpy as np, sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import outlines as O
from PIL import Image
a = np.asarray(Image.open(O.photo('01_left')).convert('RGB')).astype(float); m = O._side
s = O.c['s']; v0 = O.c['v0']; uend = np.flatnonzero(m.any(axis=0)).max()
out = []
for v in range(int(v0 - 1.95 / s), int(v0 - 0.45 / s) + 1):
    q = np.flatnonzero(m[v])
    if not len(q): continue
    u = q.max(); bc = a[v, u - 3:u - 1, 2].mean()                    # the car's own blue just inside
    cov = sum(np.clip(1 - (a[v, k, 2] - bc) / max(255 - bc, 1), 0, 1) for k in (u - 1, u, u + 1, u + 2))   # car pixels' worth
    edge = (u - 2) + cov + 0.5                                       # right edge of the car, in pixel-edge units (column k spans k-0.5..k+0.5)
    out.append(((v0 - v) * s, (uend + 0.5 - edge) * s, (uend - u) * s))
out = np.array(out); np.save('tailrows.npy', out)
print('rows', len(out), 'rear end column', uend, ' mean sub-pixel shift mm %.2f' % ((out[:, 1] - out[:, 2]).mean() * 1000))
for z, d, dq in out[::6]:
    if 0.66 < z < 1.46: print('z %.3f  d %6.1f   (whole pixel %5.1f)' % (z, d * 1000, dq * 1000))

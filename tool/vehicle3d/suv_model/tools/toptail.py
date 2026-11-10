"""The tail in the top photo: for columns across the car, how far ahead of the car's rear end the outline is, and how
far ahead the red tail lamp's rear edge is (metres; y on the hull's scale). Run: blendenv/bin/python toptail.py"""
import numpy as np, sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import outlines as O, body as B
from PIL import Image
a = np.asarray(Image.open(O.V + '/Black_SUV_Views/04_top.png').convert('RGB')).astype(int); ct = O.ct
m = O._top; s = ct['s']; ky = s * ct['k'] * B.TOP_TO_FRONT
red = (a[..., 0] > 110) & (a[..., 1] < 70) & (a[..., 2] < 80) & (a[..., 0] > a[..., 1] * 2.2)
vend = np.flatnonzero(m.any(axis=1)).max(); print('rear end row', vend, ' x %.4f' % (O.L / 2 - (vend - ct['v0']) * s), 'ky', ky)
print('    y     outline d   lamp rear edge d   lamp front edge d (mm)')
for u in range(int(ct['uc']) - 330, int(ct['uc']) + 331, 15):
    col = np.flatnonzero(m[:, u]);
    if not len(col): continue
    vo = col.max(); r = np.flatnonzero(red[1560:, u]) + 1560
    y = (u - ct['uc']) * ky
    print('%6.3f   %7.1f   %s' % (y, (vend - vo) * s * 1000, ('%7.1f   %7.1f' % ((vend - r.max()) * s * 1000, (vend - r.min()) * s * 1000)) if len(r) > 3 else '      -'))

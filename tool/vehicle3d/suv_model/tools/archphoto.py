"""The wheel openings in the owner's side photo: round each hub, how far out the dark of the wheel well ends and the
paint begins (the first of three samples in a row brighter than 12 of 255, from just outside the tyre), every 10
degrees. Prints each point as (metres behind the axle, metres up): its offset from the hub in the photo, unscaled, on
the model's hub. The wheel is the photo's size unscaled, so the opening round it is too; mapped with the body instead
(shorter between the axles, longer behind, lower), the rear wheel sat forward in its opening and both gaps closed up.
Run: blendenv/bin/python tools/archphoto.py"""
import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import outlines as O, realframe as RF
from PIL import Image
from scipy import ndimage
a = ndimage.gaussian_filter(np.asarray(Image.open(O.photo('01_left')).convert('L')).astype(float), 0.8); s = O.CFG['side']['s']; v0 = O.CFG['side']['v0']
HUB_V = 673.9                                   # the rims' lips are circles centred here (review r10): 0.4327 m up in the photo
for name, uh in (('front', 356.85), ('rear', 1366.55)):
    pts = []
    for ang in range(10, 171, 10):
        t = np.radians(ang); r = 152.0
        while r < 230:
            if all(a[int(round(HUB_V - q * np.sin(t))), int(round(uh + q * np.cos(t)))] > 12 for q in (r, r + 1, r + 2)): break
            r += 0.5
        pts.append((ang, r, r * np.cos(t) * s, RF.HUB_Z + r * np.sin(t) * s))      # rigid about the hub, like the wheel itself
    print(name, 'hub real z %.4f' % float(RF.z_real((v0 - HUB_V) * s)))
    print('  ' + ' '.join('%d:%.1f' % (p[0], p[1]) for p in pts))
    print('  ' + ', '.join('(%.3f, %.3f)' % (p[2], p[3]) for p in pts[::-1]))

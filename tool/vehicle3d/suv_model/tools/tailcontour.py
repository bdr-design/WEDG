"""Trial: the tail's line as a sub-pixel contour of the side photo (coverage from how magenta a pixel is)."""
import numpy as np, sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import outlines as O
from PIL import Image
from skimage import measure
from scipy import ndimage
a = np.asarray(Image.open(O.V + '/Black_SUV_Views/01_left.png').convert('RGB')).astype(float)
cov = 1 - np.clip((np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) / 255.0, 0, 1)
cov *= ndimage.binary_dilation(O._side, iterations=3)
c = max(measure.find_contours(cov, 0.5), key=len); s = O.c['s']
x = O.L / 2 - (c[:, 1] - O.c['u0']) * s; z = (O.c['v0'] - c[:, 0]) * s
print('contour points', len(c), 'rear-most x %.5f' % x.min(), ' X_REAR %.5f' % O.X_REAR, ' front-most %.5f' % x.max(), 'X_FRONT %.5f' % O.X_FRONT)
k = np.flatnonzero((x < -2.0) & (z > 0.66) & (z < 1.62)); br = np.flatnonzero(np.diff(k) > 1)
print('runs', len(br) + 1, k[0], k[-1])
seg = k if z[k[0]] < z[k[-1]] else k[::-1]
P = np.c_[x[seg], z[seg]]; np.save('tailcontour.npy', P)
d = (P[:, 0] - x.min()) * 1000
for i in range(0, len(P), 8): print('z %.4f  d %6.2f' % (P[i, 1], d[i]))

# the render's silhouette edge drawn over the reference photo, both at the same scale (car length = 4.985 m)
import sys
from PIL import Image, ImageFilter, ImageChops
import numpy as np
ref = np.asarray(Image.open('/home/user/WEDG/assets_src/vehicles/Black_SUV_Views/01_left.webp').convert('RGB')).astype(int)
mag = (ref[..., 0] > 200) & (ref[..., 1] < 80) & (ref[..., 2] > 200)
cols = np.where((~mag).any(0))[0]; rows = np.where((~mag).any(1))[0]
x0, x1, ground = cols.min(), cols.max(), rows.max(); s_ref = 4.985 / (x1 - x0)
k = 1.925 / 2.018
r = Image.open(sys.argv[1]).convert('RGBA'); a = np.asarray(r)[..., 3] > 20
rc = np.where(a.any(0))[0]; rr = np.where(a.any(1))[0]
s_r = 4.985 / (rc.max() - rc.min())
# scale the render to the reference's px/m (horizontal), with the reference's heights squashed to the real height
scale = s_r / s_ref
R = r.resize((int(r.width * scale), int(r.height * scale / k)))
A = np.asarray(R)[..., 3] > 20
edge = A & ~(np.asarray(Image.fromarray(A.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(5))) > 0)
out = np.asarray(Image.open('/home/user/WEDG/assets_src/vehicles/Black_SUV_Views/01_left.webp').convert('RGB')).copy()
ac = np.where(A.any(0))[0]; ar = np.where(A.any(1))[0]
ox = x0 - ac.min(); oy = ground - ar.max()
ys, xs = np.where(edge)
ok = (ys + oy >= 0) & (ys + oy < out.shape[0]) & (xs + ox >= 0) & (xs + ox < out.shape[1])
out[ys[ok] + oy, xs[ok] + ox] = (0, 255, 0)
Image.fromarray(out).resize((out.shape[1] // 2, out.shape[0] // 2)).save(sys.argv[2])

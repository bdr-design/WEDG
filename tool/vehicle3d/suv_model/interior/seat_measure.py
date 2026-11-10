"""seat_side.png split into its parts: labels(), one number per pixel, and the scale and frame that take the photo
to the seat's own space (x forward, which is the photo's right; z up from the rail's foot; y across, the photo's
side at -y)."""
import numpy as np
from scipy import ndimage
from skimage.draw import polygon
import masks as M, seat_features as F
PARTS = ('backdrop', 'headrest', 'posts', 'back', 'cushion', 'base', 'rail', 'bracket', 'buckle')
def labels():
    a = M.rgb('seat_side'); body = ~M.outside(a); lum = a.mean(2); H, W = body.shape; yy, xx = np.mgrid[0:H, 0:W]
    lab = np.zeros((H, W), np.uint8); dark = body & (lum < 70)
    base = np.zeros_like(body); r, c = polygon([p[1] for p in F.BASE], [p[0] for p in F.BASE], body.shape); base[r, c] = True
    bx, by = np.array(F.BACK_FOOT).T; nfoot = 5                       # the first five points are the back's lower edge, rear to front
    ybot = np.interp(xx, bx[:nfoot], by[:nfoot]); o = np.argsort(by[nfoot - 1:]); xfront = np.interp(yy, by[nfoot - 1:][o], bx[nfoot - 1:][o])
    corner = (563, 795)                                               # the hollow corner between the back and the cushion on the outline
    back = body & ((yy < corner[1]) & (xx < np.where(yy > 750, corner[0], 9999)) | (yy >= corner[1]) & (yy < ybot + 0.5) & (xx < xfront))
    lab[body] = 4; lab[back & (yy > 300)] = 3; lab[body & (yy <= 308) & (yy > 278)] = 2; lab[body & (yy <= 278)] = 1
    lab[base & body & ~(lab == 3)] = 5
    lab[(lab == 4) & ((yy > 965) | (xx < 500) & (yy > 860))] = 5      # the slivers of body round the base's reading belong to it
    lab[dark & (yy > 1118)] = 6; lab[body & (yy > 1150)] = 6
    lab[dark & (xx < 190) & (yy > 315) & (yy < 515)] = 7
    x0, y0, x1, y1 = F.BUCKLE; lab[body & (xx > x0 - 60) & (xx < x1 + 15) & (yy > y0 - 10) & (yy < y1 + 30) & (lab == 3) & (xx > 590)] = 8
    lab[body & (xx > 590) & (yy < 760) & (lab == 3)] = 8
    return lab
def frame():
    a = M.rgb('seat_side'); body = ~M.outside(a); r, c = np.where(body); s = F.HEIGHT / (r.max() - r.min())
    x_ref, z_ref = c.min(), r.max()
    return s, (lambda rr, cc: ((np.asarray(cc) - x_ref) * s, (z_ref - np.asarray(rr)) * s)), (x_ref, z_ref)
if __name__ == '__main__':
    lab = labels(); s, to_xz, ref = frame(); print('scale %.4f mm/px' % (s * 1e3))
    for i, n in enumerate(PARTS):
        r, c = np.where(lab == i)
        if i and len(r): print('%-9s %7d px, x %.0f..%.0f mm, z %.0f..%.0f mm' % (n, len(r), *(np.array(to_xz(r.max(), c.min())[0:1] + to_xz(r.min(), c.max())[0:1]) * 1e3), to_xz(r.max(), 0)[1] * 1e3, to_xz(r.min(), 0)[1] * 1e3))
    from PIL import Image
    pal = np.array([(255, 0, 255), (240, 220, 180), (200, 200, 210), (220, 190, 140), (200, 160, 110), (170, 150, 120), (30, 30, 30), (80, 80, 90), (220, 60, 40)], np.uint8)
    Image.fromarray(pal[lab]).resize((627, 627), Image.NEAREST).save('../../int_w/seat_labels.png')

"""The chrome belt line's plan on 04_top: its distance from the centre line by station, both sides, against the
model's glass foot (front_half at the belt's height). topbelt.py"""
import sys; sys.path.insert(0, '.')
import outlines as O, body as B, greenhouse as G, numpy as np
from PIL import Image
from scipy import ndimage
a = np.asarray(Image.open(O.photo('04_top')).convert('L')).astype(float); c = O.CFG['top']
def row(x): return c['v0'] + (O.L / 2 - x) / c['s']
def line(x, sgn, lo=0.70, hi=0.95):
    v = int(round(row(x))); r = a[v - 1:v + 2].mean(0)
    u0, u1 = sorted((c['uc'] + sgn * lo / c['s'] / c['k'], c['uc'] + sgn * hi / c['s'] / c['k'])); u0, u1 = int(u0), int(u1)
    seg = r[u0:u1]; j = int(np.argmax(seg))
    if seg[j] < 150: return None, seg[j]
    k = slice(max(j - 2, 0), j + 3); w = np.clip(seg[k] - 110, 0, None); u = u0 + (np.arange(k.start, k.stop) * w).sum() / w.sum()
    return abs(u - c['uc']) * c['s'] * c['k'], seg[j]
if __name__ == '__main__':
    print('  d    photo L   photo R   mean    model(belt)  model-photo   outline(top_half)  outline-photo line')
    for d in np.arange(1.60, 4.31, 0.10):
        x = G.XF - d; yl, bl = line(x, -1); yr, br = line(x, 1)
        ym = float(O.front_half(G.bplane(d), x)) / B.TOP_TO_FRONT
        if yl is None or yr is None: print('%.2f  no line (%.0f, %.0f)   model %.4f' % (d, bl, br, ym)); continue
        m = (yl + yr) / 2; ot = float(O.top_half(x))
        print('%.2f  %.4f   %.4f   %.4f   %.4f     %+6.1f mm     %.4f      %.1f mm' % (d, yl, yr, m, ym, (ym - m) * 1e3, ot, (ot - m) * 1e3))

"""The steering wheel photo, measured: the outer outline, the four openings and the silver bezels as contours in
metres on the wheel's own plane (u right, v up, origin at the rim's centre), to a fraction of a pixel.
The photo's rim is 1159 px wide and 1186 tall (2.3 % taller than wide), an ellipse within 1.5 px all round. A wheel
that turns has to be round, so the photo is taken as stretched upward by that much: it is measured with one scale
across and another up (read()['scale'] and ['scale_v']), and the comparison renders with the same stretch. DIAMETER has no source (searched: Toyota's sheets do not give it): 0.380 m is
assumed, which makes the photo's grip 31.5 to 33 mm thick, as grips are. A game choice until a source turns up."""
import numpy as np
from scipy import ndimage
from skimage import measure
import masks as M
DIAMETER = 0.380
def read():
    a = M.rgb('wheel'); bd = M.backdrop(a); out = M.outside(a); cov = 1 - np.clip((np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) / 250.0, 0, 1)
    filled = ndimage.binary_fill_holes(~out); edge = filled ^ ndimage.binary_erosion(filled); er, ec = np.where(edge)
    # an ellipse with level axes: A x2 + B y2 + C x + D y = 1
    sol = np.linalg.lstsq(np.c_[ec ** 2, er ** 2, ec, er], np.ones(len(ec)), rcond=None)[0]; A, B, C, D = sol
    cx, cy = -C / (2 * A), -D / (2 * B); k = 1 + A * cx * cx + B * cy * cy; Ru, Rv = float(np.sqrt(k / A)), float(np.sqrt(k / B))
    res = np.hypot((ec - cx) / Ru, (er - cy) / Rv) - 1; R = (Ru + Rv) / 2
    s, sv = DIAMETER / 2 / Ru, DIAMETER / 2 / Rv
    def uv(c): return np.c_[(c[:, 1] - cx) * s, (cy - c[:, 0]) * sv]
    cs = sorted(measure.find_contours(cov, 0.5), key=len, reverse=True)
    outer = uv(cs[0]); holes = [uv(c) for c in cs[1:] if len(c) > 300]
    lum = a.mean(2); sat = a.max(2) - a.min(2); silver = ndimage.binary_opening((~bd) & (lum > 120) & (sat < 30), iterations=2)
    lab, k = ndimage.label(silver); sizes = ndimage.sum(silver, lab, range(1, k + 1))
    bez = [uv(max(measure.find_contours((lab == i + 1).astype(float), 0.5), key=len)) for i in np.argsort(sizes)[::-1] if sizes[i] > 800]
    return dict(scale=s, scale_v=sv, centre=(cx, cy), radius_px=R, radii_px=(Ru, Rv), off_ellipse_px=float(np.abs(res).max() * R), outer=outer, holes=holes, silver=bez)
if __name__ == '__main__':
    d = read(); print('scale %.4f mm/px across, %.4f up; centre %.1f %.1f; radii %.1f x %.1f px; the outline is within %.1f px of that ellipse' % (d['scale'] * 1e3, d['scale_v'] * 1e3, *d['centre'], *d['radii_px'], d['off_ellipse_px']))
    r = np.hypot(*d['outer'].T); print('outer outline: radius %.1f to %.1f mm' % (r.min() * 1e3, r.max() * 1e3))
    for h in d['holes']: print('opening: %d points, u %.1f..%.1f mm, v %.1f..%.1f mm' % (len(h), h[:, 0].min() * 1e3, h[:, 0].max() * 1e3, h[:, 1].min() * 1e3, h[:, 1].max() * 1e3))
    for b in d['silver']: print('silver: %d points, u %.1f..%.1f mm, v %.1f..%.1f mm' % (len(b), b[:, 0].min() * 1e3, b[:, 0].max() * 1e3, b[:, 1].min() * 1e3, b[:, 1].max() * 1e3))

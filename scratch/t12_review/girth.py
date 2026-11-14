import sys, numpy as np
sys.path.insert(0, '.')
from slice import cut, pt
for x in (-150, -90, 0, 100, 180):
    c = cut(x, axis=0); c = c[c[:, 1] > 200]
    if not len(c): continue
    cen = c.mean(0); a = np.arctan2(c[:, 1] - cen[1], c[:, 2] - cen[2]); c = c[np.argsort(a)]
    q = np.vstack([c, c[:1]]); per = np.linalg.norm(np.diff(q[:, [1, 2]], axis=0), axis=1).sum()
    print(f'x {x}: girth {per:.0f} mm  depth {np.ptp(c[:,1]):.0f}  width {np.ptp(c[:,2]):.0f}  bottom {c[:,1].min():.0f}')

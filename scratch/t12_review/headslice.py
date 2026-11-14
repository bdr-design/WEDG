import sys, numpy as np
sys.path.insert(0, '.')
from slice import cut, pt
for x in range(int(pt['nose'][0]) - 10, int(pt['nose'][0]) - 260, -20):
    c = cut(x, axis=0); c = c[c[:, 1] > pt['nose'][1] - 120] if len(c) else c
    if len(c): print(f'x {x} ({pt["nose"][0]-x:.0f} mm behind the nose tip): width {np.ptp(c[:,2]):5.1f}  height {np.ptp(c[:,1]):5.1f}  top {c[:,1].max():.0f} bottom {c[:,1].min():.0f}')

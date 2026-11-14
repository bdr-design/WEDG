import sys, numpy as np
sys.path.insert(0, '.')
from slice import cut, pt
e = pt['ear_l']
for dh in (30, 50, 70):
    c = cut(e[1] + dh); c = c[(np.abs(c[:, 2] - e[2]) < 70) & (np.abs(c[:, 0] - e[0]) < 70) & (c[:, 2] * np.sign(e[2]) > 0)]
    if len(c) < 3: continue
    Q = c[:, [0, 2]] - c[:, [0, 2]].mean(0); s = np.linalg.svd(Q, compute_uv=False)
    _, _, vt = np.linalg.svd(Q); proj = Q @ vt.T
    print(f'ear {dh} mm above its base: width {np.ptp(proj[:,0]):.0f} mm, thickness {np.ptp(proj[:,1]):.1f} mm')

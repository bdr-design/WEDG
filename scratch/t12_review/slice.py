import sys, numpy as np
sys.path.insert(0, '.')
from canid_check import load
js, prims, pts, V, tex, mem = load(sys.argv[1]); P, I = prims[0]['P'] * 1000, prims[0]['I']
def cut(h, axis=1):
    d = P[:, axis] - h; out = []
    for t in I:
        a = d[t]
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if a[i] * a[j] < 0:
                s = a[i] / (a[i] - a[j]); out.append(P[t[i]] + s * (P[t[j]] - P[t[i]]))
    return np.array(out)
pt = {k: v * 1000 for k, v in pts.items()}
for name, foot, top in (('fore L', 'foot_fl', 'elbow_l'), ('hind L', 'foot_hl', 'stifle_l')):
    f = pt[foot]
    for h in range(30, 461, 30):
        c = cut(h); c = c[(c[:, 2] < -5) & (np.abs(c[:, 0] - f[0]) < 200)] if len(c) else c
        if len(c): print(f'{name} y={h:3d}: fore-aft {np.ptp(c[:,0]):5.1f} lateral {np.ptp(c[:,2]):5.1f}  x {c[:,0].min():.0f}..{c[:,0].max():.0f}')

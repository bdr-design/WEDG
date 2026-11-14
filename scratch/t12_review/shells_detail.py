import sys, numpy as np
sys.path.insert(0, '.')
from canid_check import load
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
js, prims, pts, V, tex, mem = load(sys.argv[1]); p = prims[0]; P, I = p['P'], p['I']
key = np.round(P / 1e-5).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
T = inv[I]; n = inv.max() + 1; e = np.vstack([T[:, [0, 1]], T[:, [1, 2]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
tl = lab[T[:, 0]]
for k in np.unique(tl):
    vi = np.unique(I[tl == k]); Q = P[vi] * 1000
    lo, hi = Q.min(0), Q.max(0)
    print(f'shell {k:2d} tris {(tl==k).sum():5d}  x {lo[0]:6.0f}..{hi[0]:6.0f}  y {lo[1]:5.0f}..{hi[1]:5.0f}  z {lo[2]:5.0f}..{hi[2]:5.0f}')
# cross sections of the left foreleg (z<0) and hind leg: lateral (z) and fore-aft (x) extents at heights
for name, xc in (('fore', pts['foot_fl'][0]), ('hind', pts['foot_hl'][0])):
    for h in (40, 80, 130, 180, 230, 280, 330, 380):
        s = V[(np.abs(V[:, 1] * 1000 - h) < 4) & (V[:, 2] < -0.005) & (np.abs(V[:, 0] - xc) < 0.17)] * 1000
        if len(s): print(f'{name} leg at {h} mm: fore-aft {np.ptp(s[:,0]):5.1f}  lateral {np.ptp(s[:,2]):5.1f}  (n {len(s)})')
for k in sorted(pts): print(k, np.round(pts[k] * 1000).astype(int))

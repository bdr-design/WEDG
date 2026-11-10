"""The black band under the side glass: its lower edge by station (photo frame), and how ragged it is.
bandedge.py <blend>"""
import sys, bpy, numpy as np
sys.path.insert(0, '.'); sys.path.insert(0, '..')
import realframe as RF
XF = 2.498
def bplane(d): return 1.336 + (d - 2.298) * 0.0293
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
ob = bpy.data.objects['body']; me = ob.data
names = [m.name for m in me.materials]
ti = [i for i, n in enumerate(names) if 'trim' in n]
V = np.array([ob.matrix_world @ v.co for v in me.vertices])
D = XF - RF.x_photo(V[:, 0]); Z = RF.z_photo(V[:, 2])
for sgn in (1, -1):
    lo = {}
    for p in me.polygons:
        if p.material_index not in ti: continue
        vs = list(p.vertices); d = D[vs].mean(); z = Z[vs].mean()
        if V[vs, 1].mean() * sgn < 0.45 or not (bplane(d) - 0.06 < z < bplane(d) + 0.002) or not 1.6 < d < 4.33: continue
        for vi in vs:
            b = round(D[vi] / 0.01); lo[b] = min(lo.get(b, 9), Z[vi] - bplane(D[vi]))
    bs = sorted(lo); d = np.array(bs) * 0.01; zl = np.array([lo[b] for b in bs])
    for a, b_, nm in ((1.66, 2.10, 'front door fwd'), (2.10, 2.64, 'front door aft'), (2.85, 3.6, 'rear door'), (3.8, 4.3, 'quarter')):
        k = (d > a) & (d < b_)
        if k.sum() < 4: print(nm, 'no faces'); continue
        print('side %+d %-15s lower edge under the belt: %.1f to %.1f mm (p-p %.1f, sd %.1f)' % (sgn, nm, -zl[k].max() * 1e3, -zl[k].min() * 1e3, np.ptp(zl[k]) * 1e3, zl[k].std() * 1e3))

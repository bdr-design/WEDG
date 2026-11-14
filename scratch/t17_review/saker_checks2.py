import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import Rig
from glb_read import accessor
from motion import inside_count, tri_area_n
from contact import load
if __name__ == '__main__': R = Rig(sys.argv[1]); SV, SI = load(sys.argv[2])
if __name__ == '__main__': names = [R.nodes[j].get('name') for j in R.skins[0]['joints']]
def mesh(clip, t, name): return next(m for m in R.skinned(clip, t) if m['node'] == name)
def bone_set(name, words):
    m = next(m for m in R.skinned(None, 0) if m['node'] == name); p = m['prim']
    jt = accessor(R.js, R.b, p['attributes']['JOINTS_0']).astype(int); wt = accessor(R.js, R.b, p['attributes']['WEIGHTS_0']).astype(float)
    ids = [k for k, n in enumerate(names) if any(n.startswith(w) for w in words)]
    w = sum(np.where(jt[:, k] == i, wt[:, k], 0) for k in range(jt.shape[1]) for i in ids); return np.where(w > 0.5)[0]
def pt_tri(p, a, b, c):  # exact distance point to many triangles (Ericson)
    ab, ac, ap = b - a, c - a, p - a; d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    n = np.cross(ab, ac); nn = (n * n).sum(1); dist_plane = np.abs((ap * n).sum(1)) / np.sqrt(np.maximum(nn, 1e-30))
    # barycentric projection
    v = ((ab * ab).sum(1) * d2 - (ab * ac).sum(1) * d1) / np.maximum(nn, 1e-30); u = ((ac * ac).sum(1) * d1 - (ab * ac).sum(1) * d2) / np.maximum(nn, 1e-30)
    inside = (u >= 0) & (v >= 0) & (u + v <= 1); d = np.where(inside, dist_plane, np.inf)
    def seg(p, x, y):
        e = y - x; t = np.clip(((p - x) * e).sum(1) / np.maximum((e * e).sum(1), 1e-30), 0, 1); return np.linalg.norm(p - (x + e * t[:, None]), axis=1)
    return np.minimum(d, np.minimum(seg(p, a, b), np.minimum(seg(p, b, c), seg(p, a, c)))).min()
if __name__ == "__main__":
  A, B, C = SV[SI[:, 0]], SV[SI[:, 1]], SV[SI[:, 2]]
    toes = bone_set('saker_fold', ('toe',))
    for clip, f in (('cast_off', 0), ('land_cuff', 45)):
        P = mesh(clip, f / 30, 'saker_fold')['V'][toes]; ins = inside_count(P, A, B, C)
        d = sorted([pt_tri(p, A, B, C) * 1000 for p in P[ins]], reverse=True)
        print(clip, f, 'inside', int(ins.sum()), 'exact depth mm (top 6):', [round(x, 2) for x in d[:6]], 'where (mm):', np.round(P[ins][:3] * 1000).astype(int).tolist())
    toesO = bone_set('saker_open', ('toe',))
    jt = None
    for clip, fr in (('flight', range(0, 7)), ('cast_off', range(13, 41, 3))):
        for f in fr:
            m = mesh(clip, f / 30, 'saker_open'); V, I = m['V'], m['I']
            nonfoot = ~np.isin(I, bone_set('saker_open', ('toe', 'tarsus', 'shank', 'jess'))).any(1)
            ins = inside_count(V[toesO], V[I[nonfoot, 0]], V[I[nonfoot, 1]], V[I[nonfoot, 2]])
            print(f'{clip} f{f}: toe vertices outside the body {int((~ins).sum())} of {len(toesO)}')
    shown = {'cast_off': lambda f: 'saker_fold' if f < 13 else 'saker_open', 'flight': lambda f: 'saker_open', 'land_cuff': lambda f: 'saker_open' if f < 39 else 'saker_fold'}
    base = {m['node']: m for m in R.skinned(None, 0)}
    for clip in R.clips:
        d = max(c['T'][-1] for c in R.clips[clip]); res = []
        for f in range(int(round(d * 30)) + 1):
            nm = shown[clip](f); m = mesh(clip, f / 30, nm); b = base[nm]
            a0, n0 = tri_area_n(b['V'], b['I']); a1, n1 = tri_area_n(m['V'], m['I']); ok = a0 > 1e-10; rr = a1[ok] / a0[ok]
            res.append((f, rr.min(), rr.max(), int(((rr < 0.3) | (rr > 3)).sum())))
        lo = min(res, key=lambda x: x[1]); hi = max(res, key=lambda x: x[2])
        print(f'stretch {clip} (shown mesh): min {lo[1]:.3f} f{lo[0]}, max {hi[2]:.2f} f{hi[0]}; frames with triangles beyond 0.3..3: {[(f, n) for f, _, _, n in res if n][:20]}')

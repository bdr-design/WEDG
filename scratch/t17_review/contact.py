#!/usr/bin/env python3
"""T11 reviewer: how the bird's low vertices (toes, talons) sit on a support mesh: how many are inside it (ray parity)
and how deep, and the gap of the toe undersides. usage: contact.py bird.glb support.glb [ymax_m]"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb, accessor
from bird_check import world_nodes
def load(f, skip=()):
    js, b = read_glb(f); nodes, world, _ = world_nodes(js); Ps, Is, off = [], [], 0
    for i, n in enumerate(nodes):
        if 'mesh' not in n or i not in world or any(s in n.get('name', '') for s in skip): continue
        for pr in js['meshes'][n['mesh']]['primitives']:
            P = accessor(js, b, pr['attributes']['POSITION']).astype(float); P = (world[i][:3, :3] @ P.T).T + world[i][:3, 3]
            Ps.append(P); Is.append(accessor(js, b, pr['indices']).ravel().reshape(-1, 3) + off); off += len(P)
    return np.vstack(Ps), np.vstack(Is)
if __name__ == "__main__":
    B, _ = load(sys.argv[1], skip=('hood', 'jess')); S, SI = load(sys.argv[2]); ymax = float(sys.argv[3]) if len(sys.argv) > 3 else 0.03
    low = B[B[:, 1] < ymax]
    A, Bv, C = S[SI[:, 0]], S[SI[:, 1]], S[SI[:, 2]]
    def inside(p):  # ray +X parity
        d = np.array([1.0, 0.31, 0.17]); d /= np.linalg.norm(d); e1, e2 = Bv - A, C - A; h = np.cross(d, e2); a = (e1 * h).sum(1)
        ok = np.abs(a) > 1e-12; f = np.where(ok, 1 / np.where(ok, a, 1), 0); s = p - A; u = f * (s * h).sum(1); q = np.cross(s, e1)
        v = f * (q @ d); t = f * (e2 * q).sum(1); return int(((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9) & ok).sum()) % 2 == 1
    def dist(p):  # distance to the nearest triangle (via nearest vertex + centroid approximation, fine for 1 mm)
        cen = (A + Bv + C) / 3; return np.sqrt(((cen - p) ** 2).sum(1)).min()
    ins = [p for p in low if inside(p)]
    print(f'{os.path.basename(sys.argv[1])} on {os.path.basename(sys.argv[2])}: {len(low)} low vertices, {len(ins)} inside the support')
    if ins: print('  deepest inside (mm, approx):', round(max(dist(p) for p in ins) * 1000, 1))
    # vertical gap under each low vertex cluster: lowest vertices per 10 mm x-z cell vs support surface below
    gaps = []
    for p in low:
        if inside(p): continue
        gaps.append(dist(p))
    gaps = np.array(gaps) * 1000
    print('  outside vertices: nearest-surface distance mm  min %.1f  median %.1f; count within 3 mm: %d' % (gaps.min(), np.median(gaps), (gaps < 3).sum()))
    def ray_t(p, d):
        e1, e2 = Bv - A, C - A; h = np.cross(d, e2); a = (e1 * h).sum(1)
        ok = np.abs(a) > 1e-12; f = np.where(ok, 1 / np.where(ok, a, 1), 0); s = p - A; u = f * (s * h).sum(1); q = np.cross(s, e1)
        v = f * (q @ d); t = f * (e2 * q).sum(1); m = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9) & ok
        return t[m].min() if m.any() else np.inf
    if ins:
        dep = []
        for p in ins:  # depth = shortest way out among 26 directions
            best = np.inf
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx == dy == dz == 0: continue
                        d = np.array([dx, dy, dz], float); d /= np.linalg.norm(d); best = min(best, ray_t(p, d))
            dep.append((best, p))
        dep.sort(key=lambda x: -x[0])
        print('  depth inside, mm: max %.1f, 90th pct %.1f, median %.1f' % (dep[0][0] * 1000, np.percentile([x[0] for x in dep], 90) * 1000, np.median([x[0] for x in dep]) * 1000))
        print('  deepest at (mm):', [np.round(x[1] * 1000).astype(int).tolist() for x in dep[:4]])
        from collections import Counter
        cl = Counter(tuple((np.round(x[1] * 100) * 10).astype(int).tolist()) for x in dep if x[0] > 0.004)
        print('  inside deeper than 4 mm, by 10 mm cell (x,y,z mm): count', sorted(cl.items()))

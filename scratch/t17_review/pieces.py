#!/usr/bin/env python3
"""T11 reviewer: face direction per piece. Pieces = triangles connected through shared vertex indices (as exported).
Per piece, after welding by position: boundary edges, directed edges used twice (inconsistent winding), signed
volume (negative = inside out). usage: pieces.py file.glb ...  (prints only problems unless -v)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb, accessor
from bird_check import world_nodes
verbose = '-v' in sys.argv
tot_bad = 0
for f in [x for x in sys.argv[1:] if x != '-v']:
    js, b = read_glb(f); nodes, world, _ = world_nodes(js); npieces = 0; bad = []
    for i, n in enumerate(nodes):
        if 'mesh' not in n or i not in world: continue
        for pr in js['meshes'][n['mesh']]['primitives']:
            P = accessor(js, b, pr['attributes']['POSITION']).astype(float); P = (world[i][:3, :3] @ P.T).T + world[i][:3, 3]
            I = accessor(js, b, pr['indices']).ravel().reshape(-1, 3)
            # weld by position first (a loft's seams are split by texture coordinates), then pieces by welded connectivity
            _, inv = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_inverse=True); T = inv.ravel()[I]
            par = np.arange(T.max() + 1)
            def find(x):
                while par[x] != x: par[x] = par[par[x]]; x = par[x]
                return x
            for a_, b_, c_ in T:
                ra, rb, rc = find(a_), find(b_), find(c_); par[rb] = ra; par[find(rc)] = ra
            root = np.array([find(t[0]) for t in T])
            for r in np.unique(root):
                k = root == r; Tk = T[k]; Ik = I[k]; npieces += 1
                E = np.vstack([Tk[:, [0, 1]], Tk[:, [1, 2]], Tk[:, [2, 0]]])
                Es = np.sort(E, 1); _, cu = np.unique(Es, axis=0, return_counts=True); _, cd = np.unique(E, axis=0, return_counts=True)
                vol = np.einsum('ij,ij->i', P[Ik[:, 0]], np.cross(P[Ik[:, 1]], P[Ik[:, 2]])).sum() / 6
                c = P[Ik].reshape(-1, 3).mean(0)
                prob = []
                if (cu == 1).any(): prob.append(f'open {int((cu == 1).sum())}')
                if (cd > 1).any(): prob.append(f'flipped-neighbour edges {int((cd > 1).sum())}')
                if vol <= 0: prob.append('INSIDE OUT' if vol < 0 else 'zero volume')
                if prob or verbose:
                    bad.append(f'  {n.get("name")} piece {len(Tk)} tris at {np.round(c*1000).astype(int)} mm vol {vol*1e6:.3f} cm3 {"; ".join(prob)}')
    print(f'{os.path.basename(f)}: {npieces} pieces, {len([x for x in bad if "open" in x or "flip" in x or "INSIDE" in x or "zero" in x])} with a problem')
    for x in bad: print(x)
    tot_bad += len(bad)

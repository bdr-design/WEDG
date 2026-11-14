#!/usr/bin/env python3
"""T11 reviewer: winding consistency of every primitive (after welding by position): in a closed, consistently wound
mesh every directed edge appears once. Prints directed edges used twice (= neighbouring faces wound oppositely), and
the signed volume (negative = turned inside out). usage: winding.py file.glb ..."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb, accessor
from bird_check import world_nodes
for f in sys.argv[1:]:
    js, b = read_glb(f); nodes, world, _ = world_nodes(js)
    for i, n in enumerate(nodes):
        if 'mesh' not in n or i not in world: continue
        for pr in js['meshes'][n['mesh']]['primitives']:
            P = accessor(js, b, pr['attributes']['POSITION']).astype(float); P = (world[i][:3, :3] @ P.T).T + world[i][:3, 3]
            I = accessor(js, b, pr['indices']).ravel().reshape(-1, 3)
            _, inv = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True); T = inv.ravel()[I]
            E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
            _, c = np.unique(E, axis=0, return_counts=True)
            vol = np.einsum('ij,ij->i', P[I[:, 0]], np.cross(P[I[:, 1]], P[I[:, 2]])).sum() / 6
            print(f'{os.path.basename(f):24s} {n.get("name"):16s} directed edges used twice: {int((c > 1).sum()):4d}  signed volume {vol*1e6:9.1f} cm3')

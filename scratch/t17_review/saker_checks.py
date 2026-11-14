#!/usr/bin/env python3
"""T17 reviewer: the saker rig's per-frame checks. usage: saker_checks.py rig.glb cuff.glb"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import Rig
from glb_read import accessor
from motion import inside_count, depth_out, tri_area_n
from contact import load
R = Rig(sys.argv[1]); SV, SI = load(sys.argv[2]); A, B, C = SV[SI[:, 0]], SV[SI[:, 1]], SV[SI[:, 2]]
names = [R.nodes[j].get('name') for j in R.skins[0]['joints']]
def mesh(clip, t, name): return next(m for m in R.skinned(clip, t) if m['node'] == name)
def jw(name):
    m = next(m for m in R.skinned(None, 0) if m['node'] == name); p = m['prim']
    return accessor(R.js, R.b, p['attributes']['JOINTS_0']).astype(int), accessor(R.js, R.b, p['attributes']['WEIGHTS_0']).astype(float)
def bone_set(name, words):
    jt, wt = jw(name); ids = [k for k, n in enumerate(names) if any(n.startswith(w) for w in words)]
    w = sum(np.where(jt[:, k] == i, wt[:, k], 0) for k in range(jt.shape[1]) for i in ids); return np.where(w > 0.5)[0]
info = {'cast_off': (0, 12, 'saker_fold', 13), 'land_cuff': (39, 45, 'saker_fold', None)}
# 1) contact frames: toe/talon depth in the cuff and foot slide, by frame
for clip, (f0, f1, mname, _) in info.items():
    toes = bone_set(mname, ('toe',)); ref = None; worst = []; slide = 0
    for f in range(f0, f1 + 1):
        V = mesh(clip, f / 30, mname)['V']; P = V[toes]
        ins = inside_count(P, A, B, C); d = max([depth_out(p, A, B, C) for p in P[ins]] or [0]) * 1000
        if ref is None: ref = P
        slide = max(slide, np.linalg.norm(P - ref, axis=1).max() * 1000); worst.append((f, int(ins.sum()), d))
    w = max(worst, key=lambda x: x[2]); print(f'{clip} f{f0}-{f1} ({mname}): toe vertices {len(toes)}; deepest inside the cuff {w[2]:.1f} mm at f{w[0]} ({w[1]} inside); toe slide max {slide:.1f} mm')
# also land_cuff contact frames on the open mesh before the swap (feet touch about f28)
toes = bone_set('saker_open', ('toe',)); ref = None; out = []
for f in range(26, 39):
    P = mesh('land_cuff', f / 30, 'saker_open')['V'][toes]; ins = inside_count(P, A, B, C); d = max([depth_out(p, A, B, C) for p in P[ins]] or [0]) * 1000
    out.append((f, int(ins.sum()), round(d, 1)))
print('land_cuff open mesh f26-38 (frame, toe verts inside cuff, deepest mm):', out)
# 2) flying frames: foot vertices visible (outside the body), wing vertices inside the body
feet = bone_set('saker_open', ('toe', 'tarsus')); wing = bone_set('saker_open', ('wing_fore', 'wing_hand'))
jt, wt = jw('saker_open'); bodyb = [k for k, n in enumerate(names) if n in ('body', 'tail', 'neck1', 'neck2', 'head')]
bw = sum(np.where(jt[:, k] == i, wt[:, k], 0) for k in range(jt.shape[1]) for i in bodyb); bodyv = np.where(bw > 0.99)[0]
for clip, fr in (('flight', range(0, 14)), ('cast_off', range(13, 41)), ('land_cuff', range(0, 39))):
    rows = []
    for f in fr:
        m = mesh(clip, f / 30, 'saker_open'); V, I = m['V'], m['I']
        keep = np.isin(I, bodyv).all(1); a, b, c = V[I[keep, 0]], V[I[keep, 1]], V[I[keep, 2]]
        fo = int((~inside_count(V[feet], a, b, c)).sum()); wi = int(inside_count(V[wing], a, b, c).sum())
        rows.append((f, fo, wi))
    print(f'{clip}: frames with feet vertices outside the body: {[(f, n) for f, n, _ in rows if n > 0][:40]}')
    print(f'{clip}: frames with forearm/hand vertices inside the body: {[(f, n) for f, _, n in rows if n > 0][:40]}  (feet verts {len(feet)}, wing verts {len(wing)})')
# 3) stretch per clip, both meshes, against the rest pose
for clip in R.clips:
    d = max(c['T'][-1] for c in R.clips[clip]); lo, hi, fl = 9, 0, 0
    base = {m['node']: m for m in R.skinned(None, 0)}
    for f in range(int(round(d * 30)) + 1):
        for m in R.skinned(clip, f / 30):
            b = base[m['node']]; a0, n0 = tri_area_n(b['V'], b['I']); a1, n1 = tri_area_n(m['V'], m['I']); ok = a0 > 1e-10
            rr = a1[ok] / a0[ok]
            if rr.min() < lo: lo, wlo = rr.min(), (f, m['node'])
            if rr.max() > hi: hi, whi = rr.max(), (f, m['node'])
    print(f'stretch {clip}: area ratio min {lo:.3f} at {wlo}, max {hi:.2f} at {whi}')

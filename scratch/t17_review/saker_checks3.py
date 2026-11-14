#!/usr/bin/env python3
"""T17 reviewer: the full saker set, per frame, on the mesh actually shown (morph 'hidden' < 0.5).
usage: saker_checks3.py rig.glb dass.glb wakr.glb"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import Rig
from glb_read import accessor
from motion import inside_count, tri_area_n
from contact import load
from ptt import pt_tri
R = Rig(sys.argv[1]); names = [R.nodes[j].get('name') for j in R.skins[0]['joints']]
sup = {}
for k, f in (('cuff', sys.argv[2]), ('perch', sys.argv[3])):
    SV, SI = load(f); sup[k] = (SV[SI[:, 0]], SV[SI[:, 1]], SV[SI[:, 2]])
on = {'perch_idle': 'perch', 'rouse': 'perch', 'hood_off': 'cuff', 'hood_on': 'cuff', 'cast_off': 'cuff', 'land_cuff': 'cuff', 'land_perch': 'perch'}
fly = ('flight', 'glide', 'stoop')
def bone_set(m, words):
    p = m['prim']; jt = accessor(R.js, R.b, p['attributes']['JOINTS_0']).astype(int); wt = accessor(R.js, R.b, p['attributes']['WEIGHTS_0']).astype(float)
    ids = [k for k, n in enumerate(names) if any(n.startswith(w) for w in words)]
    w = sum(np.where(jt[:, k] == i, wt[:, k], 0) for k in range(jt.shape[1]) for i in ids); return np.where(w > 0.5)[0]
base = {m['node']: dict(m, V=accessor(R.js, R.b, m['prim']['attributes']['POSITION']).astype(float)) for m in R.skinned(None, 0)}
sets = {n: (bone_set(base[n], ('toe',)), bone_set(base[n], ('toe', 'tarsus')), bone_set(base[n], ('wing_fore', 'wing_hand')), bone_set(base[n], ('body', 'tail', 'neck', 'head'))) for n in ('saker_fold', 'saker_open')}
step = int(sys.argv[4]) if len(sys.argv) > 4 else 1
for clip in R.clips:
    d = max(c['T'][-1] for c in R.clips[clip]); nf = int(round(d * 30)) + 1
    deep, slide_ref, slide, feet_out, wing_in, st_lo, st_hi, bad, perch_pen = [], None, 0, [], [], 9, 0, [], []
    for f in range(0, nf, step):
        ms = R.skinned(clip, f / 30)
        for m in ms:
            if m['node'] not in sets or (m['morph'] and m['morph'][0] >= 0.5): continue
            toes, feet, wing, bodyb = sets[m['node']]; V, I = m['V'], m['I']
            b = base[m['node']]; a0, _ = tri_area_n(b['V'], b['I']); a1, _ = tri_area_n(V, I); ok = a0 > 1e-10; rr = a1[ok] / a0[ok]
            st_lo, st_hi = min(st_lo, rr.min()), max(st_hi, rr.max()); nb = int(((rr < 0.25) | (rr > 4)).sum())
            if nb: bad.append((f, nb))
            if clip in on:
                A, B, C = sup[on[clip]]; P = V[toes]; near = P[:, 1] < 0.05
                ins = np.zeros(len(P), bool); ins[near] = inside_count(P[near], A, B, C)
                dd = max([pt_tri(p, A, B, C) * 1000 for p in P[ins]] or [0]); deep.append((f, int(ins.sum()), round(dd, 2)))
                # whole-bird penetration into the support (not the toes)
                rest = np.setdiff1d(np.arange(len(V)), feet); Q = V[rest]; close = (np.abs(Q[:, 0]) < 0.12) & (Q[:, 1] < 0.03) & (np.abs(Q[:, 2]) < 0.12)
                if close.any():
                    pi = inside_count(Q[close], A, B, C)
                    if pi.any(): perch_pen.append((f, int(pi.sum())))
            keep = np.isin(I, sets[m['node']][3]).all(1); a, bb, c = V[I[keep, 0]], V[I[keep, 1]], V[I[keep, 2]]
            if clip in fly or (clip in ('cast_off', 'land_cuff', 'land_perch') and m['node'] == 'saker_open'):
                fo = int((~inside_count(V[toes], a, bb, c)).sum()); feet_out.append((f, fo))
            wi = int(inside_count(V[wing], a, bb, c).sum())
            if wi: wing_in.append((f, wi))
    print(f'=== {clip} ({nf} frames)')
    if deep:
        w = max(deep, key=lambda x: x[2]); print(f'  toes inside the {on[clip]}: worst f{w[0]} {w[1]} verts, deepest {w[2]} mm; frames over 1 mm: {[x[0] for x in deep if x[2] > 1][:15]}')
        if perch_pen: print(f'  other bird vertices inside the {on[clip]} (frame, count): {perch_pen[:12]}')
    if feet_out: print(f'  toe vertices outside the body (frame, n) where n>0: {[x for x in feet_out if x[1]][:20]}')
    print(f'  forearm/hand vertices inside the body: {wing_in[:12]}; area ratio {st_lo:.3f}..{st_hi:.2f}; frames with triangles beyond 0.25..4: {bad[:12]}')

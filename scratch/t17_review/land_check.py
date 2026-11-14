#!/usr/bin/env python3
"""T17 reviewer: every frame of the support clips: bird vertices (shown meshes) inside the cuff/perch (exact depth),
and inside a level forearm (cylinder r 45 mm along -x from the cuff's forearm point to 400 mm behind it)."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import Rig
from motion import inside_count
from contact import load
from ptt import pt_tri
R = Rig(sys.argv[1]); sup = {}
for k, f in (('cuff', sys.argv[2]), ('perch', sys.argv[3])):
    SV, SI = load(f); sup[k] = (SV[SI[:, 0]], SV[SI[:, 1]], SV[SI[:, 2]])
FA0 = np.array([-0.06, -0.052, 0.0]); FAL = 0.40; FAR = 0.045
near = ['saker_fold', 'saker_open']
for clip, s in (('cast_off', 'cuff'), ('land_cuff', 'cuff'), ('land_perch', 'perch'), ('hood_off', 'cuff'), ('perch_hooded', 'perch'), ('perch_idle', 'perch'), ('rouse', 'perch')):
    if clip not in R.clips: continue
    d = max(c['T'][-1] for c in R.clips[clip]); rows = []
    for f in range(int(round(d * 30)) + 1):
        V = np.vstack([m['V'] for m in R.skinned(clip, f / 30) if m['node'] in near and not (m['morph'] and m['morph'][0] >= 0.5)])
        A, B, C = sup[s]; lo, hi = A.min(0) - 0.01, A.max(0) + 0.01; cand = V[((V > lo) & (V < hi)).all(1)]
        ins = inside_count(cand, A, B, C) if len(cand) else np.zeros(0, bool)
        dd = max([pt_tri(p, A, B, C) * 1000 for p in cand[ins]] or [0])
        fa = 0
        if s == 'cuff':
            q = V - FA0; along = -q[:, 0]; rad = np.hypot(q[:, 1], q[:, 2]); fa = int(((along > 0) & (along < FAL) & (rad < FAR)).sum())
        rows.append((f, int(ins.sum()), round(dd, 2), fa))
    bad = [r for r in rows if r[2] > 1.0 or r[3] > 0]
    print(f'{clip} on {s}: worst depth {max(r[2] for r in rows):.2f} mm (frame {max(rows, key=lambda r: r[2])[0]}); frames over 1 mm or into the forearm (f, n inside, depth, n in forearm): {bad[:30]}')

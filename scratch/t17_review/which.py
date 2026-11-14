import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import Rig; from glb_read import accessor
from motion import inside_count; from contact import load; from ptt import pt_tri
from collections import Counter
R = Rig(sys.argv[1]); SV, SI = load(sys.argv[2]); A, B, C = SV[SI[:, 0]], SV[SI[:, 1]], SV[SI[:, 2]]
names = [R.nodes[j].get('name') for j in R.skins[0]['joints']]
for spec in sys.argv[3:]:
    clip, f = spec.split(':'); f = int(f)
    for m in R.skinned(clip, f / 30):
        if m['node'] not in ('saker_fold', 'saker_open') or (m['morph'] and m['morph'][0] >= 0.5): continue
        V = m['V']; lo, hi = A.min(0) - 0.01, A.max(0) + 0.01; ix = np.where(((V > lo) & (V < hi)).all(1))[0]
        ins = ix[inside_count(V[ix], A, B, C)]
        jt = accessor(R.js, R.b, m['prim']['attributes']['JOINTS_0']).astype(int)
        dd = [(round(pt_tri(V[k], A, B, C) * 1000, 1), names[jt[k, 0]]) for k in ins]
        by = Counter(n for _, n in dd); mx = {}
        for d, n in dd: mx[n] = max(mx.get(n, 0), d)
        print(clip, f, m['node'], {n: (by[n], mx[n]) for n in by})

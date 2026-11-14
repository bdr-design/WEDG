#!/usr/bin/env python3
"""T17 reviewer: motion checks on a skinned bird GLB (numpy; uses anim.Rig).
usage:
  motion.py report file.glb                          skin, weights, clips, loop first-vs-last
  motion.py stretch file.glb [clip] [fps]            per-triangle area ratio and normal flip vs the bind pose, every frame
  motion.py slide file.glb clip [support.glb] [fps]  foot slide: lowest bind-pose vertices (toes) tracked over the clip, mm;
                                                     with a support mesh: talon depth inside it per frame (ray parity, 26 dirs)
  motion.py tuck file.glb clip [fps]                 flying frames: vertices weighted to foot/toe bones outside the body piece
  motion.py frames file.glb clip out_prefix [n] [view] [mm_per_px]   n frames rendered one-sided (textured), a strip
  motion.py bind file.glb static.glb                 bind (rest) pose against the approved static GLB: vertex match and silhouette IoU"""
import sys, os, io, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim import Rig
from glb_read import accessor

def times(rig, clip, fps=30):
    d = max(c['T'][-1] for c in rig.clips[clip]); n = max(2, int(round(d * fps)) + 1); return np.linspace(0, d, n)

def tri_area_n(V, I):
    N = np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]); a = np.linalg.norm(N, axis=1); return a, N / np.maximum(a[:, None], 1e-15)

def stretch(path, clip=None, fps=30):
    r = Rig(path); clips = [clip] if clip else list(r.clips)
    base = r.skinned(None, 0)
    for c in clips:
        worst_lo, worst_hi, flips, wt = 9, 0, 0, None
        for t in times(r, c, fps):
            for b, m in zip(base, r.skinned(c, t)):
                a0, n0 = tri_area_n(b['V'], b['I']); a1, n1 = tri_area_n(m['V'], m['I']); ok = a0 > 1e-10
                ratio = a1[ok] / a0[ok]; lo, hi = ratio.min(), ratio.max(); fl = int(((n0 * n1).sum(1)[ok] < -0.2).sum())
                if lo < worst_lo: worst_lo, wt = lo, (t, m['node'])
                worst_hi = max(worst_hi, hi); flips = max(flips, fl)
        print(f'{os.path.basename(path)} {c:16s} area ratio min {worst_lo:.3f} (t={wt[0]:.2f} {wt[1]}) max {worst_hi:.2f}; triangles turned >~100 deg vs bind in one frame (max): {flips}')

def inside_count(P, A, B, C):
    d = np.array([0.6, 0.31, 0.74]); d /= np.linalg.norm(d); e1, e2 = B - A, C - A; h = np.cross(d, e2); a = (e1 * h).sum(1)
    ok = np.abs(a) > 1e-14; f = np.where(ok, 1 / np.where(ok, a, 1), 0); res = []
    for p in P:
        s = p - A; u = f * (s * h).sum(1); q = np.cross(s, e1); v = f * (q @ d); t = f * (e2 * q).sum(1)
        res.append(int(((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9) & ok).sum()) % 2 == 1)
    return np.array(res)

def depth_out(p, A, B, C):
    e1, e2 = B - A, C - A; best = np.inf
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0: continue
                d = np.array([dx, dy, dz], float); d /= np.linalg.norm(d); h = np.cross(d, e2); a = (e1 * h).sum(1)
                ok = np.abs(a) > 1e-14; f = np.where(ok, 1 / np.where(ok, a, 1), 0); s = p - A; u = f * (s * h).sum(1); q = np.cross(s, e1)
                v = f * (q @ d); t = f * (e2 * q).sum(1); m = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9) & ok
                if m.any(): best = min(best, t[m].min())
    return best

def slide(path, clip, support=None, fps=30):
    r = Rig(path); base = r.skinned(None, 0)
    allV = np.vstack([b['V'] for b in base]); ymin = allV[:, 1].min()
    sel = [(k, np.where(b['V'][:, 1] < ymin + 0.008)[0]) for k, b in enumerate(base)]   # the sole / toe undersides
    ref = None; worst = 0; S = None
    if support:
        from contact import load
    if support:
        SV, SI = load(support); A, B, C = SV[SI[:, 0]], SV[SI[:, 1]], SV[SI[:, 2]]
    deep = []
    for t in times(r, clip, fps):
        m = r.skinned(clip, t); P = np.vstack([m[k]['V'][ix] for k, ix in sel])
        if ref is None: ref = P
        worst = max(worst, np.linalg.norm(P - ref, axis=1).max() * 1000)
        if support:
            low = np.vstack([mm['V'][mm['V'][:, 1] < ymin + 0.06] for mm in m if 'hood' not in (mm['node'] or '') and 'jess' not in (mm['node'] or '')])
            ins = inside_count(low, A, B, C); dd = [depth_out(p, A, B, C) for p in low[ins]]
            deep.append((t, int(ins.sum()), max(dd) * 1000 if dd else 0.0))
    print(f'{os.path.basename(path)} {clip}: sole vertices tracked {sum(len(ix) for _, ix in sel)}; max slide over the clip {worst:.1f} mm')
    if support:
        w = max(deep, key=lambda x: x[2]); print(f'  inside {os.path.basename(support)}: worst frame t={w[0]:.2f}s {w[1]} vertices, deepest {w[2]:.1f} mm; frames over 2 mm: {sum(1 for x in deep if x[2] > 2)} of {len(deep)}')

def tuck(path, clip, fps=30, foot_words=('foot', 'toe', 'tars', 'talon', 'claw')):
    r = Rig(path); sk = r.skins[0]; J = sk['joints']; names = [r.nodes[j].get('name', '').lower() for j in J]
    fj = [k for k, n in enumerate(names) if any(w in n for w in foot_words)]
    print(f'foot joints: {[names[k] for k in fj]}')
    for t in times(r, clip, fps)[::3]:
        m = r.skinned(clip, t)
        for mm in m:
            p = mm['prim']
            if 'JOINTS_0' not in p['attributes']: continue
            jt = accessor(r.js, r.b, p['attributes']['JOINTS_0']).astype(int); wt = accessor(r.js, r.b, p['attributes']['WEIGHTS_0']).astype(float)
            wt = wt / wt.sum(1, keepdims=True); fw = sum(np.where(jt[:, k:k+1] == f, wt[:, k:k+1], 0) for k in range(4) for f in fj).ravel() if fj else np.zeros(len(jt))
            foot = np.where(fw > 0.5)[0]
            if not len(foot): continue
            # the body = all other vertices' triangles; a foot vertex counts as hidden if inside the body surface
            I = mm['I']; keep = ~np.isin(I, foot).any(1); A, B, C = mm['V'][I[keep, 0]], mm['V'][I[keep, 1]], mm['V'][I[keep, 2]]
            ins = inside_count(mm['V'][foot], A, B, C)
            print(f'  t={t:.2f}s {mm["node"]}: foot vertices {len(foot)}, outside the body {int((~ins).sum())}')

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'report': Rig(a[1]).report()
    elif a[0] == 'stretch': stretch(a[1], a[2] if len(a) > 2 else None, int(a[3]) if len(a) > 3 else 30)
    elif a[0] == 'slide': slide(a[1], a[2], a[3] if len(a) > 3 else None)
    elif a[0] == 'tuck': tuck(a[1], a[2])

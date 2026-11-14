#!/usr/bin/env python3
"""T17 reviewer: skinned GLB analysis without Blender (numpy). Skin, weights, clips, loop continuity, CPU skinning.
usage: anim.py file.glb [--clip NAME --t SECONDS --dump out.npy]
As a module: load(path) -> Rig; rig.pose(clip, t) -> dict node->world 4x4; rig.skinned(clip, t) -> list of (prim, V)."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb, accessor, local

def qmat(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def slerp(a, b, u):
    d = np.dot(a, b)
    if d < 0: b, d = -b, -d
    if d > 0.9995: r = a + u * (b - a); return r / np.linalg.norm(r)
    th = np.arccos(d); return (np.sin((1 - u) * th) * a + np.sin(u * th) * b) / np.sin(th)

class Rig:
    def __init__(self, path):
        self.path = path; js, b = read_glb(path); self.js, self.b = js, b; self.nodes = js['nodes']
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get('children', []): self.parent[c] = i
        self.roots = js['scenes'][js.get('scene', 0)]['nodes']
        self.clips = {}
        for a in js.get('animations', []):
            ch = []
            for c in a['channels']:
                s = a['samplers'][c['sampler']]; T = accessor(js, b, s['input']).ravel().astype(float); V = accessor(js, b, s['output']).astype(float)
                ch.append(dict(node=c['target']['node'], path=c['target']['path'], T=T, V=V, interp=s.get('interpolation', 'LINEAR'),
                               bytes=js['accessors'][s['input']]['count'] * 4 + V.size * 4))
            self.clips[a.get('name', f'#{len(self.clips)}')] = ch
        self.skins = js.get('skins', [])
    def trs_at(self, clip, t):
        o = {}
        for c in self.clips.get(clip, []):
            T, V = c['T'], c['V']
            if c['interp'] == 'CUBICSPLINE': V = V.reshape(len(T), 3, -1)[:, 1]
            elif c['path'] == 'weights': V = V.reshape(len(T), -1)
            if t <= T[0]: v = V[0]
            elif t >= T[-1]: v = V[-1]
            else:
                k = np.searchsorted(T, t) - 1; u = (t - T[k]) / (T[k + 1] - T[k])
                if c['interp'] == 'STEP': v = V[k]
                elif c['path'] == 'rotation': v = slerp(V[k], V[k + 1], u)
                else: v = V[k] + u * (V[k + 1] - V[k])
            o.setdefault(c['node'], {})[c['path']] = np.array(v, float)
        return o
    def pose(self, clip=None, t=0.0):
        ov = self.trs_at(clip, t) if clip else {}; W = {}
        def lm(i):
            n = self.nodes[i]
            if i not in ov: return local(n)
            tr = ov[i].get('translation', n.get('translation', [0, 0, 0])); r = ov[i].get('rotation', n.get('rotation', [0, 0, 0, 1])); s = ov[i].get('scale', n.get('scale', [1, 1, 1]))
            M = np.eye(4); M[:3, :3] = qmat(np.array(r, float)) * np.array(s, float); M[:3, 3] = tr; return M
        def walk(i, M):
            W[i] = M @ lm(i)
            for c in self.nodes[i].get('children', []): walk(c, W[i])
        for r in self.roots: walk(r, np.eye(4))
        return W
    def morph(self, clip, t, i):
        ov = self.trs_at(clip, t) if clip else {}
        if i in ov and 'weights' in ov[i]: return np.array(ov[i]['weights'], float).ravel()
        m = self.js['meshes'][self.nodes[i]['mesh']]; return np.array(m.get('weights', []), float)
    def skinned(self, clip=None, t=0.0):
        W = self.pose(clip, t); out = []
        for i, n in enumerate(self.nodes):
            if 'mesh' not in n or i not in W: continue
            for p in self.js['meshes'][n['mesh']]['primitives']:
                P = accessor(self.js, self.b, p['attributes']['POSITION']).astype(float)
                I = accessor(self.js, self.b, p['indices']).ravel().reshape(-1, 3)
                mw = self.morph(clip, t, i) if p.get('targets') else []
                for k, tg in enumerate(p.get('targets', [])):
                    if k < len(mw) and mw[k] and 'POSITION' in tg: P = P + mw[k] * accessor(self.js, self.b, tg['POSITION']).astype(float)
                if 'skin' in n and 'JOINTS_0' in p['attributes']:
                    sk = self.skins[n['skin']]; J = sk['joints']
                    IBM = accessor(self.js, self.b, sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
                    JM = np.array([W[j] @ IBM[k] for k, j in enumerate(J)])
                    jt = accessor(self.js, self.b, p['attributes']['JOINTS_0']).astype(int); wt = accessor(self.js, self.b, p['attributes']['WEIGHTS_0']).astype(float)
                    if self.js['accessors'][p['attributes']['WEIGHTS_0']].get('normalized'):
                        wt = wt / {5121: 255.0, 5123: 65535.0}.get(self.js['accessors'][p['attributes']['WEIGHTS_0']]['componentType'], 1.0)
                    Ph = np.c_[P, np.ones(len(P))]; V = np.zeros((len(P), 3))
                    for k in range(4): V += wt[:, k:k+1] * np.einsum('nij,nj->ni', JM[jt[:, k]], Ph)[:, :3]
                else:
                    V = (W[i][:3, :3] @ P.T).T + W[i][:3, 3]
                out.append(dict(node=n.get('name'), V=V, I=I, prim=p, morph=list(mw)))
        return out
    def report(self):
        js = self.js; print(f'=== {os.path.basename(self.path)}  {os.path.getsize(self.path)/1024:.0f} KiB')
        for s in self.skins:
            print(f'skin: {len(s["joints"])} joints: {[self.nodes[j].get("name") for j in s["joints"]]}')
        for i, n in enumerate(self.nodes):
            if 'mesh' not in n: continue
            for p in js['meshes'][n['mesh']]['primitives']:
                if 'WEIGHTS_0' not in p['attributes']: print(f'  {n.get("name")}: not skinned'); continue
                wt = accessor(js, self.b, p['attributes']['WEIGHTS_0']).astype(float)
                if js['accessors'][p['attributes']['WEIGHTS_0']].get('normalized'): wt /= wt.max()
                nz = (wt > 1e-4).sum(1); ssum = wt.sum(1)
                print(f'  {n.get("name")}: verts {len(wt)} influences/vertex max {nz.max()} mean {nz.mean():.2f}; weight sum {ssum.min():.4f}..{ssum.max():.4f}; extra sets {"JOINTS_1" in p["attributes"]}')
        for name, ch in self.clips.items():
            dur = max(c['T'][-1] for c in ch); keys = max(len(c['T']) for c in ch); size = sum(c['bytes'] for c in ch)
            worst_r, worst_t, wr_n, wt_n = 0, 0, '', ''
            for c in ch:
                a, z = c['V'][0], c['V'][-1]
                if c['interp'] == 'CUBICSPLINE': a, z = c['V'].reshape(len(c['T']), 3, -1)[0, 1], c['V'].reshape(len(c['T']), 3, -1)[-1, 1]
                if c['path'] == 'rotation':
                    d = 2 * np.degrees(np.arccos(min(1, abs(np.dot(a / np.linalg.norm(a), z / np.linalg.norm(z))))))
                    if d > worst_r: worst_r, wr_n = d, self.nodes[c['node']].get('name')
                elif c['path'] == 'translation':
                    d = np.linalg.norm(a - z) * 1000
                    if d > worst_t: worst_t, wt_n = d, self.nodes[c['node']].get('name')
            print(f'  clip {name:16s} {dur:6.3f} s  {keys:4d} keys  {len(ch):3d} channels  {size/1024:6.1f} KiB  first-vs-last: rot {worst_r:6.2f} deg ({wr_n}), move {worst_t:6.1f} mm ({wt_n})')

if __name__ == '__main__':
    r = Rig(sys.argv[1]); r.report()

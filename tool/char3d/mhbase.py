"""MakeHuman (CC0) base body with macro targets applied, as numpy arrays. Units: metres, z up, the face toward -y."""
import numpy as np, json, os
MH = os.environ.get('MAKEHUMAN_DATA', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'makehuman/data'))

def load_obj():
    V, VT, F, FT, G = [], [], [], [], []
    g = None
    for ln in open(f'{MH}/3dobjs/base.obj'):
        if ln.startswith('v '): V.append([float(t) for t in ln.split()[1:4]])
        elif ln.startswith('vt '): VT.append([float(t) for t in ln.split()[1:3]])
        elif ln.startswith('g '): g = ln.split()[1]
        elif ln.startswith('f '):
            idx = [p.split('/') for p in ln.split()[1:]]
            F.append([int(a[0]) - 1 for a in idx]); FT.append([int(a[1]) - 1 for a in idx]); G.append(g)
    return np.array(V), np.array(VT), F, FT, G

def target(name):
    d = {}
    for ln in open(f'{MH}/targets/{name}'):
        if ln[:1] in '#\n': continue
        t = ln.split(); d[int(t[0])] = (float(t[1]), float(t[2]), float(t[3]))
    return d

def apply(V, mix):
    V = V.copy()
    for name, w in mix:
        if w == 0: continue
        for i, dv in target(name).items(): V[i] += w * np.array(dv)
    return V

# a man of about 30, average build with a little more muscle; mostly the "caucasian" shape set, which covers Arabian faces in MakeHuman
MIX = [
    ('macrodetails/universal-male-young-averagemuscle-averageweight.target', 0.75),
    ('macrodetails/universal-male-young-maxmuscle-averageweight.target', 0.25),
    ('macrodetails/caucasian-male-young.target', 0.8),
    ('macrodetails/african-male-young.target', 0.1),
    ('macrodetails/asian-male-young.target', 0.1),
    ('macrodetails/proportions/male-young-averagemuscle-averageweight-idealproportions.target', 0.5),
]

def to_blender(V):
    # MakeHuman: decimetres, y up, the face toward +z  ->  metres, z up, the face toward -y; feet on z = 0
    P = np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1) * 0.1
    return P

def body(groups=('body',)):
    """All vertices (moved so the soles touch z = 0), the UVs, and the faces of the chosen groups."""
    V, VT, F, FT, G = load_obj()
    V = apply(V, MIX)
    P = to_blender(V)
    keep = [i for i, g in enumerate(G) if g in groups]
    body_faces = [i for i, g in enumerate(G) if g == 'body']
    P[:, 2] -= P[[v for i in body_faces for v in F[i]], 2].min()
    return P, VT, [F[i] for i in keep], [FT[i] for i in keep], [G[i] for i in keep]

def joints(P):
    sk = json.load(open(f'{MH}/rigs/default.mhskel'))
    return {k: P[v].mean(0) for k, v in sk['joints'].items()}, sk

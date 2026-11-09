"""A small game rig from the MakeHuman skeleton: 27 bones, with the MakeHuman weights merged into them."""
import json, numpy as np, re
from mhbase import MH

def target_bone(b):
    if b in ('root', 'pelvis.L', 'pelvis.R', 'spine05'): return 'hips'
    if b in ('spine04', 'spine03'): return 'spine'
    if b == 'spine02' or b.startswith('breast'): return 'chest'
    if b == 'spine01': return 'upperchest'
    if b.startswith('neck'): return 'neck'
    s = '.L' if b.endswith('.L') else '.R' if b.endswith('.R') else ''
    if b.startswith(('clavicle', 'shoulder01')): return 'clavicle' + s
    if b.startswith('upperarm'): return 'upperarm' + s
    if b.startswith('lowerarm'): return 'forearm' + s
    if b.startswith(('wrist', 'metacarpal', 'finger')): return 'hand' + s
    if b.startswith('upperleg'): return 'thigh' + s
    if b.startswith('lowerleg'): return 'shin' + s
    if b.startswith('foot'): return 'foot' + s
    if b.startswith('toe'): return 'toes' + s
    return 'head'   # head, jaw, eyes, tongue and the face muscles

def build(J, sk):
    bj = lambda b, e: J[sk['bones'][b][e]]
    B = {}
    def add(n, h, t, parent): B[n] = dict(head=np.array(h, float), tail=np.array(t, float), parent=parent)
    add('hips', bj('spine05', 'head'), bj('spine05', 'tail'), None)
    add('spine', bj('spine04', 'head'), bj('spine03', 'tail'), 'hips')
    add('chest', bj('spine02', 'head'), bj('spine02', 'tail'), 'spine')
    add('upperchest', bj('spine01', 'head'), bj('spine01', 'tail'), 'chest')
    add('neck', bj('neck01', 'head'), bj('neck03', 'tail'), 'upperchest')
    add('head', bj('head', 'head'), bj('head', 'tail'), 'neck')
    for s in ('.L', '.R'):
        add('clavicle' + s, bj('clavicle' + s, 'head'), bj('shoulder01' + s, 'tail'), 'upperchest')
        add('upperarm' + s, bj('upperarm01' + s, 'head'), bj('upperarm02' + s, 'tail'), 'clavicle' + s)
        add('forearm' + s, bj('lowerarm01' + s, 'head'), bj('lowerarm02' + s, 'tail'), 'upperarm' + s)
        add('hand' + s, bj('wrist' + s, 'head'), bj('finger3-1' + s, 'head'), 'forearm' + s)
        add('thigh' + s, bj('upperleg01' + s, 'head'), bj('upperleg02' + s, 'tail'), 'hips')
        add('shin' + s, bj('lowerleg01' + s, 'head'), bj('lowerleg02' + s, 'tail'), 'thigh' + s)
        add('foot' + s, bj('foot' + s, 'head'), bj('toe3-1' + s, 'head'), 'shin' + s)
        add('toes' + s, bj('toe3-1' + s, 'head'), bj('toe3-3' + s, 'tail'), 'foot' + s)
    return B

def weights(nverts):
    """Per vertex: {new bone: weight}, normalised."""
    w = json.load(open(f'{MH}/rigs/default_weights.mhw'))['weights']
    W = [dict() for _ in range(nverts)]
    for b, lst in w.items():
        nb = target_bone(b)
        for v, x in lst:
            if v < nverts: W[v][nb] = W[v].get(nb, 0) + x
    for d in W:
        s = sum(d.values())
        if s > 0:
            for k in d: d[k] /= s
    return W

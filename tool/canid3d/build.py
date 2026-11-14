"""Builds the wolf, the guard dog and the stray dog, writes the GLB files and the pictures.

    python build.py OUT                       # every GLB into OUT, with triangles, sizes and the model's measures
    python build.py OUT wolf                  # one animal (wolf, dog, stray)
    python build.py OUT wolf quick            # and quick pictures (few samples, small)
    python build.py OUT wolf,dog,stray render # and the full picture set (JPEG)
    python build.py OUT scale render          # all of them beside the player's figure and a calf a few days old
    python build.py OUT night render          # the wolf at night at the distance the game shows it
    python build.py OUT winter render         # the wolf's winter coat beside the summer one (a question for the owner)

Blender is the `bpy` module (the project's blendenv). Nothing is downloaded: every shape and colour is made here.
CANID_POSES=alert,stalk limits the poses built; CANID_SHOTS=side,head limits the pictures.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import common  # noqa: E402
from common import V3  # noqa: E402
import canid  # noqa: E402
import paint  # noqa: E402
import species  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'out')
WHAT = sys.argv[2] if len(sys.argv) > 2 else 'all'
MODE = sys.argv[3] if len(sys.argv) > 3 else ''
QUICK = MODE == 'quick'
RENDER = MODE in ('quick', 'render')
POSES = os.environ.get('CANID_POSES')
SHOTS = os.environ.get('CANID_SHOTS')
os.makedirs(OUT, exist_ok=True)
ROOT = os.path.join(HERE, '..', '..')
MAN = os.path.join(ROOT, 'assets_src', 'characters', 'man.glb')
CAMEL = os.path.join(ROOT, 'assets_src', 'camels', 'camel_wodh_female.glb')
MASS = {'wolf': '18-20 kg', 'dog': '18-25 kg', 'stray': '18-25 kg (the same body)'}


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def want(shot):
    return not SHOTS or shot in SHOTS.split(',')


def model(kind, pose, level):
    spec, poses = species.SPECIES[kind]
    m = canid.Canid(spec, poses[pose], canid.Detail(level))
    m.build()
    return m


def build(kind, pose, level, coat_kind=None, spec=None):
    """One file: the posed animal, its atlas painted on the standing animal of the same detail level."""
    fresh()
    sp, poses = species.SPECIES[kind]
    spec = spec or sp
    rest = canid.Canid(spec, poses['alert'] if 'alert' in poses else species.DOG_POSES['alert'], canid.Detail(level))
    rest.build()
    m = canid.Canid(spec, poses[pose], canid.Detail(level))
    m.build()
    atl = paint.atlas()
    size = 512 if level == 0 else 256
    col, orm = paint.paint(coat_kind or kind, atl, size, rest)
    if level == 0 and os.environ.get('CANID_ATLAS'):
        from PIL import Image
        Image.fromarray((col[::-1] * 255).astype('uint8')).save(os.path.join(OUT, f'atlas_{kind}.png'))
    mat = common.material(kind if level == 0 else kind + '_far', col, orm)
    rname = f'{kind}_{pose}' + ('' if level == 0 else '_lod1')
    root = common.empty(rname)
    pieces = [pc for k in sorted(m.parts) for pc in m.parts[k]]
    me = common.to_mesh(rname + '_mesh', pieces, atl)
    o = common.obj(rname + '_mesh', me, mat, root)
    if level == 0:
        add_points(root, m.points)
    path = os.path.join(OUT, rname + '.glb')
    common.export(path, root)
    t, imgs, nbytes = common.glb_report(path)
    print(f'{rname}.glb: {sum(t.values())} triangles in {len(t)} mesh(es); textures {", ".join(f"{w}x{h}" for _, w, h in imgs)}; {nbytes / 1024:.0f} KB')
    if level == 0:
        for line in measures(m, o):
            print('   ' + line)
    return root, o, m


POINT_NAMES = {
    'foot_fl': 'foot_fl', 'foot_fr': 'foot_fr', 'foot_hl': 'foot_hl', 'foot_hr': 'foot_hr',
}


def add_points(root, pts):
    for name in sorted(pts):
        v = pts[name]
        if isinstance(v, tuple):
            co, fwd, up = v
            common.point(name, co, root, fwd, up)
        else:
            common.point(name, v, root)


def verts(o):
    a = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3) * 1000


def piece_bounds(pc):
    a = np.array([tuple(q) for q in pc.V])
    return a.min(0), a.max(0)


def measures(m, o):
    """The model's figures to set beside the real ones, measured on its pieces (mm)."""
    H = m.H
    out = []
    body = m.parts['body'][0]
    bv = np.array([tuple(q) for q in body.V])
    allv = verts(o)
    wx = m.points['withers'].x
    near = bv[np.abs(bv[:, 0] - wx) < 40]
    out.append(f'withers height {near[:, 2].max():.0f} mm (spec {H:.0f}); top of the head {allv[:, 2].max():.0f} mm')
    nose = m.points['nose']
    tb = m.points['tail_base'][0]
    out.append(f'nose to tail base {nose.x - tb.x:.0f} mm (in x); length overall {allv[:, 0].max() - allv[:, 0].min():.0f} mm; '
               f'body (chest front to buttock) {bv[:, 0].max() - bv[:, 0].min():.0f} mm; widest {2 * bv[:, 1].max():.0f} mm')
    tail = m.parts['body'][-1]
    tvv = np.array([tuple(q) for q in tail.V])
    out.append(f'tail tip lowest at {tvv[:, 2].min():.0f} mm above the ground; hocks at {m.points["hock_l"].z:.0f} mm; '
               f'elbows at {m.points["elbow_l"].z:.0f} mm; chest bottom at {bv[:, 2].min():.0f} mm')
    o_, hd, hn, hv, Lh = m.head_frame
    out.append(f'head (occiput to nose) {Lh:.0f} mm; ears {m.S["ear"][0] * H:.0f} mm tall, {m.S["ear"][1] * H:.0f} mm at the base')
    feet = [k for k in m.points if k.startswith('foot_')]
    lows = []
    for pc in m.parts['legs']:
        if pc.block.endswith('paw'):
            lo, hi = piece_bounds(pc)
            lows.append(lo[2])
    out.append('paws lowest point ' + ', '.join(f'{z:.0f}' for z in lows) + ' mm; legs reach ' +
               ', '.join(f'{k} {v:.2f}' for k, v in sorted(m.reach.items())))
    return out


def volume_litres(o, step=6.0):
    """The model's volume (litres) counted on a grid of vertical rays through the closed pieces, overlaps counted
    once."""
    from mathutils.bvhtree import BVHTree
    import bmesh
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bvh = BVHTree.FromBMesh(bm)
    v = verts(o)
    lo, hi = v.min(0), v.max(0)
    xs = np.arange(lo[0] + step / 2, hi[0], step)
    ys = np.arange(lo[1] + step / 2, hi[1], step)
    total = 0.0
    zs = np.arange(lo[2] + step / 2, hi[2], step)
    # count grid points inside by parity of crossings along +z for each column, with every piece's own crossings
    for x in xs:
        for y in ys:
            hits = []
            p = V3((x / 1000, y / 1000, lo[2] / 1000 - 0.01))
            while True:
                loc, nrm, idx, d = bvh.ray_cast(p, V3((0, 0, 1)))
                if loc is None:
                    break
                hits.append((loc.z * 1000, 1 if nrm.z < 0 else -1))
                p = loc + V3((0, 0, 1e-5))
            if not hits:
                continue
            depth = 0
            inside = 0.0
            start = None
            for z, s in hits:
                depth += s
                if depth > 0 and start is None:
                    start = z
                elif depth <= 0 and start is not None:
                    inside += z - start
                    start = None
            total += inside * step * step
    bm.free()
    return total / 1e6


# ------------------------------------------------------------------ pictures
def bounds(o):
    v = verts(o)
    return v.min(0), v.max(0)


def finish(png, ruler=None):
    if png is None:
        return
    if ruler:
        common.ruler(png, *ruler)
    jpg = png[:-4] + '.jpg'
    common.to_jpeg(png, jpg)
    print('picture', jpg)


def pictures(kind, pose, o, m):
    st = common.Studio(OUT, samples=10 if QUICK else 32)
    lo, hi = bounds(o)
    mid = (lo + hi) / 2000
    ext = (hi - lo) / 1000
    res = (720, 540) if QUICK else (1200, 900)
    st.rig_lights(V3(mid), dist=max(ext[0] * 2.0, 1.2))
    tag = f'{kind}_{pose}'
    ortho = max(ext[0], ext[2] * 1.33) * 1.25
    if want('side'):
        png = st.shot(tag + '_side', (mid[0], 5, mid[2]), mid, ortho=ortho, res=res)
        pxmm = res[0] / (ortho * 1000)
        x0 = res[0] / 2 - (mid[0] * 1000 - lo[0]) * pxmm
        # the ruler under the animal, along the ground (its zero under the rearmost point)
        yg = res[1] / 2 + mid[2] * 1000 * pxmm
        finish(png, (pxmm, x0, min(yg + 36, res[1] - 30), round((hi[0] - lo[0]) / 100) * 100 + 100))
    if want('three'):
        span = max(ext) * 1.2
        png = st.shot(tag + '_three_quarter', V3(mid) + V3((0.85, 0.80, 0.42)) * span * 2.3, mid, lens=60, res=res)
        finish(png)
    if want('head') and pose in ('alert', 'bark'):
        hd = V3(m.points['head'][0]) * 0.001
        fwd = V3(m.points['head'][1])
        cam = hd + (fwd * 0.55 + V3((0, 1, 0)) * 0.75 + V3((0, 0, 0.15))).normalized() * 0.55
        png = st.shot(tag + '_head', cam, hd, lens=70, res=res)
        finish(png)
    if want('front') and pose == 'alert':
        png = st.shot(tag + '_front', (mid[0] + 5, mid[1], mid[2]), mid, ortho=max(ext[1], ext[2]) * 1.5, res=(res[1], res[1]))
        finish(png)


def run_animal(kind):
    spec, poses = species.SPECIES[kind]
    for pose in poses:
        if POSES and pose not in POSES.split(','):
            continue
        build(kind, pose, 1)
        root, o, m = build(kind, pose, 0)
        if pose == 'alert' and os.environ.get('CANID_VOLUME'):
            print(f'   volume {volume_litres(o):.1f} L (at a body density near 1 kg/L, against a real mass of {MASS[kind]})')
        if RENDER:
            pictures(kind, pose, o, m)


if __name__ == '__main__':
    todo = ['wolf', 'dog', 'stray'] if WHAT == 'all' else WHAT.split(',')
    for w in todo:
        if w in species.SPECIES:
            run_animal(w)
        else:
            import scene
            getattr(scene, w)(sys.modules[__name__])

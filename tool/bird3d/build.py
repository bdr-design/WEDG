"""Builds the birds of the hunt and their gear, writes the GLB files and the pictures.

    python build.py OUT                  # every GLB into OUT, prints triangles, sizes and measures
    python build.py OUT saker            # one species (saker, houbara, curlew, gear)
    python build.py OUT saker quick      # and quick pictures (few samples, small)
    python build.py OUT all render       # and the full picture set (JPEG)

Blender is the `bpy` module (the project's blendenv). Nothing is downloaded: every shape and colour is made here.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import common  # noqa: E402
from common import V3  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'out')
WHAT = sys.argv[2] if len(sys.argv) > 2 else 'all'
MODE = sys.argv[3] if len(sys.argv) > 3 else ''
QUICK = MODE == 'quick'
RENDER = MODE in ('quick', 'render')
SHOTS = os.environ.get('BIRD_SHOTS')      # e.g. BIRD_SHOTS=side,head: only those pictures
os.makedirs(OUT, exist_ok=True)
MAN = os.path.join(HERE, '..', '..', 'assets_src', 'characters', 'man.glb')


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_root(name):
    root = common.empty(name)
    return root


def add_parts(root, prefix, parts, atlas, mat):
    objs = {}
    for k, pcs in parts.items():
        if not pcs:
            continue
        me = common.to_mesh(prefix + '_' + k, pcs, atlas)
        objs[k] = common.obj(prefix + '_' + k, me, mat, root)
    return objs


def add_points(root, pts):
    for name in sorted(pts):
        v = pts[name]
        if isinstance(v, tuple):
            co, fwd, up = v
            common.point(name, co, root, fwd, up)
        else:
            common.point(name, v, root)


def bounds(objs, names=None):
    co = []
    for k, o in objs.items():
        if names and k not in names:
            continue
        a = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get('co', a)
        co.append(a.reshape(-1, 3))
    co = np.concatenate(co) * 1000
    return co.min(0), co.max(0)


def want(shot):
    return not SHOTS or shot in SHOTS.split(',')


def shot_jpg(st, name, *a, **k):
    if not want(name.rsplit('_', 1)[1] if name.count('_') >= 2 and not name.endswith('three_quarter') else
                ('three_quarter' if name.endswith('three_quarter') else name)):
        return None
    png = st.shot(name, *a, **k)
    return png


def finish(png, ruler=None):
    if png is None:
        return
    if ruler:
        common.ruler(png, *ruler)
    jpg = png[:-4] + '.jpg'
    common.to_jpeg(png, jpg)
    print('picture', jpg)


# ------------------------------------------------------------------ the species
def species(name):
    if name == 'saker':
        import saker as m
    elif name == 'peregrine':
        import peregrine as m
    elif name == 'pigeon':
        import pigeon
        m = pigeon.PIGEON
    elif name in ('houbara', 'curlew'):
        import quarry
        m = quarry.HOUBARA if name == 'houbara' else quarry.CURLEW
    else:
        raise SystemExit('unknown ' + name)
    return m


def build_bird(name, pose, level, pictures=False):
    import paint
    m = species(name)
    fresh()
    parts, pts, body = m.build(pose, level)
    atlas = paint.atlas(name)
    size = 512 if level == 0 else 256
    col, orm = paint.paint(name, atlas, size, body)
    mat = common.material(name if level == 0 else name + '_far', col, orm)
    if level == 0 and os.environ.get('BIRD_ATLAS'):
        from PIL import Image
        Image.fromarray((col[::-1] * 255).astype('uint8')).save(os.path.join(OUT, f'atlas_{name}_{pose}.png'))
    rname = f'{name}_{pose}' + ('' if level == 0 else '_lod1')
    root = make_root(rname)
    objs = add_parts(root, name, parts, atlas, mat)
    if level == 0:
        add_points(root, pts)
    path = os.path.join(OUT, rname + '.glb')
    common.export(path, root)
    t, imgs, nbytes = common.glb_report(path)
    lo, hi = bounds(objs)
    blo, bhi = bounds(objs, ['body'])
    print(f'{rname}.glb: ' + ', '.join(f'{k} {v}' for k, v in sorted(t.items())) + f'; total {sum(t.values())} triangles; '
          f'textures {", ".join(f"{w}x{h}" for _, w, h in imgs)}; {nbytes / 1024:.0f} KB')
    print(f'   body bounds x {blo[0]:.0f}..{bhi[0]:.0f}  y {blo[1]:.0f}..{bhi[1]:.0f}  z {blo[2]:.0f}..{bhi[2]:.0f} mm')
    if level == 0:
        for line in measures(name, pose, objs, m.SPEC, lo, hi):
            print('   ' + line)
    return root, objs, pts, body


MASS = {'saker': (0.97, 1.30), 'peregrine': (0.925, 1.333), 'pigeon': (0.238, 0.380), 'houbara': (1.8, 2.4), 'curlew': (0.29, 0.535)}      # kg: README.md says from where


def measures(name, pose, objs, spec, lo, hi):
    """The model's figures to set beside the real ones: length, span, standing height, wing length (wrist to tip),
    tail, tarsus, wing area, and the wingbeat Pennycuick's (1996) formula predicts from them."""
    out = []
    rows = np.array(spec['open'])
    y, xl, xt = rows[:, 0], rows[:, 1], rows[:, 2]
    wrist = int(np.argmin(np.abs(y - spec['wrist_y'])))
    tip = np.array([y[-1], 0.5 * (xl[-1] + xt[-1])])
    if spec.get('fingers'):
        f = max(spec['fingers'], key=lambda r: r[2])
        tip = np.array([f[2], f[3]])
    wing_len = float(np.hypot(*(tip - np.array([y[wrist], xl[wrist]]))))
    chord = xl - xt
    area = 2 * (float(np.trapezoid(chord, y)) + chord[0] * y[0])
    if spec.get('fingers'):
        area += 2 * sum((r[2] - r[0]) * r[4] * 2 * 0.75 for r in spec['fingers'])
    span = 2 * (tip[0] if spec.get('fingers') else y[-1])
    tail = spec['tail'][-1][0] - spec.get('tail_root', 0)
    out.append(f'wing length (wrist to tip) {wing_len:.0f} mm, span {span:.0f} mm, wing area {area / 1e6:.3f} m2, '
               f'visible tail {tail:.0f} mm, tarsus {spec["leg"]["tarsus"]} mm')
    if pose in ('flight',):
        out.append(f'length bill to tail (flight) {hi[0] - lo[0]:.0f} mm, span (dihedral) {hi[1] - lo[1]:.0f} mm')
    else:
        out.append(f'standing height above the support {hi[2]:.0f} mm, length as it stands {hi[0] - lo[0]:.0f} mm')
    b, S, rho, g = span / 1000, area / 1e6, 1.2, 9.81
    fs = [m ** 0.375 * g ** 0.5 * b ** (-23 / 24) * S ** (-1 / 3) * rho ** (-0.375) for m in MASS[name]]
    out.append(f'wingbeat (Pennycuick 1996, sea level) {fs[0]:.1f} to {fs[1]:.1f} Hz for {MASS[name][0]} to {MASS[name][1]} kg; '
               f'wing loading {MASS[name][0] * g / S:.0f} to {MASS[name][1] * g / S:.0f} N/m2')
    return out


def run_saker(name='saker'):
    for pose in ('hooded', 'fist', 'alert', 'flight'):
        for level in ((1, 0) if pose != 'fist' else (0,)):
            root, objs, pts, body = build_bird(name, pose, level)
        if RENDER and pose != 'fist':
            pictures_bird(name, pose, root, objs, pts)


def pictures_bird(name, pose, root, objs, pts):
    """Side (with a centimetre ruler), three-quarter, close on the head, (in flight) from below and behind."""
    st = common.Studio(OUT, samples=10 if QUICK else 24, ground=(pose != 'flight'))
    lo, hi = bounds(objs)
    if name in ('saker', 'peregrine') and pose in ('hooded', 'alert') and os.path.exists(os.path.join(OUT, 'wakr.glb')):
        # on her perch, its top under her feet, the sand 300 mm below
        import scene
        scene.load(os.path.join(OUT, 'wakr.glb'), 'wakr')
        st.ground.location.z = -0.30
    mid = (lo + hi) / 2000
    ext = (hi - lo) / 1000
    span = max(ext[0], ext[2]) * 1.25
    res = (720, 540) if QUICK else (1200, 900)
    st.rig_lights(V3(mid), dist=max(span * 2.2, 0.9))
    tag = f'{name}_{pose}'
    if pose == 'flight':
        if st.ground:
            st.ground.hide_render = True
        side_scale = max(ext[0], ext[1]) * 1.15
    # side, orthographic, from the bird's left (+Y)
    ortho = max(ext[0], ext[2]) * 1.35 if pose != 'flight' else max(ext[0], ext[1]) * 1.2
    if pose == 'flight':
        png = shot_jpg(st, tag + '_side', (mid[0], 4, mid[2]), mid, ortho=ortho * 0.75, res=res)
        if png:
            pxmm = res[0] / (ortho * 0.75 * 1000)
            x0 = res[0] / 2 - (mid[0] * 1000 - lo[0]) * pxmm
            finish(png, (pxmm, x0, res[1] - 40, round((hi[0] - lo[0]) / 10) * 10))
        # straight from below, the head up the picture: the underwing as a falconer sees it cast off
        st.cam.rotation_mode = 'XYZ'
        png = None
        if want('below'):
            st.cam.location = V3((mid[0], mid[1], mid[2] - 4))
            st.cam.rotation_euler = (math.pi, 0, math.pi / 2)
            st.cam_d.type = 'ORTHO'
            st.cam_d.ortho_scale = ortho
            st.sc.render.resolution_x, st.sc.render.resolution_y = res
            st.sc.render.filepath = os.path.join(OUT, tag + '_below.png')
            bpy.ops.render.render(write_still=True)
            png = os.path.join(OUT, tag + '_below.png')
        finish(png)
        png = shot_jpg(st, tag + '_top', (mid[0], 0, 4), mid, ortho=ortho, res=res)
        if png:
            pxmm = res[0] / (ortho * 1000)
            finish(png, (pxmm, res[0] / 2 - (0.5 * (hi[1] - lo[1])) * pxmm, res[1] - 40, round((hi[1] - lo[1]) / 10) * 10))
    else:
        png = shot_jpg(st, tag + '_side', (mid[0], 4, mid[2]), mid, ortho=ortho, res=res)
        if png:
            pxmm = res[0] / (ortho * 1000)
            x0 = res[0] / 2 - (mid[0] * 1000 - lo[0]) * pxmm
            finish(png, (pxmm, x0, res[1] - 30, round((hi[0] - lo[0]) / 10) * 10))
    png = shot_jpg(st, tag + '_three_quarter', V3(mid) + V3((0.9, 0.75, 0.35)) * span * 2.2, mid, lens=60, res=res)
    finish(png)
    if pose == 'flight':
        return
    hd = V3(pts['head'][0]) * 0.001 if isinstance(pts['head'], tuple) else V3(pts['head']) * 0.001
    png = shot_jpg(st, tag + '_head', hd + V3((0.55, 0.85, 0.12)) * 0.28, hd, lens=60, res=res)
    finish(png)


if __name__ == '__main__':
    todo = ['saker', 'houbara', 'curlew', 'gear'] if WHAT == 'all' else WHAT.split(',')
    for w in todo:
        if w in ('saker', 'peregrine'):
            run_saker(w)
        elif w in ('houbara', 'curlew'):
            import quarry
            quarry.run(w, sys.modules[__name__])
        elif w == 'pigeon':
            import pigeon
            pigeon.run(sys.modules[__name__])
        elif w == 'gear':
            import gear
            gear.run(sys.modules[__name__])
        elif w == 'scale':
            import scene
            scene.scale(sys.modules[__name__])
        elif w == 'peregrine_scale':
            import scene
            scene.scale_peregrine(sys.modules[__name__])

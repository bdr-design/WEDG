"""Builds the wolf, the guard dog and the stray dog, writes the GLB files and the pictures.

    python build.py OUT                       # every GLB into OUT, with triangles, sizes and the model's measures
    python build.py OUT wolf                  # one animal (wolf, dog, stray)
    python build.py OUT wolf quick            # and quick pictures (few samples, small)
    python build.py OUT wolf,dog,stray render # and the full picture set (JPEG)
    python build.py OUT scale render          # all of them beside the player's figure and a calf a few days old
    python build.py OUT night render          # the wolf at night at the distance the game shows it
    python build.py OUT winter render         # the wolf's winter coat beside the summer one (a question for the owner)
    python build.py OUT far render            # the far models from the game's camera at 15 m
    python build.py OUT firstperson render    # the player's eyes on foot: the dog at 1 and 1.5 m, the stray at 2, the wolf at 3

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
import skin  # noqa: E402
import texture  # noqa: E402
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


TARGET = {0: 7000, 1: 1300}       # the skin's triangles, close and far
TEX = {0: 512, 1: 256}


def build(kind, pose):
    """Both detail levels of one pose: one skin over the posed build, decimated to each level's budget, its
    texture pair painted on the standing animal. Returns {level: (root, obj)} and the posed build."""
    fresh()
    spec, poses = species.SPECIES[kind]
    coat = species.COAT.get(kind, kind)
    rest = canid.Canid(spec, poses['alert'], canid.Detail(0))
    rest.build()
    m = canid.Canid(spec, poses[pose], canid.Detail(0))
    m.build()
    m1 = canid.Canid(spec, poses[pose], canid.Detail(1))
    m1.build()
    H = m.H
    o_, hd, hn, hv, Lh = m.head_frame
    head_c = o_ + hd * (0.45 * Lh)
    objs, hi, eyes = skin.skin_mesh(f'{kind}_{pose}', m.parts, H, H / 220.0, [TARGET[0], TARGET[1]], head=(tuple(head_c), 0.75 * Lh),
                                    face=m.face)
    eye_pcs = skin.eye_pieces(eyes)
    out = {}
    for level in (0, 1):
        o = objs[TARGET[level]]
        src = m if level == 0 else m1
        extras = [pc for k in sorted(src.parts) for pc in src.parts[k] if getattr(pc, 'group', '') in skin.SKIN_GROUPS_EXCLUDED]
        if level == 0:
            extras = extras + eye_pcs
        else:
            extras = [pc for pc in extras if pc.block == 'collar']
        n_skin = len(o.data.polygons)
        blocks, first = [], n_skin
        for pc in extras:
            blocks.append((first, pc.block))
            first += len(pc.T)
        skin.add_pieces(o, extras)
        UV = skin.unwrap(o, tuple(head_c), 0.75 * Lh)
        bad = skin.uv_overlaps(UV)
        if bad:
            V_, F_ = skin.mesh_arrays(o)
            for pa in bad[:3]:
                for f_ in pa:
                    print('   face', f_, 'xyz', V_[F_[f_]].round(1).tolist(), 'uv', UV[f_].round(4).tolist())
            raise SystemExit(f'{kind}_{pose} level {level}: {len(bad)} pairs of texture triangles overlap: {bad[:6]}')
        edge = int(((UV < 0.002) | (UV > 0.998)).any(axis=(1, 2)).sum())
        Vv, Fq = skin.mesh_arrays(o)
        a3 = 0.5 * np.linalg.norm(np.cross(Vv[Fq[:, 1]] - Vv[Fq[:, 0]], Vv[Fq[:, 2]] - Vv[Fq[:, 0]]), axis=1)
        e1, e2 = UV[:, 1] - UV[:, 0], UV[:, 2] - UV[:, 0]
        a2 = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) * TEX[level] ** 2
        fc_ = Vv[Fq].mean(1)
        nearhead = np.linalg.norm(fc_ - np.array(tuple(head_c)), axis=1) < 0.9 * Lh
        print(f'   texel size: body {np.sqrt(a3[~nearhead].sum() / a2[~nearhead].sum()):.1f} mm, head '
              f'{np.sqrt(a3[nearhead].sum() / a2[nearhead].sum()):.1f} mm ({TEX[level]} px)')
        print(f'   texture layout level {level}: no overlapping triangles (checked at 2048 px); {edge} faces touch its border')
        col, nrm, cover = texture.bake(coat, m, rest, o, UV, n_skin, blocks, TEX[level], H, eyes)
        if level == 0 and os.environ.get('CANID_ATLAS'):
            from PIL import Image
            Image.fromarray((np.clip(col[::-1], 0, 1) * 255).astype('uint8')).save(os.path.join(OUT, f'atlas_{kind}_{pose}.png'))
            Image.fromarray((np.clip(nrm[::-1], 0, 1) * 255).astype('uint8')).save(os.path.join(OUT, f'normal_{kind}_{pose}.png'))
        o.data.shade_smooth()
        mat = skin.material(coat if level == 0 else coat + '_far', col, nrm)
        o.data.materials.append(mat)
        rname = f'{kind}_{pose}' + ('' if level == 0 else '_lod1')
        root = common.empty(rname)
        o.name = rname + '_mesh'
        o.data.name = rname + '_mesh'
        o.parent = root
        add_points(root, m.points)
        path = os.path.join(OUT, rname + '.glb')
        common.export(path, root)
        t, imgs, nbytes = common.glb_report(path)
        print(f'{rname}.glb: {sum(t.values())} triangles; textures {", ".join(f"{w}x{h}" for _, w, h in imgs)}; '
              f'{nbytes / 1024:.0f} KB; {shells(o)} piece(s); the texture covers {cover * 100:.0f}% of its square')
        out[level] = (root, o)
        for ch in [c for c in root.children if c.type == 'EMPTY']:
            bpy.data.objects.remove(ch)          # (so the far file's points take the same names, not 'foot_fl.001')
    print(f'   the skin before decimation: {hi[0]} vertices, {hi[1]} triangles (voxel {H / 220.0:.2f} mm)')
    for line in measures(m, out[0][1]):
        print('   ' + line)
    return out, m


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


def shells(o):
    """The number of separate closed pieces in the mesh."""
    V, Fv = skin.mesh_arrays(o)
    parent = np.arange(len(V))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b, c in Fv:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    return len({find(i) for i in range(len(V))})


def section(V, Fv, axis, x):
    """The skin's section by the plane [axis] = x (mm): its segments as an [n, 2, 3] array (each crossed triangle
    gives one segment between its two crossed edges)."""
    d = V[:, axis] - x
    a, b, c = Fv[:, 0], Fv[:, 1], Fv[:, 2]
    cr = [d[a] * d[b] < 0, d[b] * d[c] < 0, d[c] * d[a] < 0]
    ends = [(a, b), (b, c), (c, a)]
    segs = []
    for e1, e2 in ((0, 1), (1, 2), (2, 0)):
        sel = cr[e1] & cr[e2]
        if not sel.any():
            continue
        pts = []
        for e in (e1, e2):
            u, v = ends[e][0][sel], ends[e][1][sel]
            t = d[u] / (d[u] - d[v])
            pts.append(V[u] + (V[v] - V[u]) * t[:, None])
        segs.append(np.stack(pts, 1))
    return np.concatenate(segs) if segs else np.zeros((0, 2, 3))


def measures(m, o):
    """The model's figures to set beside the real ones, measured on the skin (mm)."""
    H, S = m.H, m.S
    V, Fv = skin.mesh_arrays(o)
    out = []
    wx = m.points['withers'].x
    tv = np.array([tuple(q) for q in m.parts['body'][0].V])        # the torso piece: the withers on the trunk itself
    wh = tv[np.abs(tv[:, 0] - wx) < 25][:, 2].max()
    out.append(f'withers height {wh:.0f} mm (spec {H:.0f}); top of the head {V[:, 2].max():.0f} mm; lowest point {V[:, 2].min():.1f} mm')
    nose = m.points['nose']
    tb = m.points['tail_base'][0]
    out.append(f'nose to tail base {nose.x - tb.x:.0f} mm (in x); length overall {np.ptp(V[:, 0]):.0f} mm; widest {np.ptp(V[:, 1]):.0f} mm')
    o_, hd, hn, hv, Lh = m.head_frame
    out.append(f'head (occiput to nose) {Lh:.0f} mm; muzzle (eye to nose) {1 - S["eye"][0]:.2f} of it; '
               f'ears {S["ear"][0] * H:.0f} mm tall, their bases {2 * S["ear_base"][2] * H:.0f} mm apart (centres)')
    band = V[(V[:, 0] > wx + 0.03 * H) & (V[:, 0] < wx + 0.12 * H) & (np.abs(V[:, 1]) < 0.05 * H)]
    if len(band):
        out.append(f'the neck just ahead of the withers rises {band[:, 2].max() - wh:+.0f} mm over them')
    def width_at(q, dz):
        seg = section(V, Fv, 0, q.x)
        if not len(seg):
            return 0.0
        pts = seg.reshape(-1, 3)
        pts = pts[np.abs(pts[:, 2] - q.z) < dz]
        return float(np.ptp(pts[:, 1])) if len(pts) else -1.0
    occ = o_
    out.append(f'neck width just behind the skull {width_at(occ - hd * (0.04 * H), 0.05 * H):.0f} mm, across the cheeks '
               f'{width_at(occ + hd * (0.24 * Lh), 0.04 * H):.0f} mm; the muzzle at 0.62 and 0.76 of the head '
               f'{width_at(occ + hd * (0.62 * Lh), 0.03 * H):.0f} and {width_at(occ + hd * (0.76 * Lh), 0.025 * H):.0f} mm')
    et = S['eye'][0]
    eyes = m.points['eye_l'], m.points['eye_r']
    out.append(f'head width at the eyes {width_at(occ + hd * (et * Lh), 0.035 * H):.0f} mm, the eyes {(eyes[0] - eyes[1]).length:.0f} mm apart; '
               f'the muzzle at its base (0.56) {width_at(occ + hd * (0.56 * Lh), 0.03 * H):.0f} mm')
    # triangles per paw: faces within a paw's length of its sole point and below twice its height
    fc = V[Fv].mean(1)
    per = []
    for k in ('foot_fl', 'foot_fr', 'foot_hl', 'foot_hr'):
        sole = np.array(tuple(m.points[k][0]))
        L = (S['forepaw'] if k[5] == 'f' else S['hindpaw'])[0] * H
        sel = (np.linalg.norm((fc - sole)[:, :2], axis=1) < 0.70 * L) & (fc[:, 2] < sole[2] + 1.2 * S['forepaw'][2] * H)
        per.append(int(sel.sum()))
    a_ = (fc - np.array(tuple(occ))) @ np.array(tuple(hd)) / Lh
    rad = np.linalg.norm(np.cross(fc - np.array(tuple(occ)), np.array(tuple(hd))), axis=1)
    headsel = (a_ > -0.08) & (a_ < 1.1) & (rad < 0.20 * H)
    pawsum = sum(per)
    out.append('triangles per paw (fl, fr, hl, hr) ' + ', '.join(map(str, per)) +
               f'; paws {pawsum}, head (with the ears) {int(headsel.sum())}, body {len(Fv) - pawsum - int(headsel.sum())} of {len(Fv)}')
    lx = -0.16 * H
    seg = section(V, Fv, 0, lx)
    trunk = seg[seg[:, :, 2].min(1) > 0.3 * H] if len(seg) else seg
    girth = np.linalg.norm(trunk[:, 1] - trunk[:, 0], axis=1).sum() if len(trunk) else 0
    out.append(f'loin girth (at x = {lx:.0f} mm) {girth:.0f} mm')
    ang = getattr(m, 'angles', {})
    out.append('angles: ' + ', '.join(f'{k} {v:.0f}' for k, v in sorted(ang.items())))
    out.append('legs reach ' + ', '.join(f'{k} {v:.2f}' for k, v in sorted(m.reach.items())))
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
    st = common.Studio(OUT, samples=10 if QUICK else 14)
    lo, hi = bounds(o)
    mid = (lo + hi) / 2000
    ext = (hi - lo) / 1000
    res = (720, 540) if QUICK else (1000, 750)
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
    if want('top') and pose == 'alert':
        png = st.shot(tag + '_top', (mid[0], mid[1] + 0.001, 5), mid, ortho=max(ext[0], ext[1] * 1.33) * 1.2, res=res)
        finish(png)
    if want('head1m') and pose == 'alert':
        # the head at 1 m (front left, a little above), the distance the reviewer judges the faces at
        hd_ = V3(m.points['head'][0]) * 0.001
        cam = hd_ + V3((0.62, 0.62, 0.48)).normalized() * 1.0
        png = st.shot(tag + '_head_1m', cam, hd_, lens=50, res=res)
        finish(png)
    if want('paws') and pose == 'alert':
        # the forepaws from three-quarter front, low, with a raking light from the side
        f = V3(m.points['foot_fl'][0]) * 0.001
        tgt = f + V3((0.02, -0.05, 0.03))
        st.light('AREA', tgt + V3((0.1, 0.9, 0.08)), 30, tgt, 0.3)
        png = st.shot(tag + '_paws', tgt + V3((0.42, 0.30, 0.14)), tgt, lens=60, res=res)
        finish(png)
    if want('front') and pose == 'alert':
        png = st.shot(tag + '_front', (mid[0] + 5, mid[1], mid[2]), mid, ortho=max(ext[1], ext[2]) * 1.5, res=(res[1], res[1]))
        finish(png)


def run_animal(kind):
    spec, poses = species.SPECIES[kind]
    for pose in poses:
        if POSES and pose not in POSES.split(','):
            continue
        out, m = build(kind, pose)
        root, o = out[0]
        out[1][1].hide_render = True
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

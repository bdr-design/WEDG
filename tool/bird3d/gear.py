"""The falconer's gear as parts of their own: the block perch (الوكر) with the leash (المرسل), and the glove (الدس).
The hood (البرقع) and the jesses (السبوق) are on the falcon (saker.py). The sources are in README.md.

The perch: a broad flat round top on a wooden-clad stake driven into the sand, its top padded. Its origin is the
middle of the top, where the falcon's feet stand (the saker's perched origin); the sand is 300 mm below.
The glove (الدس): a padded, quilted cloth cuff over the left wrist and fist (not a fingered gauntlet), held with
the forearm level and the thumb up. Its origin is
the fist's top, where the falcon stands; X runs along the forearm toward the fist.
"""
import math

import numpy as np

import common
from common import V3, Atlas, C, Noise, Piece, Sec, lerp_col, loft, smooth_path, tube

GROUND = -300.0     # the sand under the perch's top (a game choice: see README.md)

BLOCKS = {
    'wood': (0.0, 0.5, 0.5, 1.0),
    'pad': (0.5, 0.5, 1.0, 1.0),
    'steel': (0.0, 0.25, 0.25, 0.5),
    'leash': (0.25, 0.25, 0.5, 0.5),
    'leather': (0.5, 0.0, 1.0, 0.5),
    'cuff': (0.0, 0.0, 0.5, 0.25),
}


def soft(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def painters():
    n = Noise(51)

    def wood(S, T):
        # turned wood, a dark stain, its grain along the stake, two pale turned rings
        X, Y = S * 340.0, T * 140.0
        g = n(X * 0.1 + 3, Y * 2.0 + 3, 1.0)
        col = C(0.30, 0.18, 0.10)[None, None, :] * (0.9 + 0.12 * g[..., None])
        rings = ((np.abs(X - 120) < 4) | (np.abs(X - 200) < 4))
        col = lerp_col(col, C(0.62, 0.48, 0.30), rings * 0.8)
        return col, 0.5 + 0.08 * g, np.ones_like(S)

    def pad(S, T):
        # the top's pad: green artificial turf, short dense blades
        X, Y = S * 160.0, T * 470.0
        g = n(X * 3 + 1, Y * 3 + 1, 1.0) + 0.5 * n(X + 1, Y + 1, 4.0)
        col = C(0.16, 0.34, 0.12)[None, None, :] * (0.8 + 0.3 * g[..., None])
        return col, 0.9 * np.ones_like(S), np.ones_like(S)

    def steel(S, T):
        return np.broadcast_to(C(0.45, 0.46, 0.48), S.shape + (3,)).copy(), 0.4 * np.ones_like(S), np.ones_like(S)

    def leash(S, T):
        ph = (S * 400 + T * 4) % 1.0
        col = lerp_col(np.broadcast_to(C(0.34, 0.22, 0.12), S.shape + (3,)), C(0.42, 0.29, 0.16), (ph > 0.5).astype(np.float32))
        return col, 0.75 * np.ones_like(S), np.ones_like(S)

    def leather(S, T):
        # the dass: thick padded cloth, quilted in diamonds, darker and worn where the falcon stands
        X, Y = S * 220.0, T * 300.0
        g = n(X + 7, Y + 7, 3.0) + 0.4 * n(X + 7, Y + 7, 0.7)
        col = C(0.30, 0.31, 0.22)[None, None, :] * (1 + 0.06 * g[..., None])
        q = np.minimum(np.abs(((X + Y) / 22.0) % 1.0 - 0.5), np.abs(((X - Y) / 22.0) % 1.0 - 0.5))
        quilt = 1 - soft(q, 0.0, 0.06)
        puff = soft(q, 0.0, 0.25)
        col = col * (0.82 + 0.18 * puff)[..., None]
        col = lerp_col(col, C(0.62, 0.58, 0.44), quilt * 0.55)
        tt = np.minimum(T, 1 - T)
        top = 1 - soft(tt, 0.0, 0.12)
        col = col * (1 - 0.18 * top * soft(S, 0.6, 0.8))[..., None]
        return col, 0.85 + 0.05 * g, 0.85 + 0.15 * puff

    def cuff(S, T):
        # the cuff's bound edge: dark leather with a stitched pale line
        col = np.broadcast_to(C(0.25, 0.15, 0.08), S.shape + (3,)).copy()
        line = (np.abs(S - 0.5) < 0.05) & (((T * 300) % 4.0) < 2.0)
        col = lerp_col(col, C(0.85, 0.78, 0.62), line * 0.9)
        return col, 0.6 * np.ones_like(S), np.ones_like(S)

    return {'wood': wood, 'pad': pad, 'steel': steel, 'leash': leash, 'leather': leather, 'cuff': cuff}


def ring(block, c, axis, R, r, n_around, n_tube):
    u, v = common.frame(axis, V3((1, 0, 0)) if abs(V3(axis).x) < 0.9 else V3((0, 1, 0)))
    pts = [c + (u * math.cos(2 * math.pi * k / n_around) + v * math.sin(2 * math.pi * k / n_around)) * R for k in range(n_around)]
    import bird
    return bird.loop_tube(block, pts, r, n_tube, axis)


def wakr(level=0):
    """The perch: the padded top, the turned wooden head under it, the clad stake, its foot in the sand, the leash's
    steel ring, the iron spike below the sand."""
    n = 28 if level == 0 else 12
    z, up = V3((0, 0, 1)), V3((1, 0, 0))
    out = []
    # the pad: 150 mm across (the retail figure), 10 mm thick, its edge rounded
    pad = []
    for (h, r) in ((0.0, 66.0), (-2.5, 73.0), (-6.0, 75.0), (-10.0, 74.0)):
        pad.append(Sec(V3((0, 0, h)), V3((1, 0, 0)), V3((0, 1, 0)), r))
    out.append(loft('pad', pad, n, caps=(True, True)))
    # the wooden head: a turned block under the pad, narrowing in a curve to the stake
    head = [(-9.0, 74.0), (-14.0, 75.0), (-30.0, 73.0), (-38.0, 66.0), (-50.0, 48.0), (-66.0, 32.0), (-80.0, 24.0), (-92.0, 22.0)]
    out.append(loft('wood', [Sec(V3((0, 0, h)), V3((1, 0, 0)), V3((0, 1, 0)), r) for h, r in head], n, caps=(True, True)))
    # the stake, clad in wood, with two turned rings, flaring to its foot at the sand
    stake = [(-92, 21), (-120, 20), (-124, 23), (-128, 20), (-200, 19), (-204, 22), (-208, 19), (-270, 20), (-290, 26), (GROUND + 2, 34), (GROUND - 10, 30)]
    if level != 0:
        stake = [(-92, 21), (-200, 19), (-270, 20), (GROUND + 2, 34), (GROUND - 10, 30)]
    out.append(loft('wood', [Sec(V3((0, 0, h)), V3((1, 0, 0)), V3((0, 1, 0)), r) for h, r in stake], max(10, n // 2), caps=(True, True),
                    s=[(0 - h) / 320.0 for h, r in stake]))
    if level == 0:
        # the leash's ring on the stake, and the iron spike under the sand (it shows only if the sand is dug away)
        out.append(ring('steel', V3((0, 0, -236)), z, 27.0, 2.6, 18, 6))
        out.append(loft('steel', [Sec(V3((0, 0, GROUND - 8)), V3((1, 0, 0)), V3((0, 1, 0)), 9.0),
                                  Sec(V3((0, 0, GROUND - 150)), V3((1, 0, 0)), V3((0, 1, 0)), 1.0)], 8, caps=(True, True)))
    return out


def mursil(swivel, level=0):
    """The leash from the jesses' swivel down to the perch's ring, slack."""
    a = V3(swivel)
    b = V3((27.0, 0.0, -238.0))
    mid = a.lerp(b, 0.5) + V3((32, 4, -10))
    pts = smooth_path([a, a.lerp(mid, 0.6) + V3((10, 2, 0)), mid, mid.lerp(b, 0.6) + V3((6, 0, 0)), b], 14 if level == 0 else 6)
    return [tube('leash', pts, [2.4] * len(pts), 6 if level == 0 else 4, up=V3((0, 1, 0)))]


def dass(level=0):
    """The dass: the padded cuff from mid forearm over the wrist and the fist (thumb up), the thumb's bulge over the
    curled index finger, the knuckles' ridge."""
    n = 20 if level == 0 else 10
    X, Y, Z = V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1))
    out = []
    top = 52.0          # the fist's top above the glove's axis
    o = V3((0, 0, -top))          # the axis in the file: the origin is the fist's top
    rows = [   # (x, half height up, down, half width, squareness): from mid forearm over the wrist and the fist
        (-160, 47, 47, 43, 2.2), (-153, 50, 50, 46, 2.2), (-145, 47, 47, 43, 2.2), (-100, 44, 44, 39, 2.2),
        (-70, 43, 43, 36, 2.3), (-50, 44, 45, 34, 2.4), (-25, 50, 53, 36, 2.6), (5, 52, 53, 37, 2.8),
        (28, 47, 45, 34, 2.8), (40, 35, 33, 30, 2.6), (47, 17, 17, 19, 2.2),
    ]
    if level != 0:
        rows = [rows[0], rows[2], rows[4], rows[6], rows[7], rows[9], rows[10]]
    secs = [Sec(o + X * x, Z, Y, au, ad, b, b, p=p) for (x, au, ad, b, p) in rows]
    s = [(x + 160) / 207.0 for (x, *_r) in rows]
    out.append(loft('leather', secs, n, s=s, caps=(True, True)))
    if level == 0:
        # the cuff's rolled edge
        out.append(ring('cuff', o + X * (-153), X, 48.0, 5.0, 20, 6))
        # the thumb, over the curled index finger on the fist's top (the fist's left, toward the falconer's body)
        pts = [o + V3((-42, 16, 34)), o + V3((-12, 14, 46)), o + V3((14, 8, 49)), o + V3((30, 2, 44))]
        out.append(tube('leather', smooth_path(pts, 7), [13, 12.5, 11.5, 11, 10.5, 10, 9], 8, up=Z))
        # the knuckles' ridge on the fist's back (right)
        pts = [o + V3((-18, -33, 26)), o + V3((0, -35, 12)), o + V3((10, -35, -10)), o + V3((14, -33, -30))]
        out.append(tube('leather', smooth_path(pts, 6), [5, 6, 6, 6, 5, 4], 6, up=X))
    return out


def run(B):
    import saker
    at = Atlas(dict(BLOCKS))
    sw = (84.0, 0.0, -66.0)
    for name in ('wakr', 'dass'):
        for level in (1, 0):
            B.fresh()
            col, orm = at.paint(256 if level == 0 else 128, painters())
            mat = common.material('gear' if level == 0 else 'gear_far', col, orm)
            rname = name + ('' if level == 0 else '_lod1')
            root = common.empty(rname)
            if name == 'wakr':
                parts = {'block': wakr(level), 'mursil': mursil(sw, level)}
                pts = {'wakr_top': ((0, 0, 0), (1, 0, 0), (0, 0, 1)), 'wakr_ring': ((27, 0, -236), (1, 0, 0), (0, 0, 1)),
                       'ground': ((0, 0, GROUND), (1, 0, 0), (0, 0, 1)), 'leash_swivel': (sw, (1, 0, 0), (0, 0, 1))}
            else:
                parts = {'glove': dass(level)}
                pts = {'dass_top': ((0, 0, 0), (1, 0, 0), (0, 0, 1)), 'hand_l': ((-15, 0, -52), (1, 0, 0), (0, 0, 1)),
                       'forearm': ((-120, 0, -52), (1, 0, 0), (0, 0, 1))}
            objs = B.add_parts(root, name, parts, at, mat)
            if level == 0:
                B.add_points(root, pts)
            path = B.os.path.join(B.OUT, rname + '.glb')
            common.export(path, root)
            t, imgs, nbytes = common.glb_report(path)
            lo, hi = B.bounds(objs)
            print(f'{rname}.glb: ' + ', '.join(f'{k} {v}' for k, v in sorted(t.items())) + f'; total {sum(t.values())} triangles; '
                  f'textures {", ".join(f"{w}x{h}" for _, w, h in imgs)}; {nbytes / 1024:.0f} KB; '
                  f'bounds x {lo[0]:.0f}..{hi[0]:.0f} y {lo[1]:.0f}..{hi[1]:.0f} z {lo[2]:.0f}..{hi[2]:.0f} mm')

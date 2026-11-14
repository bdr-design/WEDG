"""The coats, painted by marks with numpy (README.md says what each mark is and where it comes from).

Each texel of the atlas is first found on the standing animal (the alert pose of the close model): its place P (mm,
the rest frame) and the outward direction N there, from the sections the piece was lofted from. The marks are then
painted where they lie on the body (the saddle on the back, the pale belly, the dark rim of the eye), so they run on
across pieces and seams, and the same texture fits every pose of the same animal.
"""
import math

import numpy as np

from common import Atlas

BLOCKS = {
    'body': (0.0, 0.5, 1.0, 1.0),
    'neck': (0.0, 0.25, 0.3125, 0.5),
    'head': (0.3125, 0.25, 0.8125, 0.5),
    'jaw': (0.8125, 0.25, 1.0, 0.5),
    'foreleg': (0.0, 0.125, 0.375, 0.25),
    'hindleg': (0.375, 0.125, 0.75, 0.25),
    'ear': (0.75, 0.125, 0.875, 0.25),
    'forepaw': (0.875, 0.125, 1.0, 0.25),
    'tail': (0.0, 0.0, 0.375, 0.125),
    'hindpaw': (0.375, 0.0, 0.5, 0.125),
    'eye': (0.5, 0.0, 0.5625, 0.0625),
    'nose': (0.5625, 0.0, 0.625, 0.0625),
    'teeth': (0.5, 0.0625, 0.5625, 0.125),
    'collar': (0.625, 0.0, 0.875, 0.125),
}


def atlas():
    return Atlas(BLOCKS)


def C(*rgb):
    return np.array(rgb, np.float32)


def mix(a, b, t):
    t = np.clip(np.asarray(t, np.float32), 0, 1)[..., None]
    return a * (1 - t) + b * t


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def hash3(ix, iy, iz, seed):
    h = np.sin(ix * 127.1 + iy * 311.7 + iz * 74.7 + seed * 19.19) * 43758.5453
    return (h - np.floor(h)).astype(np.float32)


def noise3(P, cell, seed=0, stretch=(1.0, 1.0, 1.0)):
    """Smooth value noise in space (-1..1): P (..., 3) in mm, [cell] mm, [stretch] the cell's length along x, y, z
    (hairs: long along their run). The same place gives the same value on every piece."""
    q = P / (cell * np.array(stretch, np.float32))
    i = np.floor(q)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * hash3(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return (out - 0.5) * 2


class Surface:
    """Where a block's texels lie on the standing animal."""

    def __init__(self, shape):
        self.g = shape.grid(96)                         # [sections, angles, 3]
        self.s = np.array(shape.s)
        self.c = np.array([tuple(sec.c) for sec in shape.secs])
        self.shape = shape

    def at(self, S, T):
        ns, nt = self.g.shape[0], self.g.shape[1] - 1
        i = np.clip(np.searchsorted(self.s, S, side='right') - 1, 0, ns - 2)
        f = np.clip((S - self.s[i]) / np.maximum(self.s[i + 1] - self.s[i], 1e-9), 0, 1)
        tt = np.clip(T, 0, 1) * nt
        j = np.clip(np.floor(tt).astype(int), 0, nt - 1)
        g = tt - j
        a = self.g[i, j] * (1 - g[..., None]) + self.g[i, j + 1] * g[..., None]
        b = self.g[i + 1, j] * (1 - g[..., None]) + self.g[i + 1, j + 1] * g[..., None]
        P = a * (1 - f[..., None]) + b * f[..., None]
        c = self.c[i] * (1 - f[..., None]) + self.c[i + 1] * f[..., None]
        N = P - c
        N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-9)
        return P.astype(np.float32), N.astype(np.float32)


# ------------------------------------------------------------------ the coats
class Coat:
    """One animal's colours and marks. [rest]: the standing animal (canid.Canid, alert pose, close model)."""

    def __init__(self, kind, rest):
        self.kind, self.rest = kind, rest
        self.H = rest.H
        o, hd, hn, hv, Lh = rest.head_frame
        self.hf = (np.array(tuple(o)), np.array(tuple(hd)), np.array(tuple(hn)), np.array(tuple(hv)), Lh)
        self.eyes = [np.array(tuple(rest.points['eye_l'])), np.array(tuple(rest.points['eye_r']))]
        self.er = rest.S['eye'][3] * self.H

    def head_coords(self, P):
        o, hd, hn, hv, Lh = self.hf
        d = P - o
        return d @ hd / Lh, d @ hn / self.H, -(d @ hv) / self.H

    def __call__(self, block, P, N, S, T):
        f = getattr(self, 'kind_' + self.kind)
        return f(block, P, N, S, T)

    # shared pieces of a coat
    def fur(self, P, block, base, seed=1, amount=0.06):
        """Fine hair: streaks along the hair's run (back along the body and head, down the legs), lighter and darker."""
        st = (4.0, 1.0, 1.0) if block in ('body', 'neck', 'head', 'jaw') else (1.0, 1.0, 4.0)
        n1 = noise3(P, 2.2, seed, st)
        n2 = noise3(P, 9.0, seed + 7)
        return base * (1 + amount * n1[..., None] + 0.04 * n2[..., None])

    def eye_rim(self, P, col, rim, width=1.18):
        """The dark-lined lids round the eye: an almond, longer along the head than up it, its front corner a little
        lower than its back."""
        o, hd, hn, hv, Lh = self.hf
        for e in self.eyes:
            q = P - e
            a = q @ hd
            b = q @ hn + 0.18 * a
            d = np.sqrt(a * a + (b / 0.70) ** 2)
            col = mix(col, rim, sstep(self.er * (width + 0.22), self.er * width, d))
        return col

    def iris(self, S, iris, pupil):
        col = np.broadcast_to(C(0.12, 0.08, 0.05), S.shape + (3,)).copy()
        col = mix(col, iris, sstep(0.52, 0.6, S))
        col = mix(col, pupil, sstep(0.84, 0.88, S))
        return col

    def done(self, col, rough, block):
        occ = np.ones(col.shape[:2], np.float32)
        return col, np.broadcast_to(np.float32(rough), col.shape[:2]).copy(), occ

    # ---------------------------------------------------------------- the Arabian wolf
    def kind_wolf(self, block, P, N, S, T):
        H = self.H
        x, y, z = P[..., 0] / H, P[..., 1] / H, P[..., 2] / H
        buff = C(0.62, 0.57, 0.49)          # 'a mixture of black and slightly buffy grey' (Pocock)
        tawny = C(0.71, 0.56, 0.40)
        cream = C(0.87, 0.83, 0.75)
        dark = C(0.17, 0.15, 0.13)
        black = C(0.05, 0.045, 0.04)
        speck = sstep(0.15, 0.45, noise3(P, 1.8, 11, (2.5, 1, 1)))
        if block == 'eye':
            return self.done(self.iris(S, C(0.80, 0.60, 0.20), black), 0.08, block)
        if block == 'nose':
            col = np.broadcast_to(black, S.shape + (3,)).copy() * (1 + 0.15 * noise3(P, 1.2, 3)[..., None])
            return self.done(col, 0.4, block)
        if block == 'teeth':
            return self.done(np.broadcast_to(C(0.88, 0.85, 0.76), S.shape + (3,)).copy(), 0.35, block)
        if block in ('body', 'neck', 'tail'):
            up = N[..., 2]
            col = np.broadcast_to(buff, S.shape + (3,)).copy()
            # the flanks and the thighs' outer side washed tawny
            col = mix(col, tawny, 0.25 * sstep(0.2, -0.3, up))
            # pale below: the belly, the inner thighs, the chest and throat
            col = mix(col, cream, sstep(-0.35, -0.80, up))
            if block in ('neck', 'body'):
                fwd = N[..., 0]
                throat = sstep(0.0, 0.6, fwd - up * 0.7) * sstep(0.90, 0.70, z + 0.25 * up) * sstep(0.40, 0.52, x)
                col = mix(col, cream, 0.9 * throat)
            # the saddle: black-tipped guard hairs thickest along the back and over the shoulders
            sad = sstep(0.25, 0.85, up)
            if block == 'body':
                sad = sad * sstep(-0.62, -0.40, x)
            dens = 0.16 + 0.55 * sad
            col = mix(col, dark, speck * dens)
            col = mix(col, dark, 0.35 * sstep(0.93, 0.99, up))           # the darker line down the spine
            if block == 'body':
                # the dark bar over the shoulder, down and forward from the withers
                d = np.abs((x - 0.40) * 0.85 + (z - 0.86) * 0.52)
                bar = sstep(0.045, 0.01, d) * sstep(0.70, 0.80, z) * sstep(0.2, 0.6, np.abs(N[..., 1]))
                col = mix(col, dark, 0.35 * bar)
            if block == 'tail':
                s = S
                col = mix(col, buff * 0.95, 0.0)
                col = mix(col, cream * 0.95, 0.5 * sstep(0.2, 0.6, -self.tail_up(P, N)))
                gland = sstep(0.06, 0.02, np.abs(s - 0.22)) * sstep(-0.2, 0.5, self.tail_up(P, N))
                col = mix(col, dark, 0.75 * gland)
                col = mix(col, black, sstep(0.80, 0.90, s))
            col = self.fur(P, block, col)
            return self.done(col, 0.85, block)
        if block in ('foreleg', 'hindleg'):
            inner = sstep(0.05, -0.5, N[..., 1])              # the left leg's inner side faces -Y
            col = mix(tawny, cream, inner)
            col = mix(col, cream * 0.97, sstep(0.30, 0.12, z) * 0.6)  # paler toward the feet
            if block == 'hindleg':
                col = mix(col, buff, sstep(0.5, 0.75, z) * (1 - inner))
                col = mix(col, dark, speck * 0.18 * sstep(0.45, 0.7, z) * (1 - inner))
            else:
                col = mix(col, buff, sstep(0.48, 0.65, z) * (1 - inner))
                # the dark line down the front of the foreleg (as in grey wolves; faint)
                front = sstep(0.55, 0.9, N[..., 0]) * sstep(0.16, 0.22, z) * sstep(0.44, 0.36, z)
                col = mix(col, dark, 0.42 * front)
            col = self.fur(P, block, col)
            return self.done(col, 0.85, block)
        if block in ('forepaw', 'hindpaw'):
            col = np.broadcast_to(mix(tawny, cream, 0.45), S.shape + (3,)).copy()
            col = self.toes(col, S, T, N, black)
            return self.done(col, 0.8, block)
        if block in ('head', 'jaw'):
            a, b, c = self.head_coords(P)
            col = np.broadcast_to(buff, S.shape + (3,)).copy()
            col = mix(col, dark, speck * 0.32 * sstep(0.55, 0.3, a))                 # grizzled crown and brow
            col = mix(col, tawny, sstep(0.45, 0.62, a) * 0.7)                        # muzzle's top tawny
            col = mix(col, tawny * 1.03, sstep(0.0, 0.5, np.abs(c) / 0.09) * sstep(0.08, 0.25, a) * sstep(0.04, -0.01, b) * 0.6)
            # pale cheeks, lips and chin; the throat
            pale = sstep(-0.012, -0.035, b + 0.15 * (a - 0.5))
            col = mix(col, cream, pale)
            # a pale mark over the eye
            for e in self.eyes:
                q = e + self.hf[2] * (0.03 * H) - self.hf[1] * (0.01 * self.hf[4])
                col = mix(col, cream, 0.8 * sstep(0.022 * H, 0.010 * H, np.linalg.norm(P - q, axis=-1)))
            col = self.eye_rim(P, col, black)
            # a dark line from the eye's front corner toward the muzzle
            for e in self.eyes:
                q = e + self.hf[1] * (0.05 * self.hf[4]) - self.hf[2] * (0.008 * H)
                col = mix(col, dark, 0.45 * sstep(0.014 * H, 0.005 * H, np.linalg.norm(P - q, axis=-1)))
            col = self.lips(block, P, N, a, b, col, black)
            col = self.fur(P, block, col, amount=0.05)
            return self.done(col, 0.82, block)
        if block == 'ear':
            col = self.ear_paint(P, N, tawny * 0.98, cream, dark)
            return self.done(col, 0.85, block)
        if block == 'collar':
            return self.done(np.broadcast_to(C(0.2, 0.12, 0.07), S.shape + (3,)).copy(), 0.6, block)
        raise KeyError(block)

    def tail_up(self, P, N):
        """How far the tail's surface faces its own top (the side over the tail when it is raised: back and up from
        the hanging tail)."""
        return N[..., 2] * 0.5 - N[..., 0] * 0.866

    def toes(self, col, S, T, N, claw):
        # four toes: dark seams between them on the front half, black claws at the tip
        up = N[..., 2]
        fr = S
        seam = np.zeros_like(S)
        for k in (-1, 0, 1):
            seam = np.maximum(seam, sstep(0.10, 0.02, np.abs(N[..., 1] - k * 0.42)) * sstep(0.45, 0.65, fr))
        col = mix(col, col * 0.55, seam * sstep(-0.3, 0.3, up))
        col = mix(col, claw, sstep(0.86, 0.93, fr) * sstep(0.5, -0.1, up))
        col = mix(col, C(0.10, 0.09, 0.09), sstep(-0.55, -0.8, up))           # the pads below
        return col

    def lips(self, block, P, N, a, b, col, black):
        if block == 'head':
            under = sstep(-0.35, -0.75, N[..., 2] * 0.8 + 0.2 * N[..., 0])
            mouth = under * sstep(0.44, 0.54, a)
            col = mix(col, black, sstep(0.0, 0.3, mouth) * sstep(0.6, 0.3, mouth))
            col = mix(col, C(0.42, 0.22, 0.22), sstep(0.5, 0.85, mouth))      # the roof of the mouth
        else:
            hinge, jd, jn, jv = self.rest.jaw_frame
            jn = np.array(tuple(jn))
            top = (N @ jn)
            col = mix(col, black, sstep(0.25, 0.5, top) * sstep(0.85, 0.6, top) * sstep(0.40, 0.50, a))
            col = mix(col, C(0.55, 0.28, 0.30), sstep(0.7, 0.9, top))         # the tongue and gums
        return col

    def ear_paint(self, P, N, back, inner, edge):
        fwd = N[..., 0]
        col = mix(back, inner, sstep(-0.1, 0.35, fwd))
        e = sstep(0.55, 0.85, np.abs(N[..., 1]) + 0.2 * np.abs(N[..., 2]))
        col = mix(col, edge, 0.55 * e * sstep(0.2, -0.2, fwd))
        return self.fur(P, 'ear', col, amount=0.05)

    # ---------------------------------------------------------------- the guard dog and the stray
    def kind_dog(self, block, P, N, S, T):
        return self.dog(block, P, N, S, T, stray=False)

    def kind_stray(self, block, P, N, S, T):
        return self.dog(block, P, N, S, T, stray=True)

    def dog(self, block, P, N, S, T, stray):
        H = self.H
        x, y, z = P[..., 0] / H, P[..., 1] / H, P[..., 2] / H
        if stray:
            base = C(0.60, 0.46, 0.33)        # a dull ginger-tan
            back = C(0.36, 0.27, 0.19)
            white = C(0.78, 0.72, 0.62)       # off-white, dusty
        else:
            base = C(0.80, 0.63, 0.42)        # sandy (one of the pariah type's colours)
            back = C(0.68, 0.51, 0.33)
            white = C(0.92, 0.90, 0.85)
        black = C(0.05, 0.045, 0.04)
        if block == 'eye':
            return self.done(self.iris(S, C(0.36, 0.20, 0.08), black), 0.08, block)
        if block == 'nose':
            return self.done(np.broadcast_to(black, S.shape + (3,)).copy(), 0.4, block)
        if block == 'teeth':
            return self.done(np.broadcast_to(C(0.88, 0.85, 0.76), S.shape + (3,)).copy(), 0.35, block)
        if block == 'collar':
            # leather, darker at its edges; the steel ring (the small torus) is in the same block
            col = np.broadcast_to(C(0.24, 0.14, 0.08), S.shape + (3,)).copy()
            col = mix(col, C(0.12, 0.07, 0.04), sstep(0.35, 0.48, np.abs(T - 0.5)) * 0.5)
            return self.done(col, 0.6, block)
        mott = noise3(P, 40.0, 5)
        if block in ('body', 'neck', 'tail'):
            up = N[..., 2]
            col = mix(base, back, sstep(0.45, 0.9, up) * (0.9 if stray else 0.6))
            if stray:
                col = mix(col, back, 0.35 * sstep(0.1, 0.5, mott))
            col = mix(col, white, sstep(-0.3, -0.7, up) * (0.6 if stray else 1.0))
            if block == 'neck':
                fwd = N[..., 0]
                col = mix(col, white, sstep(0.1, 0.6, fwd - up * 0.5) * sstep(1.1, 0.9, z) * (0.7 if stray else 1.0))
            if block == 'body':
                col = mix(col, white, sstep(0.45, 0.55, x) * sstep(0.1, 0.6, N[..., 0]) * sstep(0.85, 0.65, z) * (0.7 if stray else 1.0))
                if stray:
                    col = self.lean(P, N, x, z, col)
            if block == 'tail':
                col = mix(col, white, sstep(0.80, 0.88, S) * (0.0 if stray else 1.0))
            col = self.fur(P, block, col, amount=0.07 if stray else 0.05)
            if stray:
                col = mix(col, C(0.66, 0.58, 0.47), 0.25 * sstep(0.62, 0.45, z) * sstep(-0.4, 0.2, -up))   # dust on the belly
            return self.done(col, 0.88 if stray else 0.82, block)
        if block in ('foreleg', 'hindleg'):
            inner = sstep(0.05, -0.5, N[..., 1])
            col = mix(base, white, inner * (0.5 if stray else 0.8))
            if not stray:
                col = mix(col, white, sstep(0.16, 0.10, z))                         # white socks
            else:
                col = mix(col, C(0.62, 0.55, 0.44), 0.45 * sstep(0.28, 0.08, z))    # dust and dirt up the legs
            col = self.fur(P, block, col)
            return self.done(col, 0.85, block)
        if block in ('forepaw', 'hindpaw'):
            col = np.broadcast_to(white if not stray else C(0.55, 0.48, 0.38), S.shape + (3,)).copy()
            col = self.toes(col, S, T, N, black)
            return self.done(col, 0.8, block)
        if block in ('head', 'jaw'):
            a, b, c = self.head_coords(P)
            col = mix(base, back, sstep(0.03, 0.08, b) * sstep(0.6, 0.3, a) * 0.5)
            col = mix(col, base * 0.82, sstep(0.75, 0.95, a))                      # the muzzle's end darker
            col = mix(col, white, sstep(-0.02, -0.045, b + 0.1 * (a - 0.5)) * (0.5 if stray else 0.8))
            col = self.eye_rim(P, col, black, 1.35)
            col = self.lips(block, P, N, a, b, col, black)
            col = self.fur(P, block, col, amount=0.05)
            return self.done(col, 0.82, block)
        if block == 'ear':
            col = self.ear_paint(P, N, back * 1.05, mix(base, white, 0.6)[None, None] * np.ones(S.shape + (1,), np.float32), back * 0.7)
            return self.done(col, 0.85, block)
        raise KeyError(block)

    def lean(self, P, N, x, z, col):
        """A thin dog: the ribs showing as shallow grooves on the chest's sides, the hip bones and the spine marked."""
        H = self.H
        side = np.abs(N[..., 1])
        # ribs: grooves slanting back and down, about 22 mm apart, over the chest behind the shoulder
        r = (x * H - (z - 0.75) * H * 0.35) / (0.040 * H)
        groove = (0.5 + 0.5 * np.cos(2 * np.pi * r)) ** 3
        zone = sstep(-0.05, 0.05, x) * sstep(0.30, 0.20, x) * sstep(0.58, 0.66, z) * sstep(0.90, 0.82, z) * sstep(0.4, 0.8, side)
        col = mix(col, col * 0.72, groove * zone)
        col = mix(col, col * 1.12, (1 - groove) * zone * 0.5)
        # the hip bone (its point under the skin) light, a hollow under it
        hp = np.array([-0.30 * H, 0.0, 0.90 * H], np.float32)
        d = np.linalg.norm((P - hp) * np.array([1, 0, 1], np.float32), axis=-1) / H
        col = mix(col, col * 1.15, sstep(0.05, 0.02, d) * sstep(0.4, 0.7, side))
        col = mix(col, col * 0.78, sstep(0.10, 0.06, d) * sstep(0.04, 0.07, d) * sstep(0.4, 0.7, side) * sstep(0.91, 0.86, z))
        # the hollow of the flank before the thigh
        fl = sstep(-0.06, -0.14, x) * sstep(-0.28, -0.20, x) * sstep(0.65, 0.72, z) * sstep(0.88, 0.80, z) * sstep(0.5, 0.8, side)
        col = mix(col, col * 0.82, fl)
        return col


def paint(kind, atl, size, rest):
    """The atlas for [kind] ('wolf', 'dog', 'stray'), [size] px: (colour, roughness/occlusion)."""
    coat = Coat(kind, rest)
    surf = {b: Surface(sh) for b, sh in rest.shapes.items()}

    def painter_for(block):
        def f(S, T):
            P, N = surf[block].at(S, T)
            col, rough, occ = coat(block, P, N, S, T)
            return col, rough, occ
        return f

    def flat(block):
        def f(S, T):
            P = np.zeros(S.shape + (3,), np.float32)
            N = np.zeros(S.shape + (3,), np.float32)
            N[..., 2] = 1
            return coat(block, P, N, S, T)
        return f

    painters = {b: painter_for(b) for b in surf}
    for b in ('teeth', 'collar'):
        if b not in painters:
            painters[b] = flat(b)
    return atl.paint(size, painters)

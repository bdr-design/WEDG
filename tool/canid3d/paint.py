"""The coats, painted by marks with numpy (README.md says what each mark is and where it comes from).

Each texel is first found on the standing animal (texture.py): its place P (mm, the rest frame: X forward, Z up, Y to
the animal's left), the outward direction N there, the piece of the build it lies over (its block, e.g. 'foreleg')
and its place on that piece (S along it, T around it). The marks are painted where they lie on the body, and where
two parts of the body meet (a leg and the trunk, the head and the neck, an ear and the skull, the tail and the rump)
the two parts' colours are blended across the join, so the skin shows no seam.
"""
import numpy as np


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


def noise3(P, cell, seed=0):
    """Smooth value noise in space (-1..1): P (..., 3) in mm, [cell] mm. The same place gives the same value in every
    pose."""
    q = P / cell
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


# the hair's run, as the noise's stretch along x, y, z: back along the trunk and head, down the legs and the tail
RUN_TRUNK = np.array([4.5, 1.0, 1.4], np.float32)
RUN_DOWN = np.array([1.0, 1.0, 4.5], np.float32)

LEG_BLOCKS = ('foreleg', 'hindleg', 'forepaw', 'hindpaw')
HEAD_BLOCKS = ('head', 'jaw', 'nose', 'eye')

PALETTES = {
    # the Arabian wolf: 'a mixture of black and slightly buffy grey' (Pocock); greyish beige; legs paler and tawny
    'wolf': dict(ground=C(0.55, 0.50, 0.43), tawny=C(0.66, 0.53, 0.39), pale=C(0.82, 0.78, 0.70), dark=C(0.14, 0.12, 0.10),
                 grizzle=0.78, saddle=0.85, bar=0.35, legline=0.40, iris=C(0.80, 0.60, 0.20), tailtip=True, gland=True,
                 white_feet=False, dust=0.0, tailwhite=False),
    # the guard dog: sandy, white chest, belly, feet and tail tip (one of the pariah type's colours)
    'dog': dict(ground=C(0.80, 0.63, 0.42), tawny=C(0.78, 0.61, 0.40), pale=C(0.92, 0.90, 0.85), dark=C(0.55, 0.40, 0.25),
                grizzle=0.10, saddle=0.35, bar=0.0, legline=0.0, iris=C(0.36, 0.20, 0.08), tailtip=False, gland=False,
                white_feet=True, dust=0.0, tailwhite=True),
    # the stray: dull ginger-tan, a darker mottled back, off-white below, dusty
    'stray': dict(ground=C(0.60, 0.46, 0.33), tawny=C(0.58, 0.45, 0.32), pale=C(0.76, 0.70, 0.60), dark=C(0.30, 0.22, 0.15),
                  grizzle=0.25, saddle=0.75, bar=0.0, legline=0.0, iris=C(0.36, 0.20, 0.08), tailtip=False, gland=False,
                  white_feet=False, dust=0.35, tailwhite=False),
}
PALETTES['wolf_winter'] = PALETTES['wolf']


class Coat:
    """One animal's coat. [rest]: the standing animal (canid.Canid, alert pose)."""

    def __init__(self, kind, rest, mouth_open=False):
        self.kind = kind
        self.mouth_open = mouth_open
        self.pal = PALETTES[kind]
        self.rest = rest
        self.H = rest.H
        o, hd, hn, hv, Lh = rest.head_frame
        self.hf = (np.array(tuple(o)), np.array(tuple(hd)), np.array(tuple(hn)), np.array(tuple(hv)), Lh)
        self.eyes = []
        self.er = rest.S['eye'][3] * self.H
        # the almond's height to its length: the dog's eye is set more to the front, so it is opened wider for the
        # front view to read it as open
        self.eye_open = 0.52 if kind.startswith('wolf') else 0.95
        for sg, side in ((1, 'l'), (-1, 'r')):
            c = np.array(tuple(rest.points['eye_' + side]))
            out = np.radians(rest.S['eye_out'])
            look = self.hf[1] * np.cos(out) - self.hf[3] * (sg * np.sin(out))
            self.eyes.append((c, look / np.linalg.norm(look)))
        self.ears = [np.array(tuple(rest.points['ear_' + s])) for s in ('l', 'r')]
        torso = rest.S['torso']
        self.tx = np.array([r[0] for r in torso])
        self.tbot = np.array([r[2] for r in torso])
        self.ttop = np.array([r[1] for r in torso])

    def head_coords(self, P):
        o, hd, hn, hv, Lh = self.hf
        d = P - o
        return d @ hd / Lh, d @ hn / self.H, -(d @ hv) / self.H

    # ---------------------------------------------------------------- the parts' colours
    def trunk(self, P, N):
        """The trunk and the neck: the ground colour, the grizzled saddle, the pale underside graded into the flank."""
        H, pal = self.H, self.pal
        x, z = P[..., 0] / H, P[..., 2] / H
        up = N[..., 2]
        col = np.broadcast_to(pal['ground'], P.shape).copy()
        # the lower flanks a little tawny, the underside pale, graded softly (no line)
        col = mix(col, pal['tawny'], 0.30 * sstep(0.25, -0.35, up))
        # (only on the trunk's lower part: a bulge's underside higher up, at the shoulder or the thigh, keeps the
        # ground colour)
        zt = np.interp(x, self.tx, self.ttop)
        zb = np.interp(x, self.tx, self.tbot)
        low = sstep(0.50, 0.22, (z - zb) / np.maximum(zt - zb, 1e-3))
        col = mix(col, pal['pale'], (sstep(-0.15, -0.85, up) ** 1.3) * low)
        # the throat and chest pale
        fwd = N[..., 0]
        throat = sstep(-0.1, 0.65, fwd - up * 0.6) * sstep(0.95, 0.70, z + 0.2 * up) * sstep(0.36, 0.52, x)
        col = mix(col, pal['pale'], 0.85 * throat)
        # the saddle: black-tipped guard hairs, in streaks along the hair, thickest on the back and over the shoulders;
        # its edge soft
        sad = sstep(0.05, 0.85, up) * sstep(-0.70, -0.42, x)
        n1 = noise3(P / RUN_TRUNK, 1.1, 11)
        n2 = noise3(P, 6.0, 12)
        streak = sstep(-0.1, 0.6, n1 + 0.35 * n2)
        dens = pal['grizzle'] * (0.18 + 0.82 * sad)
        col = mix(col, pal['dark'], streak * dens * pal['saddle'])
        col = mix(col, pal['dark'], 0.25 * pal['saddle'] * sstep(0.90, 0.99, up) * sstep(-0.6, -0.3, x))
        if pal['bar']:
            # the dark bar over the shoulder, down and forward from the withers (the V over the shoulders)
            d = np.abs((x - 0.40) * 0.85 + (z - 0.86) * 0.52)
            bar = sstep(0.06, 0.015, d) * sstep(0.66, 0.80, z) * sstep(0.1, 0.6, np.abs(N[..., 1]))
            col = mix(col, pal['dark'], pal['bar'] * bar * (0.5 + 0.5 * streak))
        if pal['dust']:
            col = mix(col, C(0.66, 0.58, 0.47), pal['dust'] * 0.7 * sstep(-0.2, -0.7, up))
            mott = noise3(P, 40.0, 5)
            col = mix(col, pal['dark'], 0.30 * sstep(0.1, 0.5, mott) * sstep(-0.1, 0.5, up))
        return col

    def leg(self, P, N, hind):
        H, pal = self.H, self.pal
        z = P[..., 2] / H
        inner = sstep(0.05, -0.55, N[..., 1] * np.sign(P[..., 1] + 1e-6))     # the inner side faces the midline
        col = mix(pal['tawny'], pal['pale'], inner * 0.85)
        col = mix(col, mix(pal['tawny'], pal['pale'], 0.45), sstep(0.30, 0.10, z) * 0.6)       # paler toward the feet
        if pal['legline'] and not hind:
            # the faint dark line down the front of the foreleg
            front = sstep(0.55, 0.92, N[..., 0]) * sstep(0.15, 0.21, z) * sstep(0.44, 0.36, z)
            col = mix(col, pal['dark'], pal['legline'] * front)
        if pal['white_feet']:
            col = mix(col, pal['pale'], sstep(0.17, 0.11, z))
        if pal['dust']:
            col = mix(col, C(0.62, 0.55, 0.44), pal['dust'] * 1.2 * sstep(0.30, 0.06, z))
        return col

    def toes(self, col, S, N):
        up = N[..., 2]
        col = mix(col, C(0.07, 0.06, 0.06), sstep(0.88, 0.96, S) * sstep(0.6, -0.2, up))     # the claws
        col = mix(col, C(0.11, 0.10, 0.10), sstep(-0.50, -0.80, up))                          # the pads below
        return col

    def head(self, P, N, block, Ph=None):
        H, pal = self.H, self.pal
        P = P if Ph is None else Ph
        a, b, c = self.head_coords(P)
        col = np.broadcast_to(pal['ground'], P.shape).copy()
        n1 = noise3(P / np.array([3.0, 1.2, 1.2], np.float32), 0.9, 21)
        col = mix(col, pal['dark'], pal['grizzle'] * 0.5 * sstep(0.0, 0.6, n1) * sstep(0.55, 0.25, a) * sstep(-0.01, 0.04, b))
        col = mix(col, pal['tawny'], sstep(0.42, 0.62, a) * 0.65)                    # the bridge of the muzzle
        col = mix(col, pal['pale'], sstep(-0.005, -0.040, b + 0.12 * (a - 0.5)))      # pale lips, chin, cheeks
        if self.kind.startswith('wolf'):
            # a pale mark over each eye; a short dark line from the eye's front corner
            for e, look in self.eyes:
                q = e + self.hf[2] * (0.030 * H) - self.hf[1] * (0.01 * self.hf[4])
                col = mix(col, pal['pale'], 0.7 * sstep(0.024 * H, 0.010 * H, np.linalg.norm(P - q, axis=-1)))
        else:
            col = mix(col, col * 0.85, sstep(0.75, 0.95, a))                         # the muzzle's end darker
        col = self.eye(P, col)
        col = self.lip_line(P, a, b, c, col)
        return self.nose_mouth(P, N, a, col, block)

    def lip_line(self, P, a, b, c, col):
        """The black edge of the lips along the mouth, from under the nose back to the corner of the mouth (below the
        eye's front), where the upper lip meets the lower: painted on the skin by place."""
        rows = self.rest.S['head']
        ta = np.array([r[0] for r in rows])
        lip = np.array([r[1] - r[3] for r in rows])          # the upper head's lower edge (H)
        # the line runs straight back to the mouth's corner (a curl up at its end would read as a grin)
        a0 = 0.62
        bl = np.interp(np.maximum(a, a0), ta, lip) + 0.004 - 0.02 * np.clip(a0 - a, 0, None)
        on = sstep(0.0045, 0.0015, np.abs(b - bl)) * sstep(0.50, 0.56, a) * sstep(1.0, 0.95, a)
        return mix(col, C(0.05, 0.045, 0.04), on)

    def eye(self, P, col):
        """The eye on the skin: an almond (longer along the head, its front corner lower, set obliquely), the iris,
        the pupil, the dark-lined lids."""
        o, hd, hn, hv, Lh = self.hf
        for (e, look), sg in zip(self.eyes, (1, -1)):
            q = P - e
            if self.eye_open > 0.6:
                # the dog's almond laid out in the plane its eye looks out of, so it reads open from the front
                across = np.cross(hn, look)
                across /= np.linalg.norm(across)
                a = q @ across * sg
            else:
                a = q @ hd
            b = q @ hn + (0.22 if self.eye_open < 0.6 else 0.08) * a
            d = np.sqrt(a * a + (b / self.eye_open) ** 2) / self.er
            # painted by its place along and up the head only, on its own side: the eye sits a little into the
            # cheek's fur, so its almond is laid on the surface over it, not on the bulge's own curve
            front = sstep(0.0, 0.3, -(P - o) @ hv * sg / self.er)
            iris = sstep(0.86, 0.70, d) * front
            col = mix(col, C(0.06, 0.05, 0.045), sstep(1.10, 0.95, d) * front)                   # the lids' dark rim
            col = mix(col, self.pal['iris'] * 0.9, iris)
            col = mix(col, C(0.03, 0.03, 0.03), sstep(0.46, 0.34, d) * iris)                     # the pupil
        return col

    def nose_mouth(self, P, N, a, col, block):
        black = C(0.05, 0.045, 0.04)
        o, hd, hn, hv, Lh = self.hf
        nose = np.array(tuple(self.rest.points['nose']))
        nr = self.rest.S['nose'][2] * self.H
        col = mix(col, black * 1.2, sstep(nr * 1.6, nr * 1.3, np.linalg.norm(P - nose, axis=-1)))
        for sg in (1, -1):                                   # the nostrils: two dark commas on the pad's front
            q = nose - hv * (sg * nr * 0.45) - hn * (nr * 0.1) - hd * (nr * 0.2)
            col = mix(col, C(0.0, 0.0, 0.0), sstep(nr * 0.38, nr * 0.22, np.linalg.norm(P - q, axis=-1)))
        hinge, jd, jn, jv = self.rest.jaw_frame
        jn = np.array(tuple(jn))
        if block == 'jaw':
            top = N @ jn
            if self.mouth_open:
                col = mix(col, black, sstep(0.30, 0.50, top) * sstep(0.80, 0.62, top) * sstep(0.40, 0.50, a))
            else:
                col = mix(col, black, sstep(0.25, 0.50, top) * sstep(0.56, 0.62, a))      # shut: the lower lip's edge
            if self.mouth_open:
                col = mix(col, C(0.55, 0.28, 0.30), sstep(0.70, 0.90, top))          # the tongue and gums
        else:
            under = sstep(-0.45, -0.80, N[..., 2] * 0.85 + 0.15 * N[..., 0])
            mouth = under * sstep(0.56, 0.62, a)
            col = mix(col, black, sstep(0.05, 0.25, mouth) * sstep(0.55, 0.35, mouth))   # the lips' thin dark line
            if self.mouth_open:
                col = mix(col, C(0.42, 0.22, 0.22), sstep(0.55, 0.9, mouth))         # the roof of the mouth
        return col

    def ear(self, P, N):
        pal = self.pal
        fwd = N[..., 0]
        col = mix(pal['tawny'] * 0.96, pal['pale'], sstep(-0.05, 0.40, fwd))           # pale fur inside
        e = sstep(0.60, 0.88, np.abs(N[..., 1]) + 0.2 * np.abs(N[..., 2]))
        return mix(col, pal['dark'], 0.5 * e * sstep(0.2, -0.2, fwd))                    # the dark edge behind

    def tail(self, P, N, S):
        pal = self.pal
        up = N[..., 2] * 0.5 - N[..., 0] * 0.866          # the tail's top when it hangs (back and up)
        col = self.trunk(P, N)
        col = mix(col, pal['pale'] * 0.96, 0.5 * sstep(0.2, 0.6, -up))
        if pal['gland']:
            col = mix(col, pal['dark'], 0.7 * sstep(0.07, 0.02, np.abs(S - 0.22)) * sstep(-0.2, 0.5, up))
        if pal['tailtip']:
            col = mix(col, C(0.05, 0.045, 0.04), sstep(0.80, 0.90, S))
        if pal['tailwhite']:
            col = mix(col, pal['pale'], sstep(0.80, 0.88, S))
        return col

    # ---------------------------------------------------------------- one colour per texel
    def __call__(self, P, N, S, T, block, group, Ph=None):
        """The colour of texels (arrays) lying over one kind of piece ([block]) of one [group]."""
        H = self.H
        x, z = P[..., 0] / H, P[..., 2] / H
        if block == 'collar':
            col = np.broadcast_to(C(0.24, 0.14, 0.08), P.shape).copy()
            return mix(col, C(0.12, 0.07, 0.04), sstep(0.35, 0.48, np.abs(T - 0.5)) * 0.5)
        if block == 'ring':
            return np.broadcast_to(C(0.55, 0.55, 0.57), P.shape).copy()
        if block == 'teeth':
            return np.broadcast_to(C(0.88, 0.85, 0.76), P.shape).copy()
        trunk = self.trunk(P, N)
        if block == 'body':
            col = trunk
        elif block == 'neck':
            a, b, c = self.head_coords(P)
            col = mix(trunk, self.head(P, N, 'head', Ph), sstep(-0.05, 0.15, a))
        elif block in LEG_BLOCKS:
            bot = np.interp(x, self.tx, self.tbot)
            col = mix(trunk, self.leg(P, N, block.startswith('hind')), sstep(bot - 0.02, bot - 0.16, z))
            if block.endswith('paw'):
                col = self.toes(col, S, N)
        elif block in HEAD_BLOCKS:
            a, b, c = self.head_coords(P)
            col = mix(trunk, self.head(P, N, block, Ph), sstep(-0.12, 0.10, a))
        elif block == 'ear':
            base = self.ears[0] if group.endswith('_l') else self.ears[1]
            h = (P - base) @ self.hf[2] / (self.rest.S['ear'][0] * H)
            lat = np.abs((P - self.hf[0]) @ self.hf[3]) / H         # (not on the crown between the ears)
            col = mix(self.head(P, N, 'head', Ph), self.ear(P, N), sstep(0.10, 0.30, h) * sstep(0.025, 0.045, lat))
        elif block == 'tail':
            col = mix(trunk, self.tail(P, N, S), sstep(0.0, 0.15, S))
        else:
            col = trunk
        # the hair's grain: lighter and darker streaks along its run
        run = RUN_DOWN if block in LEG_BLOCKS or block == 'tail' else RUN_TRUNK
        n1 = noise3(P / run, 1.1, 1)
        n2 = noise3(P, 8.0, 7)
        return col * (1 + 0.05 * n1[..., None] + 0.035 * n2[..., None])

    def height(self, P, block):
        """The fur's relief (mm) for the normal map: fine streaks along the hair's run and a coarser lie of the coat."""
        if block in ('collar', 'ring', 'teeth'):
            return np.zeros(P.shape[:-1], np.float32)
        run = RUN_DOWN if block in LEG_BLOCKS or block == 'tail' else RUN_TRUNK
        q = P / run
        return 0.30 * noise3(q, 0.9, 31) + 0.22 * noise3(q, 2.2, 32) + 0.6 * noise3(P, 14.0, 33)

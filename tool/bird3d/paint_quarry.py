"""The houbara's and the stone-curlew's plumage, painted by their real patterns (README.md names the sources)."""
import numpy as np

from common import C, Noise, hash01, lerp_col, seg_dist
from paint import body_coords, eye_place, plumage, soft, band, streaks


def painter(name, body, size):
    return HoubaraPaint(body, size) if name == 'houbara' else CurlewPaint(body, size)


def vermiculate(X, Y, n, scale=2.4):
    """Fine wavy dark lines (vermiculation) across a feather: 0..1."""
    w = np.sin((X + 1.8 * n(X + 40, Y + 40, 3.0)) * (2 * np.pi / scale) + 0.6 * np.sin(Y * 0.9))
    return soft(w, 0.55, 0.95)


def skin(S, T, col, n, rough=0.6):
    X, Y = S * 80.0, T * 40.0
    nz = n(X + 1, Y + 1, 2.0)
    sc = np.abs(((X / 2.4 + 0.5 * np.floor(Y / 2.4)) % 1.0) - 0.5) + np.abs(((Y / 2.4) % 1.0) - 0.5)
    sc = soft(sc, 0.55, 0.75)
    return col[None, None, :] * (0.92 + 0.06 * nz[..., None]) * (1 - 0.14 * sc[..., None]), rough + 0.1 * sc, np.ones_like(S)


def open_coords(spec, S, T, xc_frac=0.32):
    rows = np.array(spec['open'])
    span = rows[:, 0]
    Y = span[0] + S * (span[-1] - span[0])
    cs = np.cos(T * 2 * np.pi)
    c = np.where(cs >= 0, xc_frac * (1 - cs), xc_frac - (1 - xc_frac) * cs)
    chord = np.interp(Y, span, rows[:, 1] - rows[:, 2])
    return Y, c, c * chord, T < 0.5


class Base:
    def __init__(self, body, size, seed):
        self.body, self.size, self.n = body, size, Noise(seed)

    def claw_p(self, S, T):
        return np.broadcast_to(self.CLAW, S.shape + (3,)).copy(), 0.4 * np.ones_like(S), np.ones_like(S)

    def eye_p(self, S, T):
        col = np.broadcast_to(self.IRIS, S.shape + (3,)).copy()
        r = 1 - S
        # the iris' fine radial grain, the pupil black
        col = col * (0.9 + 0.1 * soft(r, 0.02, 0.12))[..., None]
        col = lerp_col(col, C(0.02, 0.02, 0.02), soft(S, self.PUPIL - 0.03, self.PUPIL))
        col = lerp_col(col, C(0.05, 0.04, 0.03), 1 - soft(S, 0.55, 0.66))
        return col, 0.06 * np.ones_like(S), np.ones_like(S)


# ------------------------------------------------------------------ the houbara
class HoubaraPaint(Base):
    SAND = C(0.80, 0.68, 0.49)           # the upperparts' sandy buff ground
    VERM = C(0.36, 0.27, 0.18)           # its fine dark vermiculation and arrowhead marks
    GREY = C(0.76, 0.76, 0.74)           # the fore-neck and upper breast, pale grey
    WHITE = C(0.94, 0.93, 0.90)          # the lower breast and belly
    BLACK = C(0.07, 0.065, 0.06)         # the neck's ruff stripe, the primaries
    IRIS = C(0.90, 0.80, 0.42)           # a pale yellow iris
    PUPIL = 0.93
    BILL = C(0.36, 0.35, 0.34)
    LEG = C(0.76, 0.74, 0.60)            # pale yellowish grey legs
    CLAW = C(0.25, 0.24, 0.22)

    def __init__(self, body, size):
        super().__init__(body, size, 21)
        import quarry
        self.spec = quarry.HOUBARA_SPEC

    def painters(self):
        return {'body': self.body_p, 'wing_fold': self.fold_p, 'wing_open': self.open_p, 'tail': self.tail_p,
                'thigh': self.thigh_p, 'skin': lambda S, T: skin(S, T, self.LEG, self.n),
                'horn': self.horn_p, 'claw': self.claw_p, 'eye': self.eye_p, 'crest': self.crest_p}

    def sandy(self, X, Y, w, l, nz, marks=0.6):
        """Sandy-buff feathers, finely vermiculated, each with a dark arrowhead or bar near its tip."""
        col, al, occ = plumage(X, Y, w, l, self.SAND, self.SAND * 1.04, self.VERM, 0.0, 0.0, nz, shade=0.08)
        v = vermiculate(X, Y, self.n)
        col = lerp_col(col, self.VERM * 1.2, v * 0.6)
        al2, ac, idx = __import__('common').feathers(X, Y, w, l)
        # a dark arrowhead (chevron) toward each feather's tip, and a dusky middle on many
        arrow = (np.abs(al2 - 0.60 - 0.30 * np.abs(ac)) < 0.13) & (np.abs(ac) < 0.8) & (hash01(idx, 2.0) < marks)
        col = lerp_col(col, self.VERM * 0.75, arrow * 0.9)
        mid = (1 - soft(np.abs(ac), 0.15, 0.4)) * soft(al2, 0.2, 0.45) * (1 - soft(al2, 0.55, 0.65)) * (hash01(idx, 4.0) < marks)
        col = lerp_col(col, self.VERM, mid * 0.5)
        return col, occ

    def body_p(self, S, T):
        D, Y, P, tt, au, ad, b = body_coords(self.body, S, T)
        nz = self.n(D + 300, Y + 300, 6.0)
        neck = soft(D, 255, 275) * (1 - soft(D, 405, 418))
        head = soft(D, 405, 418)
        belly = soft(tt, 0.19, 0.30)
        back, occ_b = self.sandy(-D, Y, 11, 8, nz)
        under, al, occ_u = plumage(-D, Y, 9, 7, self.WHITE, self.WHITE, self.WHITE, 0.0, 0.0, nz, shade=0.05)
        # the breast: pale grey grading to white below
        breast = soft(D, 200, 245)
        under = lerp_col(under, self.GREY[None, None, :] * (1 + 0.03 * nz[..., None]), breast * 0.9)
        col = lerp_col(back, under, belly)
        occ = occ_b * (1 - belly) + occ_u * belly
        # the neck: the hind neck sandy and vermiculated, the fore-neck grey; down each side the ruff's black stripe of
        # long feathers (from below the ear to the neck's base), white plumes below and behind it
        nk_back, _ = self.sandy(-D, Y, 6, 4.5, nz, marks=0.2)
        nk = lerp_col(nk_back, self.GREY[None, None, :] * (1 + 0.03 * nz[..., None]), soft(tt, 0.13, 0.22))
        side = np.abs(tt - 0.20)
        frayed = 1.2 * self.n(D + 700, Y * 3 + 700, 2.0)
        stripe = (1 - soft(side * P + frayed, 3.5, 6.0)) * band(D, 290, 395, 12)
        # its lower end breaks into separate long black feathers
        stripe = stripe * np.where(D < 320, (np.abs(((Y * 0.9) % 3.2) - 1.6) < 1.0), 1.0)
        nk = lerp_col(nk, self.BLACK, stripe * 0.95)
        plume = (1 - soft(np.abs(tt - 0.28) * P, 5.0, 8.0)) * band(D, 270, 330, 12)
        nk = lerp_col(nk, self.WHITE, plume * 0.8 * (1 - stripe))
        col = lerp_col(col, nk, neck)
        # the head: crown sandy and finely marked, a pale stripe over the eye, the face pale grey-buff, the throat white
        ed, ey = eye_place(self.body, self.spec['eye'])
        hd, _ = self.sandy(-D, Y, 4, 3, nz, marks=0.3)
        face = C(0.84, 0.80, 0.72)[None, None, :] * (1 + 0.03 * nz[..., None])
        hd = lerp_col(hd, face, soft(Y, ey - 6, ey + 2))
        hd = lerp_col(hd, self.WHITE, soft(tt, 0.32, 0.42))
        sup, _ = seg_dist(D, Y, (ed + 8, ey - 7), (ed - 22, ey - 7))
        hd = lerp_col(hd, C(0.92, 0.88, 0.80), np.clip(1 - (sup - 1.4) / 1.6, 0, 1) * 0.7)
        line, _ = seg_dist(D, Y, (ed - 4, ey + 1), (ed - 18, ey + 4))
        hd = lerp_col(hd, self.VERM, np.clip(1 - (line - 1.0) / 1.5, 0, 1) * 0.6)
        col = lerp_col(col, hd, head)
        return col, 0.88 + 0.05 * nz, occ

    def fold_p(self, S, T):
        L = 315.0
        X = (1 - S) * L
        tt = np.minimum(T, 1 - T) * 2
        H = 100 * (1 - 0.75 * soft(X, 170, 315))
        Yv = tt * H
        nz = self.n(X + 50, Yv + 50, 5.0)
        cov, occ = self.sandy(X, Yv, 12, 10, nz)
        # the tertials: long sandy feathers with dark bars
        ter, _, _ = plumage(X, Yv, 22, 50, self.SAND * 0.97, self.SAND, self.VERM, 0.0, 0.0, nz, shade=0.15)
        ter = lerp_col(ter, self.VERM, (np.abs(((X / 14.0) % 1.0) - 0.5) < 0.12) * 0.6)
        # the primaries: black, their bases white (the patch shows in flight), tucked under, the tips over the tail
        prim = self.BLACK[None, None, :] * (1 + 0.1 * nz[..., None])
        prim = lerp_col(prim, self.WHITE, band(X, 190, 215, 6) * soft(tt, 0.5, 0.8) * 0.8)
        col = lerp_col(cov, ter, soft(X, 120, 150) * (1 - soft(tt, 0.65, 0.85)))
        col = lerp_col(col, prim, np.maximum(soft(X, 220, 245), soft(tt, 0.72, 0.85) * soft(X, 100, 140)))
        return col, 0.86 + 0.05 * nz, occ

    def open_p(self, S, T):
        Y, c, Xc, upper = open_coords(self.spec, S, T)
        nz = self.n(Y + 20, Xc + 20, 6.0)
        hand = soft(Y, 270, 300)
        rem = soft(c, 0.40 - 0.1 * hand, 0.52 - 0.1 * hand)
        cov, _ = self.sandy(Y, Xc, 12, 9, nz)
        # above: the inner wing's coverts sandy, the flight feathers black and brown, a white patch at the primaries'
        # bases
        fl = lerp_col(C(0.30, 0.24, 0.18), self.BLACK, hand)
        fl = np.broadcast_to(fl, Y.shape + (3,)) if fl.ndim == 1 else fl
        fl = lerp_col(fl, self.WHITE, band(Y, 330, 540, 25) * band(c, 0.30, 0.62, 0.08) * 0.95)
        up = lerp_col(cov, fl, rem)
        # below: mostly white, the trailing edge and the primaries' tips black
        dn = np.broadcast_to(self.WHITE, Y.shape + (3,)).copy()
        dn = lerp_col(dn, self.BLACK, np.maximum(soft(c, 0.80, 0.9), soft(Y, 560, 620)) * 0.95)
        col = np.where(upper[..., None], up, dn)
        return col, 0.86 + 0.05 * nz, np.ones_like(S)

    def tail_p(self, S, T):
        X = S * 175.0
        top = T < 0.5
        nz = self.n(X + 9, T * 80 + 9, 5.0)
        a = np.where(top, np.abs(T * 4 - 1), np.abs((T - 0.5) * 4 - 1))
        # sandy buff with three or four slate bars and a white tip
        bars = np.abs(((X - 25) / 37.0) % 1.0 - 0.5) < 0.09
        col = self.SAND[None, None, :] * (1 + 0.04 * nz[..., None])
        col = lerp_col(col, self.VERM * 1.1, vermiculate(X, a * 40, self.n) * 0.35)
        col = lerp_col(col, C(0.30, 0.29, 0.29), bars * soft(X, 30, 50) * 0.9)
        col = lerp_col(col, self.WHITE, soft(X, 163, 169))
        col = np.where(top[..., None], col, lerp_col(col, self.WHITE, 0.45))
        return col, 0.87 * np.ones_like(S), np.ones_like(S)

    def thigh_p(self, S, T):
        # the shank feathered white above, the lower shank bare
        X = S * 120.0
        col = np.broadcast_to(self.WHITE, S.shape + (3,)).copy() * (1 + 0.03 * self.n(X, T * 80, 3.0))[..., None]
        col = lerp_col(col, self.LEG, soft(S, 0.62, 0.70))
        return col, 0.85 - 0.25 * soft(S, 0.62, 0.7), np.ones_like(S)

    def horn_p(self, S, T):
        col = lerp_col(np.broadcast_to(self.BILL * 1.25, S.shape + (3,)), self.BILL * 0.7, soft(S, 0.3, 0.9))
        return col, 0.45 * np.ones_like(S), np.ones_like(S)

    def crest_p(self, S, T):
        # the male's crest: white feathers, some with black tips
        col = np.broadcast_to(self.WHITE, S.shape + (3,)).copy()
        col = lerp_col(col, self.BLACK, soft(S, 0.55, 0.75) * (np.abs(((T * 6) % 1.0) - 0.5) < 0.3))
        return col, 0.85 * np.ones_like(S), np.ones_like(S)


# ------------------------------------------------------------------ the stone-curlew
class CurlewPaint(Base):
    SAND = C(0.70, 0.57, 0.40)           # sandy brown
    STREAK = C(0.24, 0.17, 0.11)         # dark brown shaft streaks
    WHITE = C(0.94, 0.92, 0.88)
    BUFF = C(0.86, 0.78, 0.64)
    BLACK = C(0.07, 0.06, 0.05)
    IRIS = C(0.97, 0.86, 0.18)           # the large bright yellow iris
    PUPIL = 0.90
    YELLOW = C(0.90, 0.80, 0.30)         # the bill's base
    LEG = C(0.90, 0.84, 0.48)            # pale yellow legs
    CLAW = C(0.10, 0.09, 0.08)

    def __init__(self, body, size):
        super().__init__(body, size, 41)
        import quarry
        self.spec = quarry.CURLEW_SPEC

    def painters(self):
        return {'body': self.body_p, 'wing_fold': self.fold_p, 'wing_open': self.open_p, 'tail': self.tail_p,
                'thigh': self.thigh_p, 'skin': lambda S, T: skin(S, T, self.LEG, self.n, 0.5),
                'horn': self.horn_p, 'claw': self.claw_p, 'eye': self.eye_p}

    def streaked(self, X, Y, w, l, base, nz, sw=0.16):
        return plumage(X, Y, w, l, base, base * 1.06, self.STREAK, sw, 0.12, nz, shade=0.08)

    def body_p(self, S, T):
        D, Y, P, tt, au, ad, b = body_coords(self.body, S, T)
        nz = self.n(D + 300, Y + 300, 5.0)
        head = soft(D * 1.0, 220, 232)
        belly = soft(tt, 0.2, 0.3)
        back, _, occ_b = self.streaked(-D, Y, 9, 7, self.SAND, nz)
        # the breast buff with fine streaks; the belly white, the undertail buff
        br, _, occ_u = self.streaked(-D, Y, 6, 5, self.BUFF, nz, sw=0.10)
        wh = self.WHITE[None, None, :] * (1 + 0.02 * nz[..., None])
        under = lerp_col(br, wh, (1 - soft(D, 110, 150)) * soft(tt, 0.32, 0.42))
        under = lerp_col(under, self.BUFF, (1 - soft(D, 15, 40)) * 0.7)
        col = lerp_col(back, under, belly)
        occ = occ_b * (1 - belly) + occ_u * belly
        # the face: a white stripe under the eye from the bill to the ear and a pale one above it, a dark stripe
        # between them under the eye, the throat white
        ed, ey = eye_place(self.body, self.spec['eye'])
        hd, _, _ = self.streaked(-D, Y, 4, 3, self.SAND, nz, sw=0.2)
        hd = lerp_col(hd, self.WHITE, soft(tt, 0.33, 0.40))
        low, _ = seg_dist(D, Y, (ed + 26, ey + 8), (ed - 22, ey + 10))
        hd = lerp_col(hd, self.WHITE, np.clip(1 - (low - 2.2) / 1.5, 0, 1))
        dark, _ = seg_dist(D, Y, (ed + 2, ey + 4.5), (ed - 22, ey + 5.5))
        hd = lerp_col(hd, self.STREAK, np.clip(1 - (dark - 1.2) / 1.2, 0, 1) * 0.85)
        sup, _ = seg_dist(D, Y, (ed + 20, ey - 10), (ed - 12, ey - 10))
        hd = lerp_col(hd, self.BUFF * 1.08, np.clip(1 - (sup - 1.5) / 1.5, 0, 1) * 0.7)
        col = lerp_col(col, hd, head)
        return col, 0.88 + 0.05 * nz, occ

    def fold_p(self, S, T):
        L = 255.0
        X = (1 - S) * L
        tt = np.minimum(T, 1 - T) * 2
        H = 58 * (1 - 0.7 * soft(X, 140, 255))
        Yv = tt * H
        nz = self.n(X + 50, Yv + 50, 5.0)
        cov, _, occ = self.streaked(X, Yv, 8, 6, self.SAND, nz)
        # the wing panel: across the coverts a narrow black bar above a white bar, then the grey-brown greater coverts
        b_black = (band(Yv, 15.5, 18.5, 0.8) + band(Yv, 23.0, 24.5, 0.6)) * (1 - soft(X, 110, 125))
        b_white = band(Yv, 19.0, 22.8, 0.8) * (1 - soft(X, 110, 125))
        col = lerp_col(cov, self.BLACK, b_black * 0.9)
        col = lerp_col(col, self.WHITE, b_white * 0.9)
        gc = C(0.58, 0.52, 0.44)[None, None, :] * (1 + 0.04 * nz[..., None])
        col = lerp_col(col, gc, band(Yv, 26, 40, 2.0) * (1 - soft(X, 110, 125)) * 0.8)
        # the primaries over the tail: black with a small white spot
        prim = self.BLACK[None, None, :] * (1 + 0.1 * nz[..., None])
        prim = lerp_col(prim, self.WHITE, band(X, 150, 160, 3) * band(Yv, 3, 9, 2) * 0.7)
        col = lerp_col(col, prim, soft(X, 130, 150))
        return col, 0.86 + 0.05 * nz, occ

    def open_p(self, S, T):
        Y, c, Xc, upper = open_coords(self.spec, S, T)
        nz = self.n(Y + 20, Xc + 20, 6.0)
        hand = soft(Y, 165, 190)
        rem = soft(c, 0.42 - 0.1 * hand, 0.54 - 0.1 * hand)
        cov, _, _ = self.streaked(Y, Xc, 9, 7, self.SAND, nz)
        cov = lerp_col(cov, self.WHITE, band(c, 0.20, 0.28, 0.03) * (1 - hand) * 0.85)
        cov = lerp_col(cov, self.BLACK, band(c, 0.15, 0.19, 0.02) * (1 - hand) * 0.85)
        fl = np.broadcast_to(self.BLACK, Y.shape + (3,)).copy()
        fl = lerp_col(fl, self.WHITE, band(Y, 250, 320, 12) * band(c, 0.35, 0.6, 0.06) * 0.9)
        up = lerp_col(cov, fl, rem)
        dn = np.broadcast_to(self.WHITE, Y.shape + (3,)).copy()
        dn = lerp_col(dn, self.BLACK, np.maximum(soft(c, 0.82, 0.92), soft(Y, 320, 390)) * 0.9)
        col = np.where(upper[..., None], up, dn)
        return col, 0.86 + 0.05 * nz, np.ones_like(S)

    def tail_p(self, S, T):
        X = S * 134.0
        top = T < 0.5
        nz = self.n(X + 9, T * 60 + 9, 5.0)
        col = self.SAND[None, None, :] * (1 + 0.04 * nz[..., None])
        col = lerp_col(col, self.STREAK, (np.abs(((X / 11.0) % 1.0) - 0.5) < 0.08) * 0.5)
        col = lerp_col(col, self.WHITE, band(X, 108, 120, 2) * 0.8)
        col = lerp_col(col, self.BLACK, soft(X, 121, 125))
        col = np.where(top[..., None], col, lerp_col(col, self.WHITE, 0.4))
        return col, 0.87 * np.ones_like(S), np.ones_like(S)

    def thigh_p(self, S, T):
        col = np.broadcast_to(self.BUFF, S.shape + (3,)).copy() * (1 + 0.03 * self.n(S * 90, T * 60, 3.0))[..., None]
        col = lerp_col(col, self.LEG, soft(S, 0.5, 0.6))
        return col, 0.85 - 0.3 * soft(S, 0.5, 0.6), np.ones_like(S)

    def horn_p(self, S, T):
        col = lerp_col(np.broadcast_to(self.YELLOW, S.shape + (3,)), self.BLACK, soft(S, 0.45, 0.6))
        return col, 0.4 * np.ones_like(S), np.ones_like(S)

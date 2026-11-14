"""The atlases and their painting, by species. Every colour is painted here with numpy from the descriptions in
README.md (the plumage's marks, where they are and what they come from); no picture is read.

Colours are sRGB values (as Blender stores an 8-bit image). Each block is painted in its own coordinates: for the
body, the distance along the body (mm) and the place round it (mm from the back's middle line).
"""
import math

import numpy as np

from common import Atlas, C, Noise, feathers, hash01, lerp_col, seg_dist

BLOCKS_BIRD = {
    'body': (0.0, 0.5, 1.0, 1.0),
    'wing_open': (0.0, 0.25, 0.5, 0.5),
    'wing_fold': (0.5, 0.25, 1.0, 0.5),
    'tail': (0.0, 0.0, 0.25, 0.25),
    'thigh': (0.25, 0.125, 0.375, 0.25),
    'skin': (0.25, 0.0, 0.375, 0.125),
    'horn': (0.375, 0.0, 0.5, 0.125),
    'claw': (0.375, 0.125, 0.5, 0.25),
    'eye': (0.5, 0.125, 0.625, 0.25),
    'hood': (0.625, 0.125, 0.875, 0.25),
    'hood_knot': (0.875, 0.125, 1.0, 0.25),
    'cord': (0.5, 0.0, 0.75, 0.125),
    'steel': (0.75, 0.0, 0.875, 0.125),
    'crest': (0.875, 0.0, 1.0, 0.125),
}


def atlas(name):
    return Atlas(dict(BLOCKS_BIRD))


def paint(name, at, size, body):
    if name == 'saker':
        p = SakerPaint(body, size)
    else:
        import paint_quarry
        p = paint_quarry.painter(name, body, size)
    return at.paint(size, p.painters())


# ------------------------------------------------------------------ shared helpers
def body_coords(body, S, T):
    """Body block coordinates to millimetres: d along the body, y round it from the back's middle line (both sides
    alike), the section's half perimeter at d, and tt (0 the back, 0.5 the belly)."""
    s = np.array(body.s)
    d = np.array(body.d)
    D = np.interp(S, s, d)
    rows = np.array(body.rows)
    au = np.interp(D, rows[:, 0], rows[:, 1])
    ad = np.interp(D, rows[:, 0], rows[:, 2])
    b = np.interp(D, rows[:, 0], rows[:, 3])
    # quarter perimeters of the two half ellipses (Ramanujan)
    def quarter(a, bb):
        h = ((a - bb) / (a + bb)) ** 2
        return math.pi * (a + bb) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h))) / 4
    qu, qd = quarter(au, b), quarter(ad, b)
    tt = np.minimum(T, 1 - T)          # 0 the back's middle, 0.25 the side, 0.5 the belly
    th = tt * 2 * np.pi
    # the distance round from the back: the upper quarter then the lower
    Y = np.where(th <= np.pi / 2, qu * th / (np.pi / 2), qu + qd * (th - np.pi / 2) / (np.pi / 2))
    return D, Y, qu + qd, tt, au, ad, b


def eye_place(body, spec_eye):
    """The eye's place on the body block: (d, y round from the back's middle line)."""
    d = spec_eye['d']
    au, ad, b = body.size_at(d)
    th = math.acos(max(min(spec_eye['up'] / au, 1.0), -1.0))
    h = ((au - b) / (au + b)) ** 2
    qu = math.pi * (au + b) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h))) / 4
    return d, qu * th / (math.pi / 2)


def soft(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def band(x, a, b, w):
    """1 inside a..b, easing out over w."""
    return soft(x, a - w, a) * (1 - soft(x, b, b + w))


def streaks(X, Y, sx, sy, length, width, seed, density=1.0, tilt=12.0):
    """Dark tear-drop streaks in staggered rows (X toward the tail, Y across, mm): each about [length] long and
    widest ([width]) toward its rear end, each one's length, width, place and slant ([tilt] degrees) varied at
    random so they read as feathers, not a grid. [density] 0..1 drops some. Returns 0..1 (1 inside a streak)."""
    out = np.zeros_like(X)
    for pas, shift in ((0, 0.0), (1, 0.5)):       # two offset layers: neighbours overlap like real feathers
        Xs = X + shift * sx
        row = np.floor(Xs / sx)
        off = (row % 2) * 0.5 * sy + hash01(row, 17.0 + pas) * sy
        col = np.floor((Y + off) / sy)
        idx = (row * 7919 + col * 104729 + seed * 31 + pas * 17) % 9973
        jx = (hash01(idx, 3.0) - 0.5) * 0.5 * sx
        jy = (hash01(idx, 5.0) - 0.5) * 0.45 * sy
        keep = hash01(idx, 7.0) < density * (0.75 if pas else 1.0)
        L = length * (0.65 + 0.7 * hash01(idx, 11.0))
        ang = np.radians((hash01(idx, 13.0) - 0.5) * 2 * tilt)
        lx0 = Xs - (row + 0.5) * sx - jx
        ly0 = Y + off - (col + 0.5) * sy - jy
        lx = lx0 * np.cos(ang) + ly0 * np.sin(ang)
        ly = -lx0 * np.sin(ang) + ly0 * np.cos(ang)
        a = np.clip(lx / L + 0.5, 0, 1)
        hw = width * 0.5 * np.sin(np.pi * a ** 0.6) * (0.65 + 0.7 * hash01(idx, 9.0))
        inside = (np.abs(lx) < L / 2) & keep
        out = np.maximum(out, np.clip((hw - np.abs(ly)) / 0.8, 0, 1) * inside)
    return out


def plumage(X, Y, w, l, base, fringe, centre, streak_w, fringe_w, noise, shade=0.16, drop=False, sides=0.9, dark=0.0):
    """Feathers in rows (X toward their tips, Y across, mm): a body colour, a paler or darker fringe at the edge and
    tip, a centre (shaft streak or drop) of [streak_w] (fraction of the half width; 0 none). Returns rgb and the
    feather's 'along' (for occlusion: darker at its base, where the next row overlaps it)."""
    al, ac, idx = feathers(X, Y, w, l)
    r = hash01(idx, 1.0)
    col = base[None, None, :] * (0.94 + 0.12 * r[..., None])
    if streak_w:
        if drop:      # a tear-drop: narrow at the base, widest near the tip
            sw = streak_w * (0.25 + 0.95 * np.clip(al, 0, 1)) * (1 - soft(al, 0.80, 0.95))
        else:
            sw = streak_w * np.ones_like(al)
        m = (np.abs(ac) < sw) & (al > 0.08)
        edge = np.clip((sw - np.abs(ac)) / 0.08, 0, 1) * m
        col = lerp_col(col, centre[None, None, :] * (0.9 + 0.2 * r[..., None]), edge * 0.95)
    if dark:      # a darker centre (the coverts' and scapulars' dark middles)
        cm = (1 - soft(np.abs(ac), 0.35, 0.75)) * soft(al, 0.15, 0.4) * (1 - soft(al, 0.75, 0.92))
        col = col * (1 - dark * cm[..., None])
    if fringe_w:
        f = np.maximum(soft(al, 1 - fringe_w, 1.0), sides * soft(np.abs(ac), 1 - fringe_w * 0.9, 1.0) * soft(al, 0.3, 0.6))
        col = lerp_col(col, fringe[None, None, :], f * 0.9)
    occ = 1 - shade * (1 - np.clip(al, 0, 1)) ** 2
    col = col * occ[..., None] * (1 + noise[..., None] * 0.05)
    return col, al, occ


# ------------------------------------------------------------------ the saker (a first-year female)
class SakerPaint:
    # Juvenile (فرخ) saker colours; see README.md for the sources of each mark.
    BROWN = C(0.29, 0.20, 0.145)         # a young bird's upperparts: dark brown
    FRINGE = C(0.60, 0.48, 0.36)         # their narrow pale buff edges
    CREAM = C(0.87, 0.80, 0.69)          # underparts' ground, buff-cream
    STREAK = C(0.26, 0.18, 0.13)         # the heavy dark-brown streaks of a young bird's underparts
    CROWN = C(0.66, 0.54, 0.41)          # a young bird's buff-brown crown, heavily streaked
    FACE = C(0.86, 0.79, 0.67)           # cheeks and throat, buff
    PRIM = C(0.25, 0.19, 0.15)           # the primaries, darker than the coverts
    SKIN = C(0.60, 0.64, 0.66)           # a young bird's cere, eye ring and feet: bluish grey
    HORN = C(0.56, 0.61, 0.67)           # the beak's base: bluish horn
    HORN_TIP = C(0.11, 0.11, 0.13)
    CLAW = C(0.05, 0.05, 0.055)
    IRIS = C(0.13, 0.075, 0.045)         # a falcon's dark brown iris

    def __init__(self, body, size):
        self.body = body
        self.size = size
        self.n = Noise(11)
        import saker
        self.spec = saker.SPEC

    def painters(self):
        return {'body': self.body_p, 'wing_fold': self.fold_p, 'wing_open': self.open_p, 'tail': self.tail_p,
                'thigh': self.thigh_p, 'skin': self.skin_p, 'horn': self.horn_p, 'claw': self.claw_p,
                'eye': self.eye_p, 'hood': hood_p, 'hood_knot': knot_p, 'cord': cord_p, 'steel': steel_p}

    def body_p(self, S, T):
        D, Y, P, tt, au, ad, b = body_coords(self.body, S, T)
        nz = self.n(D + 300, Y + 300, 6.0) + 0.5 * self.n(D + 300, Y + 300, 2.0)
        head = soft(D, 212, 232)                    # the head from the nape on
        belly = soft(tt, 0.17, 0.27)                # the underside from the flanks down
        # the back and mantle: plain dark brown feathers with narrow pale buff edges (a young bird; an adult's are
        # paler and barred rufous), larger toward the scapulars and smaller toward the head
        fw = 12 - 7 * head
        fl = 9 - 5.4 * head
        back, al_b, occ_b = plumage(-D, Y, fw, fl, self.BROWN, self.FRINGE, self.STREAK, 0.0, 0.07, nz, shade=0.10, sides=0.4)
        # the underparts: buff-cream with the heavy, long dark streaks of a young bird, broadest and merging on the
        # flanks, narrower up the breast, thin on the throat, few under the tail
        under_w = 8.0 - 4.0 * soft(D, 150, 215)
        under, al_u, occ_u = plumage(-D, Y, under_w, under_w * 0.72, self.CREAM, self.CREAM * 1.02, self.STREAK,
                                     0.0, 0.0, nz, shade=0.06)
        flank = soft(tt, 0.19, 0.27) * (1 - soft(tt, 0.38, 0.47))
        dens = np.clip(1.0 - 0.35 * soft(D, 170, 215) - 0.9 * (1 - soft(D, 20, 55)), 0, 1)
        sl = 26.0 - 10.0 * soft(D, 140, 205)
        sw = 5.2 + 3.5 * flank - 2.6 * soft(D, 150, 205)
        st = streaks(-D, Y, sl * 0.9, 9.0 - 2.0 * soft(D, 140, 205), sl, sw, 1, density=1.0) * np.clip(dens * 1.2, 0, 1)
        under = lerp_col(under, self.STREAK[None, None, :] * (1 + 0.1 * nz[..., None]), st * 0.95)
        col = lerp_col(back, under, belly)
        occ = occ_b * (1 - belly) + occ_u * belly
        # the head: a buff-brown crown densely streaked dark; buff cheeks finely streaked; the throat buff with thin
        # streaks; a dark streak behind the eye, a faint pale brow line, and a thin moustache (weaker than a
        # peregrine's)
        ed, ey = eye_place(self.body, self.spec['eye'])
        crown_c, _, _ = plumage(-D, Y, 4.0, 3.0, self.CROWN, self.CROWN, self.STREAK, 0.0, 0.0, nz, shade=0.06)
        cs = streaks(-D, Y, 6.0, 3.6, 6.0, 1.9, 5, density=0.95, tilt=8)
        crown_c = lerp_col(crown_c, self.STREAK, cs * 0.9)
        face = self.FACE[None, None, :] * (1 + 0.04 * nz[..., None])
        fs = streaks(-D, Y, 5.0, 4.0, 4.5, 1.2, 9, density=0.7, tilt=10)
        face = lerp_col(face, self.STREAK * 1.2, fs * 0.55 * (1 - soft(tt, 0.36, 0.44)))
        hc = lerp_col(crown_c, face, soft(Y, ey - 3, ey + 10))
        # the nape: dark brown, its feathers pale-edged
        hc = lerp_col(hc, back, (1 - soft(D, 228, 246)) * (1 - soft(Y, 6, 28)) * 0.85)
        stripe, _ = seg_dist(D, Y, (ed - 6, ey), (ed - 34, ey + 1.5))
        hc = lerp_col(hc, self.STREAK[None, None, :] * 1.05, np.clip(1 - (stripe - 2.6) / 2.0, 0, 1) * 0.9)
        mous, f = seg_dist(D, Y, (ed + 3, ey + 7), (ed - 7, ey + 21))
        hc = lerp_col(hc, self.STREAK[None, None, :] * 1.1, np.clip(1 - (mous - 1.2) / 1.6, 0, 1) * (0.8 - 0.4 * f))
        sup, _ = seg_dist(D, Y, (ed + 6, ey - 8.5), (ed - 26, ey - 8))
        hc = lerp_col(hc, self.FACE[None, None, :] * 1.04, np.clip(1 - (sup - 1.3) / 1.8, 0, 1) * 0.6)
        lore, _ = seg_dist(D, Y, (ed + 5, ey + 1), (ed + 16, ey + 3))
        hc = lerp_col(hc, self.STREAK[None, None, :] * 1.5, np.clip(1 - (lore - 1.0) / 2.5, 0, 1) * 0.35)
        col = lerp_col(col, hc, head)
        occ = occ * (1 - head) + head * (1 - 0.04 * (1 - soft(nz, -0.5, 0.5)))
        rough = 0.86 + 0.06 * nz
        return col, rough, occ

    def fold_p(self, S, T):
        """The folded wing's outside: S from the primaries' tips (0) to the wrist (1), T 0..0.5 its outer face top to
        bottom (the inner face, hidden, the same)."""
        L = 335.0
        X = (1 - S) * L                      # mm behind the wrist
        tt = np.minimum(T, 1 - T) * 2        # 0 the top edge, 1 the bottom edge
        H = 70 * (1 - 0.8 * soft(X, 160, 335))
        Yv = tt * H
        nz = self.n(X + 50, Yv + 50, 5.0)
        # coverts near the wrist: small, dark-centred, rufous-fringed; the greater coverts larger
        cov, _, occ1 = plumage(X, Yv, 9.0, 7.0, self.BROWN, self.FRINGE, self.BROWN, 0.0, 0.08, nz, shade=0.10, sides=0.4)
        gc, _, occ2 = plumage(X, Yv, 15.0, 14.0, self.BROWN * 1.02, self.FRINGE * 0.97, self.BROWN, 0.0, 0.07, nz, shade=0.10, sides=0.4)
        # the secondaries and tertials: long, brown, with a pale fringe at their tips
        sec, _, occ3 = plumage(X, Yv * 1.0, 16.0, 46.0, self.BROWN * 0.92, self.FRINGE * 0.95, self.BROWN, 0.0, 0.05, nz, shade=0.14)
        # the primaries over the rump and tail: darkest, long, their tips staggered with a thin pale edge
        prim = self.PRIM[None, None, :] * (1 + 0.05 * nz[..., None])
        fe = ((Yv + 0.15 * X) / 6.0) % 1.0
        prim = prim * (0.80 + 0.28 * soft(fe, 0.0, 0.85)[..., None])        # each primary darker at its overlapped edge
        prim = lerp_col(prim, self.FRINGE * 0.8, (fe > 0.93) * 0.5)
        tips = np.zeros_like(X)
        for k, xt in enumerate((335, 322, 306, 288, 268)):
            tips = np.maximum(tips, band(X, xt - 3.5, xt, 1.0) * soft(Yv, 0, 4) * (1 - soft(Yv, 4 + 3 * k, 10 + 3 * k)))
        prim = lerp_col(prim, self.FRINGE * 1.05, tips * 0.8)
        col = lerp_col(cov, gc, soft(X, 45, 70))
        col = lerp_col(col, sec, soft(X, 105, 130) * soft(tt, 0.35, 0.6))
        col = lerp_col(col, prim, soft(X, 150, 185))
        occ = np.where(X < 60, occ1, np.where(X < 120, occ2, occ3))
        occ = occ * (1 - 0.15 * soft(tt, 0.85, 1.0))
        return col, 0.85 + 0.05 * nz, occ

    def open_p(self, S, T):
        """The spread wing: S root (0) to tip (1); T round its section: 0 the leading edge, 0.25 the upper middle,
        0.5 the trailing edge, 0.75 the under middle."""
        rows = np.array(self.spec['open'])
        span = rows[:, 0]
        Y = span[0] + S * (span[-1] - span[0])        # mm out from the middle line
        th = T * 2 * np.pi
        cs = np.cos(th)
        c = np.where(cs >= 0, 0.32 * (1 - cs), 0.32 - 0.68 * cs)    # 0 the leading edge, 1 the trailing edge
        upper = T < 0.5
        chord = np.interp(Y, span, rows[:, 1] - rows[:, 2])
        Xc = c * chord                                 # mm behind the leading edge
        nz = self.n(Y + 20, Xc + 20, 6.0)
        hand = soft(Y, 200, 230)
        # the remiges: feathers along the chord, one every 12 mm of span on the arm, fanning on the hand
        fan = np.where(Y < 215, Y / 13.0, 215 / 13.0 + (Y - 215) / 38.0)
        fi = np.floor(fan)
        fx = fan - fi
        shaft = np.abs(fx - 0.5) < 0.05
        edge = np.abs(fx - 0.5) > 0.46
        rem_zone = np.where(upper, soft(c, 0.42 - 0.12 * hand, 0.55 - 0.12 * hand), soft(c, 0.50 - 0.34 * hand, 0.60 - 0.34 * hand))
        # upper side: dark brown coverts with rufous fringes; brown remiges, the primaries darker
        cov, _, occc = plumage(Y, Xc, 10.0, 8.0, self.BROWN, self.FRINGE, self.BROWN, 0.0, 0.16, nz)
        rem_u = lerp_col(self.BROWN * 0.92, self.PRIM, hand)[..., :] if False else None
        rem_u = (self.BROWN * 0.92)[None, None, :] * (1 - hand[..., None]) + self.PRIM[None, None, :] * hand[..., None]
        rem_u = rem_u * (1 - 0.12 * edge[..., None]) * (1 - 0.08 * shaft[..., None])
        # their inner webs: pale buff oval spots, seen faintly from above
        spots = (np.abs(((Xc / 16.0) % 1.0) - 0.5) < 0.22) & (fx < 0.42) & (fx > 0.12) & (c > 0.55)
        rem_u = lerp_col(rem_u, self.FRINGE * 0.9, spots * 0.35)
        up = lerp_col(cov, rem_u, rem_zone)
        # under side: the coverts dark brown and heavily marked (the saker's dark underwing), the remiges pale
        # grey-buff, barred, with dusky tips
        ucov, _, _ = plumage(Y, Xc, 9.0, 7.0, self.BROWN * 0.85, self.CREAM * 0.9, self.STREAK, 0.0, 0.08, nz, shade=0.06, sides=0.3)
        ucov = lerp_col(ucov, self.CREAM * 0.9, streaks(Y, Xc, 9.0, 8.0, 4.0, 2.4, 3, density=0.6) * 0.6)
        bars = np.abs(((Xc / 13.0 + fi * 0.37) % 1.0) - 0.5) < 0.17
        rem_d = C(0.86, 0.83, 0.77)[None, None, :] * (1 - 0.16 * bars[..., None]) * (1 - 0.08 * edge[..., None])
        tipdark = soft(c, 0.92, 0.99)
        rem_d = lerp_col(rem_d, C(0.42, 0.36, 0.31), tipdark * 0.6)
        dn = lerp_col(ucov, rem_d, rem_zone)
        col = np.where(upper[..., None], up, dn)
        occ = np.where(upper, occc * (1 - rem_zone) + rem_zone, 1.0)
        return col, 0.85 + 0.05 * nz, occ

    def tail_p(self, S, T):
        X = S * 225.0
        top = T < 0.5
        a = np.where(top, np.abs(T * 4 - 1), np.abs((T - 0.5) * 4 - 1))       # 0 the middle, 1 the edge
        Yw = a * 33
        nz = self.n(X + 9, Yw + 9, 5.0)
        # above: brown; the outer feathers with pale buff oval spots in bars (the central pair plainer); a pale tip
        base = self.BROWN * 1.08
        bars = np.abs(((X / 22.0) % 1.0) - 0.5) < 0.17
        feather = np.floor(Yw / 9.0)
        spot = bars & (((Yw / 9.0) % 1.0) > 0.25) & (((Yw / 9.0) % 1.0) < 0.75)
        up = base[None, None, :] * (1 + 0.05 * nz[..., None])
        up = lerp_col(up, self.FRINGE * 1.1, spot * (0.25 + 0.5 * soft(a, 0.25, 0.8)) * soft(X, 40, 60))
        shafts = (np.abs(((Yw / 9.0) % 1.0) - 0.5) < 0.04) & (feather < 4)
        up = up * (1 - 0.15 * shafts[..., None])
        tip = soft(X, 212, 218)
        up = lerp_col(up, C(0.86, 0.79, 0.67), tip)
        # below: paler, more evenly barred
        dn = C(0.78, 0.72, 0.62)[None, None, :] * (1 - 0.30 * bars[..., None] * soft(X, 40, 60)[..., None])
        dn = lerp_col(dn, C(0.9, 0.86, 0.78), tip)
        col = np.where(top[..., None], up, dn)
        return col, 0.85 + 0.04 * nz, np.ones_like(X)

    def thigh_p(self, S, T):
        # the 'trousers': long, loose cream feathers with heavy dark-brown streaks and spots, darker than the breast
        X = S * 90.0
        Y = np.minimum(T, 1 - T) * 2 * 50.0
        nz = self.n(X + 3, Y + 3, 4.0)
        col, al, occ = plumage(X, Y, 7.0, 6.0, self.CREAM, self.CREAM, self.STREAK, 0.0, 0.0, nz, shade=0.08)
        col = lerp_col(col, self.STREAK, streaks(X, Y, 15.0, 7.5, 16.0, 5.5, 4, density=1.0) * 0.95)
        return col, 0.88 + 0.04 * nz, occ

    def skin_p(self, S, T):
        # bare skin: small scales (the tarsus' net of scales, the toes' larger plates are drawn by the knuckles)
        X, Y = S * 70.0, T * 40.0
        nz = self.n(X + 1, Y + 1, 2.0)
        sc = np.abs(((X / 2.2 + 0.5 * np.floor(Y / 2.2)) % 1.0) - 0.5) + np.abs(((Y / 2.2) % 1.0) - 0.5)
        sc = soft(sc, 0.55, 0.75)
        col = self.SKIN[None, None, :] * (0.92 + 0.06 * nz[..., None]) * (1 - 0.16 * sc[..., None])
        return col, 0.55 + 0.1 * sc, np.ones_like(X)

    def horn_p(self, S, T):
        # bluish horn at the base darkening to a black-tipped hook
        nz = self.n(S * 30 + 2, T * 30 + 2, 3.0)
        t = soft(S, 0.35, 0.85)
        col = lerp_col(self.HORN[None, None, :] * (1 + 0.04 * nz[..., None]), self.HORN_TIP, t)
        return col, 0.42 - 0.05 * t, np.ones_like(S)

    def claw_p(self, S, T):
        return np.broadcast_to(self.CLAW, S.shape + (3,)).copy(), 0.35 * np.ones_like(S), np.ones_like(S)

    def eye_p(self, S, T):
        # S along the eye from its back (0) to the cornea's middle (1): the pupil at the front, the iris round it
        col = np.broadcast_to(self.IRIS, S.shape + (3,)).copy()
        col = lerp_col(col, C(0.02, 0.015, 0.012), soft(S, 0.88, 0.93))
        col = lerp_col(col, C(0.05, 0.035, 0.03), 1 - soft(S, 0.6, 0.7))
        return col, 0.06 * np.ones_like(S), np.ones_like(S)


# ------------------------------------------------------------------ the gear's blocks (on the falcon's atlas)
def hood_p(S, T):
    """The hood: natural tan leather, its seams and its edges in dark brown leather, fine stitches."""
    n = Noise(31)
    X, Y = S * 70.0, T * 160.0
    nz = n(X + 5, Y + 5, 3.0) + 0.4 * n(X + 5, Y + 5, 0.8)
    col = C(0.58, 0.40, 0.24)[None, None, :] * (1 + 0.07 * nz[..., None])
    tt = np.minimum(T, 1 - T)
    seam = np.abs(tt - 0.0) < 0.012
    col = lerp_col(col, C(0.24, 0.14, 0.08), seam * 1.0)
    edge = np.maximum(1 - soft(S, 0.04, 0.09), soft(S, 0.90, 0.95))
    lower = soft(tt, 0.38, 0.43)
    col = lerp_col(col, C(0.24, 0.14, 0.08), np.maximum(edge, lower))
    stitch = (np.abs(tt - 0.03) < 0.005) & (((S * 70) % 2.0) < 1.0)
    col = lerp_col(col, C(0.86, 0.80, 0.66), stitch * 0.9)
    return col, 0.62 + 0.05 * nz, np.ones_like(S)


def knot_p(S, T):
    col = np.broadcast_to(C(0.24, 0.14, 0.08), S.shape + (3,)).copy()
    return col, 0.6 * np.ones_like(S), np.ones_like(S)


def cord_p(S, T):
    """The jesses' braided cord: two colours plaited (a common choice; they come in many)."""
    ph = (S * 120 + T * 4) % 1.0
    a = C(0.70, 0.12, 0.10)
    b = C(0.88, 0.86, 0.80)
    col = lerp_col(np.broadcast_to(a, S.shape + (3,)), b, (ph > 0.5).astype(np.float32))
    groove = np.abs(((S * 240 + T * 8) % 1.0) - 0.5) < 0.1
    col = col * (1 - 0.25 * groove[..., None])
    return col, 0.75 * np.ones_like(S), np.ones_like(S)


def steel_p(S, T):
    return np.broadcast_to(C(0.55, 0.56, 0.58), S.shape + (3,)).copy(), 0.35 * np.ones_like(S), np.ones_like(S)

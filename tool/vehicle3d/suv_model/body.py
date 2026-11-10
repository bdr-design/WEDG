"""Step 1: the body shell, a quad loft of cross sections set by the photo outlines (outlines.py).
Each station across the length is a closed section: its height from the side outline, its half-width at each height
the softer of the front outline (the greenhouse's lean-in, the shoulders) and the top outline (the plan's rounded
corners), with rounded roof and sill edges. The result is one clean quad mesh, mirrored about the centre line."""
import bpy, bmesh, math, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outlines as O
from scipy import ndimage

# The top photo at TOP_K 1.026 is 1.980 m across its flares, the spec width; the body is built on the front photo's
# scale, which realframe.Y_SCALE (1.980 / 2.0125) takes to the spec. So top-photo widths go in at 1.026 / Y_SCALE.
import realframe as RF
TOP_TO_FRONT = 1.026 / RF.Y_SCALE

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

# The roof's crown across the car, measured on the front and rear photos: a parabola, 9 mm down at |y| 0.45 m
# (front photo 9.3, rear photo 9.6) and 13.4 mm at 0.55. It fades out down the windshield (real x +0.45 -> +1.05)
# and over the tail (-2.10 -> -2.30), where the photos show no roof.
CROWN_K = 0.0134 / 0.55 ** 2                  # per metre, real frame
CROWN_FADE = (0.45, 1.05, -2.10, -2.30)
_Z_TOP_SLOPE = (RF._ZR[-1] - RF._ZR[-2]) / (RF._ZP[-1] - RF._ZP[-2])      # real per photo height, up at the roof

def _step(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)

def crown(x, y):
    """How far the roof is below its centre line at half-width y, in the photo frame (x, y in the photo frame)."""
    xr = float(RF.x_real(x)); a, b, c, d = CROWN_FADE
    f = (1 - _step((xr - a) / (b - a))) * _step((xr - d) / (c - d))
    return f * CROWN_K / _Z_TOP_SLOPE * (np.asarray(y, dtype=float) * RF.Y_SCALE) ** 2

def section(x, n_side=64, n_top=10, n_bot=8, r_top=0.07, r_bot=0.05):
    zt, zb = float(O.side_top(x)), float(O.side_bottom(x))
    d = x - O.X_REAR; blk = d < TAIL_REACH
    xt = tail_profile()[-1][0]; near = blk and xt <= x < xt + TIP_REACH[0] + TIP_REACH[1]
    if blk and x < xt: zt = max(zt, TAIL_BLOCK_Z)      # the tail block (see below)
    if near: zt = tip_top(x)
    def top_at(y):
        """The roof's height at half-width y: the centre line less the crown; near the spoiler's tip, the tip's own
        top line slid forward with the plan, so the spoiler ends in the same thin edge right across."""
        if not near: return zt - float(crown(x, y))
        return tip_top(x - float(tail().pd(y)) * (1 - _step((x - xt - TIP_REACH[0]) / TIP_REACH[1]))) - float(crown(x, y))
    if zt - zb < 0.02: zt = zb + 0.02
    t = (1 - np.cos(np.linspace(0, math.pi, n_side))) / 2
    ze = zt                                    # the roof's height at its edge: the centre line less the crown there
    for _ in range(4):
        zs = zb + t * (ze - zb)
        # the AI views disagree on width: the top view is scaled to the front view's body width (1.97 m)
        plan = tail().half(d, zs) if blk else np.full_like(zs, O.top_half(x) * TOP_TO_FRONT)
        w = smin(O.front_half(zs), plan, 0.03)
        # round the roof and the sill edges
        rt = min(r_top, (ze - zb) / 3); rb = min(r_bot, (ze - zb) / 3)
        up = np.clip((zs - (ze - rt)) / rt, 0, 1); dn = np.clip(((zb + rb) - zs) / rb, 0, 1)
        w = w - rt * (1 - np.sqrt(np.clip(1 - up ** 2, 0, 1))) - rb * (1 - np.sqrt(np.clip(1 - dn ** 2, 0, 1)))
        w = np.maximum(w, 0.02)
        ze = max(top_at(w[-1]), zb + 0.02)
    zs = zb + t * (ze - zb)
    top = [(w[-1] * (1 - i / n_top), top_at(w[-1] * (1 - i / n_top))) for i in range(1, n_top)]
    half = [(0.0, zb)] + [(w[0] * (i / n_bot), zb) for i in range(1, n_bot)] + list(zip(w, zs)) + top + [(0.0, zt)]
    # the closed loop: up the left side, then down the right side (mirrored), without repeating the centre points
    loop = [(x, y, z) for y, z in half] + [(x, -y, z) for y, z in half[-2:0:-1]]
    return loop

# --- the tail -------------------------------------------------------------------------------------------------------
# A loft gives every station one top height, and the top line is smoothed over 2 cm. On its own that smears the back
# of the car: the shoulder on top of the bumper, the tailgate standing upright behind it and the lamps overhanging
# the gate came out as one slope (r8: the gate 20 to 40 mm too far back, the lamps 10 to 18 mm too far forward,
# tools/rearsil.py), and it filled the space under the roof spoiler. The rear is built another way.
#   Its shape. 04_top shows the tail lamps' rear edge as the bumper's own plan curve moved forward, by the same
# amount at every half-width from 0.48 to 0.80 (tools/toptail.py), and the rear glass's lower edge and the
# spoiler's edge as arcs. 04_top draws the greenhouse narrower than the other photos do (the glass's lower corners
# at 0.60 against 03_rear's 0.74); brought to the same width, both arcs are the bumper's plan within the reading
# (glass 20 mm ahead at |y| 0.5, spoiler about 30; the plan 19). So above the bumper the body is the bumper's plan
# curve slid forward by the side silhouette's depth at each height:
#       x = X_REAR + L(y, z) F + flat(pd(|y|))
# pd is the bumper's plan (how far ahead of the car's end the outline is at half-width y, outlines.top_tail_plan);
# L the tail's line in 01_left, read to a fraction of a pixel (outlines.tail_contour); flat and F are below.
# How far the bumper stands out is 01_left's (30 mm beyond the lamps, 46.5 beyond the gate). 04_top draws 82 mm;
# the silhouette is the direct view of it, so 04_top gives the shape in plan only.
#   How it is made. The last stations are a block standing proud of that surface (their sides use L less a margin,
# their tops stand above the line), and the surface is cut out of the block with one exact cut: the bumper's
# shoulder, the gate, the lamps' band, the ledge, the glass, the notch under the spoiler and the spoiler's edge.
#   Heights. 01_left draws the tail higher than 03_rear does, by 8 to 12 cm at the bumper's shoulder and by nothing
# at the window. Everything on the rear is placed at 03_rear's heights (fascia_rear), so the line's heights are
# brought to 03_rear's first, 01_left -> 03_rear: the shoulder's lower edge to the top of the bumper's dark rear
# face (0.63 at every width), its upper edge to the tailgate's lower shut line, the crease to the plate recess's top,
# the lamp's six level edges (fascia_rear.ZR uses the same pairs), the window's lower corner.
NOTCH_Z = (1.58, 1.8225, 1.827, 1.8536)        # 01_left rows: the glass fitted to the 2nd, the spoiler's underside from the 3rd to the tip
TAIL_Z = ((0.745, 0.630), (0.7767, 0.6970), (1.080, 1.058), (1.140, 1.1075), (1.158, 1.130), (1.185, 1.163),
          (1.2048, 1.185), (1.2725, 1.268), (1.320, 1.3116), (1.392, 1.392))
TAIL_LAMP = slice(3, 9)        # the pairs inside the lamp
TAIL_BLOCK_Z = 1.80            # the block's top, under the spoiler's tip
TAIL_SMOOTH = 0.003            # the photo's line is smoothed this much along its length, to take the pixel steps out,
TAIL_TOL = 0.00025             # and thinned to the fewest points within this of it
TAIL_PROUD = (0.003, 0.04)     # the block's sides: L less 3 mm, and the least L within 4 cm of height (its rows are coarse)
TAIL_FADE = (0.25, 0.30)       # game choice (the photos do not show where the bumper's step ends along the body side):
                               # F is 1 to where the plan is 0.25 m ahead of the car's end and 0 the greater of
                               # 0.30 m and 3 L further on
TAIL_EXIT = (0.40, 0.50, 0.002)   # between plan depths 0.40 and 0.50 the cut turns from the surface to the block's side
                               # and ends 2 mm outside it. Where the body is narrower than the plan there (above the
                               # lamps) a row ends on the body side before that, and no turn is needed.
TAIL_FLAT = (0.020, 0.0465, 0.0186, 0.058, 1.3116, 1.392)
                               # flat: the gate is flatter across its middle than the bumper is. At the plate
                               # recess's heights the silhouette is the gate beside the recess (|y| 0.5), and it is
                               # 3 to 6 mm ahead of the gate's middle, where the bumper's plan is 19 mm ahead. So a
                               # plan depth p loses 20 mm x tanh(p / 20 mm), 14.6 of the 18.6 mm at |y| 0.5 (in full
                               # once the slide reaches the gate's 46.5 mm). From plan depth 19 to 58 mm (|y| 0.50 to 0.65, where the lamps
                               # begin) it comes back: round the corner the plan is the bumper's own. Over the ledge
                               # above the lamps (z 1.3116 to 1.392) the flattening goes, and the glass and the
                               # spoiler have the plan whole.
TAIL_RECESS = (0.885, 1.062)   # At these heights the silhouette is not the gate's middle (the plate recess is there)
                               # but the gate beside it, 3 to 6 mm ahead; the middle's line is carried straight up.
TAIL_BETWEEN = (0.38, 0.46, 1.143, 1.2725)
                               # 03_rear shows the horizon's reflection unbroken across the gate between the lamps:
                               # the lamp's own step (6 mm, the silhouette at z 1.17 to 1.20) is not there. Inside
                               # |y| 0.38 the line runs straight between those two heights; it is the lamp's from 0.46.
TAIL_SPINE = 0.25              # behind the surface the block is this wide a side at least: a thinner fin breaks the end cap's rounding
TIP_REACH = (0.03, 0.15)       # the spoiler's top slides with the plan whole to 3 cm ahead of the tip, not at all 15 cm further on (a game choice)
TAIL_ROWS = (0.012, 0.06)      # the cutter has a row this close either side of each fold of the line, and rows no farther apart than
                               # 6 cm: smooth shading spreads a fold over the faces beside it, and a tall face showed as a band
TAIL_START = 0.0035            # the cutter's line starts this far behind the bumper's rear face
TAIL_DENSE = 0.32              # the block's stations are 5 mm apart this far from the car's end (see build)
TAIL_REACH = 1.3               # stations this far from the car's end are shaped by the tail

def tail_z(z):
    """A height on 01_left's tail as 03_rear has it. Below the shoulder the bumper's face moves down with it."""
    z = np.asarray(z, dtype=float); a = [p[0] for p in TAIL_Z]; b = [p[1] for p in TAIL_Z]
    return np.where(z < a[0], z + (b[0] - a[0]), np.where(z > a[-1], z, np.interp(z, a, b)))

def _thin(P, tol):
    """The fewest of the line's points that stay within tol of all of them (Ramer-Douglas-Peucker)."""
    keep = np.zeros(len(P), bool); keep[[0, -1]] = True; stack = [(0, len(P) - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2: continue
        a, t = P[i], P[j] - P[i]
        d = np.abs((P[i + 1:j, 0] - a[0]) * t[1] - (P[i + 1:j, 1] - a[1]) * t[0]) / max(float(np.hypot(*t)), 1e-12)
        k = int(np.argmax(d))
        if d[k] > tol: m = i + 1 + k; keep[m] = True; stack += [(i, m), (m, j)]
    return P[keep]

def _notch_fit():
    """The glass line (a quadratic), the spoiler's underside (a line) and the height where they meet."""
    z0, z1, z2, z3 = NOTCH_Z
    zg = np.arange(1.60, z1, 0.003); g = np.polyfit(zg, O.side_rear(zg), 2)
    zu = np.arange(z2, z3 + 1e-6, 0.003); u = np.polyfit(zu, O.side_rear(zu), 1)
    r = np.roots(np.polysub(g, np.concatenate(([0.0], u)))); zc = float([q.real for q in r if z1 - 0.02 < q.real < z2 + 0.02][0])
    return g, u, zc

def notch_corner(): return _notch_fit()[2]

_TAIL = None
def tail_profile():
    """The side-view line (x, z) of the whole rear face: from behind the bumper's top corner over its shoulder, up the
    tailgate and the lamp, over the ledge under the window, up the glass to the corner under the spoiler, and back
    to the spoiler's tip."""
    global _TAIL
    if _TAIL is not None: return _TAIL
    C = O.tail_contour(); s = np.r_[0, np.cumsum(np.hypot(*np.diff(C, axis=0).T))]; t = np.arange(0, s[-1], 0.001)
    C = np.c_[np.interp(t, s, C[:, 0]), np.interp(t, s, C[:, 1])]
    C = ndimage.gaussian_filter1d(C, TAIL_SMOOTH / 0.001, axis=0, mode='nearest')
    # the wiper stands 8 mm off the glass in the silhouette: the glass line is fitted above it (z 1.47 up) and carried
    # down to where the ledge under the window comes nearest it (between z 1.39 and 1.435)
    g, u, zc = _notch_fit(); zg = np.arange(1.47, NOTCH_Z[1], 0.003); g2 = np.polyfit(zg, O.side_rear(zg), 2)
    i0 = int(np.flatnonzero((C[:, 1] > TAIL_Z[0][0] - 0.01) & (C[:, 0] > O.X_REAR + 0.0005))[0])     # past the bumper's end cap
    w = np.flatnonzero((C[:, 1] > 1.39) & (C[:, 1] < 1.435)); gap = np.polyval(g2, C[w, 1]) - C[w, 0]
    i1 = int(w[np.argmin(np.abs(gap))]); zj = float(C[i1, 1]); gj = float(np.polyval(g2, zj) - C[i1, 0])
    low = C[i0:i1 + 1].copy(); low[:, 1] = tail_z(low[:, 1])
    wall = (low[:, 1] > 0.72) & (low[:, 1] < 0.88); r = (low[:, 1] > TAIL_RECESS[0]) & (low[:, 1] < TAIL_RECESS[1])
    xw = float(np.median(low[wall, 0])); low[r, 0] = np.minimum(low[r, 0], xw)
    zs = np.r_[np.arange(zj + 0.004, zc - 0.002, 0.004), zc]; k = np.array([_step((z - 1.56) / 0.04) for z in zs])
    xs = np.polyval(g2, zs) * (1 - k) + np.polyval(g, zs) * k - gj * (1 - np.array([_step((z - zj) / 0.03) for z in zs]))
    P = _thin(np.vstack([low, np.c_[xs, zs]]), TAIL_TOL); z3 = NOTCH_Z[3]
    # the line begins on the bumper's rear face; a cut begun there leaves a ribbon round the bumper as wide as the
    # line's first step in. So it is carried on down its own slope to TAIL_START behind the car, and enters the body.
    run = P[0] - P[1]; t = (O.X_REAR - TAIL_START - P[0][0]) / min(float(run[0]), -1e-5); P = np.vstack([P[0] + t * run, P])
    print(f'  tail line: {len(P) + 1} points from z {P[0][1]:.4f}, gate wall {1000 * (xw - O.X_REAR):.1f} mm in, ledge meets the glass '
          f'at z {zj:.4f} ({gj * 1000:+.2f} mm), corner under the spoiler z {zc:.4f} x {P[-1][0]:.4f}')
    _TAIL = [(float(x), float(z)) for x, z in P] + [(float(np.polyval(u, z3)), z3)]
    return _TAIL

class Tail:
    """The rear surface's functions of height and of plan depth."""
    def __init__(self):
        P = np.array(tail_profile()); self.zl, self.xl = P[:, 1], P[:, 0]
        # the plan: the top photo's outline to a fraction of a pixel near the car's end, its whole rows (top_half, as
        # the rest of the loft has it) from 0.2 to 0.3 m on
        dep = np.linspace(0, 1.6, 3201); yc, dc = O.top_tail_plan(); dc = dc + np.arange(len(dc)) * 1e-9
        wr = np.maximum.accumulate(O.top_half(O.X_REAR + dep)); t = np.clip((dep - 0.2) / 0.1, 0, 1); t = t * t * (3 - 2 * t)
        w = (np.interp(dep, dc, yc) * (1 - t) + wr * t) * TOP_TO_FRONT
        self.pw, self.pdep = np.maximum.accumulate(w) + np.arange(len(w)) * 1e-9, dep          # strictly rising, for the inverse
        zz = np.arange(self.zl[0] - 0.1, self.zl[-1] + 0.1, 0.002); Lz = self.L(zz); n = int(round(TAIL_PROUD[1] / 0.002))
        self._zs, self._Ls = zz, np.maximum(ndimage.minimum_filter1d(Lz, 2 * n + 1, mode='nearest') - TAIL_PROUD[0], 0.0)
        ya, yb, za, zb = TAIL_BETWEEN; self._La, self._Lb = float(self.L(za)), float(self.L(zb))
    def L(self, z):
        """How far ahead of the car's end the rear line is at height z; nothing below the bumper's corner."""
        z = np.asarray(z, dtype=float); return np.where(z < self.zl[0], 0.0, np.interp(z, self.zl, self.xl) - O.X_REAR)
    def Ly(self, y, z):
        """L at half-widths y: between the lamps the line runs straight past the lamp's step."""
        ya, yb, za, zb = TAIL_BETWEEN; L = float(self.L(z))
        if not za < z < zb: return np.full(np.shape(y), L)
        t = np.clip((np.abs(y) - ya) / (yb - ya), 0, 1); t = t * t * (3 - 2 * t)
        return L * t + max(L, self._La + (self._Lb - self._La) * (z - za) / (zb - za)) * (1 - t)
    def Ls(self, z): return np.interp(z, self._zs, self._Ls)
    def pd(self, y): return np.interp(np.abs(y), self.pw, self.pdep)
    def W(self, p): return np.interp(p, self.pdep, self.pw)
    @staticmethod
    def flat(p, L, z):
        """The plan depth p with the middle's crown taken out, for a slide of L at height z."""
        d0, L0, pa, pb, za, zb = TAIL_FLAT; t = np.clip((p - pa) / (pb - pa), 0, 1); u = np.clip((z - za) / (zb - za), 0, 1)
        return p - np.minimum(d0, d0 * L / L0) * (1 - u * u * (3 - 2 * u)) * np.tanh(p / d0) * (1 - t * t * (3 - 2 * t))
    @staticmethod
    def F(p, L):
        t = np.clip((p - TAIL_FADE[0]) / np.maximum(TAIL_FADE[1], 3 * L), 0.0, 1.0); return 1 - t * t * (3 - 2 * t)
    def half(self, d, zs):
        """The block's half-width at the station d ahead of the car's end, at heights zs: the plan depth p whose point
        the slide brings to this station (the first p with flat(p) + Ls F(p) >= d)."""
        p = np.linspace(0, 1.6, 801); Ls = self.Ls(zs)[:, None]
        G = self.flat(p[None, :], Ls, np.asarray(zs)[:, None]) + Ls * self.F(p[None, :], Ls); ok = G >= d
        i = np.where(ok.any(axis=1), ok.argmax(axis=1), len(p) - 1)
        j = np.maximum(i - 1, 0); r = np.arange(len(zs)); g0, g1 = G[r, j], G[r, i]
        t = np.where((i > 0) & (g1 > g0), (d - g0) / np.where(g1 > g0, g1 - g0, 1.0), 0.0)
        w = self.W(p[j] + np.clip(t, 0, 1) * (p[i] - p[j]))
        return np.where(Ls[:, 0] > 0, np.maximum(w, TAIL_SPINE), w)
_TOPB = None
def tip_top(x):
    """The spoiler's top line by its tip, from 01_left's contour: the loft's own top line is smoothed over 2 cm and
    ended 15 mm short of the tip. The contour's pixel steps are smoothed out (3 mm, from 4 to 12 mm ahead of the tip
    on), and from 3 to 9 cm ahead of the tip it hands over to the loft's line, which lies 2 mm lower."""
    global _TOPB
    xt, z3 = tail_profile()[-1]
    if _TOPB is None:
        C = O.tail_contour(0.66, 2.05); k = (C[:, 1] > z3 + 0.0005) & (C[:, 0] > xt - 0.001) & (C[:, 0] < xt + 0.13); o = np.argsort(C[k, 0])
        xs = np.arange(xt, xt + 0.12, 0.001); raw = np.interp(xs, np.r_[xt, C[k, 0][o]], np.r_[z3, np.maximum.accumulate(C[k, 1][o])])
        w = np.clip((xs - xt - 0.004) / 0.008, 0, 1); w = w * w * (3 - 2 * w)
        _TOPB = (xs, np.maximum.accumulate(raw * (1 - w) + ndimage.gaussian_filter1d(raw, 3, mode='nearest') * w))
    t = _step((x - xt - 0.03) / 0.06); return float(np.interp(x, *_TOPB)) * (1 - t) + float(O.side_top(x)) * t

_T = None
def tail():
    global _T
    if _T is None: _T = Tail()
    return _T

def _tail_row(T, xl, z, m=34):
    """One row of the cutter at height z: half-widths out from the centre line and the surface's x at each. The row
    is laid out along the plan depth p, as the block's sides are (y = the softer of the body's width at this height
    and the plan's at p), so it turns the same corner into the body side that they do."""
    fh = float(O.front_half(z)); L, Ls = float(T.L(z)), float(T.Ls(z)); pa, pb, out = TAIL_EXIT
    ye = fh + 0.8 * 0.03; pe = float(T.pd(ye)) if ye < T.pw[-1] - 1e-4 else 9.0     # where the corner has all but turned
    pm = min(pb, pe); pp = np.linspace(0, pm, 600); yy = smin(np.full_like(pp, fh), T.W(pp), 0.03) + pp * 1e-7
    y = yy[-1] * (1 - (1 - np.arange(m + 1) / m) ** 1.5); q = np.interp(y, yy, pp)
    g = np.clip((q - pa) / (pb - pa), 0, 1); g = g * g * (3 - 2 * g); Ly = T.Ly(y, z)
    x = O.X_REAR + (T.flat(q, Ly, z) + Ly * T.F(q, Ly)) * (1 - g) + (T.flat(q, Ls, z) + Ls * T.F(q, Ls) - out) * g + (xl - (O.X_REAR + L))
    if pe < pb:      # the row ends on the body side, a hair inside it: it leaves along the side, 2 mm out over 2 cm,
        y = np.r_[y, y[-1] + 0.002]; x = np.r_[x, x[-1] + 0.02]      # so the cut feathers out and leaves no step
    else: y = np.r_[y, y[-1] + 1e-4]; x = np.r_[x, x[-1]]
    return y, x

def cut_tail(ob, x_out=-2.75, y_out=1.15):
    T = tail(); P = tail_profile(); rows = []
    near, far = TAIL_ROWS
    for (x0, z0), (x1, z1) in zip(P[:-1], P[1:]):      # the line's own points, and rows beside each of them (TAIL_ROWS)
        h = math.hypot(x1 - x0, z1 - z0); ts = [0.0]
        if h > 3 * near: e = near / h; m = max(1, int(math.ceil((1 - 2 * e) * h / far))); ts += [e + (1 - 2 * e) * i / m for i in range(m + 1)]
        rows += [(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, None) for t in ts]
    # the spoiler's edge has the plan too: above the tip the cutter stands straight up, where the spoiler's top
    # (section's top_at) has come down to the tip's height at every width
    rows += [(*P[-1], None), (P[-1][0], P[-1][1] + 0.16, P[-1][1])]; V = []; ring = []
    for xl, z, zf in rows:
        y, x = _tail_row(T, xl, z if zf is None else zf); pts = [(x[-1], -y_out)] + [(x[j], -y[j]) for j in range(len(y) - 1, 0, -1)] + \
            [(x[j], y[j]) for j in range(len(y))] + [(x[-1], y_out)]
        ring.append([len(V) + j for j in range(len(pts))]); V += [(float(a), float(b), z) for a, b in pts]
    ny = len(ring[0])
    for z in (rows[-1][1], rows[0][1]): ring.append([len(V) + j for j in range(ny)]); V += [(x_out, y_out * (2 * j / (ny - 1) - 1), z) for j in range(ny)]
    n = len(ring); F = [[ring[i][j], ring[i][j + 1], ring[(i + 1) % n][j + 1], ring[(i + 1) % n][j]] for i in range(n) for j in range(ny - 1)]
    F += [[r[0] for r in ring], [r[-1] for r in ring][::-1]]
    me = bpy.data.meshes.new('tail'); me.from_pydata(V, [], F); me.update()
    c = bpy.data.objects.new('tail', me); bpy.context.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    bpy.context.view_layer.objects.active = ob
    mo = ob.modifiers.new('tail', 'BOOLEAN'); mo.operation = 'DIFFERENCE'; mo.object = c; mo.solver = 'EXACT'
    n0 = len(ob.data.polygons); bpy.ops.object.modifier_apply(modifier='tail'); bpy.data.objects.remove(c)
    ob.data.materials.clear()                    # the cut leaves an empty slot; the paint must be the body's first
    print(f'  tail: cutter {len(rows)} rows x {ny}, body faces {n0} -> {len(ob.data.polygons)}')

CAP_DOME = ((0.022, 0.0022), (0.022, 0.0012))  # rings set in from the cap's edge and how far each stands out; the middle 0.6 mm more
CAP_END = 0.004                                # the sections stop this far inside the car's ends; the caps' crowns reach them

SHARP = 40.0                                   # folds sharper than this stay crisp (see crisp)


def crisp(ob):
    """Mark the shell's hard folds once every recess is cut in it. The shell is shaded smooth, and without this the
    rim of a recess is shaded as a round shoulder that smears a few centimetres across the paint beside it."""
    ob.data.set_sharp_from_angle(angle=math.radians(SHARP))
    return sum(1 for e in ob.data.edges if e.use_edge_sharp)


def _dome(bm, f, sign):
    """Round a flat end cap out to the car's true end. A flat fan shades as one facet: the lean of the faces around it
    spreads to its middle and shows as a wedge in every reflection. Rings that rise let the lean fade as on a bumper."""
    for inset, rise in CAP_DOME:
        bmesh.ops.inset_region(bm, faces=[f], thickness=inset, use_even_offset=True)
        for v in f.verts: v.co.x += sign * rise
    c = bmesh.ops.poke(bm, faces=[f])['verts'][0]; c.co.x += sign * (CAP_END - sum(r for _, r in CAP_DOME))

def build(step=0.02):
    # Across the car's middle the rear surface stands square to the loft's axis, and the loft can only chord it from
    # one station to the next: at 2 cm that is up to 7 mm inside the surface, where the cut cannot reach. So the
    # block's stations are 5 mm apart (within 1 mm), as far forward as the rear line goes.
    a = O.X_REAR + CAP_END; xs = np.r_[np.arange(a, a + TAIL_DENSE, 0.005), np.arange(a + TAIL_DENSE, O.X_FRONT - CAP_END, step)]
    secs = [section(x) for x in xs]; n = len(secs[0])
    V = [p for s in secs for p in s]; F = []
    for i in range(len(secs) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n; F.append([a, b, b + n, a + n])
    # caps: one flat face each, rounded below
    k = (len(secs) - 1) * n; F.append(list(range(n))); F.append([k + j for j in range(n)])
    me = bpy.data.meshes.new('body'); me.from_pydata(V, [], F); me.update()
    ob = bpy.data.objects.new('body', me); bpy.context.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in [f for f in bm.faces if len(f.verts) == n]: _dome(bm, f, 1.0 if f.calc_center_median().x > 0 else -1.0)
    # the rear cap is the bumper's rear face: across the car it takes the plan's first millimetres (0.5 and 3.0 mm
    # ahead at |y| 0.10 and 0.20; from 4 mm on it is the block's side), which the dome's rings did not follow
    T = tail()
    for v in bm.verts:
        if v.co.x < O.X_REAR + CAP_END - 1e-6: v.co.x = O.X_REAR + min(float(T.pd(v.co.y)), CAP_END)
    bm.to_mesh(me); bm.free()
    cut_tail(ob)
    for p in ob.data.polygons: p.use_smooth = True
    return ob

if __name__ == '__main__':
    out = sys.argv[-1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = build()
    m = bpy.data.materials.new('paint'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1); b.inputs['Roughness'].default_value = 0.2; b.inputs['Coat Weight'].default_value = 1.0
    ob.data.materials.append(m)
    print('body faces', len(ob.data.polygons))
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'body.blend'))

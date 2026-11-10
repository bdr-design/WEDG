"""The rear: the tail lamps, the tailgate's shut line, the plate recess, the stop lamp under the spoiler, the wiper
and the bumper's parts.

Every outline is measured on 03_rear. The numbers are in the body's photo frame (y on the front photo's scale, +y the
car's left, z up); realframe maps them to the real car afterwards. 03_rear and 01_left do not agree in two places, and
one photo is followed in each:
  the tail lamp  01_left draws it 1 to 3 cm higher than 03_rear. The bands inside a real lamp are level, so the lamp
                 keeps 03_rear's heights all the way round the corner. 01_left only says how far forward each band
                 reaches; its heights are brought to 03_rear's by ZR.
  the bumper     01_left ends the red reflector and the matte corner panel farther back and 4.5 cm higher than
                 03_rear does. The bumper's parts follow 03_rear alone.
The surface itself (the bumper's shoulder, the gate, the lamps' band, the ledge) is body.py's tail; its heights are
brought to 03_rear's there, with the same pairs ZR uses for the lamp.
Below z 0.46 the body's rear is the bumper's under-curve, leaning 45 to 85 degrees, so the parts there are pushed
along the surface's own normal (mode 'surf') and meshed in close rows.
Depths behind the surface cannot be read off a photo: they are game choices, named here."""
import bpy, math, numpy as np
from mathutils import Vector
import surf
from surf import Surf, solid, cut, rrect, fillet, clip, ribbon, arc
import body as _B

LAMP_DEPTH, PLATE_DEPTH, REFL_DEPTH, PANEL_DEPTH = 0.030, 0.020, 0.012, 0.0025        # game choices

# --- the tail lamp --------------------------------------------------------------------------------------------------
# 03_rear (y, z): the housing's inner edge from its lower inner corner up to the tip, then its top edge
LAMP_INNER = [(0.5226, 1.1075), (0.5148, 1.12), (0.5031, 1.14), (0.4857, 1.16), (0.4721, 1.18), (0.4585, 1.20),
              (0.4450, 1.22), (0.4314, 1.24), (0.4217, 1.26), (0.4198, 1.27), (0.4160, 1.28), (0.4275, 1.291)]
LAMP_TOP = [(0.45, 1.300), (0.50, 1.3077), (0.60, 1.3116), (0.70, 1.3116), (0.85, 1.3096)]
# 01_left (x, its own z): the top edge going forward, then the forward edge down to the lower corner
LAMP_TOP_SIDE = [(-2.25, 1.314), (-2.20, 1.308), (-2.15, 1.302), (-2.12, 1.299), (-2.0993, 1.2931)]
LAMP_FWD = [(-2.0993, 1.26), (-2.114, 1.24), (-2.129, 1.22), (-2.167, 1.18), (-2.20, 1.155), (-2.213, 1.140)]
RED_Z = (1.185, 1.214, 1.268)          # the red lens: bottom, the line between its dark lower and lit upper band, top
RED_INNER = [(0.520, 1.185), (0.505, 1.19), (0.486, 1.20), (0.472, 1.22), (0.459, 1.24), (0.451, 1.25),
             (0.443, 1.26), (0.438, 1.268)]
RED_FWD = [(-2.108, 1.2725), (-2.108, 1.26), (-2.1258, 1.25), (-2.1346, 1.24), (-2.1434, 1.23), (-2.1493, 1.22),
           (-2.1669, 1.21), (-2.170, 1.2048)]                                           # 01_left, from the top down
CLEAR_INNER = [(0.541, 1.130), (0.527, 1.163)]                                          # the clear lens under the red
CLEAR_FWD = [(-2.19, 1.185), (-2.215, 1.158)]                                           # 01_left
CLEAR_GAP = (0.7493, 0.7746)           # the tailgate's shut line parts the clear lens
RIM_W, RIM_Z = 0.004, 1.143            # the chrome rim under the lamp; it climbs the forward edge to RIM_Z


def ZR(z):
    """A height read inside the tail lamp on 01_left, as 03_rear has it (the lamp's six level edges matched)."""
    a, b = zip(*_B.TAIL_Z[_B.TAIL_LAMP]); return float(np.interp(z, a, b))      # (1.140, 1.1075) ... (1.320, 1.3116)


# --- the tailgate ---------------------------------------------------------------------------------------------------
# The shut line's centre, from the window's lower corner down; then a corner of radius GATE_R into a level gap at GATE_Z
GATE_LINE = [(0.745, 1.392), (0.752, 1.37), (0.756, 1.35), (0.758, 1.33), (0.764, 1.29), (0.764, 1.15), (0.763, 1.00),
             (0.759, 0.90), (0.751, 0.80)]
GATE_Y, GATE_R, GATE_Z = 0.7465, 0.045, 0.7015
GATE_W = (0.006, 0.009)                # the line's width up the sides and across the bottom
# The plate recess: its left edge from the top corner down (the right one mirrors it); the floor leans, 4 mm in at the
# bottom and PLATE_DEPTH in from PLATE_RAMP[1] up
PLATE_SIDE = [(0.501, 1.062), (0.504, 1.03), (0.502, 1.00), (0.4925, 0.95), (0.476, 0.90), (0.4547, 0.87),
              (0.4285, 0.85), (0.38, 0.838), (0.30, 0.836)]
PLATE_RAMP = (0.836, 1.04)
GATE_STRIP = (0.503, 0.758, 1.0558, 1.0583)     # a thin bright line (2.4 mm) from the recess's top corner to the shut line
STOP = [(-0.177, 1.8327), (0.177, 1.8327), (0.192, 1.8483), (-0.192, 1.8483)]    # the stop lamp under the spoiler
# The wiper, parked across the glass on the car's right: its lower edge outward, then its upper edge back
WIPER = [(0.018, 1.409), (0.0, 1.4088), (-0.05, 1.4107), (-0.1, 1.4127), (-0.2, 1.4185), (-0.3, 1.4244),
         (-0.4, 1.4282), (-0.455, 1.4282), (-0.455, 1.4399), (-0.4, 1.4438), (-0.3, 1.4458), (-0.2, 1.4516),
         (-0.1, 1.4496), (-0.05, 1.4477), (0.0, 1.4458), (0.018, 1.445)]
WIPER_OFF, WIPER_T = 0.004, 0.012      # game choices: its gap to the glass and its thickness

# --- the bumper (03_rear alone) -------------------------------------------------------------------------------------
REFLECTOR = [(0.632, 0.5766), (0.895, 0.5766), (0.915, 0.5425), (0.665, 0.5425)]
REFL_POCKET = [(0.612, 0.586), (0.905, 0.586), (0.925, 0.535), (0.652, 0.535)]
REFL_LINE = [(0.925, 0.532), (0.655, 0.532), (0.610, 0.585)]       # the chrome line under it and up its inner end
# The line between the middle of the bumper and the matte corner panel, y by z (z 0.48 and 0.46 are interpolated:
# the chrome strip's tip hides the line there)
DIAG = [(0.5365, 0.566), (0.5458, 0.56), (0.5613, 0.55), (0.5729, 0.54), (0.5942, 0.52), (0.6117, 0.50),
        (0.6259, 0.48), (0.6401, 0.46), (0.6543, 0.44), (0.6718, 0.42), (0.6873, 0.40), (0.6989, 0.385)]
PANEL_TOP = [(0.927, 0.530), (0.652, 0.530), (0.606, 0.589), (0.546, 0.563)]    # the corner panel's top, going inward
PANEL_OUT = [(0.900, 0.385), (0.920, 0.410), (0.927, 0.440)]                    # its lower outer corner, going up
BAND_Z = (0.4997, 0.566)               # the satin grey band across the middle
# The chrome strip under the band: upper and lower edge from the centre out to its tip
STRIP_UP = [(0.0, 0.4890), (0.14, 0.4890), (0.17, 0.4929), (0.50, 0.4929), (0.56, 0.4910), (0.58, 0.4890),
            (0.60, 0.4832), (0.62, 0.4696)]
STRIP_LOW = [(0.0, 0.4754), (0.14, 0.4754), (0.17, 0.4852), (0.50, 0.4852), (0.56, 0.4813), (0.58, 0.4774),
             (0.60, 0.4696), (0.62, 0.4560)]
# At its ends the strip turns down the diagonal and runs to the bumper's foot, dimmer as it goes: its outer and inner
# edge from the joint down (the outer edge is the diagonal itself below z 0.44)
ARM_OUT = [(0.62, 0.4696), (0.633, 0.46), (0.6447, 0.45), (0.6543, 0.44), (0.6718, 0.42), (0.6873, 0.40), (0.6989, 0.385)]
ARM_IN = [(0.62, 0.4560), (0.6233, 0.45), (0.632, 0.44), (0.640, 0.43), (0.649, 0.42), (0.657, 0.41), (0.666, 0.40),
          (0.674, 0.39), (0.678, 0.385)]
# Game choices. The strip stands STRIP_PROUD off the paint. The under-curve it sits on leans 30 to 45 degrees, and a
# face lying on it would mirror the ground; the photo's strip is bright, so its face is stood upright (STRIP_UPRIGHT:
# 1 is plumb, 0 lies on the surface). Between |y| STRIP_EASE it eases back onto the surface, to meet the arm, which
# lies on the under-curve and which the photo shows dimming downward.
STRIP_PROUD, STRIP_UPRIGHT, STRIP_EASE, PLATE_PROUD = 0.0055, 1.0, (0.56, 0.62), 0.004
# The two dark recesses in the silver plate under the strip (the plate reaches down to the diagonal's foot)
SKID_HOLE = [(0.22, 0.4336), (0.40, 0.4336), (0.4508, 0.42), (0.507, 0.41), (0.5419, 0.40), (0.5438, 0.395),
             (0.5438, 0.391), (0.1735, 0.391), (0.1735, 0.395), (0.1813, 0.40), (0.2007, 0.41), (0.2104, 0.42)]
SENSORS = [((0.7535, 0.500), 0.012), ((0.341, 0.603), 0.011)]      # centre and radius; the first is on the corner panel


def _mirror(half):
    """A chain from the centre line outward -> the whole chain from the right side to the left."""
    h = [tuple(p) for p in half]; return [(-y, z) for y, z in h[::-1] if y > 1e-9] + h


def _lamps(S, M, add, shell):
    """The tail lamp: a pocket cut in the shell, the red and clear lenses standing in it, a chrome rim, a clear cover."""
    F, Sd = S.F, lambda x, z: S.S(x, ZR(z))
    inner = [F(y, z) for y, z in LAMP_INNER]
    top = sorted([F(y, z) for y, z in LAMP_TOP] + [Sd(x, z) for x, z in LAMP_TOP_SIDE], key=lambda p: p[0])
    fwd = [Sd(x, z) for x, z in LAMP_FWD]
    pts = inner + top + fwd; r = [0.0] * len(pts)            # rounded: lower inner corner, tip, forward top and bottom
    r[0], r[len(inner) - 2], r[len(inner) + len(top) - 1], r[-1] = 0.008, 0.005, 0.008, 0.012
    lamp = fillet(np.array(pts), r, 4)
    cut(shell, [solid(S, 'c_tail', lamp, None, 0.04, -LAMP_DEPTH, sym=True, grid=0.05)], M['black_gloss'], 'tail_lamps')
    red = np.array([F(y, z) for y, z in RED_INNER] + [Sd(x, z) for x, z in RED_FWD])
    lens = dict(grid=None, seg=0.02, sym=True, cap=False, bevel=0.0015)
    add('tail_red_lit', clip(red, 1, RED_Z[1], None), M['tail'], -0.008, -LAMP_DEPTH - 0.002, **lens)
    add('tail_red', clip(red, 1, None, RED_Z[1]), M['red_lens'], -0.010, -LAMP_DEPTH - 0.002, **lens)
    clear = np.array([F(*CLEAR_INNER[0]), F(*CLEAR_INNER[1]), Sd(*CLEAR_FWD[0]), Sd(*CLEAR_FWD[1])])
    zc = (CLEAR_INNER[0][1] + CLEAR_INNER[1][1]) / 2; ua, ub = (F(y, zc)[0] for y in CLEAR_GAP)
    for i, piece in enumerate((clip(clear, 0, None, ua), clip(clear, 0, ub, None))):
        add(f'tail_clear{i}', piece, M['lens_chrome'], -0.008, -LAMP_DEPTH - 0.002, **lens)
    end = fwd[-2] + (fwd[-3] - fwd[-2]) * (RIM_Z - fwd[-2][1]) / (fwd[-3][1] - fwd[-2][1])
    chain = fillet(np.array([inner[1], inner[0], fwd[-1], fwd[-2], end]), [0, 0.008, 0.012, 0, 0], 4)
    add('tail_rim', ribbon(chain, RIM_W, RIM_W / 2), M['chrome'], 0.001, -0.004, grid=None, seg=0.02, sym=True, cap=False)
    add('tail_cover', lamp, M['lamp_cover'], -0.002, None, grid=0.04, sym=True)


def _gate(S, M, add, shell):
    """The tailgate: its shut line (a dark ribbon on the surface, like the doors'), the plate recess, the stop lamp."""
    half = [(0.0, GATE_Z), (0.35, GATE_Z)] + arc((GATE_Y - GATE_R, GATE_Z + GATE_R), GATE_R, -90, 0) + GATE_LINE[::-1]
    chain = _mirror(half)
    w = [GATE_W[1] + (GATE_W[0] - GATE_W[1]) * min(1.0, max(0.0, (z - GATE_Z) / GATE_R)) for _, z in chain]
    add('gate_line', S.Fpoly(ribbon(chain, w), 0.01), M['groove'], 0.0012, None, grid=None, seg=0.01)     # close rows: it crosses the ledge's folds
    side = PLATE_SIDE[::-1]; plate = fillet(np.array(_mirror(side)), [0.012] + [0.0] * (2 * len(side) - 2) + [0.012], 4)
    z0, z1 = PLATE_RAMP
    floor = lambda p, u, z: -(0.004 + (PLATE_DEPTH - 0.004) * min(1.0, max(0.0, (z - z0) / (z1 - z0))))
    cut(shell, [solid(S, 'c_plate', S.Fpoly(plate, 0.03), None, 0.04, floor, mode='x', grid=0.06, seg=0.03)],
        shell.data.materials[0], 'plate')
    add('gate_strip', S.Fpoly(rrect(*GATE_STRIP, 0.0015, 2), 0.01), M['chrome'], 0.0015, -0.002, grid=None, seg=0.01,
        sym=True, cap=False)
    add('stop_lamp', S.Fpoly(STOP, 0.03), M['red_lens'], 0.003, -0.003, mode='surf', grid=None, seg=0.03, cap=False,
        bevel=0.001)


def _wiper(M, parts):
    """The wiper, standing a little off the glass (one tapered blade and the cap over its pivot)."""
    G = Surf(bpy.data.objects['glass'], -1, z_ref=1.55)
    r = [0.0] * len(WIPER)
    for i in (0, 7, 8, 15): r[i] = 0.004
    parts.append(solid(G, 'wiper', G.Fpoly(fillet(np.array(WIPER), r, 3), 0.03), M['trim'], WIPER_OFF + WIPER_T,
                       WIPER_OFF, mode='surf', grid=None, seg=0.03, bevel=0.003))
    parts.append(solid(G, 'wiper_pivot', G.Fpoly(rrect(-0.035, 0.018, 1.406, 1.449, 0.008, 3), 0.03), M['trim'],
                       WIPER_OFF + WIPER_T + 0.008, 0.0, mode='surf', grid=None, seg=0.03, bevel=0.004))


def _low(S, poly, dy=0.03, dz=0.006):
    """An end-view outline low on the bumper -> (u, z), cut finely in height: the surface there leans far over, so a
    small step in height is a long step along it."""
    P = np.asarray(poly, float); out = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        k = max(1, int(math.ceil(max(abs(b[0] - a[0]) / dy, abs(b[1] - a[1]) / dz))))
        out += [S.F(*(a + (b - a) * j / k)) for j in range(k)]
    return np.array(out)


def _strip_face(S):
    """How far straight back the chrome strip's face stands at each point (mode 'x', so its outline in the end view
    stays as measured). Each point is set back to the body's x on the strip's upper edge above it, which stands the
    face upright; towards the joint with the arm that eases off (STRIP_EASE) and the face lies back on the surface."""
    yu, zu = zip(*STRIP_UP)
    def face(p, u, z):
        y = abs(p[1]); n = S.atn(u, z)[1]; base = STRIP_PROUD / max(0.5, abs(n.x) if n else 1.0)
        k = min(1.0, max(0.0, (STRIP_EASE[1] - y) / (STRIP_EASE[1] - STRIP_EASE[0]))); k = STRIP_UPRIGHT * k * k * (3 - 2 * k)
        if k <= 0.0: return base
        r = S.bvh.ray_cast(Vector((S.end * 6.0, p[1], float(np.interp(y, yu, zu)))), Vector((-S.end, 0, 0)))[0]
        return base + (k * max(0.0, S.end * (r.x - p[0])) if r else 0.0)
    return face


def _circle(c, r, n=14):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _bumper(S, M, add, shell):
    """The bumper: the reflector in its pocket, the matte corner panel, the grey band, the chrome strip, the skid plate."""
    F = S.Fpoly; low = dict(mode='surf', grid=(0.045, 0.006), seg=0.06)
    cut(shell, [solid(S, 'c_refl', F(fillet(np.array(REFL_POCKET), 0.004, 3), 0.01), None, 0.04, -REFL_DEPTH, sym=True,
                      grid=0.02, seg=0.01)], M['black_gloss'], 'reflectors')
    add('reflector', F(REFLECTOR, 0.03), M['red_lens'], -0.003, -REFL_DEPTH - 0.002, grid=None, seg=0.03, sym=True,
        cap=False, bevel=0.001)
    line = fillet(np.array(REFL_LINE), [0, 0.006, 0], 4)
    add('refl_line', F(ribbon(line, 0.0025), 0.03), M['chrome'], 0.001, -0.002, grid=None, seg=0.03, sym=True, cap=False)
    # the corner panel is a shallow step cut in the shell, floored in matte black: it follows the under-curve exactly
    panel = PANEL_TOP + DIAG[1:] + PANEL_OUT
    cut(shell, [solid(S, 'c_panel', _low(S, panel), None, 0.04, -PANEL_DEPTH, sym=True, **low),
                solid(S, 'c_skid', _low(S, SKID_HOLE), None, 0.04, -0.012, sym=True, **low)], M['trim'], 'bumper_panels')
    # the grey band: proud of the paint, its top 10 mm a bevel that catches the light
    zb0, zb1 = BAND_Z; dz, dy = zip(*[(z, y) for y, z in DIAG[::-1]]); yb = float(np.interp(zb0, dz, dy))
    right = [(yb, zb0)] + [(y, z) for y, z in DIAG[::-1] if z > zb0 + 0.001]
    band = right + [(-y, z) for y, z in right[::-1]]
    ridge = [S.F(y, zb1 - 0.010) for y in np.linspace(-0.53, 0.53, 28)]
    add('bumper_band', F(band, 0.04), M['gunmetal'], lambda p, u, z: 0.006 * min(1.0, max(0.0, (zb1 - z) / 0.010)),
        -0.002, mode='surf', grid=(0.05, 0.02), seg=0.04, cap=False, chains=[ridge])
    strip = _mirror(STRIP_UP) + _mirror(STRIP_LOW)[::-1]
    add('bumper_strip', _low(S, strip), M['chrome'], _strip_face(S), -0.002, mode='x', grid=(0.045, 0.006), seg=0.06,
        cap=False, bevel=0.002)
    # the arm lies on the under-curve (it leans 60 to 80 degrees there); its top end is lapped under the strip's end
    (ya, za), (yb, zb) = STRIP_UP[-2], STRIP_UP[-1]; (_, zc), (_, zd) = STRIP_LOW[-2], STRIP_LOW[-1]
    t = 0.6; lap = [(ya + (yb - ya) * t, za + (zb - za) * t), (ya + (yb - ya) * t, zc + (zd - zc) * t)]
    add('strip_arm', _low(S, lap[:1] + ARM_OUT + ARM_IN[::-1] + lap[1:]), M['chrome'], STRIP_PROUD, -0.002, sym=True,
        cap=False, bevel=0.002, **low)
    # the silver plate runs from under the strip down round the under-curve, open over the two recesses; its edge is
    # tucked 2 mm under the strip and 3 mm under the arm
    top = _mirror([(y, z + 0.002) for y, z in STRIP_LOW] + [(y + 0.003, z) for y, z in ARM_IN[1:]])
    add('skid_plate', _low(S, top), M['silver'], PLATE_PROUD, -0.002, cap=False, bevel=0.0015,
        hole=[_low(S, SKID_HOLE), _low(S, [(-y, z) for y, z in SKID_HOLE])], **low)
    (c1, r1), (c2, r2) = SENSORS
    add('sensor_panel', F(_circle(c1, r1), 0.01), M['black_gloss'], -0.001, -PANEL_DEPTH - 0.002, mode='surf',
        grid=None, seg=0.01, sym=True, cap=False)
    add('sensor_ring', F(_circle(c2, r2), 0.01), M['groove'], 0.0008, None, grid=None, seg=0.01, sym=True,
        hole=F(_circle(c2, r2 - 0.0015), 0.01))


def rear(shell, M):
    S = Surf(shell, -1); parts = []
    def add(*a, **k): parts.append(solid(S, *a, **k))
    _lamps(S, M, add, shell); _gate(S, M, add, shell); _bumper(S, M, add, shell); _wiper(M, parts)
    groups = {}
    for o in parts: groups.setdefault(o.data.materials[0].name, []).append(o)
    return [surf.join(g, 'rear_' + name) for name, g in groups.items()]

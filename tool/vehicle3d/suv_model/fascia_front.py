"""The front: grille, lamps and bumper details.

Every outline is measured on the owner's photos in the photo frame: (y, z) on the front photo, and (x, z) on the side
photo for what lies round the corner. Recesses are real cuts in the shell, so they have depth and walls; bars, lamps
and trims are parts with clean outlines standing in them (surf.py). Sizes with no photo to measure (how deep a recess
is, how thick a bar is) are game choices and are named so below."""
import numpy as np
from mathutils import Vector
import surf
from surf import Surf, solid, cut, rrect, fillet

# --- measured on the front photo (half widths and heights, metres) -------------------------------------------------
_YG = np.array([(0.652, 0.536), (0.70, 0.536), (1.00, 0.563), (1.085, 0.581), (1.186, 0.602)])   # grille edge: z, half width
BARS = ((1.143, 1.181), (1.002, 1.043), (0.875, 0.902), (0.756, 0.781), (0.656, 0.682))          # chrome bars: bottom, top
SLATS = (1.094, 0.945, 0.826, 0.722)                 # thin dark slats between the bars
STRUTS = (0.0, 0.148, 0.289, 0.436)                  # vertical struts behind the bars
LAMP_Z = (1.085, 1.191)                              # headlamp, bottom and top
LAMP_TAIL = ((2.034, 1.191), (2.118, 1.085))         # its rear end on the side photo: (x, z) top and bottom
PROJ_Y, PROJ_Z, PROJ_W, PROJ_H = (0.665, 0.758, 0.851), 1.126, 0.068, 0.053
BROW_Z = (1.168, 1.182)                              # the light strip along the lamp's top
DRL_Z = (1.005, 1.077)                               # the lit bar under the lamp
DRL_TAIL = ((2.124, 1.077), (2.140, 1.005))          # its rear end on the side photo
INTAKE = ((0.558, 0.693), (0.800, 0.745), (0.822, 1.000), (0.585, 1.000))    # side intake, counter-clockwise
INTAKE_FINS = (0.954, 0.892, 0.841, 0.784)
BRACKET = ((0.822, 1.000), (0.882, 1.000), (0.849, 0.710), (0.543, 0.665), (0.543, 0.692), (0.800, 0.745))
FOG_POCKET = ((0.933, 0.512), (0.752, 0.500), (0.745, 0.432), (0.925, 0.440))
FOG_LAMP = (0.843, 0.911, 0.459, 0.493)
LOWER = ((-0.547, 0.457), (0.547, 0.457), (0.50, 0.580), (-0.50, 0.580))     # lower intake
LOWER_FINS = (0.488, 0.519, 0.550)
PLATE = (-0.084, 0.084, 0.467, 0.548)                # the small holder in the lower intake
SKID = (-0.561, 0.561, 0.404, 0.438)                 # silver skid strip
# --- game choices: depths (no photo shows them) --------------------------------------------------------------------
GRILLE_DEPTH, POCKET_DEPTH, INTAKE_DEPTH, FOG_DEPTH = 0.065, 0.040, 0.050, 0.030
GRILLE_Z0, GRILLE_LEAN = 0.95, 0.02                  # below this height the grille stands this much per metre forward


def yg(z): return float(np.interp(z, _YG[:, 0], _YG[:, 1]))


def _grille_face(S):
    """x of the grille's face at (y, z). The hull is the car's outline, and under 0.95 m its nose is the bumper,
    which the side photo shows standing 5 cm ahead of the grille (bumper 2.495, bar fronts 2.43-2.44). So above
    0.95 m the grille's face is the hull, and below it carries on down almost upright instead of following the
    hull out to the bumper."""
    def hull(y, z):
        r = S.bvh.ray_cast(Vector((6.0, y, z)), Vector((-1.0, 0.0, 0.0)))[0]
        if r is None: raise ValueError(f'no hull at y {y:.3f}, z {z:.3f}')
        return r.x
    def G(y, z):
        h = hull(y, z)
        return h if z >= GRILLE_Z0 else min(h, hull(y, GRILLE_Z0) + GRILLE_LEAN * (GRILLE_Z0 - z))
    return G


def front(shell, M):
    S = Surf(shell, 1); G = _grille_face(S); parts = []
    def at(d): return lambda p, u, z: G(p.y, z) + d - p.x          # d metres ahead of the grille's face (mode 'x')
    def add(*a, **k): parts.append(solid(S, *a, **k))
    Y = np.array([1.0, 1.0])

    # ---- the recesses: real cuts in the shell -----------------------------------------------------------------
    right = [(yg(z), z) for z in _YG[:, 0]]; opening = np.array(right + [(-y, z) for y, z in right[::-1]])
    opening = fillet(opening, [0.02, 0, 0, 0, 0.008, 0.008, 0, 0, 0, 0.02])
    lower = fillet(np.array(LOWER), 0.015)
    cut(shell, [solid(S, 'c_grille', S.Fpoly(opening), None, 0.04, at(-GRILLE_DEPTH), mode='x', grid=0.05),
                solid(S, 'c_lower', S.Fpoly(lower), None, 0.04, -INTAKE_DEPTH, mode='x', grid=0.05)], M['grille'], 'grille')
    intake = S.Fpoly(fillet(np.array(INTAKE), 0.008))
    fog = S.Fpoly(fillet(np.array(FOG_POCKET), 0.010))
    cut(shell, [solid(S, 'c_intake', intake, None, 0.04, -INTAKE_DEPTH, mode='x', sym=True, grid=0.05),
                solid(S, 'c_fog', fog, None, 0.04, -FOG_DEPTH, sym=True, grid=0.05)], M['trim'], 'intakes')
    # the headlamp runs round the corner onto the flank: its front end from the front photo, its tail from the side photo
    z0, z1 = LAMP_Z; (xt, zt), (xb, zb) = LAMP_TAIL
    uT, uB = S.S(xt, zt)[0], S.S(xb, zb)[0]
    tail = lambda z: uT + (uB - uT) * (zt - z) / (zt - zb)          # the lamp's rear edge: u at height z
    lamp = fillet(np.array([S.F(yg(z0) + 0.010, z0), (uB, zb), (uT, zt), S.F(yg(z1) + 0.010, z1)]), [0.012, 0.012, 0.006, 0.012])
    cut(shell, [solid(S, 'c_lamp', lamp, None, 0.04, -POCKET_DEPTH, sym=True, grid=0.05)], M['black_gloss'], 'lamps')

    # ---- the grille ----------------------------------------------------------------------------------------------
    for i, (b0, b1) in enumerate(BARS):                            # chrome bars with a ridge along the middle
        zc, h = (b0 + b1) / 2, b1 - b0; w0, w1, wc = yg(b0) - 0.002, yg(b1) - 0.002, yg(zc) - 0.03
        ridge = [S.F(y, zc) for y in np.linspace(-wc, wc, int(2 * wc / 0.03) + 1)]
        face = lambda p, u, z, zc=zc, h=h: G(p.y, z) + 0.004 + 0.007 * (1 - abs(z - zc) / (h / 2)) - p.x
        add(f'grille_bar{i}', S.Fpoly([(-w0, b0), (w0, b0), (w1, b1), (-w1, b1)], 0.03), M['chrome'], face, at(-0.03), mode='x',
            grid=None, seg=0.03, chains=[ridge], bevel=0.003, cap=False)
    for k, zc in enumerate(SLATS):
        w = yg(zc) - 0.001
        add(f'grille_slat{k}', S.Fpoly([(-w, zc - 0.006), (w, zc - 0.006), (w, zc + 0.006), (-w, zc + 0.006)], 0.04), M['black_gloss'],
            at(-0.022), at(-0.05), mode='x', grid=None, seg=0.04, cap=False)
    for y in STRUTS:
        add('grille_strut', S.Fpoly([(y - 0.006, 0.655), (y + 0.006, 0.655), (y + 0.006, 1.183), (y - 0.006, 1.183)], 0.05), M['trim'],
            at(-0.035), at(-GRILLE_DEPTH - 0.003), mode='x', grid=None, seg=0.05, sym=y > 0, cap=False)

    # ---- the headlamp: three projectors, a light strip along the top with a hook near the tail, a clear cover --
    for yc in PROJ_Y:
        o_ = S.Fpoly(rrect(yc - PROJ_W / 2, yc + PROJ_W / 2, PROJ_Z - PROJ_H / 2, PROJ_Z + PROJ_H / 2, 0.008), 0.02)
        i_ = S.Fpoly(rrect(yc - PROJ_W / 2 + 0.006, yc + PROJ_W / 2 - 0.006, PROJ_Z - PROJ_H / 2 + 0.006, PROJ_Z + PROJ_H / 2 - 0.006, 0.005), 0.02)
        add('projector_ring', o_, M['lens_chrome'], -0.008, -POCKET_DEPTH - 0.002, hole=i_, grid=None, seg=0.02, sym=True, cap=False, bevel=0.0015)
        uc, du = i_[:, 0].mean(), np.ptp(i_[:, 0]) / 2
        dome = lambda p, u, z, uc=uc, du=du: -0.020 + 0.009 * max(0.0, 1 - ((abs(u) - uc) / du) ** 2) * max(0.0, 1 - ((z - PROJ_Z) / (PROJ_H / 2 - 0.006)) ** 2)
        add('projector_glass', i_, M['proj_glass'], dome, None, grid=0.011, seg=0.02, sym=True)
    b0, b1 = BROW_Z
    brow = [S.F(yg(b0) + 0.018, b0), (tail(b0) - 0.085, b0), (tail(1.105) - 0.085, 1.105), (tail(1.105) - 0.060, 1.105),
            (tail(b0) - 0.060, b0), (tail(b0) - 0.035, b0), (tail(b1) - 0.030, b1), S.F(yg(b1) + 0.018, b1)]
    add('lamp_brow', np.array(brow), M['drl'], -0.006, -POCKET_DEPTH - 0.002, grid=None, sym=True, cap=False)
    add('lamp_cover', lamp, M['lamp_cover'], -0.002, None, grid=0.04, sym=True)
    # ---- the lit bar under the lamp, in line with the second chrome bar -----------------------------------------
    d0, d1 = DRL_Z; (xa, za), (xc, zc_) = DRL_TAIL
    drl = fillet(np.array([S.F(yg(d0) + 0.004, d0), S.S(xc, zc_), S.S(xa, za), S.F(yg(d1) + 0.004, d1)]), [0.004, 0.025, 0.008, 0.004])
    add('drl_bar', drl, M['drl_frost'], 0.003, -0.02, grid=0.03, sym=True, cap=False, bevel=0.002)

    # ---- the side intake with its fins, and the chrome bracket round it ------------------------------------------
    (ya, za_), (yb, zb_), (yc_, zc2), (yd, zd) = INTAKE
    y_in = lambda z: yd + (z - zd) * (ya - yd) / (za_ - zd) - 0.004
    y_out = lambda z: yb + (z - zb_) * (yc_ - yb) / (zc2 - zb_) + 0.004
    for z in INTAKE_FINS:
        add('intake_fin', S.Fpoly([(y_in(z), z - 0.005), (y_out(z), z - 0.005), (y_out(z), z + 0.005), (y_in(z), z + 0.005)], 0.03), M['black_gloss'],
            -0.008, -INTAKE_DEPTH - 0.002, mode='x', grid=None, seg=0.03, sym=True, cap=False)
    add('intake_bracket', S.Fpoly(fillet(np.array(BRACKET), [0.004, 0.004, 0.045, 0.004, 0.004, 0.02])), M['chrome'], 0.006, -0.015, mode='x',
        grid=0.02, sym=True, cap=False, bevel=0.003)
    # ---- fog lamps -------------------------------------------------------------------------------------------------
    add('fog_lamp', S.Fpoly(rrect(*FOG_LAMP, 0.008), 0.02), M['lens_chrome'], -0.006, -FOG_DEPTH - 0.002, grid=None, seg=0.02, sym=True, cap=False, bevel=0.002)

    # ---- the lower intake, the holder in it and the skid strip ---------------------------------------------------
    for z in LOWER_FINS:
        w = 0.547 - (z - 0.457) * (0.047 / 0.123) + 0.003
        add('lower_fin', S.Fpoly([(-w, z - 0.004), (w, z - 0.004), (w, z + 0.004), (-w, z + 0.004)], 0.04), M['black_gloss'], -0.010, -INTAKE_DEPTH - 0.002,
            mode='x', grid=None, seg=0.04, cap=False)
    add('plate_holder', S.Fpoly(rrect(*PLATE, 0.006), 0.03), M['trim'], 0.0, -INTAKE_DEPTH - 0.002, mode='x', grid=None, seg=0.03, cap=False)
    add('skid_strip', S.Fpoly(rrect(*SKID, 0.012), 0.03), M['silver'], 0.012, -0.012, mode='x', grid=None, seg=0.03, cap=False, bevel=0.003)

    # one object per material
    groups = {}
    for o in parts: groups.setdefault(o.data.materials[0].name, []).append(o)
    return [surf.join(g, 'front_' + name) for name, g in groups.items()]

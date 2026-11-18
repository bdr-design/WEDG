"""The trapping pigeon (حمامة الطرح), a domestic pigeon (Columba livia domestica) of the wild rock dove's blue-bar
pattern, wearing the trapper's noose harness (the design's «شبك الحمام»: «الشبك على ظهر الحمامة»): a soft strap round
the body in front of the wings and one behind them, joined on the back by a small pad that carries the nylon nooses,
and the end of the trapper's line. The sources are in README.md ("The trapping pigeon").

Millimetres; the body frame and world as in bird.py; standing, the world's origin is on the ground between the feet.
"""
import math

import bird
from common import V3, Sec, loft, smooth_path, tube
from quarry import Species

STATIONS = [      # (d, half height above the line, below it, half width): the round, plump body of a pigeon
    (0, 8, 8, 14),
    (12, 18, 22, 24),
    (35, 28, 36, 34),
    (65, 33, 45, 38),
    (95, 33, 46, 38),       # the full breast
    (118, 29, 41, 34),
    (136, 23, 32, 27),      # the neck's base
    (150, 18, 22, 20),
    (163, 15, 16, 16.5),
    (176, 16, 14, 16),      # the back of the small head
    (188, 17, 12, 15),      # the crown over the eyes
    (198, 13, 9.5, 11.5),
    (206, 7, 6, 6.5),       # the forehead's end, the bill's root
]

SPEC = {
    'beak': {'length': 18, 'droop': 2.5, 'droop_pow': 3.0, 'h0': 5.4, 'low': 0.62, 'w0': 4.8, 'h_pow': 0.8,
             'w_pow': 0.9, 'h_tip': 0.75, 'w_tip': 0.7, 'lower': (16, 3.4, 3.8), 'sink': 5, 'p': 2.3},
    'eye': {'d': 190, 'up': 2.5, 'r': 5.2, 'out': 0.80, 'fwd': 10},
    'fold': [      # tip to wrist: the folded tips two thirds down the tail
        (-72, 14, 8, 8, 1.4, 0.5),
        (-45, 18, 3, 13, 2.2, 1.5),
        (-10, 22, -4, 21, 3.0, 3),
        (25, 26, -14, 30, 3.8, 6),
        (60, 30, -24, 36, 4.5, 9),
        (90, 30, -27, 38, 5.0, 10),
        (110, 22, -20, 36, 5.5, 6),
        (122, 8, -10, 32, 4.5, 3),
    ],
    'open': [      # root to tip
        (22, 115, 2, 6, 8, 2),
        (60, 118, -4, 6, 7, 3),
        (105, 116, 2, 6, 6, 4),          # the wrist
        (150, 110, 8, 4, 4.5, 3.5),
        (200, 98, 16, 2, 3.4, 3),
        (250, 82, 26, 0, 2.6, 2),
        (290, 64, 36, -1, 1.8, 1.5),
        (315, 50, 42, -2, 1.3, 1),
        (325, 44, 42, -2, 1.0, 0.5),
    ],
    'tail': [(0, 14, 8, 0), (35, 22, 6, 0), (75, 27, 4.5, 0), (100, 29, 3.4, 0), (114, 28, 2.6, 0),
             (118, 22, 2.0, 0), (120, 7, 1.4, 0)],
    'wrist_y': 105,
    'tail_root': 12, 'tail_up': 6,
    'leg': {'knee': (70, -28, 16), 'tibia': 38, 'tarsus': 30, 'shank_r': (13, 10.5, 7, 5.0, 4.2),
            'tarsus_r': (3.6, 3.0, 3.3), 'jess_at': 0.8},
    'toes': [(0, 30, 2.6, (6, 50), 0), (-32, 22, 2.4, (5, 50), 0), (32, 23, 2.4, (5, 50), 0), (180, 17, 2.4, (5, 50), 0)],
    'wing_root': (110, 22, 26), 'neck_base': 136,
    # a 33 cm bird seen mostly at a distance: the near level with fewer rings (about 2.7k triangles; game choice)
    'near_detail': {'body_ring': 16, 'body_stations': 26, 'wing_ring': 8, 'wing_stations': 9, 'tail_ring': 8,
                    'tail_stations': 6, 'limb_ring': 6, 'toe_ring': 5, 'toe_stations': 4, 'beak_ring': 8,
                    'beak_stations': 6, 'eye_ring': 10, 'eye_stations': 4},
}

POSES = {
    # standing: the body tilted up 22 degrees, the neck up, the head level
    'alert': {'origin': (-50, 60), 'spine': [(0, 22), (118, 22), (140, 62), (172, 62), (190, 0), (215, 0)],
              'foot': (4, 17, 0), 'foot_turn': 4, 'tail_droop': -4, 'wings': 'fold'},
    # in flight: level, the wings spread, the tail fanned, the feet drawn up
    'flight': {'origin': (0, 0), 'spine': [(0, 0), (120, 0), (140, 8), (190, 0), (215, 0)], 'wings': 'open',
               'wing_dihedral': 8, 'tail_spread': 1.3, 'tucked': True, 'tuck_ankle': (42, -22, 10),
               'tuck_foot': (-14, -18, 8), 'foot': (0, 0, 0)},
}

NOOSES = 9            # nylon loops on the pad (the bal-chatri's nooses are 4-12 cm of nylon: en.wikipedia)
NOOSE_D = (42, 60)    # their diameters, mm: game choice inside that range, small enough to stand on a pigeon
LINE_R = 0.45         # nylon monofilament, drawn 0.9 mm thick (real line is thinner; under that it vanishes)


def harness(body, det, pose):
    """The noose harness: two soft straps round the body (in front of the wings, across the breast; behind them,
    round the belly), a small pad on the back between the wings, the nylon nooses standing up from it, and the
    trapper's line from the pad's back."""
    out = []
    n = 14 if det.level == 0 else 8
    for d, w in ((122, 5.0), (52, 5.5)):
        c, t, u, v = body.frame_at(d)
        au, ad, b = body.size_at(d)
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            cu, sv = math.cos(a), math.sin(a)
            r_u = (au if cu > 0 else ad) + 1.6
            ring.append(c + u * (cu * r_u) + v * (sv * (b + 1.6)))
        out.append(bird.loop_tube('strap', ring, 2.4 if det.level == 0 else 2.6, 5 if det.level == 0 else 4, t, flat=0.45))
    # the pad: a thin cloth patch over the back from strap to strap
    secs = []
    for d in (50, 70, 90, 110, 124):
        c, t, u, v = body.frame_at(d)
        au, ad, b = body.size_at(d)
        secs.append(Sec(c + u * (au + 2.0), u, v, 1.6, 1.6, 15, 15, p=3.0))
    out.append(loft('strap', secs, 8 if det.level == 0 else 6, caps=(True, True)))
    if det.level == 0:
        # the nooses: upright loops of nylon over the pad, in two staggered rows, each leaning a little outward
        for i in range(NOOSES):
            d = 58 + (116 - 58) * (i + 0.5) / NOOSES
            c, t, u, v = body.frame_at(d)
            au, ad, b = body.size_at(d)
            side = (-1) ** i
            spread = (((i * 5) % NOOSES) / max(NOOSES - 1, 1)) * 2 - 1      # -1 .. 1, in a scrambled order
            base = c + u * (au + 3.4) + v * (side * (3.0 + 7.0 * abs(spread)))
            dia = NOOSE_D[0] + (NOOSE_D[1] - NOOSE_D[0]) * ((i * 37) % NOOSES) / max(NOOSES - 1, 1)
            lean_side = side * (0.25 + 0.9 * abs(spread))
            lean_fore = 0.5 * spread
            lean = (u + v * lean_side + t * lean_fore).normalized()
            plane = (t - lean * lean.dot(t)).normalized()
            twist = 0.6 * spread
            plane = (plane * math.cos(twist) + lean.cross(plane) * math.sin(twist)).normalized()
            pts = []
            m = 10
            for k in range(m):
                a_ = 2 * math.pi * k / m
                pts.append(base + lean * (dia / 2 * (1 - math.cos(a_))) + plane * (dia / 2 * 0.6 * math.sin(a_)))
            out.append(bird.loop_tube('line', pts, LINE_R, 3, lean.cross(plane)))
        # the trapper's line: from the pad's back over the tail, its end hanging (the rest is in the trapper's hand)
        c, t, u, v = body.frame_at(52)
        au, ad, b = body.size_at(52)
        a = c + u * (au + 3.0)
        path = smooth_path([a, a - t * 40 + u * 6, a - t * 110 + u * 2, a - t * 170 - u * 30], 10)
        out.append(tube('line', path, [LINE_R * 1.3] * len(path), 4, up=u))
    return out


PIGEON = Species('pigeon', STATIONS, SPEC, POSES, head_weight=2.2, extras=harness)


def run(B):
    for pose in ('alert', 'flight'):
        for level in (1, 0):
            root, objs, pts, body = B.build_bird('pigeon', pose, level)
        if B.RENDER:
            B.pictures_bird('pigeon', pose, root, objs, pts)

"""The saker falcon (الصقر الحر, Falco cherrug), a female (the larger sex, the one flown), in her first year (فرخ):
her numbers, her three poses, her hood (البرقع) and jesses (السبوق). The sources are in README.md.

Millimetres. Body frame and world as in bird.py. In the perched poses the world's origin is the middle of the
perch's top (or of the fist's top) under the bird's feet; in flight it is the tail's base.
"""
import math

from mathutils import Vector

import bird
from common import V3, Piece, Sec, loft, mirror, smooth_path, tube

# the body: (d, half height above the line, below it, half width), d from the tail's base forward to the forehead
STATIONS = [
    (0, 10, 10, 20),
    (15, 21, 28, 33),
    (40, 34.7, 49.3, 46),
    (75, 42.6, 63.8, 54),
    (110, 45.9, 69.4, 57),
    (140, 45.9, 67.2, 57),
    (165, 41.4, 56, 52),
    (185, 30, 37, 43),      # the neck's base
    (205, 25, 28, 33),
    (222, 23, 25, 27.5),    # the nape
    (240, 28, 25, 28.5),    # the back of the head
    (258, 29, 23, 27),      # the crown over the eyes
    (272, 23, 19, 21),
    (283, 15, 13, 14),
    (290, 8, 8, 9),         # the forehead's end, where the cere begins
]

SPEC = {
    'name': 'saker',
    'beak': {'length': 27, 'droop': 14, 'droop_pow': 2.6, 'h0': 10.5, 'low': 0.62, 'w0': 6.6, 'h_pow': 0.75,
             'w_pow': 1.0, 'h_tip': 0.7, 'w_tip': 0.5, 'cere': 9, 'lower': (17, 6.0, 5.6), 'sink': 3},
    'eye': {'d': 263, 'up': 5.0, 'r': 8.2, 'out': 0.80, 'fwd': 22, 'ring': 2.6},
    'fold': [      # tip to wrist: (x, z_top, z_bottom, y_mid, half_thickness, bend); the tips 70 mm short of the tail's
        (-135, 16, 9, 10, 1.6, 0.5),
        (-95, 20, 4, 15, 2.6, 1.5),
        (-50, 25, -3, 24, 3.4, 3),
        (-8, 29, -14, 37, 4.4, 8),
        (30, 31, -28, 50, 5.0, 13),
        (70, 41, -40, 59, 6.0, 17),
        (110, 43, -44, 63, 7.0, 19),
        (150, 35, -38, 64, 9.0, 14),
        (172, 14, -24, 58, 8.0, 6),
    ],
    'open': [      # root to tip: (y, x_leading, x_trailing, z, half_thickness, camber)
        (28, 168, -8, 8, 12, 3),
        (90, 173, -22, 8, 11, 6),
        (160, 177, -14, 9, 10, 7),
        (215, 173, 0, 9, 9, 7),        # the wrist
        (280, 163, 10, 7, 6.5, 6),
        (350, 146, 18, 4, 4.8, 5),
        (420, 124, 24, 1, 3.8, 4),
        (490, 100, 32, -2, 2.8, 3),
        (550, 80, 42, -5, 2.0, 2),
        (588, 66, 50, -6, 1.6, 1),
        (600, 60, 55, -6, 1.2, 0.5),
    ],
    'tail': [      # (distance from its root, half width, half thickness, z)
        (0, 18, 10, 0), (40, 25, 8, 0), (100, 30, 6.0, 0), (160, 33, 4.6, 0), (200, 32, 3.8, 0),
        (215, 27, 3.2, 0), (222, 17, 2.6, 0), (225, 6, 1.8, 0),
    ],
    'wrist_y': 215,
    'tail_root': 20, 'tail_up': 3,
    'leg': {'knee': (89, -53, 21), 'tibia': 96, 'tarsus': 57, 'shank_r': (19, 18.5, 16, 13, 9.5),
            'tarsus_r': (6.6, 5.6, 6.2), 'jess_at': 0.5, 'trouser': 0.38},
    'toes': [      # (heading deg, length, radius, (claw length, claw arc deg), curl)
        (0, 54, 5.4, (17, 95), 0),       # the middle toe
        (-30, 40, 5.0, (19, 100), 0),     # the inner toe
        (32, 42, 4.6, (13, 90), 0),       # the outer toe
        (180, 29, 5.6, (21, 100), 0),     # the hind toe (hallux)
    ],
}

POSES = {
    # hooded on the perch: upright, relaxed, a little fluffed, head level
    'hooded': {'origin': (-58, 80), 'spine': [(0, 66), (160, 66), (200, 86), (238, 40), (262, 0), (300, 0)],
               'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': 1, 'fluff': 1.05, 'wings': 'fold'},
    # unhooded and alert: taller, sleeked, the neck stretched, the head a little raised
    'alert': {'origin': (-54, 78), 'spine': [(0, 65), (160, 65), (196, 88), (236, 48), (262, 6), (300, 6)],
              'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': 0, 'fluff': 0.97, 'neck_stretch': 12, 'wings': 'fold'},
    # cast off: level, wings spread, tail a little fanned, the legs drawn up
    'flight': {'origin': (0, 0), 'spine': [(0, 0), (170, 0), (215, 6), (262, 0), (300, 0)], 'wings': 'open',
               'wing_dihedral': 7, 'tail_spread': 1.22, 'tucked': True, 'tuck_ankle': (40, -44, 17),
               'tuck_foot': (-12, -40, 13), 'foot': (0, 0, 0)},
}


def stations(pose):
    k = pose.get('fluff', 1.0)
    st = pose.get('neck_stretch', 0.0)
    out = []
    for (d, au, ad, b) in STATIONS:
        dd = d + st * min(max((d - 185) / 37.0, 0.0), 1.0)
        kk = k if d < 200 else 1.0 + (k - 1.0) * 0.5
        out.append((dd, au * kk, ad * kk, b * kk))
    return out


def build(pose_name, level):
    """The saker in one pose: {'body': pieces, 'hood': pieces, 'jesses': pieces}, the named points (mm), and the
    body (for painting)."""
    pose = POSES[pose_name]
    det = bird.Detail(level)
    body = bird.Body(stations(pose), pose, det, head_weight=2.0)
    parts = {'body': [body.piece(det)]}
    parts['body'] += bird.beak(body, SPEC, det)
    parts['body'] += bird.eyes(body, SPEC, det)
    if pose['wings'] == 'fold':
        parts['body'] += bird.folded_wing(body, SPEC, det)
    else:
        parts['body'] += bird.open_wing(body, SPEC, det, pose)
    parts['body'] += bird.tail(body, SPEC, pose, det)
    leg, pts = bird.legs(body, SPEC, pose, det)
    for k in ('shank', 'tarsus', 'toes', 'claws'):
        parts['body'] += leg[k]
    if pose_name == 'hooded':
        parts['hood'] = hood(body, det)
    # the jesses are left off the far model: 2 mm cords are under a pixel at tens of metres
    jp = {}
    if level == 0:
        parts['jesses'], jp = jesses(body, pts, pose, det)
    pts.update(jp)
    pts.update(points(body, pose))
    return parts, pts, body


def points(body, pose):
    """Named points for the rig and the gear to come."""
    o, t, up = bird.torso(body)
    p = {}
    c, tt, u, v = body.frame_at(252)
    p['hood'] = (c + u * 4, tt, u)                    # where the hood sits: its middle, its forward and up
    p['head'] = (c, tt, u)
    p['beak_tip'] = (body.at(body.d_end) + tt * 24 - u * 13, tt, u)
    p['wing_root_l'] = (bird.torso_point(body, 150, 22, 30), t, up)
    p['wing_root_r'] = (bird.torso_point(body, 150, 22, -30), t, up)
    p['tail_base'] = (o, t, up)
    p['neck_base'] = (body.at(185), *body.frame_at(185)[1:3])
    return p


def hood(body, det):
    """The Arab hood (البرقع): soft leather round the head from the nape to the beak's root, open under the throat
    (its lower edge inside the throat's feathers), with its top knot and the two braces at the back."""
    secs = []
    n = 9 if det.level == 0 else 5
    for i in range(n):
        d = 220 + (289 - 220) * i / (n - 1)
        au, ad, b = body.size_at(d)
        c, t, u, v = body.frame_at(d)
        grow = 5.2 * (1 - 0.35 * max(0.0, (d - 270) / 16))
        secs.append(Sec(c, u, v, au + grow, max(ad - 5, 4), b + grow, b + grow, p=2.1))
    out = [loft('hood', secs, det.body_ring, caps=(True, True))]
    # the top knot: a short plaited stem and its knob on the crown
    c, t, u, v = body.frame_at(246)
    au, ad, b = body.size_at(246)
    base = c + u * (au + 2.5)
    out.append(tube('hood_knot', [base, base + u * 6, base + u * 10], [2.6, 2.2, 3.4], 6 if det.level == 0 else 4, up=t))
    # the braces: two narrow thongs from the back, hanging behind the head
    if det.level == 0:
        c, t, u, v = body.frame_at(223)
        au, ad, b = body.size_at(223)
        for side in (1, -1):
            a = c + u * (au + 2.0) + v * side * 6
            pts = smooth_path([a, a - t * 8 - u * 3 + v * side * 4, a - t * 13 - u * 14 + v * side * 7, a - t * 15 - u * 24 + v * side * 8], 6)
            out.append(tube('hood_knot', pts, [1.4] * 6, 4, up=v))
    return out


def jesses(body, pts, pose, det):
    """The jesses (السبوق): a braided cord round each leg above the foot, the two cords joined at a swivel. Perched,
    they lie over the support's front edge and hang to the swivel; in flight they trail behind the feet."""
    out, p = [], {}
    n = 8 if det.level == 0 else 5
    cord = 1.9
    sw = V3((84, 0, -58))
    for side, key in ((1, 'l'), (-1, 'r')):
        a = pts['tarsus_' + key]
        ank = pts['ankle_' + key]
        ft = pts['foot_' + key]
        axis = (ft - ank).normalized()
        u, v = bird.frame(axis, V3((1, 0, 0)))
        ring = [a + (u * math.cos(2 * math.pi * k / 12) + v * math.sin(2 * math.pi * k / 12)) * 7.4 for k in range(12)]
        out.append(bird.loop_tube('cord', ring, cord, 5 if det.level == 0 else 4, axis))
        start = a + u * 7.4
        if pose.get('tucked'):
            back = V3((-1, 0, -0.15)).normalized()
            path = smooth_path([start, start + back * 30 + V3((0, side * 3, -4)), start + back * 62 + V3((0, side * 2, -9))], n)
        else:
            path = smooth_path([start, V3((26, side * 13, cord)), V3((66, side * 6, cord)), V3((80, side * 3, -10)),
                                V3((83, side * 1.5, -40)), sw + V3((0, side * 1.2, 4))], n + 4)
        out.append(tube('cord', path, [cord] * len(path), 5 if det.level == 0 else 4, up=V3((0, 0, 1))))
        p['jess_' + key] = (a, axis, u)
    if not pose.get('tucked'):
        # the swivel: a small steel ring where the leash (المرسل) clips on
        ring = [sw + V3((math.cos(2 * math.pi * k / 10) * 6, 0, math.sin(2 * math.pi * k / 10) * 6 - 2)) for k in range(10)]
        out.append(bird.loop_tube('steel', ring, 1.3, 4, V3((0, 1, 0))))
        p['swivel'] = (sw + V3((0, 0, -8)), V3((1, 0, 0)), V3((0, 0, 1)))
    return out, p

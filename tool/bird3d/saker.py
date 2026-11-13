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
    (165, 41.4, 58, 52),
    (185, 33, 50, 46),      # the neck's base: a falcon's head sits on its shoulders, the throat full
    (205, 27, 40, 38),
    (222, 25, 32, 32),      # the nape
    (240, 28, 27, 30),      # the back of the head
    (258, 29, 23, 27.5),    # the crown over the eyes
    (272, 23, 19, 21),
    (283, 16, 14, 14.5),
    (290, 12, 10, 9.5),     # the forehead's end, where the cere begins (as deep as the bill's root)
]

SPEC = {
    'name': 'saker',
    'beak': {'length': 21, 'droop': 14, 'droop_pow': 2.0, 'h0': 12.0, 'low': 0.72, 'w0': 7.4, 'h_pow': 0.85,
             'w_pow': 1.0, 'h_tip': 0.7, 'w_tip': 0.5, 'cere': 7, 'lower': (13, 6.5, 6.4), 'sink': 7, 'tooth': 0.62},
    'eye': {'d': 263, 'up': 5.0, 'r': 8.2, 'out': 0.80, 'fwd': 22, 'ring': 2.8, 'brow': (22, 3.4, 3.6)},
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
        (28, 168, -18, 8, 12, 3),
        (90, 174, -34, 8, 11, 6),
        (160, 178, -28, 9, 10, 7),
        (215, 174, -16, 9, 9, 7),        # the wrist
        (280, 164, -14, 7, 6.5, 6),
        (350, 149, -8, 4, 4.8, 5),
        (420, 129, -2, 1, 3.8, 4),
        (490, 107, 8, -2, 2.8, 3),
        (550, 88, 22, -5, 2.0, 2),
        (588, 72, 40, -6, 1.6, 1),
        (600, 64, 52, -6, 1.2, 0.5),
    ],
    'tail': [      # (distance from its root, half width, half thickness, z)
        (0, 18, 10, 0), (40, 25, 8, 0), (100, 30, 6.0, 0), (160, 33, 4.6, 0), (200, 32, 3.8, 0),
        (215, 27, 3.2, 0), (222, 17, 2.6, 0), (225, 6, 1.8, 0),
    ],
    'wrist_y': 215,
    'tail_root': 20, 'tail_up': 3,
    'leg': {'knee': (95, -38, 20), 'tibia': 104, 'tarsus': 57, 'shank_r': (26, 22, 17, 13, 9.5),
            'tarsus_r': (6.6, 5.6, 6.2), 'jess_at': 0.5, 'trouser': 0.38},
    'toes': [      # (heading deg, length, radius, (claw length, claw arc deg), curl)
        (0, 52, 4.6, (21, 125), 0),      # the middle toe
        (-30, 39, 4.4, (23, 130), 0),     # the inner toe
        (32, 41, 4.0, (17, 120), 0),      # the outer toe
        (180, 28, 4.8, (25, 130), 0),     # the hind toe (hallux)
    ],
}

POSES = {
    # hooded on the perch: upright, relaxed, a little fluffed, head level
    'hooded': {'origin': (-58, 80), 'spine': [(0, 66), (160, 66), (200, 86), (238, 40), (262, 0), (300, 0)],
               'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': 1, 'fluff': 1.05, 'wings': 'fold'},
    # hooded on the fist (الدس): the same bird, her jesses held in the falconer's fist
    'fist': {'origin': (-58, 80), 'spine': [(0, 66), (160, 66), (200, 86), (238, 40), (262, 0), (300, 0)],
             'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': 1, 'fluff': 1.05, 'wings': 'fold', 'held': True},
    # unhooded and alert: taller, sleeked, the neck stretched, the head a little raised
    'alert': {'origin': (-54, 78), 'spine': [(0, 65), (160, 65), (196, 88), (236, 48), (262, 6), (300, 6)],
              'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': 0, 'fluff': 0.97, 'neck_stretch': 12, 'wings': 'fold'},
    # cast off: level, wings spread, tail a little fanned, the legs drawn up
    'flight': {'origin': (0, 0), 'spine': [(0, 0), (170, 0), (215, 6), (262, 0), (300, 0)], 'wings': 'open',
               'wing_dihedral': 7, 'tail_spread': 1.22, 'tucked': True, 'tuck_ankle': (35, -40, 15),
               'tuck_foot': (-22, -18, 11), 'foot': (0, 0, 0)},
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
    if pose_name in ('hooded', 'fist'):
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
    # the top knot: a small plaited leather knot sitting on the crown, with a short tuft of thong ends
    c, t, u, v = body.frame_at(246)
    au, ad, b = body.size_at(246)
    base = c + u * (au + 4.0)
    out.append(bird.ball('hood_knot', base + u * 2.6, 3.4, 8 if det.level == 0 else 5))
    if det.level == 0:
        for k, side in ((0, 1), (1, -1), (2, 0)):
            a = base + u * 4.5
            tip = a + u * 4.0 - t * (5 + 2 * k) + v * side * 2.5
            out.append(tube('hood_knot', [a, a.lerp(tip, 0.5) + u * 1.0, tip], [1.1, 0.9, 0.5], 4, up=t))
        # the braces: two leather thongs drawn through the back, their ends hanging down the nape
        c, t, u, v = body.frame_at(224)
        au, ad, b = body.size_at(224)
        for side in (1, -1):
            a = c + u * (au + 4.5) + v * side * 7
            pts = smooth_path([a, a - t * 6 + u * 1 + v * side * 5, a - t * 10 - u * 10 + v * side * 9,
                               a - t * 11 - u * 24 + v * side * 11, a - t * 10 - u * 36 + v * side * 11], 7)
            out.append(tube('hood_knot', pts, [2.0, 2.0, 1.9, 1.8, 1.7, 1.6, 1.2], 5, up=v))
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
        if pose.get('held'):
            # down over the fist's front into the falconer's grip, between his fingers
            path = smooth_path([start, V3((16, side * 9, cord)), V3((30, side * 4, -3)), V3((36, side * 2, -14)),
                                V3((34, side * 1.5, -26))], n)
        elif pose.get('tucked'):
            back = V3((-1, 0, -0.15)).normalized()
            path = smooth_path([start, start + back * 30 + V3((0, side * 3, -4)), start + back * 62 + V3((0, side * 2, -9))], n)
        else:
            path = smooth_path([start, V3((26, side * 13, cord)), V3((66, side * 6, cord)), V3((80, side * 3, -10)),
                                V3((83, side * 1.5, -40)), sw + V3((0, side * 1.2, 4))], n + 4)
        out.append(tube('cord', path, [cord] * len(path), 5 if det.level == 0 else 4, up=V3((0, 0, 1))))
        p['jess_' + key] = (a, axis, u)
    if not pose.get('tucked') and not pose.get('held'):
        # the swivel: a small steel ring where the leash (المرسل) clips on
        ring = [sw + V3((math.cos(2 * math.pi * k / 10) * 6, 0, math.sin(2 * math.pi * k / 10) * 6 - 2)) for k in range(10)]
        out.append(bird.loop_tube('steel', ring, 1.3, 4, V3((0, 1, 0))))
        p['swivel'] = (sw + V3((0, 0, -8)), V3((1, 0, 0)), V3((0, 0, 1)))
    return out, p

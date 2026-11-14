"""The quarry of falconry in the Kingdom: the Asian houbara (الحبارى, Chlamydotis macqueenii), a male, standing alert
and in flight; the Eurasian stone-curlew (الكروان, Burhinus oedicnemus) standing. The sources are in README.md.

Millimetres; the body frame and world as in bird.py; standing, the world's origin is on the ground between the feet.
"""
import math

import bird
from common import V3, Sec, loft, smooth_path, tube


class Species:
    def __init__(self, name, stations, spec, poses, head_weight=2.0, extras=None):
        self.name, self.STATIONS, self.SPEC, self.POSES = name, stations, spec, poses
        self.head_weight = head_weight
        self.extras = extras

    def build(self, pose_name, level):
        pose = self.POSES[pose_name]
        det = bird.Detail(level, self.SPEC.get('near_detail'))
        st = [(d * self.SPEC.get('scale', 1.0), au, ad, b) for (d, au, ad, b) in self.STATIONS]
        body = bird.Body(st, pose, det, head_weight=self.head_weight)
        parts = {'body': [body.piece(det)]}
        parts['body'] += bird.beak(body, self.SPEC, det)
        parts['body'] += bird.eyes(body, self.SPEC, det)
        if pose['wings'] == 'fold':
            parts['body'] += bird.folded_wing(body, self.SPEC, det)
        else:
            parts['body'] += bird.open_wing(body, self.SPEC, det, pose)
            parts['body'] += bird.fingers(body, self.SPEC, det, pose)
        parts['body'] += bird.tail(body, self.SPEC, pose, det)
        leg, pts = bird.legs(body, self.SPEC, pose, det)
        for k in ('shank', 'tarsus', 'toes', 'claws'):
            parts['body'] += leg[k]
        if self.extras:
            parts['body'] += self.extras(body, det, pose)
        o, t, up = bird.torso(body)
        c, tt, u, v = body.frame_at(body.d_end - 25)
        pts['head'] = (c, tt, u)
        pts['beak_tip'] = (body.at(body.d_end) + tt * self.SPEC['beak']['length'], tt, u)
        pts['tail_base'] = (o, t, up)
        wx = self.SPEC.get('wing_root', (150, 25, 30))
        pts['wing_root_l'] = (bird.torso_point(body, wx[0], wx[1], wx[2]), t, up)
        pts['wing_root_r'] = (bird.torso_point(body, wx[0], wx[1], -wx[2]), t, up)
        nb = self.SPEC.get('neck_base', 260)
        pts['neck_base'] = (body.at(nb), *body.frame_at(nb)[1:3])
        return parts, pts, body


# ------------------------------------------------------------------ the houbara (a male)
HOUBARA_STATIONS = [
    (0, 12, 12, 22),
    (20, 27, 35, 41),
    (60, 43, 63, 63),
    (110, 52, 78, 72),
    (160, 55, 80, 74),
    (205, 52, 72, 68),
    (240, 44, 58, 56),
    (262, 34, 44, 45),      # the neck's base
    (290, 26, 32, 32),      # the neck, its ruff of long feathers fuller at the sides
    (330, 22, 25, 25),
    (370, 19, 21, 20),
    (400, 18, 19, 18),
    (420, 20, 17, 19),      # the back of the head
    (440, 22, 18, 19.5),    # the crown over the eyes, flat
    (456, 18, 14, 16),
    (470, 7, 6, 7),         # the forehead's end
]

HOUBARA_SPEC = {
    'beak': {'length': 36, 'droop': 6, 'droop_pow': 2.2, 'h0': 8.2, 'low': 0.66, 'w0': 7.8, 'h_pow': 0.8,
             'w_pow': 0.9, 'h_tip': 0.7, 'w_tip': 0.7, 'lower': (32, 5.4, 6.6), 'sink': 7, 'p': 2.4},
    'eye': {'d': 440, 'up': 3.0, 'r': 7.6, 'out': 0.84, 'fwd': 14},
    'fold': [      # tip to wrist
        (-48, 26, 14, 24, 2.4, 1),
        (-20, 37, 6, 40, 3.4, 3),
        (20, 49, -6, 58, 4.5, 9),
        (80, 56, -38, 72, 6.0, 15),
        (140, 57, -50, 77, 7.0, 19),
        (190, 52, -46, 73, 8.0, 16),
        (222, 32, -29, 61, 8.0, 9),
        (237, 12, -10, 48, 6.0, 4),
    ],
    'open': [      # root to tip
        (35, 228, 30, 10, 14, 4),
        (120, 234, 10, 10, 13, 8),
        (210, 238, 20, 10, 12, 10),
        (280, 234, 40, 9, 10, 9),        # the wrist
        (350, 222, 52, 7, 7.5, 8),
        (430, 202, 58, 4, 5.5, 6),
        (510, 180, 62, 1, 4.2, 4),
        (580, 162, 70, -1, 3.2, 3),
        (620, 152, 84, -2, 2.6, 2),
        (640, 142, 104, -2, 2.0, 1),
    ],
    'fingers': [   # the slotted primaries: (y0, x0, y1, x1, half width, z at the tip)
        (560, 150, 708, 146, 21.0, -1),
        (560, 138, 704, 126, 21.0, -2),
        (558, 126, 696, 106, 20.5, -2),
        (554, 114, 686, 88, 20.0, -1),
        (548, 102, 672, 72, 19.5, 0),
        (542, 90, 654, 58, 19.0, 1),
    ],
    'tail': [(0, 26, 18, 0), (45, 38, 15, 0), (95, 46, 12, 0), (135, 48, 10, 0), (155, 45, 8.5, 0), (166, 36, 7, 0),
             (172, 20, 5.5, 0), (175, 6, 3.5, 0)],
    'wrist_y': 280,
    'tail_root': 25, 'tail_up': 18,
    'leg': {'knee': (138, -56, 30), 'tibia': 86, 'tarsus': 98, 'shank_r': (22, 18, 11, 8.0, 7.4),
            'tarsus_r': (7.6, 6.6, 7.2), 'jess_at': 0.8},
    'toes': [(0, 36, 6.4, (8, 40), 0), (-36, 29, 6.0, (7, 40), 0), (36, 30, 6.0, (7, 40), 0)],
    'wing_root': (205, 40, 40), 'neck_base': 262,
}

HOUBARA_POSES = {
    # alert: the body a little raised in front, the neck straight up, the head level
    'alert': {'origin': (-152, 196), 'spine': [(0, 12), (230, 14), (285, 72), (320, 86), (392, 86), (424, 0), (480, 0)],
              'foot': (10, 34, 0), 'foot_r_shift': (-36, 2, 0), 'foot_turn': 4, 'tail_droop': -2, 'wings': 'fold'},
    # in flight: level, the neck stretched forward, the wings spread with the hand's primaries slotted
    'flight': {'origin': (0, 0), 'spine': [(0, 2), (250, 2), (300, 7), (420, 2), (480, 0)], 'wings': 'open',
               'wing_dihedral': 5, 'tail_spread': 1.15, 'tucked': True, 'tuck_ankle': (60, -74, 24),
               'tuck_foot': (-55, -62, 20), 'foot': (0, 0, 0)},
}


def houbara_extras(body, det, pose):
    """The male's crest: a tuft of long, curved feathers lying back along the crown, white with black tips."""
    c, t, u, v = body.frame_at(447)
    au, ad, b = body.size_at(447)
    out = []
    # a loose tuft: eleven feathers of different lengths, overlapping, each rising a little off the crown and
    # drooping at its tip, the middle ones longest
    plan = [((i - 5) / 5.0 * 1.4, abs(i - 5) * 1.6 + (i % 2) * 2.0, 62 - abs(i - 5) * 4 + (i % 3) * 3, 5.5 + (i % 3) * 1.5)
            for i in range(11)]
    if det.level != 0:
        plan = plan[5:6]
    for side, back, L, lift0 in plan:
        base = c + u * (au - 1.5) + v * side * 4.0 - t * back
        lift = lift0 - 1.2 * abs(side)
        pts = smooth_path([base + t * 3, base - t * (L * 0.3) + u * lift + v * side * 3,
                           base - t * (L * 0.7) + u * (lift - 0.5) + v * side * 6, base - t * L + u * (lift - 3) + v * side * 8], 6 if det.level == 0 else 3)
        secs = []
        for i, q in enumerate(pts):
            f = i / (len(pts) - 1)
            a, bb = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
            tt = (bb - a).normalized()
            uu, vv = bird.frame(tt, u)
            w = 4.0 * math.sin(math.pi * min(0.15 + f * 1.1, 1.0)) + 0.5
            secs.append(Sec(q, uu, vv, 0.8, 0.6, w, p=2.0))
        out.append(loft('crest', secs, 6 if det.level == 0 else 4, caps=(True, True)))
    return out


HOUBARA = Species('houbara', HOUBARA_STATIONS, HOUBARA_SPEC, HOUBARA_POSES, head_weight=2.4, extras=houbara_extras)


# ------------------------------------------------------------------ the stone-curlew
CURLEW_STATIONS = [      # d scaled by 1.1 at build (the spec's 'scale')
    (0, 12.5, 12.5, 16.8),
    (15, 25, 32.8, 26.9),
    (45, 39, 53, 38.1),
    (80, 45.2, 60.8, 42.6),
    (115, 45.2, 57.7, 42.6),
    (140, 39, 46.8, 37),
    (158, 26.9, 30.2, 28),      # the neck's base
    (172, 25, 27, 27),
    (189, 21, 21, 23),
    (209, 19, 18, 21),
    (226, 22, 18, 22),      # the big, round head
    (242, 23, 18, 22.5),
    (256, 18, 14, 18),
    (266, 6.5, 5.5, 6.5),   # the forehead's end
]

CURLEW_SPEC = {
    'scale': 1.1,
    'beak': {'length': 37, 'droop': 3.5, 'droop_pow': 3.0, 'h0': 6.2, 'low': 0.72, 'w0': 5.0, 'h_pow': 0.7,
             'w_pow': 0.85, 'h_tip': 0.7, 'w_tip': 0.6, 'lower': (35, 4.8, 4.6), 'sink': 7, 'p': 2.3},
    'eye': {'d': 266, 'up': 4.0, 'r': 9.6, 'out': 0.80, 'fwd': 18},
    'fold': [
        (-95, 31.2, 23.4, 12.3, 1.4, 0.5),
        (-60, 35.9, 18.7, 17.9, 2, 1),
        (-15, 40.6, 6.2, 26.9, 3, 3),
        (30, 48.4, -18.7, 38.1, 4, 7),
        (75, 51.5, -39, 44.8, 4.5, 9),
        (115, 48.4, -42.1, 44.8, 5, 9),
        (145, 34.3, -29.6, 39.2, 5, 5),
        (160, 12.5, -12.5, 31.4, 4, 2),
    ],
    'open': [
        (22, 128, 30, 6, 9, 2),
        (80, 132, 22, 6, 8, 4),
        (140, 134, 34, 6, 7, 5),
        (175, 130, 50, 5, 6, 5),         # the wrist
        (230, 120, 60, 3, 4.2, 4),
        (290, 104, 66, 1, 3.0, 3),
        (345, 88, 66, -1, 2.2, 2),
        (390, 72, 58, -2, 1.6, 1),
        (410, 62, 52, -3, 1.2, 0.5),
    ],
    'tail': [(0, 15, 14, 0), (40, 21, 12, 0), (78, 22, 9, 0), (102, 17, 6.5, 0), (116, 9, 4, 0), (122, 3, 2.5, 0)],
    'wrist_y': 175,
    'tail_root': 16, 'tail_up': 15,
    'leg': {'knee': (86, -40, 19), 'tibia': 50, 'tarsus': 82, 'shank_r': (12, 10, 6.0, 4.6, 4.2),
            'tarsus_r': (5.2, 3.6, 4.2), 'jess_at': 0.8, 'knob': 8.2},
    'toes': [(0, 31, 3.6, (5, 45), 0), (-36, 25, 3.4, (4, 45), 0), (36, 25, 3.4, (4, 45), 0)],
    'wing_root': (140, 20, 25), 'neck_base': 174,
}

CURLEW_POSES = {
    'alert': {'origin': (-86, 150), 'spine': [(0, 10), (160, 10), (192, 88), (246, 82), (272, 6), (320, 6)],
              'foot': (2, 22, 0), 'foot_turn': 5, 'tail_droop': -3, 'wings': 'fold'},
    'flight': {'origin': (0, 0), 'spine': [(0, 0), (160, 0), (190, 10), (265, 0), (320, 0)], 'wings': 'open',
               'wing_dihedral': 6, 'tail_spread': 1.15, 'tucked': True, 'tuck_ankle': (50, -44, 14),
               'tuck_foot': (-70, -30, 10), 'foot': (0, 0, 0)},
}

CURLEW = Species('curlew', CURLEW_STATIONS, CURLEW_SPEC, CURLEW_POSES, head_weight=2.6)


def run(name, B):
    sp = HOUBARA if name == 'houbara' else CURLEW
    poses = ('alert', 'flight') if name == 'houbara' else ('alert', 'flight')
    for pose in poses:
        for level in (1, 0):
            root, objs, pts, body = B.build_bird(name, pose, level)
        if B.RENDER:
            B.pictures_bird(name, pose, root, objs, pts)

"""The passage peregrine of the year (فرخ الشاهين البحري, Falco peregrinus, most likely the tundra race calidus), a
female (the larger sex, the one prized: الشيهانة), in her first plumage: her own numbers, poses, and the saker's hood
and jesses fitted to her. The sources are in README.md ("The peregrine of the year").

Millimetres. Body frame and world as in bird.py and saker.py. In the perched poses the world's origin is the middle
of the support's top under her feet; in flight it is the tail's base.

Against the saker (saker.py), each difference is a measured or described one:
- the tail shorter (160 mm visible against 205), and the folded wings reaching almost to its tip (about 12 mm
  short, against the saker's 70);
- the wings pointed: the hand narrows to a sharper tip, the span less (1,080 against 1,200 mm) but the wing as long
  against the body;
- the chest broader and deeper, the neck shorter, the head rounder;
- the feet larger (the middle toe 58 mm against 52), the tarsus shorter (52 against 57);
- the bill shorter and deeper.
"""
import bird
import saker
from common import V3

STATIONS = [      # (d, half height above the line, below it, half width), d from the tail's base forward
    (0, 10, 10, 20),
    (15, 22, 30, 35),
    (40, 36.5, 52, 49),
    (75, 45, 68, 58),
    (110, 48, 73, 61),      # the broad, deep chest
    (140, 47, 70, 60),
    (163, 41.5, 59, 53),
    (180, 34, 50, 47),      # the neck's base: short, the head sits low on the shoulders
    (198, 28, 40, 39),
    (214, 26, 32, 33),      # the nape
    (232, 29, 27.5, 31),    # the back of the head: round
    (250, 30, 23.5, 28.5),  # the crown over the eyes
    (264, 24, 19.5, 21.5),
    (275, 16.5, 14.5, 15),
    (282, 12.5, 10.5, 10),  # the forehead's end, where the cere begins
]

SPEC = {
    'name': 'peregrine',
    'beak': {'length': 19, 'droop': 14, 'droop_pow': 1.9, 'h0': 12.8, 'low': 0.74, 'w0': 7.6, 'h_pow': 0.85,
             'w_pow': 1.0, 'h_tip': 0.7, 'w_tip': 0.5, 'cere': 7, 'lower': (12, 6.6, 6.5), 'sink': 7, 'tooth': 0.62},
    'eye': {'d': 255, 'up': 5.0, 'r': 8.7, 'out': 0.80, 'fwd': 22, 'ring': 2.6, 'brow': (24, 3.0, 4.4)},
    'fold': [      # tip to wrist: the tips 12 mm short of the tail's
        (-148, 15, 8, 9, 1.5, 0.5),
        (-105, 19, 3, 14, 2.5, 1.5),
        (-58, 24, -4, 23, 3.3, 3),
        (-12, 29, -15, 37, 4.4, 8),
        (30, 32, -29, 51, 5.0, 13),
        (70, 42, -41, 61, 6.0, 17),
        (110, 44, -45, 65, 7.0, 19),
        (150, 36, -39, 66, 9.0, 14),
        (170, 14, -24, 60, 8.0, 6),
    ],
    'open': [      # root to tip: (y, x_leading, x_trailing, z, half_thickness, camber); a pointed hand
        (28, 162, -20, 8, 12, 3),
        (85, 168, -34, 8, 11, 6),
        (150, 172, -26, 9, 10, 7),
        (200, 168, -14, 9, 9, 7),        # the wrist
        (260, 157, -10, 7, 6.5, 6),
        (320, 142, -4, 4, 4.8, 5),
        (380, 124, 5, 1, 3.8, 4),
        (440, 103, 18, -2, 2.8, 3),
        (490, 84, 34, -4, 2.0, 2),
        (525, 68, 50, -5, 1.4, 1),
        (540, 60, 57, -5, 1.0, 0.5),
    ],
    'tail': [      # (distance from its root, half width, half thickness, z)
        (0, 18, 10, 0), (40, 25, 8, 0), (90, 29, 6.0, 0), (130, 30, 4.6, 0), (155, 28, 3.8, 0),
        (168, 23, 3.2, 0), (175, 14, 2.6, 0), (178, 5, 1.8, 0),
    ],
    'wrist_y': 200,
    'tail_root': 18, 'tail_up': 3,
    'leg': {'knee': (95, -22, 21), 'tibia': 110, 'tarsus': 52, 'shank_r': (36, 28, 19, 13.5, 10),
            'tarsus_r': (7.0, 6.0, 6.6), 'jess_at': 0.5, 'trouser': 0.36},
    'toes': [      # (heading deg, length, radius, (claw length, claw arc deg), curl): the large feet of a bird-catcher
        (0, 58, 5.6, (23, 125), 0),      # the middle toe
        (-30, 43, 5.3, (25, 130), 0),     # the inner toe
        (32, 45, 4.9, (19, 120), 0),      # the outer toe
        (180, 31, 5.7, (27, 130), 0),     # the hind toe (hallux)
    ],
}

POSES = {
    # hooded on the perch in the tent: upright, relaxed, a little fluffed
    'hooded': {'origin': (-56, 74), 'spine': [(0, 64), (155, 64), (192, 84), (228, 40), (252, 0), (290, 0)],
               'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': 1, 'fluff': 1.05, 'wings': 'fold'},
    # hooded on the fist (الدس), her jesses held in the falconer's fist
    'fist': {'origin': (-56, 74), 'spine': [(0, 64), (155, 64), (192, 84), (228, 40), (252, 0), (290, 0)],
             'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': -9, 'fluff': 1.05, 'wings': 'fold', 'held': True,
             'grip': 'dass'},
    # unhooded on the perch: alert, sleeked, the neck up
    'alert': {'origin': (-52, 72), 'spine': [(0, 63), (155, 63), (190, 86), (226, 48), (252, 6), (290, 6)],
              'foot': (0, 22, 0), 'foot_turn': 8, 'tail_droop': 0, 'fluff': 0.97, 'neck_stretch': 10, 'wings': 'fold'},
    # in flight over the decoy: level, the wings spread, the legs drawn up
    'flight': {'origin': (0, 0), 'spine': [(0, 0), (165, 0), (208, 6), (252, 0), (290, 0)], 'wings': 'open',
               'wing_dihedral': 6, 'tail_spread': 1.18, 'tucked': True, 'tuck_ankle': (56, -26, 13),
               'tuck_foot': (22, -10, 9), 'foot': (0, 0, 0)},
}


def stations(pose):
    k = pose.get('fluff', 1.0)
    st = pose.get('neck_stretch', 0.0)
    out = []
    for (d, au, ad, b) in STATIONS:
        dd = d + st * min(max((d - 180) / 34.0, 0.0), 1.0)
        kk = k if d < 195 else 1.0 + (k - 1.0) * 0.5
        out.append((dd, au * kk, ad * kk, b * kk))
    return out


def build(pose_name, level):
    """The peregrine in one pose: {'body', 'hood', 'jesses'} pieces, the named points (mm), the body."""
    if POSES[pose_name].get('grip') == 'dass':
        import gear
        POSES[pose_name]['grip_fn'] = gear.dass_top
    pose = POSES[pose_name]
    det = bird.Detail(level)
    body = bird.Body(stations(pose), pose, det, head_weight=2.0)
    parts = {'body': [body.piece(det)]}
    parts['body'] += bird.beak(body, SPEC, det)
    spec = SPEC
    if pose_name in ('hooded', 'fist'):
        spec = dict(SPEC, eye={k: v for k, v in SPEC['eye'].items() if k not in ('brow', 'ring')})
    parts['body'] += bird.eyes(body, spec, det)
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
    jp = {}
    if level == 0:
        parts['jesses'], jp = saker.jesses(body, pts, pose, det)
    pts.update(jp)
    pts.update(saker.points(body, pose, hood_d=244, neck_d=180))
    return parts, pts, body


def hood(body, det):
    """The saker's hood (البرقع) on her head: the same pattern, cut to her rounder head by the same code (it follows
    the body's sections from the nape to the bill's root)."""
    return saker.hood_on(body, det, d0=212, d1=281, knot=238, braces=216)

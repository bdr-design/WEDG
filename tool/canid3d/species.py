"""The animals' numbers and poses. Every size is in units of the withers height H (README.md says where each figure
comes from and which are game choices); the model's own figures are measured on the files by build.py.

Torso rows: (x, top, bottom, half width above the middle, half width at the bottom), x from the body's middle forward.
Neck rows: (place 0..1, half width, half depth on the crest side, half depth on the throat side).
Head rows: (place from the occiput 0 to the nose 1, centre above the head's axis, half height above, below, half width).
Jaw rows: as the head's, about the jaw's own axis from its hinge. Paw rows: (place heel 0 to toe 1, height above and
below the paw's middle in paw heights, half width in paw widths). Tail rows: (place, half width, half depth).
Legs: sizes at each joint (half width, half depth in front, half depth behind).

Poses: drop (the body lowered, H), pitch (degrees, + the front up), neck (degrees above forward), head (degrees below
forward), jaw (opened, degrees), ears_back (degrees), tail (angles below backward for even steps along it, or
(angle, yaw toward the animal's left)), legs: per leg {x, y, z of the sole's point, meta (the metapodial's lean from
upright, + its top back), paw (the paw's forward, degrees above forward), pole (where the elbow or stifle bends to),
root (the shoulder or hip joint moved, (dx, dz) H)}.
"""

PAW = [(0.00, 0.50, 0.40, 0.32), (0.14, 0.86, 0.48, 0.46), (0.38, 0.92, 0.50, 0.50), (0.62, 0.78, 0.50, 0.50),
       (0.84, 0.55, 0.47, 0.44), (1.00, 0.18, 0.24, 0.24)]

# ------------------------------------------------------------------ the Arabian wolf (an adult, summer coat)
WOLF = dict(
    name='wolf',
    H=650.0,
    pivot_z=0.75,
    torso=[
        (-0.60, 0.855, 0.700, 0.040, 0.030),
        (-0.55, 0.905, 0.600, 0.072, 0.050),
        (-0.45, 0.935, 0.560, 0.096, 0.066),
        (-0.32, 0.932, 0.590, 0.100, 0.066),
        (-0.16, 0.922, 0.640, 0.093, 0.062),
        (0.00, 0.935, 0.585, 0.104, 0.064),
        (0.14, 0.962, 0.540, 0.114, 0.060),
        (0.27, 0.992, 0.505, 0.116, 0.052),
        (0.38, 1.000, 0.515, 0.110, 0.050),
        (0.47, 0.940, 0.540, 0.096, 0.052),
        (0.54, 0.840, 0.565, 0.074, 0.046),
        (0.59, 0.730, 0.600, 0.042, 0.032),
    ],
    withers=(0.36, 1.0),
    neck_base=(0.40, 0.80),
    neck_angle=36.0,
    neck_len=0.26,
    neck_arch=0.02,
    # the summer neck: no ruff, its top carrying the back's line into the skull, as wide behind the skull as the skull
    neck=[(0.0, 0.098, 0.140, 0.160), (0.4, 0.092, 0.110, 0.140), (0.8, 0.088, 0.085, 0.110), (1.0, 0.085, 0.072, 0.092)],
    head_len=0.350,
    head_pitch=14.0,
    occ_up=0.0,
    # a wedge broadening steadily from the nose: the muzzle (eye to nose) half the head, 60-70 mm wide at its middle;
    # a mild stop, a broad flat crown
    head=[
        (0.00, 0.000, 0.050, 0.050, 0.060),
        (0.10, 0.006, 0.074, 0.070, 0.088),
        (0.24, 0.008, 0.080, 0.076, 0.100),
        (0.38, 0.004, 0.072, 0.066, 0.088),
        (0.50, -0.004, 0.060, 0.056, 0.070),
        (0.62, -0.010, 0.054, 0.047, 0.058),
        (0.76, -0.014, 0.047, 0.040, 0.054),
        (0.90, -0.017, 0.041, 0.033, 0.044),
        (1.00, -0.020, 0.031, 0.024, 0.033),
    ],
    jaw_hinge=(0.24, -0.054),
    jaw=[
        (0.16, 0.000, 0.028, 0.042, 0.070),
        (0.30, -0.004, 0.030, 0.040, 0.066),
        (0.50, -0.006, 0.026, 0.031, 0.052),
        (0.70, -0.004, 0.022, 0.024, 0.042),
        (0.88, 0.000, 0.018, 0.019, 0.033),
        (0.96, 0.002, 0.012, 0.013, 0.022),
    ],
    nose=(0.985, -0.012, 0.024),
    eye=(0.50, 0.034, 0.051, 0.0160),
    eye_out=30.0,
    ear=(0.165, 0.106, 0.014),
    ear_base=(0.14, 0.050, 0.080),
    ear_splay=26.0,
    ear_tilt=4.0,
    ear_cup=0.45,
    teeth=True,
    canine=(0.80, -0.052, 0.024, 0.020, 0.0058),
    canine_low_cz=0.008,
    shoulder=(0.47, 0.640, 0.060),
    hip=(-0.40, 0.700, 0.056),
    fore_bones=(0.26, 0.31, 0.12),
    hind_bones=(0.28, 0.30, 0.19),
    forepaw=(0.112, 0.082, 0.050),
    hindpaw=(0.104, 0.076, 0.048),
    paw_shape=PAW,
    # the forearm and the gaskin flattened sideways (about 0.7 width to depth), as a canid's are
    fore_sizes=dict(top=(0.040, 0.080, 0.100), shoulder=(0.048, 0.068, 0.080), arm=(0.046, 0.070, 0.066),
                    elbow=(0.040, 0.048, 0.062), fore1=(0.032, 0.045, 0.045), fore2=(0.026, 0.037, 0.036),
                    carpus=(0.026, 0.032, 0.036), pastern=(0.022, 0.026, 0.026), fet=(0.025, 0.028, 0.026)),
    hind_sizes=dict(top=(0.052, 0.125, 0.125), hip=(0.060, 0.115, 0.125), thigh=(0.058, 0.098, 0.108),
                    stifle=(0.046, 0.056, 0.068), gaskin1=(0.034, 0.046, 0.064), gaskin2=(0.025, 0.033, 0.038),
                    hock=(0.024, 0.028, 0.046), meta=(0.021, 0.026, 0.028), fet=(0.025, 0.028, 0.026)),
    stance=dict(fore=dict(x=0.36, y=0.066, meta=15.0), hind=dict(x=-0.47, y=0.060, meta=10.0)),
    tail_base=(-0.585, 0.860),
    tail_len=0.60,
    tail_hang=[45, 62, 74, 80, 84],
    # about 40 mm at the root, fullest at mid-length, tapering to the tip
    tail_r=[(0.0, 0.031, 0.033), (0.18, 0.048, 0.050), (0.50, 0.064, 0.064), (0.75, 0.058, 0.058), (0.90, 0.040, 0.040),
            (1.0, 0.012, 0.012)],
    collar=None,
)

WOLF_POSES = {
    # standing alert: head up, ears pricked forward, the tail hanging
    'alert': dict(neck=38, head=18),
    # the low stalking walk near the pens: body lowered on bent legs, head at or below the back's line and reaching
    # forward, ears forward, tail held low; the left fore lifted in mid step (walk: LH, LF, RH, RF)
    'stalk': dict(drop=0.12, pitch=-3, neck=6, head=16, tail=[38, 52, 64, 72, 78],
                  legs=dict(fore_l=dict(x=0.47, z=0.07, meta=38, paw=-18),
                            fore_r=dict(x=0.30, meta=20),
                            hind_l=dict(x=-0.42, meta=6),
                            hind_r=dict(x=-0.60, meta=16))),
    # running off (the rotary gallop, the right fore alone on the ground, the left reaching, the hinds stretched back
    # after their push): what the game shows when the herdsman or the dog drives it away
    'run': dict(drop=0.05, pitch=-4, arch=10, neck=22, head=22, ears_back=55, tail=[12, 16, 20, 24, 28],
                legs=dict(fore_r=dict(x=0.28, meta=38, root=(0.0, 0.0)),
                          fore_l=dict(x=0.80, z=0.20, meta=60, paw=8, root=(0.05, 0.02)),
                          hind_l=dict(x=-0.95, z=0.20, meta=-34, paw=-110, pole=(1, 0, -0.2), root=(-0.03, 0.0)),
                          hind_r=dict(x=-0.86, z=0.10, meta=-28, paw=-100, pole=(1, 0, -0.2), root=(-0.02, 0.0)))),
}

# ------------------------------------------------------------------ the guard dog (the local pariah type), a male
DOG = dict(WOLF)
DOG.update(
    name='dog',
    H=560.0,
    torso=[
        (-0.55, 0.840, 0.690, 0.042, 0.032),
        (-0.50, 0.900, 0.590, 0.078, 0.055),
        (-0.40, 0.935, 0.560, 0.104, 0.072),
        (-0.28, 0.930, 0.590, 0.108, 0.072),
        (-0.14, 0.922, 0.630, 0.100, 0.068),
        (0.00, 0.935, 0.565, 0.112, 0.070),
        (0.13, 0.962, 0.515, 0.124, 0.066),
        (0.25, 0.990, 0.500, 0.126, 0.058),
        (0.35, 1.000, 0.505, 0.120, 0.052),
        (0.44, 0.935, 0.525, 0.104, 0.052),
        (0.52, 0.825, 0.555, 0.078, 0.044),
        (0.58, 0.720, 0.590, 0.044, 0.032),
    ],
    withers=(0.33, 1.0),
    neck_base=(0.38, 0.835),
    neck_angle=52.0,
    neck_len=0.29,
    neck=[(0.0, 0.104, 0.140, 0.160), (0.4, 0.098, 0.110, 0.135), (0.8, 0.094, 0.088, 0.108), (1.0, 0.090, 0.076, 0.090)],
    head_len=0.360,
    head_pitch=10.0,
    # the pariah type's wedge: a rounder skull, a defined stop, a shorter, broader muzzle than the wolf's
    head=[
        (0.00, 0.000, 0.056, 0.052, 0.064),
        (0.12, 0.008, 0.084, 0.072, 0.094),
        (0.28, 0.012, 0.090, 0.076, 0.104),
        (0.42, 0.008, 0.082, 0.068, 0.094),
        (0.53, -0.002, 0.068, 0.060, 0.080),
        (0.61, -0.020, 0.050, 0.052, 0.066),
        (0.75, -0.024, 0.046, 0.045, 0.058),
        (0.89, -0.026, 0.042, 0.039, 0.051),
        (1.00, -0.028, 0.031, 0.029, 0.037),
    ],
    jaw_hinge=(0.26, -0.058),
    jaw=[
        (0.18, 0.000, 0.028, 0.040, 0.074),
        (0.32, -0.004, 0.030, 0.038, 0.070),
        (0.52, -0.006, 0.026, 0.032, 0.058),
        (0.72, -0.004, 0.022, 0.025, 0.048),
        (0.90, 0.000, 0.018, 0.020, 0.038),
        (0.97, 0.002, 0.012, 0.014, 0.026),
    ],
    nose=(0.985, -0.020, 0.026),
    eye=(0.53, 0.040, 0.058, 0.0160),
    # erect, broad at the base, rounded tips (the Canaan standard)
    ear=(0.135, 0.125, 0.015),
    ear_base=(0.18, 0.056, 0.085),
    ear_splay=24.0,
    ear_tilt=4.0,
    ear_cup=0.40,
    canine=(0.82, -0.058, 0.028, 0.024, 0.0066),
    shoulder=(0.46, 0.640, 0.080),
    hip=(-0.36, 0.700, 0.070),
    fore_bones=(0.27, 0.30, 0.11),
    hind_bones=(0.29, 0.30, 0.17),
    forepaw=(0.135, 0.092, 0.052),
    hindpaw=(0.125, 0.085, 0.050),
    stance=dict(fore=dict(x=0.33, y=0.074, meta=15.0), hind=dict(x=-0.48, y=0.068, meta=8.0)),
    tail_base=(-0.540, 0.860),
    tail_len=0.55,
    # carried up and curled over the back when alert (the pariah type's sickle tail)
    tail_hang=[-50, -78, -110, -150, -180],
    tail_r=[(0.0, 0.030, 0.032), (0.25, 0.046, 0.048), (0.55, 0.050, 0.050), (0.80, 0.038, 0.038), (0.93, 0.024, 0.024),
            (1.0, 0.008, 0.008)],
    # the collar: at this place along the neck, its distance off the coat, width and thickness (mm)
    collar=(0.42, 2.0, 26.0, 4.0),
)
# fuller than the wolf: the pariah type's 'moderately broad and deep' chest and 18-25 kg on a 50-60 cm dog (the
# first build, at the widths above, came to 18.6 L before its coat: too light); the muzzle a wedge, not a sighthound's
DOG['torso'] = [(x, top, bot - 0.008 * (x > -0.2), w * 1.16, wl * 1.22) for x, top, bot, w, wl in DOG['torso']]
DOG['fore_sizes'] = {k: (w * 1.10, f * 1.08, b * 1.08) for k, (w, f, b) in DOG['fore_sizes'].items()}
DOG['hind_sizes'] = {k: (w * 1.10, f * 1.08, b * 1.08) for k, (w, f, b) in DOG['hind_sizes'].items()}
DOG['shoulder'] = (0.46, 0.640, 0.078)
DOG['hip'] = (-0.36, 0.700, 0.070)
DOG['stance'] = dict(fore=dict(x=0.33, y=0.080, meta=15.0), hind=dict(x=-0.47, y=0.074, meta=10.0))

DOG_POSES = {
    'alert': dict(neck=55, head=8),
    # lying at rest by the pen, on its chest (sternal), head up, forelegs out in front, hind legs folded beside it
    'lie': dict(drop=0.47, pitch=-2, neck=36, head=14, tail=[(72, 0), (84, 25), (12, 80), (0, 125), (0, 150)],
                legs=dict(fore_l=dict(x=0.78, y=0.085, meta=86, paw=0, n=(0, 0, 1), pole=(-1, 0, -0.2), root=(0.0, 0.13)),
                          fore_r=dict(x=0.74, y=0.080, meta=86, paw=0, n=(0, 0, 1), pole=(-1, 0, -0.2), root=(0.0, 0.13)),
                          hind_l=dict(x=-0.20, y=0.150, meta=86, paw=4, paw_y=0.0, n=(0, 0, 1), pole=(1, 0.5, 0.1), meta_y=0.0),
                          hind_r=dict(x=-0.22, y=0.150, meta=86, paw=4, n=(0, 0, 1), pole=(1, 0.5, 0.1)))),
    # barking at something: weight forward, forelegs braced ahead, head out level, mouth open, ears forward
    'bark': dict(drop=0.04, pitch=-5, neck=30, head=2, jaw=26,
                 legs=dict(fore_l=dict(x=0.47, meta=8), fore_r=dict(x=0.44, meta=10),
                           hind_l=dict(x=-0.56, meta=12), hind_r=dict(x=-0.52, meta=10))),
}

# the stray: the same body as the guard dog, another coat; wary, tail low, no collar
STRAY_POSES = {
    'alert': dict(neck=40, head=20, tail=[62, 75, 82, 84, 84], collar=False),
    'bark': dict(DOG_POSES['bark'], tail=[30, 50, 66, 74, 78], collar=False, ears_back=10),
}

# the stray's body: the guard dog's build in poor condition (a game choice of how thin): the loin and belly tucked up,
# the loin's girth about 12% under the dog's, the neck thinner, the hip bones' points and the spine showing
STRAY = dict(DOG)
STRAY['condition'] = 0.86


def _thin(rows):
    out = []
    for x, top, bot, w, wl in rows:
        k = max(0.0, 1.0 - abs(x + 0.12) / 0.30)          # most at the loin, none at the chest or the croup
        out.append((x, top - 0.006 * k, bot + 0.055 * k, w * (1 - 0.14 * k), wl * (1 - 0.14 * k)))
    return out


STRAY['torso'] = _thin(DOG['torso'])
STRAY['neck'] = [(f, w * 0.90, c * 0.92, t * 0.92) for f, w, c, t in DOG['neck']]

SPECIES = {'wolf': (WOLF, WOLF_POSES), 'dog': (DOG, DOG_POSES), 'stray': (STRAY, STRAY_POSES)}
COAT = {}

# the winter coat, for the owner to compare (not one of the delivered files): longer guard hairs on the neck, shoulders
# and back, a fuller tail, the body a little fuller; Arabian wolves' winter coat is longer than their summer one but
# far shorter than northern wolves' (README.md). The amounts are a game choice.
WOLF_WINTER = dict(WOLF)
WOLF_WINTER.update(
    name='wolf_winter',
    torso=[(x, top + 0.012 * (x > -0.5), bot - 0.006, w * 1.06, wl * 1.06) for x, top, bot, w, wl in WOLF['torso']],
    neck=[(f, w * 1.18, c * 1.22, t * 1.25) for f, w, c, t in WOLF['neck']],
    tail_r=[(f, w * 1.35, d * 1.35) for f, w, d in WOLF['tail_r']],
)
SPECIES['wolf_winter'] = (WOLF_WINTER, {'alert': WOLF_POSES['alert']})

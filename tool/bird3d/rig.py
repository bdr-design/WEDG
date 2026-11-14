"""The birds' skeletons, skin weights and clips (task T17).

    python rig.py OUT saker            # OUT/saker_rig.glb: both meshes, the hood, the jesses, the skeleton, the clips
    python rig.py OUT saker sheets     # and a contact sheet of each clip (JPEG)

A bird is built by bird.py in a rest pose (the body level, the legs down, the toes flat), once with the wings folded
and once spread. Both meshes are skinned to one skeleton; the game shows the folded mesh while the bird sits and
the spread one while it flies, and swaps them at a frame each clip names (README.md). Weights are given by code from
what each piece is (the body by its place along the centre line, a wing by its span, a toe by its length), at most
two bones a vertex. The clips are posed frame by frame: the body as a rigid transform, the neck and head by turns
that keep the head level, the legs solved so the feet stay where the clip puts them, the toes curled onto the
support, the jesses by a small cord simulation.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

import bird  # noqa: E402
import common  # noqa: E402
from common import V3, smooth_path, tube  # noqa: E402

FPS = 30
MM = 0.001
# the falcon this run builds: the saker, or the peregrine on the same skeleton and clips (its own numbers in RIG)
BIRD = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in ('saker', 'peregrine') else 'saker'
import importlib  # noqa: E402
SP = importlib.import_module(BIRD)
RIG = getattr(SP, 'RIG', {})


# ------------------------------------------------------------------ the saker's rest meshes, tagged
def saker_rest(wings, level=0):
    """The saker in the rest pose: body level (its tail base at the origin), the feet below, toes flat. Returns
    {'body': [(piece, tag)], 'hood': [...], 'jesses': [...]}, the named points (mm) and the body."""
    saker = SP
    pose = dict(saker.POSES['flight'])
    pose.update({'wings': wings, 'tucked': False, 'foot': RIG.get('rest_foot', (75, 22, -125)), 'foot_turn': 8, 'tail_droop': 0,
                 'tail_spread': 1.0, 'wing_dihedral': 0.0, 'fluff': 1.05})      # as the approved perched birds
    det = bird.Detail(level)
    body = bird.Body(saker.stations(pose), pose, det, head_weight=2.0)
    spec = saker.SPEC
    out = {'body': [(body.piece(det), ('body',))]}
    out['body'] += [(p, ('head',)) for p in bird.beak(body, spec, det) + bird.eyes(body, spec, det)]
    if wings == 'fold':
        fw = bird.folded_wing(body, spec, det)
        out['body'] += [(fw[0], ('fold', 1)), (fw[1], ('fold', -1))]
    else:
        ow = bird.open_wing(body, spec, det, pose)
        out['body'] += [(ow[0], ('wing', 1)), (ow[1], ('wing', -1))]
    out['body'] += [(p, ('tail',)) for p in bird.tail(body, spec, pose, det)]
    leg, pts = bird.legs(body, spec, pose, det)
    for i, side in enumerate((1, -1)):
        out['body'].append((leg['shank'][i], ('shank', side)))
        out['body'].append((leg['tarsus'][i], ('tarsus', side)))
        nt = len(spec['toes'])
        for k in range(nt):
            hind = abs(spec['toes'][k][0]) == 180
            out['body'].append((leg['toes'][i * nt + k], ('toe', side, k)))
            out['body'].append((leg['claws'][i * nt + k], ('claw', side, k)))
    out['hood'] = [(p, ('hood',)) for p in saker.hood(body, det)]
    out['jesses'] = rest_jesses(pts, det)
    return out, pts, body


TOE_NAMES = ('toeM', 'toeI', 'toeO', 'toeH')
JESS_N = 5
TOE_WHY = ('middle toe', 'inner toe', 'outer toe', 'hind toe')
JESS_LEN = 150.0      # mm from the anklet to the swivel (the reviewer's 15-20 cm; Gulf cords about 30 cm folded)


def rest_jesses(pts, det):
    """Each jess hanging straight down from its anklet to the swivel; the swivel on the left cord's end."""
    out = []
    cord = 1.9
    for side, key in ((1, 'l'), (-1, 'r')):
        a = pts['tarsus_' + key]
        axis = (pts['foot_' + key] - pts['ankle_' + key]).normalized()
        u, v = bird.frame(axis, V3((1, 0, 0)))
        ring = [a + (u * math.cos(2 * math.pi * k / 12) + v * math.sin(2 * math.pi * k / 12)) * 7.4 for k in range(12)]
        out.append((bird.loop_tube('cord', ring, cord, 5 if det.level == 0 else 4, axis), ('anklet', side)))
        start = a + u * 7.4
        n = 13 if det.level == 0 else 6
        path = [start + V3((0, -side * 2.0 * f, -JESS_LEN * f)) for f in np.linspace(0, 1, n)]
        out.append((tube('cord', path, [cord] * n, 5 if det.level == 0 else 4, up=V3((1, 0, 0))), ('jess', side, start)))
    end = path[-1]
    ring = [end + V3((math.cos(2 * math.pi * k / 10) * 6, 0, math.sin(2 * math.pi * k / 10) * 6 - 6)) for k in range(10)]
    out.append((bird.loop_tube('steel', ring, 1.3, 4, V3((0, 1, 0))), ('swivel', -1)))
    return out


# ------------------------------------------------------------------ the skeleton
def saker_bones(pts, body):
    """Bone heads and tails in the rest pose (mm), parents, and why each exists."""
    o = bird.torso(body)[0]
    tp = lambda x, z, y=0.0: bird.torso_point(body, x, z, y)
    B = {}

    def add(name, head, tail, parent, why):
        B[name] = (V3(head), V3(tail), parent, why)
    feet = (pts['foot_l'] + pts['foot_r']) / 2
    add('root', feet, feet + V3((0, 0, 40)), None, 'where the bird stands: moves it through the world')
    add('body', tp(80, -10), tp(180, 0), 'root', 'the torso: pitch, roll and bob')
    n0, n1, n2 = RIG.get('neck', (178, 212, 240))
    he, hd = RIG.get('head_end', 292), RIG.get('hood_d', 252)
    tr, tt = RIG.get('tail', (20, -205))
    add('neck1', body.at(n0), body.at(n1), 'body', 'the lower neck: with neck2 keeps the head level as the body tilts')
    add('neck2', body.at(n1), body.at(n2), 'neck1', 'the upper neck')
    add('head', body.at(n2), body.at(he), 'neck2', 'the head: looks around; carries beak, eyes and hood')
    add('hood', body.at(hd) + V3((0, 0, 20)), body.at(hd) + V3((0, 0, 50)), 'head', 'the hood: lifted off and set on')
    add('tail', tp(tr, 3), tp(tt, 3), 'body', 'the tail: lifts and drops')
    add('tail.L', tp(tr, 3, 6), tp(tt, 3, 18), 'tail', 'the tail\'s left feathers: fan out')
    add('tail.R', tp(tr, 3, -6), tp(tt, 3, -18), 'tail', 'the tail\'s right feathers: fan out')
    (f0x, f0z, f0y), (f1x, f1z, f1y), (f2x, f2z, f2y) = RIG.get('fold', ((160, 25, 52), (40, 22, 45), (-135, 12, 10)))
    (w0x, w0z, w0y), (w1x, w1z, w1y), (w2x, w2z, w2y), (w3x, w3z, w3y) = RIG.get('wing', ((130, 8, 30), (130, 8, 120), (125, 8, 215), (40, 0, 600)))
    kx, kz, ky = RIG.get('knee', (95, -20, 20))
    for side, s in ((1, 'L'), (-1, 'R')):
        add(f'fold.{s}', tp(f0x, f0z, f0y * side), tp(f1x, f1z, f1y * side), 'body',
            'the folded wing (folded mesh only): lifts, droops, opens before the swap')
        add(f'fold_tip.{s}', tp(f1x, f1z, f1y * side), tp(f2x, f2z, f2y * side), f'fold.{s}',
            'the folded wing\'s primaries (folded mesh only): swing out as the wing opens, so the swap matches')
        add(f'wing_up.{s}', tp(w0x, w0z, w0y * side), tp(w1x, w1z, w1y * side), 'body', 'the arm (humerus): the wingbeat')
        add(f'wing_fore.{s}', tp(w1x, w1z, w1y * side), tp(w2x, w2z, w2y * side), f'wing_up.{s}', 'the forearm: the fold at the elbow')
        add(f'wing_hand.{s}', tp(w2x, w2z, w2y * side), tp(w3x, w3z, w3y * side), f'wing_fore.{s}', 'the hand and primaries: the fold at the wrist, the upstroke flick')
        k = 'l' if side > 0 else 'r'
        knee = tp(kx, kz, ky * side)
        add(f'shank.{s}', knee, pts['ankle_' + k], 'body', 'the shank (tibia, the trousers): the leg reaches and tucks')
        add(f'tarsus.{s}', pts['ankle_' + k], pts['foot_' + k], f'shank.{s}', 'the tarsus: with the shank holds the foot planted')
        f = pts['foot_' + k]
        for ti, (hd_, length, r, claw, curl) in enumerate(SP.SPEC['toes']):
            a = math.radians((hd_ * side if abs(hd_) != 180 else hd_) + 8 * side)
            dv = V3((math.cos(a), math.sin(a), 0))
            nm = TOE_NAMES[ti]
            j = length * 0.5
            add(f'{nm}1.{s}', f + dv * -2, f + dv * j, f'tarsus.{s}', f'the {TOE_WHY[ti]}, first joint: each toe lies on the cuff its own way')
            add(f'{nm}2.{s}', f + dv * j, f + dv * (length - 2), f'{nm}1.{s}', f'the {TOE_WHY[ti]}, last joints and talon: curl and hook in')
        a = pts['tarsus_' + k] + V3((7.4, 0, 0))
        for j in range(JESS_N):
            add(f'jess{j + 1}.{s}', a + V3((0, 0, -JESS_LEN * j / JESS_N)), a + V3((0, 0, -JESS_LEN * (j + 1) / JESS_N)),
                f'tarsus.{s}' if j == 0 else f'jess{j}.{s}', 'a fifth of the jess: the cord sags, swings and trails')
    return B


def smooth01(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def blend(a, b, t):
    """Two bones' weights: t=0 all a, t=1 all b."""
    t = smooth01(t)
    if t <= 0.0:
        return {a: 1.0}
    if t >= 1.0:
        return {b: 1.0}
    return {a: 1.0 - t, b: t}


def weights_for(pc, tag, body, B):
    """Per vertex {bone: weight} for a tagged piece."""
    kind = tag[0]
    side = tag[1] if len(tag) > 1 and isinstance(tag[1], int) else 1
    s = 'L' if side > 0 else 'R'
    W = []
    if kind == 'body':
        d_st = np.array(body.d)
        cs = np.array([tuple(sec.c) for sec in body.secs])
        for q in pc.V:
            i = int(np.argmin(((cs - np.array(tuple(q))) ** 2).sum(1)))
            d = d_st[i]
            b0, b1, b2, b3 = RIG.get('body_bands', (170, 205, 230, 255))
            if d < b0:
                W.append({'body': 1.0})
            elif d < b1:
                W.append(blend('body', 'neck1', (d - b0) / (b1 - b0)))
            elif d < b2:
                W.append(blend('neck1', 'neck2', (d - b1) / (b2 - b1)))
            elif d < b3:
                W.append(blend('neck2', 'head', (d - b2) / (b3 - b2)))
            else:
                W.append({'head': 1.0})
        return W
    if kind in ('head',):
        return [{'head': 1.0} for _ in pc.V]
    if kind == 'hood':
        return [{'hood': 1.0} for _ in pc.V]
    if kind == 'tail':
        root = B['tail'][0]
        out = []
        for q in pc.V:
            along = (root.x - q.x) / 40.0
            if along < 1.0:
                out.append(blend('body', 'tail', along))
            else:
                out.append(blend('tail', 'tail.L' if q.y > 0 else 'tail.R', (abs(q.y) - 4) / 22.0))
        return out
    if kind == 'fold':
        out = []
        for q in pc.V:
            if q.x > 120:
                out.append(blend('body', f'fold.{s}', (175 - q.x) / 40.0))
            else:
                out.append(blend(f'fold.{s}', f'fold_tip.{s}', (70 - q.x) / 60.0))
        return out
    if kind == 'wing':
        out = []
        k_ = RIG.get('wing_scale', 1.0)      # the bands follow the wrist (the saker's at 215 mm)
        for q in pc.V:
            y = abs(q.y) / k_
            if y < 60:
                out.append(blend('body', f'wing_up.{s}', (y - 30) / 30))
            elif y < 160:
                out.append(blend(f'wing_up.{s}', f'wing_fore.{s}', (y - 95) / 60))      # a wide band at the elbow
            else:
                out.append(blend(f'wing_fore.{s}', f'wing_hand.{s}', (y - 172) / 76))   # and at the wrist
        return out
    if kind == 'shank':
        knee, ankle = B[f'shank.{s}'][0], B[f'shank.{s}'][1]
        L = (ankle - knee).length
        return [blend('body', f'shank.{s}', ((q - knee).dot((ankle - knee).normalized())) / (0.35 * L)) for q in pc.V]
    if kind in ('tarsus', 'anklet'):
        return [{f'tarsus.{s}': 1.0} for _ in pc.V]
    if kind in ('toe', 'claw'):
        nm = TOE_NAMES[tag[2]]
        b1, b2 = f'{nm}1.{s}', f'{nm}2.{s}'
        if kind == 'claw':
            return [{b2: 1.0} for _ in pc.V]
        h = B[b1][0]
        axis = (B[b1][1] - h).normalized()
        L = (B[b1][1] - h).length
        return [blend(b1, b2, ((q - h).dot(axis) - L * 0.85) / (L * 0.3)) for q in pc.V]
    if kind == 'jess':
        start = tag[2]
        out = []
        for q in pc.V:
            f = (start.z - q.z) / JESS_LEN * JESS_N       # 0..JESS_N along the cord
            j = min(int(f), JESS_N - 1)
            t = f - j
            if t > 0.75 and j < JESS_N - 1:
                out.append(blend(f'jess{j + 1}.{s}', f'jess{j + 2}.{s}', (t - 0.75) / 0.5))
            elif t < 0.25 and j > 0:
                out.append(blend(f'jess{j}.{s}', f'jess{j + 1}.{s}', (t + 0.25) / 0.5))
            else:
                out.append({f'jess{j + 1}.{s}': 1.0})
        return out
    if kind == 'swivel':
        return [{f'jess{JESS_N}.R': 1.0} for _ in pc.V]
    raise ValueError(kind)


def skinned_mesh(name, tagged, body, B, atlas, mat, arm):
    pieces = [p for p, t in tagged]
    me = common.to_mesh(name, pieces, atlas)
    o = common.obj(name, me, mat, arm)
    groups = {}
    vi = 0
    for pc, tag in tagged:
        for w in weights_for(pc, tag, body, B):
            for bname, val in sorted(w.items()):
                g = groups.get(bname)
                if g is None:
                    g = groups[bname] = o.vertex_groups.new(name=bname)
                g.add([vi], val, 'REPLACE')
            vi += 1
    mod = o.modifiers.new('arm', 'ARMATURE')
    mod.object = arm
    return o


def make_armature(name, B):
    arm_d = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new(name, arm_d)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = {}
    for bname in B:      # insertion order: parents first
        h, t, parent, why = B[bname]
        b = arm_d.edit_bones.new(bname)
        b.head, b.tail = h * MM, t * MM
        b.roll = 0.0
        if parent:
            b.parent = eb[parent]
        b.use_connect = False
        eb[bname] = b
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


# ------------------------------------------------------------------ posing
class Poser:
    """Sets one frame's pose: rigid transforms for the root and body, turns for the rest, solved legs and toes."""

    def __init__(self, arm):
        self.arm = arm
        self.pb = arm.pose.bones
        self.rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        for p in self.pb:
            p.rotation_mode = 'QUATERNION'

    def reset(self):
        for p in self.pb:
            p.location = (0, 0, 0)
            p.rotation_quaternion = (1, 0, 0, 0)
            p.scale = (1, 1, 1)

    def turn(self, bone, axis, deg):
        """Turn [bone] about its head by [deg] about [axis] given in the rest frame (armature space)."""
        R = self.rest[bone].to_3x3()
        q = Quaternion(R.inverted() @ V3(axis).normalized(), math.radians(deg))
        p = self.pb[bone]
        p.rotation_quaternion = p.rotation_quaternion @ q

    def place(self, bone, world):
        """The bone's armature-space matrix set to [world] @ its rest matrix (a rigid transform of its segment)."""
        bpy.context.view_layer.update()
        self.pb[bone].matrix = world @ self.rest[bone]

    def aim(self, bone, target_mm):
        """Turn [bone] so its tail points at the target (mm, armature space), keeping its twist."""
        bpy.context.view_layer.update()
        p = self.pb[bone]
        M = p.matrix.copy()
        head = M.translation
        cur = (M.to_3x3() @ V3((0, 1, 0))).normalized()
        want = (V3(target_mm) * MM - head).normalized()
        r = cur.rotation_difference(want).to_matrix().to_4x4()
        M2 = Matrix.Translation(head) @ r @ Matrix.Translation(-head) @ M
        p.matrix = M2

    def head_of(self, bone):
        bpy.context.view_layer.update()
        return self.pb[bone].matrix.translation / MM

    def tail_of(self, bone):
        bpy.context.view_layer.update()
        p = self.pb[bone]
        return (p.matrix @ V3((0, p.bone.length, 0))) / MM

    def leg(self, s, foot_mm, pole=V3((-1, 0, 0))):
        """Solve shank and tarsus so the foot lands on foot_mm (armature space), the ankle bent toward [pole]."""
        knee = self.head_of(f'shank.{s}')
        l1 = self.pb[f'shank.{s}'].bone.length / MM
        l2 = self.pb[f'tarsus.{s}'].bone.length / MM
        ankle = bird.two_bone(knee, V3(foot_mm), l1, l2, V3(pole))
        self.aim(f'shank.{s}', ankle)
        self.aim(f'tarsus.{s}', foot_mm)

    def key(self, frame, skip=()):
        for p in self.pb:
            if p.name in skip:
                continue
            p.keyframe_insert('rotation_quaternion', frame=frame)
            p.keyframe_insert('location', frame=frame)
            p.keyframe_insert('scale', frame=frame)


def rigid(pitch_deg=0.0, roll_deg=0.0, yaw_deg=0.0, at=(0, 0, 0), pivot=(0, 0, 0)):
    """A rigid transform (mm): turn about [pivot] (pitch: nose up positive), then move by [at]."""
    R = (Matrix.Rotation(math.radians(yaw_deg), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch_deg), 4, 'Y')
         @ Matrix.Rotation(math.radians(roll_deg), 4, 'X'))
    pv = V3(pivot) * MM
    return Matrix.Translation(V3(at) * MM) @ Matrix.Translation(pv) @ R @ Matrix.Translation(-pv)


class Cord:
    """A jess as a chain of points (verlet): pinned at the anklet, pulled by gravity and by the air the bird
    flies through. Points in mm, armature space."""

    def __init__(self, start, n=JESS_N + 1, length=JESS_LEN):
        self.seg = length / (n - 1)
        self.p = [V3(start) + V3((0, 0, -self.seg * i)) for i in range(n)]
        self.q = [x.copy() for x in self.p]

    def step(self, anchor, air, dt=1.0 / FPS, sub=4, end=None):
        g = V3((0, 0, -9810.0))
        for _ in range(sub):
            h = dt / sub
            self.p[0] = V3(anchor)
            if end is not None:
                self.p[-1] = V3(end)
            for i in range(1, len(self.p)):
                v = (self.p[i] - self.q[i]) * 0.92
                self.q[i] = self.p[i].copy()
                drag = (V3(air) - v / h) * 0.5 * h      # pulled toward moving with the air
                self.p[i] = self.p[i] + v + (g * h * h) + drag * h * 5
            for _ in range(4):
                self.p[0] = V3(anchor)
                if end is not None:
                    self.p[-1] = V3(end)
                for i in range(1, len(self.p)):
                    d = self.p[i] - self.p[i - 1]
                    L = d.length or 1e-6
                    corr = d * ((L - self.seg) / L)
                    if i == 1:
                        self.p[i] = self.p[i] - corr
                    elif end is not None and i == len(self.p) - 1:
                        self.p[i - 1] = self.p[i - 1] + corr
                    else:
                        self.p[i - 1] = self.p[i - 1] + corr * 0.5
                        self.p[i] = self.p[i] - corr * 0.5
        return self.p


# ------------------------------------------------------------------ the saker's clips
def lerp(a, b, t):
    return a + (b - a) * t


def ramp(f, f0, f1):
    """0 before f0, 1 after f1, eased between."""
    return smooth01((f - f0) / max(f1 - f0, 1e-6))


def keys(f, pts):
    """A value eased through [(frame, value)...]."""
    if f <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f <= f1:
            return lerp(v0, v1, smooth01((f - f0) / (f1 - f0)))
    return pts[-1][1]


def spline(f, pts):
    """A value through [(frame, value)...] with a continuous speed (monotone cubic, Fritsch-Carlson)."""
    if f <= pts[0][0]:
        return pts[0][1]
    if f >= pts[-1][0]:
        return pts[-1][1]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(len(xs) - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 2 / (1 / d[i - 1] + 1 / d[i]) for i in range(1, len(d))] + [d[-1]]
    i = max(j for j in range(len(xs) - 1) if xs[j] <= f)
    h = xs[i + 1] - xs[i]
    t = (f - xs[i]) / h
    return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[i] + (t ** 3 - 2 * t ** 2 + t) * h * m[i]
            + (-2 * t ** 3 + 3 * t ** 2) * ys[i + 1] + (t ** 3 - t ** 2) * h * m[i + 1])


PERCH_TB = V3((SP.POSES['hooded']['origin'][0], 0, SP.POSES['hooded']['origin'][1]))      # the tail base when perched (the approved static's)
STOOP_TWIST = 10.0
# the landing's path (the body's centre against where it is at contact, mm, by frame): across from the right, low,
# up past the fist's side, over it, down onto it (game choices, measured clear of the cuff and forearm by the build)
LAND_Y = [(0, -3000), (12, -900), (18, -420), (22, -300), (25, -150), (28, 0)]
LAND_Z = [(0, -150), (8, -300), (14, -260), (19, -60), (23, 90), (26, 60), (28, 0)]
LAND_X = [(0, 0), (28, 0)]
PLANTED = ('cuff', 'perch', 'ground')
PERCH_NECK = RIG.get('perch_neck', (14, -32, -40))      # neck1, neck2, head turns that put the perched frame on the static <bird>_fist.glb
PERCH_TAIL = RIG.get('perch_tail', 10)                  # the tail's lift, the same fit
SWAP_FOLD = RIG.get('swap_fold', {'out': 8, 'up': 50, 'twist': 0, 'tip_out': 10, 'tip_up': -28})      # the folded mesh at the swap (tuned at cast_off's frame 13)
SWAP_OPEN = RIG.get('swap_open', {'up': -5, 'sweep': 65, 'fore': -80, 'hand': 170, 'twist': 0})      # the spread wing at the swap (overlap 0.898 with SWAP_FOLD, side and three-quarter)
STOOP_WING = dict(SWAP_OPEN, twist=STOOP_TWIST)      # the stoop's drawn-in wing: the swap's outline, the wing turned a little leading edge down (fewest forearm and hand vertices inside the flank of those tried)
FRAMES_FEET = {}
HIDDEN_FEET = {}      # per frame: the feet meant drawn up out of sight (not reaching for the cuff or the quarry)
BODY = []
CUFF_LIFT = 10.0      # on the rounded cuff, higher: the tarsus' end clear of the thumb's bulge
FOOT_LIFT = 4.0      # mm: the foot's centre held this far above the support under it, so the soles' pads rest on it


def flat_surface(x, y):
    """The perch's padded top and the ground: flat at the feet's level."""
    return 0.0      # the tail base when perched (the static saker_fist's pose: body pitch 66)


class Heightmap:
    """The top surface of a closed mesh (the cuff as exported), sampled on a millimetre grid: z = f(x, y), the
    highest face above each point; None-like (very low) off the mesh."""

    def __init__(self, pieces, x0=-115, x1=70, y0=-60, y1=60, step=1.0):
        self.x0, self.y0, self.step = x0, y0, step
        nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
        H = np.full((ny, nx), -1e6)
        for pc in pieces:
            P = np.array([tuple(v) for v in pc.V])
            for a, b, c in pc.T:
                A, B, Cc = P[a], P[b], P[c]
                n = np.cross(B - A, Cc - A)
                if n[2] <= 1e-9:
                    continue      # only faces looking up make the top
                lo = np.floor((np.minimum(np.minimum(A, B), Cc)[:2] - (x0, y0)) / step).astype(int)
                hi = np.ceil((np.maximum(np.maximum(A, B), Cc)[:2] - (x0, y0)) / step).astype(int)
                lo = np.maximum(lo, 0)
                hi = np.minimum(hi, (nx - 1, ny - 1))
                if (hi < lo).any():
                    continue
                gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
                px, py = x0 + gx * step, y0 + gy * step
                d = (B[1] - Cc[1]) * (A[0] - Cc[0]) + (Cc[0] - B[0]) * (A[1] - Cc[1])
                if abs(d) < 1e-12:
                    continue
                l1 = ((B[1] - Cc[1]) * (px - Cc[0]) + (Cc[0] - B[0]) * (py - Cc[1])) / d
                l2 = ((Cc[1] - A[1]) * (px - Cc[0]) + (A[0] - Cc[0]) * (py - Cc[1])) / d
                l3 = 1 - l1 - l2
                ok = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
                z = l1 * A[2] + l2 * B[2] + l3 * Cc[2]
                cur = H[gy, gx]
                H[gy, gx] = np.where(ok & (z > cur), z, cur)
        self.H = H

    def __call__(self, x, y):
        fx, fy = (x - self.x0) / self.step, (y - self.y0) / self.step
        ix, iy = int(math.floor(fx)), int(math.floor(fy))
        if ix < 0 or iy < 0 or ix + 1 >= self.H.shape[1] or iy + 1 >= self.H.shape[0]:
            return -1e6
        tx, ty = fx - ix, fy - iy
        h = self.H[iy:iy + 2, ix:ix + 2]
        if (h < -1e5).any():
            return float(h.max())
        return float(h[0, 0] * (1 - tx) * (1 - ty) + h[0, 1] * tx * (1 - ty) + h[1, 0] * (1 - tx) * ty + h[1, 1] * tx * ty)


class SakerClips:
    """Each clip returns, for a frame, a dict the poser applies. Distances mm, angles degrees."""

    def __init__(self):
        import gear
        self.cuff = Heightmap(gear.dass(0))
        self.beat = 7          # frames a wingbeat at 30 fps: 4.29 Hz (Pennycuick 1996 predicts 4.3-4.8 Hz)

    # the shared pieces of a pose
    def perched_rest(self, surf):
        """The one perched pose every clip that starts or ends perched shares."""
        return {'pitch': 66.0, 'tb': PERCH_TB, 'feet': surf, 'mesh': 'fold', 'jess_hold': surf == 'cuff'}

    def perched(self, f, pitch=66.0, crouch=0.0, feet='cuff'):
        """The approved perched pose (the static saker_fist's: body 66 degrees; the neck, head and tail turns fitted
        to it), lowered and leaned forward by [crouch]."""
        tb = PERCH_TB + V3((14 * crouch, 0, -34 * crouch))
        k = 1.0 - crouch
        neck = tuple(lerp(a, b, crouch) for a, b in zip(PERCH_NECK, (0, -20, -10)))
        return {'pitch': pitch - 26 * crouch, 'tb': tb, 'feet': feet, 'mesh': 'fold', 'neck': neck,
                'tail_lift': PERCH_TAIL * k}

    def wings_flap(self, ph, amp=40.0, mean=5.0):
        """The wingbeat: ph 0..1 (0 the top of the upstroke). The arm sweeps up and down; on the upstroke the wing
        flexes at the elbow and wrist (the hand drawn back and in, its tip trailing) and the hand turns its leading
        edge up (supinates); on the downstroke the wing is fully spread and the hand turns its leading edge down."""
        up = mean + amp * math.cos(2 * math.pi * ph)
        down = math.sin(2 * math.pi * ph)        # positive in the downstroke
        flex = max(0.0, -down) ** 0.8            # the upstroke
        return {'up': up, 'sweep': 18 * flex, 'fore': -72 * flex, 'hand': 118 * flex, 'twist': 6 * down,
                'hand_up': 22 * flex - 6 * max(0.0, down), 'hand_twist': 16 * down - 10 * flex}

    HALF_FOLD = {'up': 26, 'sweep': 52, 'fore': -78, 'hand': 92, 'twist': 0, 'hand_up': 0, 'hand_twist': 0}
    RAISED = {'up': 62, 'sweep': 22, 'fore': -14, 'hand': 16, 'twist': 0, 'hand_up': 8, 'hand_twist': 0}

    def cast_off(self, f):
        """The lean and crouch on the fist (4-13) while the folded wings open at the shoulder and the primaries swing
        out (SWAP_FOLD by 13); at 14 the spread mesh in the same outline (SWAP_OPEN), opened by its bones to the
        raised wings (18); the first downstroke from 18 with the push of the legs; the feet leave at 20, trail two
        frames, then close and draw up out of sight by 24; she drops below the fist in her first beats (to about
        190 mm under it at 30) and then climbs away. The drop and the speeds are game choices."""
        crouch = ramp(f, 4, 13)
        if f < 14:
            p = self.perched(f, crouch=crouch)
            k = ramp(f, 7, 13)
            p.update({'fold': {kk: v * k for kk, v in SWAP_FOLD.items()}, 'jess_hold': True, 'settle': 1 - ramp(f, 1, 5)})
            if f == 13:
                p['wing'] = dict(SWAP_OPEN)      # the hidden spread mesh already in the same outline
            return p
        if f < 18:
            k = ramp(f, 14, 18)
            w = {kk: lerp(SWAP_OPEN.get(kk, 0.0), self.RAISED[kk], k) for kk in self.RAISED}
        else:
            # three beats from 18: the clip's end (39) falls on the flight loop's frame 0, and the beat eases into
            # the loop's (amplitude 40, mean 5) over the last frames
            g = ramp(f, 30, 38)
            beat = self.wings_flap(((f - 18) / self.beat + 0.0) % 1.0, amp=lerp(46, 40, g), mean=lerp(4, 5, g))
            w = {kk: lerp(self.RAISED[kk], beat[kk], ramp(f, 18, 19.5)) for kk in self.RAISED}
        push = ramp(f, 16, 20)
        t = max(0.0, (f - 19) / FPS)
        td = max(0.0, t - 0.1)      # she drops only once her tail is clear of the fist
        x = 70 * push + 0.5 * 5.0 * t * t * 1000 + 1100 * t
        z = -10 * push - 0.5 * 3.6 * td * td * 1000 + 0.5 * 7.0 * max(0.0, td - 0.22) ** 2 * 1000
        pitch = keys(f, [(13, 40), (17, 34), (21, 22), (28, 12), (38, 4 + 2 * math.sin(2 * math.pi * (f - 18) / self.beat))])
        tb = PERCH_TB + V3((14, 0, -34)) + V3((x, 0, z))
        feet = 'cuff' if f < 20 else ('push', ramp(f, 21, 24))
        sp = {'pitch': pitch, 'tb': tb, 'feet': feet, 'mesh': 'open', 'wing': w, 'neck': (0, -20, -10) if f < 20 else None,
              'tail_spread': lerp(1.3, 1.05, ramp(f, 16, 38)), 'jess_hold': f < 20, 'clench': ramp(f, 21, 24),
              'tail_lift': keys(f, [(15, 0), (18, 26), (27, 26), (33, 0)]),      # the tail raised clear of the fist
              'air': V3((-(20000 - (1100 + 5000 * t)) * ramp(f, 24, 36), 0, 0)),
              'settle_to': 'flight', 'settle': ramp(f, 31, 38)}      # the cords' air eased to the flight loop's
        if sp['neck'] is None:
            del sp['neck']
        if f == 14:
            sp['fold'] = dict(SWAP_FOLD)
        return sp

    def flight(self, f):
        ph = (f / self.beat) % 1.0
        w = self.wings_flap(ph)
        bob = -8 * math.cos(2 * math.pi * ph)
        return {'pitch': 4 + 2 * math.sin(2 * math.pi * ph), 'tb': V3((0, 0, bob)), 'feet': ('free', 1.0), 'mesh': 'open',
                'wing': w, 'tail_spread': 1.05, 'clench': 1.0, 'air': V3((-20000, 0, 0))}

    LAND_CENTRE = V3((120.0, 0.0, 0.0))      # the body's centre ahead of the tail base (body frame): the path is its

    def land_place(self, f):
        """Where she is (the tail base) and her heading. From contact (28) on, on the support as before. Before: she
        comes in across the falconer's front from his right, low, under the fist's height (a falcon comes to the
        fist low and swings up to it; the side and the heights are game choices), turns a quarter to face along
        the fist as she flares, rises above it clear of the cuff and forearm, and drops onto it."""
        pitch = keys(f, [(0, 4), (12, 2), (20, 30), (26, 52), (31, 44), (38, 42), (45, 66)])
        tb_c = lambda g: PERCH_TB + V3((25, 0, -10)) * (1 - ramp(g, 26, 40))
        if f >= 28:
            return tb_c(f), pitch, 0.0
        yaw = spline(f, [(0, 90), (14, 88), (22, 40), (27, 0), (28, 0)])
        Rm = lambda p_, y_: (Matrix.Rotation(math.radians(y_), 3, 'Z') @ Matrix.Rotation(math.radians(-p_), 3, 'Y'))
        c28 = tb_c(28) + Rm(keys(28, [(26, 52), (31, 44)]), 0.0) @ self.LAND_CENTRE
        dy = spline(f, LAND_Y)
        dz = spline(f, LAND_Z)
        dx = spline(f, LAND_X)
        c = c28 + V3((dx, dy, dz))
        return c - Rm(pitch, yaw) @ self.LAND_CENTRE, pitch, yaw

    def land(self, f, surface):
        """In low across the falconer's front and a swing up to the fist (land_place); the flare (body up to 55
        degrees, the wings forward and beating to brake, the tail fanned), the legs thrown forward, contact at
        28; the wings raised and folded along the back by the bones to SWAP_OPEN (37), the swap to the folded mesh
        in the same outline at 38 (SWAP_FOLD), closed by 45, the perched pose."""
        tb_air, pitch, yaw = self.land_place(f)
        brake = ramp(f, 18, 22) * (1 - ramp(f, 27, 30))
        glide = {'up': 10, 'sweep': -4, 'fore': -6, 'hand': 10, 'twist': 0, 'hand_up': 0, 'hand_twist': -4}
        if f < 19:
            # beating down the slope, then the wings held spread on the swoop up (Harris' hawks to a perch:
            # KleinHeerenbrink et al. 2022, Nature, from summaries of it, not opened)
            fl = self.wings_flap((f / self.beat) % 1.0, amp=36, mean=5)
            k = ramp(f, 9, 13)
            w = {kk: lerp(fl.get(kk, 0.0), glide.get(kk, 0.0), k) for kk in set(fl) | set(glide)}
        else:
            b = self.wings_flap(((f - 19) / 6.0 + 0.75) % 1.0, amp=34, mean=14 + 10 * ramp(f, 20, 26))
            b = {kk: lerp(glide.get(kk, 0.0), b.get(kk, 0.0), ramp(f, 19, 20.5)) for kk in set(b) | set(glide)}
            b['sweep'] -= 22 * brake        # the wings brought forward to brake
            up_back = ramp(f, 28, 32) * (1 - ramp(f, 32, 37))
            raised = dict(self.RAISED, up=58, sweep=40)
            b = {k: lerp(b.get(k, 0.0), raised.get(k, 0.0), up_back) if f < 32 else b.get(k, 0.0) for k in set(b) | set(raised)}
            fold = ramp(f, 30, 37)
            w = {k: lerp(b.get(k, 0.0), SWAP_OPEN.get(k, 0.0), fold) for k in set(b) | set(SWAP_OPEN)}
        mesh = 'open' if f < 38 else 'fold'
        reach = ramp(f, 16, 24)
        feet = surface if f >= 28 else ('reach', reach)
        sp = {'pitch': pitch, 'yaw': yaw, 'tb': tb_air, 'feet': feet, 'mesh': mesh, 'wing': w,
              'tail_spread': lerp(1.0, 1.5, brake) if f < 32 else lerp(1.5, 1.0, ramp(f, 32, 42)),
              'tail_drop': 18 * brake, 'open_toes': reach * (1 - ramp(f, 27, 29))}
        if f >= 37:
            sp['fold'] = {kk: v * (1 - ramp(f, 38, 45)) for kk, v in SWAP_FOLD.items()}
        if surface == 'perch':
            sp['settle'] = ramp(f, 36, 45)
        elif f >= 38:
            sp['jess_take'] = ramp(f, 38, 43)      # on the fist: the falconer takes the jesses as she settles
            sp['settle'] = ramp(f, 41, 45)
        if f >= 40:
            sp.update({'neck': tuple(lerp(a, b, ramp(f, 40, 45)) for a, b in zip((20 * 42 / 66, -46 * 42 / 66, -40 * 42 / 66), PERCH_NECK)),
                       'tail_lift': PERCH_TAIL * ramp(f, 40, 45)})
        return sp

    def land_cuff(self, f):
        return self.land(f, 'cuff')

    def land_perch(self, f):
        return self.land(f, 'perch')

    def perch_idle(self, f):
        """Four seconds on the perch: small shifts of weight, a look to one side, then the other, a flick of the tail;
        it loops."""
        c = 2 * math.pi * f / 120.0
        yaw = keys(f, [(0, 0), (18, 0), (28, 38), (48, 38), (58, 0), (72, 0), (80, -32), (96, -32), (106, 0), (120, 0)])
        return {'pitch': 66 + 1.5 * math.sin(c), 'tb': PERCH_TB + V3((0, 0, 1.5 * math.sin(2 * c))), 'feet': 'perch',
                'mesh': 'fold', 'head_yaw': yaw, 'head_pitch': 4 * math.sin(3 * c), 'settle': 1.0,
                'tail_drop': -10 * math.exp(-((f - 90) / 2.5) ** 2), 'fold_lift': 2 * max(0.0, math.sin(c))}

    def perch_hooded(self, f):
        """Five seconds hooded (in the tent, the car, on the perch): she sits quieter than unhooded, as the hood is
        there to keep her calm (game choice from that purpose: no looking round, no tail flick): breathing, a
        slow small turn of the head toward a sound, back; it loops. The hood itself is not keyed (game state)."""
        c = 2 * math.pi * f / 150.0
        yaw = keys(f, [(0, 0), (40, 0), (55, 12), (85, 12), (100, 0), (150, 0)])
        return {'pitch': 66 + 0.8 * math.sin(3 * c), 'tb': PERCH_TB + V3((0, 0, 1.0 * math.sin(3 * c))), 'feet': 'perch',
                'mesh': 'fold', 'head_yaw': yaw, 'head_pitch': 1.5 * math.sin(c), 'settle': 1.0}

    def rouse(self, f):
        """The rouse: every contour feather raised at once (the morph 'fluff', 2-6), the whole bird shaken through
        for about half a second (roll and head at 7 Hz, the folded wings lifted, the tail fanned with it), then the
        plumage laid smooth again (24-32)."""
        sh = ramp(f, 7, 9) * (1 - ramp(f, 22, 25))
        osc = math.sin(2 * math.pi * (f - 7) * 7.0 / FPS)
        fl = ramp(f, 2, 6) * (1 - ramp(f, 24, 32))
        return {'pitch': 66 + 4 * fl, 'tb': PERCH_TB + V3((0, 0, 6 * fl)), 'feet': 'perch', 'mesh': 'fold',
                'roll': 14 * sh * osc, 'head_yaw': 28 * sh * math.sin(2 * math.pi * (f - 7) * 7.0 / FPS + 0.6),
                'fold_lift': 12 * fl + 5 * sh * abs(osc), 'tail_spread': 1.0 + 0.12 * fl + 0.25 * sh * abs(osc),
                'fluff': fl, 'settle': 1.0}

    def hood_off(self, f):
        """On the fist: the falconer draws the braces and lifts the hood off (the hand is not drawn); she looks round."""
        lift = 70 * ramp(f, 6, 16)
        yaw = keys(f, [(0, 0), (18, 0), (22, 30), (25, -18), (28, 0)])
        return {'pitch': 66, 'tb': PERCH_TB, 'feet': 'cuff', 'mesh': 'fold', 'hood': 1.0 if f < 17 else 0.0,
                'hood_lift': lift, 'head_yaw': yaw, 'head_pitch': 6 * ramp(f, 16, 20) * (1 - ramp(f, 24, 29)), 'jess_hold': True, 'settle': 1.0}

    def hood_on(self, f):
        lift = 70 * (1 - ramp(f, 8, 20))
        return {'pitch': 66, 'tb': PERCH_TB, 'feet': 'cuff', 'mesh': 'fold', 'hood': 1.0 if f >= 7 else 0.0,
                'hood_lift': lift, 'head_pitch': -4 * ramp(f, 4, 8) * (1 - ramp(f, 18, 24)), 'jess_hold': True, 'settle': 1.0}

    def glide(self, f):
        c = 2 * math.pi * f / 60.0
        w = {'up': 6 + 1.5 * math.sin(c), 'sweep': -2, 'fore': -6, 'hand': 8 + 2 * math.sin(2 * c), 'twist': 0,
             'hand_up': 2, 'hand_twist': -4}
        return {'pitch': 3, 'roll': 4 * math.sin(c), 'tb': V3((0, 0, 3 * math.sin(c))), 'feet': ('free', 1.0),
                'mesh': 'open', 'wing': w, 'tail_spread': 1.0, 'clench': 1.0, 'air': V3((-15000, 0, 0))}

    def stoop(self, f):
        """From the glide into the stoop: the spread mesh's wings drawn in by its bones to the tightest outline that
        still reads right (SWAP_OPEN, by 12), the body tipped down 55 degrees, the head in line; held. No swap here:
        tried, the folded mesh matched the spread one at best 0.69 at this angle, a visible pop; `bind` starts from
        the same outline."""
        pitch = -55 * ramp(f, 0, 12) + 1.5 * math.sin(f / 2.0) * ramp(f, 0, 12)
        air = V3((-30000 * math.cos(math.radians(pitch)), 0, 30000 * math.sin(math.radians(-pitch))))
        g = self.glide(0)['wing']
        k = ramp(f, 0, 12)
        w = {kk: lerp(g.get(kk, 0.0), STOOP_WING.get(kk, 0.0), k) for kk in set(g) | set(STOOP_WING)}
        return {'pitch': pitch, 'head_pitch': 0.8 * pitch, 'tb': V3((0, 0, 0)), 'feet': ('free', 1.0), 'clench': 1.0,
                'air': air, 'tail_spread': 1.0, 'mesh': 'open', 'wing': w}

    def bind(self, f):
        """Binding to the quarry: thrown up from the dive, the wings braking, the legs and open feet struck forward;
        the feet close at frame 10 (on the quarry, not drawn), then heavy beats to hold."""
        pitch = keys(f, [(0, -55), (8, 38), (14, 30), (24, 20)])
        if f < 10:
            # from the stoop's end: the spread mesh in the swap's outline (SWAP_OPEN), opening to the brake
            r = {kk: lerp(STOOP_WING.get(kk, 0.0), self.RAISED[kk], ramp(f, 0, 4)) for kk in self.RAISED}
            w = {kk: lerp(r[kk], self.wings_flap(0.25, amp=46)[kk], ramp(f, 4, 10)) for kk in self.RAISED}
            w['sweep'] -= 18 * ramp(f, 3, 9)
        else:
            w = self.wings_flap(((f - 10) / 6.0) % 1.0, amp=50, mean=10)
        s_ = min(f / 24.0, 1.0)
        tb = V3((900 * (1 - (1 - s_) ** 2), 0, -150 * s_))
        return {'pitch': pitch, 'tb': tb, 'feet': ('reach', 1.0), 'mesh': 'open', 'wing': w,
                'tail_spread': 1.4 - 0.2 * ramp(f, 12, 24), 'tail_drop': 14 * ramp(f, 2, 8),
                'clench': ramp(f, 9, 11), 'open_toes': ramp(f, 0, 6) * (1 - ramp(f, 9, 11))}

    def mantle(self, f):
        """Mantling on the kill (on the ground): the wings spread and drooped to hide it, the tail fanned and down,
        the head down to it, looking up from time to time; it loops."""
        c = 2 * math.pi * f / 60.0
        look = keys(f, [(0, 0), (20, 0), (26, 1), (40, 1), (46, 0), (60, 0)])
        w = {'up': -26 + 3 * math.sin(c), 'sweep': -14, 'fore': -6, 'hand': -4, 'twist': 4, 'hand_up': -12, 'hand_twist': 6}
        return {'pitch': 22 + 2 * math.sin(c), 'tb': V3((-85, 0, 88)), 'feet': 'ground', 'mesh': 'open', 'wing': w,
                'tail_spread': 1.5, 'tail_drop': 14, 'head_pitch': -34 + 30 * look, 'head_yaw': 20 * look * math.sin(c * 2)}


HOOD_CLIPS = ('hood_off', 'hood_on')      # the only clips that key the hood
HANDOVERS = (('land_perch', 'perch_idle'), ('land_perch', 'perch_hooded'), ('land_perch', 'rouse'), ('rouse', 'perch_idle'),
             ('perch_idle', 'rouse'), ('perch_hooded', 'perch_idle'), ('land_cuff', 'hood_on'), ('land_cuff', 'cast_off'),
             ('hood_off', 'cast_off'), ('cast_off', 'flight'), ('flight', 'glide'), ('glide', 'stoop'), ('stoop', 'bind'))
HOODED_CLIPS = ('perch_hooded',)          # drawn with the hood on (the hood itself is game state)


def saker_mod():
    return SP


CLIPS = {      # name: (frames, method, loops)
    'perch_idle': (120, 'perch_idle', True), 'perch_hooded': (150, 'perch_hooded', True), 'rouse': (36, 'rouse', False), 'hood_off': (30, 'hood_off', False),
    'hood_on': (30, 'hood_on', False), 'cast_off': (39, 'cast_off', False), 'flight': (14, 'flight', True),
    'glide': (60, 'glide', True), 'stoop': (40, 'stoop', False), 'bind': (24, 'bind', False),
    'mantle': (60, 'mantle', True), 'land_cuff': (46, 'land_cuff', False), 'land_perch': (46, 'land_perch', False),
}


# ------------------------------------------------------------------ applying a pose
REST_FOOT = RIG.get('rest_foot', (75.0, 22.0, -125.0))        # the rest pose's foot, body frame (the tail base at the origin)
TUCK_FOOT = RIG.get('tuck_foot', (150.0, 8.0, -14.0))         # drawn up into the breast and belly feathers, the toes clenched: out of sight
REACH_FOOT = RIG.get('reach_foot', (150.0, 26.0, -120.0))
PUSH_FOOT = RIG.get('push_foot', (-10.0, 20.0, -95.0))        # straight back and down at the end of the kick      # thrown forward to take the cuff when landing
FIST_JESS = (36.0, 2.0, -26.0)          # where the falconer's fist holds the jesses (saker_fist)
HOOD_SHOWN = [False]      # the hood's state while posing a clip that does not key it (game state)
TALON_LIFT = 7.0                        # the distal joint's end held this far above the cuff so the curved talon's tip meets it


class Applier:
    def __init__(self, arm, clips):
        self.P = Poser(arm)
        self.arm = arm
        self.C = clips
        self.rest_root = self.P.rest['root'].translation / MM
        self.cords = None
        self.prev_root = None
        self.log = []

    def body_matrix(self, sp):
        R = (Matrix.Rotation(math.radians(sp.get('yaw', 0.0)), 4, 'Z') @ Matrix.Rotation(math.radians(-sp['pitch']), 4, 'Y')
             @ Matrix.Rotation(math.radians(sp.get('roll', 0.0)), 4, 'X'))
        return Matrix.Translation(V3(sp['tb']) * MM) @ R, R

    def to_world(self, W, p):
        return (W @ (V3(p) * MM)) / MM

    def toes_on(self, s, side, surface, foot_target):
        """Lay each toe, joint by joint, on the surface z = surface(x, y) (the exported cuff's own top, sampled; or the
        flat perch): of the angles that keep every vertex of the segment (its skin; on the last joint the talon too)
        at least 0.4 mm above the surface, the one that brings the lowest closest to it. The toes are set in the
        world from their rest frames, not from the tarsus, so they stay put while the leg moves above them."""
        P = self.P
        rest_foot = P.rest[f'tarsus.{s}'].translation / MM + P.rest[f'tarsus.{s}'].to_3x3() @ V3((0, P.pb[f'tarsus.{s}'].bone.length / MM, 0))
        for nm in TOE_NAMES:
            for j in (1, 2):
                b = f'{nm}{j}.{s}'
                V = self.toe_verts.get(b)
                bpy.context.view_layer.update()
                p = P.pb[b]
                Rr = P.rest[b]
                rest_dir = (Rr.to_3x3() @ V3((0, 1, 0))).normalized()
                if j == 1:
                    head = (V3(foot_target) + (Rr.translation / MM - rest_foot)) * MM
                else:
                    head = p.matrix.translation.copy()
                flat = V3((rest_dir.x, rest_dir.y, 0)).normalized()
                local = Rr.inverted()
                best, best_M = None, None
                for a in np.linspace(-35, 95, 131):
                    ar = math.radians(a)
                    want = flat * math.cos(ar) + V3((0, 0, -1)) * math.sin(ar)
                    r = rest_dir.rotation_difference(want).to_matrix()
                    M = Matrix.Translation(head) @ (r @ Rr.to_3x3()).to_4x4()
                    A = np.array(M @ local)
                    W = (V @ A[:3, :3].T + A[:3, 3]) / MM
                    clear = min(w[2] - surface(w[0], w[1]) for w in W)
                    score = abs(clear - 0.6) + (1000 if clear < 0.4 else 0)
                    if best is None or score < best:
                        best, best_M = score, M
                p.matrix = best_M

    def apply(self, sp, frame, key=True):
        P = self.P
        P.reset()
        W, R = self.body_matrix(sp)
        root_at = V3(sp['tb']) - PERCH_TB
        P.place('root', Matrix.Translation((root_at - self.rest_root) * MM))
        P.place('body', W)
        k = sp['pitch'] / 66.0
        if sp['mesh'] == 'fold' and 'neck' not in sp:
            # sitting: the turns fitted to the approved static (PERCH_NECK), in proportion to the body's pitch
            sp = dict(sp, neck=tuple(v * k for v in PERCH_NECK), tail_lift=sp.get('tail_lift', PERCH_TAIL))
        n1, n2, n3 = sp.get('neck', (20 * k, -46 * k, -40 * k))
        P.turn('neck1', (0, -1, 0), n1)
        P.turn('neck2', (0, -1, 0), n2)
        P.turn('head', (0, -1, 0), n3 + sp.get('head_pitch', 0.0))
        if sp.get('head_yaw'):
            P.turn('head', (0, 0, 1), sp['head_yaw'])
        P.turn('tail', (0, 1, 0), sp.get('tail_drop', 0.0) + sp.get('tail_lift', 0.0))
        fan = (sp.get('tail_spread', 1.0) - 1.0) * 45.0      # degrees each side
        P.turn('tail.L', (0, 0, -1), fan)
        P.turn('tail.R', (0, 0, 1), fan)
        if 'hood' in sp:      # keyed only by the clips that put the hood on or take it off: otherwise game state
            P.pb['hood'].scale = (1, 1, 1) if sp['hood'] >= 1.0 else (0.001,) * 3
            P.pb['hood'].location = (0, sp.get('hood_lift', 0.0) * MM, 0)      # the bone points up: its Y is up
        else:
            P.pb['hood'].scale = (1, 1, 1) if HOOD_SHOWN[0] else (0.001,) * 3
        w = sp.get('wing') or (SWAP_OPEN if sp['mesh'] == 'fold' else None)      # sitting: the hidden spread wing kept in the swap's fold
        for side, s in ((1, 'L'), (-1, 'R')):
            if w:
                P.turn(f'wing_up.{s}', (side, 0, 0), w['up'])
                P.turn(f'wing_up.{s}', (0, 0, side), w['sweep'])
                P.turn(f'wing_up.{s}', (0, side, 0), w.get('twist', 0.0))
                P.turn(f'wing_fore.{s}', (0, 0, side), w['fore'])
                P.turn(f'wing_hand.{s}', (0, 0, side), w['hand'])
                P.turn(f'wing_hand.{s}', (side, 0, 0), w.get('hand_up', 0.0))
                P.turn(f'wing_hand.{s}', (0, side, 0), w.get('hand_twist', 0.0))
            fp = sp.get('fold')
            if fp:
                P.turn(f'fold.{s}', (0, 0, -side), fp.get('out', 0.0))
                P.turn(f'fold.{s}', (side, 0, 0), fp.get('up', 0.0))
                P.turn(f'fold.{s}', (0, side, 0), fp.get('twist', 0.0))
                P.turn(f'fold_tip.{s}', (0, 0, -side), fp.get('tip_out', 0.0))
                P.turn(f'fold_tip.{s}', (side, 0, 0), fp.get('tip_up', 0.0))
            lift = sp.get('fold_lift', 0.0)
            if lift:
                P.turn(f'fold.{s}', (0, 0, -side), 0.6 * lift)
                P.turn(f'fold.{s}', (side, 0, 0), 0.5 * lift)
        # the legs and toes
        feet = sp['feet']
        for side, s in ((1, 'L'), (-1, 'R')):
            if feet in PLANTED:
                surf = self.C.cuff if feet == 'cuff' else flat_surface
                target = V3((0.0, 22.0 * side, 0.0)) + V3(sp.get('foot_shift', (0, 0, 0))) * (1 if side > 0 else 0)
                target.z = surf(target.x, target.y) + (CUFF_LIFT if feet == 'cuff' else FOOT_LIFT)
                P.leg(s, target, V3((-1, 0, -0.25)))
                self.toes_on(s, side, self.C.cuff if feet == 'cuff' else flat_surface, target)
            else:
                mode, kf = feet
                hang = V3(REST_FOOT) * V3((1, side, 1))
                tuck = V3(TUCK_FOOT) * V3((1, side, 1))
                reach = V3(REACH_FOOT) * V3((1, side, 1))
                if mode == 'free':
                    bf = hang.lerp(tuck, kf)
                elif mode == 'push':      # after the kick off the cuff the legs trail back, then tuck
                    bf = (V3(PUSH_FOOT) * V3((1, side, 1))).lerp(tuck, kf)
                else:
                    bf = tuck.lerp(reach, kf)
                target = self.to_world(W, bf)
                tk = kf if mode in ('free', 'push') else (1 - kf)      # how far drawn up
                th = math.radians(lerp(197.0, 368.0, smooth01((tk - 0.2) / 0.6)))      # back-down, through down, to forward
                pole = R.to_3x3() @ V3((math.cos(th), 0, math.sin(th)))
                P.leg(s, target, pole)
                cl = sp.get('clench', 0.0)
                op = sp.get('open_toes', 0.0)
                for nm, sign in (('toeM', 1), ('toeI', 1), ('toeO', 1), ('toeH', -1)):
                    bpy.context.view_layer.update()
                    ax = P.rest[f"{nm}1.{s}"].to_3x3() @ V3((1, 0, 0))      # each toe bends about its own axis
                    P.turn(f'{nm}1.{s}', ax, -(75 * cl - 18 * op))
                    P.turn(f'{nm}2.{s}', ax, -(95 * cl - 10 * op))
        # the jesses: a cord each, pinned at the anklet, held in the fist or free in the air
        bpy.context.view_layer.update()
        if self.prev_root is None:
            vel = V3((0, 0, 0))
        else:
            vel = (root_at - self.prev_root) * FPS
        self.prev_root = root_at
        air = V3(sp.get('air', (0, 0, 0))) - vel
        if self.cords is None:
            self.cords = {s: Cord(P.head_of(f'jess1.{s}')) for s in ('L', 'R')}
            self.gust = 0
        for side, s in ((1, 'L'), (-1, 'R')):
            anchor = P.head_of(f'jess1.{s}')
            # a little turbulence in the air, so a trailing cord swings and does not lie as a rod
            self.gust += 1
            wob = V3((0, 900 * math.sin(self.gust * 0.9 + side), 1400 * math.sin(self.gust * 0.63 + 2 * side))) if V3(air).length > 2000 else V3((0, 0, 0))
            hold = V3(FIST_JESS) * V3((1, side, 1)) if sp.get('jess_hold') else None
            if sp.get('jess_take') is not None:      # the falconer's fingers taking the free ends to his fist
                k = sp['jess_take']
                hold = self.cords[s].p[-1].lerp(V3(FIST_JESS) * V3((1, side, 1)), k) if k > 0 else None
            pts = self.cords[s].step(anchor, V3(air) + wob, end=hold)
            st = sp.get('settle', 0.0)
            key_ = sp.get('settle_to') or (sp['feet'] if isinstance(sp['feet'], str) else None)
            ref = getattr(self.C, 'perch_cords', {}).get(key_)
            if st and ref:
                # perched: the cords' one settled shape, carried by the anklet (so every perched clip starts and
                # ends with the same cords)
                a0, p0 = ref[s]
                want = [q + (anchor - a0) for q in p0]
                pts = [a.lerp(b, st) for a, b in zip(pts, want)]
                self.cords[s].p = [q.copy() for q in pts]
                if st >= 1.0:
                    self.cords[s].q = [q.copy() for q in pts]
            for j in range(JESS_N):
                P.aim(f'jess{j + 1}.{s}', pts[j + 1])
        if key:
            P.key(frame, skip=() if 'hood' in sp else ('hood',))
        # measures
        if feet in PLANTED:
            for s in ('L', 'R'):
                side = 1 if s == 'L' else -1
                want = V3((0, 22 * side, 0)) + V3(sp.get('foot_shift', (0, 0, 0))) * (1 if side > 0 else 0)
                want.z = (self.C.cuff if feet == 'cuff' else flat_surface)(want.x, want.y) + (CUFF_LIFT if feet == 'cuff' else FOOT_LIFT)
                self.log.append(('slide', frame, s, (P.tail_of(f'tarsus.{s}') - want).length))


# ------------------------------------------------------------------ build, export, sheets
def build_saker(out, sheets=False):
    import paint
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    parts_f, pts, body = saker_rest('fold')
    BODY[:] = [body]
    parts_o, _, _ = saker_rest('open')
    B = saker_bones(pts, body)
    atlas = paint.atlas(BIRD)
    col, orm = paint.paint(BIRD, atlas, 512, body)
    mat = common.material(BIRD, col, orm)
    arm = make_armature(f'{BIRD}_rig', B)
    meshes = {
        'fold': skinned_mesh(f'{BIRD}_fold', parts_f['body'], body, B, atlas, mat, arm),
        'open': skinned_mesh(f'{BIRD}_open', parts_o['body'], body, B, atlas, mat, arm),
        'hood': skinned_mesh(f'{BIRD}_hood', parts_f['hood'], body, B, atlas, mat, arm),
        'jesses': skinned_mesh(f'{BIRD}_jesses', parts_f['jesses'], body, B, atlas, mat, arm),
    }
    for k in ('fold', 'open'):
        add_hidden_morph(meshes[k], body)
    eye_x = body.at(saker_mod().SPEC['eye']['d']).x
    add_fluff_morph(meshes['fold'], body, eye_x)
    # the far level: the T11 far meshes (256 px) on the same skeleton, the same clips; no hood or jesses at that range
    pf1, _, body1 = saker_rest('fold', level=1)
    po1, _, _ = saker_rest('open', level=1)
    c1, o1 = paint.paint(BIRD, atlas, 256, body1)
    mat1 = common.material(f'{BIRD}_far', c1, o1)
    far = {'fold': skinned_mesh(f'{BIRD}_fold_far', pf1['body'], body1, B, atlas, mat1, arm),
           'open': skinned_mesh(f'{BIRD}_open_far', po1['body'], body1, B, atlas, mat1, arm)}
    for k in far:
        add_hidden_morph(far[k], body1)
        far[k].hide_render = True
    add_fluff_morph(far['fold'], body1, eye_x)
    FAR[:] = [far]
    clips = SakerClips()
    CUFF_TOP[:] = [clips.cuff]
    arm.animation_data_create()
    # the perched cords' settled shape, on the perch (free) and on the cuff (held in the fist)
    clips.perch_cords = {}
    toe_verts0 = toe_vertex_sets(meshes['fold'])
    for surf in ('perch', 'cuff'):
        A = Applier(arm, clips)
        A.toe_verts = toe_verts0
        spec0 = clips.perched_rest(surf)
        for _ in range(150):
            A.apply(spec0, 0, key=False)
        clips.perch_cords[surf] = {s: (A.P.head_of(f'jess1.{s}'), [q.copy() for q in A.cords[s].p]) for s in ('L', 'R')}
    # the flight loop's cords at its frame 0, as the loop is recorded (two loops to settle, then frame 0)
    A = Applier(arm, clips)
    A.toe_verts = toe_verts0
    nfl = CLIPS['flight'][0] if 'flight' in CLIPS else 14
    for f in range(2 * nfl):
        A.apply(clips.flight(f % nfl), 0, key=False)
    A.apply(clips.flight(0), 0, key=False)
    clips.perch_cords['flight'] = {s: (A.P.head_of(f'jess1.{s}'), [q.copy() for q in A.cords[s].p]) for s in ('L', 'R')}
    frames_mesh = {}
    log = []
    toe_verts = toe_vertex_sets(meshes['fold'])
    for name, (n, fn, loop) in CLIPS.items():
        act = bpy.data.actions.new(name)
        arm.animation_data.action = act
        A = Applier(arm, clips)
        A.toe_verts = toe_verts
        HOOD_SHOWN[0] = name in HOODED_CLIPS
        spec_fn = getattr(clips, fn)
        if loop:      # settle the cords over two loops before recording
            for f in range(2 * n):
                A.apply(spec_fn(f % n), 0)
        else:         # let the cords settle in the first frame's pose (its air included) before recording
            for _ in range(20):
                A.apply(spec_fn(0), 0)
            A.prev_root = None
        frames_mesh[name] = []
        FRAMES_FEET[name] = []
        HIDDEN_FEET[name] = []
        keys_shape = {}
        for k, o in (('fold', meshes['fold']), ('open', meshes['open']), ('fold_far', far['fold']), ('open_far', far['open'])):
            sk = o.data.shape_keys
            sk.animation_data_create()
            sk.animation_data.action = bpy.data.actions.new(name)      # the same name: merged into the clip on export
            keys_shape[k] = sk
        for f in range(n + (1 if loop else 0)):
            sp = spec_fn(f % n)
            A.apply(sp, f)
            for k, sk in keys_shape.items():
                sk.key_blocks['hidden'].value = 0.0 if sp['mesh'] == k.split('_')[0] else 1.0
                sk.key_blocks['hidden'].keyframe_insert('value', frame=f)
                if 'fluff' in sk.key_blocks:
                    sk.key_blocks['fluff'].value = sp.get('fluff', 0.0)
                    sk.key_blocks['fluff'].keyframe_insert('value', frame=f)
            frames_mesh[name].append(sp['mesh'])
            FRAMES_FEET[name].append(sp['feet'] if isinstance(sp['feet'], str) else sp['feet'][0])
            ft = sp['feet']
            HIDDEN_FEET[name].append(not isinstance(ft, str) and ((ft[0] in ('free', 'push') and ft[1] >= 0.999) or (ft[0] == 'reach' and ft[1] <= 0.001)))
        log += [(name,) + e for e in A.log]
        act.use_fake_user = True
        arm.animation_data.action = None
        for k, sk in keys_shape.items():
            sk.animation_data.action.use_fake_user = True
            SHAPE_ACTIONS.setdefault(k, {})[name] = sk.animation_data.action
            sk.animation_data.action = None
    # the tracks only once every clip is keyed: a track playing while the next clip is posed would leak into it
    thin = thin_keys([bpy.data.actions[n] for n in CLIPS])
    print(f'keys thinned: {thin[0]} of {thin[1]} kept (each removed key within {QTOL} of the quaternion, {LTOL * 1000:.2f} mm, {STOL} of scale by straight-line interpolation)')
    step_keys([a for d in SHAPE_ACTIONS.values() for a in d.values()])
    step_keys([bpy.data.actions[n] for n in HOOD_CLIPS if n in CLIPS], path_has=('pose.bones["hood"].scale',))
    for name in CLIPS:
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 0, bpy.data.actions[name])
        for k, o in (('fold', meshes['fold']), ('open', meshes['open']), ('fold_far', far['fold']), ('open_far', far['open'])):
            sk = o.data.shape_keys
            t2 = sk.animation_data.nla_tracks.new()
            t2.name = name
            t2.strips.new(name, 0, SHAPE_ACTIONS[k][name])
    # the measures: foot slide on the cuff
    for name in CLIPS:
        sl = [e[4] for e in log if e[0] == name and e[1] == 'slide']
        if sl:
            print(f'{name}: a planted foot\'s distance from its place, max {max(sl):.2f} mm over {len(sl) // 2} frames')
    path = os.path.join(out, f'{BIRD}_rig.glb')
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm, *meshes.values(), *far.values()]:      # the far level in the same file, on the same skeleton
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='NLA_TRACKS', export_skins=True,
                              export_all_influences=False, export_force_sampling=False, export_optimize_animation_size=True, export_optimize_animation_keep_anim_armature=True,
                              export_morph=True, export_morph_animation=True, export_morph_normal=False,
                              export_materials='EXPORT', export_extras=False, export_image_format='AUTO')
    common.settle(path)
    step_in_file(path)
    t, imgs, nbytes = common.glb_report(path)
    print(f'{BIRD}_rig.glb: {", ".join(f"{k} {v}" for k, v in sorted(t.items()))}; {len(B)} bones; {nbytes / 1024:.0f} KB')
    glb_checks(path, hood_clips=HOOD_CLIPS)
    return arm, meshes, frames_mesh, B, clips


def evaluated_co(o):
    """The mesh's posed vertices (mm) and triangles."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    tri = np.empty(len(me.polygons) * 3, dtype=np.int64)
    me.polygons.foreach_get('vertices', tri)
    ev.to_mesh_clear()
    return co.reshape(-1, 3) / MM, tri.reshape(-1, 3)


def silhouette(co, tri, view, px=2.0, box=None):
    """A mesh's silhouette from a direction (orthographic), on a grid of [px] mm, as a boolean image."""
    from PIL import Image, ImageDraw
    v = V3(view).normalized()
    up = V3((0, 0, 1))
    right = v.cross(up).normalized()
    up = right.cross(v).normalized()
    X = co @ np.array(tuple(right))
    Y = co @ np.array(tuple(up))
    x0, y0, x1, y1 = box if box else (X.min() - 5, Y.min() - 5, X.max() + 5, Y.max() + 5)
    w, h = int((x1 - x0) / px) + 1, int((y1 - y0) / px) + 1
    im = Image.new('1', (w, h), 0)
    d = ImageDraw.Draw(im)
    U = (X - x0) / px
    W = (y1 - Y) / px
    for a, b, c in tri:
        d.polygon([(U[a], W[a]), (U[b], W[b]), (U[c], W[c])], fill=1)
    return np.array(im, bool), (x0, y0, x1, y1)


def iou(a, b):
    return float((a & b).sum()) / max(float((a | b).sum()), 1.0)


def pair_iou(coA, triA, coB, triB, view):
    """Silhouette overlap of two posed meshes from one direction, in one frame of reference."""
    v = V3(view).normalized()
    up = V3((0, 0, 1))
    right = v.cross(up).normalized()
    up = right.cross(v).normalized()
    allc = np.vstack([coA, coB])
    X, Y = allc @ np.array(tuple(right)), allc @ np.array(tuple(up))
    box = (X.min() - 5, Y.min() - 5, X.max() + 5, Y.max() + 5)
    A, _ = silhouette(coA, triA, view, box=box)
    B_, _ = silhouette(coB, triB, view, box=box)
    return iou(A, B_)


VIEWS = {'side': (0, -1, 0), 'three_quarter': (-1, -1, -0.5), 'front': (-1, 0, 0)}


SHAPE_ACTIONS = {}
FAR = []
SHEET_PREFIX = [BIRD]
QTOL, LTOL, STOL = 0.0002, 0.00001, 0.0005      # tight: the chain from the root to a talon must stay within a millimetre


def add_hidden_morph(o, body):
    """A morph target 'hidden' that gathers every vertex to one point inside the body: at weight 1 the mesh shows
    nothing (and the game, by the convention in README.md, does not draw it)."""
    o.shape_key_add(name='Basis')
    kb = o.shape_key_add(name='hidden')
    c = bird.torso_point(body, 90, 0, 0) * MM
    for d in kb.data:
        d.co = c


FLUFF = {'body': 7.0, 'neck1': 6.0, 'neck2': 6.0, 'head': 4.0, 'shank': 6.0, 'fold': 3.0, 'fold_tip': 1.0,
         'tail': 1.5, 'tail.L': 1.5, 'tail.R': 1.5}      # mm each bone's feathers rise in the rouse (game choice)


def add_fluff_morph(o, body, eye_x):
    """A morph target 'fluff': the contour feathers raised all over, as in the first moment of a rouse, by moving
    each vertex out along its normal by FLUFF of the bones that carry it (the bill, eyes, feet and jesses do not
    move: the head only behind the eye)."""
    kb = o.shape_key_add(name='fluff')
    gi = {g.index: g.name for g in o.vertex_groups}
    me = o.data
    for v, d in zip(me.vertices, kb.data):
        a = 0.0
        for ge in v.groups:
            nm = gi[ge.group]
            key = nm.split('.')[0] if nm.split('.')[0] in ('shank', 'fold', 'fold_tip') else nm
            amt = FLUFF.get(key, 0.0)
            if nm == 'head' and v.co.x / MM > eye_x - 12:
                amt = 0.0
            a += ge.weight * amt
        d.co = v.co + v.normal * (a * MM)


def fcurves_of(act):
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out += list(bag.fcurves)
        return out


def thin_keys(actions):
    """Remove keys a straight line between their neighbours reproduces within the tolerance (Douglas-Peucker per
    channel); the rest made linear. The motion is unchanged within QTOL / LTOL / STOL."""
    kept = total = 0
    for act in actions:
        for fc in fcurves_of(act):
            pts = [(k.co[0], k.co[1]) for k in fc.keyframe_points]
            total += len(pts)
            if len(pts) < 3:
                kept += len(pts)
                continue
            tol = QTOL if 'rotation' in fc.data_path else LTOL if 'location' in fc.data_path else STOL if 'scale' in fc.data_path else 1e-4
            keep = [0, len(pts) - 1]

            def dp(i, j):
                if j <= i + 1:
                    return
                (x0, y0), (x1, y1) = pts[i], pts[j]
                worst, wi = -1.0, None
                for m in range(i + 1, j):
                    x, y = pts[m]
                    e = abs(y - (y0 + (y1 - y0) * (x - x0) / (x1 - x0)))
                    if e > worst:
                        worst, wi = e, m
                if worst > tol:
                    keep.append(wi)
                    dp(i, wi)
                    dp(wi, j)
            dp(0, len(pts) - 1)
            keep = sorted(set(keep))
            sel = [pts[i] for i in keep]
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(sel))
            for kp, (x, y) in zip(fc.keyframe_points, sel):
                kp.co = (x, y)
                kp.interpolation = 'LINEAR'
            fc.update()
            kept += len(sel)
    return kept, total


def step_keys(actions, path_has=None):
    """Morph weights (the swap's 'hidden', the rouse's 'fluff') and the hood's scale play as steps: a clip
    sampled between two keys must never show a half-gathered mesh or a shrunken hood. Keys that repeat the value
    before them are dropped, the rest made CONSTANT (exported as glTF STEP)."""
    n = 0
    for act in actions:
        for fc in fcurves_of(act):
            if path_has and not any(h in fc.data_path for h in path_has):
                continue
            pts = [(k.co[0], k.co[1]) for k in fc.keyframe_points]
            sel = [p for i, p in enumerate(pts) if i == 0 or i == len(pts) - 1 or abs(p[1] - pts[i - 1][1]) > 1e-9]
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(sel))
            for kp, (x, y) in zip(fc.keyframe_points, sel):
                kp.co = (x, y)
                kp.interpolation = 'CONSTANT'
            fc.update()
            n += 1
    return n


def step_in_file(path):
    """The exporter samples morph weights (and writes them LINEAR) whatever the curves' interpolation; sampled on
    every frame, the same values played as STEP are the curves exactly. Set STEP on every morph-weight channel and
    on the hood's scale, in the file's JSON (its length kept by the padding)."""
    import json
    import struct
    raw = bytearray(open(path, 'rb').read())
    jl = struct.unpack_from('<I', raw, 12)[0]
    g = json.loads(bytes(raw[20:20 + jl]))
    names = [nd.get('name', '') for nd in g.get('nodes', [])]
    for an in g.get('animations', []):
        for ch in an['channels']:
            t = ch['target']
            if t['path'] == 'weights' or (names[t.get('node', 0)] == 'hood' and t['path'] == 'scale'):
                smp = an['samplers'][ch['sampler']]
                assert smp.get('interpolation', 'LINEAR') in ('LINEAR', 'STEP'), smp
                smp['interpolation'] = 'STEP'
    js = json.dumps(g, separators=(',', ':')).encode()
    js += b' ' * ((-len(js)) % 4)
    rest = raw[20 + jl:]
    out = bytearray(raw[:12]) + struct.pack('<I', len(js)) + raw[16:20] + js + rest
    struct.pack_into('<I', out, 8, len(out))
    open(path, 'wb').write(out)


def glb_checks(path, hood_clips=()):
    """The build's own checks on the written file; a failure stops the build. Prints: the clips, the clip data,
    every morph-weight channel's interpolation (must be STEP), that every clip animates every bone (a bone a clip
    leaves out shows its rest pose: the standing pose, not the clip's), and that only [hood_clips] move the hood."""
    import json
    import struct
    with open(path, 'rb') as fh:
        raw = fh.read()
    jl = struct.unpack('<I', raw[12:16])[0]
    g = json.loads(raw[20:20 + jl])
    names = [nd.get('name', '') for nd in g.get('nodes', [])]
    joints = sorted(set(names[j] for sk in g.get('skins', []) for j in sk['joints']))
    acc, bad, hood, nweights, missing = set(), [], [], 0, []
    for an in g.get('animations', []):
        rot = set()
        for ch in an['channels']:
            smp = an['samplers'][ch['sampler']]
            acc.update((smp['input'], smp['output']))
            node = names[ch['target'].get('node', 0)]
            if ch['target']['path'] == 'weights':
                nweights += 1
                if smp.get('interpolation', 'LINEAR') != 'STEP':
                    bad.append((an['name'], node))
            if ch['target']['path'] == 'rotation':
                rot.add(node)
            if node == 'hood' and ch['target']['path'] == 'scale':
                acc_o = g['accessors'][smp['output']]
                if acc_o.get('min') != acc_o.get('max'):
                    hood.append(an['name'])
        miss = [j for j in joints if j not in rot]
        if miss:
            missing.append((an['name'], len(miss), miss[:3]))
    nb = sum(g['bufferViews'][g['accessors'][a]['bufferView']]['byteLength'] for a in acc)
    meshes = [m['name'] for m in g.get('meshes', [])]
    skins = len(g.get('skins', []))
    print(f'{os.path.basename(path)}: meshes {", ".join(meshes)}; {skins} skin(s), {len(g.get("animations", []))} clips, clip data {nb / 1024:.0f} KB')
    print(f'{os.path.basename(path)}: morph-weight channels {nweights}, not STEP {len(bad)}' + (f' {bad[:4]}' if bad else ''))
    print(f'{os.path.basename(path)}: every clip animates all {len(joints)} bones: ' + ('yes' if not missing else f'NO {missing}'))
    hood = sorted(set(hood))
    print(f'{os.path.basename(path)}: clips moving the hood: {", ".join(hood) if hood else "none"}')
    assert not bad, 'a morph-weight channel is not STEP'
    assert not missing, 'a clip leaves bones at their rest pose'
    assert set(hood) <= set(hood_clips), f'the hood is moved outside {hood_clips}: {hood}'
    assert skins == 1, 'the detail levels must share one skeleton'


def show_both(arm, on=True):
    """For a measure: every mesh shown (the morph 'hidden' held at 0), or back to the clip's own keys."""
    for o in arm.children:
        sk = o.data.shape_keys if o.type == 'MESH' else None
        if sk and sk.animation_data:
            if on:
                sk.animation_data.action = None
                sk.key_blocks['hidden'].value = 0.0


def use_clip(arm, name):
    """Show one clip: its actions (the skeleton's, and each mesh's morph 'hidden') played directly, every NLA track
    muted (so nothing else blends in)."""
    def assign(ad, act):
        for t in ad.nla_tracks:
            t.mute = True
        ad.action = act
        try:
            ad.action_slot = act.slots[0]
        except (AttributeError, IndexError):
            pass
    assign(arm.animation_data, bpy.data.actions[name])
    if 'hood' in arm.pose.bones:
        arm.pose.bones['hood'].scale = (1, 1, 1) if name in HOODED_CLIPS else (0.001,) * 3      # game state, unless the clip keys it
        arm.pose.bones['hood'].location = (0, 0, 0)
    for o in arm.children:
        sk = o.data.shape_keys if o.type == 'MESH' else None
        if sk and sk.animation_data:
            for t in sk.animation_data.nla_tracks:
                if t.name == name and t.strips:
                    assign(sk.animation_data, t.strips[0].action)


def toe_vertex_sets_all(o):
    """As toe_vertex_sets, but every toe vertex, each under the bone that carries most of it."""
    out = {}
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    names = {g.index: g.name for g in o.vertex_groups if g.name.startswith('toe')}
    for v in o.data.vertices:
        gs = [g for g in v.groups if g.group in names]
        if gs:
            g = max(gs, key=lambda g: g.weight)
            out.setdefault(names[g.group], []).append(co[v.index])
    return {k: np.array(v) for k, v in out.items()}


def toe_vertex_sets(o):
    """The rest positions (metres) of the vertices each toe bone carries most of."""
    out = {}
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    names = {g.index: g.name for g in o.vertex_groups if g.name.startswith('toe')}
    for v in o.data.vertices:
        for g in v.groups:
            if g.group in names and g.weight >= 0.5:
                out.setdefault(names[g.group], []).append(co[v.index])
    return {k: np.array(v) for k, v in out.items()}


def talon_depths(arm, meshes, frames_mesh, name, n, surface=None):
    """Per frame, how deep any toe or talon vertex goes under the support's surface (mm)."""
    import gear
    sc = bpy.context.scene
    use_clip(arm, name)
    out = []
    for f in range(n):
        sc.frame_set(f)
        o = meshes[frames_mesh[name][f]]
        dg = bpy.context.evaluated_depsgraph_get()
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        idx = [g.index for g in o.vertex_groups if g.name.startswith('toe')]
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3) / MM
        sel = [v.index for v in o.data.vertices if any(g.group in idx and g.weight > 0.3 for g in v.groups)]
        depth, where = 0.0, None
        for i in sel:
            x, y, z = co[i]
            if abs(y) < 45 and -100 < x < 60:
                dd = surface(x, y) - z
                if dd > depth:
                    depth, where = dd, (round(x), round(y), round(z), [g.name for g in o.vertex_groups if any(vg.group == g.index for vg in o.data.vertices[i].groups)])
        ev.to_mesh_clear()
        out.append(depth)
        if f in (0,) and where:
            print('   deepest at', where)
    return out


CUFF_TOP = []      # the cuff's Heightmap, set by the build
FOREARM = (-400.0, 45.0)      # the falconer's forearm behind the cuff: to x = -400 mm, 45 mm round (the cuff's rim 47)


def inside_support(Q, kind, parts=False):
    """For points Q (n x 3, mm, the clip's world), how deep each lies inside the support (0 outside): the cuff's
    padded loft (its rows, analytic) and the forearm behind it; or the perch's pad and turned head and stake."""
    import gear
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    depth = np.zeros(len(Q))
    if kind == 'cuff':
        r = np.array(gear.DASS_ROWS, float)
        zz = z + 52.0
        inx = (x >= r[0, 0]) & (x <= r[-1, 0])
        au, ad, b, pp = (np.interp(x, r[:, 0], r[:, k]) for k in (1, 2, 3, 4))
        a = np.where(zz >= 0, au, ad)
        F = (np.abs(y) / b) ** pp + (np.abs(zz) / a) ** pp
        d = (1.0 - np.minimum(F, 1.0) ** (1.0 / pp)) * np.minimum(a, b)
        depth = np.where(inx & (F < 1.0), d, 0.0)
        # the thumb and knuckles stand above the loft: the cuff's real top (the heightmap of its faces) above the axis
        if CUFF_TOP:
            H = CUFF_TOP[0]
            ix = np.round((x - H.x0) / H.step).astype(int)
            iy = np.round((y - H.y0) / H.step).astype(int)
            ok = (ix >= 0) & (iy >= 0) & (ix < H.H.shape[1]) & (iy < H.H.shape[0])
            top = np.full(len(x), -1e6)
            top[ok] = H.H[iy[ok], ix[ok]]
            hd = np.where((zz > 0) & (top > -1e5) & (z < top), top - z, 0.0)
            depth = np.maximum(depth, np.minimum(hd, zz))
        rr = np.sqrt(y ** 2 + zz ** 2)
        arm_in = (x < r[0, 0]) & (x > FOREARM[0]) & (rr < FOREARM[1])
        arm_d = np.where(arm_in, FOREARM[1] - rr, 0.0)
        if parts:
            return depth, arm_d
        depth = np.maximum(depth, arm_d)
    else:
        zs = [0.0, -2.5, -6.0, -10.0, -14.0, -30.0, -38.0, -50.0, -66.0, -80.0, -92.0, -400.0]
        rs = [66.0, 73.0, 75.0, 74.0, 75.0, 73.0, 66.0, 48.0, 32.0, 24.0, 22.0, 20.0]
        R = np.interp(-z, [-v for v in zs], rs)
        rr = np.sqrt(x ** 2 + y ** 2)
        ok = (z < 0.0) & (z > -400.0) & (rr < R)
        depth = np.where(ok, np.minimum(R - rr, -z), 0.0)
    return depth


def support_checks(arm, meshes, frames_mesh, name, n, kind):
    """Every frame of a clip on the cuff or the perch: before the feet take it, no vertex of the shown body inside
    it; once they have, none but the toes', and the toes within TOE_DEPTH_OK."""
    sc = bpy.context.scene
    use_clip(arm, name)
    toes = {k: np.array(sorted(group_set(meshes[k], ('toe',))), int) for k in ('fold', 'open')}
    toes_l = toes
    pre, post, tdeep = [], [], (0.0, None)
    forearm, cuff_hit = [], []
    for f in range(n):
        sc.frame_set(f)
        m = frames_mesh[name][f]
        co, _ = evaluated_co(meshes[m])
        if kind == 'cuff':
            dc, da = inside_support(co, kind, parts=True)
            d = np.maximum(dc, da)
            tl = toes_l[m]
            arm_hit = int((da[np.setdiff1d(np.arange(len(co)), tl)] > 0.5).sum())
            if arm_hit:
                forearm.append((f, arm_hit))
            dcn = dc.copy()
            dcn[tl] = 0
            if (dcn > 0.5).any():
                i = int(np.argmax(dcn))
                gi = {g.index: g.name for g in meshes[m].vertex_groups}
                v = meshes[m].data.vertices[i]
                cuff_hit.append((f, int((dcn > 0.5).sum()), round(float(dcn.max()), 1),
                                 gi[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '?'))
        else:
            d = inside_support(co, kind)
        planted = FRAMES_FEET[name][f] in PLANTED
        mask = np.ones(len(co), bool)
        if planted:
            mask[toes[m]] = False
            td = float(d[toes[m]].max()) if len(toes[m]) else 0.0
            if td > tdeep[0]:
                tdeep = (td, f)
        dm = np.where(mask, d, 0.0)
        cnt = int((dm > 0.5).sum())
        if cnt:
            i = int(np.argmax(dm))
            v = meshes[m].data.vertices[i]
            gi = {g.index: g.name for g in meshes[m].vertex_groups}
            top = gi[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '?'
            (post if planted else pre).append((f, cnt, round(float(dm.max()), 1), top))
    print(f'{name}: vertices inside the {"cuff or forearm" if kind == "cuff" else "perch"} before the feet take it '
          f'(frame, count, deepest mm, its bone): {pre if pre else "none"}')
    print(f'{name}: once planted, vertices other than the toes inside: {post if post else "none"}; '
          f'toes at most {tdeep[0]:.1f} mm in (frame {tdeep[1]})')
    if kind == 'cuff':
        print(f'{name}: inside the cuff itself, vertices other than the toes (frame, count, deepest mm): '
              f'{cuff_hit if cuff_hit else "none"}; inside the level forearm behind it: '
              f'{(str(len(forearm)) + " frames, at most " + str(max(c for _, c in forearm)) + " vertices") if forearm else "none"}')
    return pre, post, tdeep


def bone_heads(arm, rel_root=True):
    """Every bone's head and tail (mm, armature space), relative to the root bone's head: the pose, wherever the
    clip has carried the bird."""
    bpy.context.view_layer.update()
    r = arm.pose.bones['root'].head.copy() if rel_root else V3((0, 0, 0))
    out = {}
    for b in arm.pose.bones:
        out[b.name] = ((b.head - r) / MM, (b.tail - r) / MM)
    return out


def pose_gap(a, b, skip=()):
    """The largest distance between the same bone's head or tail in two poses (mm), and that bone."""
    worst, wb = 0.0, None
    for k in a:
        if any(k.startswith(p) for p in skip):
            continue
        d = max((a[k][0] - b[k][0]).length, (a[k][1] - b[k][1]).length)
        if d > worst:
            worst, wb = d, k
    return worst, wb


def handover_checks(arm, pairs, clips, skip=()):
    """Where one clip hands over to another (a transition into a loop, a landing into the perched idle), the first
    clip's last frame must lead into the second's first: their gap (the pose, against the root) is printed beside
    the largest step inside the second clip."""
    sc = bpy.context.scene
    res = []
    for a, b in pairs:
        if a not in clips or b not in clips:
            continue
        use_clip(arm, a)
        sc.frame_set(clips[a][0] - 1)
        pa = bone_heads(arm)
        use_clip(arm, b)
        nb = clips[b][0]
        prev, inner = None, 0.0
        for f in range(nb):
            sc.frame_set(f)
            p = bone_heads(arm)
            if f == 0:
                p0 = p
            if prev is not None:
                inner = max(inner, pose_gap(prev, p, skip)[0])
            prev = p
        gap, bone = pose_gap(pa, p0, skip)
        print(f'hand-over {a} (last frame) -> {b} (first): the pose differs by {gap:.1f} mm at most ({bone}); '
              f'the largest step inside {b} {inner:.1f} mm' + ('' if gap <= max(inner, 2.0) + 0.5 else '  ** too large **'))
        res.append((a, b, gap, inner))
    return res


def strip_gif(arm, meshes, frames_mesh, name, frames, out, cam, res=(240, 180), samples=6, repeat=1):
    """A small looping GIF of a clip (every frame), for the chat."""
    from PIL import Image
    sc = bpy.context.scene
    use_clip(arm, name)
    st = contact_sheet.studio
    st.sc.cycles.samples = samples
    ims = []
    for f in frames:
        sc.frame_set(f + 1)
        sc.frame_set(f)
        for k, o in meshes.items():
            if k in ('fold', 'open'):
                o.hide_render = frames_mesh[name][f] != k
        bpy.context.view_layer.update()
        root = arm.pose.bones['root'].matrix.translation
        loc, at, ortho = cam(f, root)
        st.rig_lights(V3(at), dist=1.6)
        png = st.shot(f'_g_{name}_{f:03d}', loc, at, ortho=ortho, res=res, lens=50)
        ims.append(Image.open(png).convert('RGB').quantize(colors=96, method=Image.Quantize.MEDIANCUT))
        os.remove(png)
    ims = ims * repeat
    path = os.path.join(out, f'{SHEET_PREFIX[0]}_{name}.gif')
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=int(1000 / FPS), loop=0, optimize=True)
    print('gif', path, f'{os.path.getsize(path) / 1024:.0f} KB')
    return path


def contact_sheet(arm, meshes, frames_mesh, name, frames, out, view='side', res=(320, 240), samples=8, cam=None,
                  with_cuff=True, label='', tag=None):
    """Renders the frames of a clip and tiles them into one JPEG with the frame numbers."""
    from PIL import Image, ImageDraw
    sc = bpy.context.scene
    use_clip(arm, name)
    st = getattr(contact_sheet, 'studio', None)
    if st is None:
        st = common.Studio(out, samples=samples, ground=False)
        contact_sheet.studio = st
    st.sc.cycles.samples = samples
    tiles = []
    for f in frames:
        sc.frame_set(f + 1)
        sc.frame_set(f)
        for k, o in meshes.items():
            if k in ('fold', 'open'):
                o.hide_render = frames_mesh[name][f] != k
        bpy.context.view_layer.update()
        root = arm.pose.bones['root'].matrix.translation
        loc, at, ortho = cam(f, root)
        st.rig_lights(V3(at), dist=1.6)
        png = st.shot(f'_{name}_{f:03d}', loc, at, ortho=ortho, res=res, lens=50)
        tiles.append((f, Image.open(png).convert('RGB')))
        os.remove(png)
    w, h = res
    cols = min(len(tiles), 6)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w, rows * h + 28), (250, 250, 248))
    d = ImageDraw.Draw(sheet)
    f_ = common.font(16)
    d.text((8, 5), label or f'{name} (30 frames a second); awaiting the owner\'s approval of the motion', fill=(20, 20, 20), font=f_)
    for i, (f, im) in enumerate(tiles):
        x, y = (i % cols) * w, (i // cols) * h + 28
        sheet.paste(im, (x, y))
        d.text((x + 6, y + 4), f'{f}', fill=(20, 20, 20), font=f_)
    path = os.path.join(out, f'{SHEET_PREFIX[0]}_{name}_{tag or "sheet"}.jpg')
    sheet.save(path, quality=86)
    print('sheet', path)
    return path


def tune_cast_swap(arm, meshes, clips):
    """The cast-off's and the landings' swap: the folded mesh's opening (SWAP_FOLD) and the spread mesh's fold
    (SWAP_OPEN) that match best in cast_off's frame 13 (the lower of the side and three-quarter overlaps),
    searched in alternating rounds on shrinking grids."""
    A = Applier(arm, clips)
    A.toe_verts = toe_vertex_sets(meshes['fold'])
    for o in meshes.values():
        sk = o.data.shape_keys
        if sk:
            sk.key_blocks['hidden'].value = 0.0
    base = clips.cast_off(13)
    sf, so = dict(SWAP_FOLD), dict(SWAP_OPEN)
    step = {'up': 12, 'sweep': 12, 'fore': 20, 'hand': 20, 'out': 10, 'fup': 12, 'tip_out': 12, 'tip_up': 12}
    best = None
    for rnd in range(6):
        if rnd % 2 == 0:
            c = so
            grid = [{'up': u, 'sweep': sw, 'fore': fo, 'hand': ha, 'twist': 0}
                    for u in (c['up'] - step['up'], c['up'], c['up'] + step['up'])
                    for sw in (c['sweep'] - step['sweep'], c['sweep'], c['sweep'] + step['sweep'])
                    for fo in (c['fore'] - step['fore'], c['fore'], c['fore'] + step['fore'])
                    for ha in (c['hand'] - step['hand'], c['hand'], c['hand'] + step['hand'])]
        else:
            c = sf
            grid = [{'out': o_, 'up': u, 'twist': 0, 'tip_out': to, 'tip_up': tu}
                    for o_ in (c['out'] - step['out'], c['out'], c['out'] + step['out'])
                    for u in (c['up'] - step['fup'], c['up'], c['up'] + step['fup'])
                    for to in (c['tip_out'] - step['tip_out'], c['tip_out'], c['tip_out'] + step['tip_out'])
                    for tu in (c['tip_up'] - step['tip_up'], c['tip_up'], c['tip_up'] + step['tip_up'])]
        for g in grid:
            w, fp = (g, sf) if rnd % 2 == 0 else (so, g)
            A.apply(dict(base, wing=w, fold=fp), 0, key=False)
            bpy.context.view_layer.update()
            a, ta = evaluated_co(meshes['fold'])
            b, tb = evaluated_co(meshes['open'])
            sc = min(pair_iou(a, ta, b, tb, VIEWS['side']), pair_iou(a, ta, b, tb, VIEWS['three_quarter']))
            if best is None or sc > best[0]:
                best = (sc, dict(fp), dict(w))
        sf, so = best[1], best[2]
        if rnd % 2 == 1:
            step = {k: max(3, v * 0.6) for k, v in step.items()}
        print(BIRD, 'swap round', rnd, 'overlap %.3f' % best[0], best[1], best[2])


def tune_swaps(arm, meshes, clips):
    """The stoop's swap: the folded wing's opening that best matches the spread mesh at SWAP_OPEN in that frame."""
    import itertools
    A = Applier(arm, clips)
    A.toe_verts = toe_vertex_sets(meshes['fold'])
    for o in meshes.values():
        sk = o.data.shape_keys
        if sk:
            sk.key_blocks['hidden'].value = 0.0
    sp = clips.stoop(8)
    best = None
    c = dict(SWAP_FOLD)
    step = {'out': 12, 'up': 14, 'tip_out': 12, 'tip_up': 12}
    for rnd in range(3):
        for out, up, to, tu in itertools.product(*[(c[k] - step[k], c[k], c[k] + step[k]) for k in ('out', 'up', 'tip_out', 'tip_up')]):
            fp = {'out': out, 'up': up, 'twist': 0, 'tip_out': to, 'tip_up': tu}
            A.apply(dict(sp, fold=fp, wing=dict(SWAP_OPEN)), 0, key=False)
            bpy.context.view_layer.update()
            coO, triO = evaluated_co(meshes['open'])
            coF, triF = evaluated_co(meshes['fold'])
            sc = min(pair_iou(coO, triO, coF, triF, VIEWS['side']), pair_iou(coO, triO, coF, triF, VIEWS['three_quarter']))
            if best is None or sc > best[0]:
                best = (sc, dict(fp))
        c = best[1]
        step = {k: max(4, v * 0.6) for k, v in step.items()}
        print('stoop round', rnd, 'overlap %.3f' % best[0], best[1])


def tune(arm, meshes, clips, body):
    """Search (1) the folded mesh's wing pose that matches the spread mesh at the half-fold, and (2) the neck, head
    and tail turns that put the perched frame on the approved static saker_fist.glb. Prints the best of each."""
    A = Applier(arm, clips)
    A.toe_verts = toe_vertex_sets(meshes['fold'])
    for o in meshes.values():      # both meshes drawn (the morph 'hidden' at 0) while they are compared
        sk = o.data.shape_keys
        if sk:
            sk.key_blocks['hidden'].value = 0.0
    # the spread mesh folded by its bones as far as it still reads right; the folded mesh opened (shoulder and
    # primaries) to match it
    import itertools
    base = {'pitch': 50, 'tb': PERCH_TB, 'feet': 'cuff', 'mesh': 'fold', 'fold': SWAP_FOLD}
    A.apply(dict(base), 0, key=False)
    bpy.context.view_layer.update()
    coF, triF = evaluated_co(meshes['fold'])
    best = None
    for up, sw, fo, ha in itertools.product((-12, -5, 2), (58, 65, 72), (-72, -86), (160, 175)):
        w = {'up': up, 'sweep': sw, 'fore': fo, 'hand': ha, 'twist': 0}
        A.apply(dict(base, mesh='open', wing=w), 0, key=False)
        bpy.context.view_layer.update()
        coO, triO = evaluated_co(meshes['open'])
        sc = min(pair_iou(coO, triO, coF, triF, VIEWS['side']), pair_iou(coO, triO, coF, triF, VIEWS['three_quarter']))
        if best is None or sc > best[0]:
            best = (sc, up, sw, fo, ha)
    print('fold match: best overlap %.3f with the spread wing at up %d sweep %d fore %d hand %d' % best)
    if os.environ.get('TUNE_ONLY_FOLD'):
        return best, None
    # (2) the perched frame against the approved static model, in place
    import common as _c
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.environ.get('FIST_GLB') or os.path.join(HERE, '..', '..', 'assets_src', 'birds', f'{BIRD}_fist.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    stat = [o for o in new if o.type == 'MESH' and o.name.endswith('body')][0]
    bpy.context.view_layer.update()
    coS = np.array([tuple(stat.matrix_world @ v.co) for v in stat.data.vertices]) / MM
    triS = np.array([tuple(p.vertices) for p in stat.data.polygons])
    for o in new:
        o.hide_render = True
        o.hide_set(True)
    bestp = None
    for n1 in (0, 7, 14):
        for n2 in (-32, -24, -16):
            for n3 in (-46, -40, -34):
                for tl in (4, 10, 16):
                    sp = {'pitch': 66, 'tb': PERCH_TB, 'feet': 'cuff', 'mesh': 'fold', 'neck': (n1, n2, n3), 'tail_lift': tl}
                    A.apply(sp, 0, key=False)
                    bpy.context.view_layer.update()
                    coF, triF = evaluated_co(meshes['fold'])
                    sc = min(pair_iou(coS, triS, coF, triF, VIEWS['side']), pair_iou(coS, triS, coF, triF, VIEWS['front']))
                    if bestp is None or sc > bestp[0]:
                        bestp = (sc, n1, n2, n3, tl)
    print('perched fit: best overlap %.3f at neck %d %d head %d tail %d' % bestp)
    for o in new:
        bpy.data.objects.remove(o)
    return best, bestp


def group_set(o, prefixes, wmin=0.3):
    names = {g.index for g in o.vertex_groups if g.name.startswith(prefixes)}
    return np.array([v.index for v in o.data.vertices if any(g.group in names and g.weight > wmin for g in v.groups)], int)


def inside_body(body, Q):
    """Which rest-pose points (mm, N x 3) lie inside the body's surface (by the nearest section)."""
    C = np.array([tuple(sec.c) for sec in body.secs])
    U = np.array([tuple(sec.u) for sec in body.secs])
    Vv = np.array([tuple(sec.v) for sec in body.secs])
    rows = np.array(body.rows)
    out = np.zeros(len(Q), bool)
    for i, q in enumerate(Q):
        j = int(np.argmin(((C - q) ** 2).sum(1)))
        x, y = (q - C[j]) @ U[j], (q - C[j]) @ Vv[j]
        a = rows[j, 1] if x >= 0 else rows[j, 2]
        out[i] = (abs(x) / a) ** 2 + (abs(y) / rows[j, 3]) ** 2 < 1.0
    return out


def motion_checks(arm, meshes, frames_mesh, clips, body):
    """The build's own checks, per clip: the swap's silhouette overlap, the feet out of sight in flight, the
    wing's flex in the beat."""
    sc = bpy.context.scene
    feetO = group_set(meshes['open'], ('toe', 'tarsus'))
    feetF = group_set(meshes['fold'], ('toe', 'tarsus'))
    wingO = np.array(sorted(group_set(meshes['open'], ('wing_fore', 'wing_hand'))), int)
    for name, (n, fn, loop) in CLIPS.items():
        if name in CUFF_CLIPS or name in PERCH_CLIPS:
            support_checks(arm, meshes, frames_mesh, name, n, 'cuff' if name in CUFF_CLIPS else 'perch')
        use_clip(arm, name)
        fm = frames_mesh[name]
        for f in range(1, n):
            if fm[f] != fm[f - 1]:
                worst = 1.0
                show_both(arm)
                for g in (f - 1, f):
                    sc.frame_set(g)
                    a, ta = evaluated_co(meshes['fold'])
                    b, tb = evaluated_co(meshes['open'])
                    worst = min(worst, pair_iou(a, ta, b, tb, VIEWS['side']), pair_iou(a, ta, b, tb, VIEWS['three_quarter']))
                print(f'{name}: swap {fm[f - 1]} -> {fm[f]} at frame {f}: silhouette overlap {worst:.3f} (the lower of side and three-quarter, frames {f - 1} and {f})')
        if any(m == 'open' for m in fm):
            worst, wf = 0, None
            for f in range(n):
                if fm[f] != 'open':
                    continue
                sc.frame_set(f)
                co, _ = evaluated_co(meshes['open'])
                M = np.array((arm.matrix_world @ arm.pose.bones['body'].matrix @ arm.pose.bones['body'].bone.matrix_local.inverted()).inverted())
                Q = co[wingO] * MM
                R = (Q @ M[:3, :3].T + M[:3, 3]) / MM
                cnt = int(inside_body(body, R).sum())
                if cnt > worst:
                    worst, wf = cnt, f
            print(f'{name}: forearm and hand vertices inside the body (spread mesh): max {worst}' + (f' (frame {wf})' if wf is not None else ''))
        flying = [f for f in range(n) if FRAMES_FEET[name][f] not in PLANTED and HIDDEN_FEET[name][f]]
        if flying:
            worst, wf = 0, None
            for f in flying:
                sc.frame_set(f)
                o = meshes[fm[f]]
                idx = feetO if fm[f] == 'open' else feetF
                co, _ = evaluated_co(o)
                M = np.array((arm.matrix_world @ arm.pose.bones['body'].matrix @ arm.pose.bones['body'].bone.matrix_local.inverted()).inverted())
                Q = co[idx] * MM
                R = (Q @ M[:3, :3].T + M[:3, 3]) / MM
                out = int((~inside_body(body, R)).sum())
                if out > worst:
                    worst, wf = out, f
                if name == 'cast_off':
                    pass
            print(f'{name}: feet and tarsi vertices outside the body while drawn up (frames {flying[0]}-{flying[-1]}, {len(flying)} frames): max {worst}' + (f' (frame {wf})' if wf is not None else ''))
        if name == 'flight':
            d = []
            for f in range(n):
                sc.frame_set(f)
                pb = arm.pose.bones
                sh = pb['wing_up.L'].head
                tip = pb['wing_hand.L'].tail
                d.append((tip - sh).length / MM)
            print(f'flight: shoulder to wingtip {min(d):.0f} to {max(d):.0f} mm ({100 * min(d) / max(d):.0f}% at the most flexed)')


CUFF_CLIPS = ('hood_off', 'hood_on', 'cast_off', 'land_cuff')
PERCH_CLIPS = ('perch_idle', 'perch_hooded', 'rouse', 'land_perch')
FLYING = ('flight', 'glide', 'stoop', 'bind')


def planted_frames(name, n, frames_feet):
    return [f for f in range(n) if frames_feet[name][f] in PLANTED]


def all_sheets(arm, meshes, frames_mesh, out, q, only=None):
    import gear
    at = common.Atlas(dict(gear.BLOCKS))
    gc, go = at.paint(256, gear.painters())
    gm = common.material('gear', gc, go)
    cuff = common.obj('dass', common.to_mesh('dass', gear.dass(0), at), gm)
    perch = common.obj('wakr', common.to_mesh('wakr', gear.wakr(0), at), gm)
    me = bpy.data.meshes.new('sand')
    r = 3.0
    me.from_pydata([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)], [], [(0, 1, 2, 3)])
    sand = common.obj('sand', me, None)
    sm = bpy.data.materials.new('sandm')
    sm.use_nodes = True
    sm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.62, 0.52, 0.38, 1)
    me.materials.append(sm)
    res = (240, 180) if q else (360, 270)
    paths = []
    for name, (n, fn, loop) in CLIPS.items():
        if only and name not in only:
            continue
        cuff.hide_render = name not in CUFF_CLIPS
        perch.hide_render = name not in PERCH_CLIPS
        sand.hide_render = name != 'mantle'
        k = 12
        frames = sorted(set(int(round(i * (n - 1) / (k - 1))) for i in range(k)))
        far = name in FLYING or name in ('cast_off', 'land_cuff', 'land_perch')
        d = 1.15 if far else 0.75
        side = lambda f, r, d=d: ((r.x + 0.1, r.y + 4, r.z + 0.2), (r.x + 0.1, r.y, r.z + 0.2), d)
        tq = lambda f, r, d=d: ((r.x + 1.2 * d, r.y + 1.0 * d, r.z + 0.2 + 0.55 * d), (r.x + 0.08, r.y, r.z + 0.18), None)
        if name in FLYING:
            side = lambda f, r, d=d: ((r.x + 0.1, r.y + 4, r.z), (r.x + 0.1, r.y, r.z), d)
            tq = lambda f, r, d=d: ((r.x + 1.3 * d, r.y - 1.1 * d, r.z + 0.6 * d), (r.x + 0.1, r.y, r.z), None)
        if name in ('land_cuff', 'land_perch'):      # she comes in from the side: seen across her path, from ahead of the fist
            side = lambda f, r, d=d: ((r.x + 4, r.y, r.z + 0.25), (r.x, r.y, r.z + 0.25), d * 1.2)
            paths.append(contact_sheet(arm, meshes, frames_mesh, name, frames, out, res=res, samples=6 if q else 12, cam=side,
                                       label=f'{name}, from ahead of the fist, across her path (30 frames a second): awaiting the owner\'s approval of the motion', tag='front'))
        else:
            paths.append(contact_sheet(arm, meshes, frames_mesh, name, frames, out, res=res, samples=6 if q else 12, cam=side,
                                       label=f'{name}, from the side (30 frames a second): awaiting the owner\'s approval of the motion', tag='side'))
        paths.append(contact_sheet(arm, meshes, frames_mesh, name, frames, out, res=res, samples=6 if q else 12, cam=tq,
                                   label=f'{name}, three-quarter (30 frames a second): awaiting the owner\'s approval of the motion', tag='tq'))
    return paths


if __name__ == '__main__':
    OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'out')
    os.makedirs(OUT, exist_ok=True)
    mode = sys.argv[3] if len(sys.argv) > 3 else ''
    if mode == 'tune':
        CLIPS_KEEP = dict(CLIPS)
        CLIPS.clear()
    if os.environ.get('BUILD_ONLY'):      # for trying one clip: build just these
        for k in [k for k in CLIPS if k not in os.environ['BUILD_ONLY'].split(',')]:
            del CLIPS[k]
    arm, meshes, frames_mesh, B, clips = build_saker(OUT)
    if mode == 'tune':
        CLIPS.update(CLIPS_KEEP)
        if os.environ.get('TUNE_CAST'):
            tune_cast_swap(arm, meshes, clips)
        elif os.environ.get('TUNE_SWAPS'):
            tune_swaps(arm, meshes, clips)
        else:
            tune(arm, meshes, clips, BODY[0])
        sys.exit(0)
    only = os.environ.get('CLIPS_ONLY', '').split(',') if os.environ.get('CLIPS_ONLY') else None
    if mode in ('sheets', 'quick'):
        all_sheets(arm, meshes, frames_mesh, OUT, mode == 'quick', only)
        if not only or 'feet' in only:
            contact_sheet(arm, meshes, frames_mesh, 'cast_off', [0, 12], OUT, res=(480, 360), samples=12,
                          cam=lambda f, r: ((0.35, 0.3, 0.08), (0.0, 0.0, 0.0), None), label='the feet on the cuff', tag='feet')
        if os.environ.get('GIFS'):
            bpy.data.objects['dass'].hide_render = False
            bpy.data.objects['wakr'].hide_render = True
            bpy.data.objects['sand'].hide_render = True
            follow = lambda f, r: ((r.x + 0.15, r.y + 4, r.z + 0.2), (r.x + 0.15, r.y, r.z + 0.2), 1.15)
            strip_gif(arm, meshes, frames_mesh, 'cast_off', list(range(0, 39)), OUT, cam=follow)
            bpy.data.objects['dass'].hide_render = True
            strip_gif(arm, meshes, frames_mesh, 'flight', list(range(0, 14)), OUT, repeat=3,
                      cam=lambda f, r: ((r.x + 1.6, r.y - 1.3, r.z + 0.8), (r.x + 0.15, r.y, r.z + 0.05), None))
    if mode == 'measure':
        motion_checks(arm, meshes, frames_mesh, clips, BODY[0])
        print('hand-overs, the skeleton without the jesses (simulated cords, listed after):')
        handover_checks(arm, HANDOVERS, CLIPS, skip=('jess', 'hood'))
        print('hand-overs, the jesses alone:')
        handover_checks(arm, HANDOVERS, CLIPS, skip=tuple(b.name for b in arm.pose.bones if not b.name.startswith('jess')))
        import gear
        for name, (n, fn, loop) in CLIPS.items():
            on = planted_frames(name, n, FRAMES_FEET)
            if not on:
                continue
            surf = clips.cuff if name in CUFF_CLIPS else flat_surface
            d = talon_depths(arm, meshes, frames_mesh, name, n, surf)
            print(f'{name}: deepest toe or talon vertex under the {"cuff" if name in CUFF_CLIPS else "surface"} '
                  f'while standing on it: {max(d[f] for f in on):.1f} mm over {len(on)} frames')

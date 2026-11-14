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


# ------------------------------------------------------------------ the saker's rest meshes, tagged
def saker_rest(wings, level=0):
    """The saker in the rest pose: body level (its tail base at the origin), the feet below, toes flat. Returns
    {'body': [(piece, tag)], 'hood': [...], 'jesses': [...]}, the named points (mm) and the body."""
    import saker
    pose = dict(saker.POSES['flight'])
    pose.update({'wings': wings, 'tucked': False, 'foot': (75, 22, -125), 'foot_turn': 8, 'tail_droop': 0,
                 'tail_spread': 1.0, 'wing_dihedral': 0.0})
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
    add('neck1', body.at(178), body.at(212), 'body', 'the lower neck: with neck2 keeps the head level as the body tilts')
    add('neck2', body.at(212), body.at(240), 'neck1', 'the upper neck')
    add('head', body.at(240), body.at(292), 'neck2', 'the head: looks around; carries beak, eyes and hood')
    add('hood', body.at(252) + V3((0, 0, 20)), body.at(252) + V3((0, 0, 50)), 'head', 'the hood: lifted off and set on')
    add('tail', tp(20, 3), tp(-205, 3), 'body', 'the tail: lifts, drops and fans (by its width scale)')
    for side, s in ((1, 'L'), (-1, 'R')):
        add(f'fold.{s}', tp(160, 25, 52 * side), tp(-135, 12, 10 * side), 'body',
            'the folded wing (folded mesh only): lifts, droops, opens a little before the swap')
        add(f'wing_up.{s}', tp(130, 8, 30 * side), tp(130, 8, 120 * side), 'body', 'the arm (humerus): the wingbeat')
        add(f'wing_fore.{s}', tp(130, 8, 120 * side), tp(125, 8, 215 * side), f'wing_up.{s}', 'the forearm: the fold at the elbow')
        add(f'wing_hand.{s}', tp(125, 8, 215 * side), tp(40, 0, 600 * side), f'wing_fore.{s}', 'the hand and primaries: the fold at the wrist, the upstroke flick')
        k = 'l' if side > 0 else 'r'
        knee = tp(95, -20, 20 * side)
        add(f'shank.{s}', knee, pts['ankle_' + k], 'body', 'the shank (tibia, the trousers): the leg reaches and tucks')
        add(f'tarsus.{s}', pts['ankle_' + k], pts['foot_' + k], f'shank.{s}', 'the tarsus: with the shank holds the foot planted')
        f = pts['foot_' + k]
        import saker
        for ti, (hd, length, r, claw, curl) in enumerate(saker.SPEC['toes']):
            a = math.radians((hd * side if abs(hd) != 180 else hd) + 8 * side)
            dv = V3((math.cos(a), math.sin(a), 0))
            nm = TOE_NAMES[ti]
            j = length * 0.5
            add(f'{nm}1.{s}', f + dv * -2, f + dv * j, f'tarsus.{s}', f'the {TOE_WHY[ti]}, first joint: each toe lies on the cuff its own way')
            add(f'{nm}2.{s}', f + dv * j, f + dv * (length - 2), f'{nm}1.{s}', f'the {TOE_WHY[ti]}, last joints and talon: curl and hook in')
        a = pts['tarsus_' + k] + V3((7.4, 0, 0))
        for j in range(3):
            add(f'jess{j + 1}.{s}', a + V3((0, 0, -JESS_LEN * j / 3)), a + V3((0, 0, -JESS_LEN * (j + 1) / 3)),
                f'tarsus.{s}' if j == 0 else f'jess{j}.{s}', 'a third of the jess: the cord bends and trails')
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
            if d < 170:
                W.append({'body': 1.0})
            elif d < 205:
                W.append(blend('body', 'neck1', (d - 170) / 35))
            elif d < 230:
                W.append(blend('neck1', 'neck2', (d - 205) / 25))
            elif d < 255:
                W.append(blend('neck2', 'head', (d - 230) / 25))
            else:
                W.append({'head': 1.0})
        return W
    if kind in ('head',):
        return [{'head': 1.0} for _ in pc.V]
    if kind == 'hood':
        return [{'hood': 1.0} for _ in pc.V]
    if kind == 'tail':
        root = B['tail'][0]
        return [blend('body', 'tail', (root.x - q.x) / 40.0) for q in pc.V]
    if kind == 'fold':
        return [blend('body', f'fold.{s}', (175 - q.x) / 40.0) for q in pc.V]
    if kind == 'wing':
        out = []
        for q in pc.V:
            y = abs(q.y)
            if y < 60:
                out.append(blend('body', f'wing_up.{s}', (y - 30) / 30))
            elif y < 135:
                out.append(blend(f'wing_up.{s}', f'wing_fore.{s}', (y - 105) / 30))
            else:
                out.append(blend(f'wing_fore.{s}', f'wing_hand.{s}', (y - 195) / 40))
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
            f = (start.z - q.z) / JESS_LEN * 3.0       # 0..3 along the cord
            j = min(int(f), 2)
            t = f - j
            if t > 0.75 and j < 2:
                out.append(blend(f'jess{j + 1}.{s}', f'jess{j + 2}.{s}', (t - 0.75) / 0.5))
            elif t < 0.25 and j > 0:
                out.append(blend(f'jess{j}.{s}', f'jess{j + 1}.{s}', (t + 0.25) / 0.5))
            else:
                out.append({f'jess{j + 1}.{s}': 1.0})
        return out
    if kind == 'swivel':
        return [{'jess3.R': 1.0} for _ in pc.V]
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

    def key(self, frame):
        for p in self.pb:
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

    def __init__(self, start, n=4, length=JESS_LEN):
        self.seg = length / (n - 1)
        self.p = [V3(start) + V3((0, 0, -self.seg * i)) for i in range(n)]
        self.q = [x.copy() for x in self.p]

    def step(self, anchor, air, dt=1.0 / FPS, sub=4):
        g = V3((0, 0, -9810.0))
        for _ in range(sub):
            h = dt / sub
            self.p[0] = V3(anchor)
            for i in range(1, len(self.p)):
                v = (self.p[i] - self.q[i]) * 0.92
                self.q[i] = self.p[i].copy()
                drag = (V3(air) - v / h) * 0.9 * h      # pulled toward moving with the air
                self.p[i] = self.p[i] + v + (g * h * h) + drag * h * 8
            for _ in range(3):
                self.p[0] = V3(anchor)
                for i in range(1, len(self.p)):
                    d = self.p[i] - self.p[i - 1]
                    L = d.length or 1e-6
                    corr = d * ((L - self.seg) / L)
                    if i == 1:
                        self.p[i] = self.p[i] - corr
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


PERCH_TB = V3((-58, 0, 80))
PLANTED = ('cuff', 'perch', 'ground')
FRAMES_FEET = {}
FOOT_LIFT = 2.5      # mm: the foot's centre held this far above the support, so the soles' pads rest on it


def flat_surface(x, y):
    """The perch's padded top and the ground: flat at the feet's level."""
    return 0.0      # the tail base when perched (the static saker_fist's pose: body pitch 66)


class SakerClips:
    """Each clip returns, for a frame, a dict the poser applies. Distances mm, angles degrees."""

    def __init__(self):
        import gear
        self.cuff = gear.dass_top
        self.beat = 7          # frames a wingbeat at 30 fps: 4.29 Hz (Pennycuick 1996 predicts 4.3-4.8 Hz)

    # the shared pieces of a pose
    def perched(self, f, pitch=66.0, crouch=0.0):
        tb = PERCH_TB + V3((10 * crouch, 0, -16 * crouch))
        return {'pitch': pitch - 14 * crouch, 'tb': tb, 'feet': 'cuff', 'mesh': 'fold'}

    def wings_flap(self, ph, amp=40.0, mean=5.0):
        """The wingbeat: ph 0..1 (0 the top of the upstroke). The arm sweeps up and down; on the upstroke the wing
        flexes at the elbow and wrist (the hand drawn back and in, its tip trailing) and the hand turns its leading
        edge up (supinates); on the downstroke the wing is fully spread and the hand turns its leading edge down."""
        up = mean + amp * math.cos(2 * math.pi * ph)
        down = math.sin(2 * math.pi * ph)        # positive in the downstroke
        flex = max(0.0, -down) ** 0.8            # the upstroke
        return {'up': up, 'sweep': 10 * flex, 'fore': -34 * flex, 'hand': 58 * flex, 'twist': 6 * down,
                'hand_up': 22 * flex - 6 * max(0.0, down), 'hand_twist': 16 * down - 10 * flex}

    HALF_FOLD = {'up': 26, 'sweep': 52, 'fore': -78, 'hand': 92, 'twist': 0, 'hand_up': 0, 'hand_twist': 0}
    RAISED = {'up': 62, 'sweep': 22, 'fore': -14, 'hand': 16, 'twist': 0, 'hand_up': 8, 'hand_twist': 0}

    def cast_off(self, f):
        """The lean and crouch on the fist (0-14), the wings opening, the push of the legs (15-19) with the first
        downstroke; the feet leave at 19 and close and draw up at once; she drops below the fist in the first beats,
        then climbs away. The folded mesh to frame 13; at 14 the spread mesh, its wings folded by the bones to the
        point where it still reads right, then opened by them."""
        lean = ramp(f, 3, 14)
        if f < 14:
            p = self.perched(f, pitch=66 - 22 * lean, crouch=lean)
            p.update({'fold_lift': 30 * ramp(f, 9, 13.5), 'jess_hold': True, 'mesh': 'fold'})
            return p
        # the spread mesh from frame 14: unfolding (14-18), then the beat
        g = (f - 18) / self.beat
        beat = self.wings_flap((g + 0.75) % 1.0, amp=46, mean=4) if f >= 18 else None
        if f < 18:
            k = ramp(f, 14, 18)
            w = {kk: lerp(self.HALF_FOLD[kk], self.RAISED[kk], k) for kk in self.HALF_FOLD}
        else:
            k = ramp(f, 18, 21)
            w = {kk: lerp(self.RAISED[kk], beat[kk], k) if f < 21 else beat[kk] for kk in self.RAISED}
        # the path: still on the fist to 15, the push to 19, then away: a dip below the fist, then the climb
        push = ramp(f, 15, 19)
        t = max(0.0, (f - 17) / FPS)
        x = 60 * push + 0.5 * 5.0 * t * t * 1000 + 900 * t
        z = -10 * push - 0.5 * 2.4 * t * t * 1000 + 0.5 * 4.4 * max(0.0, t - 0.25) ** 2 * 1000
        pitch = keys(f, [(14, 44), (17, 36), (20, 24), (28, 14), (40, 8)])
        tb = PERCH_TB + V3((10, 0, -16)) + V3((x, 0, z))
        if f < 19:
            feet = 'cuff'
        else:
            feet = ('push', ramp(f, 19, 25))
        return {'pitch': pitch, 'tb': tb, 'feet': feet, 'mesh': 'open', 'wing': w,
                'tail_spread': lerp(1.3, 1.08, ramp(f, 16, 32)), 'jess_hold': f < 19, 'clench': ramp(f, 19, 24)}

    def flight(self, f):
        ph = (f / self.beat) % 1.0
        w = self.wings_flap(ph)
        bob = -8 * math.cos(2 * math.pi * ph)
        return {'pitch': 4 + 2 * math.sin(2 * math.pi * ph), 'tb': V3((0, 0, bob)), 'feet': ('free', 1.0), 'mesh': 'open',
                'wing': w, 'tail_spread': 1.05, 'clench': 1.0, 'air': V3((-20000, 0, 0))}

    def land(self, f, surface):
        """A glide in, the flare (body up to 55 degrees, the wings forward and beating to brake, the tail fanned and
        dropped), the legs thrown forward, contact at frame 28, the wings folded by the bones to the half-fold, the
        swap to the folded mesh at 39, the settle to the perched 66 degrees by 45."""
        s_ = min(f / 28.0, 1.0)
        x = -3000 * (1 - s_) ** 2
        z = 400 * (1 - s_) ** 2
        pitch = keys(f, [(0, 6), (14, 14), (26, 55), (34, 62), (45, 66)])
        tb_air = V3((x, 0, z)) + PERCH_TB + V3((25, 0, -10)) * (1 - ramp(f, 26, 40))
        brake = ramp(f, 12, 18) * (1 - ramp(f, 27, 30))
        if f < 14:
            w = {'up': 8 + 2 * math.sin(f / 3), 'sweep': -4, 'fore': -6, 'hand': 10, 'twist': 0, 'hand_twist': -4}
        else:
            b = self.wings_flap(((f - 14) / 6.0) % 1.0, amp=34, mean=14)
            b['sweep'] -= 22 * brake        # the wings brought forward to brake
            fold = ramp(f, 29, 38.5)
            w = {k: lerp(b[k], self.HALF_FOLD.get(k, 0.0), fold) for k in b}
        mesh = 'open' if f < 39 else 'fold'
        reach = ramp(f, 14, 24)
        feet = surface if f >= 28 else ('reach', reach)
        return {'pitch': pitch, 'tb': tb_air, 'feet': feet, 'mesh': mesh, 'wing': w,
                'fold_lift': 30 * (1 - ramp(f, 39, 45)),
                'tail_spread': lerp(1.0, 1.45, brake) if f < 32 else lerp(1.45, 1.0, ramp(f, 32, 42)),
                'tail_drop': 18 * brake, 'open_toes': reach * (1 - ramp(f, 27, 29))}

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
                'mesh': 'fold', 'head_yaw': yaw, 'head_pitch': 4 * math.sin(3 * c),
                'tail_drop': -10 * math.exp(-((f - 90) / 2.5) ** 2), 'fold_lift': 2 * max(0.0, math.sin(c))}

    def rouse(self, f):
        """The rouse: the feathers raised and shaken through, about half a second of shaking, then smoothed."""
        sh = ramp(f, 6, 9) * (1 - ramp(f, 22, 26))
        osc = math.sin(2 * math.pi * f * 7.0 / FPS)
        return {'pitch': 66 + 3 * sh, 'tb': PERCH_TB + V3((0, 0, 4 * sh)), 'feet': 'perch', 'mesh': 'fold',
                'roll': 9 * sh * osc, 'head_yaw': 22 * sh * math.sin(2 * math.pi * f * 7.0 / FPS + 0.6),
                'fold_lift': 10 * ramp(f, 2, 7) * (1 - ramp(f, 24, 32)) + 4 * sh * abs(osc),
                'tail_spread': 1.0 + 0.25 * sh * abs(osc)}

    def hood_off(self, f):
        """On the fist: the falconer draws the braces and lifts the hood off (the hand is not drawn); she looks round."""
        lift = 70 * ramp(f, 6, 16)
        yaw = keys(f, [(0, 0), (18, 0), (23, 30), (27, -18), (30, 0)])
        return {'pitch': 66, 'tb': PERCH_TB, 'feet': 'cuff', 'mesh': 'fold', 'hood': 1.0 if f < 17 else 0.0,
                'hood_lift': lift, 'head_yaw': yaw, 'head_pitch': 6 * ramp(f, 16, 20), 'jess_hold': True}

    def hood_on(self, f):
        lift = 70 * (1 - ramp(f, 8, 20))
        return {'pitch': 66, 'tb': PERCH_TB, 'feet': 'cuff', 'mesh': 'fold', 'hood': 1.0 if f >= 7 else 0.0,
                'hood_lift': lift, 'head_pitch': -4 * ramp(f, 4, 8) * (1 - ramp(f, 18, 24)), 'jess_hold': True}

    def glide(self, f):
        c = 2 * math.pi * f / 60.0
        w = {'up': 6 + 1.5 * math.sin(c), 'sweep': -2, 'fore': -6, 'hand': 8 + 2 * math.sin(2 * c), 'twist': 0,
             'hand_up': 2, 'hand_twist': -4}
        return {'pitch': 3, 'roll': 4 * math.sin(c), 'tb': V3((0, 0, 3 * math.sin(c))), 'feet': ('free', 1.0),
                'mesh': 'open', 'wing': w, 'tail_spread': 1.0, 'clench': 1.0, 'air': V3((-15000, 0, 0))}

    def stoop(self, f):
        """From the glide into the stoop: the wings drawn in to the body, the body tipped down 55 degrees, the head
        in line looking ahead; held."""
        k = ramp(f, 0, 12)
        g = self.glide(0)['wing']
        tight = {'up': 14, 'sweep': 58, 'fore': -72, 'hand': 88, 'twist': 0, 'hand_up': 4, 'hand_twist': 0}
        w = {kk: lerp(g.get(kk, 0.0), tight[kk], k) for kk in tight}
        pitch = -55 * k + 1.5 * math.sin(f / 2.0) * k
        return {'pitch': pitch, 'head_pitch': 0.8 * pitch, 'tb': V3((0, 0, 0)), 'feet': ('free', 1.0), 'mesh': 'open',
                'wing': w, 'tail_spread': 1.0 - 0.1 * k, 'clench': 1.0, 'air': V3((-30000 * math.cos(math.radians(pitch)), 0, 30000 * math.sin(math.radians(-pitch))))}

    def bind(self, f):
        """Binding to the quarry: thrown up from the dive, the wings braking, the legs and open feet struck forward;
        the feet close at frame 10 (on the quarry, not drawn), then heavy beats to hold."""
        pitch = keys(f, [(0, -30), (8, 38), (14, 30), (24, 20)])
        if f < 10:
            w = {kk: lerp(self.RAISED[kk], self.wings_flap(0.25, amp=46)[kk], ramp(f, 2, 10)) for kk in self.RAISED}
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


CLIPS = {      # name: (frames, method, loops)
    'perch_idle': (120, 'perch_idle', True), 'rouse': (36, 'rouse', False), 'hood_off': (30, 'hood_off', False),
    'hood_on': (30, 'hood_on', False), 'cast_off': (41, 'cast_off', False), 'flight': (14, 'flight', True),
    'glide': (60, 'glide', True), 'stoop': (40, 'stoop', False), 'bind': (24, 'bind', False),
    'mantle': (60, 'mantle', True), 'land_cuff': (46, 'land_cuff', False), 'land_perch': (46, 'land_perch', False),
}


# ------------------------------------------------------------------ applying a pose
REST_FOOT = (75.0, 22.0, -125.0)        # the rest pose's foot, body frame (the tail base at the origin)
TUCK_FOOT = (24.0, 9.0, -10.0)          # drawn up under the tail coverts (as saker.POSES['flight'])
REACH_FOOT = (150.0, 26.0, -120.0)
PUSH_FOOT = (-10.0, 20.0, -95.0)        # straight back and down at the end of the kick      # thrown forward to take the cuff when landing
FIST_JESS = (36.0, 2.0, -26.0)          # where the falconer's fist holds the jesses (saker_fist)
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
        R = Matrix.Rotation(math.radians(-sp['pitch']), 4, 'Y') @ Matrix.Rotation(math.radians(sp.get('roll', 0.0)), 4, 'X')
        return Matrix.Translation(V3(sp['tb']) * MM) @ R, R

    def to_world(self, W, p):
        return (W @ (V3(p) * MM)) / MM

    def toes_on(self, s, side, surface):
        """Curl each toe, joint by joint, so the toe and its talon lie on the surface z = surface(x, y): of the
        angles that keep every vertex of that segment (the toe's skin, and on the last joint the talon) at or
        above the surface, the one that brings the lowest of them closest to it (0.5 mm)."""
        P = self.P
        for nm in TOE_NAMES:
            for j in (1, 2):
                b = f'{nm}{j}.{s}'
                V = self.toe_verts.get(b)
                bpy.context.view_layer.update()
                p = P.pb[b]
                M0 = p.matrix.copy()
                head = M0.translation
                cur = (M0.to_3x3() @ V3((0, 1, 0))).normalized()
                flat = V3((cur.x, cur.y, 0))
                flat = flat.normalized() if flat.length > 1e-6 else cur
                local = P.rest[b].inverted()
                best, best_M = None, M0
                for a in np.linspace(-35, 95, 131):
                    ar = math.radians(a)
                    want = flat * math.cos(ar) + V3((0, 0, -1)) * math.sin(ar)
                    r = cur.rotation_difference(want).to_matrix().to_4x4()
                    M = Matrix.Translation(head) @ r @ Matrix.Translation(-head) @ M0
                    A = np.array(M @ local)
                    W = (V @ A[:3, :3].T + A[:3, 3]) / MM
                    clear = min(w[2] - surface(w[0], w[1]) for w in W)
                    score = abs(clear - 0.5) + (1000 if clear < -0.3 else 0)
                    if best is None or score < best:
                        best, best_M = score, M
                p.matrix = best_M

    def apply(self, sp, frame):
        P = self.P
        P.reset()
        W, R = self.body_matrix(sp)
        root_at = V3(sp['tb']) - PERCH_TB
        P.place('root', Matrix.Translation((root_at - self.rest_root) * MM))
        P.place('body', W)
        k = sp['pitch'] / 66.0
        P.turn('neck1', (0, -1, 0), 20 * k)
        P.turn('neck2', (0, -1, 0), -46 * k)
        P.turn('head', (0, -1, 0), -40 * k + sp.get('head_pitch', 0.0))
        if sp.get('head_yaw'):
            P.turn('head', (0, 0, 1), sp['head_yaw'])
        P.turn('tail', (0, 1, 0), sp.get('tail_drop', 0.0) - 0.15 * sp['pitch'] * (1 if sp['mesh'] == 'fold' else 0))
        P.pb['tail'].scale = (sp.get('tail_spread', 1.0), 1, 1)
        hood = sp.get('hood', 0.0)
        P.pb['hood'].scale = (1, 1, 1) if hood >= 1.0 else (0.001,) * 3
        P.pb['hood'].location = (0, sp.get('hood_lift', 0.0) * MM, 0)      # the bone points up: its Y is up
        w = sp.get('wing')
        for side, s in ((1, 'L'), (-1, 'R')):
            if w:
                P.turn(f'wing_up.{s}', (side, 0, 0), w['up'])
                P.turn(f'wing_up.{s}', (0, 0, side), w['sweep'])
                P.turn(f'wing_up.{s}', (0, side, 0), w.get('twist', 0.0))
                P.turn(f'wing_fore.{s}', (0, 0, side), w['fore'])
                P.turn(f'wing_hand.{s}', (0, 0, side), w['hand'])
                P.turn(f'wing_hand.{s}', (side, 0, 0), w.get('hand_up', 0.0))
                P.turn(f'wing_hand.{s}', (0, side, 0), w.get('hand_twist', 0.0))
            lift = sp.get('fold_lift', 0.0)
            if lift:
                P.turn(f'fold.{s}', (0, 0, -side), 0.6 * lift)
                P.turn(f'fold.{s}', (side, 0, 0), 0.5 * lift)
        # the legs and toes
        feet = sp['feet']
        for side, s in ((1, 'L'), (-1, 'R')):
            if feet in PLANTED:
                target = V3((0.0, 22.0 * side, FOOT_LIFT)) + V3(sp.get('foot_shift', (0, 0, 0))) * (1 if side > 0 else 0)
                P.leg(s, target, V3((-1, 0, -0.25)))
                self.toes_on(s, side, self.C.cuff if feet == 'cuff' else flat_surface)
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
                pole = (R.to_3x3() @ V3((-1, 0, -0.3)))
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
        for side, s in ((1, 'L'), (-1, 'R')):
            anchor = P.head_of(f'jess1.{s}')
            pts = self.cords[s].step(anchor, air)
            if sp.get('jess_hold'):
                hold = V3(FIST_JESS) * V3((1, side, 1))
                # held: the cord's end is in the falconer's fist
                for i in range(1, 4):
                    pts[i] = anchor.lerp(hold, i / 3.0)
                self.cords[s].q = [p.copy() for p in pts]
            for j in range(3):
                P.aim(f'jess{j + 1}.{s}', pts[j + 1])
        P.key(frame)
        # measures
        if feet in PLANTED:
            for s in ('L', 'R'):
                side = 1 if s == 'L' else -1
                want = V3((0, 22 * side, FOOT_LIFT)) + V3(sp.get('foot_shift', (0, 0, 0))) * (1 if side > 0 else 0)
                self.log.append(('slide', frame, s, (P.tail_of(f'tarsus.{s}') - want).length))


# ------------------------------------------------------------------ build, export, sheets
def build_saker(out, sheets=False):
    import paint
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    parts_f, pts, body = saker_rest('fold')
    parts_o, _, _ = saker_rest('open')
    B = saker_bones(pts, body)
    atlas = paint.atlas('saker')
    col, orm = paint.paint('saker', atlas, 512, body)
    mat = common.material('saker', col, orm)
    arm = make_armature('saker_rig', B)
    meshes = {
        'fold': skinned_mesh('saker_fold', parts_f['body'], body, B, atlas, mat, arm),
        'open': skinned_mesh('saker_open', parts_o['body'], body, B, atlas, mat, arm),
        'hood': skinned_mesh('saker_hood', parts_f['hood'], body, B, atlas, mat, arm),
        'jesses': skinned_mesh('saker_jesses', parts_f['jesses'], body, B, atlas, mat, arm),
    }
    clips = SakerClips()
    arm.animation_data_create()
    frames_mesh = {}
    log = []
    toe_verts = toe_vertex_sets(meshes['fold'])
    for name, (n, fn, loop) in CLIPS.items():
        act = bpy.data.actions.new(name)
        arm.animation_data.action = act
        A = Applier(arm, clips)
        A.toe_verts = toe_verts
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
        for f in range(n + (1 if loop else 0)):
            sp = spec_fn(f % n)
            A.apply(sp, f)
            frames_mesh[name].append(sp['mesh'])
            FRAMES_FEET[name].append(sp['feet'] if isinstance(sp['feet'], str) else sp['feet'][0])
        log += [(name,) + e for e in A.log]
        act.use_fake_user = True
        arm.animation_data.action = None
    # the tracks only once every clip is keyed: a track playing while the next clip is posed would leak into it
    for name in CLIPS:
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 0, bpy.data.actions[name])
    # the measures: foot slide on the cuff
    for name in CLIPS:
        sl = [e[4] for e in log if e[0] == name and e[1] == 'slide']
        if sl:
            print(f'{name}: a planted foot\'s distance from its place, max {max(sl):.2f} mm over {len(sl) // 2} frames')
    path = os.path.join(out, 'saker_rig.glb')
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm, *meshes.values()]:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='ACTIONS', export_skins=True,
                              export_all_influences=False, export_force_sampling=True, export_optimize_animation_size=False,
                              export_materials='EXPORT', export_extras=False, export_image_format='AUTO')
    common.settle(path)
    t, imgs, nbytes = common.glb_report(path)
    print(f'saker_rig.glb: {", ".join(f"{k} {v}" for k, v in sorted(t.items()))}; {len(B)} bones; {nbytes / 1024:.0f} KB')
    return arm, meshes, frames_mesh, B, clips


def use_clip(arm, name):
    """Show one clip: its action played directly, every NLA track muted (so nothing else blends in)."""
    for t in arm.animation_data.nla_tracks:
        t.mute = True
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except (AttributeError, IndexError):
        pass


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
                dd = (surface or gear.dass_top)(x, y) - z
                if dd > depth:
                    depth, where = dd, (round(x), round(y), round(z), [g.name for g in o.vertex_groups if any(vg.group == g.index for vg in o.data.vertices[i].groups)])
        ev.to_mesh_clear()
        out.append(depth)
        if f in (0,) and where:
            print('   deepest at', where)
    return out


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
    path = os.path.join(out, f'saker_{name}.gif')
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
    path = os.path.join(out, f'saker_{name}_{tag or "sheet"}.jpg')
    sheet.save(path, quality=86)
    print('sheet', path)
    return path


CUFF_CLIPS = ('hood_off', 'hood_on', 'cast_off', 'land_cuff')
PERCH_CLIPS = ('perch_idle', 'rouse', 'land_perch')
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
        paths.append(contact_sheet(arm, meshes, frames_mesh, name, frames, out, res=res, samples=6 if q else 12, cam=side,
                                   label=f'{name}, from the side (30 frames a second): awaiting the owner\'s approval of the motion', tag='side'))
        paths.append(contact_sheet(arm, meshes, frames_mesh, name, frames, out, res=res, samples=6 if q else 12, cam=tq,
                                   label=f'{name}, three-quarter (30 frames a second): awaiting the owner\'s approval of the motion', tag='tq'))
    return paths


if __name__ == '__main__':
    OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'out')
    os.makedirs(OUT, exist_ok=True)
    arm, meshes, frames_mesh, B, clips = build_saker(OUT)
    mode = sys.argv[3] if len(sys.argv) > 3 else ''
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
            strip_gif(arm, meshes, frames_mesh, 'cast_off', list(range(0, 41)), OUT, cam=follow)
            bpy.data.objects['dass'].hide_render = True
            strip_gif(arm, meshes, frames_mesh, 'flight', list(range(0, 14)), OUT, repeat=3,
                      cam=lambda f, r: ((r.x + 1.6, r.y - 1.3, r.z + 0.8), (r.x + 0.15, r.y, r.z + 0.05), None))
    if mode == 'measure':
        import gear
        for name, (n, fn, loop) in CLIPS.items():
            on = planted_frames(name, n, FRAMES_FEET)
            if not on:
                continue
            surf = gear.dass_top if name in CUFF_CLIPS else flat_surface
            d = talon_depths(arm, meshes, frames_mesh, name, n, surf)
            print(f'{name}: deepest toe or talon vertex under the {"cuff" if name in CUFF_CLIPS else "surface"} '
                  f'while standing on it: {max(d[f] for f in on):.1f} mm over {len(on)} frames')

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


PERCH_TB = V3((-58, 0, 80))      # the tail base when perched (the static saker_fist's pose: body pitch 66)


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
        """The wingbeat: ph 0..1 (0 the top of the upstroke)."""
        up = mean + amp * math.cos(2 * math.pi * ph)
        down = math.sin(2 * math.pi * ph)        # positive in the downstroke's first half
        flick = max(0.0, -down)                   # the upstroke: the hand flexes back and in
        return {'up': up, 'sweep': 6 * flick, 'fore': -18 * flick, 'hand': 34 * flick, 'twist': 8 * down}

    def cast_off(self, f):
        n = 40
        if f <= 12:
            c = ramp(f, 4, 12)
            p = self.perched(f, crouch=c)
            p.update({'fold_lift': 28 * ramp(f, 7, 12), 'jess_hold': True, 'mesh': 'fold'})
            return p
        # airborne from frame 14: the root moves off the cuff, accelerating forward and up
        t = max(0.0, (f - 14) / FPS)
        x = 0.5 * 4.6 * t * t * 1000
        z = (0.5 * 1.2 * t * t - 0.3 * t * t * t) * 1000
        pitch = keys(f, [(12, 52), (18, 30), (26, 18), (40, 8)])
        tb = PERCH_TB + V3((10, 0, -16)) + V3((x, 0, z))
        ph = (f - 12) / self.beat * 0.5 + 0.0
        w = self.wings_flap(((f - 12) / self.beat) % 1.0)
        open_k = ramp(f, 12, 17)       # from the raised, swept-back pose at the swap to the full beat
        start = {'up': 55, 'sweep': 35, 'fore': -40, 'hand': 40, 'twist': 0}
        w = {k: lerp(start[k], w[k], open_k) for k in w}
        tuck = ramp(f, 26, 34)
        return {'pitch': pitch, 'tb': tb, 'feet': 'cuff' if f < 16 else ('free', tuck), 'mesh': 'open', 'wing': w,
                'tail_spread': lerp(1.25, 1.1, ramp(f, 14, 30)), 'jess_hold': f < 16, 'clench': tuck}

    def flight(self, f):
        ph = (f / self.beat) % 1.0
        w = self.wings_flap(ph)
        bob = -8 * math.cos(2 * math.pi * ph)
        return {'pitch': 4 + 2 * math.sin(2 * math.pi * ph), 'tb': V3((0, 0, bob)), 'feet': ('free', 1.0), 'mesh': 'open',
                'wing': w, 'tail_spread': 1.05, 'clench': 1.0, 'air': V3((-20000, 0, 0))}

    def land_cuff(self, f):
        s = min(f / 28.0, 1.0)
        x = -3000 * (1 - s) ** 2
        z = 400 * (1 - s) ** 2
        pitch = keys(f, [(0, 6), (14, 14), (26, 55), (34, 62), (45, 66)])
        tb_air = V3((x, 0, z)) + PERCH_TB + V3((25, 0, -10)) * (1 - ramp(f, 26, 40))
        brake = ramp(f, 12, 18) * (1 - ramp(f, 27, 30))
        if f < 14:
            w = {'up': 8 + 2 * math.sin(f / 3), 'sweep': -4, 'fore': -6, 'hand': 10, 'twist': 0}
        else:
            b = self.wings_flap(((f - 14) / 6.0) % 1.0, amp=34, mean=14)
            b['sweep'] -= 22 * brake        # the wings brought forward to brake
            fold = ramp(f, 29, 39)
            folded = {'up': 22, 'sweep': 62, 'fore': -100, 'hand': 112, 'twist': 0}
            w = {k: lerp(b[k], folded[k], fold) for k in b}
        mesh = 'open' if f < 39 else 'fold'
        reach = ramp(f, 14, 24)
        feet = 'cuff' if f >= 28 else ('reach', reach)
        return {'pitch': pitch, 'tb': tb_air, 'feet': feet, 'mesh': mesh, 'wing': w,
                'fold_lift': 18 * (1 - ramp(f, 39, 45)),
                'tail_spread': lerp(1.0, 1.45, brake) if f < 32 else lerp(1.45, 1.0, ramp(f, 32, 42)),
                'tail_drop': 18 * brake, 'clench': 0.0 if f < 28 else 0.0, 'open_toes': reach * (1 - ramp(f, 27, 29))}


CLIPS = {'cast_off': (41, 'cast_off', False), 'flight': (14, 'flight', True), 'land_cuff': (46, 'land_cuff', False)}


# ------------------------------------------------------------------ applying a pose
REST_FOOT = (75.0, 22.0, -125.0)        # the rest pose's foot, body frame (the tail base at the origin)
TUCK_FOOT = (24.0, 9.0, -10.0)          # drawn up under the tail coverts (as saker.POSES['flight'])
REACH_FOOT = (150.0, 26.0, -120.0)      # thrown forward to take the cuff when landing
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
        R = Matrix.Rotation(math.radians(-sp['pitch']), 4, 'Y')
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
        P.pb['hood'].scale = (1, 1, 1) if hood >= 1.0 else ((0.001,) * 3 if hood <= 0 else (1, 1, 1))
        if 0 < hood < 1:
            P.pb['hood'].location = (0, 0, 0)
        w = sp.get('wing')
        for side, s in ((1, 'L'), (-1, 'R')):
            if w:
                P.turn(f'wing_up.{s}', (side, 0, 0), w['up'])
                P.turn(f'wing_up.{s}', (0, 0, side), w['sweep'])
                P.turn(f'wing_up.{s}', (0, side, 0), w.get('twist', 0.0))
                P.turn(f'wing_fore.{s}', (0, 0, side), w['fore'])
                P.turn(f'wing_hand.{s}', (0, 0, side), w['hand'])
            lift = sp.get('fold_lift', 0.0)
            if lift:
                P.turn(f'fold.{s}', (0, 0, -side), 0.6 * lift)
                P.turn(f'fold.{s}', (side, 0, 0), 0.5 * lift)
        # the legs and toes
        feet = sp['feet']
        for side, s in ((1, 'L'), (-1, 'R')):
            if feet == 'cuff':
                target = V3((0.0, 22.0 * side, 0.0))
                P.leg(s, target, V3((-1, 0, -0.25)))
                self.toes_on(s, side, self.C.cuff)
            else:
                mode, kf = feet
                hang = V3(REST_FOOT) * V3((1, side, 1))
                tuck = V3(TUCK_FOOT) * V3((1, side, 1))
                reach = V3(REACH_FOOT) * V3((1, side, 1))
                if mode == 'free':
                    bf = hang.lerp(tuck, kf)
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
        if feet == 'cuff':
            for s in ('L', 'R'):
                side = 1 if s == 'L' else -1
                self.log.append(('slide', frame, s, (P.tail_of(f'tarsus.{s}') - V3((0, 22 * side, 0))).length))


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
        frames_mesh[name] = []
        for f in range(n + (1 if loop else 0)):
            sp = spec_fn(f % n)
            A.apply(sp, f)
            frames_mesh[name].append(sp['mesh'])
        log += [(name,) + e for e in A.log]
        act.use_fake_user = True
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 0, act)
        arm.animation_data.action = None
    # the measures: foot slide on the cuff
    for name in CLIPS:
        sl = [e[4] for e in log if e[0] == name and e[1] == 'slide']
        if sl:
            print(f'{name}: foot on the cuff, distance from its place max {max(sl):.2f} mm over {len(sl) // 2} frames')
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


def talon_depths(arm, meshes, frames_mesh, name, n):
    """Per frame, how deep any toe or talon vertex goes under the cuff's surface (mm)."""
    import gear
    sc = bpy.context.scene
    tr = arm.animation_data.nla_tracks[name]
    for t in arm.animation_data.nla_tracks:
        t.mute = t.name != name
    arm.animation_data.action = None
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
                dd = gear.dass_top(x, y) - z
                if dd > depth:
                    depth, where = dd, (round(x), round(y), round(z), [g.name for g in o.vertex_groups if any(vg.group == g.index for vg in o.data.vertices[i].groups)])
        ev.to_mesh_clear()
        out.append(depth)
        if f in (0,) and where:
            print('   deepest at', where)
    return out


def contact_sheet(arm, meshes, frames_mesh, name, frames, out, view='side', res=(320, 240), samples=8, cam=None,
                  with_cuff=True, label=''):
    """Renders the frames of a clip and tiles them into one JPEG with the frame numbers."""
    from PIL import Image, ImageDraw
    sc = bpy.context.scene
    for t in arm.animation_data.nla_tracks:
        t.mute = t.name != name
    st = getattr(contact_sheet, 'studio', None)
    if st is None:
        st = common.Studio(out, samples=samples, ground=False)
        contact_sheet.studio = st
    st.sc.cycles.samples = samples
    tiles = []
    for f in frames:
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
    path = os.path.join(out, f'saker_{name}{"_" + label.split()[1] if label else ""}_sheet.jpg')
    sheet.save(path, quality=86)
    print('sheet', path)
    return path


if __name__ == '__main__':
    OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'out')
    os.makedirs(OUT, exist_ok=True)
    arm, meshes, frames_mesh, B, clips = build_saker(OUT)
    if len(sys.argv) > 3 and sys.argv[3] in ('sheets', 'quick'):
        import gear
        # the cuff, at the origin (the falconer's fist, held level)
        at = common.Atlas(dict(gear.BLOCKS))
        gc, go = at.paint(256, gear.painters())
        gm = common.material('gear', gc, go)
        common.obj('dass', common.to_mesh('dass', gear.dass(0), at), gm)
        q = sys.argv[3] == 'quick'
        res = (240, 180) if q else (360, 270)
        side = lambda f, r, d=1.1: ((r.x, r.y + 4, r.z + 0.15), (r.x, r.y, r.z + 0.15), d)
        fixed = lambda cx, cz, d: (lambda f, r: ((cx, 4, cz), (cx, 0, cz), d))
        follow = lambda d, dz=0.2: (lambda f, r: ((r.x + 0.15, r.y + 4, r.z + dz), (r.x + 0.15, r.y, r.z + dz), d))
        which = os.environ.get('SHEETS', 'cast_off,flight,land_cuff,feet').split(',')
        if 'cast_off' in which:
            contact_sheet(arm, meshes, frames_mesh, 'cast_off', [0, 6, 10, 12, 14, 16, 18, 21, 24, 28, 34, 40], OUT,
                          res=res, samples=6 if q else 16, cam=follow(1.0))
        if 'feet' in which:
            contact_sheet(arm, meshes, frames_mesh, 'cast_off', [0, 12], OUT, res=(480, 360), samples=6 if q else 16,
                          cam=lambda f, r: ((0.35, 0.3, 0.08), (0.0, 0.0, 0.0), None), label='the feet on the cuff')
        if 'flight' in which:
            bpy.data.objects['dass'].hide_render = True
            contact_sheet(arm, meshes, frames_mesh, 'flight', list(range(0, 14, 1)), OUT, res=res, samples=6 if q else 16,
                          cam=lambda f, r: ((r.x + 1.6, r.y - 1.3, r.z + 0.8), (r.x + 0.15, r.y, r.z + 0.05), None))
            bpy.data.objects['dass'].hide_render = False
        if 'land_cuff' in which:
            contact_sheet(arm, meshes, frames_mesh, 'land_cuff', [0, 8, 14, 18, 22, 26, 28, 30, 33, 36, 39, 45], OUT,
                          res=res, samples=6 if q else 16, cam=follow(1.0))
    if len(sys.argv) > 3 and sys.argv[3] == 'measure':
        for name, (n, fn, loop) in CLIPS.items():
            if name in ('cast_off', 'land_cuff'):
                d = talon_depths(arm, meshes, frames_mesh, name, n)
                on = [x for f, x in enumerate(d) if (name == 'cast_off' and f < 16) or (name == 'land_cuff' and f >= 28)]
                print(f'{name}: deepest toe/talon vertex under the cuff surface while on it: {max(on):.1f} mm')

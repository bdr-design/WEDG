"""The houbara's and the stone-curlew's skeletons and clips (task T17), on the saker's machinery (rig.py).

    python rig_quarry.py OUT houbara            # OUT/houbara_rig.glb
    python rig_quarry.py OUT curlew sheets      # and its contact sheets (side and three-quarter)
    python rig_quarry.py OUT houbara measure    # the checks: feet planted, the swap's overlap, the feet in flight

The rest pose is each bird's approved alert stance (the body as approved, the neck up), built with the wings
folded and spread; both meshes on one skeleton, swapped by their morph 'hidden' as the saker's are. On the ground
the feet are planted by a gait: each foot fixed in the world through its stance, lifted and carried forward in
its swing, the toes laid flat on the ground and curled in the swing.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bird  # noqa: E402
import common  # noqa: E402
import rig  # noqa: E402
from common import V3  # noqa: E402
from rig import FPS, MM, blend, keys, lerp, ramp, smooth01  # noqa: E402

TOES = ('toeM', 'toeI', 'toeO')


def species(name):
    import quarry
    return quarry.HOUBARA if name == 'houbara' else quarry.CURLEW


# ------------------------------------------------------------------ rest meshes and bones
def rest(name, wings, level=0):
    sp = species(name)
    pose = dict(sp.POSES['alert'])
    pose.pop('foot_r_shift', None)
    pose.update({'wings': wings, 'tucked': False, 'tail_droop': 0, 'wing_dihedral': 0.0, 'tail_spread': 1.0})
    det = bird.Detail(level)
    st = [(d * sp.SPEC.get('scale', 1.0), au, ad, b) for (d, au, ad, b) in sp.STATIONS]
    body = bird.Body(st, pose, det, head_weight=sp.head_weight)
    S = sp.SPEC
    out = [(body.piece(det), ('body',))]
    out += [(p, ('head',)) for p in bird.beak(body, S, det) + bird.eyes(body, S, det)]
    if wings == 'fold':
        fw = bird.folded_wing(body, S, det)
        out += [(fw[0], ('fold', 1)), (fw[1], ('fold', -1))]
    else:
        ow = bird.open_wing(body, S, det, pose)
        out += [(ow[0], ('wing', 1)), (ow[1], ('wing', -1))]
        fg = bird.fingers(body, S, det, pose)
        out += [(p, ('wing', 1 if i % 2 == 0 else -1)) for i, p in enumerate(fg)]
    out += [(p, ('tail',)) for p in bird.tail(body, S, pose, det)]
    leg, pts = bird.legs(body, S, pose, det)
    per = len(leg['tarsus']) // 2
    nt = len(S['toes'])
    for i, side in enumerate((1, -1)):
        out.append((leg['shank'][i], ('shank', side)))
        for k in range(per):
            out.append((leg['tarsus'][i * per + k], ('tarsus', side)))
        for k in range(nt):
            out.append((leg['toes'][i * nt + k], ('toe', side, k)))
            out.append((leg['claws'][i * nt + k], ('claw', side, k)))
    if sp.extras:
        out += [(p, ('crest',)) for p in sp.extras(body, det, pose)]
    return out, pts, body, pose


NECK = {'houbara': ((262, 312), (312, 362), (362, 408)), 'curlew': ((174, 205), (205, 236))}
HEAD_FROM = {'houbara': 408, 'curlew': 236}


def bones(name, pts, body, pose):
    sp = species(name)
    S = sp.SPEC
    tp = lambda x, z, y=0.0: bird.torso_point(body, x, z, y)
    B = {}

    def add(n, h, t, parent, why):
        B[n] = (V3(h), V3(t), parent, why)
    feet = (pts['foot_l'] + pts['foot_r']) / 2
    nb = NECK[name][0][0]
    add('root', feet, feet + V3((0, 0, 40)), None, 'where it stands: moves it through the world')
    add('body', tp(80, -10), body.at(nb), 'root', 'the torso: pitch, roll, bob')
    parent = 'body'
    for i, (a, b) in enumerate(NECK[name]):
        add(f'neck{i + 1}', body.at(a), body.at(b), parent, 'the neck: up when alert, forward in the run and in flight')
        parent = f'neck{i + 1}'
    add('head', body.at(HEAD_FROM[name]), body.at(body.d_end) + (body.at(body.d_end) - body.at(body.d_end - 10)).normalized() * 30,
        parent, 'the head: looks around')
    if name == 'houbara':
        c, t, u, v = body.frame_at(447)
        au = body.size_at(447)[0]
        base = c + u * au
        add('crest', base, base - t * 40 + u * 6, 'head', 'the crest: raised and lowered')
    tr = S.get('tail_root', 20)
    L = S['tail'][-1][0]
    o, t, up = bird.torso(body)
    tb = o + t * tr + up * S.get('tail_up', 0)
    tdir = -t
    add('tail', tb, tb + tdir * L, 'body', 'the tail: lifts and drops')
    add('tail.L', tb + V3((0, 6, 0)), tb + tdir * L + V3((0, 18, 0)), 'tail', 'the tail\'s left feathers: fan out')
    add('tail.R', tb + V3((0, -6, 0)), tb + tdir * L + V3((0, -18, 0)), 'tail', 'the tail\'s right feathers: fan out')
    fold = S['fold']
    wrist_x = fold[-1][0]
    mid = fold[len(fold) // 2]
    open_ = S['open']
    wy = S['wrist_y']
    ey = wy * 0.5
    tipy = open_[-1][0] if not S.get('fingers') else max(f[2] for f in S['fingers'])
    for side, s in ((1, 'L'), (-1, 'R')):
        add(f'fold.{s}', tp(wrist_x - 10, fold[-2][1], fold[-2][3] * side), tp(mid[0], mid[1], mid[3] * side), 'body',
            'the folded wing (folded mesh): opens before the swap')
        add(f'fold_tip.{s}', tp(mid[0], mid[1], mid[3] * side), tp(fold[0][0], fold[0][1], fold[0][3] * side), f'fold.{s}',
            'the folded wing\'s primaries (folded mesh): swing out as it opens')
        xl = lambda y: float(np.interp(y, [r[0] for r in open_], [r[1] - 0.3 * (r[1] - r[2]) for r in open_]))
        add(f'wing_up.{s}', tp(xl(open_[0][0]), 8, open_[0][0] * side), tp(xl(ey), 8, ey * side), 'body', 'the arm: the wingbeat')
        add(f'wing_fore.{s}', tp(xl(ey), 8, ey * side), tp(xl(wy), 8, wy * side), f'wing_up.{s}', 'the forearm: the fold at the elbow')
        add(f'wing_hand.{s}', tp(xl(wy), 8, wy * side), tp(xl(tipy) - 20, 0, tipy * side), f'wing_fore.{s}', 'the hand: the fold at the wrist')
        k = 'l' if side > 0 else 'r'
        Lg = S['leg']
        knee = tp(Lg['knee'][0], Lg['knee'][1], Lg['knee'][2] * side)
        add(f'shank.{s}', knee, pts['ankle_' + k], 'body', 'the shank: with the tarsus, the stride')
        add(f'tarsus.{s}', pts['ankle_' + k], pts['foot_' + k], f'shank.{s}', 'the tarsus: the foot planted and swung')
        f = pts['foot_' + k]
        for ti, (hd, length, r, claw, curl) in enumerate(S['toes']):
            a = math.radians(hd * side + pose.get('foot_turn', 0.0) * side)
            dv = V3((math.cos(a), math.sin(a), 0))
            add(f'{TOES[ti]}1.{s}', f + dv * -2, f + dv * length * 0.5, f'tarsus.{s}', 'a toe: lies on the ground')
            add(f'{TOES[ti]}2.{s}', f + dv * length * 0.5, f + dv * (length - 2), f'{TOES[ti]}1.{s}', 'a toe\'s end: curls in the swing')
    return B


def weights_for(name, pc, tag, body, B):
    kind = tag[0]
    side = tag[1] if len(tag) > 1 and isinstance(tag[1], int) else 1
    s = 'L' if side > 0 else 'R'
    if kind == 'body':
        d_st = np.array(body.d)
        cs = np.array([tuple(sec.c) for sec in body.secs])
        necks = NECK[name]
        bands = [('body', necks[0][0])] + [(f'neck{i + 1}', b) for i, (a, b) in enumerate(necks)]
        W = []
        for q in pc.V:
            d = d_st[int(np.argmin(((cs - np.array(tuple(q))) ** 2).sum(1)))]
            w = {'head': 1.0}
            for i, (bn, end) in enumerate(bands):
                if d < end - 12:
                    w = {bn: 1.0}
                    break
                if d < end + 12:
                    nxt = bands[i + 1][0] if i + 1 < len(bands) else 'head'
                    w = blend(bn, nxt, (d - end + 12) / 24)
                    break
            W.append(w)
        return W
    if kind == 'head':
        return [{'head': 1.0} for _ in pc.V]
    if kind == 'crest':
        return [{'crest': 1.0} for _ in pc.V]
    if kind == 'tail':
        root = B['tail'][0]
        tdir = (B['tail'][1] - root).normalized()
        out = []
        for q in pc.V:
            along = (q - root).dot(tdir) / 40.0
            out.append(blend('body', 'tail', along) if along < 1 else blend('tail', 'tail.L' if q.y > 0 else 'tail.R', (abs(q.y) - 5) / 25.0))
        return out
    if kind == 'fold':
        h0 = B[f'fold.{s}'][0]
        hm = B[f'fold_tip.{s}'][0]
        span = (h0.x - hm.x) or 1.0
        out = []
        for q in pc.V:
            if q.x > h0.x - 20:
                out.append(blend('body', f'fold.{s}', (h0.x + 20 - q.x) / 40.0))
            else:
                out.append(blend(f'fold.{s}', f'fold_tip.{s}', (hm.x + 0.3 * span - q.x) / (0.6 * span)))
        return out
    if kind == 'wing':
        e = abs(B[f'wing_fore.{s}'][0].y)
        w = abs(B[f'wing_hand.{s}'][0].y)
        r = abs(B[f'wing_up.{s}'][0].y)
        out = []
        for q in pc.V:
            y = abs(q.y)
            if y < r + 30:
                out.append(blend('body', f'wing_up.{s}', (y - r) / 30))
            elif y < e + 35:
                out.append(blend(f'wing_up.{s}', f'wing_fore.{s}', (y - (e - 35)) / 70))
            else:
                out.append(blend(f'wing_fore.{s}', f'wing_hand.{s}', (y - (w - 40)) / 80))
        return out
    if kind == 'shank':
        knee, ankle = B[f'shank.{s}'][0], B[f'shank.{s}'][1]
        L = (ankle - knee).length
        return [blend('body', f'shank.{s}', (q - knee).dot((ankle - knee).normalized()) / (0.35 * L)) for q in pc.V]
    if kind == 'tarsus':
        return [{f'tarsus.{s}': 1.0} for _ in pc.V]
    if kind in ('toe', 'claw'):
        b1, b2 = f'{TOES[tag[2]]}1.{s}', f'{TOES[tag[2]]}2.{s}'
        if kind == 'claw':
            return [{b2: 1.0} for _ in pc.V]
        h = B[b1][0]
        ax = (B[b1][1] - h).normalized()
        L = (B[b1][1] - h).length
        return [blend(b1, b2, ((q - h).dot(ax) - L * 0.85) / (L * 0.3)) for q in pc.V]
    raise ValueError(kind)


def skinned(name, oname, tagged, body, B, atlas, mat, arm):
    me = common.to_mesh(oname, [p for p, t in tagged], atlas)
    o = common.obj(oname, me, mat, arm)
    groups = {}
    vi = 0
    for pc, tag in tagged:
        for w in weights_for(name, pc, tag, body, B):
            for bn, val in sorted(w.items()):
                g = groups.get(bn) or o.vertex_groups.new(name=bn)
                groups[bn] = g
                g.add([vi], val, 'REPLACE')
            vi += 1
    o.modifiers.new('arm', 'ARMATURE').object = arm
    return o


# ------------------------------------------------------------------ posing
class QApplier:
    def __init__(self, name, arm, B, body, toe_verts):
        self.name = name
        self.P = rig.Poser(arm)
        self.B = B
        self.body = body
        self.toe_verts = toe_verts
        self.rest_root = self.P.rest['root'].translation / MM
        self.log = []

    def toes_flat(self, s, foot_target):
        """Each toe laid joint by joint on the ground (z = 0), from its rest frame, as on the saker's perch."""
        P = self.P
        rest_foot = P.rest[f'tarsus.{s}'].translation / MM + P.rest[f'tarsus.{s}'].to_3x3() @ V3((0, P.pb[f'tarsus.{s}'].bone.length / MM, 0))
        for nm in TOES:
            for j in (1, 2):
                b = f'{nm}{j}.{s}'
                V = self.toe_verts.get(b)
                bpy.context.view_layer.update()
                p = P.pb[b]
                Rr = P.rest[b]
                rest_dir = (Rr.to_3x3() @ V3((0, 1, 0))).normalized()
                head = (V3(foot_target) + (Rr.translation / MM - rest_foot)) * MM if j == 1 else p.matrix.translation.copy()
                yaw = Matrix.Rotation(math.radians(self.yaw), 3, 'Z')
                flat = yaw @ V3((rest_dir.x, rest_dir.y, 0)).normalized()
                local = Rr.inverted()
                best, best_M = None, None
                for a in np.linspace(-30, 60, 91):
                    ar = math.radians(a)
                    want = flat * math.cos(ar) + V3((0, 0, -1)) * math.sin(ar)
                    r = rest_dir.rotation_difference(want).to_matrix()
                    M = Matrix.Translation(head) @ (r @ Rr.to_3x3()).to_4x4()
                    A = np.array(M @ local)
                    W = (V @ A[:3, :3].T + A[:3, 3]) / MM
                    clear = W[:, 2].min()
                    score = abs(clear - 0.6) + (1000 if clear < 0.4 else 0)
                    if best is None or score < best:
                        best, best_M = score, M
                p.matrix = best_M

    def apply(self, sp, frame, key=True):
        P = self.P
        P.reset()
        self.yaw = sp.get('yaw', 0.0)
        R = (Matrix.Rotation(math.radians(self.yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-sp.get('pitch', 0.0)), 4, 'Y')
             @ Matrix.Rotation(math.radians(sp.get('roll', 0.0)), 4, 'X'))
        root = V3(sp.get('root', (0, 0, 0)))
        lift = V3((0, 0, sp.get('bob', 0.0)))
        P.place('root', Matrix.Translation((root - self.rest_root) * MM))
        # the body turned about its own rest place, carried by the root
        piv = P.rest['body'].translation / MM
        W = Matrix.Translation((root + lift) * MM) @ Matrix.Translation(piv * MM) @ R @ Matrix.Translation(-piv * MM)
        P.place('body', W)
        for i, a in enumerate(sp.get('neck', ())):
            P.turn(f'neck{i + 1}', (0, -1, 0), a)
        P.turn('head', (0, -1, 0), sp.get('head_pitch', 0.0))
        P.turn('head', (0, 0, 1), sp.get('head_yaw', 0.0))
        if 'crest' in P.pb:
            P.turn('crest', (0, -1, 0), sp.get('crest', 0.0))
        P.turn('tail', (0, 1, 0), sp.get('tail_drop', 0.0))
        fan = (sp.get('tail_spread', 1.0) - 1.0) * 45.0
        P.turn('tail.L', (0, 0, -1), fan)
        P.turn('tail.R', (0, 0, 1), fan)
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
            fp = sp.get('fold')
            if fp:
                P.turn(f'fold.{s}', (0, 0, -side), fp.get('out', 0.0))
                P.turn(f'fold.{s}', (side, 0, 0), fp.get('up', 0.0))
                P.turn(f'fold_tip.{s}', (0, 0, -side), fp.get('tip_out', 0.0))
                P.turn(f'fold_tip.{s}', (side, 0, 0), fp.get('tip_up', 0.0))
        # the legs: each foot a world target; planted feet with their toes on the ground, swinging ones curled
        for side, s in ((1, 'L'), (-1, 'R')):
            target, planted, curl = sp['feet'][s]
            if target == 'trail':
                tb = W @ (V3(self.trail) * V3((1, side, 1)) * MM) / MM
                P.leg(s, tb, (W.to_3x3() @ V3((-1, 0, 0.6))))
                for nm in TOES:
                    ax = P.rest[f'{nm}1.{s}'].to_3x3() @ V3((1, 0, 0))
                    P.turn(f'{nm}1.{s}', ax, -60)
                    P.turn(f'{nm}2.{s}', ax, -80)
                continue
            target = V3(target) + V3((0, 0, rig.FOOT_LIFT))
            pole = Matrix.Rotation(math.radians(self.yaw), 3, 'Z') @ V3((-1, 0, -0.1))
            P.leg(s, target, pole)
            if planted:
                self.toes_flat(s, target)
                self.log.append(('slide', frame, s, (P.tail_of(f'tarsus.{s}') - target).length))
            else:
                for nm in TOES:
                    ax = P.rest[f'{nm}1.{s}'].to_3x3() @ V3((1, 0, 0))
                    P.turn(f'{nm}1.{s}', ax, -25 * curl)
                    P.turn(f'{nm}2.{s}', ax, -40 * curl)
        if key:
            P.key(frame)


# ------------------------------------------------------------------ the clips
def gait(t, v, period, duty, half_width, lift, x0=0.0, phases=(0.0, 0.5), yaw=0.0):
    """Each foot's world place at time t (s) for a body moving at v (mm/s) along +X: fixed through its stance,
    carried forward (and up by [lift]) through its swing. Returns {'L': (place, planted, curl), 'R': ...}."""
    stride = v * period
    out = {}
    for (s, side), off in zip((('L', 1), ('R', -1)), phases):
        u = t / period + off
        c = math.floor(u)
        p = u - c
        t0 = (c - off) * period
        land = x0 + v * t0 + duty * stride / 2
        if p < duty:
            x, z, planted, curl = land, 0.0, True, 0.0
        else:
            q = (p - duty) / (1 - duty)
            e = smooth01(q)
            x = land + e * stride
            z = lift * math.sin(math.pi * q)
            planted, curl = False, math.sin(math.pi * q)
        out[s] = (V3((x, half_width * side, z)), planted, curl)
    return out


class Clips:
    def __init__(self, name):
        self.name = name
        self.S = species(name).SPEC
        self.hw = 34 if name == 'houbara' else 22
        # wingbeats: 7 frames (4.3 Hz) for the houbara, inside the 4.2-4.7 Hz Pennycuick's formula gives it; 5 frames
        # (6 Hz) for the stone-curlew, inside its 5.9-7.4 Hz
        self.beat = 7 if name == 'houbara' else 5
        self.alert_neck = (0, 0, 0) if name == 'houbara' else (0, 0)
        self.run_neck = (-28, -18, 10) if name == 'houbara' else (-30, 8)
        self.fly_neck = (-62, -10, 8) if name == 'houbara' else (-60, 20)
        self.trail = (-60, 30, -60) if name == 'houbara' else (-80, 20, -40)

    def flap(self, ph, amp, mean):
        up = mean + amp * math.cos(2 * math.pi * ph)
        down = math.sin(2 * math.pi * ph)
        flex = max(0.0, -down) ** 0.8
        return {'up': up, 'sweep': 14 * flex, 'fore': -60 * flex, 'hand': 95 * flex, 'twist': 5 * down,
                'hand_up': 18 * flex, 'hand_twist': 12 * down - 8 * flex}

    def stand(self, f):
        """Alert on the ground: the weight on one foot (the other a little back), the head turning, a slow sway; it
        loops."""
        c = 2 * math.pi * f / 120.0
        yaw = keys(f, [(0, 0), (20, 0), (30, 35), (50, 35), (60, 0), (75, 0), (85, -30), (100, -30), (110, 0), (120, 0)])
        back = -34 if self.name == 'houbara' else -28
        feet = {'L': (V3((0, self.hw, 0)), True, 0), 'R': (V3((back, -self.hw, 0)), True, 0)}
        crest = 6 * max(0.0, math.sin(c * 2)) if self.name == 'houbara' else 0
        return {'feet': feet, 'mesh': 'fold', 'bob': 2 * math.sin(c), 'roll': 1.5 * math.sin(c), 'head_yaw': yaw,
                'neck': self.alert_neck, 'crest': crest}

    def run(self, f, n=None):
        """The run: low and level, the neck forward, the wings shut; a stride cycle of 8 frames (0.27 s) at 3 m/s for
        the houbara, 6 frames (0.2 s) at 2 m/s for the stone-curlew, each foot down a third of the cycle (game
        choices: no measured speed or stride was found); it loops in place."""
        period = 8 if self.name == 'houbara' else 6
        v = 3000.0 if self.name == 'houbara' else 2000.0
        t = f / FPS
        feet = gait(t, v, period / FPS, 0.30, self.hw * 0.8, 45 if self.name == 'houbara' else 30)
        x = v * t
        feet = {s: (V3((p.x - x + 10, p.y, p.z)), pl, c) for s, (p, pl, c) in feet.items()}      # in place
        ph = (f / period) % 1.0
        return {'feet': feet, 'mesh': 'fold', 'pitch': -6, 'bob': 8 * abs(math.cos(2 * math.pi * ph)) - (46 if self.name == 'houbara' else 26),
                'neck': self.run_neck, 'head_pitch': 6, 'tail_drop': -4}

    def take_off(self, f):
        """Two strides of run, a crouch, the spring with the wings opening (the folded mesh to 13, the spread mesh
        matched from 14), the first heavy beats low over the ground, the legs trailing back."""
        swap = 14
        if f < swap:
            r = self.run(f)
            r['pitch'] = lerp(-6, -14, ramp(f, 8, 13))
            r['bob'] += -18 * ramp(f, 8, 13)
            if f >= 9:
                r['fold'] = {k: v * ramp(f, 9, 13) for k, v in self.swap_fold.items()}
            if f == 13:
                r['wing'] = dict(self.swap_open)
            # the feet in place under the body from the crouch on
            if f >= 10:
                r['feet'] = {'L': (V3((0, self.hw, 0)), True, 0), 'R': (V3((-10, -self.hw, 0)), True, 0)}
            return r
        k = ramp(f, swap, swap + 4)
        raised = {'up': 60, 'sweep': 18, 'fore': -12, 'hand': 14, 'twist': 0}
        if f < swap + 4:
            w = {kk: lerp(self.swap_open.get(kk, 0.0), raised.get(kk, 0.0), k) for kk in raised}
        else:
            w = self.flap(((f - swap - 4) / self.beat) % 1.0, 48, 4)
        t = max(0.0, (f - swap - 2) / FPS)
        root = V3((1800 * t + 0.5 * 3000 * t * t, 0, 0.5 * 2500 * t * t))
        sp = {'mesh': 'open', 'wing': w, 'pitch': keys(f, [(swap, -10), (swap + 4, 18), (swap + 12, 8), (40, 4)]),
              'root': root, 'neck': tuple(lerp(a, b, ramp(f, swap, swap + 10)) for a, b in zip(self.run_neck, self.fly_neck)),
              'tail_spread': 1.25}
        if f < swap + 3:
            sp['feet'] = {'L': (V3((0, self.hw, 0)), True, 0), 'R': (V3((-10, -self.hw, 0)), True, 0)}
        else:
            sp['feet'] = {'L': ('trail', False, 1), 'R': ('trail', False, 1)}
        if f == swap:
            sp['fold'] = dict(self.swap_fold)
        return sp

    def flight(self, f):
        ph = (f / self.beat) % 1.0
        amp = 52 if self.name == 'houbara' else 44
        return {'mesh': 'open', 'wing': self.flap(ph, amp, 6), 'pitch': 3, 'bob': -10 * math.cos(2 * math.pi * ph),
                'neck': self.fly_neck, 'feet': {'L': ('trail', False, 1), 'R': ('trail', False, 1)}, 'tail_spread': 1.05}

    def escape(self, f):
        """The houbara's escape: it runs first, jinking from side to side, and flies only when pressed (Encyclopaedia
        Iranica, from a search summary; the jinks and their timing are game choices): a jinking run, then the
        take-off."""
        if f < 24:
            r = self.run(f)
            yaw = 18 * math.sin(2 * math.pi * f / 16.0)
            r['yaw'] = yaw
            Rz = Matrix.Rotation(math.radians(yaw), 3, 'Z')
            r['feet'] = {s_: (Rz @ p, pl, c) for s_, (p, pl, c) in r['feet'].items()}      # the stride turns with the body
            return r
        return self.take_off(f - 24 + 2)

    def crouch(self, f):
        """The stone-curlew's crouch: it lies flat with the neck stretched along the ground and stays still, trusting
        its plumage (from search summaries: crouch, freeze, then run; the timing is a game choice); down by 12,
        held, up again from 48."""
        k = ramp(f, 0, 12) * (1 - ramp(f, 48, 60))
        feet = {'L': (V3((0, self.hw, 0)), True, 0), 'R': (V3((-6, -self.hw, 0)), True, 0)}
        return {'feet': feet, 'mesh': 'fold', 'pitch': -4 * k, 'bob': -60 * k, 'neck': (-55 * k, -25 * k), 'head_pitch': 10 * k,
                'tail_drop': -6 * k}


CLIPS = {
    'houbara': {'stand': (120, 'stand', True), 'run': (16, 'run', True), 'take_off': (40, 'take_off', False),
                'flight': (14, 'flight', True), 'escape': (62, 'escape', False)},
    'curlew': {'stand': (120, 'stand', True), 'run': (12, 'run', True), 'crouch': (60, 'crouch', False),
               'take_off': (40, 'take_off', False), 'flight': (10, 'flight', True)},
}
SWAP = {      # tuned by `tune` (the folded wing's opening and the spread wing's fold that match at the swap)
    'houbara': ({'out': 36, 'up': 56, 'twist': 0, 'tip_out': 1, 'tip_up': -36}, {'up': 0, 'sweep': 70, 'fore': -109, 'hand': 194, 'twist': 0}),
    'curlew': ({'out': 10, 'up': 39, 'twist': 0, 'tip_out': -5, 'tip_up': -31}, {'up': 15, 'sweep': 95, 'fore': -11, 'hand': 195, 'twist': 0}),
}


def build(name, out, clips_wanted=None):
    import paint
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS
    tf, pts, body, pose = rest(name, 'fold')
    to, _, _, _ = rest(name, 'open')
    B = bones(name, pts, body, pose)
    atlas = paint.atlas(name)
    col, orm = paint.paint(name, atlas, 512, body)
    mat = common.material(name, col, orm)
    arm = rig.make_armature(f'{name}_rig', B)
    meshes = {'fold': skinned(name, f'{name}_fold', tf, body, B, atlas, mat, arm),
              'open': skinned(name, f'{name}_open', to, body, B, atlas, mat, arm)}
    for k in meshes:
        rig.add_hidden_morph(meshes[k], body)
    # the far level on the same skeleton (the T11 far meshes, 256 px)
    tf1, _, body1, _ = rest(name, 'fold', level=1)
    to1, _, _, _ = rest(name, 'open', level=1)
    c1, o1 = paint.paint(name, atlas, 256, body1)
    mat1 = common.material(name + '_far', c1, o1)
    far = {'fold': skinned(name, f'{name}_fold_far', tf1, body1, B, atlas, mat1, arm),
           'open': skinned(name, f'{name}_open_far', to1, body1, B, atlas, mat1, arm)}
    for k in far:
        rig.add_hidden_morph(far[k], body1)
        far[k].hide_render = True
    C = Clips(name)
    C.swap_fold, C.swap_open = SWAP[name]
    toe_verts = rig.toe_vertex_sets(meshes['fold'])
    arm.animation_data_create()
    frames_mesh, feet_planted, logs = {}, {}, []
    clips = CLIPS[name] if clips_wanted is None else {k: v for k, v in CLIPS[name].items() if k in clips_wanted}
    shape_actions = {}
    for cname, (n, fn, loop) in clips.items():
        act = bpy.data.actions.new(cname)
        arm.animation_data.action = act
        A = QApplier(name, arm, B, body, toe_verts)
        A.trail = C.trail
        sk_acts = {}
        for k, o in list(meshes.items()) + [(k + '_far', o) for k, o in far.items()]:
            sk = o.data.shape_keys
            sk.animation_data_create()
            sk.animation_data.action = bpy.data.actions.new(cname)
            sk_acts[k] = sk
        frames_mesh[cname] = []
        feet_planted[cname] = []
        spec = getattr(C, fn)
        for f in range(n + (1 if loop else 0)):
            sp = spec(f % n)
            A.apply(sp, f)
            frames_mesh[cname].append(sp['mesh'])
            for k, sk in sk_acts.items():
                sk.key_blocks['hidden'].value = 0.0 if sp['mesh'] == k.split('_')[0] else 1.0
                sk.key_blocks['hidden'].keyframe_insert('value', frame=f)
        logs += [(cname,) + e for e in A.log]
        act.use_fake_user = True
        arm.animation_data.action = None
        for k, sk in sk_acts.items():
            sk.animation_data.action.use_fake_user = True
            shape_actions.setdefault(k, {})[cname] = sk.animation_data.action
            sk.animation_data.action = None
    rig.thin_keys([bpy.data.actions[c] for c in clips] + [a for d in shape_actions.values() for a in d.values()])
    for cname in clips:
        tr = arm.animation_data.nla_tracks.new()
        tr.name = cname
        tr.strips.new(cname, 0, bpy.data.actions[cname])
        for k, o in list(meshes.items()) + [(k + '_far', o) for k, o in far.items()]:
            sk = o.data.shape_keys
            t2 = sk.animation_data.nla_tracks.new()
            t2.name = cname
            t2.strips.new(cname, 0, shape_actions[k][cname])
    for cname in clips:
        sl = [e[4] for e in logs if e[0] == cname and e[1] == 'slide']
        if sl:
            print(f'{cname}: a planted foot\'s distance from its place, max {max(sl):.2f} mm over {len(sl)} foot-frames')
    path = os.path.join(out, f'{name}_rig.glb')
    bpy.ops.object.select_all(action='DESELECT')
    for o in [arm, *meshes.values()]:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=False,
                              export_animations=True, export_animation_mode='NLA_TRACKS', export_skins=True,
                              export_all_influences=False, export_force_sampling=False, export_optimize_animation_size=True,
                              export_morph=True, export_morph_animation=True, export_morph_normal=False,
                              export_materials='EXPORT', export_extras=False, export_image_format='AUTO')
    common.settle(path)
    t, imgs, nbytes = common.glb_report(path)
    print(f'{name}_rig.glb: {", ".join(f"{k} {v}" for k, v in sorted(t.items()))}; {len(B)} bones; {nbytes / 1024:.0f} KB')
    rig.export_far(arm, far, os.path.join(out, f'{name}_rig_far.glb'))
    rig.CLIPS.clear()
    rig.CLIPS.update(clips)
    return arm, meshes, frames_mesh, B, C, body


if __name__ == '__main__':
    OUT = os.path.abspath(sys.argv[1])
    NAME = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else ''
    os.makedirs(OUT, exist_ok=True)
    arm, meshes, frames_mesh, B, C, body = build(NAME, OUT)
    if mode == 'tune':
        import itertools
        A = QApplier(NAME, arm, B, body, rig.toe_vertex_sets(meshes['fold']))
        A.trail = C.trail
        base = C.take_off(13)
        for o in meshes.values():
            o.data.shape_keys.key_blocks['hidden'].value = 0.0
        best = None
        sf, so = dict(SWAP[NAME][0]), dict(SWAP[NAME][1])
        if NAME == 'houbara':
            sf, so = {'out': 31, 'up': 55, 'twist': 0, 'tip_out': 5, 'tip_up': -50}, {'up': 5, 'sweep': 80, 'fore': -60, 'hand': 170, 'twist': 0}
        else:
            sf, so = {'out': 5, 'up': 40, 'twist': 0, 'tip_out': 5, 'tip_up': -20}, {'up': 5, 'sweep': 80, 'fore': -60, 'hand': 170, 'twist': 0}
        step = {'up': 15, 'sweep': 15, 'fore': 25, 'hand': 25, 'out': 13, 'fup': 15, 'tip_out': 15, 'tip_up': 15}
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
                a, ta = rig.evaluated_co(meshes['fold'])
                b, tb = rig.evaluated_co(meshes['open'])
                sc = min(rig.pair_iou(a, ta, b, tb, rig.VIEWS['side']), rig.pair_iou(a, ta, b, tb, rig.VIEWS['three_quarter']))
                if best is None or sc > best[0]:
                    best = (sc, dict(fp), dict(w))
            sf, so = best[1], best[2]
            if rnd % 2 == 1:
                step = {k: max(4, v * 0.6) for k, v in step.items()}
            print(NAME, 'round', rnd, 'overlap %.3f' % best[0], best[1], best[2])
    if mode in ('sheets', 'quick'):
        rig.SHEET_PREFIX[0] = NAME
        me = bpy.data.meshes.new('sand')
        r = 4.0
        me.from_pydata([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)], [], [(0, 1, 2, 3)])
        sand = common.obj('sand', me, None)
        sm = bpy.data.materials.new('sandm')
        sm.use_nodes = True
        sm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.62, 0.52, 0.38, 1)
        me.materials.append(sm)
        q = mode == 'quick'
        res = (240, 180) if q else (360, 270)
        d = 1.1 if NAME == 'houbara' else 0.8
        for cname, (n, fn, loop) in CLIPS[NAME].items():
            flying = cname in ('flight',)
            sand.hide_render = flying
            k = 12
            frames = sorted(set(int(round(i * (n - 1) / (k - 1))) for i in range(k)))
            dd = d * (1.5 if flying else 1.0)
            side = lambda f, r, dd=dd: ((r.x + 0.1, r.y + 4, r.z + 0.25), (r.x + 0.1, r.y, r.z + 0.25), dd)
            tq = lambda f, r, dd=dd: ((r.x + 1.2 * dd, r.y + 1.0 * dd, r.z + 0.3 + 0.5 * dd), (r.x + 0.1, r.y, r.z + 0.22), None)
            if flying:
                side = lambda f, r, dd=dd: ((r.x + 0.1, r.y + 4, r.z + 0.2), (r.x + 0.1, r.y, r.z + 0.2), dd)
                tq = lambda f, r, dd=dd: ((r.x + 1.3 * dd, r.y - 1.1 * dd, r.z + 0.8 * dd), (r.x + 0.1, r.y, r.z + 0.2), None)
            lab = 'awaiting the owner\'s approval of the motion'
            rig.contact_sheet(arm, meshes, frames_mesh, cname, frames, OUT, res=res, samples=6 if q else 12, cam=side,
                              label=f'{NAME} {cname}, from the side (30 frames a second): {lab}', tag='side')
            rig.contact_sheet(arm, meshes, frames_mesh, cname, frames, OUT, res=res, samples=6 if q else 12, cam=tq,
                              label=f'{NAME} {cname}, three-quarter (30 frames a second): {lab}', tag='tq')
    if mode == 'measure':
        sc = bpy.context.scene
        for cname, (n, fn, loop) in CLIPS[NAME].items():
            rig.use_clip(arm, cname)
            fm = frames_mesh[cname]
            for f in range(1, n):
                if fm[f] != fm[f - 1]:
                    worst = 1.0
                    rig.show_both(arm)
                    for g in (f - 1, f):
                        sc.frame_set(g)
                        a, ta = rig.evaluated_co(meshes['fold'])
                        b, tb = rig.evaluated_co(meshes['open'])
                        worst = min(worst, rig.pair_iou(a, ta, b, tb, rig.VIEWS['side']), rig.pair_iou(a, ta, b, tb, rig.VIEWS['three_quarter']))
                    print(f'{cname}: swap {fm[f - 1]} -> {fm[f]} at frame {f}: silhouette overlap {worst:.3f}')

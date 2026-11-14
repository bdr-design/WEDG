"""A canid (the wolf or a dog) from its numbers: a torso lofted along the body, a neck and head (with a lower jaw that
opens), ears, eyes, a nose, four legs solved from the shoulder and hip joints to the paws' places, and a tail. The
species' numbers are in species.py.

All sizes are given in units of the withers height H (the shoulder height a standing animal is measured at) and
turned into millimetres here. The rest frame: X forward, Z up from the ground, Y to the animal's left; the origin on
the ground at the middle of the body. A pose moves the body (lowers and pitches it), bends the neck and head, places
each paw on its spot and bends the tail; the legs are solved from their joints to the paws, the elbow always bending
back and the stifle (knee) forward, as in every quadruped.

Every piece keeps the sections it was lofted from (Shape), so the painter can find, for each texel of the atlas, the
place on the standing animal it lands on: markings are painted where they are on the body, not by guesswork in the
texture.
"""
import math

import numpy as np
from mathutils import Matrix, Vector

from common import V3, Piece, Sec, frame, loft, resample, smooth_path

UP = V3((0, 0, 1))


class Detail:
    def __init__(self, level):
        hi = level == 0
        self.level = level
        self.body_ring, self.body_st = (32, 26) if hi else (12, 9)
        self.neck_ring, self.neck_st = (24, 8) if hi else (8, 4)
        self.head_ring, self.head_st = (28, 14) if hi else (10, 6)
        self.jaw_ring, self.jaw_st = (16, 9) if hi else (6, 4)
        self.ear_ring, self.ear_st = (12, 6) if hi else (5, 3)
        self.eye_ring, self.eye_st = (12, 5) if hi else (0, 0)
        self.leg_ring = 14 if hi else 6
        self.thigh_ring = 16 if hi else 7
        self.paw_ring, self.paw_st = (14, 8) if hi else (6, 4)
        self.tail_ring, self.tail_st = (16, 14) if hi else (7, 6)
        self.collar_ring, self.collar_st = (8, 28) if hi else (5, 12)
        self.teeth = hi


class Shape:
    """A lofted piece's sections, kept for the painter: ring points at fine angles per section, and each section's
    place along the piece (0..1)."""

    def __init__(self, secs, s, t0=0.0, length=1.0, girth=1.0):
        self.secs, self.s, self.t0 = secs, list(s), t0
        self.length, self.girth = length, girth

    def grid(self, nt=96):
        th = [2 * math.pi * (k / nt + self.t0) for k in range(nt + 1)]
        return np.array([[tuple(sec.point(a)) for a in th] for sec in self.secs], np.float64)


def s_by_length(pts):
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (V3(b) - V3(a)).length)
    tot = L[-1] or 1.0
    return [x / tot for x in L], tot


def piece(block, secs, n, s=None, caps=(True, True), shapes=None, t0=0.0):
    if s is None:
        s, length = s_by_length([sec.c for sec in secs])
    else:
        length = sum((b.c - a.c).length for a, b in zip(secs, secs[1:]))
    girth = max(2 * math.pi * math.sqrt(((sec.au + sec.ad) / 2) * ((sec.bl + sec.br) / 2)) for sec in secs)
    pc = loft(block, secs, n, s=s, caps=caps, t0=t0)
    if shapes is not None and block not in shapes:
        shapes[block] = Shape(secs, s, t0, length, girth)
    return pc


def ik2(root, target, a, b, pole):
    """The middle joint of a two-bone limb from [root] toward [target], bending toward [pole]. Returns (mid, low, reach):
    [low] is the target, or as near as the bones reach; reach = distance / (a + b)."""
    d = target - root
    L = d.length
    reach = L / (a + b)
    L = min(max(L, abs(a - b) + 1e-3), (a + b) * 0.9995)
    dn = d.normalized()
    cosA = (a * a + L * L - b * b) / (2 * a * L)
    A = math.acos(max(-1.0, min(1.0, cosA)))
    p = pole - dn * pole.dot(dn)
    p.normalize()
    mid = root + dn * (a * math.cos(A)) + p * (a * math.sin(A))
    return mid, root + dn * L, reach


def rot_y(deg):
    """A turn about the animal's left-right axis: positive lifts the front (nose up)."""
    return Matrix.Rotation(math.radians(-deg), 3, 'Y')


def dir_xz(deg_above_forward):
    a = math.radians(deg_above_forward)
    return V3((math.cos(a), 0, math.sin(a)))


class Canid:
    """One animal in one pose. [spec]: the species' numbers (species.py); [pose]: the pose's numbers; [det]: Detail."""

    def __init__(self, spec, pose, det):
        self.S, self.P, self.d = spec, pose, det
        self.H = spec['H']
        self.parts = {}
        self.points = {}
        self.shapes = {}
        self.reach = {}
        self.bodyM = None

    # ---------------------------------------------------------------- frames
    def h(self, v):
        return v * self.H

    def body_pt(self, x, z, y=0.0):
        """A point given in the standing body's frame (units of H) to the posed world (mm)."""
        S, P, H = self.S, self.P, self.H
        piv = V3((0, 0, S['pivot_z'] * H))
        q = V3((x * H, y * H, z * H)) - piv
        q = rot_y(P.get('pitch', 0.0)) @ q
        return q + piv + V3((P.get('shift_x', 0.0) * H, 0, -P.get('drop', 0.0) * H))

    def body_dir(self, v):
        return rot_y(self.P.get('pitch', 0.0)) @ V3(v)

    # ---------------------------------------------------------------- build
    def build(self):
        self.torso()
        self.neck_head()
        for side in ('l', 'r'):
            self.foreleg(side)
            self.hindleg(side)
        self.tail()
        if self.S.get('collar') and self.P.get('collar', True):
            self.collar()
        return self.parts, self.points

    def add(self, part, pc):
        self.parts.setdefault(part, []).append(pc)

    # ---------------------------------------------------------------- torso
    def torso(self):
        S, d, H = self.S, self.d, self.H
        rows = resample(S['torso'], d.body_st)
        secs = []
        for x, top, bot, w, wl in rows:
            c = self.body_pt(x, (top + bot) / 2)
            hh = (top - bot) / 2 * H
            u = self.body_dir((0, 0, 1))
            v = self.body_dir((1, 0, 0)).cross(u)      # -Y: the animal's right
            # the lower half a little narrower than the upper (the keel of the chest, the belly's tuck)
            # the lower half narrows to [wl] at the bottom: the chest's keel, the belly's tuck
            secs.append(KeelSec(Sec(c, u, v, hh, hh, w * H, w * H, p=2.15), wl * H))
        out = secs
        self.add('body', piece('body', out, d.body_ring, shapes=self.shapes))
        self.points['withers'] = self.body_pt(S['withers'][0], S['withers'][1])
        self.points['hips'] = self.body_pt(S['hip'][0], S['hip'][1])

    # ---------------------------------------------------------------- neck, head, jaw, ears, eyes, nose
    def neck_head(self):
        S, P, d, H = self.S, self.P, self.d, self.H
        nb = self.body_pt(*S['neck_base'])
        ang = P.get('neck', S['neck_angle'])            # the neck's direction, degrees above forward
        L = S['neck_len'] * H
        occ = nb + dir_xz(ang) * L
        mid = nb + dir_xz(ang) * (L * 0.5) + dir_xz(ang + 90) * (S['neck_arch'] * H)
        # the neck runs on into the back of the head, so its end is hidden inside the skull
        hp = P.get('head', S['head_pitch'])
        inside = occ + dir_xz(-hp) * (0.16 * S['head_len'] * H) + dir_xz(-hp + 90) * (S['occ_up'] * H)
        path = smooth_path([nb, mid, occ, inside], d.neck_st)
        sizes = resample(S['neck'] + [(1.15, S['neck'][-1][1] * 0.8, S['neck'][-1][2] * 0.7, S['neck'][-1][3] * 0.7)], d.neck_st)
        secs = []
        for i, q in enumerate(path):
            a = path[max(i - 1, 0)]
            b = path[min(i + 1, len(path) - 1)]
            t = (b - a).normalized()
            u, v = frame(t, (0, 1, 0))                   # u: the animal's left; v: the crest (up and back)
            _, wid, crest, throat = sizes[i]
            k = self.P.get('ruff', 1.0) if i < len(path) - 1 else 1.0
            secs.append(Sec(q, u, v, wid * H * k, wid * H * k, crest * H * k, throat * H * k, p=2.1))
        self.add('body', piece('neck', secs, d.neck_ring, shapes=self.shapes))
        self.points['neck_base'] = (nb, (occ - nb).normalized(), UP)
        self.neck_secs = secs

        # the head: its axis from the occiput to the nose, pitched [head] degrees below forward
        hd = dir_xz(-hp)
        hn = dir_xz(-hp + 90)                            # the head's up
        hv = hd.cross(hn)                                # its right (-Y)
        Lh = S['head_len'] * H
        o = occ + hn * (S['occ_up'] * H)
        self.head_frame = (o, hd, hn, hv, Lh)
        rows = resample(S['head'], d.head_st)
        secs = [Sec(o + hd * (t * Lh) + hn * (cz * H), hn, hv, up * H, dn * H, w * H, w * H, p=2.2) for t, cz, up, dn, w in rows]
        self.add('head', piece('head', secs, d.head_ring, shapes=self.shapes))
        self.points['head'] = (o + hd * (0.35 * Lh), hd, hn)

        # the lower jaw: hinged under the cheek, opened [jaw] degrees
        jt, jcz = S['jaw_hinge']
        hinge = o + hd * (jt * Lh) + hn * (jcz * H)
        ja = math.radians(P.get('jaw', 0.0))
        jd = hd * math.cos(ja) - hn * math.sin(ja)
        jn = hn * math.cos(ja) + hd * math.sin(ja)
        jv = jd.cross(jn)
        rows = resample(S['jaw'], d.jaw_st)
        secs = [Sec(hinge + jd * ((t - jt) * Lh) + jn * (cz * H), jn, jv, up * H, dn * H, w * H, w * H, p=2.2) for t, cz, up, dn, w in rows]
        self.add('head', piece('jaw', secs, d.jaw_ring, shapes=self.shapes))
        self.points['jaw'] = (hinge, jd, jn)
        self.jaw_frame = (hinge, jd, jn, jv)

        # the nose pad: a small rounded end on the muzzle
        nt, ncz, nr = S['nose']
        nc = o + hd * (nt * Lh) + hn * (ncz * H)
        nsecs = []
        for f, r in ((-1.0, 0.55), (-0.5, 0.9), (0.0, 1.0), (0.5, 0.85), (0.9, 0.45), (1.0, 0.08)):
            nsecs.append(Sec(nc + hd * (f * nr * H * 0.8), hn, hv, r * nr * H * 0.85, r * nr * H * 0.9, r * nr * H, r * nr * H, p=2.4))
        self.add('head', piece('nose', nsecs, 12 if d.level == 0 else 6, shapes=self.shapes))
        self.points['nose'] = nc + hd * (nr * H * 0.8)

        # eyes: each a short loft along its look, the pupil at its end
        et, ecz, ey, er = S['eye']
        for side, sg in (('l', 1), ('r', -1)):
            c = o + hd * (et * Lh) + hn * (ecz * H) - hv * (sg * ey * H)
            look = (hd * math.cos(math.radians(S['eye_out'])) - hv * (sg * math.sin(math.radians(S['eye_out'])))).normalized()
            self.points['eye_' + side] = c
            if d.eye_ring:
                u, v = frame(look, hn)
                r = er * H
                secs = [Sec(c + look * (r * f), u, v, r * k * 0.72, r * k * 0.72, r * k, r * k) for f, k in
                        ((-0.9, 0.42), (-0.5, 0.86), (0.0, 1.0), (0.5, 0.86), (0.9, 0.42))]
                self.add('head', piece('eye', secs, d.eye_ring, shapes=self.shapes))

        # ears: each a cupped blade from its base on the skull to the tip, turned by the pose
        self.ears(o, hd, hn, hv, Lh)
        if d.teeth and S.get('teeth'):
            self.teeth(o, hd, hn, hv, Lh)

    def ears(self, o, hd, hn, hv, Lh):
        S, P, d, H = self.S, self.P, self.d, self.H
        et, ecz, ey = S['ear_base']
        eh, ew, eth = S['ear']                           # height, base width, thickness (H)
        back = P.get('ears_back', 0.0)                   # degrees laid back
        for side, sg in (('l', 1), ('r', -1)):
            base = o + hd * (et * Lh) + hn * (ecz * H) - hv * (sg * ey * H)
            # the ear's axis: up, splayed out [ear_splay], tipped forward or laid back
            splay = math.radians(S['ear_splay'])
            tilt = math.radians(S['ear_tilt'] - back)    # + leans the tip forward
            ax = (hn * math.cos(splay) - hv * (sg * math.sin(splay)))
            ax = (ax * math.cos(tilt) + hd * math.sin(tilt)).normalized()
            # the opening faces forward and a little out
            face = hd - hv * (sg * 0.35)
            face = (face - ax * face.dot(ax)).normalized()
            side_ax = ax.cross(face).normalized()
            secs = []
            for f, wf, cup in ((0.0, 1.0, 0.30), (0.25, 0.92, 0.32), (0.5, 0.72, 0.30), (0.72, 0.48, 0.24), (0.9, 0.22, 0.14), (1.0, 0.04, 0.02)):
                c = base + ax * (f * eh * H)
                hw = wf * ew * H / 2
                th = eth * H * (1.2 - 0.6 * f)
                # u across the ear (its width), v through it (front to back); the front hollowed (bent back at the middle)
                secs.append(Sec(c, side_ax, -face, hw, hw, th, th, p=2.0, bend=face * (cup * hw)))
            self.add('head', piece('ear', secs, d.ear_ring, shapes=self.shapes))
            self.points['ear_' + side] = base

    def teeth(self, o, hd, hn, hv, Lh):
        S, H = self.S, self.H
        # the canines: upper ones from the upper lip down, lower ones from the jaw up
        ct, ccz, cy, clen, cr = S['canine']
        hinge, jd, jn, jv = self.jaw_frame
        for sg in (1, -1):
            top = o + hd * (ct * Lh) + hn * (ccz * H) - hv * (sg * cy * H)
            tip = top - hn * (clen * H) + hd * (clen * H * 0.15)
            self.add('head', cone('teeth', top, tip, cr * H, 6))
            jt = S['jaw_hinge'][0]
            bot = hinge + jd * ((ct - 0.035 - jt) * Lh) + jn * (S['canine_low_cz'] * H) - jv * (sg * cy * 0.85 * H)
            tip2 = bot + jn * (clen * 0.8 * H) + jd * (clen * H * 0.1)
            self.add('head', cone('teeth', bot, tip2, cr * 0.9 * H, 6))

    # ---------------------------------------------------------------- legs
    def leg_targets(self, which, side):
        """The pose's paw place for a leg: the sole's point (mm), the paw's forward and up, the metapodial's direction
        (from the fetlock up) and where the middle joint bends toward."""
        S, P, H = self.S, self.P, self.H
        sg = 1 if side == 'l' else -1
        key = which + '_' + side
        stand = S['stance'][which]
        q = P.get('legs', {}).get(key, {})
        x = q.get('x', stand['x'])
        z = q.get('z', 0.0)
        y = q.get('y', stand['y'])
        sole = V3((x * H + P.get('shift_x', 0.0) * H, sg * y * H, z * H))
        fwd = dir_xz(q.get('paw', 0.0))
        meta = q.get('meta', stand['meta'])              # degrees from upright, + leaning back at its top
        m = dir_xz(90 + meta)
        if 'meta_y' in q:
            m = (m + V3((0, sg * q['meta_y'], 0))).normalized()
        if 'paw_y' in q:
            fwd = (fwd + V3((0, sg * q['paw_y'], 0))).normalized()
        pole = V3(q.get('pole', (-1, 0, 0) if which == 'fore' else (1, 0, 0)))
        pole = V3((pole.x, pole.y * sg, pole.z))
        n = q.get('n')
        if n:
            n = V3(n)
        else:
            # the paw's top: square to its forward (in the side view), on the side the leg rises from
            c1 = V3((-fwd.z, 0, fwd.x))
            n = c1 if c1.dot(m) + 0.3 * c1.z >= 0 else -c1
        root = q.get('root', (0.0, 0.0))
        return sole, fwd, m, pole, n, root

    def paw(self, sole, fwd, n, side, block, size, pts_name):
        S, d, H = self.S, self.d, self.H
        plen, pw, ph = size
        if n is None:
            n = UP - fwd * UP.dot(fwd)
        n = n.normalized()
        fwd = (fwd - n * fwd.dot(n)).normalized()
        v = fwd.cross(n)
        rows = resample(S['paw_shape'], d.paw_st)
        secs = []
        for f, up, dn, w in rows:
            c = sole + fwd * ((f - 0.20) * plen * H) + n * (0.5 * ph * H)
            secs.append(Sec(c, n, v, up * ph * H, dn * ph * H, w * pw * H, w * pw * H, p=2.6))
        self.add('legs', piece(block, secs, d.paw_ring, shapes=self.shapes))
        self.points[pts_name] = (sole, fwd, n)
        return sole + n * (0.72 * ph * H) - fwd * (0.06 * plen * H)

    def limb(self, block, joints, sizes, ring, s=None, side='l'):
        """A tube through a limb's joints: sizes per joint (width half, front half, back half); the 'up' of its
        sections is the animal's left so width is sideways and depth front to back."""
        H = self.H
        secs = []
        for i, q in enumerate(joints):
            a = joints[max(i - 1, 0)]
            b = joints[min(i + 1, len(joints) - 1)]
            t = (b - a).normalized()
            u, v = frame(t, (0, 1, 0))
            # keep 'front' (+v) toward the animal's forward
            if v.x < 0 and abs(t.z) > 0.3:
                v = -v
                u = -u
            if side == 'r':
                u = -u                                   # the outer side first on both legs (the same paint)
            w, fr, bk = sizes[i]
            secs.append(Sec(q, u, v, w * H, w * H, fr * H, bk * H, p=2.1))
        return piece(block, secs, ring, s=s, shapes=self.shapes)

    def chain(self, pts, per):
        """Points along a polyline of joints, [per] between each pair, with each one's place along the whole by length."""
        out = []
        for i in range(len(pts) - 1):
            for k in range(per[i]):
                out.append(pts[i].lerp(pts[i + 1], k / per[i]))
        out.append(pts[-1])
        return out

    def foreleg(self, side):
        S, d, H = self.S, self.d, self.H
        sg = 1 if side == 'l' else -1
        sx, sz, sy = S['shoulder']
        sole, fwd, m, pole, n, root = self.leg_targets('fore', side)
        shoulder = self.body_pt(sx, sz, sg * sy) + V3((root[0] * H, 0, root[1] * H))
        fet = self.paw(sole, fwd, n, side, 'forepaw', S['forepaw'], 'foot_f' + side)
        a, b, c = (x * H for x in S['fore_bones'])        # humerus, radius, metacarpus
        carpus = fet + m * c
        elbow, carpus, reach = ik2(shoulder, carpus, a, b, pole)
        self.reach['fore_' + side] = reach
        # the upper arm: from above the shoulder joint (inside the body) to the elbow, its muscle thick
        top = shoulder + self.body_dir((0.03 * H, 0, 0.10 * H)) * 1.0
        sz_ = S['fore_sizes']
        pts = [top, shoulder, shoulder.lerp(elbow, 0.5), elbow, elbow.lerp(carpus, 0.35), elbow.lerp(carpus, 0.7), carpus,
               carpus.lerp(fet, 0.5), fet]
        sizes = [sz_['top'], sz_['shoulder'], sz_['arm'], sz_['elbow'], sz_['fore1'], sz_['fore2'], sz_['carpus'], sz_['pastern'], sz_['fet']]
        if d.level == 0:
            self.add('legs', self.limb('foreleg', pts, sizes, d.leg_ring, s=self.limb_s(pts), side=side))
        else:
            self.add('legs', self.limb('foreleg', pts[1:], sizes[1:], d.leg_ring, s=self.limb_s(pts[1:]), side=side))
        self.points['shoulder_' + side] = shoulder
        self.points['elbow_' + side] = elbow
        self.points['wrist_' + side] = carpus

    def hindleg(self, side):
        S, d, H = self.S, self.d, self.H
        sg = 1 if side == 'l' else -1
        hx, hz, hy = S['hip']
        sole, fwd, m, pole, n, root = self.leg_targets('hind', side)
        hip = self.body_pt(hx, hz, sg * hy) + V3((root[0] * H, 0, root[1] * H))
        fet = self.paw(sole, fwd, n, side, 'hindpaw', S['hindpaw'], 'foot_h' + side)
        a, b, c = (x * H for x in S['hind_bones'])        # femur, tibia, metatarsus
        hock = fet + m * c
        stifle, hock, reach = ik2(hip, hock, a, b, pole)
        self.reach['hind_' + side] = reach
        sz_ = S['hind_sizes']
        # the thigh: a broad muscle from the croup to the stifle; the gaskin to the hock (its point, the heel bone,
        # behind); the metatarsus to the paw
        tib = (hock - stifle).normalized()
        top = hip + self.body_dir((0.02 * H, 0, 0.12 * H))
        pts = [top, hip, hip.lerp(stifle, 0.5), stifle, stifle.lerp(hock, 0.4), stifle.lerp(hock, 0.78), hock,
               hock.lerp(fet, 0.5), fet]
        sizes = [sz_['top'], sz_['hip'], sz_['thigh'], sz_['stifle'], sz_['gaskin1'], sz_['gaskin2'], sz_['hock'], sz_['meta'], sz_['fet']]
        if d.level != 0:
            pts, sizes = pts[1:], sizes[1:]
        self.add('legs', self.limb('hindleg', pts, sizes, d.thigh_ring if d.level == 0 else d.leg_ring, s=self.limb_s(pts), side=side))
        self.points['hip_' + side] = hip
        self.points['stifle_' + side] = stifle
        self.points['hock_' + side] = hock

    def limb_s(self, pts):
        s, _ = s_by_length(pts)
        return s

    # ---------------------------------------------------------------- tail
    def tail(self):
        S, P, d, H = self.S, self.P, self.d, self.H
        base = self.body_pt(*S['tail_base'])
        angs = P.get('tail', S['tail_hang'])            # degrees below backward, at even steps along the tail
        L = S['tail_len'] * H
        n = len(angs)
        pts = [base]
        for a in angs:
            a, b = (a, 0.0) if not isinstance(a, (tuple, list)) else a
            aa, bb = math.radians(a), math.radians(b)
            pts.append(pts[-1] + V3((-math.cos(aa) * math.cos(bb), math.cos(aa) * math.sin(bb), -math.sin(aa))) * (L / n))
        path = smooth_path(pts, d.tail_st)
        rows = resample(S['tail_r'], d.tail_st)
        bush = P.get('tail_bush', 1.0)
        secs = []
        for i, q in enumerate(path):
            a = path[max(i - 1, 0)]
            b = path[min(i + 1, len(path) - 1)]
            t = (b - a).normalized()
            u, v = frame(t, (0, 1, 0))
            _, w, dep = rows[i]
            secs.append(Sec(q, u, v, w * H * bush, w * H * bush, dep * H * bush, dep * H * bush, p=2.0))
        self.add('body', piece('tail', secs, d.tail_ring, shapes=self.shapes))
        self.points['tail_base'] = (base, (path[1] - path[0]).normalized(), UP)

    # ---------------------------------------------------------------- collar
    def collar(self):
        S, d, H = self.S, self.d, self.H
        f, out_mm, w_mm, th_mm = S['collar']
        secs = self.neck_secs
        i = f * (len(secs) - 1)
        i0 = int(i)
        i1 = min(i0 + 1, len(secs) - 1)
        k = i - i0
        a, b = secs[i0], secs[i1]
        ring = []
        nr = d.collar_st
        for j in range(nr):
            th = 2 * math.pi * j / nr
            q = a.point(th).lerp(b.point(th), k)
            c = a.c.lerp(b.c, k)
            ring.append(c + (q - c) * 1.0 + (q - c).normalized() * out_mm)
        axis = (b.c - a.c).normalized()
        pc = Piece('collar')
        rings = []
        m = d.collar_ring
        for j in range(nr):
            q = ring[j]
            c = a.c.lerp(b.c, k)
            radial = (q - c).normalized()
            radial = (radial - axis * radial.dot(axis)).normalized()
            rr = []
            for kk in range(m):
                ang = 2 * math.pi * kk / m
                off = radial * (math.cos(ang) * th_mm / 2) + axis * (math.sin(ang) * w_mm / 2)
                rr.append(pc.vert(q + off))
            rings.append(rr)
        for j in range(nr):
            j1 = (j + 1) % nr
            for kk in range(m):
                k1 = (kk + 1) % m
                s0, s1 = j / nr, (j + 1) / nr
                pc.tri(rings[j][kk], rings[j1][kk], rings[j1][k1], (s0, kk / m), (s1, kk / m), (s1, (kk + 1) / m))
                pc.tri(rings[j][kk], rings[j1][k1], rings[j][k1], (s0, kk / m), (s1, (kk + 1) / m), (s0, (kk + 1) / m))
        self.add('collar', pc.outward())
        # the ring: under the throat (the section's -v side is the throat)
        th = math.pi * 1.5
        q = a.point(th).lerp(b.point(th), k)
        c = a.c.lerp(b.c, k)
        radial = (q - c).normalized()
        ring_c = q + radial * (out_mm + th_mm + 9)
        self.points['collar_ring'] = ring_c
        if d.level == 0:
            self.add('collar', torus('collar', ring_c, axis.cross(radial).normalized(), 10.0, 1.8, 14, 6))


class KeelSec:
    """A torso section whose lower half narrows to [wl] (the chest's keel, the belly): like Sec, the width below the
    middle eased from the upper width to [wl] at the bottom."""

    def __init__(self, sec, wl):
        self.sec, self.wl = sec, wl
        self.c, self.u, self.v = sec.c, sec.u, sec.v
        self.au, self.ad, self.bl, self.br, self.p = sec.au, sec.ad, sec.bl, sec.br, sec.p

    def point(self, th):
        q = self.sec.point(th)
        c = math.cos(th)
        if c < 0:
            k = (-c) ** 1.5
            off = q - self.c
            along_v = off.dot(self.v)
            scale = (1 - k) + k * (self.wl / self.sec.bl)
            q = q - self.v * along_v * (1 - scale)
        return q


def cone(block, base, tip, r, n):
    ax = (tip - base).normalized()
    u, v = frame(ax, (0, 1, 0) if abs(ax.y) < 0.9 else (1, 0, 0))
    secs = [Sec(base, u, v, r, r, r, r), Sec(base.lerp(tip, 0.5), u, v, r * 0.6, r * 0.6, r * 0.6, r * 0.6),
            Sec(tip, u, v, r * 0.08, r * 0.08, r * 0.08, r * 0.08)]
    return loft(block, secs, n)


def torus(block, c, axis, R, r, n, m):
    axis = axis.normalized()
    u, v = frame(axis, (0, 0, 1) if abs(axis.z) < 0.9 else (1, 0, 0))
    pc = Piece(block)
    rings = []
    for j in range(n):
        a = 2 * math.pi * j / n
        radial = u * math.cos(a) + v * math.sin(a)
        q = c + radial * R
        rings.append([pc.vert(q + radial * (r * math.cos(2 * math.pi * k / m)) + axis * (r * math.sin(2 * math.pi * k / m))) for k in range(m)])
    for j in range(n):
        j1 = (j + 1) % n
        for k in range(m):
            k1 = (k + 1) % m
            pc.tri(rings[j][k], rings[j1][k], rings[j1][k1], (j / n, k / m), ((j + 1) / n, k / m), ((j + 1) / n, (k + 1) / m))
            pc.tri(rings[j][k], rings[j1][k1], rings[j][k1], (j / n, k / m), ((j + 1) / n, (k + 1) / m), (j / n, (k + 1) / m))
    return pc.outward()

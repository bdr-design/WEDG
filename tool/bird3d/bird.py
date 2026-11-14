"""A bird from its numbers: one body (tail base to forehead) lofted along a centre line bent by the pose, a beak, eyes,
two wings (folded on the body or spread), the tail, legs and feet. The species' numbers are in saker.py and quarry.py.

The body frame: X along the body's axis from the tail's base (0) to the front, Z up from that axis (the back), Y out
to the bird's left. The pose places that frame (its origin and pitch) and bends the neck and head; the legs are solved
from the hip to the feet's places in the world.
"""
import math

import numpy as np
from mathutils import Matrix, Vector

from common import (V3, Piece, Sec, angle_profile, bent_line, frame, loft, mirror, path_secs, resample, smooth_path,
                    smoothstep, transform, tube)


class Detail:
    def __init__(self, level, near=None):
        self.level = level
        hi = level == 0
        self.body_ring = 24 if hi else 10
        self.body_stations = 46 if hi else 15
        self.wing_ring = 12 if hi else 6
        self.wing_stations = 14 if hi else 6
        self.tail_ring = 10 if hi else 6
        self.tail_stations = 10 if hi else 4
        self.limb_ring = 8 if hi else 5
        self.toe_ring = 6 if hi else 4
        self.toe_stations = 7 if hi else 3
        self.beak_ring = 10 if hi else 6
        self.beak_stations = 9 if hi else 4
        self.eye_ring = 14 if hi else 6
        self.eye_stations = 7 if hi else 3
        for k, v in (near or {}).items():      # a small bird's near level: fewer rings where they do not show
            if hi:
                setattr(self, k, v)


class Body:
    """The body's sections along its centre line, posed. stations: rows (d, au, ad, b[, b_low]) in mm: d from the tail's
    base forward, au the half height above the line, ad below it, b the half width."""

    def __init__(self, stations, pose, det, head_weight=1.8, head_from=None):
        n = det.body_stations
        rows = resample(stations, n)
        self.rows = rows
        self.d_end = rows[-1][0]
        self.pose = pose
        ang = angle_profile(pose['spine'])
        self.angle = ang
        start = pose['origin']
        self.line = bent_line(start, self.d_end + 1, ang)
        # texture place along: by length, the head given [head_weight] times as many texels per mm
        hf = head_from if head_from is not None else rows[-1][0] - 70
        w = [1.0 + (head_weight - 1.0) * smoothstep(hf - 20, hf + 10, r[0]) for r in rows]
        s = [0.0]
        for i in range(1, len(rows)):
            s.append(s[-1] + (rows[i][0] - rows[i - 1][0]) * 0.5 * (w[i] + w[i - 1]))
        self.s = [x / s[-1] for x in s]
        self.d = [r[0] for r in rows]
        self.secs = []
        for r in rows:
            c, t = self.line(r[0])
            u, v = frame(t, (-t.z, 0, t.x))      # up: the line's direction turned a quarter up
            self.secs.append(Sec(c, u, v, r[1], r[2], r[3], r[3], p=pose.get('p', 2.0)))

    def piece(self, det, block='body'):
        return loft(block, self.secs, det.body_ring, s=self.s, caps=(True, True))

    def size_at(self, d):
        rows = np.array(self.rows)
        return [float(np.interp(d, rows[:, 0], rows[:, k])) for k in range(1, 4)]

    def frame_at(self, d):
        c, t = self.line(d)
        u, v = frame(t, (-t.z, 0, t.x))
        return c, t, u, v

    def at(self, d, up=0.0, out=0.0, fwd=0.0):
        """A point by the body's own frame at distance d along the line: [up] along the section's up, [out] along its
        v (the bird's right), [fwd] along the line."""
        c, t, u, v = self.frame_at(d)
        return c + u * up + v * out + t * fwd

    def surface(self, d, th):
        """The surface point at distance d and ring angle th (0 the top, pi/2 the left)."""
        au, ad, b = self.size_at(d)
        c, t, u, v = self.frame_at(d)
        return Sec(c, u, v, au, ad, b, b, p=self.pose.get('p', 2.0)).point(th)


def torso(body):
    """The torso's frame (the body frame): origin at the tail's base, X along the torso's straight axis."""
    c, t = body.line(0.0)
    up = V3((-t.z, 0, t.x))
    return c, t, up


def torso_point(body, x, z, y):
    o, t, up = torso(body)
    return o + t * x + up * z + V3((0, 1, 0)) * y


# ------------------------------------------------------------------ head parts
def head_frame(body, d):
    c, t, u, v = body.frame_at(d)
    return c, t, u, v


def beak(body, spec, det):
    """The beak from the forehead's end: a lofted horn bent down to its tip; the cere (if any) as a piece of its own."""
    b = spec['beak']
    d0 = body.d_end - b.get('sink', 3.0)
    c, t, u, v = head_frame(body, body.d_end)
    o = body.at(d0, up=b.get('up0', 0.0))
    pts, sizes = [], []
    n = det.beak_stations
    for i in range(n):
        f = i / (n - 1)
        # the culmen's curve: straight then hooked over [hook] of its length (falcons), or gently down (others)
        along = b['length'] * f
        drop = b['droop'] * f ** b.get('droop_pow', 2.0)
        pts.append(o + t * along - u * drop)
        h = b['h0'] * (1 - f) ** b.get('h_pow', 0.8) + b.get('h_tip', 0.8)
        w = b['w0'] * (1 - f) ** b.get('w_pow', 0.9) + b.get('w_tip', 0.6)
        lo = h * b.get('low', 0.55)
        sizes.append((h, lo, w, w))
    # sections across the beak's own curve
    secs = []
    for i, q in enumerate(pts):
        a = pts[max(i - 1, 0)]
        bb = pts[min(i + 1, n - 1)]
        tt = (bb - a).normalized()
        uu, vv = frame(tt, u)
        au, ad, bl, br = sizes[i]
        secs.append(Sec(q, uu, vv, au, ad, bl, br, p=b.get('p', 2.2)))
    out = [loft('horn', secs, det.beak_ring, caps=(True, True))]
    if b.get('tooth') and det.level == 0:
        # the falcon's tomial tooth: a small point on each edge of the upper mandible, before the hook
        f0 = b['tooth']
        i = int(round(f0 * (n - 1)))
        sec = secs[i]
        for side in (1, -1):
            base = sec.c - sec.u * (sec.ad * 0.55) + sec.v * side * (sec.bl * 0.72)
            out.append(tube('horn', [base + sec.u * 1.2, base - sec.u * 1.4, base - sec.u * 2.6], [1.5, 1.0, 0.25], 5, up=sec.v))
    if b.get('lower'):
        # the lower mandible: shorter and straight, under the upper's edges
        lo_len, lo_h, lo_w = b['lower']
        ls = []
        m = max(3, det.beak_stations // 2 + 1)
        for i in range(m):
            f = i / (m - 1)
            q = o + t * (lo_len * f) - u * (sizes[0][1] * 0.75 + b['droop'] * 0.25 * f ** 2)
            hh = lo_h * (1 - f) ** 0.7 + 0.6
            ww = lo_w * (1 - f) ** 0.8 + 0.6
            ls.append(Sec(q, u, v, hh * 0.6, hh, ww, ww, p=2.0))
        out.append(loft('horn', ls, max(6, det.beak_ring - 2), caps=(True, True)))
    if b.get('cere'):
        # the cere: bare skin over the beak's root, from inside the face onto the horn, a little fuller than it
        L = b['cere']
        cs = []
        for f, k in ((0.0, 0.92), (0.3, 1.10), (0.65, 1.08), (1.0, 0.99)):      # rising out of the face, not a collar
            q = o + t * (L * f - 8) + u * 0.6
            au, ad, bl, br = sizes[0]
            cs.append(Sec(q, u, v, au * k, ad * 0.85, bl * k, br * k, p=2.2))
        out.append(loft('skin', cs, det.beak_ring, caps=(True, True)))
    return out


def eyes(body, spec, det):
    """Each eye a lens set into the head, with its bare ring of skin round it if the species has one."""
    e = spec['eye']
    out = []
    for side in (1, -1):
        c, t, u, v = head_frame(body, e['d'])
        au, ad, b = body.size_at(e['d'])
        centre = c + u * e['up'] + v * side * (b * e.get('out', 0.86))
        look_dir = (v * side * math.cos(math.radians(e.get('fwd', 25))) + t * math.sin(math.radians(e.get('fwd', 25)))).normalized()
        r = e['r']
        secs = []
        n = det.eye_stations
        for i in range(n):
            f = i / (n - 1)
            ang = -math.pi / 2 + math.pi * f
            along = math.sin(ang) * r
            rad = max(math.cos(ang) * r, 0.25)
            uu, vv = frame(look_dir, u)
            secs.append(Sec(centre + look_dir * along, uu, vv, rad, p=2.0))
        out.append(loft('eye', secs, det.eye_ring, caps=(True, True)))
        if e.get('ring') and det.level == 0:
            # the bare skin round the eye: a flat ring laid on the face all round the eye's rim
            rr = e['ring']
            pts, n2 = [], 16 if det.level == 0 else 8
            uu, vv = frame(look_dir, u)
            for k in range(n2):
                a = 2 * math.pi * k / n2
                radial = uu * math.cos(a) + vv * math.sin(a)
                q = centre - look_dir * (r * 0.5) + radial * (r * 0.92 + rr * 0.4)
                for _ in range(80):          # out along the eye's axis until it sits on the face
                    if not inside_head(body, q, 0.2):
                        break
                    q = q + look_dir * 0.25
                pts.append(q)
            out.append(loop_tube('skin', pts, rr * 0.5, 6 if det.level == 0 else 4, look_dir, flat=0.45))
        if e.get('brow') and det.level == 0:
            # the falcon's frown: a ridge of bone and feathers over the eye, coloured from the crown beside it
            length, height, width = e['brow']
            secs = []
            m = 5 if det.level == 0 else 3
            above = (u - look_dir * u.dot(look_dir)).normalized()
            for i in range(m):
                f = i / (m - 1)
                q = centre + above * (r * 0.96) + look_dir * (r * 0.34) + t * (length * (f - 0.45))
                k = math.sin(math.pi * (0.08 + 0.84 * f))
                secs.append(Sec(q, above, look_dir.cross(above) * side, height * k + 0.3, height * k + 0.3, width * k + 0.3, p=2.0))
            pc = loft('body', secs, 8 if det.level == 0 else 5, caps=(True, True))
            s_b = float(np.interp(e['d'], body.d, body.s))
            t_b = 0.20 if side > 0 else 0.80
            pc.UV = [((s_b, t_b),) * 3 for _ in pc.T]
            out.append(pc)
    return out


def inside_head(body, q, margin):
    """Whether point q lies inside the body's surface (by its nearest section), with [margin] mm to spare."""
    best = None
    for d in np.linspace(body.d_end - 70, body.d_end, 71):
        c, t, u, v = body.frame_at(d)
        dd = abs((q - c).dot(t))
        if best is None or dd < best[0]:
            best = (dd, d, c, u, v)
    _, d, c, u, v = best
    au, ad, b = body.size_at(d)
    x, y = (q - c).dot(u), (q - c).dot(v)
    a = au if x >= 0 else ad
    p = body.pose.get('p', 2.0)
    return (abs(x) / (a + margin)) ** p + (abs(y) / (b + margin)) ** p < 1.0


def loop_tube(block, pts, radius, n, up, flat=1.0):
    """A closed ring of tube through [pts] (a loop); [flat] squeezes its section along [up]."""
    pc = Piece(block)
    m = len(pts)
    rings = []
    for i in range(m):
        a, b = pts[(i - 1) % m], pts[(i + 1) % m]
        uu, vv = frame(b - a, up)
        sec = Sec(pts[i], uu, vv, radius * flat, radius * flat, radius, radius)
        rings.append([pc.vert(sec.point(2 * math.pi * k / n)) for k in range(n)])
    for i in range(m):
        r0, r1 = rings[i], rings[(i + 1) % m]
        s0, s1 = i / m, (i + 1) / m
        for k in range(n):
            k1 = (k + 1) % n
            pc.tri(r0[k], r0[k1], r1[k1], (s0, k / n), (s0, (k + 1) / n), (s1, (k + 1) / n))
            pc.tri(r0[k], r1[k1], r1[k], (s0, k / n), (s1, (k + 1) / n), (s1, k / n))
    return pc.outward()


# ------------------------------------------------------------------ wings
def folded_wing(body, spec, det):
    """The folded wing lying on the body's side, from the primaries' tips over the tail to the wrist. Rows (x rising):
    (x, z_top, z_bottom, y_mid, half_thickness, bend) in the body frame."""
    rows = resample(spec['fold'], det.wing_stations)
    o, t, up = torso(body)
    side = V3((0, 1, 0))
    secs = []
    for (x, zt, zb, y, th, bend) in rows:
        zc = (zt + zb) / 2
        h = max((zt - zb) / 2, 0.8)
        c = o + t * x + up * zc + side * y
        secs.append(Sec(c, up, side, h, h, th, th, p=2.4, bend=-side * bend))
    # rows run from the tip (along 0) to the wrist (along 1)
    pc = loft('wing_fold', secs, det.wing_ring, caps=(True, True))
    return [pc, mirror(pc)]


def open_wing(body, spec, det, pose):
    """The spread wing, root to tip. Rows: (y, x_leading, x_trailing, z, half_thickness, camber) in the body frame
    (the body level). pose['wing_dihedral'] lifts it (deg) about the root, pose['wing_sweep'] turns the hand back."""
    rows = resample(spec['open'], det.wing_stations + 4)
    o, t, up = torso(body)
    side = V3((0, 1, 0))
    secs = []
    di = math.radians(pose.get('wing_dihedral', 0.0))
    for (y, xl, xt, z, th, cam) in rows:
        xc = xl - 0.32 * (xl - xt)      # the thickest place a third of the chord behind the leading edge
        au = xl - xc
        ad = xc - xt
        yy = y * math.cos(di)
        zz = z + (y - rows[0][0]) * math.sin(di)
        c = o + t * xc + up * zz + side * yy
        secs.append(Sec(c, t, up, max(au, 0.6), max(ad, 0.6), th, th * 0.55, p=2.0, bend=-up * cam))
    pc = loft('wing_open', secs, det.wing_ring + (2 if det.level == 0 else 0), caps=(True, True))
    return [pc, mirror(pc)]


def fingers(body, spec, det, pose):
    """Separate primary tips (bustards' slotted hand): each a thin blade from inside the wing's outer edge."""
    out = []
    if not spec.get('fingers'):
        return out
    o, t, up = torso(body)
    side = V3((0, 1, 0))
    di = math.radians(pose.get('wing_dihedral', 0.0))
    for (y0, x0, y1, x1, w, z1) in spec['fingers']:
        pts, sizes = [], []
        n = 5 if det.level == 0 else 3
        for i in range(n):
            f = i / (n - 1)
            y = y0 + (y1 - y0) * f
            x = x0 + (x1 - x0) * f
            z = (y - spec['open'][0][0]) * math.sin(di) + z1 * f * f
            pts.append(o + t * x + up * z + side * (y * math.cos(di)))
            ww = w * (1 - 0.55 * f ** 2)
            sizes.append((ww, ww, 1.6 - f, 1.2 - 0.8 * f))
        secs = []
        for i, q in enumerate(pts):
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
            d = (b - a).normalized()
            u = (t - d * t.dot(d)).normalized()
            v = d.cross(u)
            au, ad, bl, br = sizes[i]
            secs.append(Sec(q, u, v, au, ad, bl, br, p=2.0))
        pc = loft('wing_open', secs, 6 if det.level == 0 else 4, caps=(True, True), s_range=(0.97, 1.0))
        out += [pc, mirror(pc)]
    return out


# ------------------------------------------------------------------ tail
def tail(body, spec, pose, det):
    """The tail from inside the rump to its tip. Rows: (dist, half_width, half_thickness, z_offset)."""
    rows = resample(spec['tail'], det.tail_stations)
    o, t, up = torso(body)
    droop = math.radians(pose.get('tail_droop', 0.0))
    back = (-t * math.cos(droop) - up * math.sin(droop)).normalized()
    tup = back.cross(V3((0, 1, 0))).normalized()
    if tup.dot(up) < 0:
        tup = -tup
    spread = pose.get('tail_spread', 1.0)
    base = o + t * spec.get('tail_root', 20.0) + up * spec.get('tail_up', 4.0)
    secs = []
    for (dist, hw, th, zo) in rows:
        c = base + back * dist + tup * zo
        w = hw * (1 + (spread - 1) * smoothstep(0, rows[-1][0], dist))
        secs.append(Sec(c, V3((0, 1, 0)), tup, w, w, th, th * 0.8, p=2.6, bendv=-tup * 0.0))
    return [loft('tail', secs, det.tail_ring, caps=(True, True))]


# ------------------------------------------------------------------ legs and feet
def two_bone(a, c, l1, l2, bend_dir):
    """The middle joint between a and c for links l1, l2, bent toward bend_dir."""
    d = c - a
    L = min(d.length, l1 + l2 - 0.01)
    dn = d.normalized()
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    perp = (bend_dir - dn * bend_dir.dot(dn)).normalized()
    return a + dn * x + perp * h


def legs(body, spec, pose, det):
    """Each leg: the feathered shank (tibia) from inside the belly to the ankle, the bare tarsus to the foot, the toes
    and their claws. pose['feet']: the left foot's place in the world (mm) and its turn (deg, toes' heading)."""
    L = spec['leg']
    out = {'shank': [], 'tarsus': [], 'toes': [], 'claws': []}
    pts = {}
    for side in (1, -1):
        knee = torso_point(body, L['knee'][0], L['knee'][1], L['knee'][2] * side)
        fx, fy, fz = pose['foot']
        foot = V3((fx, fy * side, fz + L.get('foot_up', 0.0)))
        if side < 0 and pose.get('foot_r_shift'):
            foot = foot + V3(pose['foot_r_shift'])      # one foot a little back: the weight not evenly on both
        if pose.get('tucked'):
            # in flight the legs are drawn up under the body, the feet toward the tail
            ankle = torso_point(body, *pose['tuck_ankle'][:2], pose['tuck_ankle'][2] * side)
            foot = torso_point(body, *pose['tuck_foot'][:2], pose['tuck_foot'][2] * side)
        else:
            ankle = two_bone(knee, foot, L['tibia'], L['tarsus'], V3((-1, 0, 0)))
        # the shank: feathered, thick, from inside the belly to the ankle
        # the feathers of the shank ('trousers') hang over the tarsus' top for [trouser] of its length
        low = ankle.lerp(foot, L.get('trouser', 0.0))
        sh = smooth_path([knee, knee.lerp(ankle, 0.55), low], 5 if det.level == 0 else 3)
        rad = [L['shank_r'][0], L['shank_r'][1], L['shank_r'][2], L['shank_r'][3], L['shank_r'][4]]
        if det.level != 0:
            rad = [rad[0], rad[2], rad[4]]
        out['shank'].append(tube('thigh', sh, rad, det.limb_ring + 2, up=V3((0, side, 0)), caps=(True, True)))
        # the tarsus: bare scaled skin, a little deeper than wide; the stone-curlew's 'thick knee' is its ankle
        tp = smooth_path([ankle, ankle.lerp(foot, 0.5), foot], 4 if det.level == 0 else 2)
        tr = [L['tarsus_r'][0]] + [L['tarsus_r'][1]] * (len(tp) - 2) + [L['tarsus_r'][2]]
        out['tarsus'].append(tube('skin', tp, tr, det.limb_ring, up=V3((1, 0, 0)), caps=(True, True)))
        if L.get('knob'):
            out['tarsus'].append(ball('skin', ankle + (ankle - knee).normalized() * 0.0, L['knob'], det.limb_ring))
        heading = math.radians(pose.get('foot_turn', 0.0) * side)
        toes, claws, tips = foot_parts(foot, spec['toes'], heading, side, det, pose)
        out['toes'] += toes
        out['claws'] += claws
        pts['foot_l' if side > 0 else 'foot_r'] = foot
        pts['ankle_l' if side > 0 else 'ankle_r'] = ankle
        pts['tarsus_l' if side > 0 else 'tarsus_r'] = ankle.lerp(foot, L.get('jess_at', 0.8))
    return out, pts


def ball(block, c, r, n):
    secs = []
    m = max(3, n // 2 + 1)
    for i in range(m):
        a = -math.pi / 2 + math.pi * i / (m - 1)
        secs.append(Sec(c + V3((0, 0, 1)) * math.sin(a) * r, V3((1, 0, 0)), V3((0, 1, 0)), max(math.cos(a) * r, 0.2)))
    return loft(block, secs, n, caps=(True, True))


def foot_parts(foot, toes, heading, side, det, pose):
    """Toes from the foot's centre: each (heading deg, length, radius, curl deg). Flat on the surface when perched,
    curled into a fist in flight."""
    tucked = pose.get('tucked', False)
    toe_out, claw_out, tips = [], [], []
    rot = Matrix.Rotation(heading, 3, 'Z')
    for (hd, length, r, claw, curl) in toes:
        a = math.radians(hd * side if abs(hd) != 180 else hd)
        if tucked:
            # in flight the feet are drawn back under the tail coverts, the toes closed together, pointing back
            a = math.radians(180 + 0.25 * hd * side) if abs(hd) != 180 else 0.0
        d = rot @ V3((math.cos(a), math.sin(a), 0))
        grip = pose.get('grip_fn')     # a rounded support (the fist): its upper surface z = grip(x, y)
        n = det.toe_stations
        pts, rad = [], []
        bend = math.radians(pose.get('toe_curl', curl) if not tucked else 160)
        if tucked:
            length = length * 0.6      # the toes closed: their joints folded, the reach about two thirds
        for i in range(n):
            f = i / (n - 1)
            # the toe lies on the surface and bends down over its last joint
            ang = bend * smoothstep(0.55, 1.0, f) if tucked else 0.0
            q = foot + d * (length * f - 2.0) + V3((0, 0, r * 0.9))      # from just behind the foot's middle
            knuckle = 1.0 + 0.30 * math.sin(f * math.pi * 3) ** 2 if det.level == 0 else 1.0
            rad.append(r * (1.1 - 0.35 * f) * knuckle)
            if grip and not tucked:
                # the toe follows the support's surface: it grips the fist rather than overhangs it or sinks in
                q = V3((q.x, q.y, grip(q.x, q.y) + rad[-1] + 0.3))
            pts.append(q)
        if tucked:
            # roll the toe up toward the sole
            q = [pts[0]]
            dirv = d.copy()
            seg = length / (n - 1)
            for i in range(1, n):
                k = Matrix.Rotation(bend / (n - 1), 3, d.cross(V3((0, 0, 1))).normalized())      # curled up, into the body
                dirv = k @ dirv
                q.append(q[-1] + dirv * seg)
            pts = q
        toe_out.append(tube('skin', pts, rad, det.toe_ring, up=V3((0, 0, 1))))
        # the claw: a curved cone from the toe's end, curving down
        tipd = (pts[-1] - pts[-2]).normalized()
        down = V3((0, 0, 1)) if tucked else V3((0, 0, -1))      # clenched in flight: the talon curls in, not down
        if tucked:
            down = (down - tipd * down.dot(tipd)).normalized() if abs(down.dot(tipd)) < 0.95 else V3((1, 0, 0))
        cpts, crad = [], []
        m = 5 if det.level == 0 else 3
        for i in range(m):
            f = i / (m - 1)
            arc = math.radians(claw[1]) * f
            p0 = pts[-1] + tipd * (r * 0.4)
            dirv = tipd * math.cos(arc) + down * math.sin(arc)
            # integrate a circular arc of length claw[0]
            R = claw[0] / max(math.radians(claw[1]), 1e-3)
            pos = p0 + tipd * (R * math.sin(arc)) + down * (R * (1 - math.cos(arc)))
            cr = max(r * 0.62 * (1 - f) ** 0.9, 0.25)
            if grip and not tucked:
                pos = V3((pos.x, pos.y, max(pos.z, grip(pos.x, pos.y) + cr + 0.3)))      # the talon laid on the cuff
            cpts.append(pos)
            crad.append(cr)
        claw_out.append(tube('claw', cpts, crad, det.toe_ring, up=tipd.cross(down) if tipd.cross(down).length > 0.1 else V3((0, 0, 1))))
        tips.append(cpts[-1])
    return toe_out, claw_out, tips

"""Step 6: wheels, modelled after the rim in the owner's side photo (suv/rim_rear.png).
The rim: 12 spokes in six V pairs (each pair from one root between two studs, evenly 30 degrees apart at the lip),
machined silver faces with dark bevels and pockets, a 30 mm dish toward the hub, six studs and a black centre cap.
The size is the spec sheet's, not the photo's (the photo's wheels are 9 % bigger, see realframe.py): a 265/55R20 tyre,
0.800 m across and 265 mm wide, on a 20 x 8J rim (lip 0.536 m across), six studs on a 139.7 mm circle; track 1665 mm.

Every part is a closed solid whose faces look outward by construction (no automatic normal guessing), so a wheel
mirrored to the right side stays right side out and the back of the wheel is closed when seen from under the car.
Local frame: the axle along +Y (the car's left), the wheel's outer face at +Y."""
import bpy, bmesh, math, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import realframe as RF
R_TYRE, R_RIM, W_TYRE = RF.TYRE_D / 2, RF.RIM_R, 0.265      # the photos' wheel (realframe); the width is the spec's
# 8J is 8 inches (203 mm) between the rim flanges. Two flanges of 13 mm each make the rim 229 mm wide over all (the
# flange thickness is a game choice), so the tyre's sidewall stands 18 mm out past the rim's face on each side.
W_RIM = 8 * 0.0254 + 2 * 0.013
Y_FACE = W_RIM / 2                         # the rim's outer face
R_BARREL = R_RIM - 0.016                   # inside of the barrel (game choice: it clears the brake disc)
Y_WELL = Y_FACE - 0.115                    # the dark wall behind the spokes that closes the wheel (game choice)
HUB_Z = RF.HUB_Z
AXLE_X = RF.AXLE_X                        # front, rear
HALF_TRACK = RF.TRACK / 2
PCD_R = 0.1397 / 2
# The tyre's section, outer half: (depth below the tread's crown, half width). The owner's rear photo gives the shape
# of the shoulder: the tyre is 73 %, 84 % and 95 % of its full width at 6, 19 and 39 mm above the ground. The widest
# point is half way up the sidewall (game choice) and the bead meets the rim flange.
TYRE_SECTION = ((0.0, 0.0), (0.0008, 0.040), (0.0030, 0.075), (0.0060, 0.73 * W_TYRE / 2), (0.0105, 0.105),
                (0.019, 0.84 * W_TYRE / 2), (0.039, 0.95 * W_TYRE / 2), (0.066, W_TYRE / 2), (0.092, 0.1295),
                (0.112, 0.1215), (R_TYRE - R_RIM - 0.004, Y_FACE - 0.004))
TREAD_EDGE = 4                             # the index in TYRE_SECTION where the tread ends and the shoulder begins


def mat(name, color, metal=0.0, rough=0.5, coat=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough; b.inputs['Coat Weight'].default_value = coat
    return m


def obj(name, V, F, materials, mat_idx=None, smooth=True, sharp=40.0):
    """A mesh from faces that are already wound to look outward."""
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    for m in materials: me.materials.append(m)
    if mat_idx is not None:
        for p, i in zip(me.polygons, mat_idx): p.material_index = i
    for p in me.polygons: p.use_smooth = smooth
    if smooth:
        me.set_sharp_from_angle(angle=math.radians(sharp))
        bm = bmesh.new(); bm.from_mesh(me)                         # a change of material is always a hard edge
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.link_faces[0].material_index != e.link_faces[1].material_index: e.smooth = False
        bm.to_mesh(me); bm.free()
    return o


def revolve(name, prof, segs, materials, mat_of=None, uv=None, closed=True, sharp=40.0):
    """A solid of revolution about the Y axis. prof is [(r, y)], listed so that the outside is on the left of the
    direction of travel when r is drawn to the right and y up (a closed profile runs clockwise). Points on the axis
    become one vertex. uv, if given, is the v coordinate of every profile point (u runs round the wheel)."""
    m = len(prof); idx = []; V = []
    for r, y in prof:
        if r < 1e-9: idx.append([len(V)] * segs); V.append((0.0, y, 0.0))
        else:
            idx.append(list(range(len(V), len(V) + segs)))
            V += [(r * math.cos(2 * math.pi * k / segs), y, r * math.sin(2 * math.pi * k / segs)) for k in range(segs)]
    F, M, UV = [], [], []
    for i in range(m if closed else m - 1):
        j = (i + 1) % m
        for k in range(segs):
            k1 = (k + 1) % segs
            q = [(idx[i][k], k, i), (idx[i][k1], k + 1, i), (idx[j][k1], k + 1, j), (idx[j][k], k, j)]
            q = [c for n, c in enumerate(q) if c[0] != q[n - 1][0]]
            if len(q) < 3: continue
            F.append([c[0] for c in q]); M.append(mat_of(i) if mat_of else 0)
            UV.append([(c[1] / segs, uv[c[2]]) for c in q] if uv is not None else None)
    o = obj(name, V, F, materials, M, sharp=sharp)
    if uv is not None:
        lay = o.data.uv_layers.new(name='UVMap')
        for poly, c in zip(o.data.polygons, UV):
            for li, (a, b) in zip(poly.loop_indices, c): lay.data[li].uv = (a * 6, b)
    return o


def _spline(P, per):
    """A smooth curve through every point of P (Catmull-Rom), with per steps between neighbouring points. The points of P
    themselves stay on the curve, so the measured widths of the tyre's section are met exactly."""
    P = np.asarray(P, float); Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]]); out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = Q[i:i + 4]
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return np.array(out)


def tyre_and_rim(m_tyre, m_silver, m_dark):
    """One closed ring: the tyre from the outer bead over the tread to the inner bead, then the rim's inner flange, the
    inside of the barrel and the outer lip back to the outer bead."""
    S = np.array(TYRE_SECTION)
    tread = _spline(S[:TREAD_EDGE + 1], 2); side = _spline(S[TREAD_EDGE:], 2)
    half = np.vstack([tread, side[1:]])                             # the crown ... the bead: (depth, half width)
    half[:, 0] = np.clip(half[:, 0], 0, None); half[:, 1] = np.clip(half[:, 1], 0, W_TYRE / 2)
    nt = len(tread) - 1                                             # index of the tread's edge in half
    def v_of(i):                                                    # the texture's v: 0-0.3 a sidewall, 0.3-0.5 half the tread
        if i <= nt: return 0.5 - 0.2 * half[i, 1] / half[nt, 1]
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(half[nt:], axis=0), axis=1))]; return 0.3 * (1 - d[i - nt] / d[-1])
    outer = [((R_TYRE - half[i, 0], half[i, 1]), v_of(i)) for i in range(len(half) - 1, 0, -1)]      # the bead ... the crown
    inner = [((R_TYRE - half[i, 0], -half[i, 1]), 1 - v_of(i)) for i in range(len(half))]             # the crown ... the bead
    ty = outer + inner
    rim = [(R_RIM, -Y_FACE - 0.002), (R_RIM - 0.008, -Y_FACE - 0.003), (R_BARREL, -Y_FACE + 0.004),
           (R_BARREL, Y_FACE - 0.004), (R_RIM - 0.008, Y_FACE + 0.003), (R_RIM, Y_FACE + 0.002)]
    prof = [p for p, _ in ty] + rim; uv = [v for _, v in ty] + [0.0] * len(rim)
    n_t = len(ty) - 1                                               # segments 0 .. n_t - 1 are rubber
    silver = {n_t, n_t + 1, n_t + 5, n_t + 6}                       # the two lips; the barrel between them is dark
    return revolve('tyre', prof, 72, [m_tyre, m_silver, m_dark], mat_of=lambda i: 0 if i < n_t else 1 if i in silver else 2, uv=uv)


def rim(m_silver, m_dark, m_chrome, m_black):
    parts = []
    # behind the spokes: the hub face the spokes grow out of and a dark wall that closes the wheel, front and back
    hub = [(0.0, Y_FACE - 0.036), (0.052, Y_FACE - 0.036), (0.054, Y_FACE - 0.026), (0.060, Y_FACE - 0.024), (0.082, Y_FACE - 0.026),
           (0.086, Y_FACE - 0.040), (0.086, Y_WELL), (0.11, Y_WELL), (R_BARREL + 0.002, Y_FACE - 0.05),
           (R_BARREL + 0.002, Y_FACE - 0.062), (0.11, Y_WELL - 0.012), (0.0, Y_WELL - 0.012)]
    parts.append(revolve('hub', hub, 48, [m_dark, m_silver], mat_of=lambda i: 1 if i in (1, 2) else 0))
    # the brake disc turns with the wheel, so it can live here. One size for all four wheels (game choice)
    disc = [(0.105, Y_FACE - 0.085), (0.190, Y_FACE - 0.085), (0.190, Y_FACE - 0.110), (0.105, Y_FACE - 0.110)]
    parts.append(revolve('brake_disc', disc, 48, [mat('brake_disc', (0.16, 0.16, 0.17), metal=0.8, rough=0.6)]))
    # 12 spokes in six V pairs, as on the owner's rim: each pair grows from one root between two studs (roots at
    # 0, 60, 120 ... degrees) and splays out to the lip, where the spokes stand evenly 30 degrees apart (tips at
    # +-15 degrees from the root). Each spoke has a machined silver face and a dark bevel on the side away from its
    # partner (facing the slot between two pairs); the face dishes 20 mm toward the hub.
    V, F, M = [], [], []
    r0, r1 = 0.074, R_RIM - 0.006
    def spoke(root_a, tip_a, bevel_side):
        p0 = np.array([r0 * math.cos(root_a), r0 * math.sin(root_a)]); p1 = np.array([r1 * math.cos(tip_a), r1 * math.sin(tip_a)])
        axis = (p1 - p0) / np.linalg.norm(p1 - p0); nrm = np.array([-axis[1], axis[0]])
        rows = []
        for t in np.linspace(0, 1, 10):
            c = p0 + (p1 - p0) * t
            w = 0.026 + 0.044 * t ** 1.15
            face_y = Y_FACE + 0.001 - 0.020 * (1 - t) ** 1.3
            depth = 0.028
            sec = []
            for (u, dy) in ((-0.5, -depth), (-0.5, -0.006), (-0.5 + 0.36, 0.0), (0.5, 0.0), (0.5, -depth)):
                q = c + nrm * u * bevel_side * w; sec.append((q[0], face_y + dy, q[1]))
            if bevel_side < 0: sec = sec[::-1]
            rows.append(sec)
        base = len(V)
        for row in rows: V.extend(row)
        for i in range(len(rows) - 1):
            for j in range(5):                                      # four faces and the back: a closed tube
                a_ = base + i * 5; F.append([a_ + j, a_ + (j + 1) % 5, a_ + 5 + (j + 1) % 5, a_ + 5 + j])
                M.append(1 if j == 4 else (0 if j == 2 else 1) if bevel_side > 0 else (0 if j == 1 else 1))
        last = base + 5 * (len(rows) - 1)
        F.append([base + j for j in (4, 3, 2, 1, 0)]); F.append([last + j for j in range(5)]); M.extend([1, 1])      # its two ends
    for k in range(6):
        ra = math.radians(60 * k)
        spoke(ra + math.radians(7), ra + math.radians(15), -1)
        spoke(ra - math.radians(7), ra - math.radians(15), 1)
    parts.append(obj('spokes', V, F, [m_silver, m_dark], M, smooth=False))
    # six studs on the 139.7 mm circle between the roots, a black cap over the 106 mm centre bore
    for k in range(6):
        a = math.radians(30 + 60 * k)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0115, depth=0.024, location=(PCD_R * math.cos(a), Y_FACE - 0.014, PCD_R * math.sin(a)), rotation=(math.pi / 2, 0, 0))
        n_ = bpy.context.active_object; n_.data.materials.append(m_chrome); parts.append(n_)
    cap = [(0.0, Y_FACE - 0.008), (0.030, Y_FACE - 0.010), (0.044, Y_FACE - 0.015), (0.048, Y_FACE - 0.024), (0.048, Y_FACE - 0.038), (0.0, Y_FACE - 0.038)]
    parts.append(revolve('cap', cap, 40, [m_black]))
    return parts


def build(tyre_mat):
    m_silver = mat('rim_machined', (0.78, 0.79, 0.80), metal=1.0, rough=0.22)
    m_dark = mat('rim_dark', (0.045, 0.046, 0.05), metal=0.25, rough=0.5)
    m_chrome = mat('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
    m_black = mat('gloss_black', (0.01, 0.01, 0.01), rough=0.15, coat=1.0)
    wheels = []
    for name, x, side in (('wheel_FL', AXLE_X[0], 1), ('wheel_FR', AXLE_X[0], -1), ('wheel_RL', AXLE_X[1], 1), ('wheel_RR', AXLE_X[1], -1)):
        parts = [tyre_and_rim(tyre_mat, m_silver, m_dark)] + rim(m_silver, m_dark, m_chrome, m_black)
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts: p.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); w = bpy.context.active_object
        w.name = name; w.data.name = name
        if side < 0:                                                # the right side: mirror the points and turn every face over
            for v in w.data.vertices: v.co.y = -v.co.y
            w.data.flip_normals(); w.data.update()
        w.location = (x, side * HALF_TRACK, HUB_Z); wheels.append(w)
    return wheels

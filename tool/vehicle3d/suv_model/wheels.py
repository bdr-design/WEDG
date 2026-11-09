"""Step 6: wheels, modelled after the rim in the owner's side photo (suv/rim_rear.png).
The rim: 12 spokes in six V pairs (each pair from one root between two studs, evenly 30 degrees apart at the lip),
machined silver faces with dark bevels and pockets, a 30 mm dish toward the hub, six studs and a black centre cap.
The size is the spec sheet's, not the photo's (the photo's wheels are 8 % too big, see realframe.py): a 265/55R20 tyre,
0.800 m across, on a 20 x 8.5 rim (lip 0.536 m across), six studs on a 139.7 mm circle; track 1665 mm.
Local frame: the axle along +Y (the car's left), the wheel's outer face at +Y."""
import bpy, bmesh, math, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix

import realframe as RF
R_TYRE, R_RIM, W_TYRE = RF.TYRE_D / 2, 0.268, 0.265
HUB_Z = RF.HUB_Z
AXLE_X = RF.AXLE_X                        # front, rear
HALF_TRACK = RF.TRACK / 2
PCD_R = 0.1397 / 2

def mat(name, color, metal=0.0, rough=0.5, coat=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough; b.inputs['Coat Weight'].default_value = coat
    return m

def obj(name, V, F, materials, mat_idx=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    for m in materials: me.materials.append(m)
    if mat_idx is not None:
        for p, i in zip(me.polygons, mat_idx): p.material_index = i
    for p in me.polygons: p.use_smooth = smooth
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o

def revolve(name, prof, segs, materials, mat_of=None, uv=None):
    """prof: [(r, y)] around the Y axis."""
    V, F, M = [], [], []
    for k in range(segs + 1):
        a = 2 * math.pi * k / segs
        for r, y in prof: V.append((r * math.cos(a), y, r * math.sin(a)))
    m = len(prof)
    for k in range(segs):
        for i in range(m - 1):
            p = k * m + i; F.append([p, p + m, p + m + 1, p + 1]); M.append(mat_of(i) if mat_of else 0)
    o = obj(name, V, F, materials, M)
    if uv:
        lay = o.data.uv_layers.new(name='UVMap')
        for poly, (k, i) in zip(o.data.polygons, [(k, i) for k in range(segs) for i in range(m - 1)]):
            corners = [(k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1)]
            for li, (kk, ii) in zip(poly.loop_indices, corners): lay.data[li].uv = uv(kk / segs, ii / (m - 1))
    bpy.ops.object.select_all(action='DESELECT')
    return o

def tyre(materials):
    prof = []
    n = 24
    for i in range(n + 1):
        t = i / n; a = math.pi * t
        r = R_RIM + 0.004 + (R_TYRE - R_RIM - 0.004) * math.sin(a) ** 0.42
        w = (W_TYRE / 2) * math.cos(a) * (1 + 0.06 * math.sin(a)) - 0.004 * math.sin(a) ** 8   # a slight bulge, a crowned tread
        prof.append((r, w))
    return revolve('tyre', prof, 72, materials, uv=lambda u, v: (u * 6, v))

def rim(m_silver, m_dark, m_chrome, m_black):
    parts = []
    # the barrel and the lip
    lip = [(R_RIM + 0.004, W_TYRE / 2 - 0.004), (R_RIM, W_TYRE / 2 + 0.002), (R_RIM - 0.008, W_TYRE / 2 + 0.003), (R_RIM - 0.016, W_TYRE / 2 - 0.004),
           (R_RIM - 0.016, -W_TYRE / 2 + 0.01), (R_RIM, -W_TYRE / 2)]
    parts.append(revolve('rim_lip', lip, 72, [m_silver, m_dark], mat_of=lambda i: 0 if i < 2 else 1))
    # behind the spokes: a deep dark well and the brake disc (the disc turns with the wheel, so it can live here)
    back = [(R_RIM - 0.016, W_TYRE / 2 - 0.05), (0.11, W_TYRE / 2 - 0.115), (0.02, W_TYRE / 2 - 0.115)]
    parts.append(revolve('rim_back', back, 48, [m_dark]))
    disc = [(0.105, W_TYRE / 2 - 0.085), (0.190, W_TYRE / 2 - 0.085), (0.190, W_TYRE / 2 - 0.110), (0.105, W_TYRE / 2 - 0.110)]
    parts.append(revolve('brake_disc', disc, 48, [mat('brake_disc', (0.16, 0.16, 0.17), metal=0.8, rough=0.6)]))
    # 12 spokes in six V pairs, as on the owner's rim: each pair grows from one root between two studs (roots at
    # 0, 60, 120 ... degrees) and splays out to the lip, where the spokes stand evenly 30 degrees apart (tips at
    # +-15 degrees from the root). Each spoke has a machined silver face and a dark bevel on the side away from its
    # partner (facing the slot between two pairs); the face dishes 30 mm toward the hub.
    V, F, M = [], [], []
    r0, r1 = 0.074, R_RIM - 0.006
    def spoke(root_a, tip_a, bevel_side):
        p0 = np.array([r0 * math.cos(root_a), r0 * math.sin(root_a)]); p1 = np.array([r1 * math.cos(tip_a), r1 * math.sin(tip_a)])
        axis = (p1 - p0) / np.linalg.norm(p1 - p0); nrm = np.array([-axis[1], axis[0]])
        rows = []
        for t in np.linspace(0, 1, 10):
            c = p0 + (p1 - p0) * t; r = float(np.linalg.norm(c))
            w = 0.026 + 0.044 * t ** 1.15
            face_y = W_TYRE / 2 + 0.001 - 0.020 * (1 - t) ** 1.3
            depth = 0.028
            sec = []
            for (u, dy) in ((-0.5, -depth), (-0.5, -0.006), (-0.5 + 0.36, 0.0), (0.5, 0.0), (0.5, -depth)):
                uu = u * bevel_side
                q = c + nrm * uu * w; sec.append((q[0], face_y + dy, q[1]))
            if bevel_side < 0: sec = sec[::-1]
            rows.append(sec)
        base = len(V)
        for row in rows: V.extend(row)
        for i in range(len(rows) - 1):
            for j in range(4):
                a_ = base + i * 5 + j; F.append([a_, a_ + 1, a_ + 6, a_ + 5])
                if bevel_side > 0: M.append(0 if j == 2 else 1)
                else: M.append(0 if j == 1 else 1)
    for k in range(6):
        ra = math.radians(60 * k)
        spoke(ra + math.radians(7), ra + math.radians(15), -1)
        spoke(ra - math.radians(7), ra - math.radians(15), 1)
    parts.append(obj('spokes', V, F, [m_silver, m_dark], M, smooth=False))
    # the hub: a dark face the spokes grow out of, six studs on the 139.7 mm circle between the roots, a black cap
    # over the 106 mm centre bore
    hub = [(0.0, W_TYRE / 2 - 0.036), (0.052, W_TYRE / 2 - 0.036), (0.054, W_TYRE / 2 - 0.026), (0.060, W_TYRE / 2 - 0.024), (0.082, W_TYRE / 2 - 0.026), (0.086, W_TYRE / 2 - 0.040), (0.086, W_TYRE / 2 - 0.075)]
    parts.append(revolve('hub', hub, 48, [m_dark, m_silver], mat_of=lambda i: 1 if i in (1, 2) else 0))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0115, depth=0.024, location=(PCD_R * math.cos(a), W_TYRE / 2 - 0.014, PCD_R * math.sin(a)), rotation=(math.pi / 2, 0, 0))
        n_ = bpy.context.active_object; n_.data.materials.append(m_chrome); parts.append(n_)
    cap = [(0.0, W_TYRE / 2 - 0.008), (0.030, W_TYRE / 2 - 0.010), (0.044, W_TYRE / 2 - 0.015), (0.048, W_TYRE / 2 - 0.024), (0.048, W_TYRE / 2 - 0.036)]
    parts.append(revolve('cap', cap, 40, [m_black]))
    return parts

def build(tyre_mat):
    m_silver = mat('rim_machined', (0.78, 0.79, 0.80), metal=1.0, rough=0.22)
    m_dark = mat('rim_dark', (0.045, 0.046, 0.05), metal=0.25, rough=0.5)
    m_chrome = mat('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
    m_black = mat('gloss_black', (0.01, 0.01, 0.01), rough=0.15, coat=1.0)
    wheels = []
    for name, x, side in (('wheel_FL', AXLE_X[0], 1), ('wheel_FR', AXLE_X[0], -1), ('wheel_RL', AXLE_X[1], 1), ('wheel_RR', AXLE_X[1], -1)):
        parts = [tyre([tyre_mat])] + rim(m_silver, m_dark, m_chrome, m_black)
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts: p.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); w = bpy.context.active_object; w.name = name
        if side < 0:
            w.scale.y = -1; bpy.ops.object.transform_apply(scale=True)
            bm = bmesh.new(); bm.from_mesh(w.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(w.data); bm.free()
        w.location = (x, side * HALF_TRACK, HUB_Z); wheels.append(w)
    return wheels

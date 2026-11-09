"""Step 6: wheels, modelled after the rim in the owner's side photo (suv/rim_rear.png).
The rim: 12 straight spokes 30 degrees apart (8-10 degrees wide at the rim, 5 at mid radius), a machined silver face
with dark painted sides and pockets, a slight dish toward the hub, six lug nuts and a black centre cap.
The tyre: 0.856 m across on the 0.576 m rim face, as measured on the photo, with a tread and sidewall normal map.
Local frame: the axle along +Y (the car's left), the wheel's outer face at +Y."""
import bpy, bmesh, math, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix

R_TYRE, R_RIM, W_TYRE = 0.428, 0.288, 0.265
HUB_Z = 0.43
AXLE_X = (2.495 - 0.941, 2.495 - 3.901)   # front, rear (the photo's hub positions from its front)
HALF_TRACK = 0.86

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
    lip = [(R_RIM + 0.004, W_TYRE / 2 - 0.004), (R_RIM, W_TYRE / 2 + 0.002), (R_RIM - 0.016, W_TYRE / 2 + 0.004), (R_RIM - 0.022, W_TYRE / 2 - 0.004),
           (R_RIM - 0.022, -W_TYRE / 2 + 0.01), (R_RIM, -W_TYRE / 2)]
    parts.append(revolve('rim_lip', lip, 72, [m_silver, m_dark], mat_of=lambda i: 0 if i < 2 else 1))
    # the dark back of the face, seen between the spokes
    back = [(R_RIM - 0.022, W_TYRE / 2 - 0.05), (0.09, W_TYRE / 2 - 0.075), (0.02, W_TYRE / 2 - 0.075)]
    parts.append(revolve('rim_back', back, 48, [m_dark]))
    # spokes: tapered bars with a machined face, dished toward the hub
    V, F, M = [], [], []
    def spoke(a0):
        rs = np.linspace(0.085, R_RIM - 0.018, 9)
        rows = []
        for r in rs:
            t = (r - 0.085) / (R_RIM - 0.018 - 0.085)
            half = math.radians(2.8 + 2.0 * t ** 1.3 + 3.5 * max(0.0, 1 - (r - 0.085) / 0.05))   # flaring into the hub ring, wider at the rim
            face_y = W_TYRE / 2 - 0.006 - 0.028 * (1 - t) ** 1.5                            # the dish
            depth = 0.026
            pts = []
            for side in (-1, 1):
                a = a0 + side * half; ai = a0 + side * half * 0.78
                pts.append((r * math.cos(ai), face_y, r * math.sin(ai)))        # face edge (chamfered in)
                pts.append((r * math.cos(a), face_y - 0.006, r * math.sin(a)))    # outer edge
                pts.append((r * math.cos(a), face_y - depth, r * math.sin(a)))    # bottom
            rows.append([pts[2], pts[1], pts[0], pts[3], pts[4], pts[5]])          # around the section
        base = len(V)
        for row in rows: V.extend(row)
        for i in range(len(rows) - 1):
            for j in range(5):
                a = base + i * 6 + j; F.append([a, a + 1, a + 7, a + 6]); M.append(0 if j == 2 else 1)
    for k in range(12): spoke(math.radians(10 + 30 * k))
    parts.append(obj('spokes', V, F, [m_silver, m_dark], M, smooth=False))
    # the hub, the lug nuts and the cap
    # the hub: a machined ring the spokes grow out of, a dark centre with the lug nuts
    hub = [(0.0, W_TYRE / 2 - 0.034), (0.050, W_TYRE / 2 - 0.034), (0.056, W_TYRE / 2 - 0.030), (0.098, W_TYRE / 2 - 0.030), (0.112, W_TYRE / 2 - 0.040), (0.112, W_TYRE / 2 - 0.07)]
    parts.append(revolve('hub', hub, 48, [m_dark, m_silver], mat_of=lambda i: 1 if i in (2, 3) else 0))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.011, depth=0.022, location=(0.062 * math.cos(a), W_TYRE / 2 - 0.022, 0.062 * math.sin(a)), rotation=(math.pi / 2, 0, 0))
        n_ = bpy.context.active_object; n_.data.materials.append(m_chrome); parts.append(n_)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.036, depth=0.014, location=(0, W_TYRE / 2 - 0.024, 0), rotation=(math.pi / 2, 0, 0))
    cap = bpy.context.active_object; cap.data.materials.append(m_black); parts.append(cap)
    for p in cap.data.polygons: p.use_smooth = False
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

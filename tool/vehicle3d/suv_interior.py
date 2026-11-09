"""The cabin of the photo-built SUV, fitted to its hull.

Everything here is laid out in real metres in the car frame used for the reference measurements:
d = distance back from the front bumper, y = to the left, z = up from the ground. A point goes into the
model with x = XF - d*K, y*K, z*K (the photo model is K times the real size).
Left-hand drive (Saudi Arabia): the driver sits at y = +0.40.

Parts:
- inner skins of the body, doors and tailgate (an offset copy of the photo skin, turned inwards and
  joined to the outer skin at every edge, so no edge of the shell is ever seen from inside or through an opening)
- floor and mats, dashboard with the instrument hood, centre stack, vents and glovebox,
  centre console with armrest and cupholders, shifter
- two front seats and the second-row bench, perforated inserts, stitched grooves, headrests on posts
- steering wheel (its own object, local X = the column axis), cluster needles (their own objects)
- centre screen and cluster (one emissive atlas), rear-view mirror, sun visors, overhead console,
  grab handles, seat belts, door armrests, pulls, handles and speaker grilles
Textures come from int_tex.py (tiling maps), so UVs are in metres over the tile size.
Ergonomic numbers are game choices fitted to the hull unless marked.
"""
import bpy, bmesh, math, os, numpy as np
from mathutils import Vector, Matrix
from functools import reduce
from skimage import measure
import int_tex

C = {}            # filled by build(): XF, K, belt(d), materials

def R(p):
    return Vector((C['XF'] - p[0] * C['K'], p[1] * C['K'], p[2] * C['K']))

def to_real(x, y, z):
    K = C['K']; return (C['XF'] - x) / K, y / K, z / K

# ------------------------------------------------------------------ materials
TILE = {'int_leather': 0.22, 'int_perf': 0.15, 'int_dark': 0.22, 'int_wood': 0.55, 'int_alu': 0.25, 'int_fabric': 0.30,
        'int_carpet': 0.30, 'int_plastic': 0.25, 'int_piano': 1.0, 'int_chrome': 1.0, 'int_screen': 1.0, 'int_belt': 0.2}

def load_img(path, noncolor=False):
    im = bpy.data.images.load(path)
    if noncolor: im.colorspace_settings.name = 'Non-Color'
    im.pack(); return im

def make_mat(name, tex=None, rough=0.5, metal=0.0, coat=0.0, color=None, emit=None, nstrength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    if color: b.inputs['Base Color'].default_value = (*color, 1)
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = load_img(tex[0]); nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        if emit:
            nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
        if tex[1]:
            tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = load_img(tex[1], True)
            nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstrength
            nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m

def materials(tex_dir):
    T = int_tex.write_all(tex_dir)
    return {
        'int_leather': make_mat('int_leather', T['leather'], rough=0.48, nstrength=0.6),
        'int_perf': make_mat('int_perf', T['perf'], rough=0.52, nstrength=0.8),
        'int_dark': make_mat('int_dark', T['dark'], rough=0.55, nstrength=0.6),
        'int_wood': make_mat('int_wood', T['wood'], rough=0.22, coat=0.8, nstrength=0.3),
        'int_alu': make_mat('int_alu', T['alu'], rough=0.32, metal=1.0, nstrength=0.4),
        'int_fabric': make_mat('int_fabric', T['fabric'], rough=0.92, nstrength=0.5),
        'int_carpet': make_mat('int_carpet', T['carpet'], rough=1.0, nstrength=0.8),
        'int_plastic': make_mat('int_plastic', T['plastic'], rough=0.70, nstrength=0.5),
        'int_piano': make_mat('int_piano', None, rough=0.08, color=(0.008, 0.008, 0.009), coat=1.0),
        'int_chrome': make_mat('int_chrome', None, rough=0.06, metal=1.0, color=(0.85, 0.86, 0.88)),
        'int_screen': make_mat('int_screen', T['screen'], rough=0.15, emit=1.6),
        'int_belt': make_mat('int_belt', T['plastic'], rough=0.8, color=(0.05, 0.05, 0.05)),
    }

def use(ob, names):
    for n in names: ob.data.materials.append(C['M'][n])
    return {n: i for i, n in enumerate(names)}

# ------------------------------------------------------------------ UVs in metres, projected per face on its main axis
def tri_uv(ob):
    me = ob.data; nP = len(me.polygons)
    if not nP: return
    N = np.zeros(nP * 3); me.polygons.foreach_get('normal', N); N = N.reshape(-1, 3)
    LS = np.zeros(nP, np.int64); me.polygons.foreach_get('loop_start', LS)
    LT = np.zeros(nP, np.int64); me.polygons.foreach_get('loop_total', LT)
    MI = np.zeros(nP, np.int64); me.polygons.foreach_get('material_index', MI)
    nL = len(me.loops); LV = np.zeros(nL, np.int64); me.loops.foreach_get('vertex_index', LV)
    V = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    pol = np.empty(nL, np.int64)
    for p in range(nP): pol[LS[p]:LS[p] + LT[p]] = p
    ax = np.abs(N).argmax(1)[pol]
    tiles = np.array([TILE.get(m.name, 0.25) for m in me.materials] or [0.25])
    s = tiles[np.clip(MI[pol], 0, len(tiles) - 1)]
    co = V[LV] if ob.parent is None else V[LV]
    u = np.where(ax == 0, co[:, 1], co[:, 0]); v = np.where(ax == 2, co[:, 1], co[:, 2])
    while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
    lay = me.uv_layers.new(name='UVMap'); lay.data.foreach_set('uv', np.stack([u / s, v / s], 1).ravel())

def tri_uv_keep(ob, keep_index):
    """Tiling UVs in metres on every face except those of material keep_index (they keep their photo UVs)."""
    me = ob.data; uvl = me.uv_layers.active; names = [m.name for m in me.materials]
    for p in me.polygons:
        if p.material_index == keep_index: continue
        s_ = TILE.get(names[p.material_index], 0.25); n = p.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li, vi in zip(p.loop_indices, p.vertices):
            co = me.vertices[vi].co
            u, v = (co.y, co.z) if ax == 0 else (co.x, co.z) if ax == 1 else (co.x, co.y)
            uvl.data[li].uv = (u / s_, v / s_)

# ------------------------------------------------------------------ signed distance fields on a grid in real metres
def mx(*a): return reduce(np.maximum, a)
def mn(*a): return reduce(np.minimum, a)
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

class Grid:
    def __init__(self, lo, hi, h):
        self.lo = np.array(lo, float); self.h = h
        ax = [np.arange(lo[i], hi[i] + h, h, dtype=np.float32) for i in range(3)]
        self.D, self.Y, self.Z = np.meshgrid(*ax, indexing='ij')

def local(G, c, rot=0.0):
    d = G.D - c[0]; y = G.Y - c[1]; z = G.Z - c[2]
    if rot:
        ca, sa = math.cos(rot), math.sin(rot); d, z = ca * d - sa * z, sa * d + ca * z
    return d, y, z

def rbox(G, c, half, r, rot=0.0):
    """Rounded box. rot tilts its up axis towards the back (+d) by rot radians."""
    d, y, z = local(G, c, rot)
    q = [np.abs(d) - half[0] + r, np.abs(y) - half[1] + r, np.abs(z) - half[2] + r]
    out = np.sqrt(sum(np.maximum(a, 0) ** 2 for a in q)); ins = np.minimum(mx(*q), 0)
    return out + ins - r

def capsule(G, a, b, r):
    a = np.array(a, float); b = np.array(b, float); ab = b - a
    t = np.clip(((G.D - a[0]) * ab[0] + (G.Y - a[1]) * ab[1] + (G.Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    return np.sqrt((G.D - a[0] - t * ab[0]) ** 2 + (G.Y - a[1] - t * ab[1]) ** 2 + (G.Z - a[2] - t * ab[2]) ** 2) - r

def cyl_z(G, c, r, z0, z1):
    return mx(np.hypot(G.D - c[0], G.Y - c[1]) - r, z0 - G.Z, G.Z - z1)

def poly2d(Pd, Pz, pts):
    """Signed distance to a polygon in the d-z plane (Inigo Quilez's method)."""
    v = np.array(pts, float); n = len(v)
    dd = (Pd - v[0, 0]) ** 2 + (Pz - v[0, 1]) ** 2; s = np.ones_like(Pd)
    j = n - 1
    for i in range(n):
        e = v[j] - v[i]; wd = Pd - v[i, 0]; wz = Pz - v[i, 1]
        t = np.clip((wd * e[0] + wz * e[1]) / e.dot(e), 0, 1)
        bd = wd - e[0] * t; bz = wz - e[1] * t; dd = np.minimum(dd, bd * bd + bz * bz)
        c1 = Pz >= v[i, 1]; c2 = Pz < v[j, 1]; c3 = e[0] * wz > e[1] * wd
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3); s = np.where(flip, -s, s); j = i
    return s * np.sqrt(dd)

def groove(field, dist, depth=0.005, width=0.004, mask=1.0):
    """Press a stitched seam into a surface along the zero set of dist."""
    return field + depth * np.exp(-(dist / width) ** 2) * mask

def cut_planes(bm, faces, cuts, inv=None):
    """Split faces along planes given in real metres ((d, y, z), normal), so material borders run straight."""
    for p, n in cuts:
        co = R(p); no = Vector((-n[0], n[1], n[2])).normalized()
        if inv is not None: co = inv @ co; no = (inv.to_3x3() @ no).normalized()
        faces = [f for f in faces if f.is_valid]
        geom = faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts})
        res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-6)
        faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
    return faces

ZP = lambda z: ((0, 0, z), (0, 0, 1))
YP = lambda y: ((0, y, 0), (0, 1, 0))
DP = lambda d: ((d, 0, 0), (1, 0, 0))

def sdf_object(name, G, field, mats, assign, target, smooth=3, cuts=()):
    f = field.copy(); f[0], f[-1], f[:, 0], f[:, -1], f[:, :, 0], f[:, :, -1] = 1, 1, 1, 1, 1, 1
    v, faces, _, _ = measure.marching_cubes(f, 0.0, spacing=(G.h, G.h, G.h)); v += G.lo
    K, XF = C['K'], C['XF']
    P = np.stack([XF - v[:, 0] * K, v[:, 1] * K, v[:, 2] * K], 1)
    me = bpy.data.meshes.new(name); me.from_pydata(P.tolist(), [], faces[:, ::-1].tolist()); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    activate(ob)
    if smooth:
        mo = ob.modifiers.new('sm', 'SMOOTH'); mo.iterations = smooth; mo.factor = 0.5; bpy.ops.object.modifier_apply(modifier='sm')
    if len(me.polygons) > target:
        mo = ob.modifiers.new('dec', 'DECIMATE'); mo.ratio = target / len(me.polygons); bpy.ops.object.modifier_apply(modifier='dec')
    if cuts:
        bm = bmesh.new(); bm.from_mesh(me); cut_planes(bm, list(bm.faces), cuts)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3]); bm.to_mesh(me); bm.free()
    idx = use(ob, mats)
    for p in me.polygons:
        c = to_real(*p.center); n = (-p.normal.x, p.normal.y, p.normal.z)
        p.material_index = idx[assign(c, n)]; p.use_smooth = True
    tri_uv(ob)
    return ob

def activate(ob):
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob

# ------------------------------------------------------------------ small parts: rounded boxes, cylinders, strips
def rounded(name, c, half, r, mat, rot=(0, 0, 0), seg=3):
    """A bevelled box in real metres; rot = (roll about d, pitch towards the back, yaw) in radians."""
    K = C['K']
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0)); ob = bpy.context.active_object; ob.name = name
    ob.scale = (half[0] * K, half[1] * K, half[2] * K); bpy.ops.object.transform_apply(scale=True)
    if r > 0:
        mo = ob.modifiers.new('bv', 'BEVEL'); mo.width = min(r * K, min(half) * K * 0.98); mo.segments = 1 if r <= 0.004 else 2 if r <= 0.012 else seg; mo.limit_method = 'NONE'
        bpy.ops.object.modifier_apply(modifier='bv')
    # the car frame is mirrored in d: a pitch towards the back (+d) is a negative turn about Blender Y; rot[0] is about Blender X
    ob.rotation_euler = (rot[0], -rot[1], -rot[2]); ob.location = R(c); bpy.ops.object.transform_apply(location=True, rotation=True)
    ob.data.materials.append(C['M'][mat])
    for p in ob.data.polygons: p.use_smooth = r > 0
    tri_uv(ob); return ob

def cylinder(name, a, b, r, mat, verts=16, caps=True):
    a, b = R(a), R(b); K = C['K']
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * K, depth=(b - a).length, end_fill_type='NGON' if caps else 'NOTHING')
    ob = bpy.context.active_object; ob.name = name
    ob.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler(); ob.location = (a + b) / 2
    bpy.ops.object.transform_apply(location=True, rotation=True)
    ob.data.materials.append(C['M'][mat])
    axis = (b - a).normalized()
    for p in ob.data.polygons: p.use_smooth = abs(p.normal.dot(axis)) < 0.5
    tri_uv(ob); return ob

def strip(name, pts, width, mat, normal_hint=(0, 0, 1), thick=0.003):
    """A flat band (a seat belt) through real points."""
    V, F = [], []
    P = [R(p) for p in pts]; K = C['K']
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        side = t.cross(Vector(normal_hint)).normalized() * (width / 2 * K)
        off = t.cross(side).normalized() * (thick / 2 * K)
        V += [p - side - off, p + side - off, p + side + off, p - side + off]
    for i in range(len(P) - 1):
        a, b = 4 * i, 4 * (i + 1)
        for k in range(4): F.append([a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k])
    me = bpy.data.meshes.new(name); me.from_pydata([v[:] for v in V], [], F); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(C['M'][mat])
    tri_uv(ob); return ob

def quad_uv(name, corners, uv, mat):
    """A single quad with explicit UVs (screens). corners in real metres, in UV order (0,0) (1,0) (1,1) (0,1)."""
    me = bpy.data.meshes.new(name); me.from_pydata([R(c)[:] for c in corners], [], [[0, 1, 2, 3]]); me.update()
    lay = me.uv_layers.new(name='UVMap')
    for li, (u, v) in zip(me.polygons[0].loop_indices, uv): lay.data[li].uv = (u, v)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(C['M'][mat])
    return ob

def join(objs, name):
    objs = [o for o in objs if o]
    activate(objs[0])
    for o in objs: o.select_set(True)
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name; return ob

# ------------------------------------------------------------------ inner skins
def inner_skin(src, keep, region_mat, offset=0.028, smooth_iter=6, ratio=0.25, rim_mat='int_plastic', cuts=()):
    """Line the inside of a photo skin. The faces of src that keep() accepts are copied into a separate skin, pushed
    inwards along calm normals, turned to face the cabin, smoothed and decimated; then cut on the given planes (so the
    material borders run straight) and given cabin materials by region. Every open edge of the kept outer faces gets a
    rim strip running inwards a little past the skin, so no edge of the shell is ever seen from inside or through an
    opening. The skin and the rims are joined into src."""
    K = C['K']; me = src.data
    names = [m.name for m in me.materials]
    for n in C['M']:
        if n not in names: me.materials.append(C['M'][n]); names.append(n)
    mi = {n: i for i, n in enumerate(names)}
    mw = src.matrix_world.copy()
    wreal = lambda co: to_real(*(mw @ co))
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    sel = [f for f in bm.faces if keep(wreal(f.calc_center_median()), f)]
    if not sel: bm.free(); return
    from scipy.spatial import cKDTree
    FC = np.array([f.calc_center_median()[:] for f in sel]); FN = np.array([(f.normal * f.calc_area())[:] for f in sel])
    tree = cKDTree(FC)
    def calm_normal(v):
        ids = tree.query_ball_point(v.co[:], 0.07 * K)
        n = Vector(FN[ids].sum(0)) if ids else sum((f.normal for f in v.link_faces), Vector())
        return n.normalized() if n.length else Vector((0, 0, 1))
    # the skin, in its own mesh
    used = list({v for f in sel for v in f.verts}); idx = {v: i for i, v in enumerate(used)}
    nrm = [calm_normal(v) for v in used]
    V = [(v.co - n * offset * K)[:] for v, n in zip(used, nrm)]
    F = [[idx[v] for v in f.verts][::-1] for f in sel]                  # reversed: the skin faces the cabin
    sk_me = bpy.data.meshes.new(src.name + '_skin'); sk_me.from_pydata(V, [], F); sk_me.update()
    for m in me.materials: sk_me.materials.append(m)
    skin = bpy.data.objects.new(src.name + '_skin', sk_me); bpy.context.collection.objects.link(skin); skin.matrix_world = mw
    sb = bmesh.new(); sb.from_mesh(sk_me)
    inner = [v for v in sb.verts if not v.is_boundary]
    for _ in range(smooth_iter): bmesh.ops.smooth_vert(sb, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    sb.to_mesh(sk_me); sb.free()
    activate(skin)
    if ratio < 1:
        mo = skin.modifiers.new('dec', 'DECIMATE'); mo.ratio = ratio; bpy.ops.object.modifier_apply(modifier='dec')
    sb = bmesh.new(); sb.from_mesh(sk_me)
    faces = list(sb.faces)
    if cuts: faces = cut_planes(sb, faces, cuts, inv=mw.inverted())
    for f in sb.faces: f.material_index = mi[region_mat(wreal(f.calc_center_median()), f)]; f.smooth = True
    bmesh.ops.triangulate(sb, faces=[f for f in sb.faces if len(f.verts) > 3])
    sb.to_mesh(sk_me); sb.free()
    # rims on the outer skin's open edges, reaching 6 mm past the skin so its decimated border always lands on them
    selset = set(sel); deep = {}
    def inward(v):
        if v not in deep: deep[v] = bm.verts.new(v.co - calm_normal(v) * (offset + 0.006) * K)
        return deep[v]
    rims = []
    for f in sel:
        for e in f.edges:
            if len(e.link_faces) > 1: continue                 # only real openings need a rim
            a1, b1 = e.verts
            # keep the face's winding so the rim faces the same way round the opening
            loop = next(l for l in f.loops if l.edge is e)
            if loop.vert is b1: a1, b1 = b1, a1
            try: rims.append(bm.faces.new([b1, a1, inward(a1), inward(b1)]))
            except ValueError: pass
    for rf in rims: rf.material_index = mi[rim_mat]; rf.smooth = False
    bm.to_mesh(me); bm.free()
    # cabin UVs in metres on the skin and the rims (the photo UVs of the outer skin stay)
    for o in (src, skin):
        m_ = o.data; uvl = m_.uv_layers.active or m_.uv_layers.new(name='UVMap')
        cab = {mi[n] for n in C['M']}
        for p in m_.polygons:
            if p.material_index in cab:
                s_ = TILE.get(names[p.material_index], 0.25); n = p.normal; ax = max(range(3), key=lambda i: abs(n[i]))
                for li, vi in zip(p.loop_indices, p.vertices):
                    co = m_.vertices[vi].co
                    u, v = (co.y, co.z) if ax == 0 else (co.x, co.z) if ax == 1 else (co.x, co.y)
                    uvl.data[li].uv = (u / s_, v / s_)
    # the skin's UV layer must carry the same name as the photo skin's before joining
    if src.data.uv_layers and skin.data.uv_layers: skin.data.uv_layers[0].name = src.data.uv_layers[0].name
    activate(src); skin.select_set(True); bpy.ops.object.join()

# ------------------------------------------------------------------ the parts
FLOOR = 0.56

def floor():
    def zf(d, y):
        z = FLOOR
        if d < 1.72: z = FLOOR + (1.72 - d) / 0.32 * 0.30                       # toe board up to the firewall
        if 3.02 < d < 3.12: z = FLOOR + (d - 3.02) / 0.10 * 0.06
        if d >= 3.12: z = FLOOR + 0.06
        if d > 3.90: z = 0.80                                                       # the cargo floor over the rear axle
        if 1.45 < d < 3.10 and abs(y) < 0.17: z += 0.11 * math.cos(abs(y) / 0.17 * math.pi / 2) ** 0.6   # the tunnel
        return z
    ds = np.concatenate([np.linspace(1.40, 3.90, 34), np.linspace(3.905, 4.72, 8)]); ys = np.linspace(-1, 1, 25)
    hw = lambda d: float(np.interp(d, [3.9, 4.2, 4.5, 4.62, 4.72], [0.89, 0.86, 0.81, 0.75, 0.62]))
    V = [R((d, y * hw(d), zf(d, y * hw(d))))[:] for d in ds for y in ys]; n = len(ys); F = []
    for i in range(len(ds) - 1):
        for j in range(n - 1):
            a = i * n + j; F.append([a, a + 1, a + n + 1, a + n])
    me = bpy.data.meshes.new('floor'); me.from_pydata(V, [], F); me.update()
    ob = bpy.data.objects.new('floor', me); bpy.context.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    bm.to_mesh(me); bm.free(); ob.data.materials.append(C['M']['int_carpet']); tri_uv(ob)
    mats = [rounded(f'mat{i}', c, h, 0.008, 'int_carpet') for i, (c, h) in enumerate([
        ((2.30, 0.42, FLOOR + 0.006), (0.30, 0.22, 0.006)), ((2.30, -0.42, FLOOR + 0.006), (0.30, 0.22, 0.006)),
        ((3.30, 0.45, FLOOR + 0.066), (0.16, 0.24, 0.006)), ((3.30, -0.45, FLOOR + 0.066), (0.16, 0.24, 0.006))])]
    # a firewall behind the dashboard, so nothing shows through under it
    fw = rounded('firewall', (1.40, 0, 1.05), (0.01, 0.90, 0.30), 0, 'int_carpet')
    return [ob, fw] + mats

def dashboard():
    G = Grid((1.30, -0.93, 0.70), (2.22, 0.93, 1.48), 0.0075)
    prof = [(1.40, 0.78), (1.40, 1.30), (1.50, 1.335), (1.70, 1.312), (1.88, 1.292), (1.975, 1.272), (2.00, 1.24), (1.99, 1.195),
            (1.955, 1.155), (1.93, 1.11), (1.958, 1.088), (1.962, 1.03), (1.935, 0.97), (1.86, 0.90), (1.76, 0.84), (1.62, 0.80)]
    p2 = poly2d(G.D[:, 0, :], G.Z[:, 0, :], prof)[:, None, :]
    f = mx(p2 - 0.004, np.abs(G.Y) - 0.885)
    hood = rbox(G, (1.93, 0.40, 1.30), (0.085, 0.195, 0.06), 0.045)
    f = smin(f, hood, 0.03)
    f = mx(f, -rbox(G, (2.015, 0.40, 1.245), (0.075, 0.168, 0.068), 0.02))           # the cluster sits in the hood
    stack = rbox(G, (1.985, 0.0, 1.07), (0.07, 0.165, 0.19), 0.03)
    f = smin(f, stack, 0.025)
    shroud = capsule(G, (1.90, 0.40, 1.07), (2.10, 0.40, 1.13), 0.052)
    f = smin(f, shroud, 0.02)
    for s in (1, -1):
        f = mx(f, -rbox(G, (2.045, s * 0.095, 1.18), (0.05, 0.068, 0.027), 0.008))     # centre vents
        f = mx(f, -rbox(G, (1.995, s * 0.80, 1.18), (0.05, 0.055, 0.03), 0.01))        # side vents
    outer = rbox(G, (1.94, -0.48, 0.975), (0.06, 0.22, 0.072), 0.02); inner_ = rbox(G, (1.94, -0.48, 0.975), (0.07, 0.214, 0.066), 0.016)
    f = mx(f, -mx(outer, -inner_))                                                  # the glovebox seam
    f = groove(f, G.Z - 1.092, 0.004, 0.003, mask=(np.abs(G.Y) > 0.17))              # a stitched line above the wood
    def assign(c, n):
        d, y, z = c
        if z > 1.205 or (z > 1.13 and 0.20 < y < 0.60): return 'int_dark'
        if abs(y) < 0.17 and 1.035 < z < 1.13 and n[0] > 0.4: return 'int_piano'
        if 1.035 < z < 1.088 and abs(y) > 0.17 and not (0.20 < y < 0.60) and n[0] > 0.2: return 'int_wood'
        return 'int_leather'
    cuts = [ZP(1.035), ZP(1.088), ZP(1.13), ZP(1.205), YP(0.17), YP(-0.17), YP(0.20), YP(0.60)]
    return sdf_object('dash', G, f, ['int_dark', 'int_leather', 'int_wood', 'int_piano'], assign, 4000, cuts=cuts)

def dash_details():
    P = []
    # vent slats
    for s in (1, -1):
        for k in range(4): P.append(rounded(f'vslat{s}{k}', (2.03, s * 0.095, 1.163 + k * 0.011), (0.03, 0.064, 0.0016), 0, 'int_alu'))
        for k in range(4): P.append(rounded(f'sslat{s}{k}', (1.98, s * 0.80, 1.162 + k * 0.012), (0.03, 0.05, 0.0016), 0, 'int_alu'))
        P.append(rounded(f'vframe{s}', (2.046, s * 0.095, 1.18), (0.004, 0.07, 0.029), 0.003, 'int_alu'))
    P.append(rounded('hazard', (2.05, 0, 1.18), (0.006, 0.012, 0.010), 0.003, 'int_piano'))
    for s in (1, -1):        # the dash corners under the A pillars: no daylight between the dash end, the pillar and the door
        P.append(rounded(f'cowl{s}', (1.56, s * 0.79, 1.33), (0.13, 0.095, 0.06), 0.025, 'int_dark'))
    P.append(rounded('hazard_mark', (2.056, 0, 1.18), (0.001, 0.006, 0.005), 0.0, 'int_alu'))
    # climate: two knobs and a row of keys on the piano-black panel
    for s in (1, -1):
        P.append(cylinder(f'knob{s}', (2.055, s * 0.11, 1.075), (2.075, s * 0.11, 1.075), 0.021, 'int_alu', verts=24))
    for k in range(6):
        P.append(rounded(f'key{k}', (2.057, -0.075 + k * 0.03, 1.052), (0.004, 0.012, 0.007), 0.002, 'int_alu'))
    P.append(quad_uv('climate_disp', [(2.058, 0.07, 1.085), (2.058, -0.07, 1.085), (2.058, -0.07, 1.115), (2.058, 0.07, 1.115)],
                     [(0.40, 0.08), (0.62, 0.08), (0.62, 0.12), (0.40, 0.12)], 'int_screen'))
    # the centre screen on top of the dash, leaning back, and its stand
    P.append(rounded('screen_box', (1.875, 0, 1.40), (0.014, 0.172, 0.088), 0.008, 'int_piano', rot=(0, 0.18, 0)))
    P.append(rounded('screen_stand', (1.86, 0, 1.33), (0.03, 0.07, 0.03), 0.01, 'int_piano'))
    ca, sa = math.cos(0.18), math.sin(0.18)
    def on_screen(u, v):   # u across (left +), v up, on the face towards the cabin
        return (1.875 + 0.0145 * ca + v * sa, u, 1.40 - 0.0145 * sa + v * ca)
    P.append(quad_uv('screen', [on_screen(0.162, -0.08), on_screen(-0.162, -0.08), on_screen(-0.162, 0.08), on_screen(0.162, 0.08)],
                     [(0, 0.5), (1, 0.5), (1, 1), (0, 1)], 'int_screen'))
    # the cluster in its hood, leaning back a little
    cl = []
    tc, ts = math.cos(0.12), math.sin(0.12)
    def on_cluster(u, v): return (1.948 + v * ts, 0.40 + u, 1.25 + v * tc)
    P.append(quad_uv('cluster', [on_cluster(0.16, -0.06), on_cluster(-0.16, -0.06), on_cluster(-0.16, 0.06), on_cluster(0.16, 0.06)],
                     [(0, 0.125), (1, 0.125), (1, 0.5), (0, 0.5)], 'int_screen'))
    # start button, a small column stalk each side
    P.append(cylinder('start', (1.99, 0.62, 1.12), (2.0, 0.62, 1.12), 0.014, 'int_alu', verts=20))
    for s in (1, -1): P.append(cylinder(f'stalk{s}', (2.06, 0.40 + s * 0.05, 1.12), (2.10, 0.40 + s * 0.13, 1.115), 0.007, 'int_piano', verts=10))
    needles = []
    for name, uc in (('needle_rpm', 0.16 - 190 / 1024 * 0.32), ('needle_speed', 0.16 - 834 / 1024 * 0.32)):
        needles.append(needle(name, on_cluster(uc, 0.0), tc, ts))
    return P, needles

def needle(name, centre, tc, ts):
    """A needle on the cluster. Its local X is the dial's normal, towards the driver; local Z is the dial's up. Turning it
    about X by a negative angle moves it clockwise as the driver sees it. At rest it points at the 0 mark (lower left):
    a full sweep to the top mark is -270 degrees."""
    K = C['K']
    nrm = Vector((-tc, 0, -ts)).normalized()            # (d, y, z) = (tc, 0, -ts) in the car frame, mirrored in d
    up = Vector((-ts, 0, tc)).normalized(); side = up.cross(nrm)
    L = 0.047 * K; w = 0.0022 * K
    rot = Matrix.Rotation(math.radians(135), 3, 'X')
    V = [tuple(rot @ Vector(v)) for v in ((0.002 * K, -w, -0.008 * K), (0.002 * K, w, -0.008 * K), (0.002 * K, 0.0, L))]
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], [[0, 1, 2]]); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    m = Matrix((nrm, side, up)).transposed().to_4x4(); m.translation = R(centre); ob.matrix_world = m
    mat = bpy.data.materials.get('int_needle') or make_mat('int_needle', None, rough=0.4, color=(1.0, 0.25, 0.1))
    mat.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (1.0, 0.3, 0.1, 1)
    mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 2.0
    ob.data.materials.append(mat)
    return ob

def console():
    G = Grid((1.95, -0.18, 0.55), (3.08, 0.18, 1.10), 0.007)
    f = rbox(G, (2.55, 0, 0.74), (0.50, 0.125, 0.20), 0.035)
    f = smin(f, rbox(G, (2.84, 0, 0.99), (0.17, 0.13, 0.046), 0.04), 0.02)
    for s in (1, -1): f = mx(f, -cyl_z(G, (2.47, s * 0.052), 0.037, 0.87, 1.2))
    f = mx(f, -rbox(G, (2.27, 0.02, 0.95), (0.055, 0.04, 0.03), 0.012))
    f = groove(f, G.Y, 0.004, 0.003, mask=(G.D > 2.68))                              # the split armrest lid
    def assign(c, n):
        d, y, z = c
        if z > 0.95 and d > 2.66: return 'int_leather'
        if n[2] > 0.6 and 2.10 < d < 2.64 and z > 0.92: return 'int_wood'
        return 'int_dark'
    ob = sdf_object('console', G, f, ['int_leather', 'int_wood', 'int_dark'], assign, 1500, cuts=[DP(2.10), DP(2.64), DP(2.66), ZP(0.92), ZP(0.95)])
    # the shifter as in the reference: a stitched dark leather boot, a dark leather knob with a satin silver cap
    boot = cylinder('boot', (2.27, 0.02, 0.93), (2.275, 0.02, 1.02), 0.034, 'int_dark', verts=16)
    lever = cylinder('lever', (2.275, 0.02, 1.01), (2.285, 0.02, 1.07), 0.012, 'int_dark', verts=10)
    knob = rounded('knob', (2.29, 0.02, 1.095), (0.032, 0.026, 0.038), 0.022, 'int_dark', rot=(0, -0.12, 0))
    knob_t = rounded('knob_top', (2.293, 0.02, 1.131), (0.026, 0.021, 0.005), 0.004, 'int_alu')
    ring = cylinder('cup_ring', (2.47, 0.052, 0.935), (2.47, 0.052, 0.94), 0.039, 'int_alu', verts=20, caps=False)
    ring2 = cylinder('cup_ring2', (2.47, -0.052, 0.935), (2.47, -0.052, 0.94), 0.039, 'int_alu', verts=20, caps=False)
    return [ob, boot, lever, knob, knob_t, ring, ring2]

def seat(name, y0, d0, hip, recline, width=0.25, bench=False):
    """One seat (or the whole bench when bench). d0 = cushion centre, hip = (d, z) where cushion and back meet."""
    span = (abs(y0) + width + 0.06) if bench else width + 0.06
    yc = 0.0 if bench else y0
    G = Grid((d0 - 0.36, yc - span, 0.52), (hip[0] + 0.42, yc + span, 1.86), 0.0075)
    sa, ca = math.sin(recline), math.cos(recline)
    cush_w = span - 0.06
    f = rbox(G, (d0, yc, 0.81), (0.25, cush_w, 0.065), 0.05, rot=0.10)
    bc = (hip[0] + sa * 0.36, hip[1] + ca * 0.36)
    back = rbox(G, (bc[0], yc, bc[1]), (0.07, cush_w - 0.01, 0.34), 0.06, rot=recline)
    f = smin(f, back, 0.03)
    places = [0.47, 0.0, -0.47] if bench else [y0]
    for yp in places:
        outer = bench and abs(yp) > 0.1
        if not bench or outer:
            edges = [yp + 0.215, yp - 0.215] if not bench else [yp + np.sign(yp) * 0.215]
            for e in edges:
                f = smin(f, rbox(G, (d0, e, 0.825), (0.24, 0.055, 0.08), 0.045, rot=0.10), 0.02)
                fwd = (bc[0] - ca * 0.035, bc[1] + sa * 0.035)
                f = smin(f, rbox(G, (fwd[0], e, fwd[1]), (0.085, 0.055, 0.30), 0.05, rot=recline), 0.02)
        # seams round the insert, and two across it
        ld, ly, lz = local(G, (bc[0], yp, bc[1]), recline)
        insert = np.abs(G.Y - yp) < 0.16
        for e in (yp + 0.16, yp - 0.16): f = groove(f, G.Y - e, 0.006, 0.0035)
        f = groove(f, lz - 0.05, 0.004, 0.003, mask=insert * (ld < 0))
        f = groove(f, lz + 0.14, 0.004, 0.003, mask=insert * (ld < 0))
        f = groove(f, G.D - (d0 - 0.06), 0.004, 0.003, mask=insert * (G.Z > 0.80))
        # headrest on two posts
        hr = (hip[0] + sa * 0.86, hip[1] + ca * 0.86)
        f = mn(f, rbox(G, (hr[0], yp, hr[1]), (0.055, 0.135 if not bench or outer else 0.12, 0.095), 0.05, rot=recline * 0.5))
    if bench: f = groove(f, G.Y + 0.24, 0.006, 0.004)                                  # the 60/40 split
    # the base and its side trim
    f = mn(f, rbox(G, (d0, yc, 0.665), (0.21, cush_w - 0.03, 0.075), 0.02))
    def assign(c, n):
        d, y, z = c
        if z < 0.735: return 'int_plastic'
        near = min(places, key=lambda p: abs(y - p))
        if abs(y - near) < 0.155:
            hr_z = hip[1] + ca * 0.70
            if z < hr_z and ((z < 0.93 and n[2] > 0.55) or (z > 0.93 and n[0] < -0.45)): return 'int_perf'
        return 'int_leather'
    cuts = [ZP(0.735), ZP(0.93), ZP(hip[1] + ca * 0.70)] + [YP(p + e) for p in places for e in (-0.155, 0.155)]
    ob = sdf_object(name, G, f, ['int_leather', 'int_perf', 'int_plastic'], assign, 3600 if bench else 2000, cuts=cuts)
    posts = []
    for yp in places:
        hr = (hip[0] + sa * 0.86, hip[1] + ca * 0.86)
        for e in (-0.06, 0.06):
            top = (hr[0] - 0.01, yp + e, hr[1] - 0.06); bot = (hip[0] + sa * 0.68, yp + e, hip[1] + ca * 0.68)
            posts.append(cylinder(f'{name}_post{yp}{e}', bot, top, 0.0055, 'int_chrome', verts=8, caps=False))
    side = [] if bench else [rounded(f'{name}_sw', (d0 + 0.02, y0 + np.sign(y0) * (width + 0.01), 0.69), (0.07, 0.006, 0.018), 0.004, 'int_piano')]
    return [ob] + posts + side

def steering_wheel(centre, tilt):
    """The wheel in its own frame: a = along the column (towards the dash), u = across (left +), v = up."""
    h = 0.0032
    ax = [np.arange(-0.06, 0.06 + h, h), np.arange(-0.215, 0.215 + h, h), np.arange(-0.215, 0.215 + h, h)]
    A, U, Vv = np.meshgrid(*[a.astype(np.float32) for a in ax], indexing='ij')
    rho = np.hypot(U, Vv)
    rim = np.sqrt((rho - 0.188) ** 2 + (A * 1.05) ** 2) - 0.0168
    def rb(c, half, r):
        q = [np.abs(A - c[0]) - half[0] + r, np.abs(U - c[1]) - half[1] + r, np.abs(Vv - c[2]) - half[2] + r]
        return np.sqrt(sum(np.maximum(x, 0) ** 2 for x in q)) + np.minimum(mx(*q), 0) - r
    def cap(a, b, r):
        a = np.array(a); b = np.array(b); ab = b - a
        t = np.clip(((A - a[0]) * ab[0] + (U - a[1]) * ab[1] + (Vv - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
        return np.sqrt((A - a[0] - t * ab[0]) ** 2 + (U - a[1] - t * ab[1]) ** 2 + (Vv - a[2] - t * ab[2]) ** 2) - r
    hub = rb((-0.016, 0, -0.008), (0.026, 0.076, 0.060), 0.014)
    spokes = mn(rb((0.0, 0.125, -0.02), (0.012, 0.068, 0.032), 0.012), rb((0.0, -0.125, -0.02), (0.012, 0.068, 0.032), 0.012),
                cap((0.004, 0.028, -0.06), (0.004, 0.058, -0.182), 0.012), cap((0.004, -0.028, -0.06), (0.004, -0.058, -0.182), 0.012))
    keys = mn(rb((-0.013, 0.118, -0.016), (0.004, 0.036, 0.021), 0.004), rb((-0.013, -0.118, -0.016), (0.004, 0.036, 0.021), 0.004))
    f = mn(smin(rim, spokes, 0.012), smin(hub, spokes, 0.01), keys)
    f[0], f[-1], f[:, 0], f[:, -1], f[:, :, 0], f[:, :, -1] = 1, 1, 1, 1, 1, 1
    v, faces, _, _ = measure.marching_cubes(f, 0.0, spacing=(h, h, h)); v += np.array([ax[0][0], ax[1][0], ax[2][0]])
    K = C['K']; v *= K
    me = bpy.data.meshes.new('steering'); me.from_pydata(v.tolist(), [], faces.tolist()); me.update()
    ob = bpy.data.objects.new('steering', me); bpy.context.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    activate(ob)
    mo = ob.modifiers.new('sm', 'SMOOTH'); mo.iterations = 2; mo.factor = 0.5; bpy.ops.object.modifier_apply(modifier='sm')
    mo = ob.modifiers.new('dec', 'DECIMATE'); mo.ratio = 2000 / len(me.polygons); bpy.ops.object.modifier_apply(modifier='dec')
    idx = use(ob, ['int_dark', 'int_wood', 'int_alu', 'int_piano'])
    for p in me.polygons:
        a, u, w = p.center / K; r_ = math.hypot(u, w); ang = math.degrees(math.atan2(w, u)) % 360
        if r_ > 0.165:
            p.material_index = idx['int_wood'] if (55 < ang < 125 or 235 < ang < 305) else idx['int_dark']
        elif a < -0.0125 and abs(abs(u) - 0.118) < 0.04 and abs(w + 0.016) < 0.025: p.material_index = idx['int_piano']
        elif w < -0.06 and r_ > 0.07: p.material_index = idx['int_alu']
        else: p.material_index = idx['int_dark']
        p.use_smooth = True
    tri_uv(ob)
    ob.location = R(centre); ob.rotation_euler = (0, -tilt, 0)
    return ob

def overhead():
    P = []
    # rear-view mirror under the roof at the top of the windscreen
    P.append(rounded('mirror', (1.99, 0, 1.665), (0.022, 0.125, 0.034), 0.016, 'int_plastic', rot=(0, -0.1, 0)))
    P.append(rounded('mirror_glass', (2.012, 0, 1.665), (0.002, 0.115, 0.027), 0.01, 'int_chrome', rot=(0, -0.1, 0)))
    P.append(cylinder('mirror_stalk', (1.99, 0, 1.70), (1.985, 0, 1.79), 0.008, 'int_plastic', verts=8))
    P.append(rounded('overhead', (2.07, 0, 1.79), (0.10, 0.12, 0.03), 0.02, 'int_fabric'))
    for s in (1, -1): P.append(rounded(f'dome{s}', (2.10, s * 0.06, 1.762), (0.035, 0.03, 0.004), 0.003, 'int_alu'))
    for s in (1, -1):
        P.append(rounded(f'visor{s}', (2.03, s * 0.40, 1.775), (0.085, 0.20, 0.012), 0.010, 'int_fabric', rot=(0, 0.25, 0)))
    for d0, s in ((2.15, -1), (3.20, 1), (3.20, -1)):                                  # grab handles (none over the driver)
        P.append(rounded(f'grab{d0}{s}', (d0, s * 0.635, 1.675), (0.10, 0.012, 0.012), 0.010, 'int_plastic'))
        for e in (-0.09, 0.09): P.append(rounded(f'grabf{d0}{s}{e}', (d0 + e, s * 0.648, 1.69), (0.012, 0.012, 0.022), 0.008, 'int_plastic'))
    for s in (1, -1):                                                                      # B-pillar trims and the belts
        P.append(rounded(f'bpil{s}', (2.755, s * 0.765, 1.40), (0.055, 0.018, 0.40), 0.015, 'int_fabric', rot=(s * 0.27, 0, 0)))
        P.append(strip(f'belt{s}', [(2.78, s * 0.70, 1.58), (2.82, s * 0.64, 1.40), (2.80, s * 0.58, 1.14), (2.82, s * 0.62, 0.90)], 0.046, 'int_belt', normal_hint=(1, 0, 0)))
        P.append(rounded(f'buckle{s}', (2.84, s * 0.15, 0.93), (0.025, 0.012, 0.035), 0.008, 'int_piano'))
    return P

def wipers(body, tailgate):
    """Front wipers parked at the foot of the windscreen (joined to the body), and the rear wiper on the rear glass
    (joined to the tailgate, so it lifts with it). The glass is plain now, so the photo's painted wipers are gone."""
    ws = -math.atan(0.88)                     # the windscreen leans back about 41 degrees: the blades lie on it
    nd, nz = -math.sin(-ws), math.cos(-ws)    # its outward normal in (d, z)
    front = []
    for yc, half in ((0.31, 0.29), (-0.27, 0.27)):
        d, z = 1.46 + nd * 0.012, 1.423 + nz * 0.012
        front.append(rounded(f'blade{yc}', (d, yc, z), (0.009, half, 0.007), 0.004, 'int_plastic', rot=(0, ws, 0)))
        front.append(rounded(f'arm{yc}', (d + nd * 0.01 - 0.012, yc - 0.03, z + nz * 0.01), (0.006, half * 0.8, 0.005), 0.003, 'int_plastic', rot=(0, ws, 0)))
    ob = join(front, 'wipers'); activate(body); ob.select_set(True); bpy.ops.object.join()
    # the rear wiper: pivot low on the centre of the rear glass, parked up and to the left
    rear = [rounded('rblade', (4.655, 0.16, 1.56), (0.008, 0.20, 0.007), 0.004, 'int_plastic', rot=(0.95, 0.42, 0)),
            rounded('rarm', (4.67, 0.10, 1.50), (0.007, 0.15, 0.006), 0.003, 'int_plastic', rot=(0.95, 0.42, 0)),
            cylinder('rpivot', (4.70, 0.0, 1.40), (4.73, 0.0, 1.40), 0.018, 'int_plastic', verts=12)]
    ob = join(rear, 'rear_wiper'); activate(tailgate); ob.select_set(True); bpy.ops.object.join()

def door_details(door, d0, d1, side, front):
    """Armrest, pull, handle, speaker and switches, parented to the door so they swing with it."""
    P = []
    yin = side * 0.86
    L = d1 - d0
    P.append(rounded(f'{door.name}_arm', (d0 + L * 0.55, side * 0.83, 0.93), (L * 0.33, 0.045, 0.035), 0.028, 'int_leather'))
    P.append(rounded(f'{door.name}_pull', (d0 + L * 0.42, side * 0.835, 1.00), (0.07, 0.02, 0.025), 0.014, 'int_dark', rot=(0, 0.4, 0)))
    P.append(rounded(f'{door.name}_handle', (d0 + 0.17, side * 0.875, 1.10), (0.045, 0.012, 0.012), 0.010, 'int_chrome'))
    P.append(rounded(f'{door.name}_hcup', (d0 + 0.17, side * 0.885, 1.10), (0.06, 0.008, 0.025), 0.01, 'int_plastic'))
    rs = 0.075 if front else 0.06
    P.append(cylinder(f'{door.name}_spk', (d0 + 0.22, side * 0.885, 0.64), (d0 + 0.22, side * 0.878, 0.64), rs, 'int_plastic', verts=28))
    P.append(cylinder(f'{door.name}_spkr', (d0 + 0.22, side * 0.884, 0.64), (d0 + 0.22, side * 0.876, 0.64), rs + 0.006, 'int_alu', verts=28, caps=False))
    if front:
        P.append(rounded(f'{door.name}_sw', (d0 + L * 0.50, side * 0.80, 0.968), (0.09, 0.03, 0.006), 0.004, 'int_piano'))
        for k in range(4 if side > 0 else 1):
            P.append(rounded(f'{door.name}_k{k}', (d0 + L * 0.45 + k * 0.035, side * 0.80, 0.975), (0.012, 0.012, 0.004), 0.003, 'int_alu'))
        P.append(rounded(f'{door.name}_tw', (d0 + 0.06, side * 0.86, 1.18), (0.04, 0.03, 0.05), 0.02, 'int_piano'))   # tweeter corner
    # joined into the door itself: it swings with it, and its materials share the door lining's draws
    ob = join(P, f'{door.name}_trim')
    activate(door); ob.select_set(True); bpy.ops.object.join()
    return door

# ------------------------------------------------------------------ build
def build(XF, K, belt, bplane, body, doors, door_spans, tailgate, tex_dir):
    C.update(XF=XF, K=K, belt=belt); C['M'] = materials(tex_dir)
    belt_r = lambda d: bplane(d * K) / K                      # the belt as the same plane the hull was cut on
    def belt_cut(off):
        p0 = Vector((1.5, 0, belt_r(1.5) + off)); p1 = Vector((4.3, 0, belt_r(4.3) + off))
        t = p1 - p0; return (p0[:], (-t.z, 0, t.x))
    # inner skins of the shell, the doors and the tailgate
    def body_keep(c, f):
        d, y, z = c
        if f.material_index != 0: return False
        return 1.38 < d < 4.90 and (z > 0.50 and f.normal.z > -0.5 or z > 1.55)
    def body_mat(c, f):
        d, y, z = c
        if d > 4.40 and z < 1.72: return 'int_plastic'                 # the cargo pillars: dark trim, so tailgate seams stay dark
        if z > belt_r(d) - 0.02: return 'int_fabric'
        return 'int_carpet' if d > 3.80 else 'int_plastic'
    inner_skin(body, body_keep, body_mat, offset=0.05, ratio=0.10, cuts=[belt_cut(-0.02), DP(3.80)])
    for name, ob in doors.items():
        d0, d1 = door_spans[name][:2]
        # the photo door card (door_card) covers the lining below the belt: one dark material is enough (fewer draws)
        inner_skin(ob, lambda c, f: f.material_index == 0, lambda c, f: 'int_plastic', offset=0.032, ratio=0.18)
    inner_skin(tailgate, lambda c, f: f.material_index == 0, lambda c, f: 'int_plastic', offset=0.03)
    parts = []
    parts += floor()
    import suv_interior_photo as SP
    dash = dashboard(); SP.map_regions(dash, 'dash_front.png', 'dash_photo', SP.DASH_REGIONS[:1] + SP.DASH_REGIONS[2:], tex_dir); parts.append(dash)
    det, needles = dash_details(); parts += det
    cons = console(); SP.map_regions(cons[0], 'dash_front.png', 'dash_photo', SP.DASH_REGIONS[1:2], tex_dir); parts += cons
    parts.append(SP.front_seat('seat_FL', 0.40, tex_dir))
    parts.append(SP.front_seat('seat_FR', -0.40, tex_dir))
    bench = seat('bench', 0.0, 3.38, (3.62, 0.90), 0.42, width=0.70, bench=True)
    SP.map_regions(bench[0], 'rear_bench.png', 'bench_photo', SP.BENCH_REGIONS, tex_dir); parts += bench
    parts += overhead()
    trims = [SP.door_card(ob, door_spans[n][0] + 0.03, door_spans[n][1] - 0.03, door_spans[n][2], belt_r((door_spans[n][0] + door_spans[n][1]) / 2), tex_dir) for n, ob in doors.items()]
    for s in (1, -1):        # scuff plates on the sills: they also close the slit between the floor and the doors
        for d0, d1 in ((1.62, 2.70), (2.82, 3.66)):
            parts.append(rounded(f'scuff{s}{d0}', ((d0 + d1) / 2, s * 0.84, 0.585), ((d1 - d0) / 2, 0.055, 0.03), 0.012, 'int_plastic'))
            parts.append(rounded(f'scuffm{s}{d0}', ((d0 + d1) / 2, s * 0.84, 0.616), ((d1 - d0) / 2 - 0.03, 0.03, 0.002), 0.0, 'int_alu'))
    cabin = join(parts, 'interior')
    wipers(body, tailgate)
    wheel = SP.steering_wheel((2.20, 0.40, 1.13), 0.45, tex_dir)
    # where the eyes are (the first-person camera) and where they look
    eye = bpy.data.objects.new('eye', None); eye.location = R((2.86, 0.40, 1.585)); bpy.context.collection.objects.link(eye)
    look = bpy.data.objects.new('eye_look', None); look.location = R((-3.0, 0.38, 1.30)); bpy.context.collection.objects.link(look)
    tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in [cabin, wheel] + trims + needles)
    print('cabin triangles', tri)
    return cabin, wheel, trims, needles, eye, look

"""Step 2: the greenhouse. The window outline (measured on the side, front and rear photos, as in suv_complete.py) is
cut into the shell as planes; the glass is lifted out as its own panes, set 8 mm in, with a black lip back to the
opening; the B and C pillars are gloss black; a black surround frames each opening; chrome strips run along the
foot and the head of the side windows."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector

XF = 2.498; K = 1.034
def interp(t, d): ds, vs = zip(*t); return float(np.interp(d, ds, vs))
TOP = [(0.0, 1.13), (0.40, 1.215), (1.00, 1.245), (1.46, 1.26), (2.00, 1.27), (3.50, 1.285), (4.40, 1.30), (4.90, 1.30)]
belt = lambda d: interp(TOP, d) * K
def bplane(d): return belt(1.5) + (d - 1.5) / 2.9 * (belt(4.4) - belt(1.5))
ZTOP, ZDOOR = 1.79 * K, 1.835 * K
ZWS0, ZWS1 = 1.405 * K, 1.81 * K
ZRG0, ZRG1, RG_HALF = 1.34 * K, 1.81 * K, 0.64 * K
def ws_half(z): return interp([(1.30, 0.67), (1.60, 0.65), (1.81, 0.58)], z / K) * K
def line_plane(p0, p1):
    p0, p1 = Vector(p0), Vector(p1); return p0, (p1 - p0).cross(Vector((0, 1, 0))).normalized()
A_CO, A_NO = line_plane((XF - 1.55, 0, 1.27 * K), (XF - 2.39, 0, 1.86 * K))
Q_CO, Q_NO = line_plane((XF - 4.20, 0, bplane(4.20)), (XF - 4.42, 0, bplane(4.42) + 0.22 * K))
def plane_sign(co, no, ref):
    sg = 1 if (Vector(ref) - co).dot(no) > 0 else -1
    return lambda p: (Vector(p) - co).dot(no) * sg
behind_A = plane_sign(A_CO, A_NO, (XF - 2.6, 0, 1.6 * K))
above_Q = plane_sign(Q_CO, Q_NO, (XF - 4.0, 0, 1.6 * K))
B_PILLAR, C_PILLAR = (2.70, 2.80), (3.66, 3.74)

def cut_outline(bm):
    def geom_of(fs): return fs + list({e for f in fs for e in f.edges}) + list({v for f in fs for v in f.verts})
    def faces(test): return [f for f in bm.faces if test(f.calc_center_median(), XF - f.calc_center_median().x)]
    def bis(g, co, no):
        bmesh.ops.bisect_plane(bm, geom=g, plane_co=co, plane_no=no, dist=1e-6)
    side = lambda lo, hi: geom_of(faces(lambda c, d: abs(c.y) > 0.45 and c.z > 1.0 * K and lo < d < hi))
    bl0 = Vector((XF - 1.5, 0, bplane(1.5))); bl1 = Vector((XF - 4.4, 0, bplane(4.4)))
    bis(side(1.3, 4.6), bl0, (bl1 - bl0).cross(Vector((0, 1, 0))).normalized())
    for zc in (ZTOP, ZDOOR): bis(side(1.4, 4.75), (0, 0, zc), (0, 0, 1))
    bis(side(1.3, 2.8), A_CO, A_NO)
    for dc in (*B_PILLAR, *C_PILLAR, 4.42, 1.565, 2.735, 2.775, 3.715): bis(side(dc - 0.6, dc + 0.6), (XF - dc, 0, 0), (1, 0, 0))
    bis(side(3.9, 4.75), Q_CO, Q_NO)
    ws = lambda: geom_of(faces(lambda c, d: d < 2.6 and c.z > 1.2 * K))
    for zc in (ZWS0, ZWS1): bis(ws(), (0, 0, zc), (0, 0, 1))
    for s in (1, -1):
        p0 = Vector((0, s * ws_half(ZWS0), ZWS0)); p1 = Vector((0, s * ws_half(ZWS1), ZWS1))
        bis(ws(), p0, (p1 - p0).cross(Vector((1, 0, 0))).normalized())
    rg = lambda: geom_of(faces(lambda c, d: d > 4.4 and c.z > 1.1 * K))
    for zc in (ZRG0, ZRG1): bis(rg(), (0, 0, zc), (0, 0, 1))
    for s in (1, -1): bis(rg(), (0, s * RG_HALF, 0), (0, 1, 0))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])

def kind(c, n):
    d = XF - c.x; ay = abs(c.y); E = 1e-4
    if 1.47 < d < 2.5 and n.x > -0.2 and ZWS0 + E < c.z < ZWS1 - E and ay < ws_half(c.z) - E: return 'glass'
    if d > 4.5 and n.x < 0.2 and ZRG0 + E < c.z < ZRG1 - E and ay < RG_HALF - E: return 'glass'
    if ws_half(c.z) + 0.03 < ay < 0.95 and 1.4 < d < 4.5 and bplane(d) + E < c.z < ZTOP - E and behind_A(c) > E and d < 4.42 - E and above_Q(c) > E:
        if B_PILLAR[0] - E <= d <= B_PILLAR[1] + E or C_PILLAR[0] - E <= d <= C_PILLAR[1] + E: return 'pillar'
        return 'glass'
    return None

def build(shell, glass_mat, black_gloss, trim, chrome):
    me = shell.data
    for m in (glass_mat, black_gloss, trim): me.materials.append(m)
    gi, pi, ti = len(me.materials) - 3, len(me.materials) - 2, len(me.materials) - 1
    bm = bmesh.new(); bm.from_mesh(me); cut_outline(bm)
    glass_faces = []
    for f in bm.faces:
        k = kind(f.calc_center_median(), f.normal)
        if k == 'glass': f.material_index = gi; glass_faces.append(f)
        elif k == 'pillar': f.material_index = pi
    # a black surround: shell faces within 3 cm of a glass edge
    gverts = {v for f in glass_faces for v in f.verts}
    edge_v = [v for v in gverts if any(f.material_index != gi for f in v.link_faces)]
    from mathutils.kdtree import KDTree
    kd = KDTree(len(edge_v))
    for i, v in enumerate(edge_v): kd.insert(v.co, i)
    kd.balance()
    for f in bm.faces:
        if f.material_index == 0 and edge_v:
            co, i, dist = kd.find(f.calc_center_median())
            if dist < 0.03: f.material_index = ti
    bm.to_mesh(me); bm.free()
    # lift the glass out into its own object and set it 8 mm in, with a lip back to the opening
    for o in bpy.context.selected_objects: o.select_set(False)
    shell.select_set(True); bpy.context.view_layer.objects.active = shell
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons: p.select = p.material_index == gi
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    glass = [o for o in bpy.context.selected_objects if o is not shell][0]; glass.name = 'glass'
    bm = bmesh.new(); bm.from_mesh(glass.data); bm.normal_update()
    edges = [e for e in bm.edges if e.is_boundary]
    ret = bmesh.ops.extrude_edge_only(bm, edges=edges)
    lip_verts = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
    lip_faces = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
    # move the original pane in; the extruded copies stay at the opening, so the lip spans the 8 mm
    lipset = set(lip_verts)
    for v in bm.verts:
        if v not in lipset: v.co -= v.normal * 0.008
    for f in lip_faces: f.material_index = glass.data.materials.find(trim.name) if trim.name in glass.data.materials else 0
    bm.to_mesh(glass.data); bm.free()
    if trim.name not in glass.data.materials: glass.data.materials.append(trim)
    ti_g = glass.data.materials.find(trim.name)
    for p in glass.data.polygons:
        if len(p.vertices) == 4 and p.area < 0.002 and p.index >= 0: pass
    # chrome strips along the foot and the head of the side windows
    strips = []
    for s in (1, -1):
        for nm, zf, d0, d1 in (('low', lambda d: bplane(d) - 0.004, 1.62, 4.20), ('top', lambda d: ZTOP + 0.012, 2.40, 4.45)):
            V, F = [], []
            ds = np.linspace(d0, d1, 60)
            for d in ds:
                z = zf(d)
                hit = shell.ray_cast(Vector((XF - d, s * 1.5, z)), Vector((0, -s, 0)))
                y = hit[1].y + s * 0.004 if hit[0] else s * 0.94
                V += [(XF - d, y, z - 0.006), (XF - d, y + s * 0.006, z), (XF - d, y, z + 0.006)]
            # a closed three-sided bar, wound to look outward on the right side and turned over for the left
            for i in range(len(ds) - 1):
                a = 3 * i; F += [[a, a + 1, a + 4, a + 3], [a + 1, a + 2, a + 5, a + 4], [a + 2, a, a + 3, a + 5]]
            n = 3 * (len(ds) - 1); F += [[0, 2, 1], [n, n + 1, n + 2]]
            if s > 0: F = [f[::-1] for f in F]
            name = f"window_chrome_{nm}_{'L' if s > 0 else 'R'}"
            mesh = bpy.data.meshes.new(name); mesh.from_pydata(V, [], F); mesh.update()
            o = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(o); mesh.materials.append(chrome)
            for p in mesh.polygons: p.use_smooth = True
            mesh.set_sharp_from_angle(angle=math.radians(40))
            strips.append(o)
    return glass, strips

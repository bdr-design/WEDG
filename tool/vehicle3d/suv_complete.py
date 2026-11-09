"""Complete the owner's photo-built black SUV (assets_src/vehicles/suv.glb) so it can be driven from inside:
see-through glass that keeps the photo's reflections, real rims (cut from the side photo) on separate spinning
wheels, doors and a tailgate cut from the body on hinges, wheel-well liners, and a cabin.

Frame (as imported): x forward (front bumper at max x), y to the left, z up, ground at z = 0. The model is at the
reference photo's scale (1.99 m tall).
Run: blendenv/bin/python suv_complete.py <out_dir> [render]
"""
import bpy, bmesh, sys, os, math, json, numpy as np
from mathutils import Vector

RENDER = sys.argv[-1] in ('render', 'quick', 'ext'); QUICK = sys.argv[-1] == 'quick'; EXT = sys.argv[-1] == 'ext'
OUT = sys.argv[-2] if RENDER else sys.argv[-1]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
def first(*paths): return next((p for p in paths if os.path.exists(p)), paths[-1])
# the hull rebuilt as a smooth distance field (build_vehicle.py HULL=sdf, then bake_vehicle.py)
SRC = os.environ.get('SUV_SRC') or first(os.path.join(HERE, '..', '..', 'assets_src', 'vehicles', 'suv.glb'), os.path.join(HERE, '..', 'vehicles', 'suv2', 'suv2.glb'))
PARTS = first(os.path.join(HERE, 'suv_parts'), HERE)          # hubs.json and the rim photo

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
suv = [o for o in bpy.data.objects if o.type == 'MESH'][0]
suv.rotation_mode = 'XYZ'                       # the glTF importer leaves quaternions; the hinges turn by Euler angles
bpy.ops.object.select_all(action='DESELECT'); suv.select_set(True); bpy.context.view_layer.objects.active = suv
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# the importer's custom normals do not survive the cuts below (they leave bright seams along every cut): drop them,
# and shade by angle at the end instead
try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
except Exception as e: print('custom normals', e)
P = np.array([v.co[:] for v in suv.data.vertices])
XF = float(P[:, 0].max()); XR = float(P[:, 0].min()); L = XF - XR
print('suv', L, P[:, 1].min(), P[:, 1].max(), P[:, 2].max())
d2x = lambda d: XF - d
K = float(P[:, 2].max()) / 1.925                     # heights of this model against the real car

hubs = json.load(open(os.path.join(PARTS, 'hubs.json')))
# tyres: 265/55R20 as on the LC300 VX/ZX (Toyota spec sheets), 0.80 m across; the 20-inch rim face shows to about 0.265 m.
# The AI reference photo drew them larger (0.86 m): the real size is used, scaled to this model (K).
R_TYRE, R_RIM, W_TYRE, TRACK = 0.40 * K, 0.265 * K, 0.265 * K, 1.665
AXLES = [(d2x(hubs['front'][0]), R_TYRE), (d2x(hubs['rear'][0]), R_TYRE)]

sys.path.insert(0, HERE)
import suv_exterior
albedo_img, albedo_px = suv_exterior.paint_setup(suv)       # deep gloss black, vertex colours gone
paint = suv.data.materials[0]
def mat(name, color, metal=0.0, rough=0.5, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
    return m
M = {'trim': mat('trim', (0.02, 0.02, 0.021), 0, 0.6), 'rubber': mat('rubber', (0.03, 0.03, 0.03), 0, 0.9),
     'barrel': mat('barrel', (0.12, 0.12, 0.13), 0.8, 0.4), 'leather': mat('leather', (0.55, 0.40, 0.26), 0, 0.5)}
# glass: the same photo, partly transparent, so the reflections stay and the cabin shows through
# glass: dark, smooth and partly clear, seen from outside only (from inside the faces are culled, so the view is clear).
# The LC300 has privacy glass behind the B pillar; the windscreen and the front door glass are lighter.
def glass_mat(name, alpha):
    m = mat(name, (0.012, 0.014, 0.017), 0, 0.03, alpha=alpha)
    m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.5
    m.use_backface_culling = True; return m
glass_m = glass_mat('suv_glass', 0.50)          # the windscreen and front doors
glass_rear_m = glass_mat('suv_glass_rear', 0.78)
suv.data.materials.append(glass_m)
# the rim photo
rim_img = bpy.data.images.load(os.path.join(PARTS, 'rim_rear.png')); rim_img.pack()
rim_m = bpy.data.materials.new('rim_photo'); rim_m.use_nodes = True
nt = rim_m.node_tree; tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = rim_img
nt.links.new(tx.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
nt.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.6; nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.35

# the window line, measured on the same reference photo (distance from the front -> height, real metres)
def interp(t, d): ds, vs = zip(*t); return float(np.interp(d, ds, vs))
TOP = [(0.0, 1.13), (0.40, 1.215), (1.00, 1.245), (1.46, 1.26), (2.00, 1.27), (3.50, 1.285), (4.40, 1.30), (4.90, 1.30)]
ROOF = [(1.46, 1.335), (1.62, 1.47), (1.86, 1.66), (2.10, 1.80), (2.30, 1.855), (2.60, 1.875), (3.6, 1.880), (4.55, 1.875), (4.76, 1.865), (4.84, 1.80), (4.95, 1.31)]
belt = lambda d: interp(TOP, d) * K
roof = lambda d: interp(ROOF, d) * K
def a_pillar_d(z): return 1.46 + (z / K - 1.27) / (1.86 - 1.27) * (2.30 - 1.46)
# window outline in model units
ZTOP, ZDOOR = 1.79 * K, 1.835 * K            # top edge of the side glass; top edge of the doors (the roof rail is above)
ZWS0, ZWS1 = 1.405 * K, 1.81 * K             # windscreen: the cowl (the bonnet rises to 1.40 m just ahead of it) and the header
ZRG0, ZRG1, RG_HALF = 1.34 * K, 1.81 * K, 0.64 * K   # rear glass
def bplane(d): return belt(1.5) + (d - 1.5) / 2.9 * (belt(4.4) - belt(1.5))     # the belt as one plane (it is cut as one)
def line_plane(p0, p1):
    p0, p1 = Vector(p0), Vector(p1); return p0, (p1 - p0).cross(Vector((0, 1, 0))).normalized()
A_CO, A_NO = line_plane((XF - 1.55, 0, 1.27 * K), (XF - 2.39, 0, 1.86 * K))          # the A pillar's rear edge
Q_CO, Q_NO = line_plane((XF - 4.20, 0, bplane(4.20)), (XF - 4.42, 0, bplane(4.42) + 0.22 * K))   # the quarter glass's upswept corner
def plane_sign(co, no, ref):
    sg = 1 if (Vector(ref) - co).dot(no) > 0 else -1
    return lambda p: (Vector(p) - co).dot(no) * sg
behind_A = plane_sign(A_CO, A_NO, (XF - 2.6, 0, 1.6 * K))     # > 0 where the side glass may be
above_Q = plane_sign(Q_CO, Q_NO, (XF - 4.0, 0, 1.6 * K))
def ws_half(z): return interp([(1.30, 0.67), (1.60, 0.65), (1.81, 0.58)], z / K) * K

# ------------------------------------------------------------------ 0. the hull's flat sides are a few huge triangles:
# cut them on the door seams, the belt and the sills (straight cuts), and refine them round the wheel circles
bm = bmesh.new(); bm.from_mesh(suv.data)
def side_geom(lo, hi, zlo=0.0, zhi=9.0, ymin=0.45):
    fs = [f for f in bm.faces if ymin < abs(f.calc_center_median().y) and zlo < f.calc_center_median().z < zhi and lo < XF - f.calc_center_median().x < hi]
    es = list({e for f in fs for e in f.edges}); vs = list({v for f in fs for v in f.verts})
    return fs + es + vs
def bisect(geom, co, no):
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for dcut in (1.565, 2.735, 2.775, 3.715):
    bisect(side_geom(dcut - 1.5, dcut + 1.5, 0.30, 2.2), (d2x(dcut), 0, 0), (1, 0, 0))
bisect(side_geom(1.3, 4.0, 0.30, 0.80), (0, 0, 0.48), (0, 0, 1))                     # the sill under the doors
bl0, bl1 = (d2x(1.5), 0, belt(1.5)), (d2x(4.4), 0, belt(4.4))                          # the belt line
nb = Vector((bl1[0] - bl0[0], 0, bl1[2] - bl0[2])).cross(Vector((0, 1, 0))).normalized()
bisect(side_geom(1.3, 4.6, 0.9, 1.6), bl0, nb)
def rear_geom():
    fs = [f for f in bm.faces if XF - f.calc_center_median().x > 4.6 and f.normal.x < -0.2]
    return fs + list({e for f in fs for e in f.edges}) + list({v for f in fs for v in f.verts})
bisect(rear_geom(), (0, 0, 0.70), (0, 0, 1))                                             # the tailgate's lower edge
for s in (1, -1): bisect(rear_geom(), (0, s * 0.90, 0), (0, 1, 0))                       # and its sides
# the window outline: every edge of the glass is a plane, cut into the hull before the faces are sorted,
# so the glass, the doors and the cabin trim all get straight, clean edges
def geom_of(fs): return fs + list({e for f in fs for e in f.edges}) + list({v for f in fs for v in f.verts})
def faces_where(test): return [f for f in bm.faces if test(f.calc_center_median(), f.normal, XF - f.calc_center_median().x)]
side_up = lambda lo, hi: geom_of(faces_where(lambda c, n, d: abs(c.y) > 0.45 and c.z > 1.0 * K and lo < d < hi))
bisect(side_up(1.4, 4.75), (0, 0, ZTOP), (0, 0, 1))
bisect(side_up(1.4, 4.75), (0, 0, ZDOOR), (0, 0, 1))
bisect(side_up(1.3, 2.8), A_CO, A_NO)
for dcut in (2.70, 2.80, 3.66, 3.74, 4.42): bisect(side_up(dcut - 0.6, dcut + 0.6), (d2x(dcut), 0, 0), (1, 0, 0))
bisect(side_up(3.9, 4.75), Q_CO, Q_NO)
ws = lambda: geom_of(faces_where(lambda c, n, d: d < 2.6 and c.z > 1.2 * K))
for zc in (ZWS0, ZWS1): bisect(ws(), (0, 0, zc), (0, 0, 1))
for s in (1, -1):
    p0 = Vector((0, s * ws_half(ZWS0), ZWS0)); p1 = Vector((0, s * ws_half(ZWS1), ZWS1))
    bisect(ws(), p0, (p1 - p0).cross(Vector((1, 0, 0))).normalized())
rg = lambda: geom_of(faces_where(lambda c, n, d: d > 4.4 and c.z > 1.1 * K))
for zc in (ZRG0, ZRG1): bisect(rg(), (0, 0, zc), (0, 0, 1))
for s in (1, -1): bisect(rg(), (0, s * RG_HALF, 0), (0, 1, 0))
print('faces after the seam cuts', len(bm.faces))
bm.to_mesh(suv.data); bm.free()
# ------------------------------------------------------------------ 1. the wheel wells: a boolean cut by a cylinder on
# each wheel, from the side inwards; the cut walls become the black well liner and the photo's own wheels go away
RCUT = R_TYRE + 0.025
wells = []
for xa, za in AXLES:
    for s in (1, -1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=RCUT, depth=0.75, location=(xa, s * (0.57 + 0.375), za), rotation=(math.pi / 2, 0, 0))
        wells.append(bpy.context.active_object)
bpy.ops.object.select_all(action='DESELECT')
for w_ in wells: w_.select_set(True)
bpy.context.view_layer.objects.active = wells[0]; bpy.ops.object.join(); cutter = bpy.context.active_object
cutter.data.materials.append(M['trim'])
bm = bmesh.new(); bm.from_mesh(suv.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(suv.data); bm.free()
mod = suv.modifiers.new('wells', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cutter
try: mod.solver = 'EXACT'; mod.use_hole_tolerant = True
except Exception as e: print('solver', e)
bpy.ops.object.select_all(action='DESELECT'); suv.select_set(True); bpy.context.view_layer.objects.active = suv
bpy.ops.object.modifier_apply(modifier='wells')
bpy.data.objects.remove(cutter)
print('faces after the wells', len(suv.data.polygons), 'materials', [m.name for m in suv.data.materials])

# ------------------------------------------------------------------ 2. glass faces
glass_idx = suv.data.materials.find('suv_glass')
E = 1e-4
for p in suv.data.polygons:
    if p.material_index != 0: continue
    c = p.center; n = p.normal; d = XF - c.x; ay = abs(c.y)
    g = False
    if 1.47 < d < 2.5 and n.x > -0.2 and ZWS0 + E < c.z < ZWS1 - E and ay < ws_half(c.z) - E: g = True                     # windscreen
    elif d > 4.5 and n.x < 0.2 and ZRG0 + E < c.z < ZRG1 - E and ay < RG_HALF - E: g = True                       # rear glass
    elif ws_half(c.z) + 0.03 < ay < 0.95 and 1.4 < d < 4.5 and bplane(d) + E < c.z < ZTOP - E and behind_A(c) > E and d < 4.42 - E \
            and not (2.70 - E <= d <= 2.80 + E or 3.66 - E <= d <= 3.74 + E) and above_Q(c) > E: g = True        # side glass
    if g: p.material_index = glass_idx

def split_by_material(o, idx, name):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT')
    o.active_material_index = idx; bpy.ops.object.material_slot_select(); bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    new = [x for x in bpy.context.selected_objects if x is not o][0]; new.name = name; return new
glass = split_by_material(suv, glass_idx, 'glass')
suv.name = 'body'

# ------------------------------------------------------------------ 3. doors and the tailgate
def carve(src, test, name):
    bpy.ops.object.select_all(action='DESELECT'); src.select_set(True); bpy.context.view_layer.objects.active = src
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    me = src.data; n = 0
    for p in me.polygons:
        corners = [me.vertices[v].co for v in p.vertices]
        p.select = bool(test(p.center, p.normal) and all(test(q, None) for q in corners)); n += p.select
    if not n: return None
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    new = [x for x in bpy.context.selected_objects if x is not src][0]; new.name = name; return new
DOORS = {'door_FL': (1.565, 2.735, 1), 'door_RL': (2.775, 3.715, 1), 'door_FR': (1.565, 2.735, -1), 'door_RR': (2.775, 3.715, -1)}
def door_test(d0, d1, side):
    def t(c, n):
        d = XF - c.x
        if n is None: return d0 - 0.10 < d < d1 + 0.005 and c.y * side > 0.45 and 0.46 < c.z < ZDOOR + 0.002
        if not (d0 < d < d1) or c.y * side < 0.45 or c.z < 0.50: return False
        if c.z > bplane(d) and d0 < 2 and behind_A(c) < 0: return False   # the A pillar stays with the body
        return c.z < ZDOOR
    return t
doors = {}
for name, (d0, d1, side) in DOORS.items():
    pieces = [p for p in (carve(o, door_test(d0, d1, side), name + o.name) for o in (suv, glass)) if p]
    bpy.ops.object.select_all(action='DESELECT')
    for p in pieces: p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join(); dobj = bpy.context.active_object; dobj.name = name
    bpy.context.scene.cursor.location = Vector((d2x(d0) - 0.02, side * 0.98, 0.9)); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    doors[name] = dobj
def tail_test(c, n):
    d = XF - c.x
    if n is None: return d > 4.70 and c.z > 0.66 and abs(c.y) < 0.95
    return d > 4.80 and c.z > 0.70 and abs(c.y) < 0.90 and n.x < -0.3
pieces = [p for p in (carve(o, tail_test, 'tail' + o.name) for o in (suv, glass)) if p]
bpy.ops.object.select_all(action='DESELECT')
for p in pieces: p.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join(); tailgate = bpy.context.active_object; tailgate.name = 'tailgate'
bpy.context.scene.cursor.location = Vector((d2x(4.80), 0, roof(4.80))); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.context.scene.cursor.location = (0, 0, 0)

# ------------------------------------------------------------------ 4. the new wheels
TYRE_M = suv_exterior.tyre_material(suv_exterior.tyre_maps(os.path.join(OUT, 'tex')))
def wheel(name, x, z, side):
    tyre = suv_exterior.tyre_mesh(name + '_tyre', R_RIM, R_TYRE, W_TYRE, TYRE_M)
    # the rim face: a slightly dished disc carrying the photo of the real rim
    n = 40; V = [(0, W_TYRE / 2 - 0.01, 0)]; F = []
    for k in range(n):
        ang = 2 * math.pi * k / n; V.append((R_RIM * math.cos(ang), W_TYRE / 2 - 0.025, R_RIM * math.sin(ang)))
    for k in range(n): F.append([0, 1 + k, 1 + (k + 1) % n])
    me = bpy.data.meshes.new(name + '_rim'); me.from_pydata(V, [], F); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            vx, _, vz = V[vi]; uv.data[li].uv = (0.5 + 0.5 * vx / R_RIM, 0.5 + 0.5 * vz / R_RIM)
    rim = bpy.data.objects.new(name + '_rim', me); bpy.context.collection.objects.link(rim); me.materials.append(rim_m)
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=R_RIM, depth=W_TYRE - 0.04, end_fill_type='NOTHING', location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    barrel = bpy.context.active_object; barrel.data.materials.append(M['barrel'])
    bpy.ops.object.select_all(action='DESELECT')
    for o in (tyre, rim, barrel): o.select_set(True)
    bpy.context.view_layer.objects.active = tyre; bpy.ops.object.join(); w = bpy.context.active_object; w.name = name
    if side < 0: w.scale.y = -1; bpy.ops.object.transform_apply(scale=True)
    w.location = (x, side * TRACK / 2, z)
    return w
wheels = [wheel('wheel_FL', AXLES[0][0], AXLES[0][1], 1), wheel('wheel_FR', AXLES[0][0], AXLES[0][1], -1),
          wheel('wheel_RL', AXLES[1][0], AXLES[1][1], 1), wheel('wheel_RR', AXLES[1][0], AXLES[1][1], -1)]

# ------------------------------------------------------------------ the cuts left many small flat triangles: merge the flat ones back
def planar(o, ang=math.radians(0.8)):
    bm = bmesh.new(); bm.from_mesh(o.data); n0 = len(bm.faces)
    bmesh.ops.dissolve_limit(bm, angle_limit=ang, use_dissolve_boundaries=False, verts=bm.verts[:], edges=bm.edges[:], delimit={'UV', 'MATERIAL'})
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    print('planar', o.name, n0, '->', len(bm.faces)); bm.to_mesh(o.data); bm.free()

# ------------------------------------------------------------------ 5. the cabin
sys.path.insert(0, HERE)
import suv_interior
spans = {n: (d0 / K, d1 / K, side) for n, (d0, d1, side) in DOORS.items()}
cabin, steer, trims, needles, eye, look = suv_interior.build(XF, K, belt, bplane, suv, doors, spans, tailgate, f'{OUT}/tex')
for o in [suv, glass, tailgate] + list(doors.values()): planar(o)      # after the inner skins, so they are built on the fine cut hull
for o in [suv, glass, tailgate] + list(doors.values()):
    activate_ = bpy.context.view_layer.objects; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); activate_.active = o
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(75))     # only real hard edges (liners, rims) stay sharp
    # glass behind the B pillar is the darker privacy glass
    me_ = o.data
    if glass_m.name in me_.materials and glass_rear_m.name not in me_.materials: me_.materials.append(glass_rear_m)
    gi, gr = me_.materials.find(glass_m.name), me_.materials.find(glass_rear_m.name)
    for p_ in me_.polygons:
        if p_.material_index == gi and XF - (o.matrix_world @ p_.center).x > 2.755: p_.material_index = gr
LAMPS = suv_exterior.lamp_materials(paint, albedo_px, albedo_img)
for o in (suv, tailgate): suv_exterior.assign_lamps(o, LAMPS, XF, K)
tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print('parts', sorted(o.name for o in bpy.data.objects if o.type == 'MESH'), 'triangles', tri)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/suv_full.blend')

# ------------------------------------------------------------------ export
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if (o.type == 'MESH' and not (o.data.materials and o.data.materials[0].name == 'ground')) or o.name in ('eye', 'eye_look'): o.select_set(True)
bpy.ops.export_scene.gltf(filepath=f'{OUT}/suv_full.glb', export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=88)
print('glb', os.path.getsize(f'{OUT}/suv_full.glb'))

if RENDER:
    # the glass is only seen from outside: from inside it is clear
    for gm_ in (glass_m, glass_rear_m):
        nt = gm_.node_tree; bs = nt.nodes['Principled BSDF']; out_n = nt.nodes['Material Output']
        geo = nt.nodes.new('ShaderNodeNewGeometry'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(geo.outputs['Backfacing'], mix.inputs['Fac']); nt.links.new(bs.outputs['BSDF'], mix.inputs[1]); nt.links.new(tr.outputs['BSDF'], mix.inputs[2]); nt.links.new(mix.outputs['Shader'], out_n.inputs['Surface'])
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    sys.path.insert(0, first(os.path.join(HERE, '..', 'camel3d'), os.path.join(HERE, '..', 'camel'))); from blend_common import desert_world, ground
    sand = first(os.path.join(HERE, '..', 'assets_all', '01_terrain', 'najd.png'), os.path.join(HERE, '..', '..', 'design', 'prototype3d', 'sand.jpg'))
    desert_world(sun_elev=34, sun_rot=215); ground(sand if os.path.exists(sand) else None, size=120, tile_m=22)
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -5.3
    for m in LAMPS.values(): m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 40.0
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    def shot(path, loc, look, lens=50, res=(1200, 700)):
        sc.render.resolution_x, sc.render.resolution_y = res; cam.data.lens = lens
        cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    if not QUICK:
        shot(f'{OUT}/q34.png', (6.5, 5.0, 2.2), (0.3, 0, 0.9), lens=40)
        shot(f'{OUT}/rear34.png', (-6.0, 4.6, 2.0), (-0.3, 0, 0.9), lens=40)
    if not EXT: shot(f'{OUT}/driver.png', eye.location[:], look.location[:], lens=17, res=(1200, 800))
    if EXT:
        kk = max(XF - XR, 4.5)       # the same cameras as the hull's check renders, for a fair before/after
        shot(f'{OUT}/check_front34.png', (kk * 0.95, -kk * 0.85, kk * 0.42), (0, 0, 0.84), lens=42, res=(640, 420))
        shot(f'{OUT}/check_rear34.png', (-kk * 0.95, kk * 0.8, kk * 0.5), (0, 0, 0.84), lens=42, res=(640, 420))
        shot(f'{OUT}/front.png', (d2x(-6.0), 1.2, 1.4), (d2x(1.0), 0, 0.95), lens=45)
        shot(f'{OUT}/wheel.png', (AXLES[0][0] + 0.9, 2.2, 0.75), (AXLES[0][0], 0.83, 0.45), lens=40)
        shot(f'{OUT}/rear_lamps.png', (d2x(7.0), -2.5, 1.5), (d2x(4.8), 0, 1.05), lens=45)
        sys.exit(0)
    if QUICK: sys.exit(0)
    shot(f'{OUT}/driver_wide.png', (eye.location.x + 0.25, eye.location.y - 0.05, eye.location.z + 0.08), (d2x(1.9), -0.1, 1.15), lens=13, res=(1200, 800))
    doors['door_FL'].rotation_euler.z = -1.05; doors['door_RL'].rotation_euler.z = -1.0; tailgate.rotation_euler.y = -1.2
    shot(f'{OUT}/open.png', (1.5, 7.5, 2.6), (-0.4, 0, 1.0), lens=32)
    shot(f'{OUT}/open_in.png', (d2x(2.3), 2.6, 1.55), (d2x(2.6), 0, 1.0), lens=22)
    shot(f'{OUT}/cargo.png', (d2x(5.9), 0.0, 1.75), (d2x(3.6), 0, 1.0), lens=24)
    for o in doors.values(): o.rotation_euler = (0, 0, 0)
    tailgate.rotation_euler = (0, 0, 0)
    # a cut-away from above: the roof and glass hidden, to see the layout
    body = bpy.data.objects['body']; body.hide_render = True; glass.hide_render = True
    for o in doors.values(): o.hide_render = True
    shot(f'{OUT}/plan.png', (d2x(2.9), 0, 6.0), (d2x(2.9), 0, 0.0), lens=28, res=(800, 1100))
    shot(f'{OUT}/cut_side.png', (d2x(2.9), 5.5, 1.3), (d2x(2.9), 0, 1.1), lens=30, res=(1400, 700))

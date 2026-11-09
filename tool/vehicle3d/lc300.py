"""A full-size Saudi luxury SUV in the shape of the Land Cruiser 300, built entirely by code, with no badges or text.

Sources:
- Dimensions from Toyota's spec sheets: length 4985 mm, width 1980, height 1925, wheelbase 2850, track 1665,
  front overhang 935, approach angle 32 degrees, tyres 265/65R18 (0.80 m).
- The side profile is measured from the owner's orthographic reference photo, scaled to the real height.

Frame: x forward (the front bumper at +2.49), y to the left, z up, the ground at z = 0. Exported to glTF it becomes
x forward, y up, z to the right, which the game uses as is.
Parts are separate objects so the game can move them: four doors (hinged at the front), the tailgate (hinged at the
top), four wheels (spin, the front ones steer), the steering wheel, and emissive lights.
Run: blendenv/bin/python lc300.py <out_dir> [render]
"""
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix

OUT = sys.argv[-2] if sys.argv[-1] == 'render' else sys.argv[-1]
RENDER = sys.argv[-1] == 'render'
os.makedirs(OUT, exist_ok=True)

L, XF = 4.985, 2.4925                     # length; x of the front bumper face
WB, TRACK, FOH = 2.85, 1.665, 0.935
XA_F = XF - FOH                           # front axle x
XA_R = XA_F - WB                          # rear axle x
R_TYRE, W_TYRE = 0.401, 0.265
HALF_W = 0.99
d2x = lambda d: XF - d                    # distance from the front -> x

bpy.ops.wm.read_factory_settings(use_empty=True)

# ------------------------------------------------------------------ materials (glTF-friendly)
def mat(name, color, metal=0.0, rough=0.5, alpha=1.0, emit=None, emit_s=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = emit_s
    if coat:
        try: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.05
        except KeyError: pass
    return m
M = {
    'paint': mat('paint', (0.010, 0.010, 0.011), 0.15, 0.30, coat=1.0),        # gloss black: the shine comes from the clear coat, not from metal
    'glass': mat('glass', (0.012, 0.014, 0.017), 0.0, 0.04, alpha=0.80),
    'glass_ws': mat('glass_ws', (0.02, 0.025, 0.03), 0.0, 0.03, alpha=0.30),
    'trim': mat('trim', (0.02, 0.02, 0.021), 0.0, 0.55),
    'chrome': mat('chrome', (0.8, 0.8, 0.82), 1.0, 0.12),
    'satin': mat('satin', (0.45, 0.46, 0.47), 0.9, 0.35),
    'rubber': mat('rubber', (0.025, 0.025, 0.025), 0.0, 0.88),
    'rim': mat('rim', (0.55, 0.56, 0.58), 1.0, 0.28),
    'headlight': mat('headlight', (0.85, 0.87, 0.9), 0.3, 0.1, emit=(1.0, 0.97, 0.9), emit_s=0.0),
    'drl': mat('drl', (0.9, 0.9, 0.92), 0.0, 0.2, emit=(1.0, 1.0, 1.0), emit_s=2.0),
    'taillight': mat('taillight', (0.35, 0.01, 0.012), 0.1, 0.15, emit=(1.0, 0.02, 0.02), emit_s=0.4),
    'leather': mat('leather', (0.55, 0.40, 0.26), 0.0, 0.5),
    'dash': mat('dash', (0.03, 0.028, 0.026), 0.0, 0.6),
    'wood': mat('wood', (0.16, 0.08, 0.04), 0.0, 0.3),
    'screen': mat('screen', (0.01, 0.015, 0.02), 0.0, 0.1, emit=(0.18, 0.32, 0.45), emit_s=0.6),
    'carpet': mat('carpet', (0.05, 0.045, 0.04), 0.0, 0.95),
    'headliner': mat('headliner', (0.62, 0.56, 0.47), 0.0, 0.9),
}

def obj(name, verts, faces, mats, mat_idx=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    for m_ in mats: me.materials.append(M[m_])
    if mat_idx is not None:
        for p, i in zip(me.polygons, mat_idx): p.material_index = i
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    return o

def smooth_by_angle(o, deg=38):
    mo = o.modifiers.new('sba', 'NODES') if False else None
    try:
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(deg))
    except Exception:
        pass

def interp(table, d):
    ds, vs = zip(*table); return float(np.interp(d, ds, vs))

# ------------------------------------------------------------------ the lower body: a loft of rounded sections
# (distance from the front, value) tables, from the reference profile scaled to the real 1.925 m height
# the shoulder / beltline at the side (the hood's centre stands higher, see CROWN), measured on the reference photo
TOP = [(0.00, 1.13), (0.03, 1.18), (0.12, 1.205), (0.40, 1.215), (1.00, 1.245), (1.46, 1.26), (2.00, 1.27), (3.50, 1.285),
       (4.40, 1.30), (4.64, 1.30), (4.90, 1.30), (4.97, 1.29), (4.985, 1.25)]
CROWN = [(0.0, 0.03), (0.10, 0.05), (0.40, 0.07), (1.30, 0.075), (1.46, 0.04), (1.60, 0.012), (4.985, 0.012)]
BOT = [(0.00, 0.47), (0.03, 0.46), (0.25, 0.40), (0.55, 0.38), (1.40, 0.42), (3.50, 0.42), (4.30, 0.40), (4.70, 0.42), (4.95, 0.47), (4.985, 0.60)]
HW = [(0.00, 0.95), (0.06, 0.975), (0.25, 0.99), (4.55, 0.99), (4.90, 0.975), (4.985, 0.95)]

def section(d, n=28):
    """Half of a rounded section at station d, from the bottom centre to the top centre (y >= 0)."""
    zt, zb, w = interp(TOP, d), interp(BOT, d), interp(HW, d)
    h = zt - zb
    rt, rb = min(0.12, h * 0.3), min(0.07, h * 0.2)
    pts = []
    # bottom flat, bottom corner, the side (a slight outward shoulder), top corner, top crown
    for i in range(4): pts.append((w - rb) * i / 3 * 0.999)
    pts = [(y, zb) for y in pts]
    for i in range(1, 6):
        a = -math.pi / 2 + math.pi / 2 * i / 5; pts.append((w - rb + rb * math.cos(a), zb + rb + rb * math.sin(a)))
    for i in range(1, 8):
        t = i / 8; z = zb + rb + (h - rb - rt) * t
        bulge = 0.018 * math.sin(math.pi * t) ** 2       # the shoulder line
        pts.append((w + bulge, z))
    for i in range(0, 7):
        a = math.pi / 2 * i / 6; pts.append((w - rt + rt * math.cos(a), zt - rt + rt * math.sin(a)))
    for i in range(1, 5):
        y = (w - rt) * (1 - i / 4); pts.append((y, zt + interp(CROWN, d) * (1 - (y / w) ** 2)))      # the hood rises to its centre
    return pts

def loft(stations, sec_fn, name, mats, cap_front=True, cap_back=True, mat_fn=None):
    rings = []
    for d in stations:
        half = sec_fn(d); full = [(y, z) for y, z in half] + [(-y, z) for y, z in reversed(half[1:-1])]
        rings.append([(d2x(d), y, z) for y, z in full])
    n = len(rings[0]); V = [p for r in rings for p in r]; F = []; MI = []
    for i in range(len(rings) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            F.append([a, b, b + n, a + n])
            if mat_fn:
                c = np.mean([V[a], V[b], V[b + n], V[a + n]], 0); MI.append(mat_fn(c))
    if cap_front: F.append(list(range(n))[::-1]); MI.append(0)
    if cap_back: F.append([(len(rings) - 1) * n + j for j in range(n)]); MI.append(0)
    return obj(name, V, F, mats, MI if mat_fn else None)

stations = sorted(set(list(np.linspace(0.0, 0.3, 7)) + list(np.linspace(0.3, 4.7, 45)) + list(np.linspace(4.7, 4.985, 7))))
body = loft(stations, section, 'body', ['paint', 'trim'], mat_fn=lambda c: 1 if c[2] < 0.47 else 0)

# open the top of the lower body under the greenhouse, so the cabin is open from the beltline up
bm = bmesh.new(); bm.from_mesh(body.data)
kill = []
for f in bm.faces:
    c = f.calc_center_median(); d = XF - c.x
    if 1.50 < d < 4.80 and c.z > interp(TOP, d) - 0.03 and abs(c.y) < 0.93: kill.append(f)
bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(body.data); bm.free()

# wheel arches: cut out cylinders at the axles, a little larger than the tyre
for xa in (XA_F, XA_R):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=R_TYRE + 0.065, depth=2.6, location=(xa, 0, R_TYRE + 0.02), rotation=(math.pi / 2, 0, 0))
    cut = bpy.context.active_object; cut.data.materials.append(M['trim'])
    mo = body.modifiers.new('arch', 'BOOLEAN'); mo.object = cut; mo.operation = 'DIFFERENCE'; mo.solver = 'EXACT'; mo.material_mode = 'TRANSFER'
    bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier='arch')
    bpy.data.objects.remove(cut)

# ------------------------------------------------------------------ the greenhouse: windscreen, side glass, roof, rear glass
ROOF = [(1.46, 1.335), (1.62, 1.47), (1.86, 1.66), (2.10, 1.80), (2.30, 1.855), (2.60, 1.875), (3.6, 1.880), (4.55, 1.875), (4.76, 1.865), (4.84, 1.80), (4.95, 1.31)]
GH = (1.46, 4.95)
def gh_section(d, n=10):
    zb = interp(TOP, d) - 0.005; zt = interp(ROOF, d)
    wb_, wt = 0.935 - 0.01 * max(0.0, d - 4.5) / 0.36, 0.70
    h = max(zt - zb, 0.02); r = min(0.09, h * 0.4)
    pts = [(0.0, zt + 0.015)]
    for i in range(1, 4): pts.append((wt * i / 4 * 0.97, zt + 0.015 * (1 - (i / 4) ** 2)))
    for i in range(0, 5):
        a = math.pi / 2 * (1 - i / 4); pts.append((wt + r * math.cos(a) - r * 0, zt - r + r * math.sin(a)))
    pts.append((wb_, zb))
    pts.append((0.0, zb)) if False else None
    return [(y, z) for y, z in pts][::-1] + []

def gh_ring(d):
    half = gh_section(d)                          # from the beltline up the side to the roof centre
    return half

# build as an open surface: the side and roof from beltline to beltline
gh_st = sorted(set(list(np.linspace(GH[0], 2.35, 16)) + list(np.linspace(2.35, 4.70, 24)) + list(np.linspace(4.70, GH[1], 8)) + [2.70, 2.80, 3.66, 3.74, 4.20, 4.30, 4.42, 4.76]))
rings = []
for d in gh_st:
    half = gh_ring(d)                             # beltline (y = wb) ... roof centre (y = 0)
    full = half + [(-y, z) for y, z in reversed(half[:-1])]
    rings.append([(d2x(d), y, z) for y, z in full])
n = len(rings[0]); V = [p for r in rings for p in r]; F = []; MI = []
WIN = {'A': (1.46, 2.30), 'B': (2.70, 2.80), 'C': (3.66, 3.74), 'D': (4.52, 4.72)}
def a_pillar_d(z):                       # where the A pillar is at height z (the windscreen's side edge)
    return 1.46 + (z - 1.27) / (1.86 - 1.27) * (2.30 - 1.46)
def gh_mat(c):
    d = XF - c[0]; ay = abs(c[1]); top = c[2] > interp(ROOF, d) - 0.035
    if top and 2.25 < d < 4.78: return 0                                # roof: paint
    if ay < 0.66 and d < 2.30: return 3                                 # windscreen
    if d > 4.78: return 1 if ay < 0.78 else 0                           # rear glass; the D pillars in body colour
    if ay < 0.55: return 0
    if d < a_pillar_d(c[2]) + 0.09: return 2                            # the A pillar strip
    if 2.70 <= d <= 2.80 or 3.66 <= d <= 3.74: return 2                 # black B and C pillars
    if d > 4.42: return 0                                               # body-colour D pillar
    if d > 4.20 and c[2] < interp(TOP, d) + (d - 4.20) / 0.22 * 0.22: return 0       # the glass corner sweeps up
    return 1
for i in range(len(rings) - 1):
    for j in range(n - 1):
        a, b = i * n + j, i * n + j + 1
        F.append([a, b, b + n, a + n]); MI.append(gh_mat(np.mean([V[a], V[b], V[b + n], V[a + n]], 0)))
greenhouse = obj('greenhouse', V, F, ['paint', 'glass', 'trim', 'glass_ws'], MI)
# glass becomes its own object (it is drawn after the opaque parts)
def split_material(o, idx, name):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
    o.active_material_index = idx; bpy.ops.object.material_slot_select(); bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    new = [x for x in bpy.context.selected_objects if x is not o][0]; new.name = name; return new
glass = split_material(greenhouse, 1, 'glass')
ws = split_material(greenhouse, 3, 'windscreen')
bpy.ops.object.select_all(action='DESELECT')
glass.select_set(True); ws.select_set(True); bpy.context.view_layer.objects.active = glass; bpy.ops.object.join(); glass = bpy.context.active_object; glass.name = 'glass'

# ------------------------------------------------------------------ front: the big grille with three heavy chrome bars, slim lamps, bumper
def box(name, size, loc, m, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=False, location=False)
    if bevel:
        mo = o.modifiers.new('bv', 'BEVEL'); mo.width = bevel; mo.segments = 2
        bpy.ops.object.modifier_apply(modifier='bv')
    o.data.materials.append(M[m]); return o
def quad_panel(name, pts, m, depth=0.0):
    """A flat panel from a polygon in the y-z plane at the front (x given per point)."""
    V = [tuple(p) for p in pts]; F = [list(range(len(V)))]
    return obj(name, V, F, [m], smooth=False)
parts = []
xg = XF + 0.006
# the grille opening: a trapezoid, wider at the bottom, dark inside
gw_top, gw_bot, gz0, gz1 = 0.60, 0.68, 0.74, 1.17
parts.append(quad_panel('grille_back', [(xg, -gw_bot, gz0), (xg, gw_bot, gz0), (xg, gw_top, gz1), (xg, -gw_top, gz1)][::-1], 'trim'))
# the frame and three thick bars, a little proud of the face
for i, z in enumerate((0.84, 0.96, 1.08)):
    w = gw_bot + (gw_top - gw_bot) * (z - gz0) / (gz1 - gz0)
    parts.append(box(f'grille_bar{i}', (0.06, 2 * w - 0.03, 0.046), (xg + 0.02, 0, z), 'chrome', bevel=0.012))
parts.append(box('grille_top', (0.06, 2 * gw_top + 0.06, 0.034), (xg + 0.018, 0, gz1 + 0.012), 'chrome', bevel=0.01))
for s_ in (1, -1):
    # the frame sides follow the trapezoid
    ang = math.atan2(gw_bot - gw_top, gz1 - gz0)
    parts.append(box(f'grille_side{s_}', (0.06, 0.034, gz1 - gz0 + 0.02), (xg + 0.018, s_ * (gw_top + gw_bot) / 2 + s_ * 0.015, (gz0 + gz1) / 2), 'chrome', rot=(s_ * ang, 0, 0), bevel=0.01))
    # headlamps: slim, at the top corners beside the grille, the DRL line underneath, angled round the corner
    hl = box(f'headlamp{s_}', (0.06, 0.40, 0.07), (XF - 0.01, s_ * 0.80, 1.155), 'trim', rot=(0, 0, s_ * -0.16), bevel=0.012); parts.append(hl)
    parts.append(box(f'lamp_bar{s_}', (0.05, 0.42, 0.022), (XF + 0.004, s_ * 0.80, 1.11), 'chrome', rot=(0, 0, s_ * -0.16), bevel=0.006))
    for z_, dz in ((gz0 - 0.005, 0), (gz1 + 0.01, 0)):
        parts.append(box(f'grille_c{s_}{z_:.2f}', (0.06, 0.08, 0.03), (xg + 0.018, s_ * ((gw_bot if z_ < 1 else gw_top) - 0.02), z_), 'chrome', bevel=0.008))
    for i in range(3):
        bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.022, depth=0.03, location=(XF + 0.02 - 0.018 * i, s_ * (0.67 + 0.095 * i), 1.162), rotation=(0, math.pi / 2, 0))
        lens = bpy.context.active_object; lens.data.materials.append(M['headlight']); parts.append(lens)
    parts.append(box(f'drl{s_}', (0.03, 0.38, 0.010), (XF + 0.022, s_ * 0.80, 1.19), 'drl', rot=(0, 0, s_ * -0.16)))
    parts.append(box(f'drl_v{s_}', (0.03, 0.012, 0.16), (XF - 0.03, s_ * 0.695, 0.99), 'drl'))
    # fog lamps: thin vertical slots low in the bumper corners
    parts.append(box(f'fog{s_}', (0.03, 0.03, 0.12), (XF - 0.012, s_ * 0.80, 0.66), 'headlight', bevel=0.006))
    parts.append(box(f'fog_trim{s_}', (0.035, 0.10, 0.16), (XF - 0.018, s_ * 0.80, 0.66), 'trim', bevel=0.01))
# bumper: body colour above, a wide black intake, a silver skid plate
parts.append(box('intake', (0.05, 1.14, 0.10), (XF - 0.012, 0, 0.62), 'trim', bevel=0.02))
parts.append(box('skid_front', (0.08, 1.20, 0.07), (XF - 0.04, 0, 0.50), 'satin', bevel=0.02))
parts.append(box('bumper_low', (0.20, 1.86, 0.10), (XF - 0.10, 0, 0.46), 'trim', bevel=0.03))

# ------------------------------------------------------------------ rear: long tail lamps joined by a chrome bar, the tailgate glass, bumper
xr = XF - L + 0.025
for s_ in (1, -1):
    parts.append(box(f'tail{s_}', (0.05, 0.42, 0.07), (xr - 0.012, s_ * 0.72, 1.18), 'taillight', bevel=0.012))
    parts.append(box(f'tail_side{s_}', (0.22, 0.05, 0.07), (xr + 0.09, s_ * 0.968, 1.18), 'taillight', bevel=0.012))
    parts.append(box(f'reflector{s_}', (0.04, 0.18, 0.025), (xr - 0.02, s_ * 0.72, 0.66), 'taillight'))
parts.append(box('plate_recess', (0.02, 0.56, 0.16), (xr - 0.002, 0, 0.98), 'trim', bevel=0.01))
parts.append(box('bumper_rear', (0.14, 1.88, 0.16), (xr + 0.03, 0, 0.60), 'trim', bevel=0.025))
parts.append(box('skid_rear', (0.06, 1.0, 0.05), (xr - 0.02, 0, 0.53), 'satin', bevel=0.015))
parts.append(box('third_brake', (0.04, 0.40, 0.03), (XF - 4.74, 0, 1.86), 'taillight'))
parts.append(box('wiper', (0.02, 0.36, 0.012), (XF - 4.84, 0.05, 1.47), 'trim'))

# ------------------------------------------------------------------ sides: lower cladding, running boards, mirrors, handles, rails
for s in (1, -1):
    parts.append(box(f'step{s}', (2.0, 0.17, 0.05), ((XA_F + XA_R) / 2, s * 0.92, 0.36), 'satin', bevel=0.012))
    parts.append(box(f'clad{s}', (2.2, 0.03, 0.10), ((XA_F + XA_R) / 2, s * 1.0, 0.47), 'trim', bevel=0.012))
    parts.append(box(f'mirror{s}', (0.12, 0.20, 0.13), (d2x(1.60), s * 1.07, 1.42), 'paint', bevel=0.03))
    parts.append(box(f'mirror_stalk{s}', (0.06, 0.12, 0.05), (d2x(1.62), s * 0.98, 1.38), 'trim'))
    parts.append(box(f'rail{s}', (2.0, 0.035, 0.032), (d2x(3.45), s * 0.60, 1.918), 'trim', bevel=0.01))
    for d in (2.5, 3.45, 4.4): parts.append(box(f'rail_foot{s}{d}', (0.10, 0.04, 0.05), (d2x(d), s * 0.60, 1.895), 'trim'))
    for d in (2.55, 3.55): parts.append(box(f'handle{s}{d}', (0.16, 0.02, 0.028), (d2x(d), s * 1.0, 1.17), 'chrome', bevel=0.006))
    # arch flares: a black lip round each wheel opening
    for xa in (XA_F, XA_R):
        bpy.ops.mesh.primitive_torus_add(major_radius=R_TYRE + 0.075, minor_radius=0.03, major_segments=40, minor_segments=6,
                                         location=(xa, s * 1.005, R_TYRE + 0.02), rotation=(math.pi / 2, 0, 0))
        t = bpy.context.active_object; t.name = f'flare{s}{xa:.1f}'
        bm = bmesh.new(); bm.from_mesh(t.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.1], context='VERTS')   # keep the upper half (local y up before rotation)
        bm.to_mesh(t.data); bm.free(); t.data.materials.append(M['trim']); parts.append(t)

def sweep(name, pts, r, m):
    """A thin square tube along a polyline (chrome strips, shut lines)."""
    V, F = [], []
    for i, p in enumerate(pts):
        p = Vector(p); t = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        u = t.cross(Vector((0, 0, 1))) if abs(t.z) < 0.9 else t.cross(Vector((1, 0, 0)))
        u.normalize(); v = t.cross(u)
        for a in range(4):
            ang = math.pi / 2 * a + math.pi / 4; V.append(tuple(p + (u * math.cos(ang) + v * math.sin(ang)) * r))
    for i in range(len(pts) - 1):
        for a in range(4): F.append([i * 4 + a, i * 4 + (a + 1) % 4, (i + 1) * 4 + (a + 1) % 4, (i + 1) * 4 + a])
    return obj(name, V, F, [m])
for s in (1, -1):
    yb = lambda d, off=0.0: s * (0.935 - 0.01 * max(0.0, d - 4.5) / 0.36 + off)
    parts.append(sweep(f'belt{s}', [(d2x(d), yb(d, 0.006), interp(TOP, d) + 0.004) for d in np.linspace(1.50, 4.60, 24)], 0.007, 'chrome'))
    parts.append(sweep(f'dlo{s}', [(d2x(d), s * 0.745, interp(ROOF, d) - 0.06) for d in np.linspace(2.05, 4.66, 24)], 0.006, 'chrome'))
    parts.append(sweep(f'lowstrip{s}', [(d2x(d), s * 1.0, 0.53) for d in np.linspace(1.62, 3.68, 8)], 0.006, 'chrome'))
    for d in (1.56, 2.74, 2.775, 3.72):
        top = interp(TOP, d) + (0.0 if d < 3.7 else 0.0)
        parts.append(sweep(f'shut{s}{d}', [(d2x(d), s * 1.002, 0.46), (d2x(d), s * 1.004, 0.9), (d2x(d), s * 0.995, top)], 0.0025, 'trim'))
    parts.append(sweep(f'shut_sill{s}', [(d2x(d), s * 0.995, 0.47) for d in np.linspace(1.56, 3.72, 6)], 0.0025, 'trim'))

for xa in (XA_F, XA_R):
    for s_ in (1, -1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=R_TYRE + 0.06, depth=0.34, end_fill_type='NOTHING', location=(xa, s_ * 0.82, R_TYRE + 0.02), rotation=(math.pi / 2, 0, 0))
        lin = bpy.context.active_object; lin.name = f'liner{s_}{xa:.1f}'
        bm = bmesh.new(); bm.from_mesh(lin.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.05], context='VERTS')     # the upper half (local y is up before the rotation)
        bm.to_mesh(lin.data); bm.free(); lin.data.materials.append(M['trim']); parts.append(lin)
        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=R_TYRE + 0.06, depth=0.01, location=(xa, s_ * 0.65, R_TYRE + 0.02), rotation=(math.pi / 2, 0, 0))
        cap = bpy.context.active_object; cap.data.materials.append(M['trim']); parts.append(cap)       # the inner wall

# ------------------------------------------------------------------ wheels: tyre, multi-spoke rim, a brake disc behind
def wheel(name, x, y, side):
    R_RIM = 0.229                                   # 18 inch rim
    # tyre: a revolved profile from the bead to the tread, with a rounded shoulder
    prof = []
    for i in range(11):
        t = i / 10; a = math.pi * t
        rr = R_RIM + (R_TYRE - R_RIM) * math.sin(a) ** 0.45; ww = (W_TYRE / 2) * math.cos(a) * (1.0 + 0.05 * math.sin(a))
        prof.append((rr, ww))
    segs = 28; V = []; F = []
    for k in range(segs):
        ang = 2 * math.pi * k / segs
        for rr, ww in prof: V.append((rr * math.cos(ang), ww, rr * math.sin(ang)))
    m = len(prof)
    for k in range(segs):
        for i in range(m - 1):
            a_, b_ = k * m + i, ((k + 1) % segs) * m + i
            F.append([a_, b_, b_ + 1, a_ + 1])
    tyre = obj(name + '_tyre', V, F, ['rubber'])
    V, F, MI = [], [], []
    def ring(r0, r1, y0, y1, n, mi):
        base = len(V)
        for k in range(n):
            ang = 2 * math.pi * k / n
            V.extend([(r0 * math.cos(ang), y0, r0 * math.sin(ang)), (r1 * math.cos(ang), y1, r1 * math.sin(ang))])
        for k in range(n):
            a_, b_ = base + 2 * k, base + 2 * ((k + 1) % n); F.append([a_, b_, b_ + 1, a_ + 1]); MI.append(mi)
    ring(R_RIM - 0.004, R_RIM - 0.004, 0.125, 0.0, 36, 1)          # the barrel, dark inside
    ring(R_RIM - 0.024, R_RIM + 0.002, 0.125, 0.122, 36, 0)        # the polished lip
    ring(0.0, 0.066, 0.122, 0.118, 18, 0)                           # the hub
    nsp = 12
    for k in range(nsp):
        c = 2 * math.pi * k / nsp + (0.06 if k % 2 else -0.06)      # spokes in pairs
        base = len(V)
        for j, (rr, hw, yy) in enumerate([(0.064, 0.050, 0.119), (0.14, 0.060, 0.121), (R_RIM - 0.022, 0.075, 0.118)]):
            for e in (-1, 0, 1):
                ang = c + e * hw * (1.0 - 0.4 * (e == 0))
                lift = 0.006 if e == 0 else 0.0
                V.append((rr * math.cos(c + e * hw), yy + lift, rr * math.sin(c + e * hw)))
        for j in range(2):
            for e in range(2):
                a_ = base + j * 3 + e; F.append([a_, a_ + 1, a_ + 4, a_ + 3]); MI.append(0)
    rim = obj(name + '_rim', V, F, ['rim', 'trim'], MI)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.17, depth=0.025, location=(0, 0.045, 0), rotation=(math.pi / 2, 0, 0))
    disc = bpy.context.active_object; disc.name = name + '_disc'; disc.data.materials.append(M['satin'])
    nuts = []
    for i in range(6):
        ang = 2 * math.pi * i / 6
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.009, depth=0.02, location=(0.042 * math.cos(ang), 0.126, 0.042 * math.sin(ang)), rotation=(math.pi / 2, 0, 0))
        nut = bpy.context.active_object; nut.data.materials.append(M['chrome']); nuts.append(nut)
    for o in (tyre, rim, disc, *nuts): o.select_set(True)
    bpy.context.view_layer.objects.active = tyre; bpy.ops.object.join(); w = bpy.context.active_object; w.name = name
    if side < 0: w.scale.y = -1; bpy.ops.object.transform_apply(scale=True)
    w.location = (x, y, R_TYRE)
    for o in bpy.context.selected_objects: o.select_set(False)
    return w
wheels = [wheel('wheel_FL', XA_F, TRACK / 2, 1), wheel('wheel_FR', XA_F, -TRACK / 2, -1),
          wheel('wheel_RL', XA_R, TRACK / 2, 1), wheel('wheel_RR', XA_R, -TRACK / 2, -1)]

# join the small fixed parts into the body
for o in bpy.context.selected_objects: o.select_set(False)
for p in parts: p.select_set(True)
body.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
greenhouse.select_set(False)
smooth_by_angle(body); smooth_by_angle(greenhouse)
# ------------------------------------------------------------------ the cabin: dashboard, screens, wheel, seats, console, headliner, carpet
interior = []
def ibox(name, size, loc, m, rot=(0, 0, 0), bevel=0.0):
    o = box(name, size, loc, m, rot, bevel); interior.append(o); return o
FLOOR = 0.52
ibox('carpet', (3.3, 1.74, 0.02), (d2x(3.15), 0, FLOOR), 'carpet')
ibox('headliner', (2.55, 1.44, 0.015), (d2x(3.55), 0, 1.835), 'headliner')
# dashboard: a dark top, beige lower half, a wood strip, the binnacle and the centre screen
ibox('dash_top', (0.42, 1.70, 0.10), (d2x(1.66), 0, 1.15), 'dash', rot=(0, -0.18, 0), bevel=0.03)
ibox('dash_mid', (0.30, 1.72, 0.20), (d2x(1.78), 0, 1.00), 'leather', bevel=0.03)
ibox('dash_wood', (0.02, 1.62, 0.035), (d2x(1.93), 0, 1.06), 'wood', bevel=0.006)
ibox('dash_low', (0.25, 1.70, 0.25), (d2x(1.70), 0, 0.78), 'dash', bevel=0.03)
ibox('binnacle', (0.16, 0.42, 0.12), (d2x(1.80), 0.40, 1.19), 'dash', rot=(0, -0.25, 0), bevel=0.03)
ibox('cluster', (0.005, 0.34, 0.11), (d2x(1.875), 0.40, 1.17), 'screen', rot=(0, -0.25, 0))
ibox('screen_c', (0.012, 0.32, 0.18), (d2x(1.80), 0.0, 1.28), 'screen', rot=(0, -0.18, 0))
ibox('screen_frame', (0.02, 0.34, 0.20), (d2x(1.795), 0.0, 1.28), 'dash', rot=(0, -0.18, 0))
for y in (-0.62, -0.22, 0.22, 0.62): ibox(f'vent{y}', (0.01, 0.16, 0.05), (d2x(1.935), y, 1.12), 'satin', bevel=0.005)
# centre console with the gear selector and an armrest
ibox('console', (1.10, 0.27, 0.26), (d2x(2.30), 0, FLOOR + 0.15), 'dash', bevel=0.03)
ibox('console_top', (0.95, 0.25, 0.03), (d2x(2.35), 0, FLOOR + 0.29), 'wood', bevel=0.008)
ibox('armrest', (0.34, 0.24, 0.07), (d2x(2.72), 0, FLOOR + 0.34), 'leather', bevel=0.03)
ibox('gear', (0.07, 0.05, 0.09), (d2x(2.12), 0.03, FLOOR + 0.36), 'leather', bevel=0.02)
# front seats: cushion, backrest leaning back, headrest, side bolsters
for y in (0.40, -0.40):
    ibox(f'seat_c{y}', (0.52, 0.52, 0.13), (d2x(2.58), y, 0.80), 'leather', rot=(0, -0.06, 0), bevel=0.045)
    for e in (-1, 1): ibox(f'seat_b{y}{e}', (0.48, 0.07, 0.08), (d2x(2.58), y + e * 0.24, 0.87), 'leather', bevel=0.03)
    ibox(f'seat_bk{y}', (0.13, 0.54, 0.72), (d2x(2.93), y, 1.20), 'leather', rot=(0, -0.35, 0), bevel=0.05)
    ibox(f'seat_hr{y}', (0.10, 0.28, 0.20), (d2x(3.06), y, 1.63), 'leather', rot=(0, -0.2, 0), bevel=0.04)
    ibox(f'seat_base{y}', (0.40, 0.40, 0.22), (d2x(2.58), y, FLOOR + 0.11), 'dash')
# second-row bench
ibox('bench_c', (0.55, 1.42, 0.13), (d2x(3.55), 0, 0.82), 'leather', rot=(0, -0.05, 0), bevel=0.045)
ibox('bench_bk', (0.14, 1.42, 0.68), (d2x(3.90), 0, 1.20), 'leather', rot=(0, -0.30, 0), bevel=0.05)
for y in (-0.48, 0, 0.48): ibox(f'bench_hr{y}', (0.10, 0.26, 0.17), (d2x(4.02), y, 1.60), 'leather', rot=(0, -0.2, 0), bevel=0.035)
ibox('bench_base', (0.45, 1.40, 0.25), (d2x(3.55), 0, FLOOR + 0.12), 'dash')
ibox('cargo', (0.80, 1.60, 0.03), (d2x(4.45), 0, 0.78), 'carpet')
# pillar trims inside
for y in (0.74, -0.74):
    ibox(f'bpillar_in{y}', (0.10, 0.03, 0.62), (d2x(2.75), y * 1.05, 1.52), 'headliner')
# the steering wheel turns: its own object, its origin at the centre of the rim
col_c = Vector((d2x(2.08), 0.40, 1.10))
bpy.ops.mesh.primitive_torus_add(major_radius=0.185, minor_radius=0.017, major_segments=36, minor_segments=8, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
rim_ = bpy.context.active_object; rim_.data.materials.append(M['leather']); bpy.ops.object.transform_apply(rotation=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.065, depth=0.05, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
hub_ = bpy.context.active_object; hub_.data.materials.append(M['dash']); bpy.ops.object.transform_apply(rotation=True)
sp = []
for ang in (math.pi / 2, -math.pi / 2, math.pi):
    b_ = box('spoke', (0.02, 0.15, 0.035), (0, 0.09 * math.cos(ang), 0.09 * math.sin(ang)), 'dash', rot=(ang, 0, 0)); sp.append(b_)
for o in bpy.context.selected_objects: o.select_set(False)
for o in [rim_, hub_] + sp: o.select_set(True)
bpy.context.view_layer.objects.active = rim_; bpy.ops.object.join(); steering = bpy.context.active_object; steering.name = 'steering'
steering.location = col_c; steering.rotation_euler = (0, -0.45, 0)            # tilted towards the driver
ibox('column', (0.30, 0.07, 0.07), (d2x(1.82), 0.40, 1.02), 'dash', rot=(0, -0.45, 0))
for o in bpy.context.selected_objects: o.select_set(False)
for o in interior: o.select_set(True)
bpy.context.view_layer.objects.active = interior[0]; bpy.ops.object.join(); cabin = bpy.context.active_object; cabin.name = 'interior'

# ------------------------------------------------------------------ doors and the tailgate as separate, hinged parts
def carve(src, test, name):
    """Move the faces of src whose centre passes test() into a new object."""
    bpy.ops.object.select_all(action='DESELECT'); src.select_set(True); bpy.context.view_layer.objects.active = src
    # clear every old selection first: stale vertex selections would drag other faces along
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    me = src.data; n = 0
    for p in me.polygons:
        c = src.matrix_world @ p.center
        corners = [src.matrix_world @ me.vertices[v].co for v in p.vertices]
        p.select = test(c) and all(test(q, corner=True) for q in corners); n += p.select
    if not n: return None
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    new = [x for x in bpy.context.selected_objects if x is not src][0]; new.name = name; return new
DOORS = {'door_FL': (1.565, 2.735, 1), 'door_RL': (2.775, 3.715, 1), 'door_FR': (1.565, 2.735, -1), 'door_RR': (2.775, 3.715, -1)}
def in_door(c, d0, d1, side, corner=False):
    d = XF - c.x
    if corner: return d0 - 0.12 < d < d1 + 0.005 and c.y * side > 0.5     # corners may reach forward to the mirror only
    if d0 < 2 and 1.50 < d < 1.75 and c.y * side > 0.98 and 1.30 < c.z < 1.52: return True      # the mirror rides on the front door
    if not (d0 < d < d1) or c.y * side < 0.55: return False
    if c.z < 0.50: return False                       # the sill cladding stays on the body
    if c.z < interp(TOP, d) + 0.02: return abs(c.y) > 0.80
    if abs(c.y) < 0.68 or c.z > interp(ROOF, d) - 0.03: return False      # the roof and the rails stay
    return d > 1.98 if d0 < 2 else True              # above the beltline: the window, behind the A pillar
door_objs = {}
for name, (d0, d1, side) in DOORS.items():
    pieces = [carve(o, lambda c, corner=False: in_door(c, d0, d1, side, corner), name + '_' + o.name) for o in (body, greenhouse, glass)]
    pieces = [p for p in pieces if p]
    for o in bpy.context.selected_objects: o.select_set(False)
    for p in pieces: p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join(); dobj = bpy.context.active_object; dobj.name = name
    # a leather door card on the inside
    card = box(name + '_card', (d1 - d0 - 0.08, 0.04, 0.50), (d2x((d0 + d1) / 2), side * 0.90, 0.92), 'leather', bevel=0.015)
    card.select_set(True); dobj.select_set(True); bpy.context.view_layer.objects.active = dobj; bpy.ops.object.join()
    # hinge at the front edge, on the outer skin
    hinge = Vector((d2x(d0) - 0.02, side * 0.98, 0.9))
    bpy.context.scene.cursor.location = hinge; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    door_objs[name] = dobj
def in_tailgate(c, corner=False):
    d = XF - c.x
    return d > 4.80 and c.z > 0.70 and abs(c.y) < 0.90
pieces = [p for p in (carve(o, in_tailgate, 'tailgate_' + o.name) for o in (body, greenhouse, glass)) if p]
for o in bpy.context.selected_objects: o.select_set(False)
for p in pieces: p.select_set(True)
bpy.context.view_layer.objects.active = pieces[0]; bpy.ops.object.join(); tailgate = bpy.context.active_object; tailgate.name = 'tailgate'
bpy.context.scene.cursor.location = Vector((d2x(4.80), 0, 1.86)); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.context.scene.cursor.location = (0, 0, 0)
tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print('parts', [o.name for o in bpy.data.objects if o.type == 'MESH'], 'triangles', tri)

bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/lc300.blend')

if RENDER:
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.78, 0.76, 0.72, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.5; sun.rotation_euler = (0.8, 0.2, 2.4); sc.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); g = bpy.context.active_object; g.data.materials.append(mat('ground', (0.55, 0.42, 0.30), 0, 0.9))
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    def shot(path, loc, look, lens=50, ortho=None, res=(1200, 700)):
        sc.render.resolution_x, sc.render.resolution_y = res
        cam.data.type = 'ORTHO' if ortho else 'PERSP'
        if ortho: cam.data.ortho_scale = ortho
        else: cam.data.lens = lens
        cam.location = loc; d = Vector(look) - Vector(loc); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    sc.render.film_transparent = True; g.hide_render = True
    shot(f'{OUT}/side.png', (0, 12, 1.0), (0, 0, 1.0), ortho=5.6, res=(1400, 700))
    sc.render.film_transparent = False; g.hide_render = False
    shot(f'{OUT}/q34.png', (6.5, 5.0, 2.2), (0.3, 0, 0.9), lens=40)
    shot(f'{OUT}/front.png', (9, 0, 1.0), (0, 0, 1.0), ortho=2.6, res=(800, 800))
    shot(f'{OUT}/rear34.png', (-6.0, 4.6, 2.0), (-0.3, 0, 0.9), lens=40)
    g.hide_render = True
    lamp = bpy.data.objects.new('cabin_lamp', bpy.data.lights.new('cabin_lamp', 'AREA')); lamp.data.energy = 60; lamp.data.size = 1.2
    lamp.location = (d2x(2.4), 0, 1.75); sc.collection.objects.link(lamp)
    shot(f'{OUT}/driver.png', (d2x(2.66), 0.40, 1.57), (d2x(0.0), 0.34, 1.25), lens=20, res=(1200, 800))
    shot(f'{OUT}/cabin.png', (d2x(3.35), -0.35, 1.55), (d2x(1.7), 0.2, 1.05), lens=18, res=(1200, 800))
    lamp.hide_render = True
    g.hide_render = False
    door_objs['door_FL'].rotation_euler.z = -1.05; door_objs['door_RL'].rotation_euler.z = -1.0; tailgate.rotation_euler.y = -1.2
    shot(f'{OUT}/open.png', (1.5, 7.5, 2.6), (-0.4, 0, 1.0), lens=32)

# ------------------------------------------------------------------ export: one GLB with every part named, doors closed
for n, o in door_objs.items(): o.rotation_euler = (0, 0, 0)
tailgate.rotation_euler = (0, 0, 0)
for o in bpy.data.objects: o.select_set(o.type == 'MESH' and o.name not in ('Plane',) and not o.name.startswith('ground'))
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.data.materials and o.data.materials[0].name == 'ground': o.select_set(False)
bpy.ops.export_scene.gltf(filepath=f'{OUT}/lc300.glb', export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print('glb', os.path.getsize(f'{OUT}/lc300.glb'))

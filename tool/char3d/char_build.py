"""The player character: a Saudi man in a white thobe, red shemagh and black iqal, with leather sandals.

Body: the MakeHuman base mesh (CC0) with macro targets, posed to a relaxed stance that becomes the bind pose.
Clothes: signed distance fields built around that body, meshed with marching cubes, skinned from the body's weights.
Run: blendenv/bin/python char_build.py <out_dir>
"""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mhbase import body, joints
from rig import build, weights
from blendchar import mesh, material, armature, skin, point, stage, shoot
from scipy import ndimage
from skimage import measure

OUT = sys.argv[-1]; os.makedirs(OUT, exist_ok=True)
H = 0.005                                  # voxel size of the clothing fields (m)
LO = np.array([-0.42, -0.32, -0.03])
SHAPE = (168, 128, 372)                    # x, y, z

# ------------------------------------------------------------------ A. body, rig, bind pose
P, VT, F, FT, G = body()
J, sk = joints(P); B = build(J, sk); Wall = weights(len(P))
SKIRT_HEAD = np.array([0.0, -0.005, 0.95])
for n, t in (('skirt.F', (0, -0.19, 0.08)), ('skirt.B', (0, 0.17, 0.08)), ('skirt.L', (0.25, -0.01, 0.08)), ('skirt.R', (-0.25, -0.01, 0.08))):
    B[n] = dict(head=SKIRT_HEAD.copy(), tail=np.array(t, float), parent='hips')
used = sorted({v for f in F for v in f}); remap = {v: i for i, v in enumerate(used)}
Pb = P[used]; Fb = [[remap[v] for v in f] for f in F]; Wb = [Wall[v] for v in used]
uvs = {}
for f, ft in zip(F, FT):
    for v, t in zip(f, ft): uvs[(remap[v], tuple(f))] = VT[t]

bpy.ops.wm.read_factory_settings(use_empty=True)
skin_mat = material('skin', (0.50, 0.28, 0.16), 0.5)
ob_body = mesh('body', Pb, Fb, skin_mat)
uvl = ob_body.data.uv_layers.new(name='UV')
for poly, ft in zip(ob_body.data.polygons, FT):
    for li, t in zip(poly.loop_indices, ft): uvl.data[li].uv = VT[t]
rig = armature(B); skin(ob_body, rig, Wb)      # skin() keeps the 4 strongest bones per vertex
for s, sx in (('.L', 1), ('.R', -1)):
    point(rig, 'upperarm' + s, (0.42 * sx, 0.03, -1))
    point(rig, 'forearm' + s, (0.34 * sx, -0.16, -1))
    point(rig, 'hand' + s, (0.30 * sx, -0.08, -1))
bpy.context.view_layer.objects.active = ob_body; ob_body.select_set(True)
bpy.ops.object.modifier_apply(modifier='rig')
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT'); bpy.ops.pose.armature_apply(); bpy.ops.object.mode_set(mode='OBJECT')
m = ob_body.modifiers.new('rig', 'ARMATURE'); m.object = rig
Pp = np.array([v.co[:] for v in ob_body.data.vertices])
BJ = {b.name: (np.array(b.head_local[:]), np.array(b.tail_local[:])) for b in rig.data.bones}

# ------------------------------------------------------------------ B. body signed distance field
xs = LO[0] + H * np.arange(SHAPE[0]); ys = LO[1] + H * np.arange(SHAPE[1]); zs = LO[2] + H * np.arange(SHAPE[2])
X, Y, Z = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32), zs.astype(np.float32), indexing='ij')
surf = np.zeros(SHAPE, bool)
tris = [(f[0], f[i], f[i + 1]) for f in Fb for i in range(1, len(f) - 1)]
T = Pp[np.array(tris)]
for a in np.linspace(0, 1, 9):
    for b in np.linspace(0, 1 - a, max(2, int(9 * (1 - a)) + 1)):
        pts = T[:, 0] * (1 - a - b) + T[:, 1] * a + T[:, 2] * b
        ij = np.floor((pts - LO) / H).astype(int)
        ok = np.all((ij >= 0) & (ij < SHAPE), 1); surf[tuple(ij[ok].T)] = True
eyes = [np.array([sx * 0.029, -0.129, 1.635]) for sx in (1, -1)]
for c in eyes: surf |= (X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2 < 0.016 ** 2
inside = ndimage.binary_fill_holes(ndimage.binary_dilation(surf, iterations=1))
sdf = ((ndimage.distance_transform_edt(~inside) - ndimage.distance_transform_edt(inside)) * H + H * 0.5).astype(np.float32)
print('body field ready', inside.sum())

def sample(field, p):
    q = (np.asarray(p) - LO) / H
    return ndimage.map_coordinates(field, q.T, order=1, mode='nearest')

from functools import reduce
def mx(*a): return reduce(np.maximum, a)
def mn(*a): return reduce(np.minimum, a)

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

def plane_keep(p0, n):          # negative on the side opposite n
    n = n / np.linalg.norm(n); return (X - p0[0]) * n[0] + (Y - p0[1]) * n[1] + (Z - p0[2]) * n[2]

# ------------------------------------------------------------------ C. thobe
neck_z = BJ['neck'][0][2]
collar = 1.483 + 0.25 * (Y + 0.03)                      # the neckline: lower at the front, higher at the back
def seg_dist(a, b):
    ab = b - a; t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1] + (Z - a[2]) * ab[2]) / ab.dot(ab), 0, 1)
    return np.sqrt((X - a[0] - t * ab[0]) ** 2 + (Y - a[1] - t * ab[1]) ** 2 + (Z - a[2] - t * ab[2]) ** 2)
arm_d = np.full(SHAPE, 9.0, np.float32)
for s_ in ('.L', '.R'):
    arm_d = np.minimum(arm_d, np.minimum(seg_dist(BJ['upperarm' + s_][0], BJ['forearm' + s_][0]), seg_dist(BJ['forearm' + s_][0], BJ['hand' + s_][0])))
in_arm = arm_d < 0.085
# the torso stops at the hips; the sleeves run on down to the wrists
upper = mx(*[sdf - 0.016, np.where(in_arm, -1.0, 1.02 - Z), 0.62 - Z])
cuts = []
for s in ('.L', '.R'):
    w0, w1 = BJ['hand' + s][0], BJ['forearm' + s][0]
    d = w0 - w1; d /= np.linalg.norm(d)
    cuts.append(np.where(in_arm, plane_keep(w0 - d * 0.03, d), -1.0))      # the sleeve ends 3 cm above the wrist (only the sleeve is cut)
# the skirt falls straight from the chest and hips to just above the ankles
torso_v = np.array([i for i, w in enumerate(Wb) if sum(w.get(k, 0) for k in w if k.startswith(('upperarm', 'forearm', 'hand'))) < 0.2])
def extent(z0, z1):
    q = Pp[torso_v]; q = q[(q[:, 2] > z0) & (q[:, 2] < z1)]; return q.min(0), q.max(0)
lo_h, hi_h = extent(0.86, 1.0); lo_c, hi_c = extent(1.1, 1.3)
cx = 0.0; front = min(lo_h[1], lo_c[1]) - 0.025; back = hi_h[1] + 0.02
cy = (front + back) / 2; ry0 = (back - front) / 2; rx0 = max(hi_h[0], -lo_h[0]) + 0.03
hem = 0.075
leg_v = Pp[np.array([i for i, w in enumerate(Wb) if sum(w.get(k, 0) for k in w if k.startswith(('thigh', 'shin'))) > 0.5])]
scale = np.ones(SHAPE[2], np.float32)
for k, z in enumerate(zs):
    q = leg_v[np.abs(leg_v[:, 2] - z) < 0.01]
    if len(q): scale[k] = max(1.0, np.sqrt(((q[:, 0] - cx) / rx0) ** 2 + ((q[:, 1] - cy) / ry0) ** 2).max() + 0.08)
scale = ndimage.gaussian_filter1d(np.maximum.accumulate(scale[::-1])[::-1], 40)[None, None, :]      # never narrower lower down, a smooth A-line
print('skirt scale', scale.max(), scale[0, 0, ::40].round(2))
grow = np.clip(1.0 - Z, 0, None) * 0.03
rx = rx0 * scale + grow; ryy = ry0 * scale + grow * 0.8
skirt = (np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ryy) ** 2) - 1) * min(rx0, ry0)
skirt = np.maximum(skirt, Z - 1.22)
open_solid = np.minimum(smin(np.where(in_arm, 1.0, upper), skirt, 0.06), np.where(in_arm, upper, 1.0))
shell = np.maximum(open_solid, -(open_solid + 0.005))          # 5 mm of cloth
thobe = mx(shell, hem - Z, Z - collar, *cuts)
solid = mx(open_solid, hem - Z, Z - collar, *cuts)              # the closed volume, for hiding the body and laying the shemagh
# a stand-up collar band around the neck
band = mx(*[np.abs(sdf - 0.011) - 0.0035, collar - 0.008 - Z, Z - (collar + 0.028)])
band = np.maximum(band, np.sqrt(X ** 2 + (Y + 0.02) ** 2) - 0.11)
thobe = np.minimum(thobe, band)
print('thobe field ready')

# ------------------------------------------------------------------ D. shemagh and iqal
brow = 1.668
head_cap = np.maximum(sdf - 0.011, brow - 0.004 - Z - np.clip(Y + 0.05, 0, None) * 1.2)   # the edge sits on the brow and drops down the back
k_t = int(round((1.645 - LO[2]) / H))
head2d = (sdf[:, :, k_t] - 0.013)[:, :, None]
flare = np.clip(1.62 - Z, 0, None) * 0.32
drape = mx(*[head2d - flare, Z - 1.66, 1.43 - Z + np.clip(Y, 0, None) * 0.0, -0.062 - Y])     # falls from the temples to the shoulders, open at the face
vol = smin(head_cap, drape, 0.03)
shemagh = np.abs(vol) - 0.0055
# the back point of the folded triangle, lying on the thobe down the back
on_back = np.abs(solid - 0.007) - 0.0025
tri = mx(*[on_back, -Y, np.abs(X) - np.clip(Z - 1.16, 0, None) * 0.55, 1.16 - Z, Z - 1.47])
# the two front ends hanging on the chest
flap = mx(*[on_back, Y + 0.02, np.abs(np.abs(X) - 0.085) - 0.045 * np.clip((Z - 1.24) / 0.22, 0, 1), 1.24 - Z, Z - 1.47])
shemagh = mn(*[shemagh, tri, flap])
shemagh = np.maximum(shemagh, -(sdf - 0.004))           # never inside the skin
# iqal: two black cords round the crown, the back a little lower
kz = int(round((1.71 - LO[2]) / H)); crown = sdf[:, :, kz] - 0.015
iq_z = 1.690 - Y * 0.15                      # the front above the brow, tilted down at the back
ring = lambda dz: np.sqrt((sdf - 0.0175) ** 2 + (Z - iq_z - dz) ** 2) - 0.0068      # hugs the shemagh along a tilted band; thick enough for the 5 mm grid
iqal = np.minimum(ring(0.0), ring(0.0135))
print('headwear fields ready')

# ------------------------------------------------------------------ E. sandals (soles and a strap), the feet stand on them
sandal = np.full(SHAPE, 1.0, np.float32)
for s in ('.L', '.R'):
    fv = Pp[np.array([i for i, w in enumerate(Wb) if w.get('foot' + s, 0) + w.get('toes' + s, 0) > 0.5])]
    sole2d = np.zeros(SHAPE[:2], bool)
    ij = np.floor((fv[fv[:, 2] < 0.035][:, :2] - LO[:2]) / H).astype(int); sole2d[tuple(ij.T)] = True
    sole2d = ndimage.binary_closing(sole2d, iterations=3)
    d2 = (ndimage.distance_transform_edt(~sole2d) * H - 0.008)[:, :, None]
    sole = mx(*[d2, Z - 0.0, -0.022 - Z])
    toe_y = BJ['toes' + s][0][1]
    strap = mx(*[np.abs(sdf - 0.006) - 0.0040, np.abs(Y - (toe_y + 0.035)) - 0.022, Z - 0.075, 0.0 - Z])
    side = (X > 0) if s == '.L' else (X < 0)
    sandal = np.where(side, np.minimum(sandal, np.minimum(sole, strap)), sandal)
print('sandals ready')

def to_mesh(field, name, level=0.0, keep_largest=False, smooth_iter=6):
    v, f, _, _ = measure.marching_cubes(field, level, spacing=(H, H, H))
    v += LO
    ob = mesh(name, v, f.tolist())
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(ob.data); bm.free()
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True)
    mo = ob.modifiers.new('sm', 'SMOOTH'); mo.iterations = smooth_iter; mo.factor = 0.5
    bpy.ops.object.modifier_apply(modifier='sm')
    return ob

thobe_ob = to_mesh(thobe, 'thobe')
def drop_inner(ob, field, keep):
    V = np.array([v.co[:] for v in ob.data.vertices]); inner = sample(field, V) < -0.0022
    keepv = keep(V)
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(inner[v.index] and not keepv[v.index] for v in f.verts)], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data); bm.free()
def near_openings(V):
    k = V[:, 2] < hem + 0.07
    for s in ('.L', '.R'):
        w0, w1 = BJ['hand' + s][0], BJ['forearm' + s][0]; d = (w0 - w1) / np.linalg.norm(w0 - w1)
        k |= np.abs((V - (w0 - d * 0.03)) @ d) < 0.05
    return k
drop_inner(thobe_ob, solid, near_openings)
shemagh_ob = to_mesh(shemagh, 'shemagh')
iqal_ob = to_mesh(iqal, 'iqal', smooth_iter=8)
sandal_ob = to_mesh(sandal, 'sandals', smooth_iter=3)
np.savez_compressed(f'{OUT}/fields.npz', solid=solid.astype(np.float16), sdf=sdf.astype(np.float16))

# ------------------------------------------------------------------ F. drop the hidden body under the thobe
sv = sample(solid, Pp)
hide = ((sv < -0.006) & (Pp[:, 2] > 0.46)) | (sample(vol, Pp) < -0.004)     # legs above the shin stay hidden: they would poke through the swinging skirt     # under the thobe, or under the shemagh (scalp, ears, nape)
bm = bmesh.new(); bm.from_mesh(ob_body.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(hide[v.index] for v in f.verts)], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# close the cut ends of the shins and wrists, so no open tube shows under the hem or the cuff
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary and e.verts[0].co.z < 1.3], sides=0)
bm.to_mesh(ob_body.data); bm.free()

# ------------------------------------------------------------------ G. decimate, skin the clothes from the body
def decimate(ob, ratio):
    bpy.context.view_layer.objects.active = ob
    mo = ob.modifiers.new('dec', 'DECIMATE'); mo.ratio = ratio
    bpy.ops.object.modifier_apply(modifier='dec')
ob_body.modifiers.remove(ob_body.modifiers['rig'])
# the visible body is now separate pieces (head and neck, two hands, two lower legs): reduce each on its own,
# the face gently, hands and feet harder, then join them back
for o in bpy.context.selected_objects: o.select_set(False)
bpy.context.view_layer.objects.active = ob_body; ob_body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in bpy.context.selected_objects]
for o in parts:
    gn = [g.name for g in o.vertex_groups]; acc = {}
    for v in o.data.vertices:
        for g in v.groups: acc[gn[g.group].split('.')[0]] = acc.get(gn[g.group].split('.')[0], 0) + g.weight
    top = max(acc, key=acc.get) if acc else 'head'
    ratio = 0.45 if top in ('head', 'neck') else 0.26 if top in ('hand', 'forearm') else 0.30
    if len(o.data.polygons) > 40: decimate(o, ratio)
for o in bpy.context.selected_objects: o.select_set(False)
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = ob_body; bpy.ops.object.join()
m = ob_body.modifiers.new('rig', 'ARMATURE'); m.object = rig
for ob, r in ((thobe_ob, 3800 / len(thobe_ob.data.polygons)), (shemagh_ob, 1300 / len(shemagh_ob.data.polygons)), (iqal_ob, 900 / len(iqal_ob.data.polygons)), (sandal_ob, 500 / len(sandal_ob.data.polygons))):
    n0 = len(ob.data.polygons); decimate(ob, r); print(ob.name, n0, '->', len(ob.data.polygons))
print('body faces', len(ob_body.data.polygons))

from scipy.spatial import cKDTree
tree = cKDTree(Pp)
def arm_dist_at(V):
    q = (V - LO) / H
    return ndimage.map_coordinates(arm_d, q.T, order=1, mode='nearest')
def transfer(ob, legs_blend=False, only=None, sleeves=False):
    V = np.array([v.co[:] for v in ob.data.vertices])
    ad = arm_dist_at(V)
    d, nn = tree.query(V, k=8)
    W = []
    for i, (dd, ii) in enumerate(zip(d, nn)):
        acc = {}
        wts = 1 / (dd + 0.01)
        for wt, j in zip(wts, ii):
            for b, x in Wb[j].items(): acc[b] = acc.get(b, 0) + wt * x
        if only: acc = {b: x for b, x in acc.items() if b in only} or {only[0]: 1}
        if sleeves:
            keep_arm = float(np.clip((0.092 - ad[i]) / 0.015, 0, 1))      # only the sleeve itself follows the arm, not the thobe's side next to it
            acc = {b: (x * keep_arm if b.startswith(('upperarm', 'forearm', 'hand')) else x) for b, x in acc.items()}
            if sum(acc.values()) < 1e-6: acc = {'upperchest': 1}
            # the cuff rides on the forearm: the hand bends inside it, so the sleeve never takes the hand's weight
            for hs in ('.L', '.R'):
                if 'hand' + hs in acc: acc['forearm' + hs] = acc.get('forearm' + hs, 0) + acc.pop('hand' + hs)
            # the waist: blend into the hips so the torso and the skirt meet without a crease
            if 0.9 < V[i, 2] < 1.15 and keep_arm < 0.05:          # torso cloth only, never the sleeves
                hb = float(np.clip((1.15 - V[i, 2]) / 0.25, 0, 1)); tot = sum(acc.values())
                acc = {b: x * (1 - hb) for b, x in acc.items()}; acc['hips'] = acc.get('hips', 0) + hb * tot
        if legs_blend and V[i, 2] < 0.95 and ad[i] > 0.092:          # the skirt only; the cuffs hang below 0.95 m in the bind pose
            # the skirt: a mix of the near leg, the far leg and the hips, stiffer near the middle line
            # around the body: front, left, back, right panels; down the body: from the hips to the skirt bones
            k = float(np.clip((0.95 - V[i, 2]) / 0.40, 0, 1)); k = k * k * (3 - 2 * k)
            phi = np.arctan2(V[i, 0], -(V[i, 1] + 0.005)); c, sn = np.cos(phi), np.sin(phi)
            acc = {'hips': 1 - k, 'skirt.F': k * max(0, c) ** 2, 'skirt.B': k * max(0, -c) ** 2, 'skirt.L': k * max(0, sn) ** 2, 'skirt.R': k * max(0, -sn) ** 2}
        s = sum(acc.values()); W.append({b: x / s for b, x in acc.items()})
    skin(ob, rig, W)
transfer(thobe_ob, legs_blend=True, sleeves=True)
def transfer_sandals():
    V = np.array([v.co[:] for v in sandal_ob.data.vertices]); W = []
    for p in V:
        s = '.L' if p[0] > 0 else '.R'
        toe_y = BJ['toes' + s][0][1]
        t = float(np.clip((toe_y + 0.01 - p[1]) / 0.03, 0, 1))      # in front of the ball of the foot: the toes
        W.append({'foot' + s: 1 - t, 'toes' + s: t} if t > 0 else {'foot' + s: 1.0})
    skin(sandal_ob, rig, W)
transfer(shemagh_ob, only=['head', 'neck', 'upperchest', 'chest'])
transfer(iqal_ob, only=['head'])
transfer_sandals()

# ------------------------------------------------------------------ H. looks: skin with beard and brows, eyes, fabrics
def vcolor(ob, fn, name='Col'):
    attr = ob.data.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    for i, v in enumerate(ob.data.vertices): attr.data[i].color = (*fn(np.array(v.co[:])), 1)
rng = np.random.default_rng(3)
sm = lambda e0, e1, t: float(np.clip((t - e0) / (e1 - e0), 0, 1))
def skin_col(p):
    x, y, z = p; base = np.array([0.50, 0.28, 0.16]); hair = np.array([0.03, 0.022, 0.017])
    front = sm(-0.02, -0.06, y)
    # the beard line runs from the sideburn down the jaw; the cheeks above it stay clean
    jaw_top = 1.566 + 0.85 * max(0.0, abs(x) - 0.028)
    beard = front * sm(1.500, 1.515, z) * sm(jaw_top + 0.006, jaw_top - 0.004, z)
    lips = sm(0.030, 0.022, abs(x)) * sm(1.556, 1.562, z) * sm(1.586, 1.580, z) * sm(-0.105, -0.115, y)
    mous = sm(0.034, 0.026, abs(x)) * sm(1.584, 1.588, z) * sm(1.600, 1.596, z) * sm(-0.10, -0.11, y)
    side = sm(0.055, 0.065, abs(x)) * sm(1.66, 1.64, z) * sm(1.59, 1.61, z) * sm(0.0, -0.03, y)
    brow = sm(0.008, 0.014, abs(x)) * sm(0.056, 0.048, abs(x)) * sm(1.650, 1.656, z) * sm(1.672, 1.666, z) * sm(-0.095, -0.105, y)
    h = max(beard * (1 - lips) * 0.82, mous * 0.9, side * 0.85, brow * 0.95)
    return base * (1 - h) + hair * h
def paint_skin(tex=2048):
    img = np.zeros((tex, tex, 3), np.float32); got = np.zeros((tex, tex), bool)
    for f, ft in zip(Fb, FT):
        for a, b, c in [(0, i, i + 1) for i in range(1, len(f) - 1)]:
            uv = VT[[ft[a], ft[b], ft[c]]] * tex; p3 = Pp[[f[a], f[b], f[c]]]
            x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            m = np.array([[uv[1, 0] - uv[0, 0], uv[2, 0] - uv[0, 0]], [uv[1, 1] - uv[0, 1], uv[2, 1] - uv[0, 1]]])
            if abs(np.linalg.det(m)) < 1e-9: continue
            l = np.linalg.solve(m, np.stack([gx.ravel() - uv[0, 0], gy.ravel() - uv[0, 1]]))
            ok = (l[0] >= -0.02) & (l[1] >= -0.02) & (l[0] + l[1] <= 1.02)
            if not ok.any(): continue
            P3 = p3[0] + np.outer(l[0][ok], p3[1] - p3[0]) + np.outer(l[1][ok], p3[2] - p3[0])
            ix = np.clip(gx.ravel()[ok].astype(int), 0, tex - 1); iy = np.clip(gy.ravel()[ok].astype(int), 0, tex - 1)
            img[iy, ix] = skin_cols(P3); got[iy, ix] = True
    # fill the gaps between UV islands with the nearest painted colour
    _, (ii, jj) = ndimage.distance_transform_edt(~got, return_indices=True)
    img = img[ii, jj]
    img = ndimage.gaussian_filter(img, (0.6, 0.6, 0))
    srgb = np.where(img <= 0.0031308, img * 12.92, 1.055 * np.power(np.clip(img, 0, 1), 1 / 2.4) - 0.055)
    rgba = np.concatenate([srgb, np.ones((tex, tex, 1), np.float32)], 2)
    im = bpy.data.images.new('skin', tex, tex); im.pixels = rgba.ravel(); im.pack()
    im.filepath_raw = f'{OUT}/skin.png'; im.file_format = 'PNG'
    return im
def skin_cols(Q):
    x, y, z = Q[:, 0], Q[:, 1], Q[:, 2]
    S = lambda e0, e1, t: np.clip((t - e0) / (e1 - e0), 0, 1)
    base = np.array([0.50, 0.28, 0.16]); hair = np.array([0.03, 0.022, 0.017])
    front = S(-0.02, -0.06, y)
    # the jawline seen from the front: chin at about 1.52 m in the middle, rising to the ear at the sides
    jaw = 1.517 + 1.15 * np.maximum(0.0, np.abs(x) - 0.012) ** 1.35
    band = S(jaw - 0.004, jaw + 0.004, z) * S(jaw + 0.030, jaw + 0.020, z)          # a strip about 2.5 cm wide along the jaw
    chin = S(0.034, 0.024, np.abs(x)) * S(1.505, 1.512, z) * S(1.565, 1.556, z)     # the goatee under the lip
    beard = front * np.maximum(band, chin)
    lips = S(0.030, 0.022, np.abs(x)) * S(1.556, 1.562, z) * S(1.586, 1.580, z) * S(-0.105, -0.115, y)
    mous = S(0.034, 0.024, np.abs(x)) * S(1.584, 1.588, z) * S(1.601, 1.596, z) * S(-0.10, -0.11, y)
    side = S(0.060, 0.066, np.abs(x)) * S(1.625, 1.612, z) * S(1.585, 1.595, z) * S(0.0, -0.03, y)
    arch = 1.660 + 0.006 * np.sin(np.clip((np.abs(x) - 0.012) / 0.04, 0, 1) * np.pi) - 0.004 * S(0.03, 0.052, np.abs(x))
    brow = S(0.009, 0.015, np.abs(x)) * S(0.055, 0.047, np.abs(x)) * S(0.0045, 0.0025, np.abs(z - arch)) * S(-0.095, -0.105, y)
    rngv = (np.random.default_rng(5).random(len(x)) - 0.5) * 0.35
    h = np.clip(np.maximum.reduce([beard * (1 - lips) * (0.78 + rngv), mous * (0.85 + rngv * 0.5), side * (0.70 + rngv), brow * 0.9]), 0, 1)[:, None]
    return base * (1 - h) + hair * h
skin_img = paint_skin()
nt = skin_mat.node_tree; ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = skin_img
nt.links.new(ti.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
def use_vcolor(mat):
    nt = mat.node_tree; a = nt.nodes.new('ShaderNodeVertexColor'); a.layer_name = 'Col'
    nt.links.new(a.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
# eyes: white with a dark brown iris looking forward
eye_mat = material('eye', (1, 1, 1), 0.15); use_vcolor(eye_mat)
for c in eyes:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.0122, location=tuple(c + np.array([0, 0.0015, 0])))
    e = bpy.context.active_object; e.data.materials.append(eye_mat)
    for p in e.data.polygons: p.use_smooth = True
    def ecol(p, c=c):
        d = p / np.linalg.norm(p); f = -d[1]
        return np.array([0.006, 0.005, 0.004]) if f > 0.975 else np.array([0.06, 0.03, 0.012]) if f > 0.87 else np.array([0.74, 0.70, 0.64])
    vcolor(e, ecol); skin(e, rig, [{'head': 1.0}] * len(e.data.vertices))
thobe_mat = material('thobe', (0.86, 0.85, 0.81), 0.72, sheen=0.4)
thobe_ob.data.materials.append(thobe_mat)
for p in thobe_ob.data.polygons: p.use_smooth = True
# the shemagh's red and white weave, projected around the head
tex = np.ones((256, 256, 4), np.float32)
yy, xx = np.mgrid[0:256, 0:256]
HT = np.array([[1,1,1,1,0,0,0,1],[1,1,1,1,0,0,1,1],[1,1,1,1,0,1,1,1],[1,1,1,1,1,1,1,0],[0,0,0,1,1,1,1,0],[0,0,1,1,1,1,0,0],[0,1,1,1,1,0,0,0],[1,1,1,0,0,0,0,0]], bool)
redmask = HT[(yy // 2) % 8, (xx // 2) % 8]
red = np.array([0.42, 0.012, 0.018, 1]); white = np.array([0.86, 0.83, 0.78, 1])
tex[:] = white; tex[redmask] = red
tex[..., :3] = np.where(tex[..., :3] <= 0.0031308, tex[..., :3] * 12.92, 1.055 * np.power(tex[..., :3], 1 / 2.4) - 0.055)
img = bpy.data.images.new('shemagh', 256, 256); img.pixels = tex.ravel(); img.pack()
sh_mat = material('shemagh', (1, 1, 1), 0.8, sheen=0.5)
nt = sh_mat.node_tree; ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img; ti.interpolation = 'Linear'
nt.links.new(ti.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
shemagh_ob.data.materials.append(sh_mat)
lay = shemagh_ob.data.uv_layers.new(name='UV')
for poly in shemagh_ob.data.polygons:
    poly.use_smooth = True
    us = [(np.arctan2(shemagh_ob.data.vertices[vi].co.x, shemagh_ob.data.vertices[vi].co.y + 0.01) / (2 * np.pi)) * 6.0 for vi in poly.vertices]
    if max(us) - min(us) > 3.0: us = [u + 6.0 if u < 0 else u for u in us]
    for li, vi, u in zip(poly.loop_indices, poly.vertices, us):
        lay.data[li].uv = (u, shemagh_ob.data.vertices[vi].co.z / 0.11)          # six whole repeats round the head
iqal_ob.data.materials.append(material('iqal', (0.015, 0.015, 0.016), 0.85))
for p in iqal_ob.data.polygons: p.use_smooth = True
sandal_ob.data.materials.append(material('leather', (0.13, 0.06, 0.025), 0.6))
# stand on the soles
rig.location.z = 0.022
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/character.blend')

# ------------------------------------------------------------------ I. check renders
sc, cam = stage(res=(800, 1000), samples=32)
shoot(sc, cam, f'{OUT}/c_front.png', (0, -6, 0.92), (1.5708, 0, 0), ortho=2.0)
shoot(sc, cam, f'{OUT}/c_side.png', (6, 0, 0.92), (1.5708, 0, 1.5708), ortho=2.0)
shoot(sc, cam, f'{OUT}/c_back.png', (0, 6, 0.92), (1.5708, 0, 3.1416), ortho=2.0)
sc.render.resolution_x, sc.render.resolution_y = 800, 800
shoot(sc, cam, f'{OUT}/c_face.png', (0.55, -1.2, 1.66), (1.5708, 0, 0.43), lens=85)

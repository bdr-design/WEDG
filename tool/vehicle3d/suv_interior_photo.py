"""Cabin parts shaped after the owner's reference images and wearing them as their texture.

The owner generated six views of the cabin on magenta (tool/vehicle3d/suv_parts/interior/): the dashboard from
behind the front seats, the driver's view, the driver's door card straight on, the steering wheel from the front,
a front seat from the side and the rear bench from the front. Each part here is a signed distance field whose
outline comes from its image (the magenta is the outside), so the shape matches the picture; the image is then
projected back onto the faces that look at its camera. Faces that turn away get plain tiling leather, wood or
plastic of the same colour. Units are real metres in the cabin frame of suv_interior.py (d back from the front
bumper, y to the left, z up).
"""
import bpy, bmesh, math, os, numpy as np
from mathutils import Vector
from scipy import ndimage
from skimage import measure
from PIL import Image
import suv_interior as SI

REF = os.environ.get('INTERIOR_REF') or next(p for p in (
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'suv_parts', 'interior'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ref_int')) if os.path.isdir(p))

def load_ref(name):
    a = np.asarray(Image.open(os.path.join(REF, name)).convert('RGB')).astype(np.float32)
    mag = (a[..., 0] > 180) & (a[..., 2] > 180) & (a[..., 1] < 110)
    return a, mag

def filled_texture(name, a, mag, out_dir):
    """The image with its magenta filled by the nearest colours (push-pull), so no magenta bleeds at edges."""
    mag = ndimage.binary_dilation(mag, iterations=3)          # the pink anti-aliased rim goes with the magenta
    f = a.copy(); known = ~mag
    for _ in range(60):
        if known.all(): break
        s = ndimage.uniform_filter(f * known[..., None], (7, 7, 1)); c = ndimage.uniform_filter(known.astype(np.float32), 7)
        new = (c > 0.02) & ~known; f[new] = s[new] / c[new, None]; known |= new
    f[~known] = (30, 28, 27)
    os.makedirs(out_dir, exist_ok=True); path = os.path.join(out_dir, name.replace('.png', '_tex.png'))
    Image.fromarray(f.clip(0, 255).astype(np.uint8)).save(path)
    return path

def photo_mat(name, path, rough=0.5, metal=0.0, coat=0.0, nmap=None):
    m = SI.make_mat(name, (path, nmap), rough=rough, metal=metal, coat=coat, nstrength=0.3)
    return m

def sdf2d(mask_inside, scale, blur=1.0):
    m = ndimage.gaussian_filter(mask_inside.astype(np.float32), blur) > 0.5
    return ((ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m)) * scale).astype(np.float32)

def sample(field, rows, cols):
    return ndimage.map_coordinates(field, [rows, cols], order=1, mode='nearest')

def mesh_from_field(name, field, lo, h, to_xyz, target, smooth=2):
    f = field.copy(); f[0], f[-1], f[:, 0], f[:, -1], f[:, :, 0], f[:, :, -1] = 1, 1, 1, 1, 1, 1
    v, faces, _, _ = measure.marching_cubes(f, 0.0, spacing=(h, h, h)); v += np.array(lo)
    P = to_xyz(v)
    me = bpy.data.meshes.new(name); me.from_pydata(P.tolist(), [], faces.tolist()); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    SI.activate(ob)
    if smooth:
        mo = ob.modifiers.new('sm', 'SMOOTH'); mo.iterations = smooth; mo.factor = 0.5; bpy.ops.object.modifier_apply(modifier='sm')
    if len(me.polygons) > target:
        mo = ob.modifiers.new('dec', 'DECIMATE'); mo.ratio = target / len(me.polygons); bpy.ops.object.modifier_apply(modifier='dec')
    for p in me.polygons: p.use_smooth = True
    return ob

def set_uv(ob, fn):
    """fn(co_local, normal_local, face) -> (u, v) per corner."""
    me = ob.data; lay = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        for li, vi in zip(p.loop_indices, p.vertices):
            lay.data[li].uv = fn(me.vertices[vi].co, p.normal, p)

# ------------------------------------------------------------------ the steering wheel
def steering_wheel(centre, tilt, tex_dir, diameter=0.38):
    """Shaped after wheel.png (front view): the rim is a torus over the photo's ring, the hub and spokes are the
    photo's inner outline pressed to a depth (the airbag pad thickest, toward the driver). The photo is projected
    straight on, so buttons, stitching, the silver spoke trims and the wood inserts are the photo's own.
    Local frame as before: X along the column (towards the dash), Y across (left +), Z up."""
    a, mag = load_ref('wheel.png'); H, W = mag.shape
    inside = ~mag
    ys, xs = np.where(inside); cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    s = diameter / (xs.max() - xs.min())                       # metres per pixel
    R_out = diameter / 2; tube = 0.0158; R_mid = R_out - tube
    yy, xx = np.mgrid[0:H, 0:W]; rr = np.hypot(xx - cx, yy - cy) * s
    inner_mask = inside & (rr < R_out - 2 * tube + 0.004)        # hub and spokes
    d_in = sdf2d(inner_mask, s)
    # depth of the inner parts: the airbag pad is a thick cushion toward the driver, the spokes are thin
    pad = (np.abs(xx - cx) * s < 0.078) & ((yy - cy) * s > -0.075) & ((yy - cy) * s < 0.085) & inner_mask
    padw = ndimage.gaussian_filter(pad.astype(np.float32), 18)
    half_t = (0.011 + 0.018 * padw).astype(np.float32); a0 = (-0.004 - 0.020 * padw).astype(np.float32)
    h = 0.0024
    ax = [np.arange(-0.07, 0.04 + h, h), np.arange(-0.205, 0.205 + h, h), np.arange(-0.205, 0.205 + h, h)]
    A, U, V = np.meshgrid(*[q.astype(np.float32) for q in ax], indexing='ij')
    col = cx - U / s; row = cy - V / s                          # the driver's left (+U) is the photo's left
    rho = np.hypot(U, V)
    f_rim = np.sqrt((rho - R_mid) ** 2 + (A * 1.12) ** 2) - tube
    din = sample(d_in, row.ravel(), col.ravel()).reshape(A.shape)
    ht = sample(half_t, row.ravel(), col.ravel()).reshape(A.shape); a0s = sample(a0, row.ravel(), col.ravel()).reshape(A.shape)
    f_in = np.maximum(din, np.abs(A - a0s) - ht)
    f_in = ndimage.gaussian_filter(f_in, 1.0)
    f = SI.smin(f_rim, f_in, 0.008)
    K = SI.C['K']
    ob = mesh_from_field('steering', f, [ax[0][0], ax[1][0], ax[2][0]], h, lambda v: v * K, 3200)
    tex = filled_texture('wheel.png', a, mag, tex_dir)
    ob.data.materials.append(photo_mat('wheel_photo', tex, rough=0.45))
    set_uv(ob, lambda co, n, p: ((cx - co.y / K / s) / W, 1 - (cy - co.z / K / s) / H))
    ob.location = SI.R(centre); ob.rotation_euler = (0, -tilt, 0)
    return ob

# ------------------------------------------------------------------ front seats
def front_seat(name, y0, tex_dir, hip=(2.80, 0.86)):
    """Shaped after seat_side.png: the side outline (front to the right of the photo) pressed across the seat's width
    with rounded sides; the centre of the cushion and backrest sits a little lower than the bolsters. The photo is
    projected on both sides; the other faces wear the matching tiling leather."""
    a, mag = load_ref('seat_side.png'); H, W = mag.shape
    inside = ~mag
    ys, xs = np.where(inside)
    floor_z, top_z = SI.FLOOR + 0.0, 1.76
    s = (top_z - floor_z) / (ys.max() - ys.min())             # metres per pixel: rails on the floor to the headrest top
    front_d = hip[0] - 0.53                                    # the cushion's front edge
    x_front = xs.max()
    # photo (col, row) <- (d, z): the seat's front (smaller d) is on the photo's right
    to_col = lambda d: x_front - (d - front_d) / s
    to_row = lambda z: ys.max() - (z - floor_z) / s
    d_side = sdf2d(inside, s, blur=1.5)
    d_lo, d_hi = front_d - 0.02, front_d + (xs.max() - xs.min()) * s + 0.02
    h = 0.008
    ax = [np.arange(d_lo, d_hi + h, h), np.arange(y0 - 0.33, y0 + 0.33 + h, h), np.arange(floor_z - 0.02, top_z + 0.03, h)]
    D, Y, Z = np.meshgrid(*[q.astype(np.float32) for q in ax], indexing='ij')
    side = sample(d_side, to_row(Z).ravel(), to_col(D).ravel()).reshape(D.shape)
    # half-widths by height: rails, base, cushion and backrest, the headrest
    hw = np.where(Z < floor_z + 0.08, 0.20, np.where(Z > 1.535, 0.135, 0.265)).astype(np.float32)
    hw = ndimage.gaussian_filter(hw, (0, 0, 2.0))
    lat = np.abs(Y - y0) - hw
    f = -SI.smin(-side, -lat, 0.035)                            # rounded intersection: soft bolster edges
    centre = np.clip(1 - (np.abs(Y - y0) - 0.10) / 0.06, 0, 1) * ((Z > floor_z + 0.25) & (Z < 1.52))
    f = f + 0.014 * centre                                       # the inserts sit lower than the bolsters
    for e in (0.13, -0.13): f = SI.groove(f, Y - (y0 + e), 0.005, 0.003, mask=(Z > floor_z + 0.25) & (Z < 1.52))
    K = SI.C['K']; XF = SI.C['XF']
    to_xyz = lambda v: np.stack([XF - v[:, 0] * K, v[:, 1] * K, v[:, 2] * K], 1)
    ob = mesh_from_field(name, f, [ax[0][0], ax[1][0], ax[2][0]], h, to_xyz, 2600)
    tex = filled_texture('seat_side.png', a, mag, tex_dir)
    mat = bpy.data.materials.get('seat_photo') or photo_mat('seat_photo', tex, rough=0.5)
    ob.data.materials.append(mat); ob.data.materials.append(SI.C['M']['int_perf']); ob.data.materials.append(SI.C['M']['int_leather'])
    for p in ob.data.polygons:
        n = p.normal; d, y, z = SI.to_real(*p.center)
        if abs(n.y) > 0.55: p.material_index = 0
        elif abs(y - y0) < 0.10 and floor_z + 0.25 < z < 1.52: p.material_index = 1
        else: p.material_index = 2
    def uv(co, n, p):
        if p.material_index == 0:
            d, y, z = SI.to_real(*co); return (to_col(d) / W, 1 - to_row(z) / H)
        return (0, 0)
    set_uv(ob, uv)
    SI.tri_uv_keep(ob, keep_index=0)
    return ob

# ------------------------------------------------------------------ door cards
def door_card(door, d0, d1, side, belt_z, tex_dir, z_bottom=0.50, y_face=0.888):
    """door_FL.png pressed onto the inside of a door: a grid over the card, pushed into the cabin where the photo is
    beige (armrest and insert) or carries the switch panel and wood, and sunk where the door pocket is. The photo is
    the card's texture (mirrored for the right-hand doors, whose front is on the left as seen from inside)."""
    a, mag = load_ref('door_FL.png'); H, W = mag.shape
    top_row = 61                                                    # the window sill in the photo
    L = a.mean(2); beige = (a[..., 0] > a[..., 2] + 25) & (L > 110)
    wood = (a[..., 0] > a[..., 2] + 20) & (L > 50) & (L <= 110)
    rows, cols = np.mgrid[0:H, 0:W]
    pocket = (rows > 650) & (rows < 880) & (cols > 470) & (cols < 1160) & (L < 60)
    switch = (rows > 190) & (rows < 480) & (cols > 900) & (cols < 1240) & ~beige
    hgt = 0.030 * ndimage.gaussian_filter(beige.astype(np.float32), 8) + 0.016 * ndimage.gaussian_filter((wood | switch).astype(np.float32), 5)
    hgt += 0.018 * ndimage.gaussian_filter(((rows > 400) & (rows < 640) & beige).astype(np.float32), 14)   # the armrest's roll
    hgt -= 0.020 * ndimage.gaussian_filter(pocket.astype(np.float32), 10)
    nu, nv = 72, 48
    us = np.linspace(0, 1, nu); vs = np.linspace(0, 1, nv)
    K = SI.C['K']; V, F, UV = [], [], []
    for j, v in enumerate(vs):
        for i, u in enumerate(us):
            col = u * (W - 1); row = top_row + v * (H - 1 - top_row)
            d = d1 - u * (d1 - d0)                                    # photo left = the door's rear edge
            z = belt_z - 0.012 - v * (belt_z - 0.012 - z_bottom)
            h_ = float(ndimage.map_coordinates(hgt, [[row], [col]], order=1)[0])
            V.append(SI.R((d, side * (y_face - h_), z))[:]); UV.append(((1 - u) if side < 0 else u, 1 - row / H))
    for j in range(nv - 1):
        for i in range(nu - 1):
            a_ = j * nu + i; F.append([a_, a_ + nu, a_ + nu + 1, a_ + 1] if side > 0 else [a_, a_ + 1, a_ + nu + 1, a_ + nu])
    me = bpy.data.meshes.new(door.name + '_card'); me.from_pydata(V, [], F); me.update()
    lay = me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        for li, vi in zip(p.loop_indices, p.vertices): lay.data[li].uv = UV[vi]
        p.use_smooth = True
    ob = bpy.data.objects.new(door.name + '_card', me); bpy.context.collection.objects.link(ob)
    tex = filled_texture('door_FL.png', a, mag, tex_dir)
    mat = bpy.data.materials.get('door_photo') or photo_mat('door_photo', tex, rough=0.55)
    me.materials.append(mat)
    SI.activate(door); ob.select_set(True); bpy.ops.object.join()
    return door

# ------------------------------------------------------------------ photo regions on modelled parts
def map_regions(ob, ref_name, mat_name, regions, tex_dir, rough=0.5):
    """Give faces of ob the reference photo where a region accepts them. Each region: (test(c, n) -> bool,
    uv(d, y, z) -> (col, row)) in real metres; c is the face centre, n its normal in the cabin frame."""
    a, mag = load_ref(ref_name); H, W = mag.shape
    tex = filled_texture(ref_name, a, mag, tex_dir)
    mat = bpy.data.materials.get(mat_name) or photo_mat(mat_name, tex, rough=rough)
    me = ob.data
    if mat.name not in [m.name for m in me.materials]: me.materials.append(mat)
    mi = [m.name for m in me.materials].index(mat.name)
    lay = me.uv_layers.active or me.uv_layers.new(name='UVMap')
    n_set = 0
    for p in me.polygons:
        c = SI.to_real(*p.center); n = (-p.normal.x, p.normal.y, p.normal.z)
        for test, uvf in regions:
            if not test(c, n): continue
            p.material_index = mi; n_set += 1
            for li, vi in zip(p.loop_indices, p.vertices):
                col, row = uvf(*SI.to_real(*me.vertices[vi].co)); lay.data[li].uv = (col / W, 1 - row / H)
            break
    print('photo faces', ob.name, ref_name, n_set)

def lin(v, v0, v1, p0, p1): return p0 + (v - v0) / (v1 - v0) * (p1 - p0)

DASH_REGIONS = [
    # the centre stack face: vents, hazard, climate strip, the controls below (photo rows 410-640)
    (lambda c, n: abs(c[1]) < 0.19 and c[0] > 1.97 and n[0] > 0.35 and 1.00 < c[2] < 1.27,
     lambda d, y, z: (lin(y, 0.165, -0.165, 700, 1030), lin(z, 1.25, 1.00, 410, 640))),
    # the console top: shifter, tray, cupholders (photo rows 640-941)
    (lambda c, n: abs(c[1]) < 0.16 and 2.05 < c[0] < 2.66 and n[2] > 0.6,
     lambda d, y, z: (lin(y, 0.15, -0.15, 705, 1025), lin(d, 2.10, 2.62, 640, 941))),
    # the passenger side of the dash: the dark band with its outer vent, the beige face with the glovebox
    (lambda c, n: c[1] < -0.17 and n[0] > 0.30 and 0.88 < c[2] < 1.27,
     lambda d, y, z: (lin(y, -0.17, -0.885, 1035, 1545), lin(z, 1.27, 0.88, 335, 700))),
]
BENCH_REGIONS = [
    (lambda c, n: n[0] < -0.30 and 0.95 < c[2] < 1.55,                       # backrest fronts
     lambda d, y, z: (lin(y, -0.70, 0.70, 291, 1381), lin(z, 0.95, 1.55, 640, 185))),
    (lambda c, n: n[0] < -0.30 and c[2] >= 1.55,                             # headrests
     lambda d, y, z: (lin(y, -0.70, 0.70, 291, 1381), lin(z, 1.55, 1.76, 190, 30))),
    (lambda c, n: n[2] > 0.60 and 0.82 < c[2] < 0.98,                         # cushion tops
     lambda d, y, z: (lin(y, -0.72, 0.72, 96, 1576), lin(d, 3.13, 3.60, 770, 625))),
    (lambda c, n: n[0] < -0.45 and c[2] <= 0.90,                             # cushion fronts
     lambda d, y, z: (lin(y, -0.72, 0.72, 76, 1596), lin(z, 0.90, 0.62, 770, 900))),
]

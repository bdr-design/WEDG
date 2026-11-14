"""One skin over the pieces: the animal as a single closed surface, its texture painted on it.

1. Each group of pieces (the trunk, the neck, the head with its jaw, nose and eyes, each ear, each leg, each paw with
   its toes, the tail) is turned into a signed distance field on a voxel grid: its occupancy by the parity of vertical
   rays through the voxel columns, then the distance to the surface inside and out.
2. The groups are joined by a smooth union (the same blend as tool/camel3d/shape.py), each with its own radius, so the
   legs grow out of the trunk, the neck runs into the skull, the ears out of the skull's corners.
3. Marching cubes gives the surface (scikit-image, as the camel); it is smoothed a little and decimated to the
   triangle budget (Blender's collapse decimation), unwrapped (Blender's smart projection, the head given more of the
   texture), and painted texel by texel: each texel is found on the skin, then on the nearest piece of the posed
   animal, then at the same place on the standing animal, where the coat's marks are laid out.
4. The normal map is the fur's grain and the occlusion is baked into the colour (a few rays from each vertex).

Every step is deterministic: the same numbers give the same file.
"""
import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy import ndimage
from skimage import measure

SKIN_GROUPS_EXCLUDED = ('teeth', 'collar')


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def piece_arrays(pc):
    V = np.array([tuple(q) for q in pc.V], np.float64)
    T = np.array(pc.T, np.int64)
    return V, T


def voxelize(pieces, origin, vox, dims):
    """The union of closed pieces (mm) on a grid: a voxel is inside if an odd number of the pieces' surfaces cross
    the vertical ray below its centre (counted per piece, so overlapping pieces join)."""
    nx, ny, nz = dims
    occ = np.zeros((nx, ny, nz), bool)
    ox, oy, oz = origin
    for pc in pieces:
        V, T = piece_arrays(pc)
        cnt = np.zeros((nx, ny, nz + 1), np.int16)
        A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        lo = np.minimum(np.minimum(A, B), C)
        hi = np.maximum(np.maximum(A, B), C)
        i0 = np.ceil((lo[:, 0] - ox) / vox - 0.5).astype(int)
        i1 = np.floor((hi[:, 0] - ox) / vox - 0.5).astype(int)
        j0 = np.ceil((lo[:, 1] - oy) / vox - 0.5).astype(int)
        j1 = np.floor((hi[:, 1] - oy) / vox - 0.5).astype(int)
        I, J, K = [], [], []
        for t in range(len(T)):
            a0, a1, b0, b1 = max(i0[t], 0), min(i1[t], nx - 1), max(j0[t], 0), min(j1[t], ny - 1)
            if a0 > a1 or b0 > b1:
                continue
            a, b, c = A[t], B[t], C[t]
            area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
            if abs(area) < 1e-12:
                continue
            ii, jj = np.meshgrid(np.arange(a0, a1 + 1), np.arange(b0, b1 + 1), indexing='ij')
            px = ox + (ii + 0.5) * vox
            py = oy + (jj + 0.5) * vox
            w1 = ((px - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (py - a[1])) / area
            w2 = ((b[0] - a[0]) * (py - a[1]) - (px - a[0]) * (b[1] - a[1])) / area
            w0 = 1 - w1 - w2
            ins = (w0 > 0) & (w1 > 0) & (w2 > 0)
            if not ins.any():
                continue
            z = w0[ins] * a[2] + w1[ins] * b[2] + w2[ins] * c[2]
            k = np.clip(np.ceil((z - oz) / vox - 0.5).astype(int), 0, nz)
            I.append(ii[ins])
            J.append(jj[ins])
            K.append(k)
        if I:
            np.add.at(cnt, (np.concatenate(I), np.concatenate(J), np.concatenate(K)), 1)
            occ |= (np.cumsum(cnt, axis=2)[:, :, :nz] % 2).astype(bool)
    return occ


def sdf_of(occ, vox):
    if not occ.any():
        return np.full(occ.shape, 1e3, np.float32)
    out = ndimage.distance_transform_edt(~occ)
    ins = ndimage.distance_transform_edt(occ)
    return ((out - ins) * vox).astype(np.float32)


# the blend radius (mm, as a fraction of the withers height) each group joins the rest with
BLEND = {'cleft': 0.004, 'torso': 0.0, 'neck': 0.045, 'head': 0.040, 'tail': 0.018, 'fore': 0.034, 'hind': 0.040, 'paw': 0.012, 'ear': 0.008}


def groups_of(parts):
    out = {}
    for k in sorted(parts):
        for pc in parts[k]:
            g = getattr(pc, 'group', k)
            if g in SKIN_GROUPS_EXCLUDED:
                continue
            out.setdefault(g, []).append(pc)
    order = ['torso', 'neck', 'head', 'ear_l', 'ear_r', 'tail', 'fore_l', 'fore_r', 'hind_l', 'hind_r',
             'paw_fl', 'paw_fr', 'paw_hl', 'paw_hr']
    return [(g, out[g]) for g in order if g in out] + [(g, v) for g, v in sorted(out.items()) if g not in order]


def field(parts, H, vox):
    """The whole animal's signed distance (mm) on a grid: (F, origin, vox)."""
    groups = groups_of(parts)
    allv = np.concatenate([piece_arrays(pc)[0] for _, pcs in groups for pc in pcs])
    margin = 0.06 * H
    lo = allv.min(0) - margin
    hi = allv.max(0) + margin
    dims = np.ceil((hi - lo) / vox).astype(int)
    F = np.full(tuple(dims), 1e3, np.float32)
    sharp = np.zeros(tuple(dims), np.float32)      # where the field is kept unblurred (the paws: toes and clefts)
    for g, pcs in groups:
        k = BLEND[g.split('_')[0]] * H
        gv = np.concatenate([piece_arrays(pc)[0] for pc in pcs])
        pad = k * 2.5 + 4 * vox
        g0 = np.maximum(np.floor((gv.min(0) - pad - lo) / vox).astype(int), 0)
        g1 = np.minimum(np.ceil((gv.max(0) + pad - lo) / vox).astype(int), dims)
        sub = lo + g0 * vox
        occ = voxelize(pcs, sub, vox, tuple(g1 - g0))
        d = sdf_of(occ, vox)
        sl = tuple(slice(a, b) for a, b in zip(g0, g1))
        if g.startswith('cleft'):
            F[sl] = -smin(-F[sl], d, k)                 # cut away: the clefts between the toes
        else:
            F[sl] = np.minimum(F[sl], d) if k == 0 else smin(F[sl], d, k)
        if g.startswith('paw'):
            c0 = np.maximum(np.floor((gv.min(0) - lo) / vox).astype(int), 0)
            c1 = np.minimum(np.ceil((gv.max(0) - lo) / vox).astype(int), dims)
            sharp[tuple(slice(a, b) for a, b in zip(c0, c1))] = 1.0
    sharp = ndimage.gaussian_filter(sharp, 3.0)
    return F, lo, vox, sharp


def surface(F, origin, vox, blur=0.9, sharp=None):
    """Marching cubes on the lightly blurred field (kept sharp where [sharp] is 1): vertices (mm) and triangles."""
    Fb = ndimage.gaussian_filter(F, blur)
    # the paws less blurred (not raw: an unblurred field steps with the voxels, and the decimation spends its
    # triangles on the steps)
    F = Fb if sharp is None else Fb * (1 - sharp) + ndimage.gaussian_filter(F, PAW_BLUR) * sharp
    verts, faces, _, _ = measure.marching_cubes(F, 0.0, spacing=(vox, vox, vox))
    verts = verts + origin
    # drop the small shells: hollows left inside the body where pieces meet (never seen)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = len(verts)
    e = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]]])
    k, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    if k > 1:
        fl = lab[faces[:, 0]]
        cnt = np.bincount(fl, minlength=k)
        keep = cnt[fl] >= 0.02 * len(faces)
        faces = faces[keep]
        used = np.unique(faces)
        remap = np.full(n, -1, np.int64)
        remap[used] = np.arange(len(used))
        verts, faces = verts[used], remap[faces]
    return verts, faces


def to_blender(name, verts_mm, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in (verts_mm * 0.001)], [], [tuple(int(i) for i in f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def apply_mods(o, mods):
    """Apply modifiers through the evaluated mesh (no operators), in order."""
    for kind, props in mods:
        m = o.modifiers.new(kind, kind)
        for k, v in props.items():
            setattr(m, k, v)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    o.modifiers.clear()
    old = o.data
    o.data = me
    bpy.data.meshes.remove(old)
    return o


PAW_SPARE = 0.06          # the close skin's decimation spares the paws a little (their weight 1 - this) ...
HEAD_SPARE = 0.04         # ... and the head more: the face matters more than the paws at every distance
PAW_BLUR = 0.5


def skin_mesh(name, parts, H, vox, targets, ground=True, head=None):
    """The skin at each target triangle count: {target: Blender object}."""
    F, lo, vox, sharp = field(parts, H, vox)
    verts, faces = surface(F, lo, vox, sharp=sharp)
    if ground:
        verts[:, 2] = np.maximum(verts[:, 2], 0.0)      # pressed flat where it touches the ground
    base = to_blender(name + '_hi', verts, faces)
    # the paws kept out of the smoothing and spared by the decimation (their toes would melt into mittens)
    idx = np.clip(np.round((verts - lo) / vox).astype(int), 0, np.array(sharp.shape) - 1)
    wp = sharp[idx[:, 0], idx[:, 1], idx[:, 2]]
    vg = base.vertex_groups.new(name='body')
    body = 1.0 - PAW_SPARE * np.clip(wp * 1.5, 0, 1)
    if head is not None:
        hc, hr = head
        dh = np.linalg.norm(verts - np.array(hc), axis=1)
        body -= HEAD_SPARE * np.clip((1.3 * hr - dh) / (0.4 * hr), 0, 1)
    for w in np.unique(np.round(body, 2)):
        sel = np.nonzero(np.round(body, 2) == w)[0].tolist()
        if w > 0:
            vg.add(sel, float(w), 'REPLACE')
    apply_mods(base, [('SMOOTH', dict(factor=0.5, iterations=2, vertex_group='body'))])
    out = {}
    nf = len(base.data.polygons)
    for t in targets:
        o = base.copy()
        o.name = f'{name}_{t}'
        bpy.context.scene.collection.objects.link(o)
        # the guard makes the decimation stop short of its ratio: the ratio is corrected until the count is met
        ratio = min(1.0, t / nf)
        for _ in range(6):
            trial = base.data.copy()
            o.data = trial
            props = dict(decimate_type='COLLAPSE', ratio=ratio, use_collapse_triangulate=True)
            if t > 3000:
                props.update(vertex_group='body', vertex_group_factor=1.0)
            apply_mods(o, [('DECIMATE', props)])
            got = len(o.data.polygons)
            if abs(got - t) <= 0.01 * t:
                break
            ratio = min(1.0, ratio * t / got)
        if ground:
            me = o.data
            co = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get('co', co)
            co = co.reshape(-1, 3)
            co[:, 2] = np.maximum(co[:, 2], 0.0)       # (the decimation can push a vertex of the contact under it)
            me.vertices.foreach_set('co', co.ravel())
            me.update()
        out[t] = o
    bpy.data.objects.remove(base)
    return out, (len(verts), len(faces))


def add_pieces(o, pieces):
    """Separate closed pieces (the collar and its ring, the teeth) added to the skin's mesh: returns the first new
    face's index."""
    me = o.data
    n0v, n0f = len(me.vertices), len(me.polygons)
    vs, fs = [], []
    for pc in pieces:
        base = n0v + len(vs)
        vs.extend((q.x * 0.001, q.y * 0.001, q.z * 0.001) for q in pc.V)
        fs.extend((base + a, base + b, base + c) for a, b, c in pc.T)
    if not vs:
        return n0f
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    nv = [bm.verts.new(v) for v in vs]
    bm.verts.ensure_lookup_table()
    for f in fs:
        bm.faces.new([bm.verts[i] for i in f])
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n0f


# ------------------------------------------------------------------ arrays out of a Blender mesh
def mesh_arrays(o):
    me = o.data
    nv = len(me.vertices)
    V = np.empty(nv * 3)
    me.vertices.foreach_get('co', V)
    V = V.reshape(-1, 3) * 1000.0
    loops = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get('vertex_index', loops)
    tot = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get('loop_total', tot)
    assert (tot == 3).all()
    Fv = loops.reshape(-1, 3)
    return V, Fv


def vertex_normals(V, Fv):
    fn = np.cross(V[Fv[:, 1]] - V[Fv[:, 0]], V[Fv[:, 2]] - V[Fv[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, Fv[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


MARGIN = 0.006       # the projection's margin between islands; the packer's own is 0.004 of an island's scale


def unwrap(o, head_c_mm, head_r_mm, gain=2.0):
    """Smart projection on a copy whose head is swollen [gain] times (so the head gets that much more texture per
    millimetre), the texture places copied back by loop."""
    tmp = o.copy()
    tmp.data = o.data.copy()
    bpy.context.scene.collection.objects.link(tmp)
    me = tmp.data
    V = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', V)
    V = V.reshape(-1, 3)
    c = np.array(head_c_mm) * 0.001
    r = head_r_mm * 0.001
    d = np.linalg.norm(V - c, axis=1)
    w = np.clip((1.6 * r - d) / (0.6 * r), 0, 1)
    w = w * w * (3 - 2 * w)
    s = 1 + (gain - 1) * w
    V2 = c + (V - c) * s[:, None]
    me.vertices.foreach_set('co', V2.ravel())
    me.update()
    for ob in list(bpy.context.scene.objects):
        ob.select_set(False)
    bpy.context.view_layer.objects.active = tmp
    tmp.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(62), island_margin=MARGIN, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = np.empty(len(me.loops) * 2, np.float32)
    me.uv_layers.active.data.foreach_get('uv', uv)
    # where the decimated skin folds over itself (a sliver turned under its neighbour) the projection overlaps: one
    # face of each overlapping pair is moved to a free place of its own in the layout
    V3 = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get('co', V3)
    V3 = V3.reshape(-1, 3)
    Fv = np.empty(len(o.data.loops), np.int64)
    o.data.loops.foreach_get('vertex_index', Fv)
    Fv = Fv.reshape(-1, 3)
    uv = uv.reshape(-1, 3, 2)
    for k in range(8):
        bad = uv_overlaps(uv)
        if not bad:
            break
        relocate(uv, sorted({max(p) for p in bad}), V3, Fv)
    uv = uv.reshape(-1)
    if not o.data.uv_layers:
        o.data.uv_layers.new(name='uv')
    o.data.uv_layers[0].data.foreach_set('uv', uv)
    bpy.data.objects.remove(tmp)
    return uv.reshape(-1, 3, 2)


def relocate(uv, faces, V, Fv, size=512):
    """Give each of [faces] its own small island in a free part of the layout, at the layout's own texture density."""
    tri = V[Fv]
    a3 = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1).sum()
    e = uv[:, 1] - uv[:, 0]
    f = uv[:, 2] - uv[:, 0]
    a2 = 0.5 * np.abs(e[:, 0] * f[:, 1] - e[:, 1] * f[:, 0]).sum()
    k = math.sqrt(a2 / a3)                                # layout units per metre
    fid, _ = raster(uv, size)
    occ = fid >= 0
    m = 3                                                  # (a few texels round a moved face)
    for face in faces:
        a, b, c = tri[face]
        ex = (b - a) / max(np.linalg.norm(b - a), 1e-12)
        n = np.cross(b - a, c - a)
        n /= max(np.linalg.norm(n), 1e-12)
        ey = np.cross(n, ex)
        q = np.array([[0.0, 0.0], [(b - a) @ ex, (b - a) @ ey], [(c - a) @ ex, (c - a) @ ey]]) * k
        q -= q.min(0)
        busy = ndimage.binary_dilation(occ, iterations=m) if m else occ
        ii = np.pad(np.cumsum(np.cumsum(busy, 0), 1), ((1, 0), (1, 0)))
        sc = 1.0
        done = False
        while not done and sc > 0.05:
            # (where no place is free at the layout's density, the face is given a little less)
            w = int(math.ceil(q.max() * sc * size)) + 2 * m + 1
            win = ii[w:, w:] - ii[:-w, w:] - ii[w:, :-w] + ii[:-w, :-w]
            free = np.argwhere(win == 0)
            free = free[(free[:, 0] >= m) & (free[:, 1] >= m) & (free[:, 0] + w <= size - m) & (free[:, 1] + w <= size - m)]
            done = len(free) > 0
            if not done:
                sc *= 0.7
        if done:
            y, x = free[0]
            uv[face] = q * sc + (np.array([x, y]) + m) / size
            occ[y:y + w, x:x + w] = True
        if not done:
            raise SystemExit('no free place left in the texture layout for a face')


def uv_overlaps(UV, size=2048, eps=0.02):
    """The pairs of texture triangles that cover the same texels (inside each by more than [eps] of its own barycentric
    range, so shared edges do not count): an empty list when the layout is sound."""
    owner = np.full((size, size), -1, np.int64)
    bad = set()
    P = UV * size
    for t in range(len(P)):
        p = P[t]
        x0, y0 = np.floor(p.min(0)).astype(int)
        x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x0 > x1 or y0 > y1:
            continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-12:
            continue
        l1 = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0]) + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / d
        l2 = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0]) + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / d
        m = (l1 > eps) & (l2 > eps) & (1 - l1 - l2 > eps)
        ow = owner[y0:y1 + 1, x0:x1 + 1]
        clash = m & (ow >= 0)
        if clash.any():
            for o in np.unique(ow[clash]):
                bad.add((int(o), t))
        ow[m] = t
    return sorted(bad)


def raster(UV, size):
    """For each texel: the face it falls in (-1 if none) and its barycentric weights."""
    fid = np.full((size, size), -1, np.int64)
    bar = np.zeros((size, size, 3), np.float32)
    P = UV * size - 0.5                                   # texel centres at integer + 0.5
    for f in range(len(UV)):
        a, b, c = P[f]
        x0 = int(math.floor(min(a[0], b[0], c[0])))
        x1 = int(math.ceil(max(a[0], b[0], c[0])))
        y0 = int(math.floor(min(a[1], b[1], c[1])))
        y1 = int(math.ceil(max(a[1], b[1], c[1])))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x0 > x1 or y0 > y1:
            continue
        area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if abs(area) < 1e-12:
            continue
        xx, yy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w1 = ((xx - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (yy - a[1])) / area
        w2 = ((b[0] - a[0]) * (yy - a[1]) - (xx - a[0]) * (b[1] - a[1])) / area
        w0 = 1 - w1 - w2
        ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        ys, xs = yy[ins], xx[ins]
        fid[ys, xs] = f
        bar[ys, xs] = np.stack([w0[ins], w1[ins], w2[ins]], 1)
    return fid, bar


def fill(img, mask):
    """Every empty texel takes the nearest painted texel's value (so mipmaps never mix in the empty background)."""
    if mask.all():
        return img
    _, idx = ndimage.distance_transform_edt(~mask, return_indices=True)
    return img[idx[0], idx[1]]


def occlusion(V, VN, Fv, H):
    """Per vertex: the share of the sky seen (fixed directions, rays out to 0.2 H)."""
    bvh = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(int(i) for i in f) for f in Fv])
    n = 48
    k = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * k / n)
    th = math.pi * (1 + 5 ** 0.5) * k
    dirs = np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)
    reach = 0.2 * H
    ao = np.ones(len(V), np.float32)
    for i in range(len(V)):
        nrm = VN[i]
        cs = dirs @ nrm
        sel = cs > 0.05
        tot = 0.0
        vis = 0.0
        p = Vector(V[i] + nrm * 0.4)
        for d, c in zip(dirs[sel], cs[sel]):
            hit = bvh.ray_cast(p, Vector(d), reach)
            tot += c
            if hit[0] is None:
                vis += c
        ao[i] = vis / tot if tot > 0 else 1.0
    return ao


def material(name, col, nrm, rough=0.85):
    from common import image
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexImage')
    tc.image = image(name + '_color', col)
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = image(name + '_normal', nrm)
    tn.image.colorspace_settings.name = 'Non-Color'
    tc.extension = 'EXTEND'                 # written as clamp-to-edge: nothing wraps in from the far border
    tn.extension = 'EXTEND'
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.uv_map = 'uv'
    nt.links.new(tc.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    return m

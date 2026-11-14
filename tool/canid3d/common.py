"""What the birds share: lofted pieces with their own texture coordinates, the painted atlas, the files, the pictures.

Built in millimetres, written in metres. Axes: X forward (the bird's head), Z up, Y to the bird's left (its right side
is -Y). In the GLB (Y up) the head looks along +X as in the other models' files.

A mesh is made of pieces. Each piece is a list of triangles made here (no bmesh operation that could reorder them),
each corner with its place in its own block of the atlas (0..1 both ways), so the same code gives the same triangles.
"""
import json
import math
import os
import struct

import bpy  # (first: it brings mathutils)
import numpy as np
from mathutils import Vector

V3 = Vector


# ------------------------------------------------------------------ pieces
class Piece:
    def __init__(self, block):
        self.block = block
        self.V = []      # Vector
        self.T = []      # (i, j, k)
        self.UV = []     # ((u, v), (u, v), (u, v)) in the block, 0..1

    def vert(self, co):
        self.V.append(V3(co))
        return len(self.V) - 1

    def tri(self, a, b, c, ua, ub, uc):
        self.T.append((a, b, c))
        self.UV.append((ua, ub, uc))

    def volume(self):
        s = 0.0
        for a, b, c in self.T:
            s += self.V[a].dot(self.V[b].cross(self.V[c]))
        return s / 6.0

    def wound_consistently(self):
        """Whether the piece is closed and every triangle is wound the same way as its neighbours: each edge used
        once in each direction. With a positive volume that means every face looks out of the piece."""
        seen = {}
        for a, b, c in self.T:
            for e in ((a, b), (b, c), (c, a)):
                seen[e] = seen.get(e, 0) + 1
        return all(seen.get((j, i), 0) == k == 1 for (i, j), k in seen.items())

    def outward(self):
        """Every piece is closed: wind its triangles so the volume is positive (normals out)."""
        if self.volume() < 0:
            self.T = [(a, c, b) for a, b, c in self.T]
            self.UV = [(ua, uc, ub) for ua, ub, uc in self.UV]
        return self


class Sec:
    """One section of a loft: centre [c]; [u] and [v] its two axes (unit); half sizes [au] toward +u, [ad] toward -u,
    [bl] toward +v, [br] toward -v; [p] the squareness (2 an ellipse, more a rounded box); [bend] a vector added in
    proportion to (along u / its half size) squared (curves the section's ends that way)."""

    def __init__(self, c, u, v, au, ad=None, bl=None, br=None, p=2.0, bend=None, bendv=None):
        self.c, self.u, self.v = V3(c), V3(u).normalized(), V3(v).normalized()
        self.au = au
        self.ad = au if ad is None else ad
        self.bl = bl if bl is not None else au
        self.br = self.bl if br is None else br
        self.p = p
        self.bend = V3(bend) if bend is not None else None
        self.bendv = V3(bendv) if bendv is not None else None

    def point(self, th):
        c, s = math.cos(th), math.sin(th)
        a = self.au if c >= 0 else self.ad
        b = self.bl if s >= 0 else self.br
        x = math.copysign(abs(c) ** (2 / self.p), c) * a
        y = math.copysign(abs(s) ** (2 / self.p), s) * b
        q = self.c + self.u * x + self.v * y
        if self.bend is not None:
            q = q + self.bend * (x / max(self.au, self.ad)) ** 2
        if self.bendv is not None:
            q = q + self.bendv * (y / max(self.bl, self.br)) ** 2
        return q


def loft(block, secs, n, s=None, caps=(True, True), t0=0.0, s_range=(0.0, 1.0)):
    """Sections joined into a closed tube. Texture: along = [s] (per section, 0..1, default by length), around = the
    ring's place k / n (0 at +u, 0.25 at +v). [t0] turns where the ring starts (a fraction of a turn)."""
    pc = Piece(block)
    if s is None:
        L = [0.0]
        for a, b in zip(secs, secs[1:]):
            L.append(L[-1] + (b.c - a.c).length)
        tot = L[-1] or 1.0
        s = [x / tot for x in L]
    s = [s_range[0] + (s_range[1] - s_range[0]) * x for x in s]
    rings = []
    for sec in secs:
        rings.append([pc.vert(sec.point(2 * math.pi * (k / n + t0))) for k in range(n)])
    for i in range(len(secs) - 1):
        r0, r1 = rings[i], rings[i + 1]
        for k in range(n):
            k1 = (k + 1) % n
            t_a, t_b = k / n, (k + 1) / n
            pc.tri(r0[k], r0[k1], r1[k1], (s[i], t_a), (s[i], t_b), (s[i + 1], t_b))
            pc.tri(r0[k], r1[k1], r1[k], (s[i], t_a), (s[i + 1], t_b), (s[i + 1], t_a))
    for end, on in ((0, caps[0]), (-1, caps[1])):
        if not on:
            continue
        ring = rings[end]
        c = pc.vert(sum((pc.V[i] for i in ring), V3()) / n)
        for k in range(n):
            k1 = (k + 1) % n
            if end == 0:
                pc.tri(c, ring[k1], ring[k], (s[end], (k + 0.5) / n), (s[end], (k + 1) / n), (s[end], k / n))
            else:      # the far cap faces the other way round the ring, so both caps face out with the tube
                pc.tri(c, ring[k], ring[k1], (s[end], (k + 0.5) / n), (s[end], k / n), (s[end], (k + 1) / n))
    return pc.outward()


def frame(t, up):
    """Axes for a section across direction [t]: u is [up] made square to t, v = t x u (u x v = t)."""
    t = V3(t).normalized()
    u = (V3(up) - t * V3(up).dot(t))
    if u.length < 1e-6:
        u = V3((0, 0, 1)) - t * t.z
    u.normalize()
    return u, t.cross(u)


def path_secs(pts, sizes, up=(0, 0, 1), p=2.0):
    """Sections along a path [pts] (Vectors), each across the path's direction; sizes: (au, ad, bl, br) or a radius."""
    out = []
    for i, q in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        u, v = frame(b - a, up)
        sz = sizes[i]
        if not isinstance(sz, (tuple, list)):
            sz = (sz, sz, sz, sz)
        out.append(Sec(q, u, v, *sz, p=p))
    return out


def tube(block, pts, radii, n, up=(0, 0, 1), caps=(True, True), s_range=(0.0, 1.0)):
    return loft(block, path_secs(pts, radii, up), n, caps=caps, s_range=s_range)


def smooth_path(pts, n):
    """[n] points along a Catmull-Rom curve through [pts]."""
    pts = [V3(p) for p in pts]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    segs = len(pts) - 1
    out = []
    for i in range(n):
        f = i / (n - 1) * segs
        j = min(int(f), segs - 1)
        t = f - j
        p0, p1, p2, p3 = P[j], P[j + 1], P[j + 2], P[j + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def resample(rows, n):
    """[n] stations through a few given ones (the first column the place), every other column carried by a curve that
    never overshoots (monotone cubic). As in tool/weapon3d/akm.py."""
    rows = np.array(rows, float)
    x = rows[:, 0]
    xs = np.linspace(x[0], x[-1], n)
    out = [xs]
    h = np.diff(x)
    for c in range(1, rows.shape[1]):
        y = rows[:, c]
        d = np.diff(y) / h
        m = np.zeros_like(y)
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, len(y) - 1):
            m[i] = 0.0 if d[i - 1] * d[i] <= 0 else 2.0 / (1.0 / d[i - 1] + 1.0 / d[i])
        i = np.clip(np.searchsorted(x, xs, side='right') - 1, 0, len(x) - 2)
        t = (xs - x[i]) / h[i]
        out.append((2 * t**3 - 3 * t**2 + 1) * y[i] + (t**3 - 2 * t**2 + t) * h[i] * m[i] + (-2 * t**3 + 3 * t**2) * y[i + 1] + (t**3 - t**2) * h[i] * m[i + 1])
    return [tuple(float(v) for v in r) for r in np.array(out).T]


def bent_line(start, d_end, angle_of, step=2.0):
    """A centre line in the side view (x, z) from [start], [d_end] mm long, its direction at distance d being
    angle_of(d) degrees above the horizontal (forward = +x). Returns a function d -> (point, tangent)."""
    ds = np.arange(0.0, d_end + step, step)
    xs, zs = [start[0]], [start[1]]
    for a, b in zip(ds, ds[1:]):
        ang = math.radians(angle_of((a + b) / 2))
        xs.append(xs[-1] + (b - a) * math.cos(ang))
        zs.append(zs[-1] + (b - a) * math.sin(ang))
    xs, zs = np.array(xs), np.array(zs)

    def at(d):
        x = float(np.interp(d, ds, xs))
        z = float(np.interp(d, ds, zs))
        ang = math.radians(angle_of(d))
        return V3((x, 0, z)), V3((math.cos(ang), 0, math.sin(ang)))
    return at


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    return a + (b - a) * t


def angle_profile(knots):
    """A smooth angle (degrees) over distance from knots [(d, angle)...]: eased between knots."""
    def f(d):
        if d <= knots[0][0]:
            return knots[0][1]
        for (d0, a0), (d1, a1) in zip(knots, knots[1:]):
            if d <= d1:
                return mix(a0, a1, smoothstep(d0, d1, d))
        return knots[-1][1]
    return f


def mirror(pc):
    """A piece's mirror across the bird's middle (y -> -y), wound outward again. Its texture places are the same."""
    out = Piece(pc.block)
    out.V = [V3((q.x, -q.y, q.z)) for q in pc.V]
    out.T = list(pc.T)
    out.UV = list(pc.UV)
    return out.outward()


def transform(pc, mat):
    out = Piece(pc.block)
    out.V = [mat @ q for q in pc.V]
    out.T, out.UV = list(pc.T), list(pc.UV)
    return out.outward()


# ------------------------------------------------------------------ the atlas
class Atlas:
    """Blocks of one texture: name -> (u0, v0, u1, v1), v up (rows bottom to top, as glTF reads them flipped by the
    exporter: Blender's images and texture places both have v up)."""

    MARGIN = 0.03

    def __init__(self, blocks):
        self.blocks = blocks

    def place(self, block, uv):
        u0, v0, u1, v1 = self.blocks[block]
        mu, mv = (u1 - u0) * self.MARGIN, (v1 - v0) * self.MARGIN
        u = min(max(uv[0], 0.0), 1.0)
        v = min(max(uv[1], 0.0), 1.0)
        return (u0 + mu + u * (u1 - u0 - 2 * mu), v0 + mv + v * (v1 - v0 - 2 * mv))

    def paint(self, size, painters):
        """painters: block -> f(S, T) returning (rgb [h, w, 3], rough [h, w], occl [h, w]); S, T the block's own
        coordinates (0..1, clamped in the margin so mipmaps bleed the block's own colours)."""
        col = np.zeros((size, size, 3), np.float32)
        orm = np.zeros((size, size, 3), np.float32)
        orm[..., 0] = 1.0
        orm[..., 1] = 0.8
        for name, (u0, v0, u1, v1) in self.blocks.items():
            if name not in painters:
                continue
            x0, x1 = int(round(u0 * size)), int(round(u1 * size))
            y0, y1 = int(round(v0 * size)), int(round(v1 * size))
            w, h = x1 - x0, y1 - y0
            mu, mv = self.MARGIN, self.MARGIN
            px = (np.arange(w) + 0.5) / w
            py = (np.arange(h) + 0.5) / h
            S = np.clip((px - mu) / (1 - 2 * mu), 0, 1)[None, :].repeat(h, 0)
            T = np.clip((py - mv) / (1 - 2 * mv), 0, 1)[:, None].repeat(w, 1)
            rgb, rough, occ = painters[name](S, T)
            col[y0:y1, x0:x1] = rgb
            orm[y0:y1, x0:x1, 0] = occ
            orm[y0:y1, x0:x1, 1] = rough
        return np.clip(col, 0, 1), np.clip(orm, 0, 1)


class Noise:
    """Smooth value noise (bilinear between random lattice values), seeded: the same picture every run."""

    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)

    def __call__(self, X, Y, cell, amp=1.0):
        gx, gy = int(X.max() / cell) + 3, int(Y.max() / cell) + 3
        g = self.rng.random((gy, gx)).astype(np.float32)
        fx, fy = X / cell, Y / cell
        ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        ix, iy = np.clip(ix, 0, gx - 2), np.clip(iy, 0, gy - 2)
        a = g[iy, ix] * (1 - tx) + g[iy, ix + 1] * tx
        b = g[iy + 1, ix] * (1 - tx) + g[iy + 1, ix + 1] * tx
        return ((a * (1 - ty) + b * ty) - 0.5) * 2 * amp


def feathers(X, Y, w, l, stagger=0.5, jitter=0.3):
    """Rows of feathers on a surface in millimetres: X along the bird toward the tail (feathers point that way), Y
    across. Each feather about [w] wide, its tip about [l] behind the next row's, each row and feather shifted a
    little at random so the rows do not read as stripes. Returns (along, across, idx): along 0 at the feather's
    exposed base to 1 at its tip, across -1..1 at its edges, and a per-feather index for variety."""
    row = np.floor(X / l)
    roff = hash01(row, 11.0) * w
    off = (row % 2) * stagger * w + roff
    col = np.floor((Y + off) / w)
    idx = (row * 7919 + col * 104729) % 9973
    fy = ((Y + off) / w - col) * 2 - 1
    fx = X / l - row + (hash01(idx, 13.0) - 0.5) * jitter
    # a rounded tip: the feather's end is an arc, so its 'along' grows toward the sides
    along = np.clip(fx + 0.35 * fy ** 2, 0, 1.4)
    return along, fy, idx


def hash01(idx, salt):
    return ((np.sin(idx * 12.9898 + salt * 78.233) * 43758.5453) % 1.0).astype(np.float32)


def C(*rgb):
    return np.array(rgb, np.float32)


def lerp_col(a, b, t):
    t = np.asarray(t, np.float32)[..., None]
    return a * (1 - t) + b * t


def seg_dist(X, Y, p0, p1):
    """Distance of each (X, Y) from the segment p0-p1 (millimetres), and the place along it 0..1."""
    ax, ay = p0
    bx, by = p1
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1.0
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy)), t


# ------------------------------------------------------------------ meshes, materials, files
class WindingError(Exception):
    pass


def to_mesh(name, pieces, atlas):
    """Pieces joined into one Blender mesh (metres), its texture places in the atlas, every face smooth. Each piece
    is checked first: closed, wound consistently, positive volume (so drawn one-sided, nothing shows through)."""
    verts, faces, uvs = [], [], []
    for pc in pieces:
        if not pc.wound_consistently() or pc.volume() <= 0:
            raise WindingError(f'{name}: a {pc.block} piece is open or has faces wound inward')
        base = len(verts)
        verts.extend((q.x * 0.001, q.y * 0.001, q.z * 0.001) for q in pc.V)
        for (a, b, c), (ua, ub, uc) in zip(pc.T, pc.UV):
            faces.append((base + a, base + b, base + c))
            uvs.extend((atlas.place(pc.block, ua), atlas.place(pc.block, ub), atlas.place(pc.block, uc)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    lay = me.uv_layers.new(name='uv')
    lay.data.foreach_set('uv', np.array(uvs, np.float32).ravel())
    me.validate(clean_customdata=False)
    me.shade_smooth()
    me.update()
    return me


def image(name, rgb):
    size = rgb.shape[0]
    img = bpy.data.images.new(name, size, size, alpha=False)
    px = np.ones((size, size, 4), np.float32)
    px[..., :3] = rgb
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def material(name, col, orm):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True      # every piece is closed: one side to draw, in the shadow pass too
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexImage')
    tc.image = image(name + '_color', col)
    to = nt.nodes.new('ShaderNodeTexImage')
    to.image = image(name + '_orm', orm)
    to.image.colorspace_settings.name = 'Non-Color'
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tc.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(to.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = 0.0
    return m


def obj(name, me, mat, parent=None):
    o = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    return o


def empty(name, parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.02
    bpy.context.scene.collection.objects.link(e)
    e.parent = parent
    return e


def point(name, mm, parent, fwd=None, up=None):
    """A named point (millimetres). With [fwd] and [up] its axes are turned so its X is fwd and its Z up."""
    e = empty(name, parent)
    e.location = V3(mm) * 0.001
    if fwd is not None:
        x = V3(fwd).normalized()
        z = V3(up or (0, 0, 1))
        z = (z - x * z.dot(x)).normalized()
        y = z.cross(x)
        from mathutils import Matrix
        m = Matrix((x, y, z)).transposed()
        e.rotation_mode = 'QUATERNION'
        e.rotation_quaternion = m.to_quaternion()
    return e


def tris(o):
    return len(o.data.polygons)


def export(path, root):
    bpy.ops.object.select_all(action='DESELECT')
    for o in [root, *root.children_recursive]:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_image_format='AUTO', export_extras=False, export_materials='EXPORT')
    settle(path)


def settle(path):
    """The exporter writes a mesh's triangles in an order, and from a corner, that can differ from run to run (the same
    triangles, the same winding). Put each part's index list in one order, so the same code gives the same file byte
    for byte (as tool/weapon3d/akm.py does)."""
    raw = bytearray(open(path, 'rb').read())
    jlen = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(bytes(raw[20:20 + jlen]))
    bin0 = 20 + jlen + 8
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            acc = doc['accessors'][prim['indices']]
            view = doc['bufferViews'][acc['bufferView']]
            dt = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[acc['componentType']]
            at = bin0 + view.get('byteOffset', 0) + acc.get('byteOffset', 0)
            tri = np.frombuffer(bytes(raw[at:at + acc['count'] * np.dtype(dt).itemsize]), dt).reshape(-1, 3)
            first = tri.argmin(1)
            tri = np.stack([np.take_along_axis(tri, ((first + k) % 3)[:, None], 1)[:, 0] for k in range(3)], 1)
            tri = tri[np.lexsort((tri[:, 2], tri[:, 1], tri[:, 0]))]
            raw[at:at + tri.nbytes] = tri.astype(dt).tobytes()
    open(path, 'wb').write(bytes(raw))


def glb_report(path):
    """Triangles per mesh and the textures' sizes, read back from the written file."""
    raw = open(path, 'rb').read()
    jlen = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + jlen])
    t = {}
    for node in doc.get('nodes', []):
        if 'mesh' in node:
            m = doc['meshes'][node['mesh']]
            t[node['name']] = sum(doc['accessors'][p['indices']]['count'] // 3 for p in m['primitives'])
    imgs = []
    bin0 = 20 + jlen + 8
    for im in doc.get('images', []):
        view = doc['bufferViews'][im['bufferView']]
        data = raw[bin0 + view.get('byteOffset', 0): bin0 + view.get('byteOffset', 0) + view['byteLength']]
        w, h = struct.unpack('>II', data[16:24]) if data[:4] == b'\x89PNG' else (0, 0)
        imgs.append((im.get('name', ''), w, h))
    return t, imgs, len(raw)


# ------------------------------------------------------------------ pictures
class Studio:
    """A grey studio: a soft key from the front left above, a fill, a rim from behind; AgX so pale plumage keeps its
    detail. Cycles at few samples while working, more for the final set."""

    def __init__(self, out, samples=32, ground=True, ground_col=(0.42, 0.38, 0.33)):
        sc = bpy.context.scene
        self.sc, self.out = sc, out
        sc.render.engine = 'CYCLES'
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.render.film_transparent = False
        try:
            sc.view_settings.view_transform = 'AgX'
            sc.view_settings.look = 'None'
        except TypeError:
            sc.view_settings.view_transform = 'Filmic'
        sc.view_settings.exposure = 0.0
        w = bpy.data.worlds.new('w')
        w.use_nodes = True
        w.node_tree.nodes['Background'].inputs[0].default_value = (0.70, 0.72, 0.76, 1)
        w.node_tree.nodes['Background'].inputs[1].default_value = 0.35
        sc.world = w
        self.lights = []
        self.cam_d = bpy.data.cameras.new('cam')
        self.cam = bpy.data.objects.new('cam', self.cam_d)
        sc.collection.objects.link(self.cam)
        sc.camera = self.cam
        self.ground = None
        if ground:
            me = bpy.data.meshes.new('ground')
            r = 30.0
            me.from_pydata([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)], [], [(0, 1, 2, 3)])
            g = bpy.data.objects.new('ground', me)
            mat = bpy.data.materials.new('ground')
            mat.use_nodes = True
            b = mat.node_tree.nodes['Principled BSDF']
            b.inputs['Base Color'].default_value = (*ground_col, 1)
            b.inputs['Roughness'].default_value = 0.95
            me.materials.append(mat)
            sc.collection.objects.link(g)
            self.ground = g

    def light(self, kind, loc, energy, at, size=1.0):
        d = bpy.data.lights.new(kind, kind)
        d.energy = energy
        if kind == 'AREA':
            d.size = size
        o = bpy.data.objects.new(kind, d)
        o.location = loc
        self.sc.collection.objects.link(o)
        look(o, at)
        self.lights.append(o)
        return o

    def rig_lights(self, at, dist=1.6, scale=1.0):
        for l in self.lights:
            bpy.data.objects.remove(l)
        self.lights = []
        at = V3(at)
        k = dist * dist * scale
        self.light('AREA', at + V3((0.55, 0.85, 0.75)) * dist, 18 * k, at, 1.2 * dist)       # key: front, the bird's left, above
        self.light('AREA', at + V3((-0.6, 0.7, 0.2)) * dist, 10 * k, at, 1.5 * dist)        # fill
        self.light('AREA', at + V3((-0.7, -0.8, 0.6)) * dist, 18 * k, at, 0.8 * dist)       # rim from behind
        self.light('AREA', at + V3((0.0, 0.0, 1.0)) * dist, 8 * k, at, 1.5 * dist)          # sky

    def shot(self, name, loc, at, lens=60, ortho=None, res=(1200, 800)):
        self.cam.location = V3(loc)
        look(self.cam, at)
        self.cam_d.type = 'ORTHO' if ortho else 'PERSP'
        if ortho:
            self.cam_d.ortho_scale = ortho
        self.cam_d.lens = lens
        self.cam_d.clip_start = 0.01
        self.sc.render.resolution_x, self.sc.render.resolution_y = res
        self.sc.render.resolution_percentage = 100
        path = os.path.join(self.out, name + '.png')
        self.sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        return path


def look(o, at):
    o.rotation_euler = (V3(at) - o.location).to_track_quat('-Z', 'Y').to_euler()


def font(size):
    from PIL import ImageFont
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def ruler(path, px_per_mm, x0, y, length_mm, step_label=100):
    """A centimetre ruler drawn on an orthographic side picture: x0 its zero's pixel, y its line."""
    from PIL import Image, ImageDraw
    im = Image.open(path).convert('RGB')
    d = ImageDraw.Draw(im)
    f = font(20)
    ink = (30, 28, 26)
    d.line((x0, y, x0 + length_mm * px_per_mm, y), fill=ink, width=2)
    for mm in range(0, int(length_mm) + 1, 10):
        x = x0 + mm * px_per_mm
        h = 20 if mm % step_label == 0 else 13 if mm % 50 == 0 else 7
        d.line((x, y, x, y - h), fill=ink, width=2)
        if mm % step_label == 0:
            d.text((x - 8, y + 5), str(mm // 10), fill=ink, font=f)
    d.text((x0 + length_mm * px_per_mm + 12, y - 10), 'cm', fill=ink, font=f)
    im.save(path)


def to_jpeg(png, jpg, quality=88):
    from PIL import Image
    Image.open(png).convert('RGB').save(jpg, quality=quality, optimize=True)
    os.remove(png)

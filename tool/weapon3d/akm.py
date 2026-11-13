"""The Kalashnikov (AKM pattern) built by code at its real size: the rifle as a herder keeps it.

    python akm.py OUT_DIR            # writes OUT_DIR/akm.glb, akm_lod1.glb and akm.blend, prints the measures
    python akm.py OUT_DIR render     # and the pictures (akm_right.png, ...)

Blender is the `bpy` module. Everything is made here: the shape from the dimensions in README.md, one 512 px colour
texture and one roughness/metal texture painted with numpy, no downloaded mesh or picture.

Axes: X along the rifle (the butt at 0, the muzzle at 880 mm), Z up, Y across; the rifle's right side (the selector and
charging handle) is -Y. Built in millimetres with the bore's axis at z = 0, written in metres.
"""
import math
import os
import sys

import bpy  # (first: it brings bmesh and mathutils)
import bmesh
import numpy as np
from mathutils import Matrix, Vector

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
RENDER = len(sys.argv) > 2 and sys.argv[2] == 'render'
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ the texture's blocks (u0, v0, u1, v1)
BLOCKS = {
    'wood': (0.0, 0.5, 1.0, 1.0),
    'oxide': (0.0, 0.0, 0.25, 0.5),
    'edge': (0.25, 0.0, 0.5, 0.25),
    'bright': (0.5, 0.0, 0.75, 0.25),
    'bakelite': (0.25, 0.25, 0.5, 0.5),
    'canvas': (0.5, 0.25, 0.75, 0.5),
    'bore': (0.75, 0.0, 1.0, 0.25),
}
BLOCK_ID = {k: i for i, k in enumerate(BLOCKS)}
ID_BLOCK = {i: k for k, i in BLOCK_ID.items()}
LENGTH = 880.0


def paint_textures(size=512):
    """The colour and the occlusion/roughness/metal pictures, by block. Rows run bottom to top (v up)."""
    rng = np.random.default_rng(7)
    col = np.zeros((size, size, 3), np.float32)
    orm = np.zeros((size, size, 3), np.float32)      # r occlusion (1), g roughness, b metal
    orm[..., 0] = 1.0
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size      # v, u

    def fine(scale, amp):      # fine tileless noise
        n = rng.random((size // scale + 1, size // scale + 1)).astype(np.float32)
        n = np.kron(n, np.ones((scale, scale), np.float32))[:size, :size]
        return (n - 0.5) * amp

    def block(name):
        u0, v0, u1, v1 = BLOCKS[name]
        return (xx >= u0) & (xx < u1) & (yy >= v0) & (yy < v1)

    # laminated birch under a red-brown shellac: thin layer lines along the length (along u), periodic in v so faces
    # mapped anywhere in the block join; darker where hands hold it (the handguard's swell, the stock's wrist: by x)
    m = block('wood')
    v = (yy - 0.5) / 0.5
    lines = 0.5 + 0.5 * np.sin(2 * np.pi * (v * 22 + 0.35 * np.sin(2 * np.pi * (xx * 3 + v * 2)) + 0.12 * np.sin(2 * np.pi * xx * 11)))
    lines = lines ** 3
    streak = fine(2, 0.10) + 0.6 * np.kron(rng.random((size // 64 + 1, size // 4 + 1)).astype(np.float32) - 0.5, np.ones((64, 4), np.float32))[:size, :size] * 0.12
    x_mm = xx * LENGTH
    held = np.exp(-((x_mm - 585) / 60) ** 2) * 0.30 + np.exp(-((x_mm - 222) / 28) ** 2) * 0.26
    base = np.array([0.34, 0.105, 0.035], np.float32)      # amber-red shellac over birch, darkened by years of handling
    dark = np.array([0.15, 0.045, 0.018], np.float32)
    w = (1 - 0.45 * lines)[..., None] * base + (0.45 * lines)[..., None] * dark
    w = w * (1 + streak[..., None]) * (1 - held[..., None])
    col[m] = w[m]
    orm[..., 1][m] = (0.42 + 0.10 * lines + 0.25 * held)[m]
    # black oxide steel: a deep satin black
    m = block('oxide')
    g = 0.040 + fine(1, 0.012) + fine(8, 0.008)
    col[m] = np.stack([g, g, g * 1.08], -1)[m]
    orm[..., 1][m] = (0.50 + fine(2, 0.08))[m]
    orm[..., 2][m] = 0.9
    # the edges every used rifle shows: the black worn thin to dark steel
    m = block('edge')
    g = 0.16 + fine(1, 0.06) + fine(4, 0.05)
    col[m] = np.stack([g, g, g * 1.03], -1)[m]
    orm[..., 1][m] = (0.42 + fine(2, 0.08))[m]
    orm[..., 2][m] = 1.0
    # bare bright steel: the bolt carrier, the muzzle, the selector's arc
    m = block('bright')
    g = 0.50 + fine(1, 0.07) + fine(4, 0.05)
    col[m] = np.stack([g, g, g * 1.02], -1)[m]
    orm[..., 1][m] = (0.34 + fine(2, 0.08))[m]
    orm[..., 2][m] = 1.0
    # the pistol grip: a dark red-brown phenolic, mottled, glossier than the wood
    m = block('bakelite')
    mot = np.kron(rng.random((size // 6 + 1, size // 6 + 1)).astype(np.float32), np.ones((6, 6), np.float32))[:size, :size]
    mot = 0.6 * mot + 0.4 * np.roll(mot, 3, 0)
    b = np.array([0.20, 0.050, 0.022], np.float32)[None, None, :] * (0.65 + 0.7 * mot[..., None])
    col[m] = b[m]
    orm[..., 1][m] = 0.30
    # the sling: khaki-olive canvas webbing
    m = block('canvas')
    weave = 0.5 + 0.5 * np.sin(2 * np.pi * xx * size / 3) * np.sin(2 * np.pi * yy * size / 3)
    c = np.array([0.30, 0.27, 0.15], np.float32)[None, None, :] * (0.85 + 0.2 * weave[..., None])
    col[m] = c[m]
    orm[..., 1][m] = 0.95
    m = block('bore')
    col[m] = 0.004
    orm[..., 1][m] = 0.9
    return np.clip(col, 0, 1), np.clip(orm, 0, 1)


def image(name, rgb):
    size = rgb.shape[0]
    img = bpy.data.images.new(name, size, size, alpha=False)
    px = np.ones((size, size, 4), np.float32)
    px[..., :3] = rgb
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


# ------------------------------------------------------------------ building pieces
class Build:
    """One mesh being built: each piece is made apart, its hard edges bevelled (the bevel's faces take the worn
    colour), then joined. [detail] 0 is the rifle in the hands, 1 the rifle seen slung on a walking figure."""

    def __init__(self, detail=0):
        self.detail = detail
        self.bm = bmesh.new()
        self.blk = self.bm.faces.layers.int.new('blk')

    def seg(self, n):      # segments round a tube, by detail
        return n if self.detail == 0 else max(5, n // 2)

    def piece(self):
        return bmesh.new()

    def add(self, pm, block, wear=None, bevel=0.0, min_angle=28):
        """Join piece [pm]: its faces take [block]; with [bevel] mm its hard edges are bevelled and those faces take
        [wear] ('edge' the black worn thin, 'bright' bare steel)."""
        bmesh.ops.remove_doubles(pm, verts=pm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(pm, faces=pm.faces)
        layer = pm.faces.layers.int.new('blk')
        for f in pm.faces:
            f[layer] = BLOCK_ID[block]
        if bevel and self.detail == 0:
            hard = [e for e in pm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(min_angle)]
            if hard:
                r = bmesh.ops.bevel(pm, geom=hard, offset=bevel, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
                for f in r['faces']:
                    f[layer] = BLOCK_ID[wear or block]
        me = bpy.data.meshes.new('piece')
        pm.to_mesh(me)
        pm.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    # --- shapes (all return nothing: they add to the piece [pm])
    @staticmethod
    def box(pm, x0, x1, y0, y1, z0, z1):
        r = bmesh.ops.create_cube(pm, size=1.0)
        for v in r['verts']:
            v.co = Vector((x0 + (v.co.x + 0.5) * (x1 - x0), y0 + (v.co.y + 0.5) * (y1 - y0), z0 + (v.co.z + 0.5) * (z1 - z0)))

    @staticmethod
    def prism(pm, pts, y0, y1):
        """A side outline [(x, z)...] given thickness from y0 to y1."""
        vs = [pm.verts.new((x, y0, z)) for x, z in pts]
        f = pm.faces.new(vs)
        r = bmesh.ops.extrude_face_region(pm, geom=[f])
        bmesh.ops.translate(pm, verts=[e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)], vec=(0, y1 - y0, 0))

    @staticmethod
    def prism_x(pm, pts, x0, x1):
        """A cross-section [(y, z)...] run along the rifle from x0 to x1."""
        vs = [pm.verts.new((x0, y, z)) for y, z in pts]
        f = pm.faces.new(vs)
        r = bmesh.ops.extrude_face_region(pm, geom=[f])
        bmesh.ops.translate(pm, verts=[e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)], vec=(x1 - x0, 0, 0))

    @staticmethod
    def tube(pm, a, b, r0, r1=None, n=12, caps=True):
        """A round bar from point a to point b."""
        a, b = Vector(a), Vector(b)
        d = b - a
        r = bmesh.ops.create_cone(pm, cap_ends=caps, cap_tris=False, segments=n, radius1=r0, radius2=r0 if r1 is None else r1, depth=d.length)
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        bmesh.ops.transform(pm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=r['verts'])

    @staticmethod
    def loft(pm, secs, n=12, cap0=True, cap1=True):
        """Rounded sections joined. Each: (x, z, angle of the section's long axis in the side view (deg; 90 is up),
        half length along it, half width across the rifle, squareness (2 an ellipse, more a rounded box))."""
        rings = []
        for (x, z, ang, h, w, p) in secs:
            ax = Vector((math.cos(math.radians(ang)), 0, math.sin(math.radians(ang))))
            ring = []
            for k in range(n):
                t = 2 * math.pi * (k + 0.5) / n
                c, s = math.cos(t), math.sin(t)
                a = math.copysign(abs(c) ** (2 / p), c) * h
                b = math.copysign(abs(s) ** (2 / p), s) * w
                ring.append(pm.verts.new(Vector((x, 0, z)) + ax * a + Vector((0, b, 0))))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(n):
                pm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
        if cap0:
            pm.faces.new(rings[0][::-1])
        if cap1:
            pm.faces.new(rings[-1])

    @staticmethod
    def strap(pm, path, y0, y1, t):
        """A band of thickness [t] bent along a side-view path [(x, z)...], from y0 to y1 across."""
        pts = [Vector((x, 0, z)) for x, z in path]
        inner, outer = [], []
        for i, p in enumerate(pts):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            d = (b - a).normalized()
            nrm = Vector((-d.z, 0, d.x)) * (t / 2)
            inner.append(p - nrm)
            outer.append(p + nrm)
        for i in range(len(pts) - 1):
            q = [inner[i], inner[i + 1], outer[i + 1], outer[i]]
            lo = [pm.verts.new((v.x, y0, v.z)) for v in q]
            hi = [pm.verts.new((v.x, y1, v.z)) for v in q]
            pm.faces.new(lo)
            pm.faces.new(hi[::-1])
            for k in range(4):
                pm.faces.new((lo[k], hi[k], hi[(k + 1) % 4], lo[(k + 1) % 4]))

    @staticmethod
    def ribbon(pm, path, half, y0, y1):
        """A flat webbing seen from the side: [half] its half width in the side view, from y0 to y1 thick."""
        pts = [Vector((x, 0, z)) for x, z in path]
        lo, hi = [], []
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            nrm = Vector((-d.z, 0, d.x)) * half
            lo.append(p - nrm)
            hi.append(p + nrm)
        for i in range(len(pts) - 1):
            for y, flip in ((y0, False), (y1, True)):
                q = [pm.verts.new((v.x, y, v.z)) for v in (lo[i], lo[i + 1], hi[i + 1], hi[i])]
                pm.faces.new(q[::-1] if flip else q)

    # --- finishing
    def mesh(self, name):
        bm = self.bm
        bmesh.ops.triangulate(bm, faces=bm.faces)
        uv = bm.loops.layers.uv.new('uv')
        for f in bm.faces:
            name_b = ID_BLOCK[f[self.blk]]
            u0, v0, u1, v1 = BLOCKS[name_b]
            mu, mv = (u1 - u0) * 0.04, (v1 - v0) * 0.04
            n = f.normal
            for lp in f.loops:
                co = lp.vert.co
                if name_b == 'wood':
                    # the layer lines run along the rifle: u is the place along it, v wraps round the section
                    u = min(max(co.x / LENGTH, 0.004), 0.996)
                    across = co.z if abs(n.y) > 0.55 else co.y
                    fr = (across / 46.0) % 1.0
                    lp[uv].uv = (u, v0 + mv + fr * (v1 - v0 - 2 * mv))
                else:
                    a = (co.x * 0.0131 + co.z * 0.0173 + co.y * 0.0071) % 1.0
                    b = (co.y * 0.0193 + co.z * 0.0117 + co.x * 0.0057) % 1.0
                    lp[uv].uv = (u0 + mu + a * (u1 - u0 - 2 * mu), v0 + mv + b * (v1 - v0 - 2 * mv))
        bmesh.ops.scale(bm, vec=(0.001, 0.001, 0.001), verts=bm.verts)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(32))
        return me


# ------------------------------------------------------------------ the rifle (millimetres; the sources in README.md)
RIGHT = -1      # the selector and charging handle are on -Y


def rifle(detail=0):
    b = Build(detail)
    hi = detail == 0
    N = b.seg

    # the fixed laminated stock: the straight comb a little under the bore's line, deep at the butt, slim at the wrist
    p = b.piece()
    b.loft(p, [(3, -68, 90, 57, 16.5, 4.0), (40, -63, 90, 52, 18.5, 3.4), (130, -41, 90, 36, 18, 3.0), (212, -14, 90, 25.5, 16.5, 3.0), (243, -11, 90, 24.5, 15.5, 3.4)], n=N(14))
    b.add(p, 'wood')
    p = b.piece()      # the steel butt plate
    b.loft(p, [(0, -68, 90, 58, 17.3, 4.0), (3.6, -68, 90, 58, 17.3, 4.0)], n=N(14))
    b.add(p, 'oxide', 'bright', 0.9)

    # the stamped receiver and its rear end
    p = b.piece()
    b.prism(p, [(240, -36), (252, -44), (470, -44), (470, 18), (240, 18)], -16.5, 16.5)
    b.add(p, 'oxide', 'edge', 0.8)
    # the ribbed stamped dust cover, its arch from the receiver's rails
    arch = [(16.5 * math.cos(t), 18 + 16.0 * math.sin(t)) for t in np.linspace(0, math.pi, N(10))]
    p = b.piece()
    b.prism_x(p, arch, 250, 440)
    b.add(p, 'oxide', 'edge', 0.7, min_angle=50)
    if hi:
        for x in (290, 327, 364, 401):      # its cross ribs
            p = b.piece()
            b.prism_x(p, [(17.3 * math.cos(t), 18 + 16.9 * math.sin(t)) for t in np.linspace(0.10, math.pi - 0.10, 9)], x, x + 6)
            b.add(p, 'oxide', 'edge', 0.5, min_angle=50)
        # the rivets of the front and rear trunnions and the three axis pins, each side
        for side in (1, -1):
            for (x, z, r) in [(448, 8, 2.4), (462, 8, 2.4), (448, -8, 2.4), (462, -8, 2.4), (455, -30, 2.4), (249, 4, 2.4), (249, -14, 2.4), (318, -12, 2.0), (339, -5, 2.0), (301, -9, 2.0), (392, -28, 2.6)]:
                p = b.piece()
                b.tube(p, (x, side * 16.4, z), (x, side * 17.3, z), r, n=8)
                b.add(p, 'oxide', 'edge', 0.3)
        # the bolt carrier's bare steel seen through the right side's slot
        p = b.piece()
        b.box(p, 366, 438, RIGHT * 17.0, RIGHT * 16.4, 6, 17.4)
        b.add(p, 'bright')
    # the charging handle, on the right, the bolt closed
    p = b.piece()
    b.prism(p, [(421, 8.5), (436, 8.5), (437, 16.5), (424, 17.5)], -40, -16.5) if RIGHT < 0 else None
    b.add(p, 'oxide', 'bright', 0.9)

    # the selector lever on the right, up at safe, with its finger tab; and its arc worn bright into the receiver
    if hi:
        p = b.piece()
        b.prism(p, [(261, 2), (263, -4), (270, -6), (276, -2), (300, 5), (364, 9), (364, 16), (300, 14), (268, 9)], RIGHT * 18.6, RIGHT * 17.2)
        b.add(p, 'oxide', 'edge', 0.4)
        p = b.piece()
        b.box(p, 356, 364, RIGHT * 25, RIGHT * 18.6, 9, 14)
        b.add(p, 'oxide', 'bright', 0.6)
        p = b.piece()      # the arc: a thin strip lying on the receiver's side
        c, r0, r1 = Vector((268, 0, 2)), 93.0, 95.0
        angs = np.linspace(math.radians(4), math.radians(-21), 8)
        ring = [(c.x + r * math.cos(a), c.z + r * math.sin(a)) for a in angs for r in (r0,)] + [(c.x + r1 * math.cos(a), c.z + r1 * math.sin(a)) for a in angs[::-1]]
        vs = [p.verts.new((x, RIGHT * 16.56, z)) for x, z in ring]
        p.faces.new(vs)
        b.add(p, 'bright')

    # the rear sight: its block ahead of the dust cover, the tangent leaf hinged at its front, the notch at the rear
    p = b.piece()
    b.prism(p, [(440, 18), (500, 18), (512, 26), (512, 34), (498, 40), (444, 40), (440, 34)], -11, 11)
    b.add(p, 'oxide', 'edge', 0.7)
    p = b.piece()
    b.prism(p, [(446, 40), (540, 37), (540, 40), (449, 44), (449, 50), (446, 50)], -5, 5)
    b.add(p, 'oxide', 'edge', 0.4)
    if hi:
        p = b.piece()      # the slider and its catch
        b.box(p, 500, 510, -9, 9, 37.5, 44.5)
        b.add(p, 'oxide', 'edge', 0.5)

    # the pistol grip (phenolic), raked back
    rake = math.radians(20)
    d = Vector((-math.sin(rake), 0, -math.cos(rake)))
    top = Vector((283, 0, -43))
    secs = []
    for t, fb, w in [(0, 24, 14.5), (14, 20.5, 14.5), (55, 19, 14), (88, 18.5, 13.5), (99, 16, 12.5)]:
        c = top + d * t
        secs.append((c.x, c.z, -20.0, fb, w, 2.7))      # the long axis front to back, square to the grip's rake
    p = b.piece()
    b.loft(p, secs, n=N(12))
    b.add(p, 'bakelite')

    # the trigger guard, the trigger and the magazine catch
    p = b.piece()
    b.strap(p, [(300, -44), (301, -62), (312, -73), (350, -74), (364, -64), (369, -44)], -6.5, 6.5, 1.6)
    b.add(p, 'oxide', 'edge', 0.3)
    p = b.piece()
    b.prism(p, [(315, -44), (322, -44), (320.5, -56), (315, -66), (311.5, -65), (315.5, -55)], -3, 3)
    b.add(p, 'oxide', 'edge', 0.4)
    p = b.piece()
    b.prism(p, [(369, -44), (377, -44), (378, -60), (372, -64), (369, -58)], -5, 5)
    b.add(p, 'oxide', 'edge', 0.4)

    # the 30-round steel magazine: its curve an arc, forward at the foot; ribs on its sides; the floor plate
    R, x_top, z_top, arc_len = 232.0, 405.0, -44.0, 172.0
    cx = x_top + R
    def on_arc(s):
        phi = s / R
        return cx - R * math.cos(phi), z_top - R * math.sin(phi), math.degrees(phi)
    secs = []
    for s in np.linspace(-6, arc_len, 9 if hi else 5):
        x, z, deg = on_arc(s)
        secs.append((x, z, deg, 33.0, 13.6, 7.0))      # 66 mm front to back, 27 mm wide
    p = b.piece()
    b.loft(p, secs, n=N(12))
    b.add(p, 'oxide', 'edge', 0.9, min_angle=40)
    x, z, deg = on_arc(arc_len)
    x2, z2, _ = on_arc(arc_len + 3.5)
    p = b.piece()
    b.loft(p, [(x, z, deg, 34.2, 14.6, 7.0), (x2, z2, deg, 34.2, 14.6, 7.0)], n=N(12))
    b.add(p, 'oxide', 'bright', 0.8, min_angle=40)
    if hi:
        for s in (62, 96, 130):      # the side ribs
            xa, za, da = on_arc(s)
            xb, zb, db = on_arc(s + 5)
            p = b.piece()
            b.loft(p, [(xa, za, da, 30.0, 14.7, 7.0), (xb, zb, db, 30.0, 14.7, 7.0)], n=12)
            b.add(p, 'oxide', 'edge', 0.5, min_angle=40)

    # the barrel, the gas tube above it, the cleaning rod under it
    p = b.piece()
    b.tube(p, (470, 0, 0), (846, 0, 0), 7.5, n=N(12))
    b.add(p, 'oxide')
    p = b.piece()
    b.tube(p, (498, 0, 22), (668, 0, 22), 8.2, n=N(10))
    b.add(p, 'oxide')
    if hi:
        p = b.piece()
        b.tube(p, (668, 0, -12.6), (853, 0, -12.6), 2.7, n=6)
        b.tube(p, (853, 0, -12.6), (861, 0, -12.6), 3.7, n=6)
        b.add(p, 'oxide', 'bright', 0.4)

    # the laminated handguards: the lower with its palm swells, the upper over the gas tube
    p = b.piece()
    b.loft(p, [(470, -10, 90, 20, 18, 3.4), (500, -10, 90, 20, 19, 3.2), (545, -10.5, 90, 20.5, 22.5, 3.0), (602, -10.5, 90, 20.5, 22.5, 3.0), (640, -10, 90, 19.5, 19.5, 3.2), (662, -10, 90, 19, 18.5, 3.4)], n=N(14))
    b.add(p, 'wood')
    p = b.piece()
    b.loft(p, [(512, 23, 90, 13.5, 13.5, 2.3), (640, 23, 90, 13.0, 13.0, 2.3)], n=N(12))
    b.add(p, 'wood')
    p = b.piece()      # the handguard's retainer
    b.box(p, 660, 668, -19.5, 19.5, -30, 10)
    b.add(p, 'oxide', 'edge', 0.6)

    # the gas block, slanted forward, with the bayonet lug under it
    p = b.piece()
    b.prism(p, [(664, -9), (700, -9), (705, -3), (692, 31), (664, 31)], -10, 10)
    b.add(p, 'oxide', 'edge', 0.8)
    if hi:
        p = b.piece()
        b.box(p, 688, 703, -5, 5, -18, -9)
        b.add(p, 'oxide', 'edge', 0.5)

    # the front sight: its tower, the two ears, the post between them
    p = b.piece()
    b.prism(p, [(806, -9.5), (842, -9.5), (842, 9.5), (836, 9.5), (831, 30), (813, 30), (809, 9.5), (806, 9.5)], -7.5, 7.5)
    b.add(p, 'oxide', 'edge', 0.7)
    for side in (1, -1):
        p = b.piece()
        b.prism(p, [(813, 30), (831, 30), (831, 45), (827, 52), (817, 52), (813, 45)], side * 4.6, side * 7.5)
        b.add(p, 'oxide', 'bright', 0.6)
    p = b.piece()
    b.tube(p, (822, 0, 30), (822, 0, 49), 1.3, n=6)
    b.add(p, 'oxide')

    # the slanted compensator: its lip low on the right, the bore dark inside it
    n = N(12)
    p = b.piece()
    lip = Vector((0, RIGHT * 0.5, -0.866))
    rear, front, inner = [], [], []
    for k in range(n):
        t = 2 * math.pi * k / n
        dirv = Vector((0, math.cos(t), math.sin(t)))
        rear.append(p.verts.new((846, 9.3 * dirv.y, 9.3 * dirv.z)))
        xf = 872.5 + 7.5 * dirv.dot(lip)
        front.append(p.verts.new((xf, 9.3 * dirv.y, 9.3 * dirv.z)))
        inner.append(p.verts.new((xf - 2.5, 4.4 * dirv.y, 4.4 * dirv.z)))
    for k in range(n):
        j = (k + 1) % n
        p.faces.new((rear[k], rear[j], front[j], front[k]))
        p.faces.new((front[k], front[j], inner[j], inner[k]))
    p.faces.new(rear[::-1])
    bore = p.faces.new(inner)
    b.add(p, 'oxide', 'bright', 0.8, min_angle=40)
    b.bm.faces.ensure_lookup_table()
    for f in b.bm.faces:      # the bore's disc is the one small face looking forward inside the compensator
        c = f.calc_center_median()
        if f[b.blk] == BLOCK_ID['oxide'] and c.x > 862 and abs(c.y) < 2.5 and abs(c.z) < 2.5 and f.normal.x > 0.5:
            f[b.blk] = BLOCK_ID['bore']

    # the sling's swivels: the front on the left of the retainer, the rear on the left of the stock
    for (x, z, y) in [(664, -20, 19.5), (72, -60, 18.5)]:
        p = b.piece()
        b.strap(p, [(x - 6, z + 5), (x - 6, z - 9), (x + 6, z - 9), (x + 6, z + 5)], y, y + 2.2, 2.0)
        b.add(p, 'oxide', 'edge', 0.3) if hi else b.add(p, 'oxide')
    return b


def sling(detail=0):
    """The canvas sling hanging slack along the left side, from the front swivel to the stock's."""
    b = Build(detail)
    a, c = Vector((664, 0, -26)), Vector((72, 0, -66))
    n = 14 if detail == 0 else 6
    path = []
    for i in range(n + 1):
        t = i / n
        q = a.lerp(c, t)
        path.append((q.x, q.z - 62 * math.sin(math.pi * t) ** 0.9))
    p = b.piece()
    b.ribbon(p, path, 15.0, 20.2, 22.0)
    b.add(p, 'canvas')
    if detail == 0:
        for (x, z) in (path[0], path[-1]):      # the steel hooks
            p = b.piece()
            b.box(p, x - 7, x + 7, 19.8, 22.4, z - 6, z + 6)
            b.add(p, 'oxide', 'edge', 0.4)
    return b


# ------------------------------------------------------------------ the scene, the files, the pictures
def material():
    col, orm = paint_textures()
    m = bpy.data.materials.new('akm')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexImage')
    tc.image = image('akm_color', col)
    to = nt.nodes.new('ShaderNodeTexImage')
    to.image = image('akm_orm', orm)
    to.image.colorspace_settings.name = 'Non-Color'
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tc.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(to.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


def obj(name, me, mat, parent=None):
    o = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    return o


def point(name, mm, parent):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.02
    e.location = Vector(mm) * 0.001
    e.parent = parent
    bpy.context.scene.collection.objects.link(e)
    return e


# where the rifle is held and carried (millimetres), for the figure's hands and the sling's ends
POINTS = {
    'grip_r': (270, 0, -92),          # the right hand, round the pistol grip
    'hand_l': (585, 0, -22),          # the left hand, under the lower handguard's swell
    'sling_front': (664, 21, -26),
    'sling_rear': (72, 20, -66),
    'muzzle': (880, 0, 0),
    'butt': (0, 0, -68),
}


def build_scene(detail):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mat = material()
    root = bpy.data.objects.new('akm' if detail == 0 else 'akm_lod1', None)
    bpy.context.scene.collection.objects.link(root)
    body = obj('akm_body', rifle(detail).mesh('akm_body'), mat, root)
    strap = obj('akm_sling', sling(detail).mesh('akm_sling'), mat, root)
    for k, v in POINTS.items():
        point(k, v, root)
    return root, body, strap


def measure(body, strap):
    def tris(o):
        return sum(len(p.vertices) - 2 for p in o.data.polygons)
    co = np.array([v.co[:] for v in body.data.vertices]) * 1000
    lo, hi = co.min(0), co.max(0)
    return {'tris_body': tris(body), 'tris_sling': tris(strap), 'length': hi[0] - lo[0], 'height': hi[2] - lo[2], 'width': hi[1] - lo[1], 'x0': lo[0], 'x1': hi[0], 'z0': lo[2], 'z1': hi[2]}


def export(path, root):
    bpy.ops.object.select_all(action='DESELECT')
    for o in [root, *root.children]:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_image_format='AUTO', export_extras=False, export_materials='EXPORT')


def render(root):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.62, 0.60, 0.57, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    sc.world = w
    def light(kind, loc, energy, size=1.0, rot=(0, 0, 0)):
        d = bpy.data.lights.new(kind, kind)
        d.energy = energy
        if kind == 'AREA':
            d.size = size
        o = bpy.data.objects.new(kind, d)
        o.location = loc
        o.rotation_euler = rot
        sc.collection.objects.link(o)
        return o
    key = light('AREA', (0.25, -1.2, 1.1), 260, 1.6)
    fill = light('AREA', (0.6, 1.3, 0.5), 120, 1.6)
    top = light('AREA', (0.44, 0.0, 1.4), 90, 2.0)
    cam_d = bpy.data.cameras.new('cam')
    cam = bpy.data.objects.new('cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = Vector((0.44, 0, -0.06))
    def look(o, at):
        o.rotation_euler = (Vector(at) - o.location).to_track_quat('-Z', 'Y').to_euler()
    for l in (key, fill, top):
        look(l, target)
    # a backdrop that fills every view
    bg = bpy.data.materials.new('bg')
    bg.use_nodes = True
    bg.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.50, 0.48, 0.45, 1)
    bg.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95
    def shot(name, loc, ortho=None, res=(2000, 800), at=target, lens=85):
        cam.location = loc
        look(cam, at)
        cam_d.type = 'ORTHO' if ortho else 'PERSP'
        if ortho:
            cam_d.ortho_scale = ortho
        cam_d.lens = lens
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = os.path.join(OUT, name)
        bpy.ops.render.render(write_still=True)
    shot('akm_right.png', (0.44, -3, -0.06), ortho=1.0)
    shot('akm_left.png', (0.44, 3, -0.06), ortho=1.0)
    shot('akm_top.png', (0.44, 0, 3), ortho=1.0, res=(2000, 400), at=(0.44, 0, 0))
    shot('akm_front.png', (3.5, 0, -0.06), ortho=0.42, res=(800, 800))
    shot('akm_three_quarter.png', (1.55, -1.35, 0.45), res=(2000, 1100), lens=70)
    shot('akm_close.png', (0.42, -0.62, 0.16), res=(2000, 1100), at=(0.40, 0, -0.03), lens=60)


for detail in (1, 0):
    root, body, strap = build_scene(detail)
    m = measure(body, strap)
    name = 'akm.glb' if detail == 0 else 'akm_lod1.glb'
    export(os.path.join(OUT, name), root)
    kb = os.path.getsize(os.path.join(OUT, name)) / 1024
    print(f"{name}: body {m['tris_body']} triangles, sling {m['tris_sling']}, length {m['length']:.1f} mm (x {m['x0']:.1f} to {m['x1']:.1f}), height {m['height']:.1f} mm (z {m['z0']:.1f} to {m['z1']:.1f}), width {m['width']:.1f} mm, file {kb:.0f} KB")
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, 'akm.blend')))
if RENDER:
    render(root)

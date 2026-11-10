"""Steps 2-5 parts: mirrors (photo frame, from the owner's photos), and the wheel arches and roof rails (real frame,
traced on the real side photo; see DIMENSIONS.md). x forward, y left, z up, metres."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
import wheels as WH
import realframe as RF
import outlines as O

def activate(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o

def rbox(name, centre, size, bevel, mat, segments=3, subdiv=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new('bv', 'BEVEL'); m.width = bevel; m.segments = segments; m.limit_method = 'NONE'; bpy.ops.object.modifier_apply(modifier='bv')
    if subdiv:
        m = o.modifiers.new('sd', 'SUBSURF'); m.levels = subdiv; bpy.ops.object.modifier_apply(modifier='sd')
    o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return o

def join(objs, name):
    activate(objs[0])
    for o in objs: o.select_set(True)
    bpy.ops.object.join(); o = bpy.context.active_object; o.name = name; return o

def mirrors(paint, glass, black):
    """Housing 0.30 m long, out to 1.10 m from the centre line, 1.34-1.58 m up (front and top photos), on an arm from the
    door's front corner; the mirror glass faces back."""
    out = []
    for s in (1, -1):
        h = rbox(f'mirror_housing{s}', (0.66, s * 1.005, 1.46), (0.26, 0.19, 0.22), 0.06, paint, subdiv=1)
        # taper the housing toward the door and toward the front
        for v in h.data.vertices:
            t = (abs(v.co.y) - 0.91) / 0.19
            v.co.z = 1.46 + (v.co.z - 1.46) * (0.82 + 0.18 * t)
            if v.co.x > 0.66: v.co.y = s * (0.91 + (abs(v.co.y) - 0.91) * (1 - 0.25 * (v.co.x - 0.66) / 0.13))
        g = rbox(f'mirror_glass{s}', (0.528, s * 1.01, 1.46), (0.012, 0.165, 0.185), 0.005, glass)
        yin = float(O.front_half(1.37, 0.70)) - 0.025          # the arm starts 25 mm inside the outline: the pane is set 8 mm in, and leans
        arm = rbox(f'mirror_arm{s}', (0.70, s * (yin + 0.965) / 2, 1.37), (0.16, 0.965 - yin, 0.05), 0.02, black)
        out.append(join([h, g, arm], f'mirror_{"L" if s > 0 else "R"}'))
    return out

# Roof rails, real frame, measured on the real side photo (along the car 4.343 mm/px, corrected about 27 px for the
# yaw between the rail and the hub): one continuous rail a side. It leaves the roof 0.0 m behind the car's centre, is at
# full height from -0.219 to -1.763 and meets the roof again at -1.880, with one foot in the middle at -1.09. The bar is
# 27 mm thick. The top line is a shallow arch: 1.909 at x -0.245, 1.9266 from -0.98 to -1.25, 1.912 at -1.70, which is
# 24 mm per metre squared ahead of the highest point and 40 behind it; the highest point is set to the official overall
# height, 1.925 m. The open slot under the bar ends at x -1.647 at the back (the rear foot is 0.23 m long).
# In plan (the owner's top photo, 3.05 mm/px): the bar is 16-18 px = 50 mm wide and the two rails close in toward the
# tail with the roof: centre line 0.538 m out at x 0.24, 0.532 at -0.03, 0.522 at -0.86, 0.505 at -1.41.
RAIL_X = (0.0, -0.219, -1.09, -1.763, -1.880)
RAIL_Y0, RAIL_TAPER, RAIL_W = 0.533, 0.020, 0.050
RAIL_BAR, RAIL_TOP = 0.027, RF.H
RAIL_PEAK_X, RAIL_ARCH = -1.10, (0.024, 0.040)   # the arch: where it is highest; metres lost per metre squared ahead, behind
RAIL_SLOT_REAR = -1.647                          # where the open slot under the bar ends at the back

def rail_y(x): return RAIL_Y0 + RAIL_TAPER * x

def rail_top(x): return RAIL_TOP - RAIL_ARCH[0 if x > RAIL_PEAK_X else 1] * (x - RAIL_PEAK_X) ** 2

def _smooth(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)

def roof_rails(shell, black):
    """Runs in the real frame, after the warp: the rails sit on the roof (found by ray cast) and top out at 1.925 m."""
    out = []; x0, x1, xm, x2, x3 = RAIL_X
    xs = np.linspace(x0, x3, 120)
    w = RAIL_W / 2                                               # (y offset, 0 foot .. 1 top): a rounded top
    sect = ((-w, 0.0), (-w, 0.45), (-0.72 * w, 0.90), (-0.36 * w, 1.0), (0.36 * w, 1.0), (0.72 * w, 0.90), (w, 0.45), (w, 0.0))
    for s in (1, -1):
        def roof(x, y):
            r = shell.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)))
            return r[1].z if r[0] else 1.86
        rc = np.array([roof(x, s * rail_y(x)) for x in xs])
        rise = np.array([min(_smooth((x0 - x) / (x0 - x1)), _smooth((x - x3) / (x2 - x3))) for x in xs])
        top = (rc + 0.006) * (1 - rise) + np.array([rail_top(x) for x in xs]) * rise
        # 1 where the bar stands clear of the roof, 0 at the three feet
        clear = np.array([min(_smooth((x1 - 0.02 - x) / 0.06), _smooth((x - RAIL_SLOT_REAR + 0.03) / 0.06), _smooth((abs(x - xm) - 0.04) / 0.05)) for x in xs])
        V, F = [], []
        for i, x in enumerate(xs):
            for dy, t in sect:
                foot = roof(x, s * (rail_y(x) + dy)) - 0.010
                zb = foot + clear[i] * (top[i] - RAIL_BAR - foot)
                V.append((x, s * (rail_y(x) + dy), zb + t * (top[i] - zb)))
        n = len(sect)
        for i in range(len(xs) - 1):
            for j in range(n):
                a = i * n + j; F.append([a, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j])
        F.append(list(range(n))); k = (len(xs) - 1) * n; F.append([k + j for j in reversed(range(n))])
        me = bpy.data.meshes.new(f'rail{s}'); me.from_pydata(V, [], F); me.update()
        o = bpy.data.objects.new(f'roof_rail_{"L" if s > 0 else "R"}', me); bpy.context.collection.objects.link(o)
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        me.materials.append(black)
        for p in me.polygons: p.use_smooth = True
        out.append(o)
        if s > 0:
            full = rise > 0.999; over = (top - rc)[full]
            print(f'roof rails: roof under the rail {rc[full].min():.3f}-{rc[full].max():.3f}, rail top {top[full].min():.4f}-{top.max():.4f}, '
                  f'{over.min() * 1000:.0f}-{over.max() * 1000:.0f} mm over the roof, gap {(over.min() - RAIL_BAR) * 1000:.0f}-{(over.max() - RAIL_BAR) * 1000:.0f} mm')
    return out

# Roof antenna (a fin on the centre line), real frame, from the owner's photos mapped to the real frame. The top photo
# has it from x -1.60 to -1.78 (0.18 m long), its body 63 mm wide on a base rim 81 mm wide, ending 4 cm ahead of the
# tailgate seam. The rear photo has it 73 mm tall and this wide at these heights over the roof: 78 mm at 10, 61 at 18,
# 38 at 33, 30.5 at 50, 25 at 60, 19 at 67. In the side photo its tip shows level with the rail tops, at x -1.74 to -1.80.
# FIN_RING is that outline from behind: (half width mm, height mm, 0 for the low pod .. 1 for the thin blade on it).
# Game choices (no photo shows them): the pod is widest two thirds of the way back, the blade four fifths.
FIN_X, FIN_PEAK_X, FIN_TOP = (-1.60, -1.78), -1.75, RF.H
FIN_RING = ((40.5, 0, 0), (40.5, 6, 0), (39, 10, 0), (30.5, 17, 0.15), (23, 25, 0.4), (19, 33, 0.65), (17, 40, 0.8),
            (15.2, 50, 0.9), (12.5, 60, 1), (9.5, 67, 1), (5.5, 71.5, 1), (0, 73, 1))
FIN_POD = 25.0                                    # mm: up to here the outline is the pod's, above it the blade's
FIN_WIDEST = (0.66, 0.80)                         # where along the fin the pod and the blade are widest (game choice)

def antenna(shell, mat):
    x0, x1 = FIN_X; n = 36; tp = (x0 - FIN_PEAK_X) / (x0 - x1)
    def roof(x, y):
        r = shell.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)))
        return r[1].z if r[0] else 1.85
    def plan(t, widest, q): return math.sin(math.pi * t ** (math.log(0.5) / math.log(widest))) ** q
    def h_pod(t): return math.sqrt(max(1 - abs(2 * t - 1) ** 4, 0.0))
    def h_blade(t): return 1 - (1 - t / tp) ** 1.6 if t < tp else math.sqrt(max(1 - ((t - tp) / (1 - tp)) ** 2, 0.0))
    ztop = FIN_RING[-1][1]
    # the tip is the official height: stretch the blade so that the highest station reaches it
    xp = FIN_PEAK_X; tall = (FIN_TOP - roof(xp, 0.0)) * 1000
    kb = (tall - FIN_POD * h_pod(tp)) / (ztop - FIN_POD)
    ts = [0.5 - 0.5 * math.cos(math.pi * (i + 0.5) / n) for i in range(n)]     # closer together at the two ends
    m = 2 * len(FIN_RING) - 1
    for _ in range(3):                             # the roof falls away under the fin, so settle the blade's stretch
        V = []
        for t in ts:
            x = x0 + (x1 - x0) * t; half = []
            for k, (hw, z, b) in enumerate(FIN_RING):
                y = hw * ((1 - b) * plan(t, FIN_WIDEST[0], 0.6) + b * plan(t, FIN_WIDEST[1], 0.5)) / 1000
                zz = (min(z, FIN_POD) * h_pod(t) + max(z - FIN_POD, 0.0) * kb * h_blade(t)) / 1000
                half.append((y, zz - (0.004 if k == 0 else 0.0)))
            ring = half + [(-y, z) for y, z in half[-2::-1]]
            V += [(x, y, roof(x, y) + z) for y, z in ring]
        kb -= (max(v[2] for v in V) - FIN_TOP) * 1000 / (ztop - FIN_POD)
    F = []
    for i in range(n - 1):
        for j in range(m - 1):
            F.append([i * m + j, i * m + j + 1, (i + 1) * m + j + 1, (i + 1) * m + j])
        F.append([i * m + m - 1, i * m, (i + 1) * m, (i + 1) * m + m - 1])                 # the underside
    F.append(list(range(m - 1, -1, -1))); F.append([(n - 1) * m + j for j in range(m)])    # the two small ends
    me = bpy.data.meshes.new('antenna'); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new('roof_antenna', me); bpy.context.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(50))
    zs = np.array([v[2] for v in V]); ys = np.array([abs(v[1]) for v in V])
    print(f'antenna: roof {roof(xp, 0.0):.4f} at the tip, top {zs.max():.4f}, {tall:.1f} mm tall, {2000 * ys.max():.1f} mm wide at the rim')
    return o

# Wheel openings. The wheels are the size the owner's photos draw them (his decision), and the real car's openings do
# not hold them: the real front opening tops out 0.862 m up, 15 mm over the bigger tyre. So the openings are the
# owner's photo's too: on 01_left, round each hub, where the dark of the wheel well ends and the paint begins, every
# 10 degrees (tools/archphoto.py; black against dark paint, so within about 15 mm). Each point is (metres behind the
# axle, metres up), from the front foot over the top to the rear foot, and it is the point's offset from the hub in
# the photo, unscaled, set on the model's hub: the wheel is the photo's size unscaled, so the opening round it is
# too. (Mapped with the body instead, the rear wheel sat 31 mm from the front of its opening and 90 from the back,
# where the photo has 79 and 48, and the gap over the tyres was 66 mm for the photo's 104.) Both openings top out
# 0.948 m up, 104 mm over the tyre.
ARCH_PTS = (
    ((-0.493, 0.20), (-0.493, 0.495), (-0.478, 0.582), (-0.452, 0.669), (-0.414, 0.755), (-0.360, 0.837), (-0.286, 0.904),
     (-0.192, 0.936), (-0.095, 0.945), (0.000, 0.948), (0.095, 0.948), (0.193, 0.939), (0.285, 0.901), (0.357, 0.834),
     (0.411, 0.753), (0.450, 0.668), (0.477, 0.582), (0.491, 0.495), (0.491, 0.20)),
    ((-0.507, 0.20), (-0.507, 0.497), (-0.487, 0.585), (-0.454, 0.670), (-0.409, 0.751), (-0.355, 0.831), (-0.285, 0.901),
     (-0.192, 0.935), (-0.095, 0.945), (0.000, 0.948), (0.095, 0.948), (0.195, 0.943), (0.290, 0.910), (0.359, 0.836),
     (0.407, 0.749), (0.447, 0.666), (0.466, 0.578), (0.477, 0.492), (0.477, 0.20)))
FLARE_W = (0.029, 0.041)          # the flare band's width over the top of the opening: front, rear. The owner's decision (10 Nov):
                                  # the openings follow the photo's wheels unscaled and stand 37 mm higher against the body than in
                                  # the photo, so the bands are thinned by that much and their tops stay where the photo has them
                                  # (0.977 and 0.989 m up: the photo's opening, mapped, plus the real photo's 66 and 78 mm)
FLARE_Y, FLARE_END_Z = 0.990, 0.50   # the flares are the widest point of the car: the official 1.980 m; they end 0.50 m up
# A flare's face is the top photo's outline (which along the openings is the flares): 0.985 over the wheels, and still
# 0.981 at the rear door, where the door skin behind it is 5 cm further in; at the tail end it comes in to 0.957.
# The official width is 1.980, 4 mm a side more than the photo's flares, and that is added all along. (Up to r22 a
# flare stood 26 mm proud of the body beside it, which was right only while the doors were as wide as the fenders.)
# how far in from the car's middle the wheel openings are cut, front and rear: the wheelhouses' inner walls. The rear
# one stands 35 mm inside the tyre's inner face (the spec's 1665 mm track and 265 mm tyre put that face 0.700 m out);
# the front one is left further in, for the tyre's swing when steered. Before r26 both were 0.60, which put the rear
# wells 0.1 m into the cabin, where the second row sits.
WELL_IN = (0.60, 0.665)
FLARE_OVER = 0.004
# The owner's decision (10 Nov, on r24's pictures): a flare stands no more than FLARE_PROUD out of the body beside it.
# That thins the rear flare's front leg, which on the photo's outline stood 44 to 64 mm proud of the rear door, like a
# fin. The door's skin comes out to meet it (outlines.REAR_BULGE), because the flare has to cover the tyre.
FLARE_PROUD = 0.028
TYRE_COVER = (0.970, 0.40)          # the tyre's face is 0.965 out (measured on the wheel's mesh); within 0.40 m of the hub the flare covers it by 5 mm

def arch_curve(i, offset=0.0, step=0.012):
    """The opening of arch i (0 front, 1 rear) as an array of model (x, z), from the front foot over the top to the rear
    foot, with its corners rounded, moved outward by offset."""
    p = np.asarray(ARCH_PTS[i], float)
    for _ in range(3):                                             # Chaikin corner cutting
        q, r = 0.75 * p[:-1] + 0.25 * p[1:], 0.25 * p[:-1] + 0.75 * p[1:]
        p = np.vstack([p[:1], np.column_stack([q, r]).reshape(-1, 2), p[-1:]])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; t = np.linspace(0, d[-1], int(d[-1] / step) + 1)
    p = np.column_stack([np.interp(t, d, p[:, 0]), np.interp(t, d, p[:, 1])])
    tg = np.gradient(p, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
    p = p + offset * np.column_stack([-tg[:, 1], tg[:, 0]])        # outward is to the left of the direction of travel
    return np.column_stack([WH.AXLE_X[i] - p[:, 0], p[:, 1]])

def arches(shell, paint, liner, flare_mat):
    """Cut each wheel opening from the shell to the outline from the owner's photo (ARCH_PTS), line it, and lay a flare band along
    its edge, its face on the top photo's outline (FLARE_OVER). Runs in the real frame."""
    # where the body is beside each flare, before the openings are cut
    body_y = {}
    for i in (0, 1):
        for s in (1, -1):
            ys = []
            for x, z in arch_curve(i, FLARE_W[i] + 0.03):
                r = shell.ray_cast(Vector((x, s * 2.0, max(z, 0.45))), Vector((0, -s, 0)))   # above the sill
                ys.append(abs(r[1].y) if r[0] else np.nan)
            ys = np.array(ys); ok = ~np.isnan(ys); ys = np.interp(np.arange(len(ys)), np.flatnonzero(ok), ys[ok])
            body_y[i, s] = np.convolve(np.pad(ys, 6, mode='edge'), np.ones(13) / 13, mode='valid')
    cutters = []
    for i in (0, 1):
        c = arch_curve(i); ring = [(c[0][0], -0.2)] + [tuple(q) for q in c[1:-1]] + [(c[-1][0], -0.2)]
        for s in (1, -1):
            me = bpy.data.meshes.new('cutter'); n = len(ring)
            V = [(x, s * WELL_IN[i], z) for x, z in ring] + [(x, s * 1.30, z) for x, z in ring]
            F = [list(range(n)), list(range(n, 2 * n))] + [[j, (j + 1) % n, n + (j + 1) % n, n + j] for j in range(n)]
            me.from_pydata(V, [], F); me.update()
            o = bpy.data.objects.new('cutter', me); bpy.context.collection.objects.link(o)
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            cutters.append(o)
    cut = join(cutters, 'arch_cutters'); cut.data.materials.append(liner)
    activate(shell)
    if liner.name not in shell.data.materials: shell.data.materials.append(liner)
    mo = shell.modifiers.new('arches', 'BOOLEAN'); mo.operation = 'DIFFERENCE'; mo.object = cut; mo.solver = 'EXACT'
    mo.material_mode = 'TRANSFER'
    bpy.ops.object.modifier_apply(modifier='arches'); bpy.data.objects.remove(cut)
    flares = []
    for i in (0, 1):
        w = FLARE_W[i]; c = arch_curve(i); tg = np.gradient(c, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
        nrm = np.column_stack([tg[:, 1], -tg[:, 0]])               # outward in model (x, z): x runs forward here
        keep = c[:, 1] >= FLARE_END_Z - 0.08
        for s in (1, -1):
            by = body_y[i, s]; V, F = [], []
            for (x, z), (nx, nz), yb in zip(c[keep], nrm[keep], by[keep]):
                f = _smooth((z - (FLARE_END_Z - 0.08)) / 0.10)        # the band tapers into the body at its two ends
                yo = min(float(O.top_half(float(RF.x_photo(x)))) * 1.026 + FLARE_OVER, FLARE_Y)
                yf = yb + min(max(yo - yb, 0.006), FLARE_PROUD) * f; ww = w * (0.55 + 0.45 * f)
                if abs(x - WH.AXLE_X[i]) < TYRE_COVER[1]: yf = max(yf, min(yo, TYRE_COVER[0]))      # never inside the tyre's face
                for u, y in ((-0.006, yf - 0.060), (-0.006, yf - 0.006), (0.0, yf), (0.5 * ww, yf), (0.8 * ww, yf - 0.004),
                             (0.95 * ww, yf - 0.010), (ww, yf - 0.018), (ww + 0.002, yb - 0.03)):
                    V.append((x + nx * u, s * y, z + nz * u))
            m = 8; rows = int(keep.sum())
            for a in range(rows - 1):
                for b in range(m - 1): F.append([a * m + b, a * m + b + 1, (a + 1) * m + b + 1, (a + 1) * m + b])
            me = bpy.data.meshes.new('flare'); me.from_pydata(V, [], F); me.update()
            o = bpy.data.objects.new('flare', me); bpy.context.collection.objects.link(o)
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
            if sum(f.normal.y * s * f.calc_area() for f in bm.faces) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
            bm.to_mesh(me); bm.free()
            me.materials.append(flare_mat)
            for p in me.polygons: p.use_smooth = True
            flares.append(o)
            print(f'arch {i} side {s:+d}: body beside the flare {by[keep].min():.3f}-{by[keep].max():.3f} m out')
    return join(flares, 'arch_flares')

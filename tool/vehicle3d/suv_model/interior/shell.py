"""The cabin's shell where no photo gives its shape: the headliner, the B and C pillars' trims, the firewall and the
pedals. Set from the hull (hullspace.py and the greenhouse's own numbers, real frame): the side glass's outer face is
0.81 m out at the belt and 0.70 at z 1.70; the glass's head is 1.756 m up; the roof's skin 1.86; the B pillar runs
from x -0.274 to -0.182 and the C pillar from -1.141 to -1.067; the belt is 1.23 m up at the front door's front and
1.29 at the rear door's rear. Everything here is a CHOICE of form within those numbers: the photos show the
headliner's front edge and the pillars only at the pictures' borders."""
import bpy, bmesh, math, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imats, cabin as C

HEAD_Z, HEAD_EDGE = 1.77, (0.62, 1.725)          # the headliner's height on the centre line; where it turns down to the glass's head (y, z)
HEAD_X = (0.47, -2.10)                           # from the windshield's header to the rear glass's
PILLARS = {'B': (-0.274, -0.182), 'C': (-1.141, -1.067), 'D': (-2.080, -1.900)}
CARGO = ((-2.30, -2.05, -1.19), (0.66, 0.78, 0.78), 1.285)      # the cargo room's side trims: their face's y by station (the hull's skin is 0.74 to 0.97 out there, rounding in to the tailgate at x -2.44), and their top, at the belt
WELL_X, WELL_Y, WELL_Z = (-0.79, -1.78), 0.590, 0.96         # the rear wells' trim: its ends, its face and its top
A_PILLAR = ((1.035, 0.800, 1.27), (0.333, 0.666, 1.76))      # the A pillar's middle line on the hull's inside (measured on the built car: between the windshield and the door's glass the body is 0.25 m long at each height, from (0.94, 0.74) to (0.70, 0.78) at z 1.42 and from (0.51, 0.66) to (0.27, 0.70) at 1.72), left side: at the dashboard's top and at the headliner
def glass_y(z): return float(np.interp(z, (1.26, 1.40, 1.55, 1.70, 1.756), (0.812, 0.785, 0.747, 0.702, 0.680)))      # the side glass's outer face (hull, mean of the door stations)
TRIM_IN = 0.055                                  # a pillar trim's cabin face stands this far inside the glass's outer face


def _quad_strip(bm, rows, mat, smooth=True):
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(len(r0) - 1):
            f = bm.faces.new((r0[k], r1[k], r1[k + 1], r0[k + 1])); f.material_index = mat; f.smooth = smooth


def build(name='cabin_shell'):
    mats = [imats.m(n) for n in ('trim_leather', 'cabin_black', 'cabin_carpet', 'cabin_silver')]; bm = bmesh.new()
    # the headliner: flat across the middle, falling 45 mm to its edge, then a short roll down to the glass's head
    ys = np.r_[np.linspace(-1, 1, 21) * HEAD_EDGE[0]]; prof = [(y, HEAD_Z - (HEAD_Z - HEAD_EDGE[1]) * abs(y / HEAD_EDGE[0]) ** 3) for y in ys]
    edge = [(s * (HEAD_EDGE[0] + 0.035), HEAD_EDGE[1] - 0.012) for s in (-1, 1)] + [(s * (glass_y(1.756) - 0.02), 1.70) for s in (-1, 1)]
    prof = [edge[2], edge[0]] + prof + [edge[1], edge[3]]
    rows = [[bm.verts.new((x, y, z - 0.03 * max(0.0, (x - 0.30) / 0.17) ** 2)) for y, z in prof] for x in np.linspace(HEAD_X[0], HEAD_X[1], 28)]
    _quad_strip(bm, rows, 0)
    # the pillars' trims: a cabin-side face following the glass's lean, with returns to the glass either end
    for (x0, x1) in PILLARS.values():
        for s in (1, -1):
            zs = np.linspace(1.24, 1.745, 8); rows = []
            for z in zs:
                yo = glass_y(z); yi = yo - TRIM_IN
                rows.append([bm.verts.new((x, s * y, z)) for x, y in ((x1 + 0.012, yo - 0.015), (x1 + 0.004, yi), (x0 - 0.004, yi), (x0 - 0.012, yo - 0.015))])
            _quad_strip(bm, rows, 0, smooth=False)
    # the A pillars' trims: the hull's pillar inside the glass (hullspace.py), from under the dashboard's top to the headliner
    for s_ in (1, -1):
        foot, head = np.array((A_PILLAR[0][0], s_ * A_PILLAR[0][1], A_PILLAR[0][2])), np.array((A_PILLAR[1][0], s_ * A_PILLAR[1][1], A_PILLAR[1][2])); al = (head - foot) / np.linalg.norm(head - foot)
        u = np.array((-1.0, 0, 0)); u = u - al * u.dot(al); u /= np.linalg.norm(u); v = np.array((0, -s_ * 1.0, 0)); v = v - al * v.dot(al) - u * v.dot(u); v /= np.linalg.norm(v)
        rows = [[bm.verts.new(tuple(foot + al * t + u * a + v * b)) for a, b in ((-0.058, 0.018), (-0.045, 0.036), (0.0, 0.046), (0.055, 0.036), (0.072, 0.016))] for t in np.linspace(-0.08, np.linalg.norm(head - foot) - 0.10, 7)]
        _quad_strip(bm, rows, 0)
    # the firewall under the dashboard and the footwells' forward wall, in shadow; the pedals
    z0 = C.FLOOR_Z
    for vs in (((0.93, -0.80, z0), (0.93, 0.80, z0), (0.80, 0.80, 0.95), (0.80, -0.80, 0.95)),):
        f = bm.faces.new([bm.verts.new(v) for v in vs]); f.material_index = 1
    def box(c, h, mat):
        vs = [bm.verts.new((c[0] + sx * h[0], c[1] + sy * h[1], c[2] + sz * h[2])) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            f = bm.faces.new([vs[k] for k in q]); f.material_index = mat; f.smooth = False
    box((0.84, 0.33, z0 + 0.13), (0.012, 0.045, 0.035), 1)          # the brake
    box((0.86, 0.20, z0 + 0.11), (0.012, 0.028, 0.060), 1)          # the accelerator
    def well_top(x):
        if not WELL_X[1] <= x <= WELL_X[0]: return C.REAR_FLOOR[1]
        u = (x - WELL_X[0]) / (WELL_X[1] - WELL_X[0]); zl = z0 if x > C.REAR_FLOOR[0] else C.REAR_FLOOR[1]; return zl + (WELL_Z - zl) * (1 - (2 * u - 1) ** 4) ** 0.5 + 0.025
    # the cargo room's side trims, from the rear doors back, standing on the wells' trims and the floor; the tailgate's inner panel
    for s_ in (1, -1):
        st = []
        for x in np.linspace(CARGO[0][-1], CARGO[0][0], 16):
            y = float(np.interp(x, CARGO[0], CARGO[1])); zf = well_top(x)
            st.append([bm.verts.new((x, s_ * yy, z)) for yy, z in ((y - 0.06, zf + 0.003), (y, zf + 0.06), (y, CARGO[2] - 0.01), (y + 0.008, CARGO[2]), (y + 0.018, CARGO[2]))])
        _quad_strip(bm, st, 0)
    xt = CARGO[0][0]; yt = CARGO[1][0]
    rows = [[bm.verts.new((x, y, z)) for y in (-yt, yt)] for x, z in ((xt, C.REAR_FLOOR[1]), (xt, 1.15), (xt + 0.045, CARGO[2] - 0.01), (xt + 0.035, CARGO[2]), (xt + 0.02, CARGO[2]))]      # (the tailgate leans forward above 1.15 m)
    _quad_strip(bm, rows, 0, smooth=False)
    # the rear wheels' wells, trimmed: the hull's inner wall there is 0.60 m out, from x -0.85 to -1.74 at the floor and up to 0.95 m
    for s_ in (1, -1):
        st = []
        for x in np.linspace(WELL_X[0], WELL_X[1], 13):
            zl = z0 if x > C.REAR_FLOOR[0] else C.REAR_FLOOR[1]; zt = well_top(x)
            st.append([bm.verts.new((x, s_ * y, z)) for y, z in ((0.74, zt + 0.02), (WELL_Y + 0.02, zt), (WELL_Y, zt - 0.02), (WELL_Y, (z0 if x > C.REAR_FLOOR[0] else C.REAR_FLOOR[1]) + 0.002))])
        _quad_strip(bm, st, 0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # the headliner and the trims are seen from inside: make sure they face the cabin's middle
    for f in bm.faces:
        c = f.calc_center_median(); to_mid = (-0.3 - c.x, -c.y, 1.2 - c.z)
        if f.material_index == 0 and f.normal.x * to_mid[0] + f.normal.y * to_mid[1] + f.normal.z * to_mid[2] < 0: f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

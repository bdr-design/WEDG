"""Under the floor, real frame: what hangs below the shell's floor and shows from low in front and low behind.

The shell's closed floor (0.30 m up, rising to 0.33 at the rear axle) stands for the frame, the tanks and the exhaust.
What the owner's photos show below it (mapped to the real frame, measured by r7work/ub_measure.py and side_low.py):
- rear photo: a low centre at 0.266 m for |y| <= 0.08, a band at 0.275-0.284 m from there out to |y| 0.54, and round
  mounts down to 0.2255 m at |y| 0.60-0.64, just inside the tyres;
- front photo: a flat cover at 0.244-0.246 m for |y| <= 0.28, 0.237-0.241 out to 0.40, then the lower arms: 0.230-0.233
  at |y| 0.42-0.52 and 0.221-0.226 at 0.54-0.64;
- side photo: nothing under about 0.32 m behind the rear tyre or ahead of the front one, so everything low is hidden
  by the tyres from the side. No spare wheel and no boxes are hung under the tail for that reason.

HEIGHTS. The wheels are the size the owner's photos draw them (his decision; realframe), so the hub is where the
photos have it, 0.412 m up, and everything under the floor is at the height the photos map to:
- the rear differential's underside at 0.266. The official minimum ground clearance, 225 mm (toyota.jp, ZX), is for the
  spec's tyre, whose hub is 42 mm lower: 225 + 42 = 267, so the photo's axle is the official one on a bigger wheel;
- the lowest points are the front arms' outer ends, 0.221 (front photo 0.221-0.226), and the rear links' eyes, 0.2255.
  Nothing inboard of the tyres comes below 0.221.

The shell is solid between the rear wheel wells, so a tunnel is cut there for the axle, its springs and dampers.
Its cross-section stays inside the tyre's disc, so no daylight shows through the car from the side.
Every size below that has no source beside it is a game choice: it is drawn to look right, not measured.
The rear axle and the front suspension are separate objects, so a later rig can move them with the wheels."""
import bpy, math
from mathutils import Vector
import realframe as RF, surf

CLEARANCE = 0.225 + RF.HUB_Z - RF.HUB_SPEC_Z   # under the rear differential: the official 225 mm, lifted with the hub (0.267; the photo 0.266)
FLOOR_MIN = 0.221                    # the photos' lowest point inboard of the tyres (the front arms' outer ends)
HUB_DROP = 0.412 - RF.HUB_Z          # the photos' hub height minus the model's: nothing, with the photos' wheels
TYRE_IN = 0.700                      # the tyres' inner faces: half track 0.8325 - half width 0.1325


def unsprung(z_photo):
    """Height in the model of a wheel-carried part that the photo maps to z_photo."""
    return max(z_photo - HUB_DROP, FLOOR_MIN)


BAND_Z = unsprung(0.280)             # rear photo's band 0.275-0.284 for |y| 0.20-0.54: the stabiliser bar
EYE_Z = unsprung(0.2255)             # rear photo's round mounts at |y| 0.60-0.64: the lower link eyes
ARM_Z = (0.243, unsprung(0.221))     # front lower arms: underside at the body pivot (photo), and from |y| 0.46 outward
COVER_Z = (0.245, 0.238)             # front cover's underside for |y| <= 0.28, and at |y| 0.40 (front photo)
DIFF = (0.150, 0.170, RF.HUB_Z - CLEARANCE)   # differential housing half sizes; y from the photo's 0.34 m low centre
TUBE_R, AXLE_Y = 0.045, 0.76         # axle tube radius, and how far out it runs (into the wheel)
TUNNEL_X, TUNNEL_Y, TUNNEL_Z = (-0.22, 0.28), 0.62, 0.60   # axle tunnel: from the axle in x, half width, ceiling


class _Parts:
    """Collects closed solids into one mesh. Every solid is turned outward by its own signed volume when it is added,
    so the result does not depend on a normals recalculation over parts that pass through each other."""
    def __init__(self): self.V, self.F = [], []

    def add(self, V, F):
        V = [tuple(float(c) for c in v) for v in V]; vol = 0.0
        for f in F:
            a = Vector(V[f[0]])
            for i in range(1, len(f) - 1): vol += a.dot(Vector(V[f[i]]).cross(Vector(V[f[i + 1]])))
        assert abs(vol) > 1e-10, 'a part without volume'
        if vol < 0: F = [f[::-1] for f in F]
        o = len(self.V); self.V += V; self.F += [[o + i for i in f] for f in F]

    def loft(self, rings):
        """Rings of equal count joined in order, the first and the last closed with a flat cap."""
        n, m = len(rings[0]), len(rings); F = []
        for j in range(m - 1):
            for k in range(n): F.append([j * n + k, j * n + (k + 1) % n, (j + 1) * n + (k + 1) % n, (j + 1) * n + k])
        F.append(list(range(n))[::-1]); F.append([(m - 1) * n + k for k in range(n)])
        self.add([p for r in rings for p in r], F)

    def sweep(self, path, r, n=8):
        """A round bar along a polyline; r is one radius or one per point."""
        P = [Vector(p) for p in path]; rs = r if isinstance(r, (list, tuple)) else [r] * len(P); rings = []; u = None
        for i, p in enumerate(P):
            t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
            if u is None:
                u = t.cross(Vector((0, 0, 1)))
                if u.length < 1e-6: u = t.cross(Vector((1, 0, 0)))
            u = (u - t * u.dot(t)).normalized(); w = t.cross(u)
            rings.append([tuple(p + rs[i] * (math.cos(a) * u + math.sin(a) * w)) for a in (2 * math.pi * k / n for k in range(n))])
        self.loft(rings)

    def cyl(self, p0, p1, r0, r1=None, n=12): self.sweep([p0, p1], [r0, r0 if r1 is None else r1], n)

    def box(self, lo, hi):
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        self.loft([[(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)] for z in (z0, z1)])

    def ellipsoid(self, c, radii, nu=16, nv=12, e=(0.6, 0.8)):
        """A cast housing: an ellipsoid with fuller shoulders. e[0] < 1 flattens top and bottom, e[1] < 1 squares the plan."""
        cx, cy, cz = c; rx, ry, rz = radii; pw = lambda v, q: math.copysign(abs(v) ** q, v); V = [(cx, cy, cz - rz)]; F = []
        for j in range(1, nv):
            ph = -math.pi / 2 + math.pi * j / nv; cp, sp = pw(math.cos(ph), e[0]), pw(math.sin(ph), e[0])
            for i in range(nu):
                th = 2 * math.pi * i / nu
                V.append((cx + rx * cp * pw(math.cos(th), e[1]), cy + ry * cp * pw(math.sin(th), e[1]), cz + rz * sp))
        V.append((cx, cy, cz + rz)); top = len(V) - 1
        for i in range(nu):
            F.append([0, 1 + (i + 1) % nu, 1 + i]); F.append([top, top - nu + i, top - nu + (i + 1) % nu])
        for j in range(nv - 2):
            for i in range(nu):
                p = 1 + j * nu; F.append([p + i, p + (i + 1) % nu, p + nu + (i + 1) % nu, p + nu + i])
        self.add(V, F)

    def obj(self, name, mat):
        me = bpy.data.meshes.new(name); me.from_pydata(self.V, [], self.F); me.update()
        for p in me.polygons: p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(35)); me.materials.append(mat)
        o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
        return o


def tunnel(shell, mat):
    """Open the solid shell between the rear wheel wells, so the axle has air round it. Must run after the wells are cut."""
    xa = RF.AXLE_X[1]; P = _Parts()
    P.box((xa + TUNNEL_X[0], -TUNNEL_Y, -0.2), (xa + TUNNEL_X[1], TUNNEL_Y, TUNNEL_Z))
    surf.cut(shell, [P.obj('axle_tunnel', mat)], mat, 'axle_tunnel')


def _helix(c, z0, z1, R, turns, seg=10):
    return [(c[0] + R * math.cos(2 * math.pi * k / seg), c[1] + R * math.sin(2 * math.pi * k / seg),
             z0 + (z1 - z0) * k / (turns * seg)) for k in range(int(turns * seg) + 1)]


def rear_axle(mat):
    """The rigid axle on the rear hubs with what is bolted to it: differential and pinion nose, brake backing plates,
    lower link eyes and links, dampers, coil springs, panhard rod and the stabiliser bar under it."""
    xa, zh = RF.AXLE_X[1], RF.HUB_Z; P = _Parts(); roof = TUNNEL_Z + 0.02
    P.cyl((xa, -AXLE_Y, zh), (xa, AXLE_Y, zh), TUBE_R, n=14)
    P.ellipsoid((xa, 0.0, zh), DIFF)
    P.sweep([(xa + 0.09, 0, zh + 0.004), (xa + 0.24, 0, zh + 0.011), (xa + 0.24, 0, zh + 0.011), (xa + 0.258, 0, zh + 0.012),
             (xa + 0.258, 0, zh + 0.012), (xa + TUNNEL_X[1] + 0.03, 0, zh + 0.014)],
            [0.088, 0.052, 0.064, 0.064, 0.038, 0.038], n=12)                      # pinion nose, flange, shaft into the wall
    for s in (1, -1):
        P.cyl((xa, s * 0.775, zh), (xa, s * 0.800, zh), 0.165, n=20)                # brake backing plate, inside the rim
        P.cyl((xa, s * AXLE_Y, zh), (xa, s * 0.822, zh), 0.070)                      # hub, 2 mm into the wheel's back wall
        ez = EYE_Z + 0.032; ey = (0.600, 0.658)                                     # lower link eye: the photo's round mount
        P.cyl((xa + 0.012, s * ey[0], ez), (xa + 0.012, s * ey[1], ez), 0.032)
        P.loft([[(xa + a, s * ey[0] + s * 0.006, z), (xa + b, s * ey[0] + s * 0.006, z), (xa + b, s * ey[1] - s * 0.006, z),
                 (xa + a, s * ey[1] - s * 0.006, z)] for a, b, z in ((-0.022, 0.046, ez), (-0.040, 0.040, zh))])
        P.cyl((xa + 0.012, s * 0.629, ez), (xa + 0.55, s * 0.52, 0.345), 0.020, n=8)   # lower link, up into the floor
        P.cyl((xa - 0.075, s * 0.528, 0.300), (xa - 0.075, s * 0.582, 0.300), 0.026, n=10)                 # damper eye
        P.box((xa - 0.095, min(s * 0.535, s * 0.575), 0.300), (xa - 0.030, max(s * 0.535, s * 0.575), zh))  # its bracket
        P.sweep([(xa - 0.075, s * 0.555, 0.300), (xa - 0.088, s * 0.531, 0.43), (xa - 0.088, s * 0.531, 0.43),
                 (xa - 0.105, s * 0.500, roof)], [0.019, 0.019, 0.031, 0.031], n=10)                       # damper rod, body
        P.cyl((xa, s * 0.43, zh + TUBE_R - 0.012), (xa, s * 0.43, zh + TUBE_R + 0.006), 0.078, n=14)       # spring seat
        P.sweep(_helix((xa, s * 0.43), zh + TUBE_R + 0.012, roof, 0.060, 4.5), 0.008, n=6)                 # coil spring
        P.box((xa - 0.198, min(s * 0.31, s * 0.35), BAND_Z - 0.003), (xa - 0.142, max(s * 0.31, s * 0.35), BAND_Z + 0.040))
        P.loft([[(xa + a, s * 0.318, z), (xa + b, s * 0.318, z), (xa + b, s * 0.342, z), (xa + a, s * 0.342, z)]
                for a, b, z in ((-0.190, -0.150, BAND_Z + 0.040), (-0.060, -0.010, zh - 0.022))])            # clamp strut
    b = BAND_Z + 0.014                                                              # stabiliser bar: its underside is the band
    P.sweep([(xa - 0.36, -0.52, 0.335), (xa - 0.205, -0.52, b + 0.006), (xa - 0.17, -0.488, b), (xa - 0.17, 0.488, b),
             (xa - 0.205, 0.52, b + 0.006), (xa - 0.36, 0.52, 0.335)], 0.014, n=8)
    P.cyl((xa - 0.115, -0.52, 0.405), (xa - 0.115, 0.56, 0.470), 0.016, n=8)        # panhard rod, behind the tube
    P.box((xa - 0.140, -0.545, zh - 0.01), (xa - 0.030, -0.495, 0.425))             # its bracket on the axle
    P.box((xa - 0.145, 0.530, 0.445), (xa - 0.085, 0.590, roof))                    # and on the body
    return P.obj('axle_rear', mat)


def front_suspension(mat):
    """The engine under-cover between the front wheels, and each side's lower wishbone, ball joint, knuckle, hub,
    backing plate, drive shaft, tie rod and upper arm. The damper is left out: the shell is solid where it stands."""
    xa, zh = RF.AXLE_X[0], RF.HUB_Z; P = _Parts(); zt = 0.318                       # tops are inside the shell's floor
    prof = lambda zb: [(xa - 0.36, 0.306), (xa - 0.36, zt), (xa + 0.40, zt), (xa + 0.40, 0.310), (xa + 0.16, zb), (xa - 0.26, zb)]
    P.loft([[(x, y, z) for x, z in prof(zb)] for y, zb in ((-0.45, 0.300), (-0.40, COVER_Z[1]), (-0.28, COVER_Z[0]),
                                                           (0.28, COVER_Z[0]), (0.40, COVER_Z[1]), (0.45, 0.300))])
    rect = lambda x, y, zb, w=0.028, t=0.034: [(x - w, y, zb), (x - w, y, zb + t), (x + w, y, zb + t), (x + w, y, zb)]
    for s in (1, -1):
        for xp, xe in ((xa + 0.17, xa + 0.022), (xa - 0.19, xa - 0.022)):           # the wishbone's two legs
            xm = xp + (xe - xp) * (0.46 - 0.36) / (0.74 - 0.36)
            P.loft([rect(xp, s * 0.36, ARM_Z[0]), rect(xm, s * 0.46, ARM_Z[1]), rect(xe, s * 0.74, ARM_Z[1])])
        P.cyl((xa, s * 0.74, ARM_Z[1] + 0.002), (xa, s * 0.74, 0.300), 0.034, 0.028, n=10)                 # ball joint
        ring = lambda yc, z, wx, wy: [(xa - wx, s * yc - wy, z), (xa + wx, s * yc - wy, z), (xa + wx, s * yc + wy, z), (xa - wx, s * yc + wy, z)]
        P.loft([ring(0.748, 0.270, 0.036, 0.020), ring(0.752, 0.430, 0.050, 0.020), ring(0.712, 0.590, 0.022, 0.016)])   # knuckle
        P.cyl((xa, s * 0.752, zh), (xa, s * 0.822, zh), 0.075)                       # hub, 2 mm into the wheel's back wall
        P.cyl((xa, s * 0.775, zh), (xa, s * 0.800, zh), 0.165, n=20)                 # brake backing plate
        P.sweep([(xa, s * 0.58, zh), (xa, s * 0.60, zh), (xa, s * 0.60, zh), (xa, s * 0.68, zh), (xa, s * 0.752, zh)],
                [0.022, 0.022, 0.052, 0.026, 0.024], n=10)                          # drive shaft and its boot
        P.cyl((xa - 0.14, s * 0.58, 0.345), (xa - 0.12, s * 0.745, 0.340), 0.011, n=8)                      # tie rod
        P.cyl((xa - 0.12, s * 0.745, 0.340), (xa - 0.03, s * 0.750, 0.360), 0.016, n=8)                     # steering arm
        for dx in (0.13, -0.13): P.cyl((xa, s * 0.712, 0.585), (xa + dx, s * 0.585, 0.600), 0.014, n=8)      # upper arm
    return P.obj('suspension_front', mat)


def floor_paint(shell, mat):
    """The shell's underside is not painted body colour: every face that looks down, under 0.45 m, gets the matte
    underbody material."""
    me = shell.data
    if mat.name not in me.materials: me.materials.append(mat)
    mi = me.materials.find(mat.name); n = 0
    for p in me.polygons:
        if p.normal.z < -0.8 and p.center.z < 0.45: p.material_index = mi; n += 1
    print(f'floor: {n} faces under the shell made matte')


def check(rear, front):
    """The rules above, measured on the finished parts: lowest points inboard of the tyres, and that everything under
    0.300 m is within the tyre's chord of its axle, so the tyres hide it from the side."""
    R = RF.TYRE_D / 2; ok = True
    for o, xa, floor in ((rear, RF.AXLE_X[1], FLOOR_MIN), (front, RF.AXLE_X[0], FLOOR_MIN)):
        V = [v.co for v in o.data.vertices]
        S = [V[e.vertices[0]].lerp(V[e.vertices[1]], k / 8) for e in o.data.edges for k in range(9)]   # along every edge
        inb = [v for v in S if abs(v.y) < TYRE_IN]
        low = min(inb, key=lambda v: v.z)
        over = max((abs(v.x - xa) - math.sqrt(R * R - (RF.HUB_Z - v.z) ** 2), v) for v in inb if v.z < 0.300)
        dup = len(V) - len({(round(v.x, 5), round(v.y, 5), round(v.z, 5)) for v in V})
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        print(f'{o.name}: lowest inboard {low.z:.4f} at y {low.y:+.3f} (limit {floor}); past the tyre chord {over[0] * 1000:+.0f} mm '
              f'at x {over[1].x:.3f} z {over[1].z:.3f}; duplicate vertices {dup}; triangles {tris}')
        ok &= low.z > floor - 1e-4 and over[0] <= 0 and dup == 0
    low2 = min((v.co for v in rear.data.vertices if DIFF[1] + 0.02 < abs(v.co.y) < TYRE_IN), key=lambda v: v.z)
    print(f'axle_rear outside the differential: lowest {low2.z:.4f} at y {low2.y:+.3f} (limit {FLOOR_MIN})')
    lowd = min(v.co.z for v in rear.data.vertices if abs(v.co.y) < DIFF[1]); print(f'differential underside {lowd:.4f} (meant {CLEARANCE:.4f})')
    assert ok and low2.z > FLOOR_MIN - 1e-4, 'underbody rule broken'


def build(shell, mat):
    """Runs after the wheel wells are cut (ext_parts.arches)."""
    floor_paint(shell, mat); tunnel(shell, mat)
    rear, front = rear_axle(mat), front_suspension(mat); check(rear, front)
    return rear, front

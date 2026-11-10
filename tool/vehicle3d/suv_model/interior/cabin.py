"""The cabin: where the interior's parts stand in the car (real frame: x forward from the car's middle, y to the
left, z up from the ground), and the cameras the three cabin photos are compared from.

Sourced:
- the official cabin of the five-seat ZX: 1955 mm long, 1640 wide, 1190 high (室内長, 室内幅, 室内高: Toyota's
  主要諸元表; kakaku.com and carsensor give the same). The length runs from the instrument panel's rear end to the
  rear end of the second row's backs; the height from the floor to the headliner.
- the front head restraints' top at least 800 mm over the H-point along the torso line (FMVSS 202a): it sets the
  front seat's size (seatcam.py).
- for the seated positions, the Lexus LX 600's published SAE figures, as the nearest sourced measure: it is built on
  the same frame and wheelbase as this car, but it is another body, so they place the seats to within a few cm,
  not exactly: front headroom 960 mm and legroom 1044 (SAE H61, L34), second row headroom 990 and legroom 930.
- the hull (hullspace.py and the measures below, on the built car): the windshield's foot inside at (1.02, 1.355),
  the doors from x 0.9385 to -0.1365 and on to -1.1825 (sides.py), the rear wells' walls 0.665 m out (ext_parts).
Marked CHOICE: what none of these gives (the floor's height, the pedals' station, the seats' fore-aft setting within
what the figures allow, every rounding)."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix, Vector

CABIN_L, CABIN_W, CABIN_H = 1.955, 1.640, 1.190       # official (five-seat ZX)
FLOOR_Z = 0.555                                      # CHOICE: with the official height the headliner is then 1.745 m up, 11.5 cm under the roof's skin (the glass roof's frame)
HEAD_Z = FLOOR_Z + CABIN_H
# The dashboard and everything dash_front's camera places stand DASH_DZ higher than first fitted: the photo fixes
# them against its camera, whose height was a guess (1.45 m), and at that the dashboard's top was 95 mm under the
# windshield's foot (the review of 10 Nov). Raised so that the top meets the glass's foot (3 mm under it), the wheel's centre is then
# 0.35 m over the driver's H-point, as usual in this class.
DASH_DZ = 0.075
IP_REAR = 0.548                                      # where the official length is taken from: the instrument panel's rear end at its top (the lip of the dashboard's top).
# (Taken from its lower face, 0.37, the length put the second row's H-point at the rear door's rear edge, its eye behind the C pillar and its belt's
# guide 0.38 m ahead of the shoulder, 1.2 m behind the driver's H-point where 0.95 to 1.0 is usual (the review of 10 Nov). From the top's lip it agrees
# with the C pillar and with the LX 600's second-row legroom. Which point Toyota measures from is not published with the figure: CHOICE.)
DOOR_Y = CABIN_W / 2                                 # the door trims' panel face at their foot (the cabin's widest)
DOOR_LEAN = 5.5                                      # degrees: the trims lean in with the glass, so their top edge is 0.765 m out, inside the glass (0.81 at the belt)
FRONT_DOOR_X, REAR_DOOR_X = (0.9385, -0.1365), (-0.1365, -1.1825)
REAR_FLOOR = (-0.99, 0.635)                          # behind the second row the floor steps up over the rear axle (the hull's underside is 0.60 m up from x -1.06 to -1.55): where, and to what height
ARCH = (-1.294, 0.408, (0, 20, 40, 60, 80, 90, 100, 120, 140, 160, 180), (0.506, 0.516, 0.532, 0.564, 0.544, 0.540, 0.548, 0.574, 0.531, 0.496, 0.477), 0.035)
# (the rear wheel's well in the hull, measured on the built car: the hub (x, z); the well's radius by the angle from straight ahead; how far clear of it the rear doors' trims are cut)
def _clear_of_arch(x, z):
    dx, dz = x - ARCH[0], z - ARCH[1]; return np.hypot(dx, dz) > np.interp(np.degrees(np.arctan2(dz, dx)), ARCH[2], ARCH[3], left=0.0, right=0.0) + ARCH[4]
FRONT_DOOR_TOE = 0.022                               # radians: the front doors' trims turn in toward the front with the hull's plan (their front end 23 mm further in)
REAR_TRIM_TOP = (1.252, 1.280)                       # the rear trims' top edge at the door's front and rear: the belt is 1.26 at the front and rises to 1.29 at the rear
DASH_END = (0.38, 1.02)                              # the front trims give way to the dashboard's end ahead of x 0.38 and over z 1.02 (the dashboard's end meets the door there)
TRIM_GAP = 0.006                                     # each trim stops this short of its door's edges (the shut line)
TRIM_TOP_Z = 1.235                                   # the trims' top edge, at the window's sill (the belt is 1.229 to 1.261 along the front door)
SEAT_Y = 0.435                                       # the front seats' middle across: the gap between them is then 0.32 m, for a 0.29 m console
# the pedals and the driver's H-point (the seat is placed by its H-point, which seat3d.hpoint finds on the built seat):
# the accelerator's pad 0.20 m ahead of the heel point (AHP) on the floor; the ankle 0.04 ahead of the heel and 0.09
# up; the H-point where the LX 600's headroom (960) and legroom (1044) put it: 0.858 m from the headliner along a
# line 8 degrees back of upright, and 0.790 m from the ankle (SAE J1100 H61 and L34, less their 102 and 254 mm)
AHP = (0.75, FLOOR_Z)                                # CHOICE within the hull: the toe board stands behind the front wells (x 1.10)
def _h_point():
    head = HEAD_Z - 0.045 * (SEAT_Y / 0.62) ** 3; z = head - 0.858 * math.cos(math.radians(8)); ax, az = AHP[0] + 0.04, AHP[1] + 0.09
    return ax - math.sqrt(0.790 ** 2 - (z - az) ** 2), z
H_POINT = _h_point()
# The steering wheel's centre x, y, z and its rake in degrees (top leaning forward). On dash_front its rim runs from
# column 195 to 613 and from row 295 to 713: a circle 418 px across with its middle at (404, 504). Through that
# photo's camera (below), a wheel 0.38 m tall is 0.77 m from the camera along its axis, which puts its middle here.
# (The photo draws it as wide as it is tall; seen 30 degrees from the side it should be 0.87 as wide. The height is
# used.) The rake is a CHOICE.
WHEEL = (0.430, 0.417, 1.172 + DASH_DZ, 24.0)        # (the two-view fit puts it at 0.441, 0.423, 1.167: the mean of the two; raised with the dashboard)
# dash_front's camera, from four readings on the photo (none of them can be checked against a second one, so this
# is a fit, not a measurement):
#   the screen's display, 291 px wide; a 12.3 inch display is 0.292 m wide, so about 997 px per metre at the screen;
#   the cup holders, drawn as ellipses 0.70 as tall as wide: they are seen from 44 degrees above the level;
#   their middle at row 872, 25.4 degrees under the photo's middle row: so the camera looks down by 18.6 degrees;
#   the windshield's lower edge at row 300 on the centre line, which the hull has at x 1.0, z 1.28.
# With the screen 0.55 m ahead of the car's middle that puts the camera at x -0.30 on the centre line, 1.45 m up (a
# sitting eye's height), with 847 px focal length on the 1672 px frame (89 degrees across). The car's centre line is
# at column 856. The photo has no front seats in it; the comparison hides them.
# The door trims in this photo are not door_FL's (their switches stand in two columns of four here, nearly upright,
# and in one slanting row of four there), so they were not used. An earlier fit that did use them gave a long lens
# 4.2 m back, under which the console's top would be seen edge-on; the photo shows it from well above.
# (position, where it looks, degrees across, the column of the car's centre line or None, what to hide)
_d = lambda pos, yaw, pitch: (pos, (pos[0] + math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)), pos[1] + math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)), pos[2] - math.sin(math.radians(pitch))))
# the second row's bench: the cushion's depth to the backs' foot (CHOICE); RISE over the first fit, which the LX 600's
# second-row headroom (990) asks for (its H-point 0.86 m up); the cushion's top at its rear and at its front piping;
# the backs' lean (degrees), thickness and tops (outer, middle); and the cushion's front edge, set so that the backs'
# rear end stands the official cabin length behind the instrument panel's
def _bench(depth=0.50, rise=0.07, lean=20.0, thick=0.13):
    top = (0.745 + rise, 0.770 + rise); back_top = (1.37 + rise, 1.34 + rise)
    return depth, rise, top, lean, thick, back_top, IP_REAR - CABIN_L + thick + (back_top[0] - top[0]) * math.tan(math.radians(lean)) + depth
BENCH = _bench()
REAR_CAM = (1.06, 0.53)            # rear_bench's camera against the bench: ahead of the cushion's front edge and over its top (the review's fit, re-measured)
def _rear_cam():
    p = (BENCH[6] + REAR_CAM[0], 0.0, BENCH[2][1] + REAR_CAM[1]); return _d(p, 180.0, 11.5)
CAMERAS = {'dash_front': (*_d((-0.30, 0.0, 1.45 + DASH_DZ), 0.0, 18.6), 89.2, 856, ('seat_',)),
           # driver_pov: fitted with dash_front's camera held (twoview.py, 15 landmarks to 8.7 px): over the driver's
           # seat, looking down 35.6 degrees and 4.4 to the right, 76.5 degrees across. It is above a seated eye: the
           # photo was drawn from there. The game's own seated eye is SEATED_EYE.
           'driver_pov': (*_d((-0.194, 0.433, 1.658 + DASH_DZ), -4.4, 35.6), 76.5, None, ('seat_', 'cabin_headliner')),      # (1 cm over the headliner, as the fit has it: the comparison leaves the headliner out)
           # rear_bench: one camera fits what it shows of the bench (REAR_CAM), not its belts' anchors; the centre line is at column 837.5
           'rear_bench': (*_rear_cam(), 71.6, 837.5, ('seat_F', 'dashboard', 'steering', 'door_trim_F'))}
SEATED_EYE = (H_POINT[0] - 0.13, SEAT_Y, H_POINT[1] + 0.69)      # a seated eye over the driver's H-point (SAE J941's eyellipse centre, roughly: CHOICE)


def _place(ob, loc, rot=(0, 0, 0)):
    ob.location = loc; ob.rotation_euler = rot; return ob


# the built car whose hull the cabin is fitted into: the repository's suv.blend beside this folder, or the working build
HULL = os.environ.get('SUV_BLEND') or next(p for p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'suv.blend'), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'r26', 'suv.blend')) if os.path.exists(p))
def _tidy(ob):
    """Every object: duplicate vertices merged, zero-area faces and loose vertices dropped. Each open sheet (whatever
    has a free edge: screens, grilles, seams, trims, the floor) is made consistent and turned as a whole so that most
    of its area faces one of the occupants' eyes; closed bodies keep the outward faces the builders gave them. Last,
    any shading normal (relief_n) that points against its faces is turned with them."""
    eyes = [Vector(SEATED_EYE), Vector((SEATED_EYE[0], -SEATED_EYE[1], SEATED_EYE[2])), Vector((-1.0, 0.44, 1.52)), Vector((-1.0, -0.44, 1.52)), Vector((-1.0, 0.0, 1.52))]
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me); mw = ob.matrix_world.copy(); m3 = mw.to_3x3()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-6); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.faces.ensure_lookup_table(); seen = set()
    for f0 in bm.faces:
        if f0.index in seen: continue
        comp, stack = [], [f0]; seen.add(f0.index)
        while stack:
            f = stack.pop(); comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        if not any(e.is_boundary for f in comp for e in f.edges): continue
        bmesh.ops.recalc_face_normals(bm, faces=comp); score = 0.0
        for f in comp:
            c = mw @ f.calc_center_median(); n = m3 @ f.normal; score += f.calc_area() * (1 if any(n.dot(e - c) > 0 for e in eyes) else -1)
        if score < 0: bmesh.ops.reverse_faces(bm, faces=comp)
    lay = bm.verts.layers.float_vector.get('relief_n')
    if lay is not None:
        bm.normal_update()
        for v in bm.verts:
            n = Vector(v[lay])
            if n.length > 0.5 and v.link_faces and n.dot(sum((f.normal for f in v.link_faces), Vector())) < 0: v[lay] = -n
    bm.to_mesh(me); bm.free()
    if me.attributes.get('relief_n') is not None:
        import relief as R; R.shade(me)


def build():
    """Everything built so far, set in the car. Returns the objects."""
    import seat3d as SEAT, door as DOOR, steering as ST, door_measure as DM
    out = []
    for side, name in ((1, 'seat_FL'), (-1, 'seat_FR')):
        # the photo's seat has its controls on its right: it is the right-hand seat; the left one is its mirror
        ob = SEAT.build(name, mirror=side > 0); hx, hz = SEAT.hpoint(ob); zmin = min(v.co.z for v in ob.data.vertices)
        rise = H_POINT[1] - hz - (FLOOR_Z - zmin); SEAT.risers(ob, rise)          # the seat stands on its rails' brackets, which take up what its own height lacks
        out.append(_place(ob, (H_POINT[0] - hx, side * SEAT_Y, H_POINT[1] - hz)))
    # the front left trim as built faces -y with x forward: it stands on the left door as it is; the right one is its mirror
    s, _, _ = DM.frame(); H = 1024 * s; zb = TRIM_TOP_Z - H * (1 - 60 / 1024)
    for side in (1, -1):
        for row, (xf, xr) in (('F', (FRONT_DOOR_X[0], FRONT_DOOR_X[1] + TRIM_GAP)), ('R', (REAR_DOOR_X[0] - TRIM_GAP, REAR_DOOR_X[1] + TRIM_GAP))):
            # the rear doors have no photo of their own (rear_bench shows their trims at its borders): the front trim, shortened to the rear door's length
            sx = (xf - xr) / DM.DOOR_LENGTH
            # (a rear door is cut round the wheel's arch, as the hull's door is; a front one ends 4 cm short of the door's front, beside the dashboard's end, where the hull narrows)
            keep = (lambda x, z, xr=xr, sx=sx: _clear_of_arch(xr + x * sx, zb + z)) if row == 'R' else (lambda x, z, xr=xr, sx=sx: (xr + x * sx < FRONT_DOOR_X[0] - 0.04) & ~((xr + x * sx > DASH_END[0]) & (zb + z > DASH_END[1])))
            d = DOOR.build('door_trim_%s%s' % (row, 'L' if side > 0 else 'R'), keep=keep); d.location = (xr, side * (DOOR_Y + 0.012 + 0.030), zb)
            d.scale = ((xf - xr) / DM.DOOR_LENGTH, side, 1); d.rotation_euler = (side * math.radians(DOOR_LEAN), 0, -side * FRONT_DOOR_TOE if row == 'F' else 0.0); out.append(d)
            if row == 'R':          # a rear trim's top follows the belt, which rises toward the rear: its height grows from front to rear
                for v in d.data.vertices: u = v.co.x / DM.DOOR_LENGTH; v.co.z *= ((REAR_TRIM_TOP[1] - zb) * (1 - u) + (REAR_TRIM_TOP[0] - zb) * u) / (TRIM_TOP_Z - zb)
    w = ST.build('steering_wheel'); x, y, z, rake = WHEEL
    # the wheel is built facing -y with z up: turn it to face the driver (-x) and lean its top forward
    # (about x first: its face, which looks along -y, tips up by the rake; then about z by -90 degrees: it looks along -x, at the driver,
    # with the photo's right on the car's right. Up to here it was turned +90 and showed its back to the cabin.)
    w.rotation_euler = (math.radians(-rake), 0, -math.pi / 2); w.location = (x, y, z); out.append(w)
    import dash as DASH; out.append(DASH.build())
    import bench3d as BENCH; out.append(BENCH.build())
    import shell as SHELL; out.extend(SHELL.build())
    import liner as LINER; out.append(LINER.build(HULL, cover=[o for o in out if o.name.startswith(('door_trim', 'dashboard', 'cabin_shell', 'cabin_headliner', 'seat_bench'))]))
    # the floor: flat (a choice: no photo shows the tunnel or the footwells' shape), between the doors and, further back, between the rear wheels' wells
    import imats; X0, X1 = SHELL.WELL_X; Y = SHELL.WELL_Y - 0.002; xs, zs = REAR_FLOOR      # (the floor's edge just inside the wells' trims, which stand on it)
    front = [(0.93, 0.835), (X0, 0.835), (X0, Y), (xs, Y)]; rear = [(xs, Y), (X1 - 0.05, Y), (X1 - 0.05, 0.74), (-2.05, 0.74), (-2.38, 0.62)]
    V = [(x, y, FLOOR_Z) for x, y in front] + [(x, -y, FLOOR_Z) for x, y in front[::-1]] + [(x, y, zs) for x, y in rear] + [(x, -y, zs) for x, y in rear[::-1]]
    me = bpy.data.meshes.new('cabin_floor'); me.from_pydata(V, [], [list(range(8))[::-1], list(range(8, 18))[::-1], [3, 4, 17, 8]]); me.materials.append(imats.m('cabin_carpet'))
    for p in me.polygons:
        if p.normal.z < 0: p.flip()
    f = bpy.data.objects.new('cabin_floor', me); bpy.context.collection.objects.link(f); out.append(f)
    bpy.context.view_layer.update()                  # (the objects' world matrices: the faces are turned in the car's frame)
    for ob in out: _tidy(ob)
    return out


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); obs = build()
    print('cabin: %d objects' % len(obs)); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

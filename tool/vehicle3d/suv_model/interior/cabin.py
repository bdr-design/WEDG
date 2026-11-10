"""The cabin: where the interior's parts stand in the car (real frame: x forward from the car's middle, y to the
left, z up from the ground), and the cameras the three cabin photos are compared from.

What is measured: the hull (hullspace.py on the built car): the roof's outer skin 1.86 m up over the seats, the
windshield from (x 0.97, z 1.40) to (0.48, 1.75) on the centre line, the doors' skin 0.922 m out at z 1.0, the
front door from x 0.9385 to -0.1365 and the rear door on to -1.1825 (sides.py). The official cabin is 1635 mm
wide and 1215 mm high (DIMENSIONS.md 9).
What is a game choice until the cabin photos are measured (marked CHOICE): the floor's height, where the seats, the
wheel and the dashboard stand, and the cameras."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix, Vector

CABIN_W, CABIN_H = 1.635, 1.215                      # official
FLOOR_Z = 0.555                                      # CHOICE: the headliner is then 1.77 m up, 9 cm under the roof's skin
DOOR_Y = CABIN_W / 2                                 # the door trims' panel face at their foot (the cabin's widest)
DOOR_LEAN = 5.5                                      # degrees: the trims lean in with the glass, so their top edge is 0.765 m out, inside the glass (0.81 at the belt)
FRONT_DOOR_X, REAR_DOOR_X = (0.9385, -0.1365), (-0.1365, -1.1825)
TRIM_TOP_Z = 1.235                                   # the trims' top edge, at the window's sill (the belt is 1.229 to 1.261 along the front door)
SEAT_X, SEAT_Y = -0.38, 0.411                        # CHOICE: the front seats' rearmost point (the hip point, 0.34 m ahead of it, is then 0.47 m behind the wheel's centre and the cushion's nose 5 cm under the rim); across, they are centred on the wheel
# The steering wheel's centre x, y, z and its rake in degrees (top leaning forward). On dash_front its rim runs from
# column 195 to 613 and from row 295 to 713: a circle 418 px across with its middle at (404, 504). Through that
# photo's camera (below), a wheel 0.38 m tall is 0.77 m from the camera along its axis, which puts its middle here.
# (The photo draws it as wide as it is tall; seen 30 degrees from the side it should be 0.87 as wide. The height is
# used.) The rake is a CHOICE.
WHEEL = (0.430, 0.417, 1.172, 24.0)        # (the two-view fit puts it at 0.441, 0.423, 1.167: the mean of the two)
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
CAMERAS = {'dash_front': ((-0.30, 0.0, 1.45), (-0.30 + math.cos(math.radians(18.6)), 0.0, 1.45 - math.sin(math.radians(18.6))), 89.2, 856, ('seat_',)),
           # driver_pov: fitted with dash_front's camera held (twoview.py): 1.66 m up over the driver's seat, looking down
           # 35.6 degrees and 4.4 degrees to the right, 1061 px focal length (76.5 degrees across)
           'driver_pov': ((-0.20, 0.41, 1.45), (-0.20 + math.cos(math.radians(-3.4)) * math.cos(math.radians(21.0)), 0.41 + math.sin(math.radians(-3.4)) * math.cos(math.radians(21.0)), 1.45 - math.sin(math.radians(21.0))), 76.0, None, ('seat_',)),
           # rear_bench: no camera fits all of it. Its bench is 1467 px wide at the cushion's front edge and its
           # seat backs 1053 px across; taking the bench as 1.45 m wide, the backs as 1.40 m and 0.5 m further away
           # gives 1447 px focal length (60 degrees across) 1.43 m ahead of the cushion's front edge; the cushion's top,
           # 171 px deep for 0.5 m, is then seen from 23 degrees above, 0.73 m over it, looking down 16 degrees. At
           # that the belts' webbing comes out 52 mm wide (47 is the standard). The cushion's front edge is taken 0.75 m
           # behind the car's middle and 0.93 m up (CHOICE). The centre line is at column 840.
           'rear_bench': ((0.68, 0.0, 1.66), (0.68 - math.cos(math.radians(16.0)), 0.0, 1.66 - math.sin(math.radians(16.0))), 60.0, 840, ('seat_F', 'dashboard', 'steering', 'door_trim_F'))}


def _place(ob, loc, rot=(0, 0, 0)):
    ob.location = loc; ob.rotation_euler = rot; return ob


def build():
    """Everything built so far, set in the car. Returns the objects."""
    import seat3d as SEAT, door as DOOR, steering as ST, door_measure as DM
    out = []
    for side, name in ((1, 'seat_FL'), (-1, 'seat_FR')):
        # the photo's seat has its controls on its right: it is the right-hand seat; the left one is its mirror
        out.append(_place(SEAT.build(name, mirror=side > 0), (SEAT_X, side * SEAT_Y, FLOOR_Z)))
    # the front left trim as built faces -y with x forward: it stands on the left door as it is; the right one is its mirror
    s, _, _ = DM.frame(); H = 1024 * s; zb = TRIM_TOP_Z - H * (1 - 60 / 1024)
    for side in (1, -1):
        for row, (xf, xr) in (('F', FRONT_DOOR_X), ('R', REAR_DOOR_X)):
            # the rear doors have no photo of their own (rear_bench shows their trims at its borders): the front trim, shortened to the rear door's length
            d = DOOR.build('door_trim_%s%s' % (row, 'L' if side > 0 else 'R')); d.location = (xr, side * (DOOR_Y + 0.012 + 0.030), zb)
            d.scale = ((xf - xr) / DM.DOOR_LENGTH, side, 1); d.rotation_euler = (side * math.radians(DOOR_LEAN), 0, 0); out.append(d)
    w = ST.build('steering_wheel'); x, y, z, rake = WHEEL
    # the wheel is built facing -y with z up: turn it to face the driver (-x) and lean its top forward
    # (about x first: its face, which looks along -y, tips up by the rake; then about z by -90 degrees: it looks along -x, at the driver,
    # with the photo's right on the car's right. Up to here it was turned +90 and showed its back to the cabin.)
    w.rotation_euler = (math.radians(-rake), 0, -math.pi / 2); w.location = (x, y, z); out.append(w)
    import dash as DASH; out.append(DASH.build())
    import bench as BENCH; out.append(BENCH.build())
    import shell as SHELL; out.append(SHELL.build())
    bpy.ops.mesh.primitive_plane_add(size=1); f = bpy.context.active_object; f.name = 'cabin_floor'; f.scale = (2.6, CABIN_W, 1); f.location = (-0.35, 0, FLOOR_Z)
    import seat as S2; f.data.materials.append(S2._mat('cabin_carpet', (0.42, 0.33, 0.22), rough=0.95)); out.append(f)
    return out


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); obs = build()
    print('cabin: %d objects' % len(obs)); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

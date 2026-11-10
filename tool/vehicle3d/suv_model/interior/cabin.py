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
DOOR_Y = CABIN_W / 2                                 # the door trims' panel plane (the cabin's widest)
FRONT_DOOR_X, REAR_DOOR_X = (0.9385, -0.1365), (-0.1365, -1.1825)
TRIM_TOP_Z = 1.235                                   # the trims' top edge, at the window's sill (the belt is 1.229 to 1.261 along the front door)
SEAT_X, SEAT_Y = -0.50, 0.42                         # CHOICE: the front seats' rearmost point; across, they are centred on the wheel
# The steering wheel's centre x, y, z and its rake in degrees (top leaning forward). On dash_front its middle is at
# column 408, row 520 and it is 384 px wide: 0.42 m left of the centre line and 1.105 m up if it is 0.33 m ahead of
# the car's middle. That distance and the rake are a CHOICE; at it the photo's wheel is 0.36 m across, not 0.38.
WHEEL = (0.33, 0.42, 1.105, 24.0)
# the cameras the cabin photos are compared from: position, where they look, and the horizontal field of view in degrees. CHOICE, to be solved.
# dash_front is nearly an elevation: on it the left door's switch panel, which door_FL has running 0.19 m rearward
# as it drops, shifts only 36 px sideways from its top end to its bottom end. With the door where the hull puts it
# that makes the camera 4.2 m behind the car's middle with a long lens (4833 px focal length on a 1672 px frame,
# 19.6 degrees across): about 1017 px per metre at the dashboard. The car's centre line is at column 856. Nothing
# behind x -0.05 is in the photo (no seats), so the comparison clips there.
# (position, where it looks, degrees across, the column of the car's centre line or None, nearest x drawn or None)
CAMERAS = {'dash_front': ((-4.19, 0.0, 1.17), (0.60, 0.0, 1.15), 19.64, 856, -0.05),
           'driver_pov': ((-0.30, 0.37, 1.28), (0.75, 0.30, 1.08), 78.0, None, None),          # CHOICE, to be solved
           'rear_bench': ((-0.05, 0.0, 1.20), (-1.6, 0.0, 1.05), 92.0, None, None)}            # CHOICE, to be solved


def _place(ob, loc, rot=(0, 0, 0)):
    ob.location = loc; ob.rotation_euler = rot; return ob


def build():
    """Everything built so far, set in the car. Returns the objects."""
    import seat as SEAT, door as DOOR, steering as ST, door_measure as DM
    out = []
    for side, name in ((1, 'seat_FL'), (-1, 'seat_FR')):
        # the photo's seat has its controls on its right: it is the right-hand seat; the left one is its mirror
        out.append(_place(SEAT.build(name, mirror=side > 0), (SEAT_X, side * SEAT_Y, FLOOR_Z)))
    # the front left trim as built faces -y with x forward: it stands on the left door as it is; the right one is its mirror
    s, _, _ = DM.frame(); H = 1024 * s
    for side, name in ((1, 'door_trim_FL'), (-1, 'door_trim_FR')):
        d = DOOR.build(name); d.location = (FRONT_DOOR_X[1], side * DOOR_Y, TRIM_TOP_Z - H * (1 - 60 / 1024))
        if side < 0: d.scale = (1, -1, 1)
        out.append(d)
    w = ST.build('steering_wheel'); x, y, z, rake = WHEEL
    # the wheel is built facing -y with z up: turn it to face the driver (-x) and lean its top forward
    w.rotation_euler = (0, math.radians(rake), -math.pi / 2) if False else (math.radians(-rake), 0, math.pi / 2); w.location = (x, y, z); out.append(w)
    bpy.ops.mesh.primitive_plane_add(size=1); f = bpy.context.active_object; f.name = 'cabin_floor'; f.scale = (2.6, CABIN_W, 1); f.location = (-0.35, 0, FLOOR_Z)
    import seat as S2; f.data.materials.append(S2._mat('cabin_carpet', (0.42, 0.33, 0.22), rough=0.95)); out.append(f)
    return out


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); obs = build()
    print('cabin: %d objects' % len(obs)); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

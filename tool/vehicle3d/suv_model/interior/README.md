# SUV interior (work in progress, not reviewed)

The owner's decision (10 Nov): the interior must match his six photos with no difference. The photos are in
`tool/vehicle3d/suv_parts/interior/`; they are measured against, never projected.

State: first passes of everything the six photos show except the cabin's shell behind the front doors (headliner,
B, C and D pillars, rear door trims, carpet, pedals) and the third row. Nothing has been through an independent
review yet, and most inner details (seams, stitching, perforation, vent slats, materials) are still to do.

| File | What it is |
|---|---|
| `masks.py` | finds the photos and their magenta backdrop |
| `zoom.py` | a gridded enlargement of part of a photo, to read coordinates off |
| `relief.py` | a solid from a photo's region: its thickness, flat in the middle and rounded to its edge, with its own shading normals; flat shapes, blocks and bezels on a plane |
| `photocam.py` | a cabin photo's camera, and planes in the car to lay the photo's regions on |
| `cabin.py` | where the parts stand in the car, and the three cabin photos' cameras (with how each was fitted and what does not fit) |
| `shot.py`, `shot_wheel.py`, `shot_cabin.py` | render a part or the cabin from a photo's camera, beside the photo, and score it |
| `hullspace.py` | measures the space inside the built hull |
| `wheel_measure.py`, `wheel_features.py`, `wheel_seam.npy`, `steering.py` | the steering wheel |
| `seat_measure.py`, `seat_features.py`, `seat.py` | the front seat |
| `door_measure.py`, `door_features.py`, `door.py` | the front door trim |
| `dash.py`, `dash_features.py` | the dashboard, console, A pillars and mirror |
| `bench.py` | the second row's bench |

Measured so far, outline IoU against each square-on photo: steering wheel 0.985, seat 0.994, door trim 0.9995 (the
door photo fills its frame, so that last figure says little). The cabin photos have no score yet.

The six photos do not agree with each other or with one camera each (cabin.py lists what was found): dash_front's
door trims are not door_FL's; its wheel is drawn round though seen from the side; rear_bench's bench, belts and
cushion top each ask for a different camera.

Not sourced: the wheel's diameter (0.380 m assumed; it makes the photo's grip 31.5 to 33 mm thick) and the seat's
size (1.08 m from the rail's foot to the headrest's top assumed). The door trim's scale comes from the model's own
door length (1.075 m). Not in any of the three photos: depth across the photo's plane. The wheel's `DISH`, `PLATE`
and `PAD_RISE`, the seat's `WIDTHS` and the door's `DEPTH` are placeholders until the cabin photos are measured.

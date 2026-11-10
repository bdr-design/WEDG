# SUV interior (work in progress, not reviewed)

The owner's decision (10 Nov): the interior must match his six photos with no difference. The photos are in
`tool/vehicle3d/suv_parts/interior/`; they are measured against, never projected.

State: the whole cabin stands in the built car (front seats, steering wheel, dashboard and console, four door
trims, second-row bench with its belts, headliner, A to D pillar trims, wheel-well and cargo trims, floor) and
`inhull.py` finds none of it outside the hull. Still to do: most inner details (perforation, the cushion's own seams,
vent slats, the instrument faces, stitching on the dashboard), the front belts, the third row (not built: the
photos show a five-seat cabin with headrests behind), the materials' fine tuning, the GLB and its phone check.

When the photos disagree (they are AI renders: no camera fits all of any cabin photo, and the six do not agree
with each other), the rule is:
1. a part's own square-on photo rules its shape (wheel, seat_side, door_FL);
2. the cabin photos (dash_front, driver_pov, rear_bench) rule where things stand and what is there;
3. the hull rules the glass, the pillars, the wheel wells and the floor: nothing may stand outside it;
4. what none of them gives is a choice, marked CHOICE where it is made, and kept inside real proportions.

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
| `seat_measure.py`, `seat_features.py`, `seatcam.py`, `seat3d.py` | the front seat, through seat_side's own perspective camera (`seat.py` is the superseded square-on first pass) |
| `door_measure.py`, `door_features.py`, `door.py` | the front door trim |
| `dash.py`, `dash_features.py` | the dashboard (one lofted body with the instruments' binnacle), the stack, screen, console and mirror |
| `bench3d.py` | the second row's bench (`bench.py` is the superseded first pass) |
| `shell.py` | headliner, pillar trims, wheel-well and cargo trims, firewall, pedals: from the hull's own measures |
| `inhull.py` | checks every cabin vertex against the built car's body and glass |

Measured so far, outline IoU against each part's own photo: steering wheel 0.985, front seat 0.964 through the
photo's perspective camera (the square-on first pass scored 0.994 square-on, which was the wrong test: 0.73 through
the camera), door trim 0.9995 (the door photo fills its frame, so that figure says little). The cabin photos have
no score: a score against a photo whose camera was fitted to the same photo is circular.

The six photos do not agree with each other or with one camera each (cabin.py lists what was found): dash_front's
door trims are not door_FL's; its wheel is drawn round though seen from the side; rear_bench's bench, belts and
cushion top each ask for a different camera.

Not sourced: the wheel's diameter (0.380 m assumed; it makes the photo's grip 31.5 to 33 mm thick) and the seat's
size (1.00 m from the rail's foot to the headrest's top: seatcam.py says why). The door trim's scale comes from the model's own
door length (1.075 m). Not in any of the three photos: depth across the photo's plane. The wheel's `DISH`, `PLATE`
and `PAD_RISE`, the seat's `WIDTHS` and the door's `DEPTH` are placeholders until the cabin photos are measured.

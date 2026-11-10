# SUV interior (work in progress, not reviewed)

The owner's decision (10 Nov): the interior must match his six photos with no difference. The photos are in
`tool/vehicle3d/suv_parts/interior/`; they are measured against, never projected.

State: the whole cabin stands in the built car (front seats on their rail brackets, steering wheel, dashboard with
its lower panel, console and armrest, four door trims, the second-row bench with its wings, seams, belts and their
guides, headliner, pillar trims, wheel-well and cargo trims, a liner over the rest of the hull's inside, floor).
Measured on the last build (the fifth review's scripts):
- `inhull.py` (vertices and triangles): nothing more than 1.9 mm outside the hull;
- 14 pairs of triangles cross, all the liner's behind trims' top edges and a dashboard end;
- bare hull seen from the seats: 0.65 % of the view from the driver's eye, 1.0 % from the rear middle: slivers along
  the glass's edges and the A pillars' edges, a line at the windshield's foot, and a band round the tailgate's top
  (the fifth review: 6.9 % of an 80 degree view looking back). Not yet solved: the right answer is the windows' own
  seals and reveals, not more liner;
- one z-fight of two colours on the rear trims (about 3 cm2 at (-0.50, +-0.84, 0.83)), not yet found.
Still to do as well: the seats' finer shapes (perforation, inserts), the door's switch panel, the shifter, the photo
differences the reviews list.

Game files (the owner's decision: layered detail): `../cabin.glb` is the whole cabin (67k triangles, one draw);
`../cabin_lod0.glb` is the layer the game loads while the player is inside (lod_cabin.py: the faces no occupant can
see from a box round each seat's eye dropped, 44k). From those eyes it differs from the full cabin on 0 to 0.3 % of
pixels; an eye leaning well outside the boxes can see a few dozen pixels through it (the fifth review). The owner's
figure is about 40k. The game must draw the black glass clear from inside.

Five seats: the owner chose the official ZX's five seats (10 Nov), though rear_bench shows a third row's headrests.

When the photos disagree (they are AI renders: no camera fits all of any cabin photo, and the six do not agree
with each other), the rule is:
1. a part's own square-on photo rules its shape (wheel, seat_side, door_FL);
2. the cabin photos (dash_front, driver_pov, rear_bench) rule where things stand and what is there;
3. the hull rules the glass, the pillars, the wheel wells and the floor: nothing may stand outside it;
4. published measures (cabin.py lists them) override the photos where they disagree, with the owner's leave;
5. what none of them gives is a choice, marked CHOICE where it is made, and kept inside real proportions.

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
| `inhull.py` | checks every cabin vertex and triangle against the built car's body and glass |
| `liner.py` | lines the hull's inside wherever no other part covers it, following the skin and leaving the glass clear |
| `export_glb.py` | the cabin as one mesh with one palette material (one draw) |

Measured so far, outline IoU against each part's own photo: steering wheel 0.985, front seat 0.965 through the
photo's perspective camera (the square-on first pass scored 0.994 square-on, which was the wrong test: 0.73 through
the camera), door trim 0.9995 (the door photo fills its frame, so that figure says little). The cabin photos have
no score: a score against a photo whose camera was fitted to the same photo is circular.

The six photos do not agree with each other or with one camera each (cabin.py lists what was found): dash_front's
door trims are not door_FL's; its wheel is drawn round though seen from the side; rear_bench's bench, belts and
cushion top each ask for a different camera.

Not sourced: the wheel's diameter (0.380 m assumed; it makes the photo's grip 31.5 to 33 mm thick). The seat's size is set by the head restraint rule (seatcam.py). The door trim's scale comes from the model's own door length (1.075 m).

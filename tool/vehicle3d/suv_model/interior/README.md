# SUV interior (work in progress, not reviewed)

The owner's decision (10 Nov): the interior must match his six photos with no difference. The photos are in
`tool/vehicle3d/suv_parts/interior/`; they are measured against, never projected.

State: first passes of the three square-on photos (steering wheel, front seat, front door trim). None has been
through an independent review, and their inner details are mostly still to do.

| File | What it is |
|---|---|
| `masks.py` | finds the photos and their magenta backdrop |
| `zoom.py` | a gridded enlargement of part of a photo, to read coordinates off |
| `relief.py` | a solid from a square-on photo's region: its width across, flat in the middle and rounded to its edge, with its own shading normals |
| `shot.py` | renders the seat or the door trim from its photo's camera and scores it: `python shot.py seat seat.blend out.png` |
| `wheel_measure.py`, `wheel_features.py`, `wheel_seam.npy` | the wheel photo's outline, openings and scale; the pad, switch pods and buttons |
| `steering.py`, `shot_wheel.py` | builds the wheel; renders and scores it |
| `seat_measure.py`, `seat_features.py`, `seat.py` | the seat photo split into parts; first readings of its inner lines; the builder |
| `door_measure.py`, `door.py` | the door trim photo split by colour; the builder |

Measured so far, outline IoU against each photo: steering wheel 0.985, seat 0.994, door trim 0.9995 (the door
photo fills its frame, so that last figure says little).

Not sourced: the wheel's diameter (0.380 m assumed; it makes the photo's grip 31.5 to 33 mm thick) and the seat's
size (1.08 m from the rail's foot to the headrest's top assumed). The door trim's scale comes from the model's own
door length (1.075 m). Not in any of the three photos: depth across the photo's plane. The wheel's `DISH`, `PLATE`
and `PAD_RISE`, the seat's `WIDTHS` and the door's `DEPTH` are placeholders until the cabin photos are measured.

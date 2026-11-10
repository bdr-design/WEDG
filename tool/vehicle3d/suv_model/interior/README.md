# SUV interior (work in progress, not reviewed)

The owner's decision (10 Nov): the interior must match his six photos with no difference. The photos are in
`tool/vehicle3d/suv_parts/interior/`; they are measured against, never projected.

State: only the steering wheel is started, and it has not been through an independent review.

| File | What it is |
|---|---|
| `masks.py` | finds the photos and their magenta backdrop |
| `zoom.py` | a gridded enlargement of part of a photo, to read coordinates off |
| `wheel_measure.py` | the wheel photo's outline, openings and scale (the photo is 2.7 % taller than wide and is taken as stretched) |
| `wheel_features.py` | the pad, the switch pods and their buttons, read off enlargements and snapped to the photo's edges |
| `wheel_seam.npy` | the pad's seam, traced on the photo (pixels, row then column) |
| `steering.py` | builds the wheel: `python steering.py out.blend` |
| `shot_wheel.py` | renders it from the photo's camera and scores it: `python shot_wheel.py wheel.blend out.png` |

Measured so far (steering wheel): outline IoU 0.985 against the photo.

Not sourced: the wheel's diameter (0.380 m assumed; it makes the photo's grip 31.5 to 33 mm thick). Not in the
photo: every depth (the photo is square-on); `DISH`, `PLATE` and `PAD_RISE` in `steering.py` are placeholders.

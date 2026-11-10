# Reviewing the SUV model: brief for an independent review agent

The owner's rule (CLAUDE.md): Claude builds everything itself; agents only review. A reviewer changes no file of the
model. It measures, reproduces and reports; each finding is then re-measured before anything is changed.

## What is being reviewed
An SUV modelled from scratch in Blender by code (this folder), in the shape of a Land Cruiser 300 ZX with no badges.
The owner's four orthographic photos are AI renders and are used only to measure against; they are never projected
on the model. Dimensions come from the official spec sheet and one real side photo (DIMENSIONS.md).

## Frames
- Real frame (the model): x forward with the car centred on x = 0 (nose +2.4925, front axle +1.5555, rear axle
  -1.2945), y to the car's left, z up from the ground, metres.
- Photo frame: the owner's photos through views.json (side: x = 2.495 - (u - 40) * 0.0029422, z = (821 - v) *
  0.0029422; front: y = (u - 627.5) * 0.00189005 * 0.97242, z = (1172 - v) * 0.00189005; rear: y = (627 - u) *
  0.0019445 * 1.02853, z = (1159 - v) * 0.0019445; top: x = 2.495 - (v - 80) * 0.0027478, y = (396.5 - u) *
  0.0027478 * 1.08049 * 1.026).
- realframe.py maps photo frame -> real frame (x_real, y_real, z_real) and back.

## Tools
- Build: `blendenv/bin/python build.py out/<run> render` writes suv.blend, q34.png, wheel.png.
- Score: `REAL=1 blendenv/bin/python compare_ext.py out/<run>/suv.blend out/<run>/cmp` renders the model from each
  photo's own orthographic camera and writes, per view, `<view>.png` (the render), `<view>_photo_real.jpg` (the photo
  mapped to the real frame, pixel-aligned with the render), `<view>_side.jpg`, `<view>_overlay.jpg` (red: photo only,
  blue: render only) and scores.json. In those images a pixel is s metres (views.json) in the real frame.
- Open suv.blend with bpy to measure the mesh directly (bounding boxes, ray casts, object names).
- Soundness: `volcheck.py <blend>` (every part: volume, open and over-shared edges, zero faces) and `backface.py
  <blend> <out_dir> name:x,y,z:lx,ly,lz:lens ...` (red where a back face shows from outside).
- Both ends without the full build: `btest.py <out.blend> [norear] [front]` (saved in the real frame).
- The tail (scratch tools, tools/): rearsil, plansec, gatex, toptail, loops, sidehit, rcmp; DIMENSIONS.md 7.6.

## What to check
1. Every number in DIMENSIONS.md against its source: recompute the derived ones, and measure the photo ones yourself
   on the photos.
2. The model against DIMENSIONS.md: measure suv.blend (length, width, height, axles, hub, tyre, clearance, arches,
   rails, steps, handles, shut lines).
3. The model against the photos: crop the render and the mapped photo to each feature and measure the difference in
   millimetres. Say which differences come from the photos being wrong or disagreeing, and which from the model.
4. The code: mistakes, dead or misleading comments, numbers with no source that are not marked as a game choice.
5. The scorer: anything that would flatter or punish the model unfairly.
6. Geometry faults visible in perspective renders: holes, flipped normals, parts floating or sunk, z-fighting.

## Report
A list of findings, most serious first. For each: what is wrong, where (file and line, or the feature and view), the
numbers you measured and how to reproduce them, and how sure you are. Separate facts you measured from guesses.
Do not fix anything.

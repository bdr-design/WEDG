# Building the SUV from scratch: brief for each building agent

The owner wants the SUV modelled from scratch in Blender, matching his photos to the millimetre. The photos are
references only: never project or print them on the model. Use real modelled geometry and real materials (gloss
black paint, chrome, glass, rubber, black plastic, lamp lenses, emission for the lamps).

## Frame and tools (all paths are under /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad)
- Model frame: x forward (the nose is at x 2.498, the tail at -2.492), y to the car's left, z up from the ground,
  in metres. This is the photos' own frame (vehicles/suv2/views.json maps every photo pixel to it).
- Photos: vehicles/Black_SUV_Views/01_left.png (left side, nose to the left), 02_front.png, 03_rear.png and 04_top.png
  (nose up). All are orthographic on magenta. suvm/out/02_front_grid.jpg and 03_rear_grid.jpg have a 10 cm grid
  drawn over the front and rear (bright lines every 0.5 m, y = 0 on the centre line, z = 0 at the ground).
- Pixel to metre: side u -> x = 2.495 - (u - 40) * 0.0029393, v -> z = (821 - v) * 0.0029393.
  front u -> y = (u - 627.5) * 0.0018882 * 0.97242, v -> z = (1172 - v) * 0.0018882.
  rear u -> y = (627 - u) * 0.0019426 * 1.02853, v -> z = (1159 - v) * 0.0019426.
  top v -> x = 2.495 - (v - 80) * 0.0027450, u -> y = (396.5 - u) * 0.0027450 * 1.0805 * 1.026.
- Blender: blendenv/bin/python (bpy 5.x as a module). Build the whole car with
  `cd <your dir> && ../blendenv/bin/python build.py out/<run> render` (writes suv.blend, q34.png and wheel.png).
- Score it with `../blendenv/bin/python ../suv/compare_ext.py out/<run>/suv.blend out/<run>/cmp`. This renders the
  model from the exact camera of each photo, then prints the silhouette IoU, the edge distance (mm) and the colour
  error. It writes <view>.png (the render, pixel-aligned with the photo), <view>_side.jpg and <view>_overlay.jpg
  (red: in the photo only, blue: in the render only). Set SCORE_VIEWS=front to render only some views.
  For your own part, crop both the render and the photo to its region and measure there (edges, positions in mm).
- The photos disagree slightly with one another (for example the top view is about 2.5 % narrower than the front;
  the scorer corrects this with TOP_K). Where two views disagree, follow the view that shows the feature face-on.

## Rules
- Work only in your own copy of the build folder (named in your task). Edit only the files you own; read the others.
- Keep the function names and signatures that build.py calls, so your file drops back into the main build.
- Keep it light enough for a phone: stay within the triangle budget given in your task.
- Measure, change, rebuild, score, look at the side-by-sides; repeat until your part matches as closely as the
  photos allow. Positions should be within a few millimetres where the photo is sharp.
- Finish with a short report: what you built, scores before and after (whole views and your own region), what still
  differs and why (for example, where the photos contradict each other).

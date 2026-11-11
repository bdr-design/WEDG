# SUV fully modelled in Blender from scratch (owner's decision, 9 Nov 2026)

The owner rejected the photo-projected model ("ماتشبه صوري") and asked for the whole SUV, exterior and interior,
to be modelled from scratch in Blender like a 3D artist would. The photos are references to measure against only,
and are never printed on the model. Materials are real: gloss black paint, chrome, glass, rubber, leather, wood.
Deliverables: a full .blend file and a game GLB. Claude builds everything; agents only review (CLAUDE.md).

References:
- Exterior, orthographic: scratchpad/vehicles/Black_SUV_Views/01_left, 02_front, 03_rear, 04_top (png).
  Mapping to the model frame is in scratchpad/vehicles/suv2/views.json: x forward (centred, L = 4.99), y left,
  z up from the ground.
- Interior: scratchpad/suv/ref_int/ (dash_front, driver_pov, door_FL, wheel, seat_side, rear_bench).
- Rim: scratchpad/suv/rim_rear.png.

Scoring: scratchpad/suv/compare_ext.py renders any model from the four exterior photo cameras. It prints the
silhouette IoU, the edge distance in mm and the colour error, and writes side-by-sides and overlays. The goal is
IoU ≥ 0.97 in every view, with the features (lamps, grille, windows, door lines, arches) within about 1 cm.
As of r11 the side, front and top views meet it (0.990, 0.971, 0.989) and the rear does not (0.952): the rear photo
disagrees with the spec's width, which the model keeps (DIMENSIONS.md sections 3, 4 and 6).

Steps:
1. Body shell: a quad loft of cross sections from the side, front and top outlines (mirrors and wheels removed
   from the outlines), with crease edges, smoothed with subdivision. Wheel arches cut and flared.
2. Greenhouse: modelled glass panes and black frames, the B, C and D pillars, the chrome window line.
3. Front: grille frame and bars, headlamp units (housing, lens, projectors, DRL strip), bumper, intake, skid plate.
4. Rear: tail lamps, the chrome garnish, bumper, reflectors, tailgate seam.
5. Sides: door seams, handles, mirrors, roof rails, running boards.
6. Wheels: a modelled 12-spoke two-tone rim from the rim photo, tyres with tread (the owner's photo's size since r10).
7. Interior from the six photos: dash, screen, cluster, centre stack with its silver frame, vents with slats,
   console, shifter, steering wheel, seats with bolsters and seams, door cards, headliner, pillars.
   The owner's decision (10 Nov): the interior must match the six photos with no difference, front and rear alike
   (the glass is blacked out, so it is seen from the driver's eye and through open doors). The photos are in
   tool/vehicle3d/suv_parts/interior/: three square-on (wheel, seat_side, door_FL), measured like the exterior's,
   and three in perspective (dash_front, driver_pov, rear_bench), which need a camera each. They are measured
   against, never projected. The owner's further decisions (10 Nov): published sources may override his photos
   where they conflict; five seats (the official ZX's, though rear_bench shows a third row's headrests); layered
   detail for the game (the player's car close up about 40k outside and the interior about 40k, loaded only from
   inside; 12k at a distance; an impostor far off). Official cabin of the five-seat ZX: 1955 x 1640 x 1190 mm long,
   wide, high (Toyota's 主要諸元表, kakaku.com, carsensor); the seated positions from the Lexus LX 600's published SAE
   figures (same frame and wheelbase). The steering wheel's diameter has no source yet. The state is in
   interior/README.md.
8. Doors and tailgate as hinged parts, the game hooks (as in suv_complete.py: door_*, wheel_*, steering,
   needle_*, eye/eye_look, tail_light/head_light materials), the game GLB and LOD, a performance check in the
   prototype.
9. Agents review each step against the photos with compare_ext.py (brief: REVIEW.md); every finding is re-measured
   before it is acted on; fix; show the owner side by side.

## Two versions of the car (the owner's decision, 11 Nov)

- **Our own, built by code** (this folder: the hull from the owner's photos at the official dimensions, the
  interior from the six photos and published measures, with the photos' detail as textures). Everything in it is
  ours, so it may be used if the game is ever sold. Its last state before any outside model was added is commit
  `0197fe3` on this branch. Keep it that way: nothing from an outside model goes into these files.
- **A private one with a downloaded model** (the owner's game is private and earns nothing): a free Sketchfab model
  of the LC300 (Ddiaz Design, licence CC BY-NC-SA 4.0: no commercial use, the author credited, changes shared alike).
  It goes in its own folder, `thirdparty/`, with its licence and credit beside it, and is never mixed into the
  code-built files. If the game ever earns anything, that folder is dropped and the code-built version used.
- 11 Nov, the owner: the private car is to be the downloaded model whole, outside and inside, with suspension and
  sinking in sand ("تغريز"), lightness first. Built by `thirdparty_build.sh` (see `thirdparty/README.md`):
  - the outside as a near layer (about 40k triangles, wheels on their own corners for the springs, the driver's door
    on its hinge) and a far layer (about 12k);
  - the interior (loaded when the player comes to the car; seen only from the driver's seat and the open door),
    with a turning steering wheel and the door's trim swinging with the door;
  - the ride and the sand in `design/prototype3d/car_physics.js`, its numbers in `docs/GDD.md` section 9.1.

## Progress
- Step 1 (body shell), the wheels, the arches, the mirrors and the roof rails are done. Build b3 scores IoU 0.982
  side, 0.925 front, 0.911 rear, 0.889 top (TOP_K 1.026). Next: the greenhouse (glass panes recessed, black frames,
  the chrome belt strip), using the window outline from suv_complete.py (TOP/ROOF tables, pillars at d 2.70-2.80,
  3.66-3.74, quarter glass to 4.42, windscreen 1.405-1.81 K, rear glass 1.34-1.81 K; x = 2.50 - d, z = value * 1.034).
- Front features measured on 02_front (y, z in m): headlamps y 0.60-0.93, z 1.10-1.21; grille y +-0.60, z 0.665-1.19,
  with 4 chrome bars at z about 1.18, 1.04, 0.91, 0.79; L-shaped chrome DRL bars at y +-0.86, z 0.70-1.10; lower intake
  z 0.32-0.66 with a chrome strip at 0.44; fog lamps at y +-0.88, z 0.48.
- 9 Nov: the owner asked for the dimensions to come from the sources and the photos. DIMENSIONS.md has the official
  ZX figures (4985 x 1980 x 1925, wheelbase 2850, track 1665, 265/55R20) and a real side photo measured against the
  owner's: the photos put the rear axle 119 mm too far back, the wheels 9 % too big and the car about 10 cm high.
  realframe.py maps everything built in the photo frame to the real frame; the arches, shut lines, handles and wheels
  are built in the real frame. The rim is now six V pairs of spokes, as in the photo. Two scorer bugs fixed (the
  front, rear and top renders ignored the photos' sideways stretch; the top camera was turned 180 degrees). Build r4,
  scored with REAL=1: IoU side 0.970, front 0.934, rear 0.943, top 0.986.
- 9 Nov, review round 1 (independent agent, every finding re-measured and confirmed): the official 1925 mm is over
  the roof rails, not the roof; the real photo's height scale is 4.17 mm/px, not 4.27; the wheel is 20 x 8J; the
  photo's tyres are 9 % too big; the arches are not one circle and differ front to rear; the scorer cut nothing at
  the ground and filled holes on one side only. Build r5: the z map now runs through four heights (ground, door
  bottoms 429, window foot 1253, rail tops 1925), the hub is at the loaded 370 mm, the arches are traced on the real
  photo (tops 862 front, 930 rear), and the body steps in under the doors to a black sill that carries the side steps.
  r5, REAL=1: side 0.988, front 0.941, rear 0.951, top 0.986.
- 9 Nov, build r6: the rails taper in plan with the roof and are 50 mm wide (top photo); a roof antenna fin; under
  the floor, a rear rigid axle whose differential sits at the official 225 mm clearance, and the front under-cover
  and lower arms (underbody.py); the shell's underside is matte. r6, REAL=1: side 0.988, front 0.965, rear 0.955,
  top 0.986; 195,898 triangles before any LOD. DIMENSIONS.md section 6 lists what still differs and why.
- 9 to 10 Nov, build r7: wheels closed and re-measured (8J rim), a glass roof from the top photo, the axle tunnel,
  everything under the floor under one clearance rule, a last tidy pass over every mesh. 181,262 triangles.
- 10 Nov, build r8: the rear re-measured on 03_rear and its parts rebuilt on the surface (lamps with level bands, plate
  recess, shut line, reflectors, corner panels, chrome strip and silver plate, sensors, wiper, stop lamp); clear lamp
  covers; a guard in every cut against stray faces. 175,706 triangles.
- 10 Nov, build r9: the tail's surface itself. It was one smeared slope, up to 38 mm off; it is now the side photo's
  silhouette, read to a fraction of a pixel, slid along the bumper's plan from the top photo: a shoulder on the bumper
  that runs round the corners, an upright tailgate behind it, lamps that stand out over it, a crowned rear glass.
  Within 4 mm of the silhouette from the tailgate to the lamps. The side glass's black surround is a clean band.
  Three independent reviews of r9: the first found two misreadings of the top photo and nine smaller faults, the
  second confirmed the corrections and found four more, the third confirmed those. All are corrected but those
  listed at the end of DIMENSIONS.md 7.4.
  r9, REAL=1: side 0.989, front 0.970, rear 0.950, top 0.989; 190,448 triangles before any LOD. DIMENSIONS.md
  section 7 has the measurements, section 6 what still differs and why.
- 10 Nov, builds r10 and r11: the owner's decisions: the wheels as his photos draw them (tyre 0.872 m, rim's lip
  0.296 m out, hub 0.408 m; r11 after the review's re-measurement, with the wheel openings from his photo too,
  since the real car's do not hold the bigger wheel), and the glass roof stays. The windshield's side edges are cut
  along their knee and its surround is a band (r11). The outlines are read to a fraction of a pixel, which takes the bands out
  of the hood's and the flanks' reflections. The model builds from the repository alone, and the built suv.blend is
  kept beside the code. r12 sets the openings round the hubs unscaled, as the wheels are, after the r11 review found the rear wheel forward in
  its opening. r13 ends the side step ahead of the rear opening; r14 thins the flare bands (the owner's decision), so their tops stay
  where the photo has them. r14, REAL=1: side 0.990, front 0.971, rear 0.952, top 0.989; 190,050 triangles.
- 10 Nov, build r15: the owner's decisions: no mud flaps, and the glass blacked out all round (opaque black, the
  panes' lips marked sharp so the dark glass shades clean along leaning edges).
- 10 Nov, build r16: the windshield's pane widened to the front photo's glass (it was 4 to 7 cm narrow a side).
  190,126 triangles.
- 10 Nov, builds r17 and r18: the crease along the greenhouse's side that the owner saw from the front (the front
  outline was bridged straight behind the mirrors), and the rear door's shut line stopped at the rear flare. The
  review of r16 confirmed r13 to r16. 190,218 triangles.
- 10 Nov, build r19: the review of r18 confirmed the crease gone and found the mirrors left off the narrowed doors
  and the side glass hollow in section: the glass is flat now, the turn is in the shoulder under the belt, and the
  mirrors' arms reach the doors. r19, REAL=1: side 0.990, front 0.973, rear 0.951, top 0.989; 190,230 triangles.
- 10 Nov, builds r21 and r22: every side pane flat from its foot (review of r19); Saudi number plates reading
  ا م ن 1, front and rear (plate.py). 189,749 triangles.
- 10 Nov, builds r23 and r24: the body side rebuilt from 04_top (DIMENSIONS.md 8) after the review of r21: the side
  glass an arc onto the top photo's chrome line, the shoulder hung on the belt, doors narrower than the fenders so
  the side step shows, step and flares on the top photo's outline; top IoU 0.993. r24 after the review of r23:
  handles laid along the skin, plates seated (and the band moved to the middle), the hull's rows kept in place.
- 10 Nov, build r25, the owner's decisions on r24's pictures: the rear door swells gently out to the fender round
  the wheel (r24's sweep read as a diagonal crease from behind) and the rear flare's front leg is thinned to 2 to
  3 cm proud of the door. IoU side 0.989, front 0.975, rear 0.950, top 0.993.
- 10 Nov, build r20: the belt line raised to the photo's chrome line (it was 2 to 4.5 cm low) and the quarter glass's
  lower edge kicked up to its rear edge as in the photo, with the chrome strip along it. 189,764 triangles.
- 10 Nov, build r26: the rear wheels' wells cut to 0.665 m from the middle (0.60 before), out of the cabin.
- 10 Nov, the interior (step 7), four rounds of independent review: the whole cabin stands inside the hull, laid
  out from the official cabin and the LX 600's seated positions, with the photos' shapes. Its near layer
  (lod_cabin.py: faces no occupant sees dropped) is 44k triangles and draws once. Open: slivers of bare hull at the
  glass's edges and round the tailgate's top (the windows' seals), a few crossing triangles behind trims. The outside's layers
  (lod_ext.py, bake_lod.py): a near layer of 55k (the full car's light baked into the body's normals, the glass and
  lamps kept fuller) differs from the full car on 1.3 % of pixels; a 12k distance layer on 1.2 % from 13 m. Not yet
  reviewed or exported.
- Next: the outside's layers with baked normals done properly; the interior's remaining photo differences (the
  bench's and seats' finer shapes, the door's switch panel, the shifter); the quarter glass's kick-up and chrome
  surround, lug nuts, step tread; opening doors.

## Back to our car in the game (the owner's decision, 11 Nov, after trying the game on his phone)

The downloaded model, thinned from 1.1 million triangles to 65k for the phone, showed facets and odd shading. The
owner chose our code-built car (this folder) for the game again. `ours_game.py` makes its game files from
`suv.blend`:
- `lod_ext.py ... 150000 game`: the near layer, 150k triangles (185k of 210k are seen; the wheels, arches and chrome
  keep more).
- `lod_ext.py ... 15000 far`: the far layer.
- The wheels sit on their corners for the springs and steering. The driver's eye comes from `interior/cabin.py`'s
  SEATED_EYE, and the cabin from `cabin_lod0.glb` (44k).

The game files are `design/prototype3d/models/veh_suvfull.json`, `veh_suvfar.json` and `veh_suvcabin.json`. The
player's car casts no shadow (the owner's word).

Moving parts and the seat view (12 Nov, ours_game.py):
- The driver's door is cut from the body along its shut lines (door_split) with its window, chrome, handle and mirror,
  under 'door_FL' at the hinge (9k triangles, 7 draws); the cabin's door trim swings with it ('doorcard_FL').
- The steering wheel is apart from the cabin (from the full cabin.glb by its loose pieces in the wheel's sweep) under
  'steering' on the column's axis; play.js turns it 15 times the road wheels' angle.
- The cabin layer is rebuilt from the full cabin.glb: culled from the seats' eyes and from the open doorway, the wheel
  and the trim kept whole as they move (53k triangles, three draws).
- seat_split: what no eye round the seated eye sees, past the cabin and through the glass, is under 'outside', which
  the game hides in the seat view (the seat view was 449k triangles against the 400k budget). Faces seen from behind
  count, since the paint and trim go out two-sided.


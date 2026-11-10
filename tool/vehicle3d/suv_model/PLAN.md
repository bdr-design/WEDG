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
   against, never projected. Official cabin size (a Japanese listing's catalogue figures, to be checked against
   Toyota's sheet): 2775 x 1635 x 1215 mm long, wide, high. The steering wheel's diameter has no source yet.
8. Doors and tailgate as hinged parts, the game hooks (as in suv_complete.py: door_*, wheel_*, steering,
   needle_*, eye/eye_look, tail_light/head_light materials), the game GLB and LOD, a performance check in the
   prototype.
9. Agents review each step against the photos with compare_ext.py (brief: REVIEW.md); every finding is re-measured
   before it is acted on; fix; show the owner side by side.

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
- Next: the quarter glass's
  kick-up and chrome surround, lug nuts, step tread; then the interior (step 7), opening doors, GLB and LOD.

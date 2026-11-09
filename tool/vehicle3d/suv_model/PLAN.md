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

Steps:
1. Body shell: a quad loft of cross sections from the side, front and top outlines (mirrors and wheels removed
   from the outlines), with crease edges, smoothed with subdivision. Wheel arches cut and flared.
2. Greenhouse: modelled glass panes and black frames, the B, C and D pillars, the chrome window line.
3. Front: grille frame and bars, headlamp units (housing, lens, projectors, DRL strip), bumper, intake, skid plate.
4. Rear: tail lamps, the chrome garnish, bumper, reflectors, tailgate seam.
5. Sides: door seams, handles, mirrors, roof rails, running boards.
6. Wheels: a modelled 12-spoke two-tone rim from the rim photo, 265/55R20 tyres with tread.
7. Interior from the six photos: dash, screen, cluster, centre stack with its silver frame, vents with slats,
   console, shifter, steering wheel, seats with bolsters and seams, door cards, headliner, pillars.
8. Doors and tailgate as hinged parts, the game hooks (as in suv_complete.py: door_*, wheel_*, steering,
   needle_*, eye/eye_look, tail_light/head_light materials), the game GLB and LOD, a performance check in the
   prototype.
9. Agents review each step against the photos with compare_ext.py; fix; show the owner side by side.

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
  owner's: the photos put the rear axle 119 mm too far back, the wheels 8 % too big and the car about 5 cm high.
  realframe.py maps everything built in the photo frame to the real frame; the arches, shut lines, handles and wheels
  are built in the real frame. The rim is now six V pairs of spokes, as in the photo. Two scorer bugs fixed (the
  front, rear and top renders ignored the photos' sideways stretch; the top camera was turned 180 degrees). Build r4,
  scored with REAL=1: IoU side 0.970, front 0.934, rear 0.943, top 0.986.

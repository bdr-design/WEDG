# Vehicles from four photos

The owner generates four orthographic photos of each vehicle on magenta:
left side, front, rear and top. They live in
`assets_src/vehicles/<Name>_Views/` with the prompts used. This folder turns
them into game models.

## Steps

1. **`build_vehicle.py`** (shape):
   - Cuts each view out of the magenta background.
   - Scales the side and top views to the real length and the front and
     rear views to the same height. The AI views disagree slightly on width,
     so each is stretched sideways to the real width.
   - Keeps the space that lies inside all four silhouettes (the visual hull).
     By default (`HULL=sdf`) each outline becomes a signed distance in
     metres, sampled between pixels, so the long, nearly flat bonnet and
     roof have no voxel terraces:
     - Notches narrower than `CLOSE` px are keying noise and are closed.
     - The outlines are smoothed (`SDF_SIGMA` px), and more along the car's
       length (`LEN_SIGMA` px). This flattens the waves that a straight pull
       of the top outline turned into vertical streaks on the doors, while
       the nose and tail keep their place. The front and rear outlines are
       smoothed across the width as well, which takes the ribs out of the roof.
     - The views meet in a rounded intersection (`ROUND`, 1.2 cm).
     - Outside each outline, the photo's background is filled with the edge
       colour for only `FILL_PUSH` steps, then with dark paint. A hull edge
       that reaches past an outline never picks up stretched fill.
     `HULL=voxel` keeps the old binary grid.
   - Meshes it with marching cubes, smooths it lightly (Taubin), and stores a
     smoothed normal field.
2. **`bake_vehicle.py`** (texture):
   - Projects each photo onto the surfaces that face its camera. A smoothed
     normal field decides which photo paints which surface.
   - Background seen through windows or chassis gaps becomes dark glass or
     shadow.
   - Bakes everything into one 2K texture, sets paint roughness and
     clearcoat, exports a GLB, and renders check images in desert light.

## Models

| Model | Real size used | Triangles | GLB |
|---|---|---|---|
| `shas` (LC70-style single-cab pickup, white) | 5.22 × 2.12 m | 30k | 1.5 MB |
| `suv` (LC300-style SUV, black) | 4.99 × 2.2 m | 30k | 1.3 MB |
| `tractor` (6x4 tractor unit, red) | 6.9 × 2.85 m | 30k | 1.4 MB |
| `caravan` (shepherd's cabin on a flatbed) | 12.5 × 3.2 m | 24k | 1.2 MB |

## Running it

```
blendenv/bin/python build_vehicle.py <views folder> <name> <length> <voxel> <tris> <roughness> <clearcoat> <width incl. mirrors>
VEH=<name> blendenv/bin/python bake_vehicle.py
```

`bake_vehicle.py` imports `blend_common.py` from `tool/camel3d`.

## Limits

- A visual hull cannot carve hollows. The pickup bed is filled to its walls,
  and the photo of the empty bed is painted on top.
- No logos or names, by design: the brands are trademarks.

## The owner's SUV, completed for driving (`suv_complete.py`)

The black SUV from the owner's photos, made drivable from inside. Output:
`assets_src/vehicles/suv_full.glb`.

The hull was built with `HULL=sdf SDF_SIGMA=7 CLOSE=15 FILL_PUSH=3 TAUBIN=4`, 8 mm voxels and 36k triangles, then baked.

```
blendenv/bin/python suv_complete.py <out_dir> [render|quick|ext]
```

- **Glass:** every edge of the glass is first cut into the hull as a plane: the belt, the A pillar, the B and C pillars, the quarter glass corner, the windscreen and the rear glass. Then the faces are sorted by those planes, so every edge is straight.
  - The glass is dark and untextured, and is seen from outside only. From the driver's seat it is clear.
  - The windscreen and front door glass are at 50 % opacity. Behind the B pillar it is privacy glass at 78 %.
- **Doors and tailgate:** cut on the same planes into their own objects, with hinges at their front (doors) or top (tailgate) edge.
- **Wheel wells:** a boolean cylinder per wheel. Its walls become the black liner.
- **Wheels:**
  - Tyres are 265/55R20, as on the LC300 VX/ZX in Toyota's spec sheets. The AI photo drew them 0.86 m across; the real 0.80 m is used.
  - The rim face is the real rim cut from the side photo (`suv_parts/rim_rear.png`).
  - The tyre has a tread and sidewall maps with no lettering.
- **Paint (`suv_exterior.py`):**
  - The dark, neutral paint pixels of the photo texture are pushed darker.
  - The photo's own sky and tree reflections inside wide paint areas are pulled to the paint around them.
  - The material is solid black: a satin colour layer with a full clear coat.
- **Lamps:** the faces around the head and tail lamps have their own materials. Their emission maps are cut from the photo: white for the daytime running lamps, red for the tail lamps. The game lights the tail lamps when braking.
- **Cabin (`suv_interior.py`, textures from `int_tex.py`):**
  - Laid out in real metres, left-hand drive.
  - The photo skin is lined on the inside: an offset copy is smoothed, decimated and cut into material bands. Rims close every opening.
  - Signed-distance seats with perforated inserts and seams, a dashboard with an instrument hood and vents, a console with a wood top, and a steering wheel with wood arcs.
  - The centre screen and cluster (with Arabic text) are emissive. The cluster needles are separate objects.
  - Also: a mirror, visors, grab handles, belts, door armrests with switches, and scuff plates on the sills.
- **Wipers:** two at the foot of the windscreen and one on the rear glass, which lifts with the tailgate. The plain glass no longer carries the photo's painted ones.
- **Game hooks:**
  - Objects: `door_FL`/`FR`/`RL`/`RR`, `tailgate`, `wheel_*`, `steering`, `needle_speed`, `needle_rpm`.
  - Empties: `eye` and `eye_look` for the first-person camera.
  - Materials: `tail_light` and `head_light`.
- **Shading:** the importer's custom normals are dropped, because they leave seams along the cuts. Shading is smooth by angle at 75°, so only the liners and rims keep hard edges.
- **Weight:** about 96k triangles: body about 34k, cabin about 34k. The door trims are joined into the doors, which saves draws. Only the outer skin, the lamps and the wheels cast shadows.
- **Measured in the prototype:** at a phone viewport, the heaviest frames measured, shadow pass included, were 195 draws (seen from above the farm) and 342k triangles (walking by the car). The budget is 200 draws and 400k triangles. The game shows the full model only within 20 m or while driving; beyond that it uses a 12k model of the same hull (`slim_vehicle.py`).

**Known gaps:**
- Up close at wheel height, the reflections on the lower body break into teeth near the arches. The decimated surface still has small waves there. Smoothing it or transferring smoothed normals made it worse, so neither is used.
- The tailgate's chrome strip reads as dull grey, as it does in the photo's dark reflections.
- The far mirror is a thin wedge, because a visual hull cannot carve it.
- The grille and lower bumper are painted, not modelled.
- The reference photos make the body about 3.5 % too short for its height: length over height is 2.50, against 2.59 for the real car (4985/1925 mm).

## The Land Cruiser 300 built by code (`lc300.py`)

`lc300.py` builds the black full-size SUV from code, with no photos projected and no badges or text. The output is `assets_src/vehicles/lc300.glb`.

- **Sources:**
  - Toyota's spec sheets give the dimensions: length 4985 mm, width 1980, height 1925, wheelbase 2850, track 1665, front overhang 935, and 265/65R18 tyres.
  - The side profile is measured on `Black_SUV_Views/01_left` and scaled to the real height.
  - `lc300_overlay.py` draws the model's silhouette over the reference photo to check the match.
- **Body:**
  - A loft of rounded sections for the lower body, with the arches cut out, and a second loft for the greenhouse.
  - Chrome on the window line, the roof line and low on the doors; shut lines.
  - A trapezoid grille with three heavy chrome bars, slim corner lamps with an LED line, and fog slots.
  - Long tail lamps joined by a chrome bar.
  - Running boards, roof rails, mirrors and handles.
- **Moving parts:** separate objects with their pivots in place, so the game can move them.
  - Four doors hinged at the front.
  - The tailgate hinged at the top.
  - Four wheels with tyres and 12-spoke alloys; the front ones steer.
  - The steering wheel.
  - The brake lights, a `taillight` material whose emission the game raises.
- **Interior:**
  - Dashboard with a cluster screen and a centre screen, wood trim and vents.
  - Steering wheel and column.
  - Leather front seats, the second-row bench, the console with the gear selector and armrest.
  - Leather door cards, headliner and carpet.
- **Size:** about 22.7k triangles, 16 materials, a 0.9 MB GLB.

```
python lc300.py out/v render      # q34, rear34, front, side, driver and open-doors renders, plus lc300.glb
python lc300_overlay.py out/v/side.png out/v/overlay.jpg
```

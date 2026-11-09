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
   - Keeps the space that lies inside all four silhouettes (the visual hull)
     on a 1–2.5 cm grid.
   - Meshes it with marching cubes, smooths it (Taubin) so no voxel steps
     show in paint reflections, and stores a smoothed normal field.
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

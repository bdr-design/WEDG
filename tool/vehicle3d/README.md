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

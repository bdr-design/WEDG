# Engine benchmark: which 3D renderer is lightest for Marah

This is a throwaway benchmark for ADR 0005. Each candidate renders the same
scene, runs the same automatic sequence and reports the same numbers. CI
(`.github/workflows/engine-bench.yml`) builds every app and runs it on an
Android emulator.

| Folder | Renderer |
|---|---|
| `flutter_scene_app/` | flutter_scene (Flutter GPU / Impeller) |
| `thermion_app/` | Thermion (Google Filament) |

## The scene (identical in every app)

- **Terrain:** `assets/terrain.glb`, the real Abanat terrain.
  - Three rings, 72.6k triangles, with the 2048 px satellite texture.
  - Axes: x east, y up, z south, in metres from the yard.
- **Camels:** `assets/camel_lod1.glb` (8k triangles, 1K textures, 38 bones),
  with the `walk` clip playing.
  - Instances stand on a jittered grid with 4 m spacing, centred on (0, 0, 0).
  - Each has a random heading and its own clip time offset.
  - They walk in place; no locomotion.
  - `camel_lod0.glb` and `camel_lod2.glb` are there for later LOD tests.
- **Sun:** one directional light with shadows.
  - Direction toward the sun: (-0.791, 0.407, 0.457), a low afternoon sun
    in the west.
  - The shadow covers about ±72 m around the herd.
  - Use the engine's normal shadow filtering, 1536 or the nearest supported
    map size.
- **Sky:** a clear sky colour, plus image-based or ambient light if the
  engine has it.
- **Camera:** looks from (-74, 41, 48) at (0, 1, 0), field of view 40°.
- **Render scale:** at most 1.5× device pixels, if the engine lets us set it.

## The automatic sequence and what it prints

On launch the app runs without input:
1. Logs `BENCH {"engine":"<name>","startup_ms":<ms from main() to the first rendered frame>}`.
2. For each N in 34, 100 and 200:
   - Spawn N camels.
   - Warm up for 3 s.
   - Measure for 10 s.
   - Log `BENCH {"engine":"<name>","n":N,"frames":..,"fps":..,"p50_ms":..,"p90_ms":..,"p99_ms":..,"rss_mb":..}`.
   - Frame times come from Flutter's `FrameTiming.totalSpan`, plus the
     engine's own per-frame time if it reports one, as `engine_p50_ms`.
   - `rss_mb` comes from `ProcessInfo.currentRss`.
3. Logs `BENCH_DONE`.

Print each line with `print()` so it reaches logcat under the `flutter` tag.

## Size

`flutter build apk --release --split-per-abi`. The figure that counts is the
size of `app-arm64-v8a-release.apk`. An empty Flutter app is the baseline.

## Reading the numbers

- **The emulator renders in software** (SwiftShader). Its frame times compare
  the engines' CPU and driver overhead, not real phone GPU speed.
- **APK size, memory and startup** are meaningful as they are.
- **A real mid-range phone has the final word** before ADR 0005 is accepted.

## The yard (`assets/yard/`), ported from the prototype

Made by `tool/world_export/` from the three.js prototype. Every engine loads
the same files.

| File | What it holds |
|---|---|
| `yard.glb` | Every fixed object of the yard and the grazing camp: walls, pens, shades, troughs, room, tent and its furnishings, tank, feed shed, cabin, the water tanker, and the roads draped on the terrain. Merged into 5 materials (a colour palette texture, textiles, walls, mesh panels, ground decals), so it is about 5 draws. 37k triangles, 1.5 MB. No lights and no physical materials. |
| `yard_scatter.json` with `grass_tuft.glb`, `bush.glb`, `stone.glb`, `tamarisk_clump.glb`, `tamarisk_trunk.glb` | Ground cover and trees as instance data: position, yaw, scale and a linear-RGB tint per instance. Grouped in cells, with the prototype's distance bands (draw all, part or none of a cell's instances by distance) and shadow flags. 42,000 grass tufts, 1,500 bushes, 2,600 stones (8 triangles each), plus the tamarisks. |
| `vehicles.json` | Each vehicle: the model GLB (`assets_src/vehicles/*_mobile.glb`, 12k triangles), position, yaw and tint. Also the caravan rig at the camp. |

**Frame:** x east, y up, z south, in metres from the yard, the same as
`terrain.glb`.

**Not in the files:**
- **The ground's look up close.** The prototype multiplies the satellite
  colour by the owner's sand photo near the camera. That is a terrain
  material, done in the engine.
- **The final colours of grass and trees.** They depend on the engine's sky
  and ambient light.

**Checked:** loading only these files in a plain three.js page
(`tool/world_export/verify.html`) gives the same yard as the prototype from
the drone view. Geometry and placement match. The colours differ only
because that page has no sand detail and no sky lighting.

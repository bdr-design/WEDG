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

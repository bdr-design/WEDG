# Bench Thermion

The Thermion (Google Filament) candidate of the engine benchmark in
`../README.md`. It is an Android app (`com.marah.bench.thermion`) and it is
not part of the repo's pub workspace.

- **Versions:** `thermion_flutter` and `thermion_dart` 0.6.1, pinned. They
  bundle Filament v1.77.2.
- **Native build:** `thermion_dart`'s Dart build hook downloads the
  prebuilt Filament archives from
  `pub-c8b6266320924116aaddce03b5313c0a.r2.dev`. It then compiles
  Thermion's C++ with the Android NDK for each ABI. The first build needs
  that host and takes several minutes.
- **Renderer:** Filament's OpenGL ES backend. On Android, Thermion never
  uses Vulkan.

## What it does

The app follows the automatic sequence of `../README.md` and prints the
`BENCH` lines. Each per-N line also carries these fields:

- `engine_*`: the time of each Thermion render on its render thread:
  animations, culling, command recording and `endFrame`. The GL driver
  thread is not included. `FrameTiming.totalSpan` only covers Flutter
  compositing Thermion's texture.
- `spawn_ms`, `visible_renderables` and `render_px`.

The comments in `lib/src/bench_scene.dart` explain each scene choice.

## Tests

The pure logic has unit tests in `test/`: the herd layout, the percentiles
and BENCH lines, the sky harmonics and the bundled assets. Running
`flutter test` in this folder also builds Thermion's native library for the
host. That needs the Filament host above, plus Clang and libc++ 18 on
Linux. Without them, copy `lib/src/{bench_stats,herd_layout,sky_light}.dart`,
`test/` and `assets/` into a scratch package that has no Thermion
dependency, and run the tests there.

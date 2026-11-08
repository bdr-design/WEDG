# Which 3D renderer is lightest for Marah (research, 2026-11-08)

This feeds [ADR 0005](adr/0005-3d-world.md) and the benchmark in
`tool/engine_bench/`. It was researched by an agent, and the two key claims
were re-checked against the sources (marked **checked**). Tags:
- **[M]** measured by the researcher.
- **[3p]** measured by a named third party.
- **[C]** claimed by docs or the maintainer.
- **[I]** inference.

## Ranking (lightness first, realism second)

| Rank | Option | Added size (arm64) | Runtime model | Budget features | Maturity |
|---|---|---|---|---|---|
| 1 | flutter_scene 0.24.3 (Flutter GPU / Impeller) | About 3–6 MB [I]; package assets 1.1 MB [M] | Draws inside Flutter's own Impeller frame, so no second GPU context and no texture copy. Dart scene graph on the UI thread. | Skinned glTF with blending, instancing with per-instance data, custom vertex stage that can read textures, KTX2 to ETC2, cached static shadow tiles, LOD [C] | MIT, one strong maintainer, breaking minor releases |
| 2 | Thermion 0.6.1 (Filament) | About 6–9 MB [I]; Filament core 2.96 MB and glTF loader 3.09 MB uncompressed [M] | Native C++ renderer on its own thread, shown through a Flutter Texture. Android uses Filament's OpenGL ES backend. | Clip crossfade, instancing (count only), KTX2, PCF/VSM/PCSS cascaded shadows, custom materials. No LOD or static-shadow cache API [I]. | Apache-2.0, one main maintainer |
| 3 | three_js Dart port (flutter_angle) | ANGLE adds 6.4 MB uncompressed [M] | Dart scene graph plus a Dart WebGL port over FFI | No KTX2 [M]; known Android bugs | One maintainer |
| 4 | WebView running the three.js prototype | About 0 MB native | Separate renderer and GPU processes; a bridge each frame; platform-view compositing | Everything the prototype has | Varies by the device's WebView |
| 5 | Unity as a Library | About 30–40 MB [3p] | Two engines; 80–180 MB kept after unload [C] | Best tooling | Plugin depends on undocumented Unity calls |

Not viable now: flame_3d, flutter3d and Godot embedding (experimental or
stubs).

## The finding that matters most: mid-range Android runs OpenGL ES

**Checked** against Flutter's engine source (`impeller/renderer/backend/vulkan/driver_info_vk.cc`):
- Impeller turns Vulkan off for Adreno 650 and older, which covers the whole
  5xx/6xx range in many mid-range phones.
- It turns Vulkan off for all Huawei GPUs.
- It turns Vulkan off for Samsung Xclipse below Vulkan 1.3.
- Those phones use Impeller's OpenGL ES path.
- Below Android 10 (API 29), Flutter uses Skia, and Flutter GPU is not
  available at all.

**Checked** against flutter_scene issue #484 (0.24.3, Firebase Test Lab).
The scene was one room with about 525 static meshes, 2 skinned characters,
a 2048 px sun shadow and a shadowed spot light:

| Phone | Backend | fps | Raster |
|---|---|---|---|
| Pixel 6a | Vulkan | 59 | 14 ms |
| Galaxy A52s (Adreno 642L) | OpenGL ES fallback | 12 | 122 ms |
| Galaxy A16 | OpenGL ES | 9 | 184 ms |

- **Shadows:** removing them was the biggest single saving (122 → 45 ms on
  the A52s).
- **Unity on the same scene:** 60 fps on the first three phones, about 30 fps
  on the A52s.
- **Maintainer's view:** GPU time is similar on both backends, and the
  OpenGL ES slowness comes from frame pacing. He recommends `renderScale` and
  fewer shadowed lights.

## What this means for the plan

1. Keep flutter_scene first, behind `WorldRenderer`, with Thermion as the
   measured alternative.
2. **The deciding phone is an OpenGL ES-fallback phone** (an Adreno 6xx
   Galaxy A model, or an A16), not a Vulkan flagship.
3. Run the same benchmark on Thermion. **Switch** if flutter_scene misses
   the budget on that phone, even with live shadows from camels only, and
   Thermion meets it.
4. Android minSdk 29.
5. WebView and Unity are out for weight. three_js fails the compressed
   texture requirement.

**Risks:**
- Live camel shadows are the expensive part on OpenGL ES.
- flutter_scene's LOD reportedly draws level 0 in shadow passes. Shadows
  from a lighter mesh need a hidden shadow-only mesh, or per-pass selection.
- Both alternatives depend on one maintainer each.

## Sources

- https://pub.dev/packages/flutter_scene
- https://github.com/bdero/flutter_scene/issues/484
- https://github.com/bdero/flutter_scene/issues/444
- https://github.com/flutter/flutter/blob/main/engine/src/flutter/impeller/renderer/backend/vulkan/driver_info_vk.cc
- https://github.com/flutter/flutter/blob/main/engine/src/flutter/shell/platform/android/flutter_main.cc
- https://pub.dev/packages/thermion_flutter and https://github.com/nmfisher/thermion
- https://repo1.maven.org/maven2/com/google/android/filament/
- https://pub.dev/packages/three_js and https://pub.dev/packages/flutter_angle
- https://pub.dev/packages/flutter_embed_unity and https://docs.unity3d.com/Manual/UnityasaLibrary.html
- https://developer.android.com/topic/performance/memory/guide/webview-memory

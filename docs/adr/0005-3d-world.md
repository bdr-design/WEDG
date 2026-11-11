# ADR 0005: A real-time 3D world

- Status: proposed. The owner chose the direction on 2026-11-08. It
  becomes accepted only after the engine spike below passes.
- Deciders: owner ("very realistic, like a 3D world"; later chose to have
  Claude build the models by code), Claude.

## Context

The owner rejected the 2D screens. The map is the centre of play (GDD §9),
and it must be a realistic 3D world. The camera moves, rotates and zooms
from the Kingdom down to a single camel.

The game stays in Flutter. The domain, saves and worker isolate (ADRs
0001–0004) do not change. Only the app layer gains a 3D view.

## Options

| Option | For | Against |
|---|---|---|
| **flutter_scene** (Flutter GPU / Impeller), MIT | Official Flutter track. PBR, image-based lighting, shadows, instancing, automatic LODs, skinned animation with blending, post-processing, on iOS, Android and web. Runs on our Flutter 3.47 stable. | Pre-1.0: minor releases can break the API. No built-in terrain. |
| Thermion (Filament), Apache-2.0 | Filament is a mature PBR renderer. | One maintainer. Fewer documented features (shadows and instancing not listed). Native assets flag. |
| Unity as a library inside Flutter | Best tooling for terrain, animation and LOD | Two engines, much larger app, harder builds; conflicts with "light". |
| Port the game to Unity | Best long-term 3D tooling | Throws away the Dart domain and tests. |

## Decision (pending the spike)

1. Render with **flutter_scene**, pinned to an exact version.
2. Put it behind our own interface (`WorldRenderer`, a new
   `packages/marah_world`). Screens and the engine never import the 3D
   package directly. If flutter_scene fails us, only this package changes
   (Thermion is the fallback).
3. The world is drawn from `PlayerSnapshot`s. The renderer owns no game
   state. The worker isolate stays the only owner of the game.
4. **Lightness budget:**
   - Only camels near the camera are animated. Far ones get a cheaper
     mesh, and the farthest are drawn as instanced impostors.
   - One camel mesh per body type. The six colours are textures, not
     separate models.
   - Compressed textures and meshes.
   - A frame-time budget per device class, checked by a benchmark scene
     in CI. The numbers are in "Measured budget" below.
5. **Geography:**
   - The Kingdom and regions come from real elevation data and real
     satellite imagery, so the Nafud, Tuwaiq and Dahna are real.
   - Pens, shades, troughs and fences are built in code at real size.
6. **Models:** built by code from the owner's photos (`tool/camel3d`,
   `tool/vehicle3d`, `tool/terrain3d`), each checked against the photo,
   breed measurements and gait sources by independent review.

## Measured budget (from the three.js prototype, 2026-11-08)

A performance review measured the prototype at a 390 × 844 phone viewport.
The fixes below were applied to the prototype (`design/prototype3d/`).

| View | Before: draws / triangles | After |
|---|---|---|
| Drone | 457 / 916k | 221 / 236k |
| Near the herd | 59 / 776k | 56 / 245k |
| Farm room | 308 / 998k | 175 / 280k |
| Grazing camp | 258 / 838k | 50 / 184k |
| Hill (70 km terrain) | 42 / 647k | 7 / 76k |

Counts include the shadow pass. Texture memory went from 217 to 99 MiB.

*Correction (2026-11-11):* these counts came from `renderer.info`, which
three.js resets after the shadow pass, so they left the shadow pass out.
The counts below are taken at each draw call instead.

**What made the difference:**
- Grass, bushes and stones were split into cells, and each cell draws all,
  part or none of its instances by distance.
- The terrain is three rings at 50 m, 100 m and about 550 m (73k triangles,
  not 239k).
- Off-screen camels are culled. The three detail levels share one skeleton
  and one mixer, and the 8k mesh casts the shadow.
- Animation updates every 2nd frame past 48 m and every 4th past 150 m.
- The yard's fixed objects are merged by material.
- Footprints are one instanced mesh.
- Vehicles are 12k triangles with 1K textures.
- PCF shadows on a 1536 map, a render scale of 1.5, anisotropy 4, and
  standard (not physical) materials.
- **Shadows:**
  - Each camel's shadow comes from the next lighter mesh: 8k up close,
    1.5k further out, so far camels now have one.
  - Objects smaller than 30 cm cast none.
  - The shadow area follows the view in 4 m steps, and the map is redrawn
    every other frame.

**Shadows only for the camels?** The owner asked. We measured it in the room
view:
- **Shadow pass:** 63 draws and 93k triangles with every shadow. With the
  camels alone it is 14 draws and 21k.
- **What is lost:** the cars, shade, room and trees no longer shadow the
  ground, so they look like they are floating in the low afternoon sun.

**Decision:**
- **Prototype:** keep every shadow.
- **Flutter build:** static objects (buildings, shades, fences, trees,
  parked vehicles) go in a cached shadow map, refreshed only when the sun
  has moved. A game day lasts about 3.4 real hours, so the sun moves about
  1° every 35 s. Only the camels cast live shadows each frame.

**Budget for the Flutter build (checked in CI on a benchmark scene):**
- At most 200 draws and 400k triangles per frame, shadows included.
- At most 80 MiB of textures, compressed (KTX2 with ASTC or ETC2).
- At most 16 skinned camels near the camera, and no allocations per frame.
- Live shadows from camels only; static shadows cached (see above).
- Render scale at most 1.5.

**The herd in three tiers:**
- **Under about 25 m:** skinned camels with blended clips, at most about
  12 to 16.
- **25 to 150 m:** a baked bone-matrix animation texture (3 clips × about
  40 frames × 38 bones is about 112 KB). These are drawn as one instanced
  draw per detail level, with the clip, time and coat set per instance.
- **Beyond 150 m:** two-triangle impostors, one draw for thousands.

Camel state goes to `WorldRenderer` as flat arrays, not as one scene object
per camel.

## Measured again (prototype, 2026-11-11)

The game now has the landscape screen, first-person play, the player's car
with its cabin, and the in-game phone. Measured at 844 × 390 (a phone held
sideways), every draw call of a frame that redraws the shadow map counted:

| View | Before: draws / triangles | After |
|---|---|---|
| Map, drone view | 317 / 282k | 161 / 288k |
| Map, close view | 98 / 232k | 58 / 258k |
| On foot, at the start | 224 / 334k | 111 / 289k |
| On foot, by the car | 282 / 402k | 143 / 350k |
| In the car, from the seat | 276 / 476k | 164 / 434k |
| In the car, from behind | 280 / 395k | 161 / 353k |
| In the car, out on the sand | 94 / 236k | 69 / 182k |

WebGL calls per frame fell by 38 to 48% in every view (for example, the drone
view from 3,162 to 1,693 with the shadow map redrawn). Texture memory, counted
uncompressed with mipmaps, fell from 132 to 103 MiB.

**What made the difference:**
- **Shadow-only stand-ins are no longer drawn in the picture.** They write no
  colour or depth, but three.js still drew them. Their material is now hidden
  while the frame's draw list is built and shown only for the shadow pass.
- **The fixed casters' shadows are baked into merged meshes,** one per 64 m
  square and face side. These are the buildings, shades, fences, tree trunks,
  troughs and parked vehicles. They are the same geometry, so the shadows are
  the same. The yard's shadow draws fell from 37 to about 12.
- **The player's car casts by rigid part:** the body, each hub, each wheel and
  the driver's door, 26 shadow draws down to 10. While the door is shut, the
  body's shadow comes from the far model with its wheels cut out (9k
  triangles, not 54k). Close-up renders against the exact shadow differ in
  under 1% of pixels, all at shadow edges. With the door open, the exact body
  casts.
- **The yard merges by look, not by material.** Plain materials that differ
  only in colour, roughness and metalness share one mesh. Those values are
  stored per vertex and read by the shader, so the picture is unchanged.
- **Ground-cover cells are larger:** 50 m for grass and stones, 160 m for
  bushes. Each cell's density band is taken from its nearest edge, so nothing
  thins near the viewer. Ground-cover draws in the drone view fell from 124
  to 45.
- **The camel's coat textures are shared.** The three detail levels use one
  copy, since the middle and far copies were the same atlas made smaller.
  The normal map is kept at 1024, because the 2048 one held nothing finer (a
  round trip through 1024 differs by 56 dB PSNR).
- **The wheel tracks are one single-pass decal.** three.js draws a
  see-through two-sided material twice and rebuilt its program state 8 times
  a frame.
- **No shadow caster also receives a shadow.** Before, the shadow pass
  switched programs 8 times a frame.
- **`Math.hypot` is gone from the per-frame loops,** because it left garbage
  on every call.

**What is still over or open:**
- **From the driver's seat:** 434k triangles, 8% over 400k. The cabin built
  from the owner's photos is 85k of these. Lightening it is a trade of
  realism for weight, so it is the owner's decision.
- **Skinned meshes:** up to 30 camels are skinned in the prototype. Their
  measured CPU cost is about 0.25 ms per frame on the test machine. The
  three-tier herd above is the Flutter build's plan.
- **Garbage per frame:** about 50 to 75 KB, mostly three.js's animation
  mixer. This is a minor collection every few seconds, not a stutter.
- **Not yet measured on a real phone.** All figures come from headless
  Chromium with a software GPU, so frame times there are not a phone's.

## Spike (must pass before this is accepted)

The spike is a throwaway app, outside the repo. It must show:
- A terrain mesh with a sand PBR material.
- Sun shadows and a sky.
- A skinned glTF that walks, with a blend to a second clip.
- 50, 200 and 500 animated instances, with frame times.
- A custom vertex shader for instanced, texture-baked animation (the
  middle tier above). If flutter_scene cannot do this, that alone triggers
  the fallback.
- KTX2 (ASTC or ETC2) texture upload.
- Release web and Android builds.

## Risks

- **API churn in flutter_scene:** mitigated by pinning the version and by
  the adapter package.
- **Low-end Android:** mitigated by the LOD and impostor budget, and by a
  cap on animated camels in view.
- **AI-made quadruped rigs may move badly:** mitigated by piloting one
  camel first. Simple clips (graze, couch) can be keyed by script on the
  rig if the tools lack them.

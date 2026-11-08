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

**Budget for the Flutter build (checked in CI on a benchmark scene):**
- At most 200 draws and 400k triangles per frame, shadows included.
- At most 80 MiB of textures, compressed (KTX2 with ASTC or ETC2).
- At most 16 skinned camels near the camera, and no allocations per frame.
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

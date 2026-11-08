# ADR 0005: A real-time 3D world

- Status: proposed. The owner chose the direction on 2026-11-08. It
  becomes accepted only after the engine spike below passes.
- Deciders: owner ("very realistic, like a 3D world"; camel models
  generated with AI), Claude.

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
     in CI.
5. **Geography:**
   - The Kingdom and regions come from real elevation data and real
     satellite imagery, so the Nafud, Tuwaiq and Dahna are real.
   - Pens, shades, troughs and fences are built in code at real size.
6. **Models:**
   - The owner generates the camels and vehicles with AI 3D tools.
   - We pilot one camel first and check its proportions, topology,
     textures, rig and animation before generating the rest
     ([../3d-assets.md](../3d-assets.md)).

## Spike (must pass before this is accepted)

The spike is a throwaway app, outside the repo. It must show:
- A terrain mesh with a sand PBR material.
- Sun shadows and a sky.
- A skinned glTF that walks, with a blend to a second clip.
- 50, 200 and 500 animated instances, with frame times.
- Release web and Android builds.

## Risks

- **API churn in flutter_scene:** mitigated by pinning the version and by
  the adapter package.
- **Low-end Android:** mitigated by the LOD and impostor budget, and by a
  cap on animated camels in view.
- **AI-made quadruped rigs may move badly:** mitigated by piloting one
  camel first. Simple clips (graze, couch) can be keyed by script on the
  rig if the tools lack them.

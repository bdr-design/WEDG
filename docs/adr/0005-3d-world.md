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
| Map, drone view | 317 / 282k | 178 / 280k |
| Map, close view | 98 / 232k | 67 / 234k |
| On foot, at the start | 224 / 334k | 123 / 337k |
| On foot, by the car | 282 / 402k | 159 / 397k |
| In the car, from the seat | 276 / 476k | 174 / 483k |
| In the car, from behind | 280 / 395k | 173 / 403k |
| In the car, out on the sand | 94 / 236k | 73 / 238k |

WebGL calls per frame fell by 33 to 40% in the views above (the drone view from
3,162 to 1,911 with the shadow map redrawn); an independent count found 20% on
the open sand. Texture memory, counted uncompressed with mipmaps, fell from 132
to 103 MiB once a camel has been seen up close. Before that it is a little
higher than it was, since the near colour map is now sent with the first camel.

**What made the difference:**
- **Shadow-only stand-ins are no longer drawn in the picture.** They write no
  colour or depth, but three.js still drew them. Their material is now hidden
  while the frame's draw list is built and shown only for the shadow pass.
- **The fixed casters' shadows are baked into merged meshes,** one per 64 m
  square and face side. These are the buildings, shades, fences, tree trunks,
  troughs and parked vehicles. They are the same geometry, so the shadows are
  the same. The yard's shadow draws fell from 37 to about 12.
- **The player's car casts by rigid part:** the body, each hub, each wheel and
  the driver's door, 26 shadow draws down to 10, with the same geometry.
  - A lighter body shadow, from the far model with its wheels cut out, was
    tried and dropped. Review found it changed the car's shadow by about 8% of
    its area, widening the light through the windows. It would have saved
    55k shadow triangles per redraw.
  - Whether to trade that for weight is the owner's call.
- **The yard merges by look, not by material.** Plain materials that differ
  only in colour, roughness and metalness share one mesh. Those values are
  stored per vertex and read by the shader, so the picture is unchanged.
- **Ground-cover cells are larger:** 35 m for grass and stones, 160 m for
  bushes.
  - A cell whose nearest edge is within the first band is drawn whole, so
    nothing thins near the viewer. Further out, a cell is drawn by its
    middle, as before. The grass drawn grows by 20 to 46% (the drone view
    from 7.0k to 8.7k triangles, from the seat 5.0k to 7.3k), about 2k
    triangles of the budget: the price of nothing thinning near the viewer
    (an independent review measured it; this note first said it stayed as
    it was).
  - Ground-cover draws in the drone view fell from 124 to 58.
  - Bush cells cast while any of them can lie in the sun's shadow square,
    tested along its real axes. On the ground that square stretches along the
    sun, to 144 × 354 m.
- **The camel's coat textures are shared.** The three detail levels use one
  copy, since the middle and far copies were the same atlas made smaller.
  The normal map is kept at 1024, because the 2048 one held nothing finer (a
  round trip through 1024 differs by 56 dB PSNR).
- **The wheel tracks are one decal, wound to face up and drawn once.**
  three.js draws a see-through two-sided material twice and rebuilt its
  program state 8 times a frame. They are drawn after the ground's other
  decals.
- **No shadow caster also receives a shadow.** Before, the shadow pass
  switched programs 8 times a frame.
- **`Math.hypot` is gone from the per-frame code,** because it left garbage
  on every call. Only pointer handlers still use it.

**What is still over or open:**
- **From the driver's seat:** 483k triangles, 21% over 400k.
  - The cabin built from the owner's photos is 85k of these, and the car's
    exact shadow is 70k.
  - Lightening either trades realism for weight, so it is the owner's
    decision.
- **Skinned meshes:** up to 30 camels are skinned in the prototype. Their
  measured CPU cost is about 0.25 ms per frame on the test machine. The
  three-tier herd above is the Flutter build's plan.
- **Garbage per frame:** about 50 to 75 KB, mostly three.js's animation
  mixer. This is a minor collection every few seconds, not a stutter.
- **Long session:** 10 rounds of walking, getting in, driving, getting out
  and using the phone, with the JS heap collected between checks. After the
  first round has loaded the cabin and the near detail levels, nothing
  grows: at rounds 4 and 8 there were 175 geometries, 78 textures, 36
  programs, the same scene and DOM, and a heap of 48.5 and 48.6 MiB. The
  cabin's shaders compile in the background as the player walks up to the
  door, so getting in does not stall.
- **Not yet measured on a real phone.** All figures come from headless
  Chromium with a software GPU, so frame times there are not a phone's.

## Measured again (prototype, 2026-11-12)

The player's car is now ours (the owner's choice of 11 Nov), with a driver's
door that swings and a steering wheel that turns, and each camera draws only
what it can see of it. Measured the same way, at 844 × 390:

| View | 11 Nov (our car, first build) | Now |
|---|---|---|
| Map, drone view | 183 / 273k | 183 / 273k |
| On foot, by the car | 154 / 403k | 167 / 394k |
| In the car, from the seat | 139 / 449k | 145 / 361k |
| In the car, from behind | 166 / 411k | 189 / 404k |
| In the car, out on the sand | 63 / 233k | 84 / 226k |

**What made the difference:**
- **Each view draws what it can see** (tool/vehicle3d/suv_model/ours_game.py,
  view_split). Every material's faces are sorted by whether the seated
  driver's eyes see them, past the cabin and through the glass, and whether
  the chase camera's places see them (a fan of 50 degrees either side behind,
  1.6 to 2.6 m up). The seat view leaves 89k triangles of the near layer
  undrawn. The view from behind leaves 10k. The pictures match the old ones
  within 0.2% of pixels; the difference is the herd moving and the number
  plates, which now show their image.
- **The cabin is rebuilt from the full cabin** with the wheel and the door's
  trim apart: 53k triangles in three draws. It is culled from the seats' eyes
  and from the open doorway, since the door now opens.
- **The door** costs 7 draws (its materials) and 9k triangles, moved out of
  the body.

**Still over:**
- **From behind: 404k triangles, 1% over** (resolved later the same day, below:
  382k). The car is 143k of it, the yard
  116k, the shadow pass 82k (59k of it the fixed casters), the camels 30k.
  Lighter than this from behind would mean a coarser car up close, which the
  owner turned down when he chose this car, so it is his call. Two smaller
  options: the grass's near band back to its old size (about 1.5k here), or a
  cached map for the fixed casters' shadows (59k from every frame that redraws
  the shadow map; real engine work).

**Later the same day: every view within the budget.** Measured the same way, at 844 × 390:

| View | Before | Now |
|---|---|---|
| Map, drone view | 183 / 273k | 183 / 252k |
| On foot, by the car | 167 / 394k | 167 / 379k |
| In the car, from the seat | 145 / 361k | 144 / 340k |
| In the car, from behind | 189 / 404k | 187 / 385k |
| In the car, out on the sand | 84 / 226k | 83 / 228k |

Still over, for a moment: **on foot with the driver's door open, 422k** (166
draws) for the 1.2 to 1.55 s the door swings as the player gets in or out.
The whole car and the cabin are drawn then. It was about 443k before the
shadow copies below.

- **The parked vehicles' shadows come from coarse copies**
  (tool/vehicle3d/shadow_proxy.py). The two shas, the tractor and the caravan
  were 48k of the 81k triangles redrawn in every shadow pass, at full detail.
  Each now casts from a copy of 1.4k triangles in place of 12k. The copy stays
  within 3 cm of the full outline for 99% of it, against a shadow texel of
  9.4 cm (1536 texels over 144 m). The copies are baked into the fixed shadow
  meshes like the yard's casters and never drawn; the full models draw as
  before. The shadow pass went from 82k to 61k in every view of the yard.
  The ground shadows match. On the vehicles themselves the self-shadow pattern
  they already had shifts a little: 0.07% of pixels in the yard's views, up to
  2.7% in a close view of the caravan's ribbed side (the review's measure).
- **The chase camera by walls and buildings** works out the height that sees
  over a wall from where the line to the car enters it, not from its own
  height (it shook 5-7 cm three times a second by the yard's wall). It climbs
  at most 5 m/s (it rose 74 cm in one frame as the room came between), and
  comes in (at most 6 m/s) rather than rise more than 5 m over the car. It never enters a wall
  or a building below its top: it is put back out by the side it came in by,
  so it slides along that face, and lets go at most 4 m/s. (Held at the face
  along its line, it jumped up to 3 m toward the car as the line swung onto a
  corner.) Where its line to the car passes under a roof (the room's porch,
  the car shade's cloth) it stays low enough for that line to clear the roof.
  Searches of
  thousands of runs turning and driving by every wall end and building found
  no frame inside a box.
- **The chase view's split now covers the camera over a wall.** The builder's
  eyes for it are at 5.6 and 6.8 m back and 1.3 to 4.2 m up (they were 1.6 to
  2.6 m at 5.6 m). Where the camera is outside them (facing down a dune, 5 m
  over the room, close in), the game draws all of the car, so no faces are
  missing: 7 draws and about 11k triangles more for those moments. By the yard
  wall the view stays split: 199 draws, 362k.
- **The door takes its whole window frame, and the doorway has its sill.**
  The frame is whole all round: the top, the rear post and a front sash
  member along the pane's front edge (the pane cut clean 3 cm under the A
  pillar's trim).
  With the door open, a band under the seat showed straight through the car.
  The sill, its scuff plate and the door's jambs are a few dozen triangles.
- **The far layer's normals are recomputed.** The decimation left its own,
  6 to 26 degrees off the faces on average, against the near layer's 1 to 9.
  The side windows and the B pillar's black strip then caught different light
  and popped at the 20 m swap. The pixels that change at the swap went from
  1,618 to 1,031 over three views. What remains is the coarser shape itself:
  the wheels' spokes and the hood's edge.
- **The enlarged phone re-flows its screens** for the narrow width its
  magnified content has (186 pt across at 956 × 440, 164 at 844 × 390). One
  attribute switches it as the phone enlarges: two layouts and about 9 ms of
  style and layout on this machine, once. A finger sliding it or scrolling an
  app causes no layout at all.

**The frame meter and the GPU question (FSR1).** The meter (#fps, on in the
iPhone app) sorted every frame time of the session once a second. On a
phone, after some minutes, that took a few ms and made one slow frame a
second: near 2% of frames, so the "slowest 1%" the owner read (23-24 ms) was
partly the meter's own. It now keeps a histogram. After its warm-up it also
runs a 24 s test on the owner's phone, alternating the full render scale and
70% every 4 s, and shows the typical and slowest-1% frame times for each. If
70% is much quicker, the GPU is the limit and a lower render scale with an
upscaler such as FSR1 would help. If not, it would not.

**His phone's answer (12 Nov): no FSR1; the frame was CPU-bound.** After
three minutes of play, with Low Power Mode off: 30 frames a second, the
slowest 1% 38 ms, one stutter. Full scale (1.5x) and 70% gave the same frame
times, 33.0 and 33.0 ms (slowest 1% 44 and 43). The pixels are not the limit,
so FSR1 would not help, and the test is taken out. He had 60 frames a second
on an earlier build. A profile here then put the frame's CPU work at 0.5 ms
for the game itself and 9.9 ms for three.js issuing the drawing. The scene
had 4,992 objects, 3,876 of them camel bones:
- each camel's two lighter detail levels kept their own 38 bones, driving
  nothing;
- the main skeleton's bones were walked by the renderer although never drawn;
- every bone was recomputed every frame, even far off where the animation
  steps every 2nd or 4th frame;
- every camel's bone texture was re-sent every frame.
Now the dead bones are gone, the bones are out of the renderer's walk, and
each camel updates its own matrices and skeleton only on the frames its
animation steps. The objects went from 4,992 to 2,408 (594 walked when
drawing, from 4,470), and the frame's CPU work here from 9.9 to 5.2 ms. The
pictures are the same (0.01 to 0.04% of pixels, the animation's phase). WebKit
passes each WebGL call to its GPU process, so on the phone this side weighs
more. The meter now shows both parts on the phone, as averages per frame
(WebKit's clock is in whole milliseconds; an average over many frames is
still exact).

A sharper picture than 1.5x (the budget above) is the owner's trade-off: 3x
is four times the pixels and, at his screen, about 100-125 MB more for the
drawing buffers, with more heat over a long session.

**Garbage per frame, again.** In Chromium the game code makes 50 KB a frame on
the map and 75 KB in play. 40 to 62 KB of it comes from three.js's
`Interpolant.evaluate`, called by the camels' animation mixers. V8 boxes the
doubles of that shared, polymorphic function as heap numbers. The iPhone's
WebKit (JavaScriptCore) keeps doubles unboxed, so this garbage, and the minor
collections it brings, are most likely Chromium's alone (not yet confirmed on
the phone; the meter's stutter count will show it). The drawing itself makes
68 to 81 KB a frame in three.js's uniform uploads and sorting.

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

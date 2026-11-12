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
- PCF shadows on a 1536 map, a render scale of 1.5 (2x since 12 Nov, the
  owner's choice, below), anisotropy 4, and standard (not physical) materials.
- **Shadows:**
  - Each camel's shadow comes from the next lighter mesh: 8k up close,
    1.5k further out, so far camels now have one.
  - Objects smaller than 30 cm cast none.
  - The shadow area follows the view in 4 m steps, and the map is redrawn
    every other frame (every frame while the player's car moves, since 12 Nov,
    below).

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
- Render scale 2x (the owner's choice for a sharper picture, 12 Nov; it was
  at most 1.5). What it costs on his phone is measured below.

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

**The cameras, after the owner's phone (12 Nov).** The chase camera sat too
close and turned with the car; the map was hard to hold. The chase camera is
now 8 m behind the car's middle and 2.7 m up (it was 5.6 and 2.05), and its
heading follows the car's at 2/s (it was 4/s, so about half a second behind in
a turn). A finger dragged across the screen turns it round the car (290
degrees for the screen's width); the camera follows the finger smoothed over
about 70 ms and at most 3 rad/s, and eases back behind 2 s after the finger
lifts, at most 70 degrees a second. Two reviews found what the turn did near
the yard's buildings, and the rules below came from them:
- it does not tilt (tilted, it came down through the porch's roof and onto
  the room, put out by its nearest side 2 m in a frame);
- it never comes nearer the car's middle than 2.9 m while it is less than a
  metre over the car's roof (the car's corners are 2.7 m out; let go by a wall
  as the turn swung back it once went through the car, and swept round under
  the porch it flew over the roof 0.8 m up);
- over a building's top or a roof it stays over it until it is off it (it
  came down onto the room and was put out by its nearest side, 2.1 m in a
  frame; held over the room it came down through the porch's roof);
- with the car under a roof it comes in in front of a building rather than
  rise over it (held over the room, the porch's roof hid the car 2 s);
- its height rises no faster than the car climbs plus 5 m/s (let out from
  under a roof it rose a metre a frame), and it is never less than 0.6 m over
  the sand (swung round beside a steep slope it went 2 m under);
- it moves back out no faster than 4 m/s (backing out from under the car
  shade it stepped 47 cm a frame).

Over the reviews' sweeps (standing by every wall, building, roof and corner
with the camera swung right round at 2.5 and 8 rad/s, held at eight angles and
let go, and driving by them with it turned), at 30 and 60 fps: no frame
inside a wall, a building, the car or the porch's roof; the largest step
beyond the camera's own turn 0.45 m at 30 fps; the largest turn of the view
16 degrees a frame at 30 fps (8 at 60). With no finger the camera is as
before: no frame inside anything, and the same eight frames of the car hidden
(the tamarisk at (-4, 11), which no obstacle list holds, and frames the
reviews' sight test, with boxes 0.3 m larger than the walls, counted though
the picture shows the car). What remains: parked under the porch with its
back to the room, the camera turned by the finger eases back only as far as
the room lets it (62 degrees round from behind, 6.3 m out, the car in view)
and stays there until the car moves off (the place behind the car is inside
the room's box); after a long drag it can stay over the car's rear quarter,
about 1 m over the roof. Under the porch with the room behind, with or without
a finger, the camera can stand about 1 m over the tailgate, 2.3 m from the
car's middle (the room's face leaves no more room; so before this change too).
Swept behind a building, the car can be hidden for a moment until the camera
comes in. Turned round by the finger, a few yard views reach 203-204 draws. The view split's chase eyes moved with it (8 and 9.2 m back,
1.4 to 5 m up, 50 degrees either side): 952 views across that range show at
most 4 px missing. Turned further round by the finger, the game draws all of
the car, as by a wall.

**Driving through the yard toward the pens** took in the pens, the room and
many camels near: 193 to 205 draws and up to 431k triangles, with the old
camera as with the new. Two changes, neither visible:
- **The camels' full detail level only within 8 m** (40k triangles; the 8k
  level to 48 m, the 1.5k beyond). It was used to 16 m. The 8k level now
  receives the shadows that fall on it too (it did not: a camel in a pen's
  shade past the bound was drawn as in full sun, 20% brighter, the review).
  In the real lit scene, at 7.7 to 16 m, in the sun and in a shade, from eye
  height and from the chase camera, the two levels differ in 0.2 to 0.4% of
  the camel's pixels, its brightness within 0.4%. The camel whose card is open
  keeps the full level to 16 m (its close view is at 14 m). Each bound is 3%
  further going out than coming in; in 600 s of camels at and bobbing across a
  bound, no change was undone within a second.
- **The ground cover in 50 m cells** (35 m before): one draw per cell, up to
  19 draws fewer (none out on the sand, 7 in the map's close view), for 2k to
  7k triangles more in most views and 21k more in the map's close view. All of
  the cover within 45 m is drawn in every view; at 45 to 90 m it is denser
  than before, not thinner. The phone's frame is bound by its CPU issuing the
  draws, so the draws count for more.

Measured the same way, at 844 x 390:

| View | Before | Now |
|---|---|---|
| Map, drone view | 183 / 252k | 164 / 259k |
| Map, close view | 67 / 213k | 60 / 221k |
| On foot, by the car | 167 / 379k | 145 / 381k |
| In the car, from the seat | 144 / 340k | 134 / 350k |
| In the car, from behind (under the car shade) | 187 / 385k | 180 / 397k |
| In the car, out on the sand | 83 / 228k | 84 / 233k |
| West across the yard | 205 / 402k | 186 / 405k |
| West, nearer the pens | 193 / 431k | 179 / 398k |
| North across the yard | 186 / 407k | 177 / 406-412k |

The draws are under the budget everywhere; the triangles are at it in the
yard's heavy directions (397k to 412k). The view from behind at the start is
higher than before because under the car shade the camera now comes in under
the cloth instead of rising, which puts it outside the split's fan, so all of
the car is drawn there (8k more). The camels move between runs, so a yard view
varies by about 10 draws and 20k triangles. What remained heavy: the player's
car at the chase camera's 8 m (64 draws, 145k triangles, a third of the
picture) and the terrain (3 draws, 73k).

**The player's car in three layers, and its shadow (the owner, 12 Nov:
"سوها").** A middle layer (lod_ext.py's 'mid', 82k triangles, the same parts,
door, wheels and view split as the near one; the glass and the tailgate's trims
kept fuller, as at half they went jagged) is drawn from 6.5 m to 20 m, so the
chase camera at its 8 m draws it; the near one within 6.5 m, from the seat and
while the door swings; the far one beyond 20 m. Its wheels and door are moved
as the near layer's. Seen from the chase camera the two layers differ in 1.4 to
1.5% of the car's pixels (the rear glass's top edge, the trim line under the
number plate, the grille's backing, the wheels' spokes); on foot at 6.2 to 20 m
in 0 to 1.4%. In 25k frames across 72 scenarios the swap never flickered.
The car now casts a shadow, from a coarse copy of the far layer (1.8k
triangles; 99% of it within 5 cm of the far layer, 25 cm at the worst; its
shadow overlaps the near layer's own by 92 to 99.9%), drawn in no picture: one
draw in the shadow pass. While the car moves the shadow map is redrawn every
frame (every other frame, the shadow sat a frame behind the car: 0.9 m at
100 km/h at 30 fps). The middle layer carries its own copy of the tyres' and
plate's textures (3.8 MiB on the GPU); the three layers could share one. (The owner had asked for no shadow
on 11 Nov, when the full layers cost 40k to 125k triangles a redraw; with the
camera 8 m back the car looked to float over the sand.) Measured the same way:

| View | Before | Now |
|---|---|---|
| In the car, from behind | 180 / 397k | 178 / 328k |
| In the car, out on the sand | 84 / 233k | 84 / 168k |
| West across the yard | 186 / 405k | 186 / 339k |
| West, nearer the pens | 179 / 398k | 179 / 333k |
| North across the yard | 177 / 412k | 178 / 414k |

North across the yard the camera comes in by the room to within 6.5 m of the
car, which then draws its near layer: still over, by 14k.

The map's camera is held like a phone's map. One finger drags the ground,
the point under the finger staying under it (to 0 px once the drag ends, on
the sand itself: a plane at the point turned about, 1.1 m over the sand, slid
the sand a quarter of the finger's way in a low view; OrbitControls' own pan
moved the ground a quarter to three quarters of the finger's way up or down
the screen). Let go moving, it glides on a little; a finger put down again
stops it (the ground slid on under a still finger), and the glide and the
controls' easing run in seconds, not frames. Two fingers pinch about the
ground between them, and the wheel about the ground under the pointer: the
camera and the point it turns about are drawn toward that ground by the same
factor, so it stays under the fingers (within 3 px on the yard's ground;
OrbitControls' own zoom to the pointer turned the camera back to its old point
whenever the view was low, and the ground under an off-centre pinch went
960 px off). A twist turns the map from 12 degrees, about the ground between
the fingers and with them (through OrbitControls' damping a 40 degree twist
had turned 11 by the lift and 27 a moment later); both fingers moved the same
way up or down tilt it from 10 px, the whole tilt over two thirds of the
screen's height; until one of those starts they only pinch (a pinch that was
not straight tilted it 37 degrees). The point turned about keeps to the
ground once dragged; from the hill view, whose point is in the air, it first
moves along the line of sight to the ground, the picture unchanged. A drag
stops following a camel or the herd and the card's button reads «تابعها»
again; a pinch does not stop it. The place pins take no touch of their own: a
finger that came down on a pin did not drag the map, and a second finger
landing on one did not pinch it. A tap is tried against the pins first, in
the game's coordinates (held upright, the screen is turned). A drag that
starts near the horizon still falls back to OrbitControls' own pan.

**The camels drawn a frame late (found by the review of the bones change).**
three.js counts its frames before the shadow pass, so a skeleton the shadow
pass updated was skipped by the next frame's picture. With the shadow map
redrawn every other frame, every camel in sight was drawn on those frames
with the frame before's pose: the head 22 to 27 cm behind, at 30 fps 15 poses
a second. Each camel now updates its skeleton itself, straight after its
bones move; drawn and true poses are the same (0.00 cm) on every frame.
Past 48 m a camel's place still moves in its animation's steps (every 2nd or
4th frame), at most 6 to 8 cm, under a pixel at 60 fps.

**The render scale stays at 1.5x** (the owner, 12 Nov: "نخليها"). *Later the same
day, of the blur and the washed-out colours ("التغبيش وبهتان الالوان"), after
pictures of each:* the render scale is 2x (on his 3x screen 1.5x drew a quarter of
its pixels, 2x draws 44%: 78% more than 1.5x), and the tone mapping is
Khronos PBR Neutral in place of AgX (AgX left the sand 40% less saturated and
the contrast a quarter lower: mean saturation 0.34 to 0.56, contrast 48 to 63
on the sand). Both his choices. A review then measured what Neutral does to
the dark parts: from the driver's seat 28% of the picture is under luma 32 (8%
under AgX), the dashboard and the cluster near black. Shown the two side by
side, he kept it as it is (12 Nov). The tent's Sadu and rugs drawn finer (the
diamonds' steps up close, his picture) take 4.35 MiB more texture memory with
their mipmaps, 5.2 MiB in all; asked, he kept them (12 Nov).

Still over, for a moment: **on foot with the driver's door open, 422k** (166
draws) for the 1.2 to 1.55 s the door swings as the player gets in or out.
The whole car and the cabin are drawn then. It was about 443k before the
shadow copies below. *Settled 12 Nov (the owner: the door is not to open
while he is on foot):* getting out, the door now opens and shuts with the
driver still in his seat (from behind, the view goes to the seat first), and
then he stands outside by the shut door; getting in, the view was already the
seat's. From the seat's eye nothing is missing with the door open at any
angle if only the seat's split is drawn, so it stays drawn so: the frames of
the swing are 265k to 343k (343k while the cabin first loads), and no frame
shows the door open on foot (31 to 33 frames at 418k before), interrupted or
not. While the door swings the car stands still with its driving not run
(held on the brake pedal at first, the pedals read it as a press at a stop
and put the car in reverse, the review).

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
  eyes for it were at 5.6 and 6.8 m back and 1.3 to 4.2 m up (they were 1.6 to
  2.6 m at 5.6 m; moved with the camera since, below). Where the camera is outside them (facing down a dune, 5 m
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
so FSR1 would not help, and the test is taken out. (A review later pointed
out that 33.0 ms is every second refresh at 60 Hz: something else held the
frame to 30 a second, and two settings that both fit under it say nothing of
what more pixels cost. The 2x figures below are from his phone itself.) He had 60 frames a second
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

A sharper picture than 1.5x is the owner's trade-off: 3x is four times the
pixels and, at his screen, about 100-125 MB more for the drawing buffers,
with more heat over a long session. At the 2x he chose, the buffers (4x MSAA,
about 44 bytes a pixel) take about 71 MiB at his 956 x 440 screen, 31 MiB
more than at 1.5x; Chromium's GPU process here grew by 29 to 50 MiB.

**Garbage per frame, again.** In Chromium the game code makes 50 KB a frame on
the map and 75 KB in play. 40 to 62 KB of it comes from three.js's
`Interpolant.evaluate`, called by the camels' animation mixers. V8 boxes the
doubles of that shared, polymorphic function as heap numbers. The iPhone's
WebKit (JavaScriptCore) keeps doubles unboxed, so this garbage, and the minor
collections it brings, are most likely Chromium's alone (not yet confirmed on
the phone; the meter's stutter count will show it). The drawing itself makes
68 to 81 KB a frame in three.js's uniform uploads and sorting.

**The herd on the owner's phone (12 Nov).** His meter at 2x: 60 frames a
second everywhere but by the herd, where it fell to 52 (the slowest 1%
27 ms, 4 stutters in 3 minutes). The game's own work took 1.3 ms a frame and
three.js issuing the drawing 1.6 ms, so the rest was WebKit's and the GPU's.
Measured here (no GPU: counted where it can be, the software renderer's time
as a guide only):
- **Not the calls.** By the herd the frame makes fewer WebGL calls than in the
  yard or on the sand (450 to 680 against 820 to 1,030).
- **The pasture's grass.** It is the thickest in the game: about half (52%)
  of the 42,000 tufts are round the camp. Standing in it, 13,000 to 15,500
  tufts are drawn, and the GPU shaded 1.0 to 3.5 grass fragments for every
  pixel of the screen (up to 69 deep). 85 to 88% of them were thrown away by
  the alpha test,
  since the blades fill 16% of their card. In the yard and on the sand, next
  to none. Hiding the grass took a third off the software renderer's time
  there.
- **Cut to the blades** (world.js, fitCard: the smallest four-cornered card
  holding every texel the alpha test can keep, with a one-texel margin), a
  grass card is 63% of its square for the same two triangles. By the herd
  that is 37 to 38% fewer grass fragments. Of those the alpha test kept, all
  but 0.002% (and, with 4x MSAA, all but 0.02 to 0.16% of the samples at
  far-off cards' edges) are still kept; none of it shows. The bushes' cards (and their shadow pass) and the tamarisks'
  are cut the same way. The pictures: 0.2 to 0.6% of pixels differ by more
  than 8 levels in 255, specks on the blades' edges where the card's two
  triangles now meet differently; none in the yard.
- **The first camel to come near** sent its full and middle meshes to the GPU
  then (about 1.5 MB) and readied a shader (743 ms in the software renderer
  at the middle level's first use). That is now
  done under the loading screen, once for each coat.
- What it does on his phone is for his meter to say.

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

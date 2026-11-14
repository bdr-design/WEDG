# Task T1: a full farm with 40 camels inside the draw budget

Read $SC/agents/GUIDE.md first (SC = /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad).
Base commit: a20b49d (the session branch's head). Worker's worktree: /home/user/wt/t1, branch wt/t1.

## The problem (measured, not yet fixed)

The budget (docs/adr/0005-3d-world.md, "Budget for the Flutter build"): at most 200 draws and 400k triangles a frame,
shadows included; at most 16 skinned camels near the camera; no allocations per frame.

Measured with $SC/review_de2/draws.js at 956x440, the default map view, every draw call counted (main pass / shadow
pass, worst frame):

| Scene | main / shadow, worst frame |
|---|---|
| The start (2 camels) | 97 / 21, 120 |
| Everything built, 2 camels | 148 / 28, 178 |
| Everything built, 40 camels | 186 / 66, **254** (346k triangles) |

The shadow map is redrawn at least every other frame (farm.html, renderer.shadowMap.autoUpdate = false and its redraw
rule), so the 254 comes at least half the frames. Going from 2 to 40 camels adds about 38 main-pass and 38 shadow
draws: each camel is its own skinned mesh (class Camel in design/prototype3d/farm.html: three detail levels, shadow
stand-ins from the next lighter mesh, setLod by distance). The owner felt it on his phone: 60 fps elsewhere, 52 by the
herd. The engine's yard holds up to 40 camels (Presenter.yardCount) and the farm 56 head, so this is where every
long game ends up.

## What is wanted

With everything built and 40 camels in the yard, at the default map view AND at the views a player really takes (the
near view of the pens, walking among the camels, the chase view from the car by the pens): at most 200 draws and 400k
triangles in the worst frame, shadows included, and no more than 16 skinned camels animated at once. The start and
the 2-camel scenes must not get heavier.

The ADR already names the design ("The herd in three tiers"): skinned camels near the camera (at most 12 to 16);
farther ones drawn as ONE instanced draw per detail level from a baked bone-matrix animation texture, with the clip,
time and coat per instance; beyond 150 m, impostors. Follow it unless you find and measure something better; say why.

It must lose nothing the player sees:
- Realism: the camels' gait and poses stay the real ones (the baked clips are the same clips); coats, sizes by age
  (sizeOf), calves beside their dams, the idle/graze/walk behaviour. No visible pop when a camel changes tier at
  the view distances a player uses (compare pictures at the switch distance).
- Shadows: every camel still casts its shadow where it does today. If the budget cannot be met without dropping or
  simplifying some shadows, that is a trade-off between realism and weight: the owner's decision. Build the lossless
  part, and bring the options with measurements and pictures.
- Everything that works on a camel today still works: tapping a camel on the map opens its card, follow, the card's
  values from the engine, a camel arriving (bought yesterday) or leaving (sold), a calf growing, the pens' counts.
- Smoothness beyond the counts: no allocations per frame in the new path (check with the page's own frame meter,
  #fps, and a heap check across a few hundred frames), no hitch when the yard changes (measure the JavaScript time of
  syncYard with 40 camels), texture memory within the budget's 80 MiB.

## Measure and report

- The table above again, before and after, with draws.js (copy it; it fakes the built farm and 40 camels through
  window.__farm.setGame), plus the near view of the pens and one walking view among the camels: main / shadow draws,
  triangles, skinned meshes animated, worst frame.
- Pixel comparisons before/after of the same frame (the camels' clip time pinned) at the default view and the near
  view ($SC/review_de2/abdiff.js shows how): say what differs and why.
- JavaScript time per frame of the camel update (mixers, tier choice) with 40 camels, before and after, measured in
  the page (performance.now around it over 300 frames), as a relative figure (this machine is not the phone).
- The checks in the guide that cover what you touched (the page has no Dart; still run the proto_engine page checks
  if you touch engine.js or the snapshot's use).
- Update docs/adr/0005-3d-world.md ("Measured again" with today's date, 13 Nov 2026) with the new figures and what
  was done, and design/prototype3d/README.md if the description of the herd changes.

## Left open on purpose (do not fix here)

- The start's Land Cruiser, the compound wall and light poles standing at a new farm (a note for the owner).
- The engine's side: yardCount stays 40; herds beyond the yard are a later task.

# Task T17: the birds' rig and clips, then the peregrine of the year

For the pair that built the birds (task T11). Read docs/agents/GUIDE.md again, then the T11 brief
(docs/agents/T11_hunt_birds.md), tool/bird3d/README.md and design/birds/README.md as they are on the session
branch. Base: the session branch's head when you start. Worker's worktree: /home/user/wt/t17, branch wt/t17
(the old /home/user/wt/t11 was removed after it landed). Reviewer's folder: $SC/t17_review (it may reuse its
scripts in $SC/t11_review). Commit often. Never push.

## What the owner decided (14 Nov 2026)

- The birds' look: «اعتمدها وكمّل: نبدأ العظام والحركات (الطيران، النزول، المسك) ونبني فرخ الشاهين البحري (طير مزاد
  الطرح). النواقص المعروفة تنصلح مع الحركات.» (docs/agents/owner_decisions_2026-11-14.md, item 1.)
- The hunting season's design is approved (docs/agents/hunting_owner_decisions.md, last section; design/hunt/,
  design/ui/phone_falcon.jpg, docs/proposals/hunting_season_design.md): the clips serve that design: the falcon on
  the cuff unhooded and cast off by the player's hand, the flight, the catch or the miss, the falcon lost and
  found; at the trapping camp the pigeon released by hand, a falcon over the decoy, the bird in the net.
- The texture stays at 512 px until he tries it on his phone.

## Part 1: the rig and clips (the saker, the houbara, the stone-curlew)

Follow the plan in tool/bird3d/README.md (written in T11), corrected where the approved design asks for more.
1. One skeleton per bird, as few bones as the motion honestly needs (state the count and why each bone exists;
   the camel's rig, tool/camel3d, is the house pattern for skinning, baking and export); the wings fold and
   spread by the rig if that reads right at the game's distances, or by a folded and a spread wing mesh swapped at
   take-off and landing as T11 proposed: build the one that looks right close (the cast-off is seen from one to
   three metres) and measure both ways' cost before choosing; say which and why.
2. The clips, each with its real reference (wingbeat rate, speeds, durations: sourced by number in the README, or
   marked a game choice): the saker: perched idle (small shifts, a look around), rouse, the hood off and on,
   cast off from the cuff, flapping flight, glide, the stoop, binding to the quarry, mantling on the kill,
   landing on the cuff and on the perch; the houbara: standing, the run, take-off, flight, and its escape (the
   real houbara's defence: sourced); the stone-curlew: standing, the run, the crouch, take-off, flight. Loops
   loop without a pop; transitions blend; feet stay planted on the cuff and the perch (measure the slide in
   millimetres).
3. The known gaps close with the motion, as he said: the toes on the cuff (thick, knuckled, curved, the talons
   hooking in; no vertex inside the cuff beyond a millimetre or two in any frame of any cuff clip), the jesses
   trailing in flight as soft cords (not stiff rods), the feet tucked in flight in every flying frame, the
   houbara's crest, the line at the bill's base, the stone-curlew's two legs no longer superposed in the standing
   pose (as was done for the houbara).
4. Weight: bones and skin weights per vertex within what the game's skinning allows (the ADR's limit on skinned
   animals near the camera is for camels: say what a scene of one falcon, a few quarry and a pigeon costs, and
   whether the far level is skinned, baked to a clip texture like the herd, or a rigid pose); triangles and
   textures unchanged from T11's bands; clip data size; one draw per bird (plus gear).
5. Deliver: the rigged GLBs in assets_src/birds/ (the static ones kept or replaced: say), the clips' names and
   lengths in the README, and for the owner: a contact sheet of each clip (frames side by side) and short
   turntable strips as pictures (JPEG; no video hosting; if a GIF or MP4 is small and renders in the app's chat,
   one for the cast-off and one for the flight), marked "awaiting the owner's approval of the motion".
6. The same code gives the same GLB twice.

## Part 2: the peregrine of the year (فرخ الشاهين البحري), after part 1's rig exists

The bird of the trapping business: the only bird the trapping auction sells (docs/proposals/hunting.md section 9;
docs/research-realism.md). Built by the same code as the saker with its own numbers, never a recoloured saker:
its real size by sex (the female, the larger, is the one prized: sourced), its build (shorter tail, longer
pointed wings, broader chest, the larger feet of a bird-catcher), the juvenile's plumage (brown above, streaked
below, the moustache, the pale cere and feet of a bird of the year: sourced by marking), in the poses the design
shows (in the net and in the hand, hooded on the perch in the tent, on the cuff, in flight over the decoy), on
the saker's rig where the skeleton honestly fits. Dimension table, pictures with a ruler and beside the saker
and the man, two detail levels, 512 px, the same GLB twice. Marked "awaiting the owner's approval of the look".
Also the trapping pigeon (the decoy with its noose harness: the design's «شبك الحمام»): a small model with a
flutter clip, in the same manner, sized by its real measure.

## Report

The guide's report, with: bones per bird, the clips' table (name, length, reference), the measures (foot slide,
talon depth in the cuff per clip, triangles, textures, clip sizes, draws), what is unsure, and the questions that
are the owner's (the motion's look; anything the research could not settle), recommendation first.

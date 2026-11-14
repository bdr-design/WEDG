# Task T12: the wolf and the dogs, built by code, to show the owner

Read docs/agents/GUIDE.md first (in it, $SC is the work machine's scratch folder:
/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad), then /home/user/WEDG/CLAUDE.md.
Base: the session branch's head when you start. Worker's worktree: /home/user/wt/t12, branch wt/t12. Reviewer's
folder: $SC/t12_review. Commit often: the machine was restarted once tonight (disk kept, processes lost).

## What the owner asked (13 Nov 2026)

«ابي تدخل الحيوانات الان وتعرضها علي كذالك موسم القنيص»: he wants the animals made now and shown to him. The birds
are built (task T11, /home/user/wt/t11: tool/bird3d and its README are the nearest pattern, with tool/camel3d for a
four-legged animal and tool/weapon3d). This task is the animals of his decision on wolves
(docs/agents/hunting_owner_decisions.md; docs/proposals/gdd_hunting_section.md section 13.5; research in
docs/research-realism.md section 8, sources [139], [149], [151], [168]):
- the wolf is a rare danger at night to the calves; it is protected; killing it never lowers the danger;
- stray dogs are a like danger (a game choice where the research has no source);
- the right protection is a strong fence, a herdsman and a guard dog: the guard dog is a thing the player buys and
  feeds.

The owner sleeps. A proxy agent answers the questions that are his (docs/agents/PROXY.md): bring each with its
options, the facts and your recommendation first; the director puts it to the proxy.

The game's rule for every model: built by code at its real size, realism above all, every number sourced or marked
a game choice, light on a mid-range phone (the budget in docs/adr/0005-3d-world.md). No downloaded mesh or picture
goes into the repository; a photograph may be looked at as a reference and named in the README. Network: many hosts
are refused from this machine; say plainly for each figure whether you opened the page or know it only from a search
summary, as tool/bird3d/README.md does. Do not try to get around a refusal.

## Build (shape, coat and poses, for the owner's eye; no rig yet)

1. The Arabian wolf (الذيب العربي, Canis lupus arabs), not a northern grey wolf: its real size (it is small: find
   shoulder height, length, weight, by sex, sourced), its build (lean, long legs, large ears for its size, short
   thin summer coat and the winter coat: say which you build and why), its colours and markings (painted by code:
   say what each marking is and where it comes from), the eyes, the fused middle toe pads if you model the feet that
   closely (say if you do not). Poses: standing alert; the low stalking walk it would be seen in at night near the
   pens; one pose of your choice that the game will need (say why). It is seen at night at tens of metres, rarely
   near: size the detail levels to that, and say how it reads under the game's night light (render it in the dark
   of the game's night as well as in daylight for the look).
2. The guard dog (كلب الحراسة): find what dog really guards camels and sheep at a Saudi عزبة (the research's source
   [149] names a guard dog without a breed: look for the real practice: the local dogs herders keep, by their names
   in the Kingdom, and whether a named breed is used; if no source settles it, say so and propose the commonest
   local type as a game choice). Its real size and coat; a collar or a chain if that is the practice (sourced).
   Poses: standing alert; lying at rest by the pen; barking stance if cheap.
3. The stray dog (الكلب الضال): the free-ranging dogs of the Kingdom's town edges (the type seen in the reports of
   [151]). If the same mesh as the guard dog with another coat and condition (leaner, no collar) is the honest
   answer, do that and say so; do not build a second mesh for the sake of it.
4. A question, not a build: the saluki (السلوقي) is the hound of the Kingdom's hunting tradition. Whether hunting
   with it belongs in the game is the owner's. Research its real place in Saudi hunting and its legal standing
   under the hunting rules in docs/research-realism.md section 8 (is hunting hares with salukis allowed, in what
   season: sourced, or "not found"), and bring it as a question with your recommendation first. Build nothing of it.
5. For each animal built: a dimensions table (real figure, source, the model's figure measured on the file); two
   detail levels with triangles justified against the frame's 400k (say how many a scene really shows: one or two
   wolves; one guard dog; a few strays), one material and at most one 512 px texture pair each unless you show why
   more is needed; fur by texture and silhouette only (no shells, no alpha cards unless measured cheap and shown
   to be needed); named points for what comes next (feet, hips, shoulders, neck base, head, jaw, tail base, the
   collar's ring); a short plan for the rig and clips the game will need (the wolf: stalk, trot, run, carry off;
   the dog: idle, lie, bark, run, chase), each with its real reference (gait footfall order and speeds: sourced)
   and its cost in bones. The camel's rig (tool/camel3d) is there: say what of it can be reused for a canid and
   what cannot. Do not rig now.

## Deliver

tool/canid3d/ (scripts and a README in the pattern of tool/bird3d/README.md), the GLBs in assets_src/canids/, the
pictures in design/canids/ (JPEG): each animal and pose from the side with a centimetre ruler, three-quarter, close
on the head, one picture of all of them beside the player's figure (assets_src/characters/man.glb) and a camel calf
(the game's own calf model, at the age the research's case names: a few days old) for scale, and the wolf at night
at the distance the game will show it. Light the pictures so pale coats are not burnt out and dark ones not lost.
The same code must give the same GLB twice (see how tool/weapon3d/akm.py settles its index order, and how
tool/bird3d does). design/README rows marked "awaiting the owner's approval".
In your report: the pictures' paths, the dimension tables, triangles and texture memory per file, what is unsure,
and the owner's questions with your recommendation first (the look; the guard dog's type; the saluki; anything
else that is his).

## Left open on purpose

- Rig and animation (the next task, after the owner approves the look).
- The danger's rules in the engine, buying and feeding the guard dog, the fence: a later task.
- The other protected animals the research names (الضبع، النمر، المها، الغزلان، الوعول): not now.

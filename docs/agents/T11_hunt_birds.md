# Task T11: the birds of the hunt, built by code, to show the owner

Read $SC/agents/GUIDE.md first (SC = /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad),
then /home/user/WEDG/CLAUDE.md. Base commit: the session branch's head when you start
(`git -C /home/user/WEDG rev-parse claude/vigilant-noether-nydua2`). Worker's worktree: /home/user/wt/t11, branch
wt/t11. Reviewer's folder: $SC/t11_review.

## What the owner asked (13 Nov 2026)

«ابي تدخل الحيوانات الان وتعرضها علي كذالك موسم القنيص»: he wants the animals of the hunt made now and shown to him.
Hunting enters the game by his earlier decisions (docs/proposals/gdd_hunting_section.md, the draft of GDD section 13,
and docs/proposals/hunting.md: read both; research in docs/research-realism.md section 8): falconry first
(المقناص بالصقر), falcon contests with it (الملواح ومزاين الصقور), the air rifle later.

The game's rule for every model: built by code at its real size, realism above all, every number sourced or marked
a game choice, light on a mid-range phone (the budget in docs/adr/0005-3d-world.md). See how the others are made and
documented: tool/camel3d, tool/char3d, tool/vehicle3d, tool/weapon3d (akm.py and its README are the nearest
pattern: one script, Blender as the bpy module at $SC/blendenv/bin/python, painted textures, two detail levels,
named points, a dimensions table with sources, pictures with a ruler and beside the player's figure
assets_src/characters/man.glb). No downloaded mesh or picture goes into the repository; a photograph may be looked
at as a reference and named in the README.

## Build (this task: shape, plumage and poses, for the owner's eye; no rig yet)

1. The falcon: the saker (الصقر الحر), the falconers' bird in the Kingdom, a female (the larger sex, the one flown):
   - perched, hooded (البرقع) and jessed (السبوق), on its block perch (الوكر) and on the falconer's glove/cuff
     (الدس / المنقلة: find the right Saudi words and the real objects, sourced);
   - unhooded, alert, on the perch;
   - in flight, wings spread (the pose seen from below and behind when it is cast off).
   The gear (hood, jesses, leash, perch, glove) as parts of their own, at their real sizes.
   Say in the README what would turn this saker into the other birds the research names (الشاهين، الجير) and which
   of them the game needs first: that is the owner's choice; bring it as a question with pictures only if cheap.
2. The quarry of falconry in the Kingdom: الحبارى (the Asian houbara, MacQueen's bustard) standing alert, and in
   flight; الكروان (the stone-curlew; the research's source [140] says which species) standing.
3. For each: real measurements (length, wingspan, standing height, weight for the record; the sexes' difference)
   from named sources, in a table: real figure, source, the model's figure; the plumage by its real pattern and
   colours (painted by code; say what each marking is and where it comes from); the eye, cere, feet and talons right
   for the species. Two detail levels (close: the bird on the fist or perch beside the player and car, a few metres
   away; far: in flight or on the ground at tens of metres), one material and at most one 512 px texture pair per
   bird unless you show why more is needed; triangles justified against the frame's 400k (say how many birds a
   scene really shows: one falcon, a few quarry).
4. Named points for what comes next (where the jesses tie, the hood sits, the feet grip the glove, the wing roots),
   and a short plan for the rig and clips the hunt will need (perched idle and rouse, cast off, flapping flight,
   glide, stoop, bind to the quarry; the houbara's run, take-off and flight; the stone-curlew's run), with each
   clip's real reference (wingbeat rate, speeds: sourced) and the cost in bones and triangles. Do not rig now.

## Deliver

tool/bird3d/ (scripts and a README in the pattern of tool/weapon3d/README.md), the GLBs in assets_src/birds/, the
pictures in design/birds/ (JPEG): each bird and pose from the side with a centimetre ruler, three-quarter, close on
the head, and one picture of all of them beside the player's figure for scale (the falcon on a glove at the height
a standing man holds it, the houbara and the stone-curlew on the ground). Light the pictures so white and pale
plumage is not burnt out. The same code must give the same GLB twice (see how akm.py settles its index order).
In your report: the pictures' paths, the dimension tables, triangles and texture memory per file, what is unsure,
and the owner's questions with your recommendation first.

## Left open on purpose

- Rig and animation (the next task, after the owner approves the look).
- The air rifle's quarry (يمام، قطا، سمان، حجل): later.
- Putting the birds into the game page.

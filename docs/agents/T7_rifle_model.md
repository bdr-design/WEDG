# Task T7: a Kalashnikov rifle model for the game, built by code at its real dimensions

Read $SC/agents/GUIDE.md first. Base commit: a20b49d. Worker's worktree: /home/user/wt/t7, branch wt/t7.

## Why

The owner (13 Nov 2026) wants a Kalashnikov rifle (كلاش) in the game, for the hunting subject being researched in a
task beside this one (T6). The project's rule: models are built by code (tool/camel3d, tool/vehicle3d, tool/char3d:
read their READMEs and how they work in Blender's Python, and how the Land Cruiser was built to the real spec-sheet
dimensions), realism first, and light on the phone (docs/adr/0005-3d-world.md). The owner has sent no photos of the
rifle yet: build the shape from the published dimensions and reference drawings of the real rifle, and say plainly
that its look (wood, wear, finish) awaits his photos or his choice.

## What is wanted

- The classic rifle as it is known in the Gulf: the AKM pattern with wooden furniture (fixed wooden stock, wooden
  handguard, the curved 30-round magazine), unless your research of what «الكلاش» most commonly is in Saudi Arabia
  says otherwise (say what you found and build that).
- Every dimension from a source (the manufacturer's or an armoury manual's figures: overall length, barrel length,
  height, the stock, the magazine, the sight radius, the weight for the record), listed in the tool's README with
  its source. Where a dimension has no source, take it from a scaled reference drawing and mark it so.
- Built by a script, tool/weapon3d/ (Blender Python, as the other tools: the Blender environment the project used is
  $SC/blendenv, a Python venv with bpy; check tool/vehicle3d and tool/char3d for how they run it), that writes the
  model as GLB with PBR materials (blued steel, wood, the magazine), no downloaded meshes or textures.
- Light: detail levels for the hands (first person, close) and for a rifle slung on a walking figure seen from the
  chase or map camera: state the triangles and texture memory of each and keep them small against the budget (the
  whole frame is 200 draws and 400k triangles; a carried rifle should be a few thousand triangles at most at its
  nearest and one draw).
- Ready to carry: the model's origin and named points for the right hand (the grip), the left hand (the handguard),
  the sling's two ends and the muzzle, so the player figure (tool/char3d) can hold or sling it later. Do NOT put it
  into the game page (design/prototype3d): another task is changing those files; that comes after.
- Pictures for the owner: the rifle from the side (both), top, front and three-quarter, against its real dimensions
  (an overlay or a ruler), and beside the player figure for scale if tool/char3d's figure can be loaded.

## Deliver

In the worktree: tool/weapon3d/ (the script, a README with the sourced dimensions and how to run it), the GLB where
the other models live (design/prototype3d/models/, named plainly), the pictures under design/ (say where). In your
report: the pictures' paths, the dimension table with sources and the model's measured dimensions against them, the
triangles and texture memory per detail level, what awaits the owner's photos or choice, and what you could not verify.

# T12 review plan (phase 2), base 56caa10
1. commits_check.sh base head: files, binaries only GLB in assets_src/canids + JPEG in design/canids; no network/image
   loads in code; JPEGs without camera EXIF; design/README rows 'awaiting the owner's approval'.
2. repro.sh head "<build cmd>": two builds byte-identical; committed GLBs == built; audit: no reads outside source.
3. canid_check.py on every GLB (phase2.sh): draws (1 per file expected: one material), tris near/far, 512 pair max,
   memory; closed, no inside-out shells, one-sided, opaque (no alpha cards/shells); named points complete (feet x4,
   hips, shoulders, neck base, head, jaw, tail base, collar ring on the guard dog); feet on y=0 +-2 mm; symmetry
   p95 small in symmetric poses; sizes vs REF; ratios (leg/chest, depth/withers, len/withers, ear, tail tip vs hock).
4. Dimension tables in README: each 'real' figure's source and opened/search label true to what can be opened
   (only *.wikipedia.org + commons/upload.wikimedia opened from here); model column == my measurement.
5. Renders (canid_render.py, Cycles CPU, 2 threads): side with ruler, tq, head; game view at 30 m night and day;
   compare with Commons photos (ref/): tail low/straight, ears large, long legs, narrow chest, grizzled saddle, dark
   tail tip, pale muzzle/throat/legs, amber eye; guard/stray NOT wolf-like (curled/sickle tail, smaller ears, broader
   chest) and the stray leaner, no collar, same mesh if honest.
6. The worker's pictures: every animal/pose side+ruler, tq, head close, line-up with man.glb and calf at 0.55 x
   camel_wodh_female (farm.html SIZE_AT), wolf at night at game distance; lighting not burnt/lost (histogram clip %).
7. Rig plan: gait footfalls (walk lateral sequence; trot diagonal; gallop rotary at speed / transverse slower),
   speeds sourced (Mech 1994 8.7 km/h travel; chase figures popular-source only), bone counts, camel rig reuse.
8. Night: the prototype has no night -> must be called a game choice. Saluki question: law status per s8 + 2013 hare
   season (dogs/falcons, 40 days) as an old precedent; open-land route not found.
9. Owner's rules: player-facing text Arabic, nothing floating; no downloaded mesh/picture; budget ADR 0005.

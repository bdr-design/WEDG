# Camel models by code

The owner chose to have the camels made by code rather than by an AI 3D
tool (ADR 0005). This folder builds a rigged, animated camel from one side
photo.

| Step | Script | Output |
|---|---|---|
| 1. Cut-out | (GrabCut, see `segment` in the session notes) | `mask.png` from the photo |
| 2. Shape | `shape.py` | `camel_hi.npz` (~330k triangles) |
| 3. Game mesh and textures | `bake.py` | `camel_lod0.blend`, 2K albedo and normal maps |
| 4. Rig and clips | `rig.py` | `camel_rigged.blend` (idle, graze) |
| 4b. Walk from foot physics | `walk_physics.py` | replaces `walk`, prints slip and contact checks |
| 5. Export | `export_glb.py` | `camel_wodh_female.glb` |
| 6. Detail levels | `lods.py` | `_lod1.glb` (8k triangles, 1K textures, 625 KB), `_lod1_4k.glb` (4k triangles, 1K textures, 468 KB: the farm's middle level since the owner's choice of 14 Nov 2026), `_lod2.glb` (1.5k triangles, 512 px, 269 KB); same skeleton, bind pose and clips. Run in the work folder with `camel_rigged.blend`, its two 2048 px maps (`camel_albedo_2048.png`, `camel_normal_2048.png`) and `camel_wodh_female.glb`; the same files come out byte for byte each run |
| Checks | `render_tex.py`, `render_anim.py`, `feet_closeup.py`, `feet_clay.py`, `feet_walk.py`, `body_views.py`, `ortho_compare.py` | Cycles renders in desert light; close-ups of the lower legs standing, untextured and through a stride; front, rear and three-quarter views; a side view at the photo's own scale to lay over it |

## How each step works

- **Shape:**
  - The body, neck and head are the photo's outline inflated sideways, with
    real camel widths per region (barrel, narrow hump ridge, narrow neck and
    head).
    - The barrel is about 57 cm wide and round in section (the radius
      window is wider than the body's half-depth, so the belly and hump are
      not keeled). Heart girth about 2.2 m, as measured on Wadh she-camels.
    - The thighs part below the vulva, with the udder and four teats
      between them, and the hook bones show at the top of the hips.
    - The chest pad sits between the forelegs with a flat underside.
    - Small rounded ears, flat and turned out.
  - **Legs, matched to the photo at every height:**
    - Forearm about 17 cm deep below the elbow and 13–15 cm at mid
      forearm; gaskin 19 cm under the stifle and 14 cm at the hock.
    - Flat from the side: the leg tubes are squeezed sideways about their own
      axis, so a forearm is about 10 cm wide from the front and a gaskin
      about 13 cm.
    - The hind legs sit a little closer in, with the hocks closer together
      than the feet.
  - The legs, knees, ears, chest pad, lower lip and tail are tapered tubes
    and ellipsoids at real proportions.
  - **Lower legs and feet**, matched to the photo:
    - The cannon is a slim bone with the flexor tendons behind it, so it is
      deeper than wide (about 8.5 × 6 cm in front, 8 × 5 cm behind).
    - The fetlock flares to about 13.5 cm, then the pastern runs forward and
      down into the pad.
    - A broad, low cushion with a flat sole that spreads at the ground,
      about 24 × 19 cm on the forefeet and 22 × 17 cm behind.
    - Two toes side by side with a cleft between them and a nail over the
      front of each.
    - The rig's pastern and foot bones follow the same points, so the pad
      rolls onto the toes at push-off and curls in the swing.
  - Everything is joined with a smooth union and meshed with marching cubes.
  - Scale: 443 px = 1 m, so the hump is 2.05 m above the ground.
- **Textures:** the photo is projected from the side onto side-facing skin.
  The top, bottom, front and legs get a coat built from the photo's own
  colours.
  - The lower legs stay white, with a light cream stain above the pad.
  - Grey nails, calluses on the knees and chest pad, and a leathery sole
    underneath.
  - A short-range ambient-occlusion bake darkens the toe cleft, nail rims and
    joint creases.
  - The normal map adds fur grain.
- **Clips:**
  - `idle` (4 s).
  - `walk`: built from foot physics and checked against Muybridge's camel
    walking (*Animal Locomotion* plate 737, 1887; in
    `assets_src/reference/`).
    - **Footfalls:** a lateral-sequence walk close to a pace. The hind foot
      lands first and the forefoot of the same side about 12% of a stride
      later. Each foot is down for 65% of the stride. A planted foot moves
      back at exactly the ground speed. At the end of the stance the heel
      lifts while the toes stay down, and the roll fades out over the first
      quarter of the swing.
    - **Forelimb:** the shoulder joint sits forward of the elbow, as in the
      photo. While the leg carries weight, the forearm and cannon form one
      straight column with the carpus locked. The shoulder blade takes 60%
      of the swing, and the shoulder and elbow take up the length, with the
      elbow behind the shoulder. In the swing the carpus folds forward about
      78°, the cannon trails back, and the fetlock flexes so the toe trails
      and the sole faces back.
    - **Hind limb:** the thigh swings about the hip, and the hock points
      back in every frame.
    - **Joint accuracy:** the legs splay slightly, so each joint is re-aimed
      until the fetlock lands within 2 mm of its target.
    - **Swing height:** the sole clears the ground by about 7 cm in front
      and 6 cm behind. The height comes from the folded carpus and hock.
    - **Body:** it vaults over the planted legs, rising at mid-stance and
      dipping at the change of support (about 4 cm). It shifts over the side
      carrying the weight, and the neck and head counter the bob.
    - **Checked** with `gait_measure.py` (joint bend directions, footfalls,
      side shift) and `sole_clear.py` (lowest point of each foot's mesh).
    - **Weight:** the pads spread under load.
    - **Pace:** 1.15 m/s (about 4 km/h), 1.45 s and 1.67 m per stride.
    - **Measured:** the toes slip under 2 mm per frame and stay within 2 mm
      of the ground while planted.
  - `graze` (4 s): the muzzle reaches the ground about 0.75 m in front of
    the forefeet.
- **Budget:** 40k triangles, 37 bones, 2K textures, 2.1 MB GLB.

## Where the inputs are (durability)

The camel's source inputs live only in the session's scratch folder (`$SC/camel/`: `mask.png`, `ref_fill.png`,
`camel_hi.npz`, `joints.json`, `feet.json`, `camel_lod0.blend`, `camel_rigged.blend`, and the two 2048 px maps
`camel_albedo_2048.png` and `camel_normal_2048.png`; about 12 MB). The game works without them (its levels are in
`assets_src/camels` and the page's `models/`), but the levels, the rig, the clips and the textures cannot be rebuilt
if that folder is cleared. Some of them derive from the owner's photograph and the repository is public, so whether
they are kept in it is the owner's decision.

## Running it

```
python3 -m venv blendenv
blendenv/bin/pip install bpy==5.2.3 opencv-python-headless scikit-image scipy numpy
cd <work dir with ref photo + mask.png>
blendenv/bin/python shape.py && blendenv/bin/python bake.py && blendenv/bin/python rig.py && blendenv/bin/python export_glb.py
```

## Next

- The couch-down, lying and stand-up clips.
- The bull, the calf and the majaheem body.
- The other four light coats as textures on the same mesh.
- Impostors for distant crowds.

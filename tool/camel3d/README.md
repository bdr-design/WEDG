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
| 6. Detail levels | `lods.py` | `_lod1.glb` (8k triangles, 1K textures, 618 KB), `_lod2.glb` (1.5k triangles, 512 px, 264 KB); same skeleton and clips |
| Checks | `render_tex.py`, `render_anim.py` | Cycles renders in desert light |

## How each step works

- **Shape:**
  - The body, neck and head are the photo's outline inflated sideways, with
    real camel widths per region (barrel, narrow hump ridge, narrow neck and
    head).
  - The legs, knees, fetlocks, two-toed foot pads, ears, chest pad, lower lip
    and tail are tapered tubes and ellipsoids at real proportions.
  - Everything is joined with a smooth union and meshed with marching cubes.
  - Scale: 443 px = 1 m, so the hump is 2.05 m above the ground.
- **Textures:** the photo is projected from the side onto side-facing skin.
  The top, bottom, front and legs get a coat built from the photo's own
  colours, with dust toward the feet, calluses on the knees and chest pad,
  and dark soles. The normal map adds fur grain.
- **Clips:**
  - `idle` (4 s).
  - `walk`: built from foot physics and checked against Muybridge's camel
    walking (*Animal Locomotion* plate 737, 1887; in
    `assets_src/reference/`).
    - **Footfalls:** a lateral-sequence walk close to a pace. A planted foot
      moves back at exactly the ground speed. At the end of the stance the
      heel lifts while the toes stay down.
    - **Forelimb:** while it carries weight, the forearm and cannon form one
      straight column with the carpus locked. The shoulder blade turns with
      the stride, and the shoulder and elbow take up the length. In the
      swing the carpus folds about 78° and the pastern curls.
    - **Hind limb:** the thigh swings about the hip, and the hock folds back.
    - **Joint accuracy:** the legs splay slightly, so each joint is re-aimed
      until the fetlock lands within 2 mm of its target.
    - **Body:** carried at the height the planted legs allow, with a 1.2 cm
      bob, a sideways shift over the supporting side and a roll. The neck and
      head counter the bob.
    - **Weight:** the pads spread under load.
    - **Pace:** 1.15 m/s (about 4 km/h), 1.45 s and 1.67 m per stride.
    - **Measured:** the toes slip under 2 mm per frame and stay within 2 mm
      of the ground while planted.
  - `graze` (4 s): the muzzle reaches the ground about 0.75 m in front of
    the forefeet.
- **Budget:** 40k triangles, 37 bones, 2K textures, 2.1 MB GLB.

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

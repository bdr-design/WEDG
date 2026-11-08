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
  - `walk`: built from foot physics, not keyed by hand (`walk_physics.py`).
    - Each planted foot moves back under the body at exactly the ground
      speed.
    - The legs turn about the top of the shoulder blade and the hip joint.
      The lower legs are solved so the carpus folds forward and the hock
      back.
    - The body drops only as far as the planted legs need (an inverted
      pendulum), shifts over the side carrying it and rolls.
    - Gait: a lateral-sequence walk close to a pace; the forefoot lands 8%
      of a stride after the hind foot of the same side.
    - 0.85 m/s, 1.3 s per stride, 1.1 m stride.
    - Measured: planted pads slip under 1 mm per frame and stay within
      2 mm of the ground. The body bobs about 5 cm.
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
- LOD1 and LOD2.

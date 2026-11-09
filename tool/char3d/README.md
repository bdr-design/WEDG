# The player character, built by code

A Saudi man in a white thobe, red shemagh, black iqal and leather sandals.
He is rigged, and has walk, run and idle clips. The output is
`assets_src/characters/man.glb`.

## Steps

1. **`char_build.py`** (the body and the clothes):
   - **Body:** the MakeHuman base mesh (CC0) with male macro targets, about 1.74 m tall.
   - **Rig:** the MakeHuman skeleton merged into 26 game bones (`rig.py`), plus four skirt bones.
   - **Bind pose:** the arms held a little out, so the armpits stay open when the clothes are made.
   - **Clothes:** signed distance fields round the body, meshed with marching cubes and decimated:
     - The thobe is a 5 mm shell, open at the hem, the cuffs and the neck, with a collar band. The skirt is an A-line that always contains the legs.
     - The shemagh is a cap and a drape open at the face. The back point and the two front ends lie on the thobe. The houndstooth weave repeats 6 times round the head.
     - The iqal is two cords on a band tilted down at the back.
     - The sandals are a sole and a toe strap.
   - **Hidden body:** what the thobe and the shemagh cover is removed, and the cut ends are capped.
   - **Triangles:** the face keeps its detail; hands and feet are cut harder. The total is about 12.5k.
   - **Skinning:**
     - The clothes take their weights from the body: the sleeves from the arms, the torso cloth from the spine, the skirt from the hips and four panel bones.
     - At most 4 bones per vertex, as in glTF.
   - **Looks:**
     - Skin: one 1K texture painted through the UVs, with a short beard, moustache and brows.
     - Eyes: an iris and pupil.
2. **`char_walk.py`** (the clips and the export):
   - Walk, run and idle come from a footfall plan and two-bone IK. The heel strikes with the toes up, and the heel rises at push-off while the toes stay flat.
   - **Skirt panels:** front, back, left and right swing each frame so the cloth clears both shins, ankles and feet. The front panel follows the leading leg and the back panel the trailing one.
   - **Export:** one GLB with the three clips.
3. **`measure_gait.py`**:
   - Prints the stance share and the planted-foot speed of each clip.
   - Measured:
     - Walk: about 58% stance, the foot moving at 1.23 m/s.
     - Run: about 30% stance with a flight phase, at 3.5 m/s.
   - The game plays each clip at the matching rate, so the feet do not slide.
4. **`find_fin.py`** lists the most stretched cloth edges in a run frame, with their weights. It finds badly weighted cloth.

## Running it

The MakeHuman data is a sparse clone of `makehumancommunity/makehuman`: `makehuman/data/3dobjs`, `rigs` and `targets`. Its assets are CC0. Point `MAKEHUMAN_DATA` at that `data` folder. Blender is the `bpy` module.

```
python char_build.py out/c      # renders out/c/c_front.png, c_side.png, c_back.png, c_face.png
python char_walk.py out/c/character.blend out/w render
python measure_gait.py out/w/animated.blend
```

## Known gaps

- The fingers are merged into one hand bone, so they cannot curl yet.
- The thobe stretches a little at the armpit in the run.
- The shemagh has no folds or front peak.

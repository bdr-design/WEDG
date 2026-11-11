# Outside models (private use only)

Models made by others, kept apart from the code-built car. Each is used under its own licence, recorded here.

The owner's game is private and earns nothing (his word, 11 Nov). If that ever changes, everything in this folder
and the `thirdparty_*` scripts' outputs must be dropped: the code-built car in `../` is ours and stays usable (its
last state before any outside model is commit 0197fe3).

## 2024 Toyota Land Cruiser LC300 VXR 409 TT

- Author: Ddiaz Design, https://sketchfab.com/ddiaz-design
- Source: https://sketchfab.com/3d-models/2024-toyota-land-cruiser-lc300-vxr-409-tt-0937e2b405964856a1aac96f54861274
- Licence: CC BY-NC-SA 4.0, http://creativecommons.org/licenses/by-nc-sa/4.0/ (the author credited; no commercial
  use; changed versions under the same licence). Its licence file is `lc300_LICENSE.txt` here.
- Downloaded by the owner from Sketchfab (glTF), 11 Nov 2026. 1.1 million triangles, 30 materials.
- Used for: the whole private car, outside and inside (the owner's decision, 11 Nov: "the downloaded model, whole",
  with his rules for the car: black gloss paint, the glass fully dark, the Saudi plate ا م ن 1, no badges or names,
  layers for the phone).

Credit line, wherever the game shows its credits:

> This work is based on "2024 Toyota Land Cruiser LC300 VXR 409 TT"
> (https://sketchfab.com/3d-models/2024-toyota-land-cruiser-lc300-vxr-409-tt-0937e2b405964856a1aac96f54861274)
> by Ddiaz Design (https://sketchfab.com/ddiaz-design) licensed under CC-BY-NC-SA-4.0
> (http://creativecommons.org/licenses/by-nc-sa/4.0/)

What was changed (so the changed version is under the same licence):
- Set in our car's frame: its axles on ours, scaled by the spec's wheelbase.
- No brand marks: the badges (grille, tailgate, the tailgate's name in letters and its two small badges, the left
  front door's badge, the wheel caps) and the steering wheel's emblem dropped (the pad's plain
  recess it sat in shows); the plates (each reading the car's name) replaced by our Saudi plates; the tyres' sidewall lettering and logo, the sound system's logo, the "HDMI" label, the car's name (in colour and roughness)
  and the screens' pictures (app icons) taken off the textures; the screens made plain dark displays.
- Paint black gloss; all glass opaque black gloss.
- Split in two: the interior (the cabin's parts; loaded only while the player is inside) and the outside (the rest).
- Faces nobody can see dropped, then thinned for the phone (figures from the last build; see below for the budget):
  - the interior: what the driver sees from the seat, and what the open driver's door shows. About 82k triangles
    plus the door's trim (about 6k). Its 6600 small parts (buttons, rings) are kept whole, and so are the edges of
    its big panels: thinned with the rest, they broke into holes and slits. It loads in the background and is drawn
    only from the driver's seat or while the door stands open;
  - the outside: a near layer of about 65k and a far layer of about 14k (its glass held: thinned, the far car had no windows). That is one draw per material, plus the
    wheels, the calipers and the driver's door, which are apart because they move. The edges of parts over 0.01 m²,
    the tailgate's emblem recess and the roof's antenna are held in the thinning. Faces the thinning turned over are
    turned back. A dark panel stands behind the grille and the intakes, where the radiator is;
  - textures: at most 1K inside, 512 on the near outside and 256 on the far; roughness maps at 512. Textures that a
    face reads at one point only, or that hardly vary, become plain values. Identical images are merged. UV maps no
    texture reads are dropped;
  - materials: metal only where it is metal (the source puts 0.4-0.7 on leather, fabric and rubber); a clear coat
    only on the paint.
- Moving parts for the game: the four wheels on their own corners (for the springs and the steering); the steering
  wheel on its column's axis, fitted to the rim alone (about 25 degrees from level); and the driver's door with its
  trim on the model's own hinge.
- The glass's faces turned into the cabin dropped (from inside, the game sees out through the glass).
- What belongs to the interior is judged against the model's own outside (its paint, glass and lamps), not against
  our code-built hull. Judged against our hull, the tail lamps' housings were lost.

**The car's measures against the spec** (the model is scaled so that its wheelbase is the spec's; the rest is the
artist's, measured on the near layer):

| | Model | Spec (DIMENSIONS.md) |
|---|---|---|
| Wheelbase | 2.850 m | 2.850 m |
| Front axle | x +1.556 | x +1.556 |
| Length | 5.046 m | 4.985 m (+61 mm) |
| Width (body) | 1.956 m | 1.980 m (-24 mm) |
| Height | 1.910 m | 1.925 m (-15 mm) |
| Track | 1.630 m | 1.665 m (-35 mm) |
| Tyre | 0.83 m across | 0.80 m (265/55R20; +3.5 %) |

**Weight against the owner's budget:** on 10 Nov the owner chose about 40k triangles inside and about 40k outside
near. This model needs more to have no holes: about 87k inside (drawn only from the driver's seat or through the
open door) and about 65k outside near. At 48-51k the near layer showed the sky through the bonnet and the tailgate;
at 65k a few slivers remain (the tail lamps' upper inner corners, the rear bumper's upper slats, the spoiler's edge);
the engine bay and the wheel wells are closed from behind by dark inward-facing shells.
That trade-off is the owner's to confirm.

How it is made (from `../`): `BLENDPY=<python with bpy> sh thirdparty_build.sh <scene.gltf> suv.blend <work dir> <out dir>`
(the out dir outside the repository: the built files are not committed; `thirdparty/*.glb` is ignored)
(thirdparty_frame.py, thirdparty_tex.py, thirdparty_cabin.py, interior/lod_cabin.py, thirdparty_clean.py,
thirdparty_car.py, thirdparty_lod.py, thirdparty_rig.py, thirdparty_export.py). It writes `lc300_interior.glb`, `lc300_near.glb` and `lc300_far.glb`.

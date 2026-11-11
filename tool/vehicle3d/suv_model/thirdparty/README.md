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
  front door's badge, the wheel caps) and the steering wheel's emblem dropped (its opening in the pad filled flat); the plates (each reading the car's
  name) replaced by our Saudi plates; the tyres' sidewall lettering and logo, the sound system's logo, the car's name
  and the screens' pictures (app icons) taken off the textures; the screens made plain dark displays.
- Paint black gloss; all glass opaque black gloss.
- Split in two: the interior (the cabin's parts; loaded only while the player is inside) and the outside (the rest).
- Faces nobody can see dropped (the interior: from the seats; the outside: from round the car, above it and the
  seats), then thinned for the phone: the interior to about 114k triangles (its 8230 small parts, buttons and rings,
  kept whole: thinned with the rest they broke into holes), the outside to a near layer of about 40k and a far layer
  of about 12k (one draw per material). Textures at most 1K (the switches' sheet 2K inside), the roughness maps 512.

How it is made (from `../`): `sh thirdparty_build.sh <scene.gltf> suv.blend <work dir> thirdparty`
(thirdparty_frame.py, thirdparty_tex.py, thirdparty_cabin.py, interior/lod_cabin.py, thirdparty_clean.py,
thirdparty_car.py, thirdparty_lod.py, thirdparty_export.py). It writes `lc300_interior.glb`, `lc300_near.glb` and `lc300_far.glb`.

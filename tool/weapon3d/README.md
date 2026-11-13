# The Kalashnikov, built by code

The owner asked for a Kalashnikov rifle (كلاش) for the hunting subject, and for its design to be decided here, with
no photos of his own (13 Nov 2026). `akm.py` builds it in Blender's Python: the shape from the dimensions below, one
painted 512 px colour texture and one roughness/metal texture, no downloaded mesh or picture.

Its place in the game is the owner's decision of 13 Nov 2026: it enters with its risk, as cheating does in the
festivals, and is never shown as lawful. By the Saudi rules found it is no lawful hunting weapon and no private person
may own one (`docs/proposals/hunting.md`, `docs/proposals/gdd_hunting_section.md`).

## The design

The AKM pattern with wooden furniture, the «كلاش روسي» of the Gulf, as a herder who looks after it keeps it: clean
and used, not new and not battered.

- Stamped receiver with its rivets and axis pins, the ribbed dust cover, the selector lever on the right (up, at
  safe) with the arc it wears bright into the receiver, the charging handle and the bolt carrier's bare steel.
- Laminated birch stock and handguards under a red-brown shellac, darker where hands hold them; the lower handguard
  with its palm swells; a steel butt plate.
- A dark red-brown phenolic pistol grip; the ribbed steel 30-round magazine.
- Black oxide steel, its edges worn to dark steel, and bare at the muzzle, the front sight's ears, the charging
  handle and the magazine's floor plate.
- The tangent rear sight, the front sight with its two ears, the slanted gas block, the cleaning rod, the slanted
  compensator.
- A khaki canvas sling, a part of its own (`akm_sling`), so it can be left off.
- No maker's marks, stamps, numbers or writing.

The Chinese Type 56 (milled receiver, hooded front sight, no compensator, often a folding spike bayonet) is at least
as common in Saudi hands as the Russian AKM. Which of the two the game's rifle is, is the owner's choice; this is the
AKM.

## Dimensions

Millimetres, measured along the rifle from the butt plate, and up or down from the bore's axis. None of the sources'
pages could be opened from the build machine: the published figures are from search summaries of the pages named,
and the placements are from a museum photograph of a real AKM (Armémuseum, Stockholm, on Wikimedia Commons) scaled to
880 mm by the reviewer, good to about 2%. The photograph is a reference only and is not in the repository.

| What | Real | Source | Model |
|---|---|---|---|
| Overall length | 880 | AKM, Wikipedia (en, ru); armoury-online.ru | 880 |
| Barrel | 415 | the same | the barrel's breech is inside the receiver; its muzzle at 860 |
| Sight radius | 378 | AKM, Wikipedia; Russian training notes | 378 (the notch at 462, the post at 840) |
| Height, front sight to the magazine's foot | 246 (photo); 258 (Imperial War Museum catalogue) | photo; iwm.org.uk 30030076 | 245 |
| Front sight's top above the bore | 48 to 49 | photo | 50 (the ears), 48.5 (the post) |
| Buttstock wood | 5 to 235, the butt 92 tall, its top about level with the bore | photo | 3 to 238, 91 tall |
| Length of pull | 321 | Arsenal Inc (a part's figure) | 321 (the trigger at 321) |
| Pistol grip | 236 to 305, its foot 133 under the bore | photo | 251 to 299 at the top, its foot 132 under |
| Magazine | its top from 384, its foot 197 under the bore and about 100 forward | photo | from 384, 195 under, 104 forward |
| Lower handguard | 491 to 642, from 17 above the bore to 30 under | photo | 491 to 642, 14 above to 31 under |
| Upper handguard | 543 to 641 | photo | 543 to 641 |
| Gas block | about 730 | photo | 716 to 747 |
| Width | no maker's figure; 43 to 70 in catalogues | Imperial War Museum; AK-74M's 70 | 62 with the charging handle |
| Weight (for the record) | 3.1 kg without magazine; the steel magazine 0.33 kg | ru Wikipedia; armoury-online.ru | – |

Marked as taken from proportion, with no source of their own: the receiver's height (52) and width (33), the dust
cover's height (22), the barrel's thickness (14.4), the compensator (22 long), the sights' and the selector's small
parts, the sling (25 wide). The front sling swivel is on the handguard's retainer, as on the AKM (the AK-47 has it on
the gas block).

## Weight on the phone

| Detail level | For | Triangles (rifle + sling) | Draws |
|---|---|---|---|
| `akm.glb` | in the hands, close | 5,368 + 144 | 1 (2 with the sling: the same material, a part of its own) |
| `akm_lod1.glb` | slung on a walking figure | 746 + 24 | 1 (2 with the sling) |

One material, two 512 px textures (colour; roughness and metal): 2 x 1.4 MiB uncompressed with mips, less compressed.
The steel's bevels are real faces mapped to the worn colours, so the edge wear costs no extra texture.

## Points for the hands and the sling

Named empties under the root (metres in the file): `grip_r` (the right hand round the pistol grip), `hand_l` (the left
hand under the lower handguard's swell), `sling_front`, `sling_rear`, `muzzle`, `butt`. The origin is the butt
plate's centre line at the bore's height: X along the rifle to the muzzle, Z up, the rifle's right side at -Y (in the
GLB, Y up).

## Running it

Blender is the `bpy` module (the project's `blendenv`).

```
python akm.py out            # out/akm.glb, akm_lod1.glb, akm.blend; prints triangles and measures
python akm.py out quick      # and the right side's picture, fast
python akm.py out render     # and all the pictures: both sides (the right with a centimetre ruler), top, front,
                             # three-quarter, close, and beside the player's figure (assets_src/characters/man.glb)
```

The game's copies are `assets_src/weapons/akm.glb` and `akm_lod1.glb`; the pictures are in `design/weapon/`.

## Not done yet

- It is not in the game page: holding and slinging it on the figure comes with the hunting design.
- The figure's fingers cannot curl (tool/char3d's known gap), so a held rifle will need that first.
- No fire, recoil or sound.

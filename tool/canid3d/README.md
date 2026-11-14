# The wolf and the dogs, built by code

The owner asked on 13 Nov 2026 for the animals to be made now and shown to him («ابي تدخل الحيوانات الان وتعرضها علي
كذالك موسم القنيص»). His decision on wolves (`docs/agents/hunting_owner_decisions.md`,
`docs/proposals/gdd_hunting_section.md` 13.5, `docs/research-realism.md` section 8):

- the wolf is a rare danger to the calves at night;
- it is protected, and killing it never lowers the danger;
- stray dogs are a like danger (a game choice where the research has no source);
- the right protection is a strong fence, a herdsman and a guard dog, which the player buys and feeds.

These scripts build, in Blender's Python, at their real sizes:

- the Arabian wolf (الذيب العربي, *Canis lupus arabs*): an adult in its summer coat, standing alert, in the low
  stalking walk near the pens, and running off;
- the guard dog (كلب الحراسة): the local pariah type (the Bedouin dog; see "The guard dog's type"), a male with a
  leather collar, standing alert, lying at rest by the pen, and barking;
- the stray dog (الكلب الضال): **the guard dog's build in poor condition** (the same code and numbers with a body
  condition setting: the loin and belly tucked up, the neck thinner, the hip bones and the spine showing), another
  coat (dull, dusty) and no collar, standing wary and barking.

No mesh or picture is downloaded: every shape comes from the numbers below and every colour is painted with numpy
from the descriptions below. There is no rig yet. The poses are separate meshes; the rig comes after the owner
approves the look (plan at the end).

**Each animal is one skin** (the second round, after the reviewer found the first round's 17–24 pieces stuck into
one another reading as toys): the build's pieces are only its skeleton of shapes. They are turned into distance
fields, joined by smooth unions (the legs grow out of the trunk, the neck into the skull, the ears out of the skull's
corners, the toes out of the paw) and meshed as one closed surface, as `tool/camel3d/shape.py` builds the camel.

## Files

| File | What | Triangles | Draws | Texture pair |
|---|---|---|---|---|
| `assets_src/canids/wolf_alert.glb`, `wolf_stalk.glb`, `wolf_run.glb` | the wolf, close: one skin | 7,000 each | 1 | 512 px |
| `wolf_*_lod1.glb` | the wolf, far: the same skin decimated | 1,300 each | 1 | 256 px |
| `dog_alert.glb`, `dog_lie.glb`, `dog_bark.glb` | the guard dog, close: the skin, its collar and the collar's ring (3 pieces); barking, also the four canines | 7,616 / 7,616 / 7,760 | 1 | 512 px |
| `dog_*_lod1.glb` | the guard dog, far: the skin and the collar (2 pieces) | 1,420 each | 1 | 256 px |
| `stray_alert.glb`, `stray_bark.glb` | the stray, close: one skin (the barking file adds the canines) | 7,000 / 7,142 | 1 | 512 px |
| `stray_*_lod1.glb` | the stray, far | 1,300 each | 1 | 256 px |

- **One mesh and one material per file, one-sided:** the skin and every extra piece are closed. The collar is in the
  same mesh and the same texture.
- **The texture pair:** colour (the occlusion baked into it: 48 rays from each vertex) and a tangent-space normal
  map (the fur's grain: fine streaks along the hair's run and the coat's coarser lie); roughness is one value
  (0.85). 512 px close is 2.67 MiB uncompressed with mipmaps (both textures, RGBA8, counted as ADR 0005 counts them),
  about 0.67 MiB as ASTC 4×4. 256 px far is 0.67 MiB uncompressed.
- **The texture layout:** Blender's smart projection of the skin, packed with a margin of 0.003 (about 1.5 texels
  at 512 px) between islands, the head given 2.0 times the texture per millimetre (the unwrap is made on a copy whose
  head is swollen, then copied back). The texture covers about 58% of its square: a texel is about 3.0 mm on the
  body and 1.6 mm on the head at 512 px (6.0 and 3.2 mm far).
  - **No two texture triangles overlap:** where the decimated skin folds a sliver under its neighbour, the projection
    overlaps; one face of each such pair is moved to a free place of its own. `build.py` rasterises every triangle at
    2048 px and stops the build if any two share texels.
  - Empty texels take their nearest painted texel's colour, which within a margin is the island's own.
  - The samplers clamp to the edge (nothing wraps in from the far border); the tangents are written into the file
    (the normal map is in their frame).
  - **The margin, a trade-off:** margins of 0.010–0.013 (5–7 texels) left only 25–30% of the square covered, half
    the texture's sharpness; 3 texels kept 45% (3.7 mm a texel on the body: the grizzle stepped close up); 1.5 texels
    keep 58%. With no overlaps left, a thin margin only lets a mipmap far down mix two neighbouring islands, whose
    colours are near each other on one animal.
- **Reproducible:** the same code writes the same GLB files byte for byte. The exporter's triangle order is settled
  after writing (`common.settle`, as in `tool/weapon3d/akm.py` and `tool/bird3d`). Checked by building every file
  twice and comparing checksums (the report gives the result).
- **The teeth:** only the open-mouthed poses (barking) have the canines. Shut, they would sit inside the lips. The rig
  will carry them always, hidden by the closed jaw.

The pictures are in `design/canids/` (JPEG):
- **Each animal and pose:** from the side (orthographic, with a centimetre ruler along the ground) and from three
  quarters.
- **Standing and barking poses:** a close view of the head.
- **Standing:** the front view, the view from above, and the forepaws close from three-quarter front with a raking light (`*_alert_paws.jpg`).
- `canids_far_15m.jpg`: the far models (standing) from the game's camera at 15 m in the game's light, as the phone
  shows them, with a ×4 enlargement.
- `canids_scale.jpg`: all of them beside the player's figure and a calf a few days old.
- `wolf_night_20m.jpg`, `wolf_night_46m.jpg`, `wolf_day_46m.jpg`: the wolf where the game will show it (below).
- `wolf_summer_winter.jpg`: the coats compared (question 2).

The studio pictures use AgX tone mapping and soft area lights, so the pale belly and the sandy dog keep their detail
and the dark saddle is not lost. The night pictures use the game's own tone mapping (Khronos PBR Neutral).

## Weight on the phone

The budget is ADR 0005's: 200 draws and 400k triangles a frame with shadows, and 80 MiB of compressed textures.

- **What a scene shows:** one or two wolves, one guard dog, a few strays. The wolf and the strays come at night and
  are mostly seen far. The guard dog may be near the camera at the pens.
- **A night scene:**
  - two wolves far: 2 × 1,300;
  - the guard dog close: 7,616;
  - three strays far: 3 × 1,300;
  - total about 13k triangles in 6 draws, 12 with each casting a live shadow;
  - that is 3% of the triangle budget (7% counting the shadow pass) and 3% of the draws.
  - Textures: three animals, each with its close and far pairs, are 10 MiB uncompressed, about 2.5 MiB compressed.
- **How large the wolf is on the screen** (the game's camera: 40° vertical field of view, 956 × 440, the camera 28°
  down):
  - about 48 css px tall at 10 m, 24 at 20 m (measured on `wolf_night_20m.jpg`: 22 px), 16 at 30 m, 10 at the 46 m
    of the camp view.
  - The close model is for under about 10 m (the guard dog at the pen, a wolf the camera is brought to).
  - The far model (1,300 triangles) is for 10 m and beyond.
- **The far model's triangles:**
  - At 20 m the wolf covers about 1,000 screen pixels, so its 1,300 triangles are about one to a pixel.
  - Beyond about 30 m a third level of about 300 triangles would do, and that is cheap to add. Not built: at most
    five canids in a scene make 6.5k far triangles, under 2% of the budget.
- **Why the close model is 7k:**
  - The skin before decimation has about 300k triangles; collapse decimation keeps them where the shape turns.
  - The toes need about 350–450 triangles a paw to read as four toes close up; at 5,600 in all they took half the
    model and starved the face. At 7,000 the wolf has about 1,950 in the head (with the ears), 1,570 in the four paws
    and 3,480 in the body; the decimation spares the head a little and the paws a little (`skin.HEAD_SPARE`,
    `PAW_SPARE`). 7k is still under 2% of the frame's 400k.
  - As one skinned mesh this is cheap next to the camels' 8–40k.
- **Fur is texture and silhouette only:** no shells and no alpha cards. The brush of the tail and the thigh's
  breeches are in the outline; the grizzle of the guard hairs in the colour; the hair's grain in the normal map.

## The poses

- **Standing (all three animals):** the femur about 20° from upright (21° the wolf, 17° the dog: the reviewer's
  20–30°), the stifle at about 116–120°, the hock at about 126°, every paw flat on the ground.
- **The wolf's run:** the right fore alone on the ground, the left reaching, the hind legs stretched back after their
  push with both hocks at about 152° by this build's measure (the reviewer's measure from the named points reads a few degrees more; about 160° was asked), the back bent (10° per withers height along it),
  the tail streaming back and a little down. Muybridge's dog gallop (plate 707), the reviewer's reference, could not
  be opened from my tools; the pose follows the reviewer's description of it.
- **The dog lying:** on its chest, the elbows and forearms resting on the ground (the skin is pressed flat where it
  touches: its lowest point is at 0), the hind legs folded beside it, the tail along the ground.

## The Arabian wolf

**Why this wolf.** It is the wolf of the Kingdom (research [139], [148]–[150]). It is one of the smallest wolves:
lean and long-legged, with ears large for its size. That is how it differs from a northern grey wolf, and why the model
is narrow-chested, tucked up at the loin and high on its legs.

**Which coat, and why.** I built the summer coat:
- **What it is:** short and thin, the hair longer along the back.
- **Why:**
  - It is the coat it wears most of the Arabian year.
  - It is the coat that makes it read as the Arabian wolf, not a northern one.
- **The winter coat:** longer than the summer one but far shorter than northern wolves'. It is shown beside it in
  `wolf_summer_winter.jpg`: a fuller neck ruff and tail, the body a little fuller (the amounts a game choice). Which
  coat the game shows when is question 2.

**Sex.** The sources give no figures by sex (below). The model is an adult at the commonly cited 65 cm, built as a
male; a female is smaller by an unknown amount. That makes the sex a game choice.

### Dimensions

Sources:
- **(search)** marks a figure known only from a search summary. **No page could be opened from my tools:**
  en.wikipedia.org was refused and I tried no other host after it, as the brief asks.
- **(opened by the reviewer)** marks a figure the reviewer read in the page's text (it could fetch en.wikipedia's
  and ar.wikipedia's raw text), with the citation the page gives.
- **The model column** is measured on the file by `build.py` (the measures it prints).

| What | Real | Source | Model |
|---|---|---|---|
| Shoulder (withers) height | 64–66 cm on average; 70 cm in one Arabic source | en.wikipedia 'Arabian wolf', citing the UK Wolf Conservation Trust's leaflet *(opened by the reviewer)*; Saudipedia الذئب العربي *(search)* | 650 mm |
| Weight (for the record) | about 20 kg on average (one source 25 kg); females possibly as little as 10 kg | en.wikipedia, citing Lopez 2004 *(opened by the reviewer)*; Saudipedia, mawdoo3 *(search)*; a forum post *(search, weak)* | the skin's volume 27.8 L. Less the summer coat's depth (about 1.5 cm over about 0.6 m² of skin, about 9 L), that is about 19 L, so about 19 kg at a body's density: inside the range |
| Length | 114 cm, not saying what it measures; head and body not found for this subspecies | Saudipedia *(search)* | nose to tail base 996 mm; overall, nose to tail as it hangs, 1,158 mm |
| Tail | "reaches its hocks" | Saudipedia *(search)* | 390 mm (0.60 H), about 40 mm across at the root, fullest at mid-length; its tip about level with the hocks (the side picture) |
| Skull length | about 200.8 mm (cranial length) | animal database pages citing older literature *(search, weak)* | head, occiput to nose, 227 mm (with the skin, nose and fur); the muzzle (eye to nose) 0.52 of it, 80 mm wide at its base and about 64 mm at its middle; 127 mm wide at the eyes (the eyes 65 mm apart: 1.95 times, the reviewer's head-front photograph about 2.1), 138 mm across the cheeks; a stop, the forehead rising about 20 mm behind the eyes |
| Ears | "proportionally larger" than other wolves'; no length found | en.wikipedia, citing Mills 1945 *(opened by the reviewer)* | 107 mm tall, 69 mm at the base, their bases' centres 104 mm apart on the skull's corners *(a game choice)* |
| Chest depth, leg lengths, paw size | not found | – | chest bottom 328 mm, elbows 299 mm, hocks 145 mm; forepaw 73 × 53 mm *(game choices, from canid proportions)* |

The model's own proportions are game choices from general canid anatomy:
- withers height 1.0;
- body length, chest front to buttock, 1.24 (it includes the forechest and the breech);
- chest depth 0.49;
- head 0.35;
- forelimb bones 0.26 / 0.31 / 0.12, hind limb bones 0.28 / 0.30 / 0.19, all as fractions of the withers height.

### Coat, by mark

Pocock describes the colour as "a mixture of black and slightly buffy grey" (en.wikipedia quoting him *(search)*).
It is paler than the Indian wolf *(search)*. Where a mark below is "as in grey wolves", it is the common grey-wolf
pattern, not confirmed for *arabs*.

| Mark | Where | From |
|---|---|---|
| Buffy grey ground, grizzled with black-tipped guard hairs | everywhere above | Pocock *(search)* |
| The guard hairs thickest along the back and over the shoulders: a darker saddle, and a darker line down the spine | back | as in grey wolves; the back's hair stays long in the summer coat (Harrington & Paquet 1982, via ar.wikipedia *(opened by the reviewer)*) |
| A faint dark bar over the shoulder, down and forward from the withers | shoulder | as in grey wolves |
| A light tawny wash on the lower flanks; tawny legs, pale inside | flanks, legs | as in grey wolves |
| Pale cream belly, inner thighs, chest and throat | below | as in grey wolves |
| A faint dark line down the front of the foreleg | forearm | as in grey wolves (faint; not confirmed for *arabs*) |
| Pale cheeks, lips and chin; a tawny-grey bridge to the muzzle; a pale mark over each eye; a short dark line from the eye's front corner | face | as in grey wolves |
| Dark-lined almond lids; an amber-yellow iris | eyes | the lids as in all wolves; amber the usual wolf colour, not confirmed for *arabs* |
| A black nose and black lips | – | – |
| Ears: tawny backs with dark edges, pale fur inside | ears | as in grey wolves |
| Tail: grizzled above, paler below, a dark spot over the tail gland a fifth of the way down, a black tip | tail | as in grey wolves |
| Black claws | paws | – |

**The fused middle toe pads** (the third and fourth toes' pads, occasionally joined behind; told in the tracks;
en.wikipedia citing Ferguson & Menache 2002 *(opened by the reviewer)*; ar.wikipedia, citing Macdonald 1992, says the two
middle toes are fused):
- Each paw is part of the skin: four toe bulges in front (the middle two longest) with the clefts between them cut
  in, the dark claw tips painted, the dark pads below; on the forelegs the carpal pad, a small bump behind the wrist.
  The field is kept unblurred at the paws and the decimation spares them, so the toes survive. The forepaw is about
  83 mm long (the reviewer's 80–90). The legs are not thickened: the reviewer measured the photographs' pastern
  (about 30 mm) and forearm (about 51 mm), which the model matches.
- The fused pads are under the foot, so they would show only in a print in the sand or a paw turned up: they are not
  modelled or painted (a track decal could carry them later).

## The guard dog

**What really guards the herds.**
- **What source [149] (Panthera, AlUla) says:** farmers keep "security dogs", keep the stock in traditional
  enclosures, and employ herdsmen at times of high risk. It names no breed *(search)*.
- **What else was looked for:**
  - a Saudi source naming the dogs herders keep at an عزبة, or a breed used there;
  - Arabic searches for كلب حراسة الغنم والإبل, الكلب البدوي, البلدي, الهولي.
  - None was found *(searches returned nothing on dogs)*.
- **The nearest:** saudi-archaeology.com's page on the "Canaan or Bedouin Dog" *(search)*:
  - a pariah dog of medium, strong build, the chest moderately broad and deep, the loin well tucked up, pricked ears,
    the tail carried moderately high;
  - Bedouin captured and tamed young males rather than breeding them;
  - "they make excellent guard dogs for the camp", "also used to guard the livestock".
  - The same breed is also called the "Bedouin sheep dog" (en.wikipedia 'Canaan Dog' *(search)*).
- **Proposed (a game choice, question 3):** the local pariah type, which herders call by no breed name I could
  confirm (كلب بلدي / كلب بدوي are the plain words). Built with the Canaan or Bedouin dog's figures.

| What | Real | Source | Model |
|---|---|---|---|
| Shoulder height | males 50–60 cm, females 45–50 cm | Kennel Club and UKC Canaan Dog standards *(search)* | 560 mm, a male |
| Weight (for the record) | 18–25 kg | the same *(search)* | the skin's volume 21.4 L; less about 5 L of short coat, about 16–17 kg: at the range's low end, a lean working dog (the stray: 20.2 L) |
| Build | square, chest to the elbows, loin tucked up, wedge head, short erect ears broad at the base, bushy tail curled over the back when alert | the same; saudi-archaeology.com *(search)* | nose to tail base 815 mm; head 202 mm, the muzzle 0.47 of it (70 and 60 mm wide at 0.62 and 0.76), 115 mm across the cheeks; ears 76 × 70 mm, their bases' centres 95 mm apart; loin girth 470 mm (the stray's 394 mm, 16% less); the tail curled over the back |
| Coat | short to medium, harsh; sand to red-brown, white, black, with or without white markings | breed standards *(search)* | sandy, white chest, belly, socks and tail tip: one of the type's colours, a game choice |
| Collar | not found as a practice for herders' dogs | – | a dark leather collar 26 mm wide with a steel ring under the throat *(a game choice: it marks the dog as the player's own)* |

## The stray dog

- **Who they are:** the free-ranging dogs of the town edges, reported attacking people in al-Ahsa, Buraidah,
  al-Aflaj and Riyadh. The municipal ministry told municipalities to trap, vaccinate, sterilise and release them, and
  ended poisoned baits (research [151]).
- **What they look like:** no Saudi survey of their coat or condition was found *(search)*. Two Saudi studies of
  stray dogs (Riyadh, Asir, Qassim) report parasites, not looks *(search)*.
- **Why the guard dog's build:** they are the same pariah stock as the herders' dogs, so the honest model is the
  guard dog's numbers and code with a body condition setting (`condition` 0.86 in `species.py`, a game choice of how
  thin): the loin and belly tucked up, the loin's girth about 12% under the dog's (measured below), the neck thinner,
  the hip bones' points and the spine's processes showing. The poses differ, as the rig's will.
- **The coat:** a dull ginger-tan with a darker, mottled back; off-white below, dusty on the belly and legs; no
  collar. The colour is a game choice.

## Where the night pictures stand

**The game has no night yet:** the prototype's sun is a fixed November afternoon (`design/prototype3d/farm.html`
around lines 302–320). So the night light in `wolf_night_*.jpg` is my own choice (a game choice): a full moon's cool
light from high in the south-east and a faint blue sky, with the game's tone mapping. How the wolf reads at night must
be judged again when the game has its night.

The pictures:
- The stalking wolf's far model, 3 m from a calf, seen from the game's camera at 20 m and at 46 m (the camp view's
  distance), at 956 × 440.
- A ×3 enlargement of the place beside it, so it can be read (the enlargement is not what the phone shows).
- `wolf_day_46m.jpg`: the same in the game's afternoon light.

What they show:
- At night the buffy wolf reads as a dark shape against the moonlit sand: it is the shape (the low head, the
  hanging tail) that tells it, not the coat.
- At 46 m it is about 10 px tall.

**The calf:** the game has no calf model. `farm.html` draws a calf a few days old as the grown she-camel
(`assets_src/camels/camel_wodh_female.glb`) at 0.55 of her size (its `SIZE_AT`, a game choice there). The research's
case [168] is a calf three days old, so the pictures use the same.

## Named points

In the GLB, metres, under each file's root (the close and the far file of a pose carry the same points). The animal faces +X; the origin is on
the ground under the body's middle.
- `foot_fl`, `foot_fr`, `foot_hl`, `foot_hr`: the sole's point under each paw, with its forward and up.
- `shoulder_l` / `_r`, `elbow_*`, `wrist_*` (the carpus).
- `hip_l` / `_r`, `stifle_*`, `hock_*`.
- `withers`, `hips`.
- `neck_base` (with the neck's direction), `head` (with the head's axis), `jaw` (the hinge, with the jaw's axis),
  `nose`.
- `eye_l` / `_r`, `ear_l` / `_r` (their bases).
- `tail_base` (with its direction).
- `collar_ring` (the guard dog only): where a chain or lead clips on.

## How it is built

- `common.py`: copied from `tool/bird3d` (the loft, the files, the studio, the GLB settling).
- `canid.py`: the shapes of one animal from its numbers, in groups (the trunk, the neck, the head, each ear, each
  leg, each paw, the tail).
  - The torso is lofted along the body, its lower half narrowing to a keel at the chest and the belly; the back can
    bend (the run).
  - The neck runs on into the back of the skull. The head is lofted along its axis as a wedge, with a lower jaw hinged
    under the cheek, and a nose pad; the eyes are small bulges on the skull's sides.
  - The ears are cupped blades with rounded tips, set on the skull's corners, splayed and tipped by the pose.
  - The legs are tubes through their joints, the forearm and gaskin flattened sideways. Each leg is solved by two-bone
    inverse kinematics from the shoulder or hip joint to the carpus or hock, which is placed from the paw's spot and
    the metapodial's lean: the elbow always bends back and the stifle forward. The kneecap and the heel bone's point
    are small bulges, so the stifle and the hock show.
  - Each paw: its pad and four toe bulges; the carpal pad behind each wrist.
  - The tail; the collar and its ring; in an open mouth, the canines.
  - A thin animal's hip bones and spinal processes as small bulges (the stray's condition).
- `skin.py`: the one skin.
  - Each group's occupancy on a voxel grid (H / 220: 2.95 mm for the wolf), by the parity of vertical rays through its
    closed pieces; its signed distance by distance transforms.
  - The groups joined by smooth unions (the camel's `smin`), each with its own radius (the neck 0.045 H, the legs
    0.034–0.040 H, the head 0.040 H, the tail 0.018 H, the paws 0.012 H, the ears 0.008 H).
  - Marching cubes (scikit-image) on the lightly blurred field; hollows left inside dropped; pressed flat where it
    touches the ground; smoothed twice; decimated (Blender's collapse) to 5,600 and 1,300 triangles.
  - Unwrapped (smart projection, packed, the head given more texture).
- `texture.py`: the texture pair. Each texel is found on the skin, then on the nearest piece of the posed build, then
  at the same place on the standing build, where the coat is laid out; the skin's normal is turned back the same way.
- `paint.py`: the coats, by mark, blended across the joins (a leg into the trunk, the head into the neck, an ear into
  the skull, the tail into the rump), so the skin shows no seam; the fur's relief for the normal map.
- `species.py`: the animals' numbers (in units of the withers height) and poses.
- `scene.py`: the scale, night, winter and far pictures.
- `build.py`: runs everything, writes the files and pictures, and prints the measures.

```
python build.py OUT                         # every GLB, with triangles, sizes and the model's measures
python build.py OUT wolf quick              # quick pictures of one animal (wolf, dog, stray)
python build.py OUT wolf,dog,stray render   # the full picture set
python build.py OUT wolf_winter             # the winter coat (only for the comparison)
python build.py OUT scale,night,winter,far render
CANID_VOLUME=1 ...                          # also the standing model's volume
```

**Requirements:** Blender as the `bpy` module (the project's `blendenv`), with numpy, SciPy, scikit-image (marching
cubes) and Pillow in the same environment.

**Time:** the whole set (16 GLBs) takes about 17 minutes on this machine (4 cores shared with other agents), the
pictures much longer. Each pose's field is voxelised piece by piece in Python (a ray parity per voxel column), each
texel of two textures is found on the skin, on the nearest piece and on the standing animal, and the occlusion casts
48 rays from every vertex; the overlap check rasterises every triangle at 2048 px. The GLB files are copied to `assets_src/canids/` and the
pictures to `design/canids/`.

## The rig and clips to come (not built)

**Bones: 32.**
- root, hips, spine, chest;
- neck 2, head, jaw, ears 2;
- each foreleg 5: scapula, humerus, radius, metacarpus, paw;
- each hind leg 4: femur, tibia, metatarsus, paw;
- tail 4.
- The collar rides on the first neck bone.

**Mesh cost:** one skinned 6–7k mesh close (under about 10 m), and the 1.3k far mesh with a baked bone-matrix
animation texture beyond it, as ADR 0005 plans for the camels: 32 bones × about 40 frames × 5 clips is about 100 KB.

**What of the camel's rig (`tool/camel3d/rig.py`, 37 bones) is reused:**
- its `bone()` helper and the way it keys clips and bakes them;
- the leg chains' structure: scapula, upper arm, forearm, cannon, pastern and foot map to scapula, humerus, radius,
  metacarpus and paw (the canid has one bone fewer: its toes and pad are one paw bone); thigh, shin, cannon, pastern
  and foot map to femur, tibia, metatarsus and paw;
- the ear bones, and the tail chain (3 bones, the canid's 4).

**What is not reused:**
- The camel's bone places: written as camel coordinates (`W(...)`). The canid's come from this model's named points.
- Its five-bone neck (two for a canid) and its lip bone (a jaw for a canid).
- Its clips: a camel paces, moving both legs of a side together. A canid walks in a four-beat lateral sequence,
  trots in diagonal pairs and gallops.

| Clip | Animal | Real reference | Source |
|---|---|---|---|
| Stalk (slow, crouched walk) | wolf | walk footfalls in lateral sequence: LH, LF, RH, RF | Hildebrand 1980 *(search; his gait classification, not a wolf measurement)*; speed: to film or watch, not found |
| Trot | wolf, dogs | diagonal pairs together; the wolf's usual travelling pace about 8 km/h, kept up for hours | Animal Diversity Web 'Canis lupus' *(search)*; 8–9 km/h, another page *(search)* |
| Run, chase | wolf, dogs | the rotary gallop at high speed (dogs use the transverse gallop at lower speed); the wolf's top speed 56–64 km/h, held in a chase for about 20 minutes | Walter & Carrier 2007, cited by Biancardi & Minetti 2012 *(search)*; San Diego Zoo Wildlife Alliance fact sheet *(search)*; 55–70 km/h, another page *(search)* |
| Carry off (drag) | wolf | the case [168]: the wolf "dragged out" a three-day-old calf. A newborn camel is far heavier than a wolf can carry, so the clip is a backward drag, head low, the calf's neck in the jaws | research [168]; how a wolf drags: to film or watch |
| Idle (breathing, head turns, ears) | dogs, wolf | – | to film or watch |
| Lie down, lie, get up | dog | – | to film or watch |
| Bark | dogs | the jaw opens on each bark; the rate is not found | to film or watch |

## What is unsure

- **No page was opened by my tools.** Every figure is from search summaries or from the reviewer's opened pages,
  marked as such: no head-and-body length or sexed figure for the Arabian wolf, and no measured ear, chest, leg or
  paw size.
- **The wolf's look beyond Pocock's line** (the saddle, the shoulder bar, the leg line, the face, the eye colour) is
  the common grey-wolf pattern, not confirmed for *arabs*.
- **The guard dog's type is not settled by any source:** the pariah or Bedouin dog is the nearest description of
  herders' dogs in Arabia, from one page.
- **The collar is not a sourced practice.**
- **The volume check is rough:** it subtracts an assumed coat depth.
- **The game has no night**, so the night pictures' light is my choice.
- **Not modelled:** the fused pads (under the foot), teeth in the closed mouth, and the inside of the mouth beyond a
  painted tongue and gums.

## Known gaps, plainly (for the owner)

- **The eyes and the lip line are paint** on the skin: close up they show the texture's steps (an eye is about 25
  texels long).
- **The texture's size:** a texel is about 3 mm on the body (1.6 mm on the head); the grizzle's streaks show their
  steps in the closest pictures.
- **The toes' clefts** are shallow cuts: close up from the front they read as four toes, with some facets.
- **Where a leg meets the trunk** the skin can show a faint crease, and a little webbing between the elbow and the
  chest.
- **The dog's neck** stands about 55 mm over the withers when it holds its head high (a dog's neck crest; the wolf's
  summer neck is +6 mm).
- **Muybridge's plate 707** (the dog's gallop) could not be opened; the run follows the reviewer's description.
- **The stray's loin** is 16% under the dog's (the reviewer asked 10–15%).
- **The game has no night yet:** the night pictures' moonlight is my choice.

## Questions for the owner (my recommendation first)

1. **Is the look of the wolf, the guard dog and the stray approved, before the rig?** I recommend yes, then the rig
   (32 bones) with the clips above.
2. **The wolf's coat.** I recommend the summer coat all year (built), the one that reads as the Arabian wolf.
   - Option: the winter coat (`wolf_summer_winter.jpg`) in December to February, done cheaply by scaling the neck and
     tail bones in the rig rather than a second mesh.
   - Option: the winter coat all year. It reads more like a northern wolf.
3. **The guard dog's type.** I recommend the local pariah or Bedouin dog (built: sandy with white, a male about 56 cm).
   No source names a breed for herders in the Kingdom; the one description of Arabian herders' dogs is this type.
   - Option: a large imported livestock guardian breed. No source for its use in the Kingdom was found.
   - Option: let the player choose a coat (more textures on the same mesh).
4. **The saluki (السلوقي)** is a question, not a build (see below). I recommend leaving hunting with salukis out of the
   game for now.
5. **The guard dog's collar.** I recommend keeping it: it marks the dog as the player's and gives a ring for a chain.
   Real practice was not found.

### The saluki: its place in Saudi hunting and the law

- **The hound of the tradition:** the Arab News article "The Bedouin's best friend" (January 2025) says the
  International Aseel Arabian Saluki Center in the Kingdom works to keep the breed from crossbreeding. Its president
  calls it a national symbol beside the falcon, the Arabian horse and the camel *(search)*. Before cars, falconers'
  main quarry was houbara, hares and stone-curlews (research [155]).
- **What the law allows:**
  - The hunting regulation names hunting dogs (السلق) as a traditional means (research [135], *search*).
  - Hunting with them is confirmed only in the dog zones of the licensed fenced estates (المحازات), whose game is
    hares, jerboas and the dhub (research [142]).
  - Saudipedia says the Northern Reserve for Sustainable Hunting (set up 2022, about 2,000 km²) is the only reserve
    where firearms, falcons and salukis are all allowed, by an NCW licence *(search)*.
  - This season's permits go to air-rifle holders and falconers (research [131]).
  - Outside the estates, hunting a hare is fined SAR 18,000 (research [139]).
- **Is hunting hares with salukis in open land allowed, and in what season:** not found. No permit route for it was
  found. The estates' own season for salukis was not found; the general season runs 1 September to 31 January
  (research [127]–[129]).
- **The contests:** saluki beauty and lure contests were found in the Emirates (the Arabian Saluki Center in Abu
  Dhabi, its 2026–27 championship *(search)*), but none in the Kingdom.
- **Recommendation:** leave the saluki out for now. If the owner wants it later, the only real place for it is an
  outing to a licensed estate's dog zone, with its licence and fee, after falconry is built. Hares hunted with
  salukis in open land would teach a fine of SAR 18,000.

## Not done yet

- The rig and the clips (the next task).
- The danger's rules in the engine; buying and feeding the guard dog; the fence (a later task).
- A third, far level (about 300 triangles) for beyond 30 m: cheap if wanted.
- Putting the animals into the game page.

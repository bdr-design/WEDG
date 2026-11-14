# The birds of the hunt, built by code

**Status: awaiting the owner's approval of the look.** The rig and clips wait for it (the proxy's answer, batch 2
of `docs/agents/proxy_decisions.md`). The known gaps are listed beside the pictures, in `design/birds/README.md`.

The owner asked on 13 Nov 2026 for the hunt's animals to be made now and shown to him («ابي تدخل الحيوانات الان
وتعرضها علي كذالك موسم القنيص»). Falconry comes first in the hunting design (`docs/proposals/gdd_hunting_section.md`,
`docs/proposals/hunting.md`, `docs/research-realism.md` section 8). These scripts build its birds and the falconer's
gear in Blender's Python, at their real sizes:

- the saker falcon (الصقر الحر, *Falco cherrug*), a first-year female (فرخ): hooded on her perch, hooded on the fist
  (her jesses held in the falconer's fist), unhooded and alert, and in flight;
- the houbara (الحبارى, MacQueen's bustard, *Chlamydotis macqueenii*), a male, standing alert and in flight;
- the stone-curlew (الكروان, *Burhinus oedicnemus*: research source [140] names the Eurasian stone-curlew), standing
  alert and in flight;
- the hood (البرقع) and jesses (السبوق) on the falcon, the block perch (الوكر) with its leash (المرسل), and the cuff
  (الدس).

No mesh or picture is downloaded. Every shape comes from the numbers below and every colour is painted with numpy
from the descriptions below. Photographs were only looked at, never used: the Commons photographs the reviewer traced
for its outline checks, named in the checks section.

There is no rig yet. The poses are separate meshes. The rig comes after the owner approves the look (plan at the
end).

## Files

| File | What | Triangles (parts) | Draws |
|---|---|---|---|
| `assets_src/birds/saker_hooded.glb` | perched, hooded, jessed, the swivel ready for the leash | 5,352 body + 724 hood + 560 jesses = 6,636 | 3 |
| `saker_fist.glb` | the same bird hooded on the fist, her jesses running into the falconer's grip | 5,352 + 724 + 400 = 6,476 | 3 |
| `saker_alert.glb` | perched, unhooded, alert | 5,896 + 560 jesses = 6,456 | 2 |
| `saker_flight.glb` | cast off: wings spread, the feet clenched (toes and talons curled in) and drawn up into the belly and undertail feathers, out of sight; only the jesses trail | 6,232 + 400 = 6,632 | 2 |
| `saker_*_lod1.glb` | the far model of each pose: no jesses, brow, tooth or eye ring (under a pixel at tens of metres) | 1,334 (hooded, with the hood) / 1,204 / 1,300 | 1–2 |
| `houbara_alert.glb`, `houbara_flight.glb` | | 5,428 / 6,484 | 1 |
| `houbara_*_lod1.glb` | | 1,084 / 1,468 | 1 |
| `curlew_alert.glb`, `curlew_flight.glb` | | 5,084 / 5,420 | 1 |
| `curlew_*_lod1.glb` | | 1,120 / 1,216 | 1 |
| `wakr.glb` | the perch and the leash | 1,228 + 168 = 1,396 | 2 |
| `dass.glb` | the cuff, its front rounded closed over the fist | 944 | 1 |
| `wakr_lod1.glb`, `dass_lod1.glb` | | 436 / 160 | 2 / 1 |

Each bird file has one material, one-sided, and one texture pair: colour plus occlusion/roughness. The pair is 512 px
for the close model and 256 px for the far one. That is 2.67 MiB uncompressed with mipmaps (0.67 MiB far), counted as
ADR 0005 counts it, and about a quarter of that compressed. The gear has its own 256 px pair (128 px far). Every piece
is a closed surface, wound outward (the build refuses a piece that is open or has a face wound inward, so nothing shows
through when drawn one-sided as the game draws it), the texture coordinates stay inside their blocks, and the same code writes the same GLB files
byte for byte. The exporter's triangle order is settled after writing, as in `tool/weapon3d/akm.py`. I checked this
by building twice and comparing checksums: all 19 files were identical.

The pictures are in `design/birds/` (JPEG): each bird and pose from the side, orthographic, with a centimetre ruler;
a three-quarter view; a close view of the head (standing poses); for flight, the views straight from below (head up the
picture: the underwing as a falconer sees it) and from above (with a ruler across the span); `birds_scale.jpg`, everything beside the player's figure; and `birds_fist.jpg`,
the hooded falcon on the cuff of the figure's left hand. The lighting uses AgX tone mapping and a soft key, so white
and cream plumage keeps its detail.

## Weight on the phone

The budget is ADR 0005's: 200 draws and 400k triangles a frame with shadows, and 80 MiB of compressed textures.

- **What a hunt scene shows:** one falcon close (on the fist, the perch or just cast off), at most a few quarry, and
  the falcon far off while it chases.
  - Close falcon with hood and jesses, the cuff and a perch: 6.6k + 0.9k + 1.4k = about 9k triangles, 6 draws
    (12 with the shadow pass).
  - Three quarry far off: 3 × 1.1–1.5k triangles, 3 draws.
  - All together that is about 2–3% of the triangle budget, and 4 texture pairs (about 11 MiB uncompressed, about 3
    MiB compressed).
- **Why the close model is 5–7k and not the 2–3k that `docs/proposals/hunting.md` estimated:**
  - The falcon on the fist is seen from one or two metres, beside the player.
  - Its silhouette (the hooked beak, the eye's ring, four toes with curved talons, the trousers, the primaries over
    the tail, the brow over the eye and the tomial tooth) takes the triangles: the toes and talons alone are about
    1,200.
  - Skinning one 6k mesh is cheap next to the camels' 8–40k.
- **A 1024 px pair for the falcon** (10.7 MiB uncompressed) would sharpen the head and feather fringes in the close
  view: texture memory spent for looks, so the owner's decision (question 4).

## The saker (a female in her first year)

**Which bird.** The female is the larger sex and the one flown. She is built in her first year (فرخ), the age class
of the passage birds trapped on migration and sold at the National Falcon Centre's autumn auction. Both فرخ and
قرناس (over a year) have their own classes in the ملواح and مزاين (research [169], [172]). A young saker's bare parts
(cere, eye ring, feet) are bluish grey. She is darker and more heavily streaked than an adult (HBW via Wikipedia: young
birds "darker and more heavily streaked"; field guides in search summaries: juveniles have "bluish to greyish (not
clear yellow) feet, cere and orbital ring").

**What she shows as a فرخ** (and what the pictures show): heavy, long dark-brown streaks below, broadest and merging
on the flanks and trousers, narrower up the breast, thin on the throat; plain dark brown upperparts, each feather with
only a narrow pale buff edge; a buff-brown crown densely streaked dark, buff cheeks finely streaked, a dark streak
behind the eye and a thin moustache; dark underwing coverts against paler barred flight feathers.

**What changes for an adult (قرناس):** all on the texture, not the mesh.
- Cere, eye ring and feet turn yellow.
- The underparts become whiter, with smaller, rounder drop spots, still heaviest on the flanks and trousers.
- The upperparts become paler brown, each feather edged and barred rufous-buff.
- The crown becomes paler and the moustache stays thin.

That is a second texture on the same mesh, cheap to add: question 2.

### Dimensions

Millimetres and grams.
- **Sources:** what is marked *(opened)* was read in the page's text (the reviewer's fetched copy of the English
  Wikipedia page, which cites HBW). What is marked *(search)* is known only from a search summary: no page could be
  opened from this machine, because every host was refused. What is marked *(reviewer)* is the reviewer's measurement
  on a Commons photograph.
- **Model column:** the model figures are measured on the files by `build.py` and by the reviewer's `bird_check.py`.

| What | Real | Source | Model |
|---|---|---|---|
| Length, bill to tail | 45–57 cm species; female the upper part | HBW (Orta et al. 2019) via en.wikipedia *(opened)*; female ~56 cm, Cascades Raptor Center *(search)* | 519 (flight pose) |
| Wingspan | 97–126 cm species; females 120–130 | HBW via en.wikipedia *(opened)*; Animal Diversity Web *(search)* | 1,200 (1,191 with the wings' lift) |
| Weight (for the record) | female 970–1,300 g, male 730–990 | HBW via en.wikipedia *(opened)*; sakerlife3.mme.hu *(search)* | – |
| Wing length (wrist to tip) | female 390–412 | ELA Foundation fact file 14 *(search)* | 402 |
| Tail | about 214–233 (larger column) | falcons.co.uk table after Cramp & Simmons 1980 *(search; its columns unlabelled)* | 225 from its root, 205 showing |
| Folded wing tips short of the tail tip | about 70 (a falconer tells a saker from a peregrine by it) | reviewer *(Commons photographs; rough)* | 70 |
| Height perched, crown above the perch top | about 320–450 | reviewer *(photo, rough)* | 339 hooded, 334 alert (441–443 from tail tip to crown) |
| Tarsus | not found | – | 57 *(from proportion: a game choice)* |
| Rule for the ملواح | a saker must span at least 16 inches (406 mm, likely the wing) | research [169] *(search)* | – |

Sexes: the male is about a third smaller (the tiercel). Its figures are above; it is not built.

### Plumage, by mark

| Mark | Where | From |
|---|---|---|
| Plain dark brown upperparts, each feather with only a narrow pale buff edge | back, scapulars, coverts | young sakers "darker", HBW *(opened)*; field guides *(search)* |
| Buff-cream underparts with heavy, long dark-brown streaks of varied length and slant, merging on the flanks and trousers, narrower up the breast, thin on the throat | underparts, trousers | the same; young birds "more heavily streaked" |
| Buff-brown crown densely streaked dark; buff cheeks finely streaked; a faint pale line over the eye | head | the same |
| Dark streak behind the eye; a thin moustache (a bold one reads as a peregrine) | face | the same; reviewer's guidance |
| Dark primaries, each darker at its overlapped edge, with narrow pale tips staggered on the folded wing | wing | the same |
| Tail brown with pale oval spots in bars, the central pair plainer, a pale tip; paler and barred below | tail | the same |
| Dark, pale-spotted underwing coverts against paler, barred flight feathers with a thin dusky trailing edge | underwing in flight | a saker field mark *(search; reviewer)* |
| Dark brown iris (never yellow) in a ring of bare skin; a brow ridge over the eye (the falcon's frown); both left off under the hood | eye | the same |
| Bluish-grey cere, eye ring and feet; a short, deep, strongly hooked bluish horn bill with a black hook and the tomial tooth; long curved black talons | bare parts | juvenile, the same |

The sakers of the Kingdom's markets come in shades (أشقر، أحمر، أدهم). This one is a mid brown bird. The other shades
are colour changes on the same texture.

## The houbara (a male)

| What | Real | Source | Model |
|---|---|---|---|
| Length | about 65 cm | en.wikipedia 'Asian houbara' *(opened)*; 70 cm oiseaux.net *(search)* | 655 (flight) |
| Wingspan | about 140 cm | en.wikipedia *(opened)*; 170 cm on kuwaitbirds.org *(search, an outlier)* | 1,424 |
| Weight (for the record) | 1.2–3.2 kg species; male about 1.96 kg, female 1.15 kg (a database mirror, species not certain) | oiseaux.net; worldspecies mirror *(search)* | – |
| Sexes | male 9–15% larger on most measures | Jarrett & Warren 1999 via en.wikipedia *(opened)*; Alonso et al. 2023, *Ardeola* 70 *(search; its tables not seen)* | the male |
| Standing height, alert | about 340–480 | reviewer *(Commons photo scaled by the 65 cm length)* | 432 |
| Wing length (wrist to tip), tarsus | not found | – | 440, 98 *(proportion: game choices)* |

An African houbara fact sheet gives 73 cm (male) and 66 cm (female) "tall" (bilderreich.de, *(search)*). That matches
a length rather than a standing height, so it was not used.

**Plumage** (en.wikipedia *(opened)*: "brown above and white below, with black stripes down the sides of the neck... In
flight... large areas of black and brown on the flight feathers and a white patch at the base of the primaries. From
below the wing is mostly white with a black trailing edge"; the crest "long and curved feathers which are white or
black with white bases"):
- **Upperparts:** sandy buff, densely vermiculated dark brown, with dark arrowhead marks on the larger feathers.
- **Neck and breast:** an ash-grey fore-neck and breast.
- **The neck's stripe:** black, down each side of the neck. Its lower end breaks into separate long feathers, with
  white plumes below.
- **Belly:** white.
- **Crest:** a tuft of five white feathers with black tips, lying back on the crown.
- **Wing:** black primaries with the white patch at their bases (spread, in flight); at rest the primaries are mostly
  hidden under the tertials, only their tips showing over the broad, rounded tail.
- **Tail:** sandy, with three slate bars and a white tip.
- **Bare parts:** a pale yellow iris, a grey-horn bill and pale yellowish-grey legs.
- **Toes:** three, with **no hind toe**. Bustards have none.

## The stone-curlew

| What | Real | Source | Model |
|---|---|---|---|
| Length | 38–46 cm (40–44, Beaman & Madge 2011) | en.wikipedia *(opened)*; madeirabirds.com *(search)* | 425 (flight) |
| Wingspan | 76–88 cm (77–85) | the same | 820 |
| Weight (for the record) | 290–535 g (370–450, Hume 2002) | the same | – |
| Standing height | about 290–360 | reviewer *(Commons photo, two scalings)* | 292 (the legs shortened and the body deepened to the photos' proportions, the head held higher) |
| Wing length, tarsus | not found | – | 246, 82 *(proportion: game choices)* |

Sexes: alike.

**Plumage** (en.wikipedia *(opened)*: "a strong yellow and black beak, large yellow eyes... cryptic plumage... striking
in flight, with black and white wing markings"; search summaries: sandy brown streaked dark, a white bar on the folded
wing, pale yellow legs, the thick "knees"):
- **Upperparts:** sandy brown, every feather with a dark shaft streak.
- **Underparts:** the breast buff and finely streaked, the belly white.
- **Face:** a white stripe under the eye and a pale one above it, with a dark stripe between them; the throat white.
- **Folded wing:** a narrow black bar above a white bar, then grey-brown coverts.
- **Primaries:** black, with a small white spot.
- **Tail:** a wedge reaching about the wing tips, a black tip with white before it.
- **Eye:** a very large bright yellow iris with a small black pupil.
- **Bill:** short and stout, yellow at the base and black at the tip.
- **Legs:** long and pale yellow, with the visibly swollen intertarsal joint (the 'thick knee').
- **Toes:** three, with **no hind toe**.

The Arabian birds are of the pale southern subspecies (*saharae* / *harterti*: the subspecies is not confirmed by a
source read here).

## The gear, by its Saudi words

| Word | What it is | Model | From |
|---|---|---|---|
| البرقع | the hood: soft leather to the head's size, with an opening for the beak, to calm the bird | rounded tan leather over the head from the nape to the beak's root; dark edging, a stitched crown seam, a top knot, two braces at the back; its lower edge inside the throat's feathers | SPA 'ثماني أدوات تشكل حياة الصقر' and its reprints in al-Madina, almowaten, al-Jazirah *(search)*; Arab hoods with braces and a top knot or bead, ithra.com and other pages *(search)* |
| السبوق | the jesses: cords tied round the bird's legs, joined to the leash | braided cord (red and white: a game choice, they come in many colours) round each tarsus 27 mm above the sole, about 15 cm to a steel swivel | SPA *(search)*; Gulf jesses as nylon cords about 30 cm *(search, a UAE source)*; the reviewer: 15–20 cm each |
| المرسل | the leash from the jesses' swivel to the perch | a braided brown cord, slack, from the swivel to the perch's ring | research [155] *(search)*; 'mursil leash... midwar swivel' *(search, UAE)* |
| الوكر | the perch: a broad flat top on a stick pushed into the sand; an iron stake clad in wood, sometimes decorated | a 150 mm padded top (green artificial turf) on a turned wooden head and a clad stake 300 mm above the sand, two turned rings, a steel ring for the leash, an iron spike under the sand | ar.wikipedia صقارة *(opened)*; SPA *(search)*; a 150 mm turf-topped block perch, retail listing *(search)*; height 300 mm a game choice inside the reviewer's 25–60 cm |
| الدس | the cuff over the falconer's hand and wrist, to carry the falcon and keep the talons off (المنقلة is the word in the Emirates and Qatar) | a quilted, padded cloth cuff over the wrist and the fist (not a fingered glove), its bound edge closed round the wrist over the sleeve's end | SPA *(search)*; ar.wikipedia's caption 'منقلة (قفاز)' of Carl Raswan falconing in al-Jawf *(opened)*; the reviewer's description |

The falcon is carried on the **left** hand (Arab News 2019 *(search)*). In `birds_scale.jpg` the figure's left fist is
1.19 m above the ground and the falcon's feet are at 1.24 m. On the fist (`saker_fist.glb`) her toes and talons rest on the cuff's surface (from the cuff's own
sections)
and her jesses run down over the fist's front into the falconer's grip; the leash is not shown there.

The figure's forearm is turned level and its hand bone shortened for that picture only, so the fingers stay inside
the cuff. The fingers cannot curl yet (tool/char3d's known gap).

Research [155] also names the cage (القفص), the scales (الميزان) and the lure (الملواح). The cloth bag (المخلاة) and a
tracker are also part of the kit. None of them is built yet.

## From the saker to the other falcons

The festival's ملواح races الحر، الشاهين، الجير شاهين، الجير تبع، الجير بيور and القرموشة (research [169]); its مزاين
judges الحر and الجير بيور. Each would be the same code with new numbers and a new texture.

- **الشاهين (the peregrine; the Gulf's desert form is the paler 'red-naped' شاهين):**
  - Smaller: a female about 45–50 cm.
  - Its folded wing tips reach the tail's tip (about 7 cm farther than the saker's), and its tail is shorter.
  - Its head is darker: a black hood and a bold black moustache.
  - An adult is barred below; a young bird is streaked.
  - To build it: new body stations and wing rows, and a new atlas.
- **الجير (the gyrfalcon) and the جير-حر / جير-شاهين hybrids:**
  - Bigger and heavier: a female about 55–60 cm.
  - A broader wing and a deeper chest.
  - Its morphs (white, grey, dark) are textures.
  - The hybrids sit between their parents in size and pattern.

The figures above are from memory and were not checked against a source in this task.

**Recommended:** the game needs الحر first (built). Then the الجير بيور, because it is one of only two classes judged
in the مزاين, before الشاهين. That is the owner's choice (question 3).

## Named points

In the GLB, metres, under each file's root:
- **Every bird:**
  - `foot_l` / `foot_r`: the grip, under the toes' middle, on the support's surface.
  - `ankle_l` / `ankle_r`.
  - `tarsus_l` / `tarsus_r`: on the tarsus.
  - `wing_root_l` / `wing_root_r`: mirrored.
  - `tail_base`, `neck_base`, `head`, `beak_tip`.
  - Points with axes carry the bird's forward as X.
- **The saker also has:**
  - `hood`: inside the head, where the hood sits.
  - `jess_l` / `jess_r`: where the jesses tie, 27 mm above the sole.
  - `swivel`: where the leash clips on.
- **The perch:** `wakr_top` (the falcon's place), `wakr_ring`, `leash_swivel`, `ground`.
- **The cuff:** `dass_top` (the falcon's place), `hand_l` (the fist's middle, for the hand bone), `forearm`.

In millimetres in the build:
- The bird faces +X, with Z up and Y to its left.
- A perched or standing bird's origin is the support's surface between its feet.
- A flying bird's origin is its tail's base.

## How it is built

- `common.py`: lofted pieces that carry their own texture places, the atlas painter, the files and the studio.
- `bird.py`: one bird from its numbers.
  - The body (tail base to forehead) is lofted along a centre line that the pose bends: the torso's pitch, then the
    neck and the head.
  - The beak (with the cere and lower mandible), the eyes (with a bare ring if the species has one).
  - The wings: folded on the body, or spread with an airfoil section and camber, with the bustard's slotted primaries.
  - The tail, and the legs solved from the knee to the feet's places.
  - The toes and talons (four toes for the falcon, three for the others).
- `saker.py`, `quarry.py`: the species' numbers and poses.
- `paint.py`, `paint_quarry.py`: the plumage, painted by marks.
  - Feathers in rows with fringes, dark middles and shaft streaks.
  - The saker's tear-drop streaks, the houbara's vermiculation and arrowheads, the curlew's wing panel.
  - The face marks, placed from the eye's place on the body.
- `gear.py`: the perch, the leash and the cuff.
- `scene.py`: the scale picture.
- `build.py`: runs everything, writes the files and pictures, and prints the measures.

```
python build.py OUT                      # every GLB, with triangles, sizes and the model's measures
python build.py OUT saker quick          # quick pictures of one species
python build.py OUT gear                 # the perch and the cuff (needed under the perched pictures)
python build.py OUT saker,houbara,curlew,scale render    # the full picture set
```

Blender is the `bpy` module (the project's `blendenv`). The GLB files are copied to `assets_src/birds/`, and the
pictures to `design/birds/`.

## The rig and clips (task T17)

**Status: awaiting the owner's approval of the motion.** He approved the look on 14 Nov 2026 and asked for the bones
and the motion (the flight, the landing, the catch). `rig.py` (the saker) and `rig_quarry.py` (the houbara and the
stone-curlew) build them. The static GLBs above stay as the approved look; the rigged files are new:

| File | Meshes (triangles) | Bones | Clips |
|---|---|---|---|
| `saker_rig.glb` | folded 5,896, spread 6,232, hood 724, jesses 580 | 49 | 12 |
| `saker_rig_far.glb` | folded 1,204, spread 1,300 (the far meshes of T11, 256 px) | 49 | the same 12 |
| `houbara_rig.glb` / `_far` | folded 5,428 / 1,084, spread 6,484 / 1,468 | 36 | 5 |
| `curlew_rig.glb` / `_far` | folded 5,084 / 1,120, spread 5,420 / 1,216 | 34 | 5 |

**One skeleton, two meshes, swapped where their outlines match.** Each bird is built in a rest pose (the saker with
the body level and the legs down; the quarry in their approved alert stance), once with the wings folded and once
spread. Both meshes are skinned to the same skeleton. Folding the spread wing all the way by bones was tried: past
about two thirds the feathers cross the body and the hand pokes out past the tail, so the close views need the
folded mesh. So the folded wing has two bones (the shoulder and the primaries) and opens a little, the spread wing
folds by its three bones, and the two poses were searched so their silhouettes match; the swap happens in that
frame. Measured by the build (the lower of the side and three-quarter overlap, in the frames before and after):

| Swap | Overlap |
|---|---|
| saker `cast_off`, frame 14 | 0.911 |
| saker `land_cuff` / `land_perch`, frame 38 | 0.893 / 0.891 |
| stone-curlew `take_off`, frame 14 | 0.909 |
| houbara `take_off` and `escape` | 0.864 (its broad, slotted wing folds least well; the closest the search found) |

**The swap is in the file.** Each body mesh has a morph target `hidden` that gathers its vertices to one point
inside the body; every clip keys it (1 hidden, 0 shown), so a mixer plays the swap with no game code. The hood is
hidden the same way by its bone's scale (0). **Convention for the page** (a later task): a mesh whose morph
`hidden` is at 1, and the hood when the bone `hood` is scaled to 0, are set not visible, so they cost no draw.

**The saker's bones (49)** and why:

| Bones | Count | Why |
|---|---|---|
| root, body | 2 | where she stands; the torso's pitch, roll, bob |
| neck1, neck2, head | 3 | keep the head level as the body tilts; the head looks round |
| hood | 1 | the hood lifted off and set on (scale 0: not shown) |
| tail, tail.L, tail.R | 3 | the tail lifts and drops; its two halves fan out (the flare, the mantle) |
| fold, fold_tip (each side) | 4 | the folded mesh's wing opens at the shoulder and its primaries swing out to meet the swap |
| wing_up, wing_fore, wing_hand (each side) | 6 | the beat at the shoulder; the flex at the elbow and wrist on the upstroke; the hand's twist |
| shank, tarsus (each side) | 4 | the legs: reach, push, tuck; the foot planted |
| two per toe, four toes (each side) | 16 | each toe lies on the rounded cuff its own way, its talon hooked in |
| five per jess (each side) | 10 | the jesses sag between the anklet and the fist, swing and trail as soft cords |

The houbara has a three-bone neck and a crest bone, the stone-curlew a two-bone neck; both have three toes (no
hind toe) and no hood or jesses. At most two bones a vertex.

**The clips** (30 frames a second; looping clips repeat their first frame at the end):

| Bird | Clip | Frames | Reference |
|---|---|---|---|
| saker | `perch_idle` (loop) | 120 | small shifts of weight, a look to each side, a flick of the tail: game choice |
| saker | `rouse` | 36 | the feathers raised and shaken (about half a second at 7 shakes a second): game choice |
| saker | `hood_off`, `hood_on` | 30 each | on the fist; the hood lifted (the hand not drawn), she looks round |
| saker | `cast_off` | 41 | the lean and crouch, the wings opening to the swap at 14, the push with the legs, the feet off the fist at 20, trailing two frames, drawn up by 24; she drops about 190 mm below the fist in her first beats, then climbs (the drop and the speeds are game choices) |
| saker | `flight` (loop) | 14 | two beats of 7 frames: 4.3 Hz, inside the 4.3–4.8 Hz Pennycuick's (1996) formula predicts; the wing flexes at the elbow and wrist on the upstroke (shoulder to tip 73% of its spread length), the hand twists; the body bobs against the beat |
| saker | `glide` (loop) | 60 | the wings held, a slow roll |
| saker | `stoop` | 40 | the spread mesh's wings drawn in by its bones to the tightest outline that still reads right, the body tipped 55° down, the head in line; no swap here (the folded mesh matched at best 0.69 at this angle); `bind` starts from the same outline |
| saker | `bind` | 24 | thrown up from the dive, the feet struck forward, closing at frame 10 (on the quarry), heavy beats |
| saker | `mantle` (loop) | 60 | on the ground over the kill: the wings spread and drooped, the tail fanned, the head down, looking up |
| saker | `land_cuff`, `land_perch` | 46 each | in low, about 350 mm under the fist, a swing up, the flare (the tail fanned, the wings forward braking), contact at 28, the wings folded along the back to the swap at 38, the perched pose at 45; the approach is a game choice |
| houbara | `stand` (loop) | 120 | alert, one foot back, the head turning, the crest lifting |
| houbara | `run` (loop) | 16 | low and level, the neck forward; a stride every 8 frames at 3 m/s (game choice: no measured speed found) |
| houbara | `take_off` | 40 | two strides, a crouch, the spring, deep beats, the legs trailing behind the body with the feet closed |
| houbara | `flight` (loop) | 14 | 7-frame beats (4.3 Hz, inside the 4.2–4.7 Hz predicted), the neck stretched |
| houbara | `escape` | 62 | it runs first, jinking, and flies when pressed (Encyclopaedia Iranica, from a search summary; the jinks are a game choice) |
| stone-curlew | `stand` (loop) | 120 | alert, one foot back, the head turning |
| stone-curlew | `run` (loop) | 12 | a stride every 6 frames at 2 m/s (game choice) |
| stone-curlew | `crouch` | 60 | down flat, the neck along the ground, held still, up again (crouch, freeze, then run: search summaries) |
| stone-curlew | `take_off` | 40 | as the houbara's |
| stone-curlew | `flight` (loop) | 10 | 5-frame beats (6 Hz, inside the 5.9–7.4 Hz predicted) |

**The approved perched pose.** The perched frames use the neck, head and tail turns fitted to the approved
`saker_fist.glb`: silhouette overlap 0.89 from the side and 0.96 from the front, in place (the toes, gripping, and
the tarsus differ most).

**Measured** (by `rig.py OUT saker measure`, `rig_quarry.py OUT <bird> measure`, and the reviewer's own tools):
- A planted foot stays within 0.00 mm of its place (saker, every clip on the cuff, perch or ground), within 0.56
  mm in the houbara's run.
- Toes on the cuff: each toe is laid joint by joint on the exported cuff's own top (a millimetre heightmap of its
  faces), set in the world so it stays put while the leg moves. By the reviewer's method (ray parity and exact
  distance against the exported `dass.glb`): the deepest toe vertex 1.2 mm inside, in any sampled frame of
  `cast_off`, `land_cuff` and `hood_off`; 0.0 mm on the perch and the ground.
- Feet out of sight in flight: no toe or tarsus vertex outside the body in any saker frame meant drawn up
  (`flight`, `glide`, `stoop`, `cast_off` from 24, the landings' glide). The houbara and the stone-curlew fly with
  their legs trailing and their feet closed, as they are seen to (from field guides, not opened).
- Skin stretch (the shown mesh): in `flight` the triangles' area stays between 0.07 and 3.7 of rest (16 triangles
  beyond 0.25–4 at the wrist on the upstroke); near the swaps, for one to four frames, down to 0.007 at the tightly
  folded wrist.
- Clip data: 401 KB for the saker's twelve clips (keys thinned within 0.0002 of the quaternion and 0.01 mm, so
  the chain from the root to a talon stays within a millimetre, then the exporter's lossless reduction); the far
  file carries the same clips.
- The same code writes the same files twice.

**Weight on the phone.** A hunting scene: one falcon close (one body mesh drawn at a time: 5.9–6.2k triangles, plus
the hood and jesses 1.3k: 3 draws), a few quarry far (1.1–1.5k each, one draw each, skinned on the same skeletons
as near), and the trapping pigeon (to come). Skinning one bird of 34–49 bones and up to 6.5k vertices is far below a
herd camel's cost; the far level is skinned too (its clips are the near ones), so no clip texture is needed for
these few birds. Textures unchanged (512 px near, 256 px far).

**Pictures** (`design/birds/motion/`, awaiting the owner's approval of the motion): for every clip a contact sheet
from the side and one three-quarter (`<bird>_<clip>_side.jpg`, `_tq.jpg`), the saker's feet on the cuff close,
and two small GIFs (the cast-off and the flight).

## What is unsure

- **Wing area and the flight silhouette.**
  - The model's wings are 0.183 m² (saker, aspect ratio 7.9 against about 7.5–8 for a large falcon), 0.236 m²
    (houbara) and 0.054 m² (stone-curlew), from planforms drawn in proportion and widened to the reviewer's
    photograph. No measured wing area was found.
  - The predicted wingbeats depend on these areas.
- **Overlaps with the reviewer's photo outlines:**
  - houbara 0.71, stone-curlew 0.53 (0.68 with the photo turned 25°), saker alert 0.52 (0.59 turned 10°), saker in
    flight 0.58;
  - most of the gap is pose: the photographed saker leans well forward (the reviewer withdrew the 0.80 mark for it:
    body depth over chord is 0.244 on the model against 0.25 on the photo, head over chord 0.21 on both), the flight
    photo is a braking bird with its tail fanned, the stone-curlew photo a hunched bird.
- **Not found, so made from proportion (game choices):** tarsus and wing lengths of the houbara and the stone-curlew;
  the saker's tarsus; the hood's, the cuff's and the perch's sizes beyond the 150 mm top; the jesses' colours.
- **No page could be opened from this machine.** Everything is from the text of the reviewer's fetched Wikipedia pages
  or from search summaries, marked as such.

## Questions for the owner

The proxy answered these provisionally (batch 2 of `docs/agents/proxy_decisions.md`); they stand until the owner
says otherwise.

1. **Is the look approved?** Waits for the owner. Until then: no rig and no clips; the models and pictures are on
   the session branch marked as awaiting his approval. My recommendation for the rig, when it comes: a folded and a
   spread wing mesh swapped at take-off and landing.
2. **The saker's age.** Answered provisionally: the first-year bird (فرخ) as the player's first falcon (a farm-bred
   saker of the year at the August auction); the adult (قرناس) later as a second texture on the same mesh.
3. **Which falcon next.** Answered provisionally: the peregrine of the year (الشاهين البحري فرخ), because the
   trapping research found the trapping auction sells only that bird; started only after he approves the saker. The
   gyr (الجير) later, as a real مزاين class. (My recommendation had been the الجير بيور first.)
4. **512 or 1024 px for the falcon on the fist.** Not decided: 512 px stays until he tries it on his phone.

## Not done yet

- The rig and the clips (next task).
- The adult saker's texture, the other falcons, the air rifle's quarry (later, by the brief).
- The cage, scales, lure, bag and tracker.
- Putting the birds into the game page.

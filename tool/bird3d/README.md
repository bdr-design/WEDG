# The birds of the hunt, built by code

The owner asked on 13 Nov 2026 for the hunt's animals to be made now and shown to him («ابي تدخل الحيوانات الان
وتعرضها علي كذالك موسم القنيص»). Falconry comes first in the hunting design (`docs/proposals/gdd_hunting_section.md`,
`docs/proposals/hunting.md`, `docs/research-realism.md` section 8). These scripts build its birds and the falconer's
gear in Blender's Python, at their real sizes:

- the saker falcon (الصقر الحر, *Falco cherrug*), a first-year female (فرخ): hooded on her perch or the fist, unhooded
  and alert, and in flight;
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
| `assets_src/birds/saker_hooded.glb` | perched, hooded, jessed | 5,628 body + 564 hood + 560 jesses = 6,752 | 3 |
| `saker_alert.glb` | perched, unhooded, alert | 5,628 + 560 jesses = 6,188 | 2 |
| `saker_flight.glb` | cast off: wings spread, legs drawn up, jesses trailing | 5,964 + 400 = 6,364 | 2 |
| `saker_*_lod1.glb` | the far model of each pose: no jesses (a 2 mm cord is under a pixel at tens of metres) | 1,456 (hooded, with the hood) / 1,332 / 1,428 | 1–2 |
| `houbara_alert.glb`, `houbara_flight.glb` | | 4,996 / 6,052 | 1 |
| `houbara_*_lod1.glb` | | 1,084 / 1,468 | 1 |
| `curlew_alert.glb`, `curlew_flight.glb` | | 5,084 / 5,420 | 1 |
| `curlew_*_lod1.glb` | | 1,120 / 1,216 | 1 |
| `wakr.glb` | the perch and the leash | 1,256 + 168 = 1,424 | 2 |
| `dass.glb` | the cuff | 864 | 1 |
| `wakr_lod1.glb`, `dass_lod1.glb` | | 448 / 140 | 2 / 1 |

Each bird file has one material, one-sided, and one texture pair: colour plus occlusion/roughness. The pair is 512 px
for the close model and 256 px for the far one. That is 2.67 MiB uncompressed with mipmaps (0.67 MiB far), counted as
ADR 0005 counts it, and about a quarter of that compressed. The gear has its own 256 px pair (128 px far). Every piece
is a closed surface, the texture coordinates stay inside their blocks, and the same code writes the same GLB files
byte for byte. The exporter's triangle order is settled after writing, as in `tool/weapon3d/akm.py`. I checked this
by building twice and comparing checksums: all 18 files were identical.

The pictures are in `design/birds/` (JPEG): each bird and pose from the side, orthographic, with a centimetre ruler;
a three-quarter view; a close view of the head (standing poses); for flight, the views from below and behind and from
above (with a ruler across the span); `birds_scale.jpg`, everything beside the player's figure; and `birds_fist.jpg`,
the hooded falcon on the cuff of the figure's left hand. The lighting uses AgX tone mapping and a soft key, so white
and cream plumage keeps its detail.

## Weight on the phone

The budget is ADR 0005's: 200 draws and 400k triangles a frame with shadows, and 80 MiB of compressed textures.

- **What a hunt scene shows:** one falcon close (on the fist, the perch or just cast off), at most a few quarry, and
  the falcon far off while it chases.
  - Close falcon with hood and jesses, the cuff and a perch: 6.8k + 0.9k + 1.4k = about 9k triangles, 6 draws (12
    with the shadow pass).
  - Three quarry far off: 3 × 1.1–1.5k triangles, 3 draws.
  - All together that is about 2–3% of the triangle budget, and 4 texture pairs (about 11 MiB uncompressed, about 3
    MiB compressed).
- **Why the close model is 5–6k and not the 2–3k that `docs/proposals/hunting.md` estimated:**
  - The falcon on the fist is seen from one or two metres, beside the player.
  - Its silhouette (the hooked beak, the eye's ring, four toes with curved talons, the trousers, the primaries over
    the tail) takes the triangles: the toes and talons alone are about 1,200.
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
| Height perched, crown above the perch top | about 320–450 | reviewer *(photo, rough)* | 340 hooded, 334 alert (441 from tail tip to crown) |
| Tarsus | not found | – | 57 *(from proportion: a game choice)* |
| Rule for the ملواح | a saker must span at least 16 inches (406 mm, likely the wing) | research [169] *(search)* | – |

Sexes: the male is about a third smaller (the tiercel). Its figures are above; it is not built.

### Plumage, by mark

| Mark | Where | From |
|---|---|---|
| Dark brown upperparts, each feather with a darker middle and a narrow rufous-buff fringe | back, scapulars, coverts | young sakers "darker", HBW *(opened)*; field guides *(search)* |
| Cream-buff underparts with bold dark-brown tear-drop streaks, heaviest on the flanks and lower breast, finer up the breast, none on the throat | underparts, trousers | the same; young birds "heavily streaked" |
| Pale buff, finely streaked crown; cream cheeks; unmarked throat | head | the same |
| Dark streak behind the eye; a thin, faint moustache (a bold one reads as a peregrine) | face | the same; reviewer's guidance |
| Dark primaries with narrow pale tips, staggered on the folded wing | wing | the same |
| Tail brown with pale oval spots in bars, the central pair plainer, a pale tip; paler and barred below | tail | the same |
| Dark underwing coverts against paler, barred flight feathers with a dusky trailing edge | underwing in flight | a saker field mark *(search; reviewer)* |
| Dark brown iris (never yellow) | eye | the same |
| Bluish-grey cere, eye ring and feet; bluish horn bill with a black hook; black talons | bare parts | juvenile, the same |

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
- **Upperparts:** sandy buff, finely vermiculated dark brown, with dark arrowhead marks on the larger feathers.
- **Neck and breast:** a pale ash-grey fore-neck and upper breast.
- **The neck's stripe:** black, down each side of the neck. Its lower end breaks into separate long feathers, with
  white plumes below.
- **Belly:** white.
- **Crest:** white feathers with black tips, lying back on the crown.
- **Wing:** black primaries, with the white patch at their bases.
- **Tail:** sandy, with three slate bars and a white tip.
- **Bare parts:** a pale yellow iris, a grey-horn bill and pale yellowish-grey legs.
- **Toes:** three, with **no hind toe**. Bustards have none.

## The stone-curlew

| What | Real | Source | Model |
|---|---|---|---|
| Length | 38–46 cm (40–44, Beaman & Madge 2011) | en.wikipedia *(opened)*; madeirabirds.com *(search)* | 425 (flight) |
| Wingspan | 76–88 cm (77–85) | the same | 820 |
| Weight (for the record) | 290–535 g (370–450, Hume 2002) | the same | – |
| Standing height | about 290–360 | reviewer *(Commons photo, two scalings)* | 319 |
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
- **Tail:** a black tip, with white before it.
- **Eye:** a very large bright yellow iris.
- **Bill:** short and stout, yellow at the base and black at the tip.
- **Legs:** long and pale yellow, with the thick intertarsal joint.
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
| الدس | the cuff over the falconer's hand and wrist, to carry the falcon and keep the talons off (المنقلة is the word in the Emirates and Qatar) | a quilted, padded cloth cuff from mid forearm over the wrist and the fist (not a fingered glove), its edge bound in leather | SPA *(search)*; ar.wikipedia's caption 'منقلة (قفاز)' of Carl Raswan falconing in al-Jawf *(opened)*; the reviewer's description |

The falcon is carried on the **left** hand (Arab News 2019 *(search)*). In `birds_scale.jpg` the figure's left fist is
1.19 m above the ground and the falcon's feet are at 1.24 m.

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

## The rig and clips to come (not built)

- **Bones:** about 30 a bird.
  - Body 3, neck 3, head 1, tail 2 with a fan, each wing 5 (humerus, forearm, hand, two primary groups), each leg 5
    (thigh, shank, tarsus, front toes, hind toe).
  - The hood and jesses ride on the head and tarsus bones.
- **Mesh cost:** one skinned 5–6k mesh close, and the 1.1–1.5k far mesh with a baked animation texture, as the camels
  will have (ADR 0005).
- **The folded wing and the spread wing are different meshes now.** For the rig there are two options:
  - fold the spread wing with the bones (one mesh, the feathers sliding under each other: harder to get clean);
  - swap a folded mesh for a spread one at take-off and landing, the way many games do.

  I recommend the swap. It costs one more mesh in memory, not in the frame.

| Clip | Real reference | Source |
|---|---|---|
| Saker perched idle, rouse (the feather shake), head turns | – | to film or watch: no figure found |
| Cast off from the fist, flapping flight | wingbeat about 4.5–5.0 Hz for a 0.97–1.3 kg female with this model's span and wing area (0.157 m²) | Pennycuick 1996, *J. Exp. Biol.* 199:1613, f = m^3/8 g^1/2 b^-23/24 S^-1/3 ρ^-3/8 (the paper found by search; its formula as he gives it, not opened) |
| Level flight to the lure | 400 m in 16.5–18.1 s, so 22–24 m/s (80–87 km/h) on average from the release | research [182], [183] *(search)* |
| Glide, stoop | a peregrine's stoop over 200 km/h; the saker hunts more by level chase than stoop | thewire.in, Lund University *(search)*; en.wikipedia saker *(opened)* |
| Bind to the quarry | – | to film or watch |
| Houbara run, take-off, flight | relies on running and flies when pressed; wingbeat about 4.3–4.7 Hz predicted for 1.8–2.4 kg; speeds not found | Encyclopaedia Iranica *(search)*; Pennycuick 1996 |
| Stone-curlew run, flight | wingbeat about 6–7 Hz predicted for 0.29–0.54 kg; speeds not found | Pennycuick 1996 |

## What is unsure

- **Wing area and the flight silhouette.**
  - The model's wings are 0.157 m² (saker), 0.228 m² (houbara) and 0.054 m² (stone-curlew), from planforms drawn in
    proportion. No measured wing area was found.
  - The reviewer's outline of a braking saker shows broader wings than the model's (silhouette overlap 0.56; the
    target was 0.70).
  - The predicted wingbeats depend on these areas.
- **Overlaps with the reviewer's photo outlines are below its targets:**
  - houbara 0.70 (target 0.80), saker alert 0.51 (0.58 with the photo turned 10°), stone-curlew 0.46;
  - part of the gap is pose: the photographed saker leans well forward, and the stone-curlew is a plump, hunched bird;
  - the stone-curlew overlay put the model upside down, so its figure is not a true one;
  - the bodies were deepened once toward the photos (saker +12% in the torso, stone-curlew +30%); more would need the
    photos' poses.
- **Not found, so made from proportion (game choices):** tarsus and wing lengths of the houbara and the stone-curlew;
  the saker's tarsus; the hood's, the cuff's and the perch's sizes beyond the 150 mm top; the jesses' colours.
- **No page could be opened from this machine.** Everything is from the text of the reviewer's fetched Wikipedia pages
  or from search summaries, marked as such.

## Not done yet

- The rig and the clips (next task).
- The adult saker's texture, the other falcons, the air rifle's quarry (later, by the brief).
- The cage, scales, lure, bag and tracker.
- Putting the birds into the game page.

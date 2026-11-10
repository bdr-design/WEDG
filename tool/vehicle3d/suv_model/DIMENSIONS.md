# SUV dimensions: spec sheet, real photo and the owner's photos

The owner asked for the dimensions to come from the sources and the photos (9 Nov 2026). The owner's four
orthographic photos are AI renders. This file records what the official sources say, what a real photo of the car
measures, where the owner's photos disagree, and what the model uses. `realframe.py` implements it.

## 1. Official figures

The trim that matches the owner's car (20-inch wheels, full chrome front) is the ZX.

| Figure | Value | Source |
|---|---|---|
| Length × width × height | 4985 × 1980 × 1925 mm (ZX) | toyota.jp spec sheet, via bestcarweb.jp |
| Wheelbase | 2850 mm | every source |
| Track (tread), front / rear | 1665 / 1665 mm (ZX); 1667 / 1668 (AU VX, GR Sport) | toyota.jp; Toyota AU via CarExpert |
| Minimum ground clearance | 225 mm (ZX); 235 mm official AU, 245 unladen | toyota.jp; Toyota AU |
| Tyres | 265/55R20 109V (ZX, VX, Sahara); 265/65R18 (GR Sport) | toyota.jp FAQ; Toyota AU |
| Wheel | 20 × 8J, 6 studs on a 139.7 mm circle (ZX) | toyota.jp FAQ table |
| Approach / departure angle | 32° / 25° (24° approach on the Sahara ZX) | Toyota AU via CarsGuide |
| Turning radius | 5.9 m (ZX) | toyota.jp |

Derived: a 265/55R20 tyre is 20 × 25.4 + 2 × 0.55 × 265 = **799.5 mm** across.

Notes on the sources:
- The overall height of 1925 mm is the highest point of the car, which on the ZX is the top of the roof rails, not the
  roof panel. The real photo confirms it (section 2: rail tops 1.92 m, roof 1.86 m).
- The wheel is 8J wide in Toyota's own table. An aftermarket guide (autostw.com.au) says 8.5; Toyota's figure is used.
  toyota.jp could not be opened from the build session, so the table was read through a web search of
  `toyota.jp/pages/contents/faq/2.0/pdf/228/0196271.pdf`. The inset and the centre bore are not used by the model, and
  the sources disagree on them (the Toyota table reads as inset 60, aftermarket guides say about +55), so they are not
  recorded as facts here.
- Not published anywhere I could reach: overhangs, width with mirrors, window and pillar sizes, the rail and antenna
  sizes. Those come from the photos (sections 2 and 4).

Sources:
- https://toyota.jp/pages/contents/landcruiser300/004_p_001/pdf/landcruiser300_spec_202503.pdf (via https://bestcarweb.jp/feature/column/1339442)
- https://toyota.jp/pages/contents/faq/2.0/pdf/228/0196271.pdf (factory tyre and wheel table)
- https://www.carexpert.com.au/toyota/landcruiser/2025/dimensions
- https://www.carsguide.com.au/car-news/lc300-wading-depth-approach-and-departure-angles-towing-locking-diffs-and-tyre-specifics
- https://autostw.com.au/blogs/news/toyota-land-cruiser-300-tyre-size-guide-wheel-specs-pcd-centre-bore-torque-settings
- https://wheel-size.jp/size/lexus/lx/2024/ (the same 265/55R20 on an 8J × 20 wheel on the LX)

## 2. A real photo, measured

Wikimedia Commons, "Moscow, Toyota Land Cruiser ZX grey, Sept 2025 01.jpg" (1280 px copy in
`scratchpad/lc300_ref/real_016.jpg`). It is listed as a ZX, but it has the GR Sport front, GR Sport side steps and
18-inch 265/65R18 wheels; the body, doors, glass and rails are the same as the ZX. It is used to measure from, never
shown on the model.

Scales:
- Along the car: wheelbase 656.2 px = 2850 mm, so 4.343 mm/px.
- Up: the tyre gives 4.19 mm/px (hub to tyre top 95.6 px = the free radius, 0.401 m, of a 265/65R18). The heights
  below were read at 4.17, half a percent less, a rounding choice made before the tyre was measured: at 4.19 every
  height in the table is 0.5 % more (the rail tops read 1926 mm, the official 1925).
- The two scales differ because the photo is taken with about 15° of yaw (the tailgate shows):
  cos⁻¹(4.19 / 4.343) = 15.3°. A point that is nearer the camera than the hub cap therefore shifts along the car by
  0.27 × its depth; the arch lips (5 cm nearer, 14 mm) and the rails (about 27 px, an estimate from their depth) are
  corrected for it.
- Ground line: 671 px under the front hub and 683 px under the rear hub.

Distances behind the front hub, in mm. "Mapped" is the owner's photo after the x map of section 4:

| Feature | Owner's photo | Real photo | Owner − real | Mapped − real |
|---|---|---|---|---|
| Front door, front edge | 616 | 617 | −1 | −9 |
| Front handle, centre | 1536 | 1522 | +14 | −6 |
| B-pillar door seam | 1714 | 1692 | +22 | 0 (knot) |
| Rear handle, centre | 2594 | 2473 | +121 | +31 |
| Rear door, rear edge | 2844 | 2738 | +106 | −3 |
| Rear hub | 2969 | 2850 (spec) | +119 | 0 (knot) |
| Quarter glass, rear tip | 3491 | 3416 | +75 | +11 |
| Tail lamp, front edge | 3652 | 3616 | +36 | −11 |
| Tail | 4053 | 4048 (spec 4985 − 937) | +5 | 0 (knot) |

Heights above the ground, in mm (real photo at 4.17 mm/px):

| Feature | Owner's photo | Real photo / spec | Owner's photo, mapped |
|---|---|---|---|
| Hub (loaded) | 437 | 370 (88.4 px at 4.19) | 412 |
| Tyre diameter | 870 | 799.5 (spec, 265/55R20) | built at the spec size |
| Rim lip diameter | 588 | about 540 (20-inch) | built at 536 |
| Door-bottom shut line | 455 | 429 (102.8 px) | 429 (knot) |
| Window foot at the front door | 1340 | 1253 (300.5 px) | 1253 (knot) |
| Roof at the rail foot | 1938 | 1859 (445.8 px) | 1842 |
| Roof crown | 1955 to 1964 | about 1860 to 1870 | 1858 to 1867 |
| Rail tops | 2023 | 1925 (spec); 1917 on the photo (459.7 px) | 1925 (knot) |
| Wheel opening, top edge, front / rear | about 940 | 862 / 930 | built from the real photo |
| Flare top, front / rear | | 929 / 1007 | built from the real photo (model 929 / 1008 to 1010) |

## 3. What this says about the owner's photos

- From the nose to the B pillar they match the real car within about 2 cm.
- Behind the B pillar, the rear wheel, the rear door's rear edge and the rear handle are about 115 mm too far back
  (photo wheelbase 2969 mm, spec 2850 mm). The tail is in the right place, so the rear overhang is about 115 mm too
  short.
- The wheels are 9 % too big: the tyre is 870 mm across, against 799.5 mm for the real 265/55R20 (870 / 799.5 =
  1.088), so they look like 22-inch wheels. Said the other way round, the model's real-size tyres are 8 % smaller
  than the photo's. The hub is 67 mm too high (437 against 370).
- The whole car is drawn about 5 % too tall: the rails top out at 2023 mm, against the official 1925 mm.
- Widths: views.json scaled the front, rear and top photos by assuming a 2.2 m mirror-to-mirror width, which no
  source gives. On those scales the photos measure 2012.5 mm (front), 2076 mm (rear) and 1980 mm (top, with
  TOP_K 1.026) across the flares, the widest point. The spec sheet says 1980 mm.
- The photos also disagree with one another, so no model can match all four exactly:
  - the mirrors: 1.100 m a side in the front photo (1.082 at the spec width), 1.129 in the top photo;
  - the roof rails: the rear photo draws them 3 to 4 cm further out than the top photo (rear photo 0.511 to 0.584 m
    a side, the model after the top photo 0.470 to 0.558), and the top photo draws them 0.2 to 0.3 m further forward
    than the side photo (x +0.30 to −1.65 against 0 to −1.88);
  - the roof: the top photo's windshield header is at x +0.578, the side photo's at +0.440, while both have the
    antenna at the same place. Positions along the roof are therefore placed by proportion between the header and
    the antenna (roof.py);
  - under the car: the front photo shows a dark band from tyre to tyre down to about 0.245 m (engine under-cover and
    lower arms), while the rear photo shows only the rear axle's hardware there: a band at 0.275 to 0.284 m (mapped)
    between the differential and the link mounts, and nothing of the front under-cover behind it. In a true
    orthographic rear view the front under-cover would show;
  - the front and rear photos draw the lower body about 5 cm lower than the side photo does;
  - the tail: the rear photo's tail lamps and bumper parts sit at other heights than the side photo's (section 7).

## 4. What the model uses (realframe.py)

- Length 4985, width 1980, height 1925 (over the roof rails), wheelbase 2850, track 1665, front overhang 937 (the
  owner's photo; the real photo agrees from the hub to the door), rear overhang 1198.
- Axles at x = +1.5555 and −1.2945 (the car centred on x = 0, nose at +2.4925).
- Tyres 265/55R20 (799.5 mm), rim 20 × 8J with its lip 536 mm across, six studs on a 139.7 mm circle. The hub is
  370 mm up, the loaded radius measured on the real photo. The tyre is rigid, so it reaches 30 mm under the ground,
  which hides it; that reads as a loaded tyre.
- Everything measured on the owner's photos is built in the photo frame, then mapped:
  - x: piecewise linear through the nose, the front hub, the B-pillar seam, the rear hub and the tail
    (photo −937 / 0 / 1714 / 2969 / 4053 mm behind the front hub → −937 / 0 / 1692 / 2850 / 4048). The fit leaves
    31 mm at the rear handle and 11 mm or less elsewhere (section 2); the handles and shut lines are built from the
    real photo anyway.
  - z: piecewise linear through the ground, the door-bottom shut line, the window foot and the rail tops
    (photo 0 / 455 / 1340 / 2022.6 → 0 / 429 / 1253 / 1925). It puts the roof crown at 1858 to 1867, as on the real
    photo.
  - y: × 1980 / 2012.5 (the body is built on the front photo's scale). The rear photo's y values go in at
    (1980 / 2076) / (1980 / 2012.5) = 0.9694 (fascia_rear.RY), and the top photo's at TOP_K / Y_SCALE (body.py).
- Built directly in the real frame:
  - **Wheel openings** (ext_parts.ARCH_PTS): traced point by point on the real photo. Both are flat-topped with a
    rounder front shoulder and a straight rear slope; the top edge is 862 mm up at the front and 930 at the rear, and
    the flare band over it is 66 and 78 mm wide (tops 929 and 1008 to 1010; the real photo's are 929 and 1007). The flares stand 26 mm out of the flank and stop
    at 0.990 m a side, so the widest point of the car is the spec's 1980 mm.
  - **Door shut lines, handles, fuel flap** (sides.py), from the real photo: the front door's front edge 617, the B
    seam 1692 and the rear door's rear edge 2738 behind the front hub; door bottoms 429 up; handle centres 1522 and
    2473 behind the front hub, 1130 and 1152 up, 0.27 m long.
  - **Sill and side steps** (sides.py): under the door bottoms the body steps in 6 cm to a black sill (0.905 m out)
    that carries the step, whose outer edge is flush with the door skin (0.962). The step runs from 599 to 2363 mm
    behind the front hub on the real photo (the owner's photo, mapped, gives 588 to 2335). Its heights come from the
    owner's photo through the z map, because the real photo is a GR Sport with a different step: bottom 303, top of
    the silver outer face 350, the tread's inner edge 377.
  - **Roof rails** (ext_parts.RAIL_*): one continuous rail a side. Along the car, from the real photo: it leaves the
    roof at the car's centre (x 0.0), is at full height from −0.219 to −1.763 and meets the roof again at −1.880,
    with one foot in the middle at −1.09; the bar is 27 mm thick. In plan, from the owner's top photo: the bar is
    50 mm wide and the rails close in toward the tail with the roof (centre line 0.538 m out at x 0.24, 0.505 at
    −1.41; the model uses 0.533 + 0.020 x). The rail tops are the official overall height, 1925 mm.
  - **Roof antenna** (ext_parts.FIN_*): a fin on the centre line, from the owner's photos mapped to the real frame.
    Top photo: x −1.60 to −1.78 (0.18 m long). Rear photo: the body is 78 / 61 / 38 / 30.5 / 25 / 19 mm wide at
    10 / 18 / 33 / 50 / 60 / 67 mm up; the model's is 63 mm wide on an 81 mm base rim and 73 mm tall. Side photo: its
    tip is level with the rail tops, so the fin's top is the official overall height as well.
  - **Glass roof** (roof.py): the panoramic panel of the top photo (front edge, divider and rear edge read on it,
    outline about 8 mm). The top photo puts the roof's header 0.14 m further forward than the side photo does and
    the antenna at the same place, so positions along the roof are placed by proportion between the two. The real ZX
    has a small moonroof instead: the owner's decision is open.
  - **Wheels** (wheels.py): 265/55R20 on a 20 x 8J rim: 203 mm between the flanges, 229 mm over all (the flanges'
    13 mm is a game choice), tyre 799.5 mm. The tyre's crown is read on the rear photo (73 %, 84 % and 95 % of the
    width at 6, 19 and 39 mm from the tread).
  - **Under the floor** (underbody.py), under one rule. After mapping, the photos' hub is 42 mm too high (412
    against 370). Parts the body carries (the front under-cover, the arms' inner pivots) keep the photo's mapped
    height; parts the wheels carry (the rear axle and everything bolted to it, the front arms' outer ends) hang
    42 mm lower. The official minimum clearance, 225 mm, is taken under the rear differential, where the rear
    photo has it once lowered (266 − 42 = 224). Nothing else inboard of the tyres is below 230 (a game choice).
    The rule costs 0.0045 of the rear view's IoU (the photo's axle is drawn 42 mm higher).
- No source for the width with mirrors: the model keeps the front photo's mirrors, which come out at 1.082 m a side
  (1.100 on the photo before its width is brought to the spec; the top photo draws them at 1.129).

## 5. Scoring

`compare_ext.py` renders the model from each photo's own orthographic camera. With `REAL=1` it first maps each photo
into the real frame the same way the model is mapped, so the score measures the model against the photo as it would
look at the real dimensions (each photo at its own width calibration, realframe.PHOTO_Y_SCALE). The tyres can never
match exactly, because the photo's tyres are 9 % bigger.

Scorer faults fixed on 9 Nov 2026, so scores from before them are not comparable:
- the renders ignored the photos' sideways stretch k (front 0.972, rear 1.029, top 1.109); they now render with that
  pixel aspect;
- the top camera rendered the car turned 180 degrees (front at the bottom); the near-symmetric plan hid it;
- the front and rear cameras' sideways offset had the wrong sign (under 1 mm on these photos, whose centre lines
  are within half a pixel of the image centre);
- the render is now cut at the photo's ground row, because the rigid tyres reach 30 mm under the ground;
- holes are filled in both outlines, not only in the photo's, so open wheel arches and see-through gaps count the same
  on both sides.

Silhouette IoU with `REAL=1`:

| Build | Side | Front | Rear | Top | What changed |
|---|---|---|---|---|---|
| r4 | 0.970 | 0.934 | 0.943 | 0.986 | real frame; older scorer and a one-line z map, so only roughly comparable |
| r5 | 0.988 | 0.941 | 0.951 | 0.986 | review fixes: z map through four heights, 1925 over the rails, hub 370, traced arches, sill and steps |
| r6 | 0.988 | 0.965 | 0.955 | 0.986 | rails tapered in plan, roof antenna, rear axle and front under-cover |
| r7 | 0.988 | 0.969 | 0.950 | 0.988 | closed wheels, glass roof, axle tunnel, underbody under one clearance rule, tidy pass |
| r8 | 0.989 | 0.969 | 0.950 | 0.989 | rear parts re-measured on 03_rear and rebuilt (section 7), clear lamp covers, cut guard |
| r9 | 0.989 | 0.970 | 0.950 | 0.989 | the tail's surface rebuilt from the side silhouette and the top photo's plan (section 7), side-glass surround |

Edge distance (mm) and colour error, side / front / rear / top:

| Build | Edge distance | Colour error |
|---|---|---|
| r6 | 46 / 25 / 53 / 93 | 45 / 62 / 50 / 38 |
| r7 | 43.8 / 16.6 / 54.1 / 104.9 | 44.9 / 55.7 / 50.0 / 36.6 |
| r8 | 44.5 / 15.8 / 28.3 / 100.7 | 44.7 / 53.8 / 49.9 / 36.4 |
| r9 | 43.6 / 15.8 / 24.2 / 101.9 | 45.3 / 53.7 / 49.3 / 35.9 |

Those two numbers are dominated by reflections and highlights that the photos paint and a clean render does not
have, so they are useful only for comparing one build with the next. The silhouette scores cannot see what r8 and r9
changed: the parts and the surface inside the outline. Section 7 measures those directly.

## 6. Known differences that remain (r9)

Because the photos are wrong or disagree (not to be fixed):
- the tyres and wheels (the model's real-size tyres are 8 % smaller than the photos'; pending the owner's decision);
- the differential is 42 mm lower than in the rear photo (official clearance on the real hub), so it also shows as a
  small nub under the front under-cover in the orthographic front view;
- the front under-cover shows in the orthographic rear view, where the rear photo has open air;
- the rails follow the top photo, so they sit 3 to 4 cm further in than the rear photo draws them;
- the mirrors follow the front photo;
- the tail's heights follow 03_rear, so in the side view the bumper's shoulder is 8 to 12 cm lower than 01_left draws
  it and the tail lamp 1 to 3 cm lower (section 7);
- the bumper stands out beyond the lamps by 01_left's 30 mm, not 04_top's 82;
- the glass panes are set 8 mm in (a game choice), so at the rear glass's heights the silhouette is 7 mm inside 01_left's;
- below z 0.46 the rear of the body is the under-curve the side photo shows, so the rear photo's lowest parts (the
  silver plate, the strip's arms, the corner panels' lower part) lie on a slope of 45 to 85 degrees. A camera behind
  and above the car does not see them.

Because the model is not finished (later steps in PLAN.md):
- the hood and the flanks show faint bands in reflections (the loft's stations), and the windshield's surround is
  still taken face by face (small steps at its corners);
- the quarter glass is a plain shape; the photo's kicks up at the rear and has a chrome surround;
- no interior yet, so the rear lamps' housings and the far windows show through the glass;
- the lug nuts are flat, the step tread has no ribs, there are no mud flaps and no number plate;
- approach 29.7 and departure 24.0 degrees, measured on the model, against the official 32 and 25.

## 7. The rear

### 7.1 What the photos say

01_left, the tail's line read to a fraction of a pixel (outlines.tail_contour; tools/tailrows.py and
tailcontour.py). d is the distance ahead of the car's rear end, z is 01_left's own height, photo frame, millimetres
and metres:

| Part | z | d |
|---|---|---|
| bumper's rear face | up to 0.72 | 0 to 2 |
| shoulder on top of the bumper | 0.747 to 0.777 | 0.5 rising to 41.5 |
| tailgate, lower part, upright | 0.78 to 0.94 | 46.5 |
| tailgate beside the plate recess | 0.96 to 1.05 | 50 to 52.5 |
| panel under the lamps | 1.09 to 1.15 | 42 to 46 |
| tail lamp, rear-most | 1.21 to 1.29 | 30 to 32.5 |
| lamp's top face | 1.29 to 1.31 | 33 to 58 |
| ledge under the window | 1.31 to 1.40 | 58 to 131 |
| rear glass | 1.465 to 1.607 | 152 to 198 |

The wiper stands 8 mm off the glass in this silhouette (z 1.43 to 1.46); the glass line is fitted above it.

03_rear (y on the front photo's scale): the bumper's dark rear face ends, and its lit top begins, at z 0.627 to 0.632
at every width; the lit top runs up to the tailgate's lower shut line at 0.697 to 0.706; the plate recess from 0.836
to its top corner at 1.062, 0.50 a side; the tail lamp from 1.1075 to 1.3116 with its bands at 1.130, 1.163, 1.185,
1.214 and 1.268; between the lamps the horizon's reflection crosses the gate unbroken at 1.11 to 1.14 (no step
there); the red reflectors 0.5425 to 0.5766; the satin band 0.4997 to 0.566; the chrome strip 0.4754 to 0.4929; the
silver plate down to 0.3948.

04_top, on its own scale (tools/toptail.py; the independent review's top3 to top5):
- the outline (the bumper's plan), to a fraction of a pixel: 2.9 / 4.6 / 6.2 / 11.1 / 18.6 / 42 / 78 / 130 mm ahead of
  the car's end at half-widths 0.20 / 0.25 / 0.30 / 0.40 / 0.50 / 0.60 / 0.70 / 0.80;
- the tail lamp's rear edge is 80 to 86 mm ahead of the outline at every half-width from 0.48 to 0.80, on both
  sides: the body above the bumper has the bumper's own plan curve, moved forward;
- the rear glass's lower edge is an arc: 8.5 / 20 / 28 / 36.5 mm ahead of its middle at 0.30 / 0.40 / 0.45 / 0.50;
- the spoiler's edge is an arc: 5 / 11 / 16 / 30 / 49 mm at 0.20 / 0.30 / 0.35 / 0.40 / 0.50.
04_top draws the greenhouse narrower than 03_rear does (the glass's lower corners at 0.60 against 0.74). Brought to
the same width, the glass's arc is 20 mm ahead at 0.5 and the spoiler's about 30, against the bumper's plan's 19:
the same curve within the reading. (An earlier reading here took a seam on the roof for the spoiler's edge and
called the edge straight; the review caught it.)

### 7.2 Where they disagree, and which is followed

- **Heights.** 01_left draws the tail higher than 03_rear: the bumper's shoulder from 0.745 to 0.777 against 0.630
  to 0.697, the crease at 1.08 against 1.058, the lamp 1 to 3 cm higher, the window's lower corner the same (1.392).
  The rear is what a camera behind the car sees, and every rear part is measured on 03_rear, so the tail's line is
  brought to 03_rear's heights (body.TAIL_Z) before it is used.
- **How far the bumper stands out.** 01_left: 30 mm beyond the lamps and 46.5 beyond the gate. 04_top: 82. 01_left's
  depths are used (the silhouette is the direct view of them); 04_top gives only the shape in plan.
- **The lamp and the bumper's parts** on the body side: 01_left has them 1 to 4.5 cm higher than 03_rear. The lamp
  keeps 03_rear's level bands round the corner (fascia_rear.ZR); the bumper's parts follow 03_rear alone.
- No official figure for the height of the bumper's top or of the load floor was found (searched November 2026).

### 7.3 How the surface is built (body.py, "the tail")

Above the bumper the body is the bumper's plan curve slid forward by the tail line's depth at each height:
x = X_REAR + L(y, z) F + flat(pd(|y|)). pd is the bumper's plan from 04_top; L the line of 7.1 at 03_rear's heights.
Three things are read off the photos on top of that:
- flat: the gate is flatter across its middle than the bumper. At the plate recess's heights the silhouette is the
  gate beside the recess, at |y| 0.5, and it is 3 to 6 mm ahead of the gate's middle, where the bumper's plan is
  19 mm ahead. Up to 20 mm of the plan's first depth is taken out; it comes back between |y| 0.50 and 0.65, where
  the lamps begin, and over the ledge above the lamps, so the glass and the spoiler have the plan whole.
- at the plate recess's heights the line of the gate's middle is carried straight up (the silhouette there is not
  the middle);
- between the lamps (inside |y| 0.38) the line runs straight past the lamp's own 5 mm step, as 03_rear shows it.
The last stations of the loft are a block standing proud of this surface, 5 mm apart, and one exact cut carves the
surface, the notch under the spoiler and the spoiler's edge out of it.

One game choice, named in the code: where the bumper's step dies out along the body side (TAIL_FADE: whole to where
the plan is 0.25 m ahead of the car's end, gone 0.30 m further on).

### 7.4 Result

The model's rear-most point at each height against 01_left's silhouette, real frame, millimetres (tools/rearsil.py; + is the model further forward):

| z real | r8 | r9 |
|---|---|---|
| 0.75 to 0.95 (tailgate) | −23 to −38 | −3 to +3 |
| 1.05 to 1.20 (panel and lamps) | −7 to +18 | −4 to +2 |
| 1.25 | +4 | +2 |
| 1.00 (crease) | −20 | −11: the crease is at 03_rear's height, 2 cm lower |
| 0.65 and 0.70 (shoulder) | | +33 and +48: the shoulder is at 03_rear's heights, 8 to 12 cm lower |

In r8 the gate, the shoulder and the lamps were one smeared slope. The independent review measured the first r9
build's centre line against its own reading of 01_left: within 0.6 mm from the shoulder to the window (and r8
53 to 19 mm off on the gate). The body is closed: its only open edges are the nine window and roof openings
(tools/loops.py), no edge is shared by more than two faces, and no back face shows from outside (backface.py).
54 objects, 24 materials, 91 draws, 187,918 triangles.

Left as it is: a ribbon under half a millimetre wide round the bumper's top corner and where the cut leaves the
body side (it shades clean); the windshield's surround; the wiper's pivot 15 to 21 mm behind the silhouette.

### 7.5 The parts on it (fascia_rear.py), decided in r8

- The tail lamp's bands are level at 03_rear's heights; 01_left only says how far forward each reaches.
- The bumper's parts follow 03_rear alone. Below z 0.46 they lie on the under-curve and are pushed along its own
  normal, in close rows, re-paired in space (surf._relax), or they shade as streaks.
- The chrome strip's face is stood plumb and 5.5 mm proud, and the silver plate 4 mm proud (game choices): lying on
  the under-curve they would mirror the ground, and the photo's are bright.
- Recess depths cannot be read off a photo: lamp 30 mm, plate 20, reflector 12, corner panel 2.5 (game choices).
- The stop lamp and the reflectors do not glow; the lamp covers are clear; there is no number plate.
- A cut removes faces left standing outside the old body (surf.cut). The test asks every old face at the nearest
  distance which side the point is on (surf._outside): asking one face alone called the faces of a pocket beside
  an edge stray and made holes beside the grille. tidy.py dissolves slivers under 0.02 mm and closes cracks of up to
  four sides in the body.

### 7.6 Tools (tools/)

rearsil (silhouette against the model), plansec (level cuts), gatex and gatenorm (depth and lean of the gate),
toptail (the top photo's tail), tailrows and tailcontour (the side photo's line), loops and openedges (open edges),
sidehit (what a ray from the side meets), rcmp (rear photo against a render, by window).

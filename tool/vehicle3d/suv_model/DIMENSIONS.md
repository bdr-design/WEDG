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
| Hub (loaded) | 433 (the rims' centre; 437 from the tyre's edges) | 370 (88.4 px at 4.19) | 408 |
| Tyre diameter | 872 | 799.5 (spec, 265/55R20) | the owner's photo's, by his decision: 872 as built |
| Rim lip diameter | 592 | about 540 (20-inch) | 592 as built |
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
- The wheels are 9 % too big: the tyre is 872 mm across, against 799.5 mm for the real 265/55R20 (872 / 799.5 =
  1.09), and the rim's lip is 0.296 m out, a 23.3 inch rim. The hub is 63 mm too high (433 against 370). The owner
  has decided the model keeps these wheels as drawn (section 4).
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
- Wheels as the owner's photo draws them (below): tyre 872 mm, rim's lip 592 mm across, six studs on a 139.7 mm
  circle, hub 408 mm up. The tyre is rigid, so it reaches 28 mm under the ground, which hides it; that reads as a
  loaded tyre.
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
  - **Wheel openings** (ext_parts.ARCH_PTS): from the owner's photo, like the wheels: round each hub on 01_left,
    where the dark of the wheel well ends and the paint begins, every 10 degrees (tools/archphoto.py; black against
    dark paint, so within about 15 mm). Each point keeps its offset from the hub in the photo, unscaled, as the
    wheel does. Both openings top out 948 mm up. Gaps round the tyre as seen from the side, model / photo: front
    57 ahead, 98 over, 55 behind / 64, 104, 62; rear 71, 98, 41 / 79, 104, 48 (the flare's lip is 6 mm inside the
    cut). The real photo's openings (tops 862 front, 930 rear) were used up to r10 and do not hold the bigger
    wheel; r11 mapped the photo's openings with the body, which put the rear wheel forward in its opening. The
    flare band over each opening is 29 and 41 mm wide (section 6), topping out 979 and 991 mm up. The flares stand
    26 mm out of the flank and stop at 0.990 m a side, so the widest point of the car is the spec's 1980 mm.
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
  - **Wheels** (wheels.py, realframe.py): **the owner's decision, 10 Nov: the size his photos draw them, not the
    spec's.** On 01_left the rims' bright lips are circles centred 0.4327 m up in the photo, which maps to a hub
    0.408 m up (the real photo's loaded hub: 0.370). The lip ends 100.5 px out (0.296 m: a 23.3 inch rim against the
    spec's 20) and the tyre's edge 148.3 px out (0.872 m across; the spec's 265/55R20 is 0.7995). The sidewall is
    140 mm. The width is kept at the spec's 265 on an 8J rim (203 mm between the flanges, 229 over all; the flanges'
    13 mm is a game choice). The tyre's crown is read on the rear photo (73 %, 84 % and 95 % of the width at 6, 19
    and 39 mm from the tread). (r10 had the lip at 0.303 and the hub at 0.412, read off one side of each wheel; the
    review's circle fits corrected both.)
  - **Under the floor** (underbody.py). With the photos' wheels the hub is where the photos have it, so everything
    under the floor is at the height the photos map to: the rear differential's underside at 0.266 (the official
    minimum clearance of 225 mm is for the spec's tyre, whose hub is 38 mm lower: 225 + 38 = 263), the rear links'
    eyes at 0.2255, the front under-cover at 0.238 to 0.245 and the front arms' outer ends at 0.221, the lowest
    point of the car.
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
| r10 | 0.990 | 0.971 | 0.952 | 0.989 | the photos' wheels (owner's decision); outlines read to a fraction of a pixel |
| r11 | 0.990 | 0.971 | 0.952 | 0.989 | wheels and wheel openings re-measured on the photo; windshield's side edges and surround |
| r12 | 0.990 | 0.971 | 0.951 | 0.989 | wheel openings set round the hubs unscaled, like the wheels |
| r14 | 0.990 | 0.971 | 0.952 | 0.989 | side step clear of the rear opening (r13); flare bands thinned (owner's decision) |
| r22 | 0.990 | 0.973 | 0.952 | 0.989 | windshield's edges (r16), flat side glass and the belt on the photo's chrome line (r17 to r21), number plates |
| r24 | 0.989 | 0.975 | 0.951 | 0.993 | the body side from the top photo (section 8): arc glass, shoulder on the belt, narrower doors, step and flares on the outline; plates seated |
| r25 | 0.989 | 0.975 | 0.950 | 0.993 | the rear fender's swell round the wheel and a thinner flare leg at the rear door (the owner's decisions) |

Edge distance (mm) and colour error, side / front / rear / top:

| Build | Edge distance | Colour error |
|---|---|---|
| r6 | 46 / 25 / 53 / 93 | 45 / 62 / 50 / 38 |
| r7 | 43.8 / 16.6 / 54.1 / 104.9 | 44.9 / 55.7 / 50.0 / 36.6 |
| r8 | 44.5 / 15.8 / 28.3 / 100.7 | 44.7 / 53.8 / 49.9 / 36.4 |
| r9 | 44.1 / 15.8 / 24.0 / 102.1 | 45.3 / 53.7 / 49.0 / 35.8 |
| r10 | 46.1 / 16.6 / 24.1 / 97.0 | 44.5 / 53.8 / 48.9 / 35.8 |
| r11 | 44.1 / 16.3 / 24.0 / 109.4 | 43.8 / 53.7 / 48.8 / 35.8 |
| r12 | 43.7 / 16.3 / 24.2 / 109.5 | 43.6 / 53.6 / 48.9 / 35.7 |

Those two numbers are dominated by reflections and highlights that the photos paint and a clean render does not
have, so they are useful only for comparing one build with the next. The silhouette scores cannot see what r8 and r9
changed: the parts and the surface inside the outline. Section 7 measures those directly.

## 6. Known differences that remain (r9)

Because the photos are wrong or disagree (not to be fixed):
- the wheels are the photos' (the owner's decision), 9 % bigger than the spec's 265/55R20, so the lowest point is
  221 mm up where the official clearance is 225;
- the front under-cover shows in the orthographic rear view, where the rear photo has open air;
- the rails follow the top photo, so they sit 3 to 4 cm further in than the rear photo draws them;
- the mirrors follow the front photo;
- behind the mirrors the front and rear photos do not show the body's side (z 1.28 to 1.63: the shoulder under
  the glass and most of the side glass), and they never show the doors, which are narrower than the fenders. Since
  r23 that part comes from 04_top and 01_left (section 8). 04_top draws the cabin 25 to 37 mm narrower at the glass's
  head than 02_front and 03_rear do; the front and rear photos are followed there;
- 04_top's chrome line runs in to 0.733 (top photo's scale) by the quarter glass's rear end, 45 mm inside the
  glass's line at the B pillar, which would leave about 2 cm of painted pillar beside the rear photo's back window.
  The taper to the rear is held at 18 mm (a game choice), so the chrome strip is 9 mm outside 04_top's line 0.19 m
  ahead of the quarter glass's rear end and 21 to 25 mm outside it in the last 12 cm;
- 04_top draws the cabin shorter than 01_left: the door seams and the pillars are 0.10 m (B pillar) to 0.28 m (the
  rear door's rear edge) further forward on it, while the wheels are at the same stations on both. The model keeps
  01_left's stations (section 8.2);
- the flares are the official 1.980 m across, 4 mm a side more than 04_top's outline;
- the tail's heights follow 03_rear, so in the side view the bumper's shoulder is 8 to 12 cm lower than 01_left draws
  it and the tail lamp 1 to 3 cm lower (section 7);
- the bumper stands out beyond the lamps by 01_left's 30 mm, not 04_top's 82;
- the glass panes are set 8 mm in (a game choice), so at the rear glass's heights the silhouette is 7 mm inside 01_left's;
- below z 0.46 the rear of the body is the under-curve the side photo shows, so the rear photo's lowest parts (the
  silver plate, the strip's arms, the corner panels' lower part) lie on a slope of 45 to 85 degrees. A camera behind
  and above the car does not see them.

Because the model is not finished (later steps in PLAN.md):
- above and below the windshield the surround is still taken face by face (its leaning side edges are bands
  since r11: the pane's edge was cut along the chord across its knee and stood 2 to 3 cm out of line, in steps);
- the bands the hood and the flanks showed in reflections were the photos' pixel steps (folds of 2 degrees between
  stations on the hood, median; 0.3 now that the outlines are read to a fraction of a pixel, outlines._frac and
  _iron; the review measured 0.26 to 0.33); the windshield frame's reflection on the hood's rear third is still wavy;
- the belt and the quarter glass (r20): the chrome line under the side glass on 01_left is at z 1.336 / 1.356 /
  1.371 / 1.380 at 2.30 / 3.10 / 3.50 / 3.80 m behind the nose (photo frame), and kicks up behind 3.88 to 1.518 at
  4.33, where the quarter glass ends. Up to r19 the belt was 2 to 4.5 cm lower, rose half as fast, and the quarter
  glass ran 9 cm further back with a short steep corner. The kick-up is one straight cut (up to 13 mm over the
  photo's curve), with the chrome strip along it; the photo's wide bright blade up the glass's rear edge and its
  rounded upper rear corner are not modelled yet;
- the glass is blacked out all round and opaque (the owner's decision, 10 Nov: the full dark tint), so nothing
  shows through it from outside; there is no interior yet;
- the lug nuts are flat and the step tread has no ribs. There are no mud flaps behind the wheels, by the owner's
  decision (10 Nov), though his photo has them;
- number plates (plate.py, r22), the owner's choice: a Saudi private plate reading ا م ن 1, front and rear. Four
  cells, Eastern Arabic digit and Arabic letters over their Latin equivalents (ا A, م Z, ن N), with the band that
  carries the country's name and KSA in the middle, between the number and the letters (the long plate since 2014;
  r22 and r23 had it at the right); the long plate, 520 x 110 mm (Wikipedia's figure for the current series; other
  sources give 550 x 110 and 520 x 113, and 335 x 155 for the short plate). The national emblem is not drawn: a
  plain disc stands for it (a game choice). The rear one lies on the floor of the plate recess and leans 4.8 degrees
  with it, 1 to 3 mm off it; the front one stands upright on a black bracket, a wedge 4 mm deep at its top and
  28 mm at its foot that takes up the slope of the intake's bars (no photo shows how the front plate is held; r22
  and r23 had both plates clear of everything near them, floating);
- the wheel openings follow the photo's wheels unscaled while the body is brought to the spec's height, so each
  opening stands 37 mm higher against the body than in the photo. The owner's decision (10 Nov): the flare bands are
  thinned by that much (29 and 41 mm for the real photo's 66 and 78), so their tops stay where the photo has them,
  979 and 991 mm up, clear of the head lamp's cover and 95 mm under the fuel flap;
- the rear door's shut line stops at the top of the rear flare (on the real car it runs on across it);
- the rear door and the rear flare (r25, the owner's decisions of 10 Nov on r24's pictures): the door's skin goes
  out to the rear fender as a gentle swelling round the wheel, and the flare's front leg stands 19 to 28 mm out of
  it, where 04_top's outline has the flare 4 to 6 cm outside the door. So the model's outline from above is 5 to
  9 mm inside 04_top's at d 3.4 to 3.6, and the door's widest line is up to 3 cm outside 04_top's at d 3.2 to 3.3
  (the step shows 3 cm less from above there). r24 had 04_top's sweep and outline: the skin ran out 48 mm in 9 cm
  of height at the rear door's seam, a diagonal crease from the rear three-quarter, and the leg stood 44 to 64 mm
  proud, like a fin;
- left by the reviews of r25: the diagonal hollow is gone (the worst hollow turn across its place is 2.9 degrees in
  2 cm, 0.4 to 0.9 mm deep; r24 20 to 23 degrees). At a grazing angle of 9 degrees from behind, wavy dark streaks show
  in the reflection along the rear door's rear seam (the haunch mirroring the body; gone at 14 degrees). The rear
  door's skin is 24 mm further out than r24's at real x -1.0, z 1.0, which no photo checks;
- left by the review of r24: the fuel flap's front 5 to 8 cm lies where the skin turns out to the fender. The
  mirror's arm lands on the side glass 2 to 6.5 cm above its foot, where 01_left has it on the door skin under the
  belt. The front plate's bracket hangs free below the intake's lowest bar;
- the review of r16 confirmed the step, the flares (tops 0.979 and 0.991, 37 mm under the head lamp's cover and
  94 mm under the fuel flap), the blacked-out glass and the windshield (pane edge 4 to 6 mm inside the photo's
  line, pillar 46 mm wide from the front where the photo has 46), and left as known: matte patches on the roof
  just behind the windshield's header (the surround there is still taken face by face), and the pillar's foot
  25 mm wider than the photo's;
- the windshield (r16): on 02_front the glass ends at a dark line 1 cm wide, the gap to the A pillar, 0.75 m out
  at z 1.50, 0.73 at 1.58, 0.71 at 1.66, 0.69 at 1.74 and 0.66 at 1.82 (photo frame, both sides alike). The pane
  runs to 5 mm short of it with a 12 mm surround; up to r15 it was 4 to 7 cm narrower a side;
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
  19 mm ahead. A plan depth p loses 20 mm x tanh(p / 20 mm), 14.6 of the 18.6 mm at |y| 0.5; it comes back between
  |y| 0.50 and 0.65, where the lamps begin, and over the ledge above the lamps, so the glass and the spoiler have
  the plan whole.
- at the plate recess's heights the line of the gate's middle is carried straight up (the silhouette there is not
  the middle);
- between the lamps (inside |y| 0.38) the line runs straight past the lamp's own 6 mm step, as 03_rear shows it.
The last stations of the loft are a block standing proud of this surface, 5 mm apart, and one exact cut carves the
surface, the notch under the spoiler and the spoiler's edge out of it. The bumper's rear face takes the plan's
first millimetres as well, and the spoiler's top comes down to its tip along the plan, so it ends in the same thin
edge right across (its tip was 15 mm short of 01_left's before).

Game choices, named in the code: where the bumper's step dies out along the body side (TAIL_FADE: whole to where
the plan is 0.25 m ahead of the car's end, gone 0.30 m further on) and how far ahead of the tip the spoiler's top
stops following the plan (TIP_REACH: whole to 3 cm, not at all 15 cm further on).

### 7.4 Result

The model's rear-most point at each height against 01_left's silhouette, real frame, millimetres (tools/rearsil.py; + is the model further forward):

| z real | r8 | r9 |
|---|---|---|
| 0.75 to 0.95 (tailgate) | −23 to −38 | −3 to +3 |
| 1.05 to 1.20 (panel and lamps) | −7 to +18 | −4 to +2 |
| 1.25 | +4 | +2 |
| 1.00 (crease) | −20 | −11: the crease is at 03_rear's height, 2 cm lower |
| 0.65 and 0.70 (shoulder) | | +33 and +48: the shoulder is at 03_rear's heights, 8 to 12 cm lower |

In r8 the gate, the shoulder and the lamps were one smeared slope. The body is closed: its only open edges are the
nine window and roof openings (tools/loops.py), no edge is shared by more than two faces, and no back face shows
from outside (backface.py). 54 objects, 24 materials, 91 draws, 190,448 triangles.

Three independent reviews. The first measured the centre line against its own reading of 01_left (within 0.6 mm from
the shoulder to the window; r8 was 19 to 53 mm off on the gate) and found two misreadings of 04_top (the glass's and
the spoiler's arcs) and nine smaller faults. The second confirmed the corrections on the rebuilt model (plan within
0.6 mm of the photo out to |y| 0.75, glass 18.8 mm ahead at 0.5, bumper face ending at z 0.630, no step up the rear
corners) and found four more: the spoiler's edge still straight in the middle, a shading band on the gate's flanks,
the bumper's face off the new plan, two comments. Those are corrected and re-measured (spoiler's end 20 mm ahead of
its middle at |y| 0.5 and 46 at 0.6; bumper face 0.5 / 2.9 / 4.6 mm ahead at 0.10 / 0.20 / 0.25). The third
confirmed those four by its own measurement (edge 20.5 and 43.5 mm ahead at 0.5 and 0.6, tip 1.8 mm short of
01_left's instead of 15; no tilt left on the gate's tall faces; bumper face within 0.05 mm of the plan; shoulder's
lower edge at z 0.629 to 0.633 at every width) and found a ripple in the spoiler's top line by the tip, from the
contour's pixel steps; the line is now smoothed there (slopes 11 to 15 degrees from 2 cm ahead of the tip on).
That last change is measured by the builder only.

Left as it is:
- the lamp's own step is no longer in the side silhouette: between the lamps the line runs straight, so at z 1.19 to
  1.22 the model is 2 to 4 mm ahead of 01_left;
- a ribbon under half a millimetre wide round the bumper's top corner (it shades clean);
- the windshield's surround is still taken face by face, and a stair-stepped chrome line remains at the quarter
  glass's lower rear corner;
- the wiper's pivot is 15 to 21 mm behind the silhouette;
- the spoiler's outer corners are rounder than the plan (115 mm ahead of the middle at |y| 0.70, the plan 78), and
  the folds of its lip reach 38 degrees, just under the 40 at which a fold is drawn sharp.

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

## 8. The body side between the cowl and the tail (r23)

### 8.1 What the photos say

02_front and 03_rear show the side only where nothing stands out past it: the glass above the mirrors (z over
1.63, photo frame) and the fenders' tops (up to z 1.28; the two photos agree within 7 mm there: 0.925 and 0.932 at
1.28, hull scale). Up to r22 that one outline was used at every station, so the doors were as wide as the fenders
and covered the side step, and what the mirrors hide was filled in by rule (a flat glass and a ledge under it).

04_top shows the side from above between the mirror and the tail (tools/topbelt.py, tools/topsec.py; top photo's
scale, times 1.026 for real metres; d is metres behind the nose in the photo frame):

| What | Where it is |
|---|---|
| the chrome line under the side glass | 0.794 at d 1.8, 0.7985 at 2.0, 0.8036 at 2.55 (its widest), 0.798 at 3.0, 0.789 at 3.5, 0.775 at 3.8, 0.733 at 4.2; left and right within 3 mm of their mean |
| a thin black line outside the chrome | 8 mm wide, then paint |
| a crease along the doors | 0.855 to 0.863, d 1.9 to 3.3 |
| the door skin's widest line (where the step comes out from under it) | 0.893 to 0.899, d 1.8 to 3.3; it sweeps out to the rear fender: 0.909 at 3.4, 0.928 at 3.5, 0.943 at 3.55 |
| the outline between the wheels (the step's outer edge) | 0.9424 at d 1.6, 0.953 at 2.0, 0.957 at 2.9 |
| the outline at d 1.5, between the front flare and the step | 0.939: the fender is still at its full width there |
| the glass's head line | 0.647 at d 2.5, 0.632 at 3.7 |

01_left shows a highlight along the doors 65 to 70 mm under the chrome line (z 1.27 at d 2.0, 1.287 at 3.0 to 3.4),
rising with the belt and sweeping up over the rear wheel; the door handles are at z 1.17 to 1.25.

### 8.2 Where they disagree, and which is followed

- The glass's head: 04_top has it 0.663 m out (real), 02_front 0.687 and 03_rear 0.693 at the same height. The
  front and rear photos agree with each other and are followed: above the mirrors the glass is their outline.
- The glass's foot is hidden in the front and rear photos, so 04_top's chrome line is followed. The two fit one
  surface if the glass is an arc, as a side glass is: 16 degrees off plumb at z 1.63 and 9 at its foot, radius
  2.4 m. (The front outline above the mirrors is itself curved the same way: 16 degrees at 1.66, 19 at 1.75, 23 at
  1.83.)
- The quarter glass's rear end: see section 6 (the taper is held at 18 mm).
- Along the car: the seams that cross the chrome line are at d 1.547, 2.570 and 3.484 on 04_top (the front door's
  front edge, the B pillar, the rear door's rear edge) and its quarter glass ends at 4.262; on 01_left they are at
  1.544, 2.668, 3.760 and 4.328. The handles differ the same way (rear handle 3.21 to 3.45 against 3.39 to 3.68).
  The wheels do not: both photos have the rear flare round d 3.4 to 4.4. So 04_top draws the cabin shorter over
  the same wheels. The doors, pillars and handles keep 01_left's stations (and the real photo's); the cabin's
  readings from 04_top (the chrome line) are moved to them by those four landmarks (outlines.TOP_CABIN); what
  belongs to the wheels (the fender's sweep, the flares, the step) is used where 04_top has it.

### 8.3 How it is built (outlines.side_half)

From the top down, at each station: the glass (outlines.glass_half) less the plan's bow at that station
(outlines.taper: 15 mm at d 1.8, 0 at 2.65, 5 at 3.4, 11 at 3.8, 18 from 4.2 back), fading out above the glass's
head toward the roof's edge, which stays; at the belt (the chrome line on 01_left, which rises to the rear) a shoulder runs down and out to the crease,
65 mm below the belt at every station; from the crease the door skin bulges to its widest, 0.895 (top photo's scale),
at z 1.0, and is plumb below that. Over the rear wheel (d 3.30 to 3.66 blends) the fender's top, which the photos
show up to z 1.28, carries on up to the belt as one arc (blended in along the car between d 3.55 and 4.00), and
lower down the door's skin swells out to the fender's width round the wheel: all of it within 0.45 m of the hub as
seen from the side, none beyond 0.85 m (outlines.REAR_BULGE; the owner's decision, section 6); the two are joined
by a soft maximum (a hard one left a hollow line of 8 to 13 degrees where they crossed, tools/hollow.py). Below the
fenders' bulge the body's width is limited to 1.97 m, the limit coming in over z 0.96 to 1.06. A hard limit at 1.0
left a level hollow line along both fenders up to r24 (10 degrees in 2 cm and 2.8 mm deep behind the front arch);
the review of r25 still measures 5.3 degrees and 1.5 mm there, up to 18 degrees ahead of the front arch (42 in
r24), and a faint level hollow along the doors at real z 0.90 to 0.92 (1 to 2.5 degrees, under 1 mm deep), none
of which it could make out in a render. 04_top has the rear
handle as far out as the front one and 01_left has it over d 3.39 to 3.68; the skin is 16 mm out at its rear end.
At the front the fender's width fades into the door from
d 1.48 to 1.82 (under the mirror on 04_top), and ahead of the cowl (d 1.60 to 1.15 blends) the front photo's outline
is used whole. The hull's rows are 5 mm apart in the 11 cm under the belt, with one row on the belt (body._rows): at
the old 37 mm the loft chorded the shoulder and its hollow corner stood 8 to 10 mm proud. The rows keep their
places from the cowl to the tail: where they changed height along the car the quads sheared and the surface rippled
(the rear fender in r23's first build, the A pillar's foot while the belt's row left the belt there).

The black band under the belt is 10 mm tall (04_top's 8 mm line), under the quarter glass's kick-up too; the chrome
strip is 9 mm tall, centred 1 mm under the belt line, from d 1.58, and its middle stands 3 mm outside the glass's
foot, which is set that much inside 04_top's line. The door handles lie along the skin and lean with it
(sides.handles): 0 to 4 mm off it at the four corners of each bar's back (tools/seated.py); the review's 1 mm grid
found the rear bars' lower rear corners 0.6 to 0.75 mm into the skin over a patch of 14 by 11 mm. The side step's outer edge is 04_top's outline (sides.step_y), the sill is 45 mm inside
the door skin, and each flare's face is 04_top's outline plus 4 mm (ext_parts.FLARE_OVER), but no more than 28 mm
out of the body beside it (FLARE_PROUD, the owner's decision) and never less than 5 mm outside the tyre's face
(TYRE_COVER; the face is 0.965 m out). The upright shut lines run up to the chrome
strip at their own stations in 6 mm steps.

### 8.4 Result (measured on r24; the last two lines on r25)

- the chrome strip's middle against 04_top's line (tools/chromeplan.py): within 1 mm from d 1.8 to 3.5 on 04_top
  (1.82 to 3.77 on the model), +3 at 3.6, +4 at 3.9, +9 at 4.0, +21 and +25 at 4.1 and 4.2 (the held taper);
- the model's outline from above against 04_top's (tools/topout.py): within 1 mm along the step (d 1.7 to 3.2),
  +3 to +4 mm on the flares, -5 mm at d 1.5; top IoU 0.993 (0.989 before);
- folds in plan under the belt (tools/planfold.py, 2 cm chords, d 1.2 to 4.6): under 4 degrees (r21: 13 to 29 on
  the front door); the black band's lower edge is straight (tools/bandedge.py);
- the handles' bars 1.2 to 1.3 mm off the skin at both ends, the rear plate 1 to 3 mm off the recess floor
  (tools/seated.py);
- the flares stand 9 mm or more outside their tyres at every station, and the rear flare's front leg 19 to 28 mm
  out of the door (tools/tyrecover.py);
- 209,565 triangles (190 thousand before: the shoulder's rows).

Not known from any photo: the section of the shoulder between the belt and the crease (taken as straight, 42 to 49
degrees), the door skin below its widest line (taken as plumb), and the haunch over the rear wheel between z 1.28
and the belt (one arc).


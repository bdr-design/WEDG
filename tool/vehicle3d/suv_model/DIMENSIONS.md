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
| Tyres | 265/55R20 (ZX, VX, Sahara); 265/65R18 (GR Sport) | Toyota AU, autostw.com.au |
| Wheel | 20 × 8.5, PCD 6 × 139.7 mm, centre bore 106.1 mm, offset ≈ +55 | autostw.com.au, wheel-size.jp |
| Approach / departure angle | 32° / 25° (24° approach on the Sahara ZX) | Toyota AU via CarsGuide |
| Turning radius | 5.9 m (ZX) | toyota.jp |

Derived: a 265/55R20 tyre is 20 × 25.4 + 2 × 0.55 × 265 = **799.5 mm** across.

Not published anywhere I could reach: overhangs, width with mirrors, window and pillar sizes. Those come from the
photos (section 2).

Sources:
- https://toyota.jp/pages/contents/landcruiser300/004_p_001/pdf/landcruiser300_spec_202503.pdf (via https://bestcarweb.jp/feature/column/1339442)
- https://www.carexpert.com.au/toyota/landcruiser/2025/dimensions
- https://www.carsguide.com.au/car-news/lc300-wading-depth-approach-and-departure-angles-towing-locking-diffs-and-tyre-specifics
- https://autostw.com.au/blogs/news/toyota-land-cruiser-300-tyre-size-guide-wheel-specs-pcd-centre-bore-torque-settings
- https://wheel-size.jp/size/lexus/lx/2024/ (the same 265/55R20 8Jx20 wheel on the LX)

## 2. A real photo, measured

Wikimedia Commons, "Moscow, Toyota Land Cruiser ZX grey, Sept 2025 01.jpg" (1280 px copy in
`scratchpad/lc300_ref/real_016.jpg`). It is listed as a ZX, but it has the GR Sport front and 18-inch 265/65R18
wheels; the body, doors and glass are the same as the ZX. It is taken from the side with about 10° of yaw (the
tailgate shows). It is used to measure from, never shown on the model.

Scale: wheelbase 656.2 px = 2850 mm along the car; heights at 4.27 mm/px (cross-checked with the 801.7 mm tyre, 187 px).
Ground line: 671 px under the front hub and 683 px under the rear hub.

Distances behind the front hub, in mm:

| Feature | Owner's photo | Real photo | Owner − real |
|---|---|---|---|
| Front door, front edge | 616 | 617 | −1 |
| Front handle, centre | 1536 | 1522 | +14 |
| B-pillar door seam | 1714 | 1692 | +22 |
| Rear handle, centre | 2594 | 2473 | +121 |
| Rear door, rear edge | 2844 | 2738 | +106 |
| Rear hub | 2969 | 2850 (spec) | +119 |
| Quarter glass, rear tip | 3491 | 3416 | +75 |
| Tail lamp, front edge | 3652 | 3616 | +36 |
| Tail | 4053 | 4048 (spec 4985 − 937) | +5 |

Heights above the ground, in mm:

| Feature | Owner's photo | Real photo / spec |
|---|---|---|
| Hub | 437 | 381 (374 front, 389 rear) |
| Tyre diameter | 864 | 800 (spec) |
| Rim lip diameter | 588 | ≈ 540 (20-inch) |
| Window foot at the front door | 1345 | 1299 |
| Roof edge at the rail feet | 1938 | 1896 |
| Roof crown | 1955 | 1925 (spec) |
| Rail tops (no cross bars) | 2019 | 1977 (seen from below, so a little low) |
| Door bottoms | 541 | 451 to 459 |
| Wheel arch top edge | about 0.94 | 926; flare top 999 |

## 3. What this says about the owner's photos

- From the nose to the B pillar they match the real car within about 2 cm.
- Behind the B pillar, the rear wheel, the rear door's rear edge and the rear handle are about 115 mm too far back
  (photo wheelbase 2969 mm, spec 2850 mm). The tail is in the right place, so the rear overhang is about 115 mm too
  short.
- The wheels are 8 % too big: the tyre is 864 mm across, against 800 mm for the real 265/55R20, so they look like
  22-inch wheels. That lifts the car about 56 mm at the hub, 46 mm at the window foot and 30 mm at the roof.
- Widths: views.json scaled the front, rear and top photos by assuming a 2.2 m mirror-to-mirror width, which no
  source gives. On those scales the photos measure 2012.5 mm (front), 2076 mm (rear) and 1980 mm (top, with
  TOP_K 1.026) across the flares, the widest point. The spec sheet says 1980 mm.
- The mirrors disagree between the photos: 1.105 m a side in the front photo (1.082 at the spec width), 1.135 in the
  top photo.

## 4. What the model uses (realframe.py)

- Length 4985, width 1980, height 1925 (roof crown), wheelbase 2850, track 1665, front overhang 937, rear overhang 1198.
- Axles at x = +1.5555 and −1.2945 (the car centred on x = 0, nose at +2.4925).
- Tyres 265/55R20 (799.5 mm), rim 20 × 8.5 with its lip 536 mm across, studs on a 139.7 mm circle, hub 382 mm up.
  A rigid tyre on a 382 mm hub sinks 18 mm into the ground, which reads as a loaded tyre.
- Everything measured on the owner's photos is built in the photo frame, then mapped:
  - x: piecewise linear through the nose, the front hub, the B-pillar seam, the rear hub and the tail
    (photo 0 / 1714 / 2969 / 4053 mm behind the front hub → 0 / 1692 / 2850 / 4048). The fit leaves at most 33 mm
    (the rear handle) and otherwise 15 mm or less.
  - z: one line through the hub (437 → 381) and the roof crown (1955 → 1925). It puts the window foot at 1304
    (real 1299) and the rail tops at 1990 (real 1977, seen from below).
  - y: × 1980 / 2012.5 (the body is built on the front photo's scale). The rear photo's y values go in at
    (1980 / 2076) / (1980 / 2012.5) = 0.9694 (fascia_rear.RY), and the top photo's at TOP_K / Y_SCALE (body.py).
  - The arch flares stop at 0.99 m a side, so the widest point is the spec's 1980 mm.
- Built directly in the real frame from the real photo: the wheel arches (a 476 mm circle round a point 7 cm above the
  hub, so the top edge is 926 mm up), the door shut lines (front edge 617, B seam 1692, rear edge 2738 behind the front
  hub, the door bottoms 455 up, round the rear arch), the handles (centres 1522 and 2473 behind the front hub,
  0.27 m long), and the fuel flap.
- No source for the width with mirrors: the model keeps the front photo's mirrors, which come out at 1.082 m a side.

## 5. Scoring

`compare_ext.py` with `REAL=1` maps each photo into the real frame the same way before it scores the model, so the
score measures the model against the photo as it would look at the real dimensions (each photo at its own width
calibration, realframe.PHOTO_Y_SCALE). The tyres can never match exactly, because the photo's tyres are 8 % bigger.

Two scorer bugs were fixed on 9 Nov 2026, so earlier front, rear and top scores are not comparable:
- the renders ignored the photos' sideways stretch k (front 0.972, rear 1.029, top 1.109); they now render with that
  pixel aspect;
- the top camera rendered the car turned 180 degrees (front at the bottom); the near-symmetric plan hid it.

| Build | Side | Front | Rear | Top |
|---|---|---|---|---|
| r4 (real frame, fixed scorer) | 0.970 | 0.934 | 0.943 | 0.986 |

What is left in the front and rear views is mostly the photo's bigger tyres and a 3 cm band under the bumpers: the
front and rear photos draw the lower body about 5 cm lower than the side photo does.

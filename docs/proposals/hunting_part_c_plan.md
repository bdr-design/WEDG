# The hunting season, part C: the camp and the outing on the map (plan, 19 Nov 2026)

The design is the owner's approved storyboard, `design/hunt/trip_board.jpg` (`design/hunt/trip.cjs`, frames 1-22), and
`docs/proposals/hunting_season_design.md`. The engine (part A) and the phone (part B) are built: `StartTrip`,
`EndTrip`, `MoveCamp`, `SpotFalcon`, `ReleaseLure`, `CastFalcon`, `SearchFalcon`. `Trips.leg/night/card` give the drive and
the nights through the calendar's own `away()`. The snapshot's `falcons.trip` says where he is: `arriveOn/arriveMinute`,
`homeOn/homeMinute`, `leg`, `stop`, `sighted`, `done`. The phone's `openTrip(kind, ground, nights, onGo)` is the card
before leaving. Part C draws all of this on the map.

## What exists to draw with

- **Land:** `tool/terrain3d` builds real land (SRTM elevation and a Sentinel-2 colour) for one area. Today that area is
  70 x 66 km around the farm, with fine rings 4 km and 12 km round the yard and 550 m cells beyond.
  - طرف النفود (14 km west) and المحازة (17 km) are inside it, but on its coarse cells.
  - The trapping grounds (الحماد about 600 km north, and the rest) are outside it.
  - Both hosts the tool uses answer from this machine.
- **Models:** the LC300 and the man are built. These are not built yet:
  - the tent, the supplies, the pigeon cage, the nets, the perch and the falcons' room;
  - the birds: the saker, the houbara and the stone-curlew are rigged on `wip/t17`; the peregrine is begun there;
  - the man's arm carrying a falcon.

## The parts, in order

**C1: the map, the room and the camp** (this round; nothing in it waits on the birds):
1. **The falcons' room** in the yard once it is built (frames 4-5). A building made by code, with its pin and card:
   - the card shows how many falcons, which want الدعو today, and the moult;
   - its buttons are «ادعهم» (CareFalcons) and «نادي الصقور» (the phone's club).
2. **The grounds' pins** on the farm's map (frames 1-3):
   - the two hunting grounds lie west at their real bearing and distance;
   - the trapping grounds' pins point north at their bearing, on the horizon.
   - A pin's card (Sadu) carries:
     - the distance;
     - the season, or that it is closed;
     - for a trip, the nights he chooses;
     - «اطلع للرحلة» or «اطلع للمخيم». That button opens the phone's «قبل ما تمشي» card, and its «اطلع» sends
       StartTrip.
3. **The drive** is the calendar's jump (`Trips.leg`), under the phone's own progress screen. The camp's land and
   models are loaded and made ready (sent to the GPU, their shaders compiled, as the lobby does) **during** that jump,
   so nothing loads in play.
4. **The camp** at the ground (frames 7-8, 13):
   - the land is the ground's own (see question 1);
   - the tent, the supplies, and for trapping the pigeon cage and the nets;
   - the car parked beside them, and he is in its seat;
   - the tent's pin opens the camp card: the day, the supplies left, the farm's days left «تقريبًا», and «نام لين الفجر»
     (`tripNight`) and «فك المخيم وارجع» (EndTrip, then the jump home);
   - a stop lights the phone's button (decision 3).
   - The farm is not drawn while he is away. One land is held in memory at a time beside the farm's; the camp's is
     let go once he is home.
5. **Home:** the drive home is the jump, then the farm as he left it, and the calendar's summary with the trip's lines
   (frame 22, already the phone's).

**C2: the falconry outing** (after T17's birds land and the man's arm is built), frames 9-12 and 20-21:
- the hooded saker on the fist;
- the cast button at the edge, which warns and does not act in a banned place or time;
- the flight and the result card;
- a lost falcon and the tracker's button.

**C3: the trapping day** (after the peregrine and the pigeon), frames 14-17:
- the binoculars' view;
- the pigeon and the net;
- the catch card, and the release.

## Questions for the owner (the proxy answers tonight; recommendation first)

1. **The far grounds' land:**
   - (a) each ground's own real land, built by `tool/terrain3d` at its coordinates, about 3 MB each, loaded during
     the drive (recommended: realism first, and size does not matter);
   - (b) the farm's land as a stand-in (the storyboard's frame 13 says so).
2. **The near grounds' land** (طرف النفود, المحازة):
   - (a) the farm's own land, with its fine rings centred on the camp so the ground is as detailed there as at the
     yard (recommended: the same real data, and no extra download);
   - (b) a separate cut like the far grounds.
3. **Getting there:**
   - (a) the calendar's jump for every ground, the engine's drive time (recommended: the approved design's way, and one
     way for all; the car is driven at the farm and at the camp);
   - (b) the near grounds driven for real in the car, 14 km on the real land, the engine's clock running.
4. **The camp's models and the room** (no photos of his for them):
   - (a) built by code now from real sizes, as provisional looks for his eye, and rebuilt from his photos if he sends
     some (recommended);
   - (b) wait for his photos.
5. **What the car does at camp:**
   - (a) parked, with him in the seat and the camp's pin in view, as in frame 7 (recommended);
   - (b) on foot beside the tent.
6. **The trapping grounds' pins** (the engine has 16, all round the kingdom; the storyboard drew two):
   - (a) every ground at its real bearing on the horizon, shown only while the trapping season is open, the map's
     overlap rule keeping them apart (recommended: real places, and out of the way for ten months);
   - (b) every ground all year;
   - (c) one pin «أراضي الطرح» opening a list.
7. **Where he picks the nights:**
   - (a) a stepper in the ground's card, «الليالي − 3 +», where 0 reads «طلعة يوم» on a ground near enough; the card
     before leaving then shows those nights (recommended: the storyboard's «الأيام: تختارها» on the ground's card);
   - (b) on the phone's card before leaving.

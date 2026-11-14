# Rushing and the calendar (task T15, part A: the design, revised after review)

Status: **a design awaiting the owner's approval**. While he sleeps his proxy answers for him, provisionally:
batches 4 and 4b in `docs/agents/proxy_decisions.md`. Nothing here is built. Once this revision is reviewed, the build
(part B) goes on the side branch and stays off his phone's build until he approves the design (batch 4, item 12).

Pictures: `design/ui/phone_rush.jpg` (drawn by `phone_rush.cjs`) and `design/ui/phone_calendar.jpg` (drawn by
`phone_calendar.cjs`). They are drawn from games the engine played (seed 4242, 1 October 2026), and from saves the
engine made (`tool/proto_engine/bin/t15_design_saves.dart`).

What the owner asked, the night of 13–14 Nov 2026 (`docs/agents/owner_instructions_2026-11-14_night.md`):

- «اي شي اسويه او ابنيه اقدر اسرعه يبني بنفس اللحظة بتكلفه اعلى»: anything he does or builds can be hurried to finish
  at once, for a higher cost.
- «بخطه مدروسه ومحكمه خليني اقدر انتقل بين المواسم بنفسي يعني تقويم وهكذا موجود اختياري»: with a well-studied, tight
  plan, he moves between the seasons himself, with a calendar that is optional.
- No errors, nothing heavy on the phone, thought through.

The two requests meet. Money hurries what money can hurry in the real world. What it cannot hurry (a pregnancy, a
calf growing, a buyer's offer, a festival's date) the player reaches by moving the calendar forward. That is the
proxy's reading of "anything" (batch 4, item 1: "anything money can really hurry"), for the owner to confirm.

Line numbers below are at the session branch's head `ff3250b` (the المزاين build included).

## 1. What takes game time after the player decides (from the code)

### Money can hurry it in the real world (rushable)

| What | Where it waits | How it is finished in a day in the real world |
|---|---|---|
| A facility being built: 3 days | `handlers.dart:654` (`doneOn = today + Balance.buildDays`), `balance.dart:213`; finished by `UpkeepSystem._finish`, `systems.dart:99-110` | Each of the game's facilities exists ready-made. A pen is welded steel panels set up on site; the 30,000 L tank is a factory-made tank brought on a lorry and set on its base; the feed store is a prefabricated steel shed or a ready shade; the caravan is driven in on a trailer; a بيت الشعر is pitched in hours; the room is a prefabricated cabin (غرفة جاهزة) lifted off a truck. A day means a second crew and work into the night. |
| An order of water or feed on its way: 1 day | `handlers.dart:596` (`arrives = today + Balance.deliveryDays`), `balance.dart:136`; delivered by `UpkeepSystem._deliver`, `systems.dart:112-143` | A tanker or a truck sent out now, not on tomorrow's round. **It only matters on a day the herd went short (section 2.2).** |
| A camel bought, on the truck: 1 day | `eligibility.dart:78-79` (`onTheWay`), `balance.dart:282`; `acquiredOn = today` on buying, `handlers.dart:114` | A second driver, so the lorry does not stop for the night. The transport authority's reported rule (2017; to confirm against the current regulation) is 9 hours of driving a day. The game's road estimate makes Tabuk to Riyadh about 17 hours at 80 km/h, and Jouf to Najran (1,804 km) longer (`balance.dart:274-281`). |

### Money cannot hurry it (not rushable; the calendar reaches it)

| What | Where | Why money cannot hurry it |
|---|---|---|
| A pregnancy: 356–410 days | `handlers.dart:917-928` (`_gestation`), `balance.dart:18-21`; the birth `systems.dart:532-580` | Biology |
| A calf growing (its ages, the 90 days of free nursing, the year's lactation, the age it can breed) | `balance.dart:34,39,46,227-241` | Biology |
| A treated camel's recovery: half to all of the illness's days | `handlers.dart:529-531`, `catalog.dart:163-215` (`recoverDays`) | Biology: the vet has already done what money buys |
| An untreated camel's illness | `systems.dart:392-404` | The vet's treatment is the hurry. It exists in the engine (`Treat`); the phone gets its first screen for it (section 7) |
| A bull's rest between coverings: 2 days | `balance.dart:49` | Biology |
| A buyer's offer on a listing (a chance each day) | `systems.dart:633-690` | A buyer's choice. The broker's quick sale (`QuickSale`) is already the "sell now, for less" |
| An offer's 3 days, a listing's 45 | `balance.dart:290-296` | Deadlines, not waits |
| A festival's days, its registration, its round's day | `world_gen.dart:203-255`, `systems.dart:892-930` | The festival's own calendar. Late entry, with its fee, is already the paid way after the closing (`balance.dart:321-322`) |
| الفحل وإنتاجه's results: 10 days of DNA tests | `balance.dart:353` | The festival's laboratory |
| Ownership registered 30 days before a round | `eligibility.dart:244`, `balance.dart:310` | A rule against buying winners. Paying past it would be fraud, so the truck's rush must not touch `acquiredOn` (section 2.3) |
| A ban from the festivals | `balance.dart:418` | A penalty |
| The seasons, the rains, the green pasture | `pasture.dart`, `balance.dart:169-186` | Weather |

### An option rather than a refusal: the vet's early pregnancy scan

The check comes 21 days after mating (`balance.dart:24`, a game choice; `BreedingSystem`, `systems.dart:487-531`).
A vet's ultrasound shows a camel's pregnancy from about day 15 to 20. That is real practice, and it tells only what
the check would tell, a few days sooner. The proxy answered yes (batch 4b, item 6, marked OUR READING):

- **Rule:** from day 15 after mating, «افحصها بالسونار» on a female awaiting her check: paid; the check's result comes
  today (`PregnancyConfirmed` or `PregnancyFailed`, the same `conceived` drawn at mating). It is no rush of biology:
  the pregnancy is what it was.
- **Fee:** SAR 300, a game choice (no price found), from cash or on account, since it is the vet.
- **For the owner:** realism may also argue for moving the ordinary check itself toward days 15 to 20. It is not
  moved here.
- **Not drawn:** the phone has no breeding screen yet. The scan's row belongs there when it comes.

## 2. Rushing: the rules

### 2.1 Common to all

- **Finishes now.** The rush command does in the handler what the daily system would have done, and emits the same
  event (`FacilityBuilt`, `SupplyDelivered`), so every screen already knows it. It emits `Rushed {what, fee}` first.
- **Two places it is offered** (batch 4, item 4):
  - on what is already under way: «استعجل» on the row;
  - at the moment of ordering or building, a line beside the normal order: «أو ابنه الحين بـ 18,000 ريال».
  - Where that line sits is the owner's eye. The pictures put it under the row's own line, in the accent colour, as
    a tappable second choice.
- **Before he confirms:** the extra cost in riyals with its word, on the row.
- **Two taps**, as الحراج's sale: the first tap turns the button red («أكّد») and the row says what it does; any
  other tap, or `SURE_FOR`, stands it down (the same guards, `phone.js`'s sure-tap code).
- **Cash only:** never on the merchant's account; refused below zero (`inDebt`) (batch 4, item 3). Not enough cash:
  the button off and the row saying so («الاستعجال 6,000 ريال، ورصيدك 193»).
- **The bank:** its own kind «الاستعجال», each line what was hurried («شبك ثاني، خلص بيومه») (item 5).
- **Prices:** every figure is a marked game choice. The Labour Law's overtime (art. 107: the hourly wage plus 50% of
  the basic wage) is about wages, so it is a reason the work costs more, not the source of a facility's whole
  price.

### 2.2 Water and feed: real only on a short day (batch 4b, item 1)

The review proved that a rushed delivery bought nothing as first designed. The order comes at the next day's start,
before the herd drinks (`UpkeepSystem.run`: `_deliver` then `_consume`, `systems.dart:76-80`), and today's ration
and water were already taken at dawn. Over 10 days the reviewer's two games came out identical.

So a rush of water or feed is offered **only on a day the herd went short**, and then it makes today good.

- **"Short today", by the engine's own fields.** `_consume` (`systems.dart:145-197`) is extended to record the day's
  account in new farm state: `today = {water: need, drunk; barley: need, eaten; alfalfa: need, eaten; dryBefore}`.
  `dryBefore` is `dryDays` before today's step. Short today means `drunk < need` for water, or `eaten < need` for
  feed; `farm.short` already says the same (`systems.dart:168-176`).
- **What a rushed delivery does** (it arrives now):
  - it is put in the tank or the store as a delivery is (`_deliver`'s own code: the tank filled to the top, the rest
    going back);
  - **Water:** the herd drinks what today's need still lacks, `x = min(need − drunk, waterL)`, and `drunk += x`. If
    `drunk ≥ need`, the day is a full day: `dryDays = 0` and `short` loses water, exactly as `_consume` treats a
    full day. Else, if `drunk ≥ need / 2`, the day holds the count: `dryDays = dryBefore`. Else nothing changes but
    the litres.
  - **Feed:** the herd eats what today's ration still lacks from each feed, and
    `fedShare = (barley eaten + alfalfa eaten) / need`; `short` loses a feed that now covers the day.
  - **Today's condition:** `CareSystem` ran at dawn with the short day. The difference is applied once to each
    camel: `condition += conditionPull × ((plan target − 35) × (fedShare′ − fedShare) + (thirstPenalty if the day
    stopped counting dry))`, clamped as Care clamps. The update is linear in its target, so this is what Care would
    have made of the corrected day. How much of the day's loss it undoes (all of today's, as here) is a game choice.
  - A camel that died of thirst at dawn stays dead. A thirst death comes from yesterday's count (`systems.dart:
    412-418`), and the rush resets the count for tomorrow: that is its real worth.
- **When the herd is not short today**, nothing is offered. The row says honestly «الطلبة العادية توصل قبل شرب حلالك
  بكرة» (water) and «… قبل علفة حلالك بكرة» (feed).
- **A played day equals a jumped day.** The rule reads only the day's record, never the minute, so a rush at 08:00 and
  at 20:00 give the same world. A jump never rushes (the player is away; a standing order covers the stores).
  Part B tests both: the same rush at two minutes gives equal states, and a game jumped to a short day then rushed
  equals one played to it then rushed.
- **Price:** water, half the tanker's price again (the 19 t: SAR 100 more; the 6 t: SAR 60). Feed, half the order's
  price again, at most SAR 300 (a truck sent alone; one bag of barley at SAR 64 costs SAR 32 more, not the first
  design's flat SAR 150). Both are game choices.
- **Cash only**, flagged for the owner (batch 4b, item 1): on a short day this rush comes close to a necessity, yet
  the ordinary delivery still comes tomorrow on the account.

### 2.3 The camel on the truck (batch 4b, item 2)

- **The camel's `acquiredOn` is not touched.** It counts the 30 days of ownership before a round
  (`eligibility.dart:244`), and moving it would make a camel bought 29 days before a round eligible.
- **New state instead:** `Camel.arrivedOn` (a `GameDay?`). `onTheWay` becomes `!homeBred && arrivedOn == null &&
  today − acquiredOn < camelTruckDays`. A rush sets `arrivedOn = today`. Until the rush is used, every camel's is
  null, so nothing else changes.
- **Price by the part of the day left:** `fee = round5(trucking × 0.5 × max(0.2, (1440 − m) / 1440))`. Here `m` is
  the game's minute of the day (`RealTimeClock.minuteOfDay()`, `time.dart:65-70`).
  - At dawn the fee is the full half of the trucking (نجمة from Hail, trucking SAR 1,069: SAR 535). At 18:00 it is
    SAR 135; the floor is a fifth of that half (SAR 105).
  - The curve and the floor are game choices.
  - The domain has no clock, so the command carries the game hour the phone showed (`Rush(actor, camel, hour)`). The
    handler accepts this hour or the one before, so a price shown is the price paid. The phone redraws the price
    when the game's hour changes (about every 8.6 real minutes), not per frame.
- **The row says** «توصل الحين بـ 535 ريال زيادة». At buying time, under «اشترها» on the listing: «أو اشترها وتوصل
  الحين بـ …».

### 2.4 Engine (part B)

- One command, `Rush(actor, target, {hour})`, where the target is a facility under construction, a delivery (on a
  short day) or a camel on the truck. A second form, `BuildFacility(..., now: true)` and `OrderSupply(..., now:
  true)` and `BuyListing(..., now: true)`, does the order and its rush in one step.
- Refusals: `notFound`, `notShortToday {supply}`, `insufficientFunds {needed}`, `inDebt {debt}`.
- `LedgerCategory.rush`; the event `Rushed`.
- **New state, so a save version (v10, the director's number):** `Camel.arrivedOn`, the farm's day record (2.2),
  the standing order and the vet's contract (section 5). The migration from v9 gives each its empty default, and is
  tested on a copy of a real saved game (batch 4, item 6's condition).
- The same seed on the VM and in JavaScript.

## 3. What goes wrong when days pass unattended (the engine's rules, measured)

`dart run tool/proto_engine/bin/unattended.dart` (seed 4242, from 1 October 2026; stores as each farm has them):

| Farm left alone | 7 days | 91 days | 365 days |
|---|---|---|---|
| The start (one nursing camel and her calf, a month of stores) | nothing | barley low on day 26, out day 30; alfalfa and water out day 31; **both camels die of thirst on day 42** | the same |
| Full farm (56 head, all facilities, 3 shepherds, tank and store full, SAR 20,000) | nothing | feed out day 18, water out day 31, **all 56 die of thirst on day 42** | the same; money below zero from day 151 |
| Full farm kept stocked | – | 6 fall ill, **1 dies untreated** | 44 fall ill, **22 die untreated** (39%) |
| Kept stocked, every illness treated | – | 5 ill, all recover | 1 calf lost (the first-year loss), **none to illness** |

The rules behind them:

- **Feed and water run out.** Nothing is ordered by itself; each day takes from the stores
  (`systems.dart:145-197`).
  - The start's 6,000 L tank and 1,000 kg shade hold about a month.
  - The full farm's 36,000 L and 11,000 kg hold about **31 days of water and 18 of feed** at 56 head.
  - There is a warning at 3 days (`balance.dart:191`, `SupplyLow`).
- **Thirst kills fast.** Past the days a camel can go without water (`balance.dart:169-174`), each dies with a chance
  that climbs 15% a day (`systems.dart:412-418`).
- **An untreated illness** kills after 10 days, with a rising chance (`systems.dart:392-404`,
  `balance.dart:88-92`). Self-recovery comes only after 25 days, at 3% a day.
- **The merchant's account** runs to a month of the herd's needs, at least SAR 5,000 (`account.dart:24-36`). Past it
  nothing is ordered, and an order is refused (`accountFull`).
- **Wages** are taken on the 1st (`systems.dart:84-96`). The engine's `CashNegative` comes only on that day. Money
  that goes below zero otherwise (a festival's trucking at judging, `systems.dart:989-991`; a fine) has no notice, so
  the jump checks the cash itself.
- **A pregnant camel calves** on her day. A nursing camel drinks 42 L, and calves can outgrow the pens (no event).
- **Offers** expire after 3 days, **listings** after 45 (`systems.dart:597-619`).
- **A festival's registration** closes 7 days before it starts; late entry runs to 72 hours before the round, at
  SAR 1,000 a head (`balance.dart:321-322`).
- **The round's day:** the round is judged at dawn and its six stages are told through the day at 7:00, 8:30, 10:00,
  12:30, 15:30 and 18:00 (`balance.dart:365`, `ContestSystem.tellDay`, `systems.dart:1232`). A day passed over is
  told all at once as the next begins (`game.dart:209-211`).
- **A treatment can be found** any day, a fine of SAR 13,400 (`balance.dart:425-443`).

## 4. What a jump costs (measured)

`tool/proto_engine/bin/jump_cost.dart` runs the daily pipeline for the stretch, then the save's encoding and the
screen's snapshot, as `EngineCore` does after a catch-up. Stores are filled so the herd lives. The machine is a shared
desktop CPU, 4 cores under load from other agents; one run each after a warm-up; the slowest day is in brackets.

| Herd | Span | VM (Dart JIT) | JavaScript (node, dart2js -O2) | Save (VM / JS) | Snapshot (VM / JS) |
|---|---|---|---|---|---|
| 2 head (the start) | 7 days | 3.6 ms | 1 ms | – | – |
| | 91 days | 14 ms | 23 ms | 5 ms / 5 ms | 4 ms / 3 ms |
| | 365 days | 39 ms (1.0) | 61 ms (3) | 5 ms / 5 ms | 4 ms / 3 ms |
| 56 head (the full farm) | 7 days | 1 ms | 2 ms | | |
| | 91 days | 13 ms | 21 ms | 4 ms / 3 ms | 3 ms / 4 ms |
| | 365 days | 68 ms (1.7) | 80 ms (3) | 7 ms / 5 ms | 4 ms / 4 ms |
| 10,000 head (ADR 0004's most) | 7 days | 59 ms (10.8) | 216 ms (41) | 201 ms / 456 ms | 127 ms / 197 ms |
| | 91 days | 832 ms (31.9) | 2.2 s (37) | 257 ms / 419 ms | 63 ms / 129 ms |
| | 365 days | 2.5 s (17.9) | 7.7 s (41) | 175 ms / 419 ms | 32 ms / 93 ms |

The save at 10,000 head is 6.8 MB; at 56 head it is 0.16 MB. The event counts agree between the VM and JavaScript.
To repeat: `dart run tool/proto_engine/bin/jump_cost.dart`, and
`dart compile js -O2 tool/proto_engine/bin/jump_cost.dart -o jc.js && node jc.js`.

**On his phone (estimated, not measured).** His iPhone prototype runs the engine as JavaScript in a Web Worker, so
the JavaScript column is the one to scale. A mid-range phone's core is about two to three times slower than this
desktop. That puts **a year at 10,000 head at about 15 to 25 s**, a season at 4 to 7 s, and a year at the game's 56
head at 0.2 to 0.3 s. The proxy's condition stands: a year's jump stays, with the progress view and «وقّف هنا»
working at any moment, and is on the owner's list of phone tests, with a season's cap as the fallback (batch 4b,
item 7).

- The work runs where the catch-up runs: the Worker, or the app's isolate (ADR 0002), never the UI thread. It goes in
  6 ms slices with a yield between them (`engine_core.dart:300`).
- **The 3D world is not drawn while the phone is open**, so a jump adds no frame work. The progress view is redrawn
  on the engine's progress pushes only, at most four a second.
- One save at the end. The summary is counted as it runs, never kept as a list of events (14,216 at 10,000 head over
  a year).
- The longest jump is a year, the catch-up's own cap (`engine_core.dart:32`).

## 5. The one mechanism for being away

The calendar's jump, and later the hunting camp of days and a falcon outing of days (the owner said tonight that an
outing may last days), all use one mechanism. Hunting is not built; it will call this.

`EngineCore.away(AwayPlan plan) → AwayResult`. `Game` holds the part with no clock: `Game.runAway(plan, onDay)`.

- **The plan:**
  - a target day;
  - the stops, as conditions on the game's state, checked after each simulated day;
  - a landing minute of the day (06:00 for the calendar);
  - extra conditions a caller adds (the hunt: its outing's own end; his falcon's daily care, a named hook
    `AwayStop.falconCare`, empty until hunting is built).
- **The loop:** the catch-up's own loop over `advanceDays(1)`, yielding every 6 ms. After each day:
  - the day's events go to the summary's counters;
  - the stop conditions are read from the state (and the day's events where the state cannot tell);
  - the cancel flag is checked;
  - the loop ends at the first stop, at the target, or on cancel.
- **The cancel flag, outside the queue.** `EngineCore._serial` queues every operation, and the worker queues every
  message but `'stored'` (`worker_host.dart:108`). So `stopAway()` is not an operation: it sets `_cancelAway = true`
  directly. `WorkerHost.receive` handles `op: 'stopAway'` at once, beside `'stored'`, and the app's isolate does the
  same in its port listener. The loop yields every slice, so the message lands within about 6 ms of work, and the
  jump ends at the end of the day it is on.
- **Progress pushes:** `AwayProgress {day, done, total}`, at most four a second.
- **Landing:** the clock's anchor is moved so that the real now is the landing minute of the day the jump ended on.
  The sum is in the clock's own microseconds, because a game day is `L = Duration.microsecondsPerDay ~/ 7 =
  12,342,857,142 µs` and 86,400,000 / 7 ms is not whole:
  - `elapsed = (D − startedOn) × L + ceil(m × L / 1440)`, with `D` the day landed on and `m` the landing minute;
  - `clockShiftMs = floor((nowµs − startedAtµs − elapsed) / 1000)` (floor: the elapsed time comes out at most 1 ms
    long, so the minute stays `m`).
  - Then the ordinary catch-up and `tellTo(minuteOfDay)` go on from there. Landing at 06:00 means no stage of a round
    is told until 07:00, as on any played day.
- **One save at the end, then marked good** (`store.markGood()`, as `_start` and `newGame` do,
  `engine_core.dart:126,143`). Otherwise `openPrevious` would open the world before the jump with its old anchor, and
  a jump could be undone to use what it revealed.
- **The result:** `AwayResult {from, to, target, stop: {kind, day, subject}?, summary: {milk, spent by kind, births,
  illnesses, recoveries, deaths by cause, deliveries, built, registrations, offers, wages}}`. The phone draws the
  stop card and the summary from it.
- **Refused:** a target not after today or more than 365 days ahead; a camel sick and untreated, unless a vet's
  contract is in force (batch 4, item 9); his round's day being told today (the go button waits for the day's end).
- **Online later:** the server owns the clock (ADR 0001), so this is the single-player game's.

## 6. The calendar

### The app

«التقويم», the ninth app on the home screen, after the eight now built (the six, المزاين, المحادثات) (batch 4, item
11). It is optional in every sense: a player who never opens it plays the game as it is. It adds no work to a day of
the engine and nothing to a frame, and writes nothing over the game.

- **The year** (view 2): twelve month strips from this month, read right to left as the phone reads.
  - The past pale and today a mark.
  - The breeding season (November to April, `balance.dart:30`) a green line.
  - Each festival's registration (light) and its days (amber), from the engine's festivals.
  - His dated things: a confirmed pregnancy's due day (red), a milking's end (blue).
  - The hunting season is not built; the strips have room for its band.
- **What is coming** (view 3): the same things as rows, each a target. Also a ban's end and a listing's expiry when
  he has them.
- **A day or season picked** (view 4): its month as a grid, the day ringed, what is on it, «امشِ لين …».

### The card before the jump (views 5 and 6)

- **The days each store lasts** against the days asked, from today's need, with a button that fills it by the phone's
  own order. For water it says, as الوايت does, that part of a tanker goes back unpaid when the tank is near full.
  The figures say «تقريبًا»; the card never runs the engine forward, since that would tell an illness before it came.
- **What he can set before leaving:**
  - the standing order (yes, batch 4, item 6): set in الوايت and العلف. When a store comes down to its last 3 days the
    supplier sends a top-up, paid as an order (cash, then the account);
  - the vet's contract (yes, item 7): in العزبة. SAR 1,000 a month and SAR 20 a head (a game choice, told to him), and
    each illness treated the day it comes at the vet's own price, on account as the vet is;
  - shepherds, the ration and the calf's share: already in the engine.
- **What falls due on the way:** the breeding season and who can be bred (by `Eligibility.femaleCanBreed`,
  `eligibility.dart:25-55`); the festivals in the stretch and his entries; his round's day; the milk's money a day;
  wages on each 1st against the cash; a calving due.
- **A warning when the herd will outgrow its pens** (a calving due with the pens full).
- **What stops it**, so nothing surprises him; and that everything else runs and is told at the end.
- **A sick camel:** the go button waits until she is treated («عالجها» on the card), unless a vet's contract is in
  force.
- **Forward only:** «التقويم يمشي لقدام بس: الأيام اللي تمضي ما ترجع.» The go button takes two taps.

### Under way (view 7)

The day reached, a bar, the days done of the stretch, the milk's money so far, the stores' days. «وقّف هنا» ends it at
the day reached (section 5's flag), at any moment. With a large herd the screen says it may take seconds.

### The stops: conditions on the state after each day

| Stop | Condition after the day | What the stop card offers |
|---|---|---|
| A camel falls ill (no vet's contract) | a camel of his is `sick` and was not yesterday | «عالجها» (section 7) |
| A camel dies of illness or thirst | `Died` with cause illness or thirst today | look at the herd |
| A store at 3 days, or a day gone short (no standing order) | days left ≤ 3 with nothing on its way, or `farm.short` not empty | «اطلب وايت» / «اطلب علف»; on a short day the rush |
| Money below zero | `cash < 0` and it was not at the jump's start or the last check | البنك |
| The account at its limit, or an order or treatment refused | `onAccount ≥ Account.limit` first reached, or a standing order or the contract refused | sell or pay; البنك |
| A fine or a ban, for any cause | `TamperingFound`, `SaleRefused`; `bannedThrough` moved | what was found and the fine |
| An offer on his listing | `OfferReceived` | الحراج's listings, and when the offer runs out («السوم ينتهي بعد يومين») |
| **His round's day** | a round with his entry has `day == today` (judged at dawn, `told == 0`) | **lands at 06:00**, before the first stage at 07:00; «شوف يوم الشوط» opens المزاين's day, told stage by stage |
| A registration closing in 3 days (batch 4b, item 3) | a festival's `closesOn − today == 3`, he has no entry, and one of his camels passes `Eligibility.canEnter` for one of its single rounds; once a festival | المزاين's festival page |
| The breeding season opens (item 4) | the season's first day and a female passes `Eligibility.femaleCanBreed`; once a year | the herd |
| The herd outgrows its pens (item 5) | head > capacity, first time | العزبة, «ابنِ شبك» |
| His falcon's care (when hunting is built) | the named hook `falconCare` | – |

Not stops, told at the end: births and calves lost, pregnancies confirmed or failed, recoveries, deaths of old age
and the calves' first-year losses, wages, deliveries, facilities finished, listings expired, registrations opening.

If the herd-outgrowing stop cannot be built tonight, the card's warning and a summary line stay, and the stop is
listed as owed to the owner (batch 4b, item 5).

**How often it stops.** `dart run tool/proto_engine/bin/unattended.dart stops` plays a jump with these stops; at each
stop the "player" does what it asks (treats, fills by orders) and goes on. The standing order and the vet's contract
are now charged as the engine would charge them (the first table filled the stores for free and cleared the account
before each treatment, the review). The full farm has SAR 400,000 (its year costs about 370,000) and 10,000 head has
20 million and a month of stores: test amounts, so that the stops are the farm's and not an empty purse's.

| Farm, a jump of | 91 days | 365 days |
|---|---|---|
| The start | 4 (2 registrations, 2 stores) | 21 (5 registrations, 14 stores, 2 illnesses) |
| Full farm | 14 (4 registrations, 6 stores, 4 illnesses, the breeding season) | 80 (8 registrations, 41 stores, 32 illnesses, breeding, crowded) |
| Full farm, standing order | 9 (4 registrations, 4 illnesses, breeding) | 42 (8, 32 illnesses, breeding, crowded) |
| Full farm, vet's contract | 10 (4 registrations, 6 stores, breeding) | 50 (8, 41 stores, breeding, crowded) |
| Full farm, both | **5** (4 registrations, breeding) | **10** (8 registrations, breeding, crowded on day 178) |
| 10,000 head, standing order | 90: an illness **every day** | – |
| 10,000 head, both | **5** (4 registrations, breeding) | – |

So with both conveniences, the stops left are the ones he would want: a registration he could still make, the
breeding season, the pens full. Without them a full farm stops every week or so, and a large herd cannot get past a
day.

**In the drawn game** (seed 4242 from 1 October, target المربعانية's first day, 7 December, 67 days):
- The card offers a 6 t tanker (SAR 120: water for about 115 days) and 2 bags and 12 bales (SAR 452: barley for
  about 48 days, alfalfa 53), so it says the jump will stop about 15 November.
- Played on the fast clock with those orders, the engine's first store stop came on Sunday 15 November (barley,
  3 days left).
- The milk had brought SAR 851, three orders had come, three festivals had opened registration, nothing fell ill.
- (That run predates the registration stop. With it, the jump would first have stopped on 8 October, three days
  before مزاين حائل's registration closed, since نورة could enter. The drawn stop is kept because it shows a store
  stop; the registration stop is drawn from the round's save.)

### At the end (view 9)

What happened, from the engine's events and ledger, in the phone's words: the days and dates, the milk's money, what
was delivered, who fell ill, recovered or died, calves born, festivals opened, a ban ended or a listing expired, and
why it stopped. The details are in البنك and the herd.

## 7. The vet's screen (the phone's first «عالجها»)

The engine has `Treat` (`handlers.dart:509-549`), and the map's camel card says «مريضة، تبي علاج» (farm.html), but
nothing in the game sends it. The calendar's stop and the wait on the go button need it, so it is part of this
design.

- **Where:** in العزبة, a section «يبي علاج» at the top when any of his camels is sick, one row each. The calendar's
  card and stop show the same row. The map's camel card can carry the same button later.
- **The row:** the camel and her illness («الفريدة · إسهال الحيران»); since when; the vet's price today; how long she
  takes to recover, from the illness's days (half to all of `recoverDays`: «تطيب بـ 3 إلى 6 أيام»); and «عالجها». One
  tap, as an order, since it is a necessity and not irreversible harm.
- **The price:** `Treat` draws it from the illness's range with the day's keyed randomness (`handlers.dart:518-520`).
  The snapshot carries today's quote, worked out with the same key, so the phone shows the exact price the vet will
  ask today. A quote is no hidden value: a vet names his price.
- **Money:** from cash, else on the merchant's account to its limit (the owner's decisions 9 and 10), with the
  account's line under the row as العلف has it. Past the limit: «حساب التاجر وصل حده…».
- **Untreated:** the row says plainly what waiting does («لو تركتها بعد 10 أيام ممكن تموت»).
- **The vet's contract** row under it: «عقد البيطري · 1,000 ريال بالشهر و20 للراس · يعالج اللي يمرض بيومه»
  «اتعاقد».
- **In the drawn game:** seed 4242 kept by its orders; الفريدة, نورة's calf born 28 March, fell ill with إسهال
  الحيران on 8 May 2027. The engine's own Treat on a copy priced it at SAR 500, recovery 13 May.

## 8. Decisions (the proxy's, provisional) and what is still the owner's

Batches 4 and 4b in `docs/agents/proxy_decisions.md`:

- **Not rushed:** what money cannot hurry (our reading of "anything").
- **Prices:**
  - a facility: half again, pro rata to the days left (now: ×1.5 at ordering);
  - water: +50% of the tanker; feed: +50% of the order, at most SAR 300 (revised from a flat 150), both only on a
    short day;
  - the truck: by the part of the day left.
  - All are game choices.
- **Money and display:** cash only (flagged on a short day); the rush on what is under way and at ordering; its own
  kind in البنك.
- **Build:** a standing order and a vet's contract are built, with the save's migration tested on a real save; the
  stops as in section 6; a year's jump, phone-tested; «التقويم» the ninth app; built on a side branch, off his phone
  until he approves.
- **Waiting for him:** the design itself; the invented prices and the contract's fee; the two flags (a short day's
  rush cash only; moving the ordinary check toward days 15 to 20); the phone test of a long jump; his word to put the
  build on his phone.

## 9. GDD rows to add in part B (Arabic, as the GDD is written)

- الاستعجال: اللي ينبني أو بالطريق يخلص الحين بسعر أعلى، ويقدر يختاره وقت الطلب بعد:
  - المنشأة نص سعرها زيادة لو باقي لها 3 أيام، وأقل كل ما قربت **(اختيار لعب)**. كل منشأة تنقام بيوم بطاقم ثاني
    وشغل بالليل: الشبوك ألواح حديد تنلحم، والخزان جاهز ينزل من اللوري، والمستودع هنجر جاهز، والكرفان ينسحب،
    وبيت الشعر ينصب بساعات، والغرفة غرفة جاهزة.
  - الوايت والعلف المستعجل بس لو الحلال ما شرب أو ما شبع اليوم: يوصل الحين ويكمل نقص اليوم، وما ينحسب اليوم عطش
    أو جوع. الوايت نص سعره زيادة، والعلف نص سعر الطلب زيادة لين 300 ريال **(اختيار لعب)**.
  - الناقة على اللوري توصل الحين بسواق ثاني، بنص نقلها زيادة أول النهار، وينقص كل ما مضى من اليوم لين خمس ذاك
    **(اختيار لعب)**، وتاريخ تملكها ما يتغير.
  - كله من الرصيد بس.
- التقويم: تطبيق اختياري في الجوال، يوري السنة ويمشي اللعبة لقدام لين يوم يختاره اللاعب، ويوقف لو صار شي يبيه،
  ويوصل الساعة 6 الصبح **(اختيار لعب)**.
- الطلب الثابت: المورّد يرسل علف أو وايت لما يقرب المخزون يخلص (3 أيام)، ويندفع مثل أي طلب **(اختيار لعب)**.
- عقد البيطري: 1,000 ريال بالشهر و20 للراس، ويعالج اللي يمرض بيومه بسعر العلاج **(اختيار لعب)**.
- سونار الحمل: من اليوم 15 بعد التلقيح، بـ 300 ريال **(واقعي الفحص، والسعر اختيار لعب)**.

# Rushing and the calendar (task T15, part A: the design)

Status: **a design awaiting the owner's approval** (through his proxy while he sleeps). Nothing here is built.
Pictures: `design/ui/phone_rush.jpg` (drawn by `phone_rush.cjs`) and `design/ui/phone_calendar.jpg` (drawn by
`phone_calendar.cjs`), from games played in the engine (seed 4242, 1 October 2026).

What the owner asked, the night of 13–14 Nov 2026 (`docs/agents/owner_instructions_2026-11-14_night.md`):

- «اي شي اسويه او ابنيه اقدر اسرعه يبني بنفس اللحظة بتكلفه اعلى»: anything he does or builds can be hurried to finish
  at once, for a higher cost.
- «بخطه مدروسه ومحكمه خليني اقدر انتقل بين المواسم بنفسي يعني تقويم وهكذا موجود اختياري»: with a well-studied, tight
  plan, let him move between the seasons himself: a calendar, optional.
- No errors, nothing heavy on the phone, thought through.

The two meet: what money can hurry in the real world is rushed; what it cannot (a pregnancy, a calf growing, a
buyer's offer, a festival's date) is reached by moving the calendar forward.

## 1. What takes game time after the player decides (from the code)

Line numbers are at the base commit `ab17668`.

### Can be hurried by money in the real world (proposed: rushable)

| What | Where it waits | Real way to hurry it |
|---|---|---|
| A facility being built: 3 days | `handlers.dart:652` (`doneOn = today + Balance.buildDays`), `balance.dart:254` (`buildDays = 3`), finished by `UpkeepSystem._finish`, `systems.dart:95-107` | The contractor works nights and brings a second crew, at the overtime rate (Saudi Labour Law art. 107: the hourly wage plus 50% of the basic wage) |
| An order of water on its way: 1 day | `handlers.dart:594` (`arrives = today + Balance.deliveryDays`), `balance.dart:136` (`deliveryDays = 1`), delivered by `UpkeepSystem._deliver`, `systems.dart:109-140` | A tanker sent out now instead of on tomorrow's round |
| An order of feed on its way: 1 day | the same lines as water | A truck sent today for the one order |
| A camel bought, on the truck: 1 day | `eligibility.dart:78-79` (`onTheWay`: `today - acquiredOn < camelTruckDays`), `balance.dart:282` (`camelTruckDays = 1`); set on buying, `handlers.dart:111-115` (`acquiredOn = today`) | A second driver, so the lorry does not stop for the night: a lorry driver's day is 9 hours of driving (the transport authority's rule as reported in 2017; to confirm against the current regulation) and the longest trip in the game is about 17 hours (`balance.dart:274-279`) |

### Cannot be hurried by money (proposed: not rushable; the calendar reaches them)

| What | Where | Why money cannot |
|---|---|---|
| The pregnancy check: 21 days | `handlers.dart:486,498`, `balance.dart:24`; `BreedingSystem`, `systems.dart:494-519` | Biology: a scan shows nothing before the embryo is there; the 21 days are already the early check (a game choice) |
| A pregnancy: 356–410 days | `handlers.dart:859-870` (`_gestation`), `balance.dart:18-21`; the birth `systems.dart:520-571` | Biology |
| A calf growing (ages, the free nursing's 90 days, the year's lactation, breeding ages) | `balance.dart:34,39,46,182-185,195-205` | Biology |
| A treated camel's recovery: half to all of the illness's days | `handlers.dart:527-529`, `catalog.dart:160-210` (`recoverDays`), `systems.dart:396` | Biology: the vet has already done what money buys |
| An untreated camel's illness | `systems.dart:383-395` | The vet's treatment is the hurry, and it exists (`Treat`) |
| A bull's rest between coverings: 2 days | `balance.dart:49` | Biology |
| A buyer's offer on a listing (a chance each day) | `systems.dart:643-683` (`MarketSystem`, buyers) | A buyer's choice. The broker's quick sale (`QuickSale`) is already the "sell now, for less" |
| An offer's 3 days, a listing's 45 | `balance.dart:288-296` | They are deadlines, not waits |
| A festival's days, its registration window, its round's day | `world_gen.dart:203-255` (`seasonPlan`, `planSeason`), `systems.dart:876-910` | The festival's own calendar. Late entry after the closing, with its fee, is already the paid way (`balance.dart:322-325`) |
| الفحل وإنتاجه's results: 10 days of DNA tests | `balance.dart:363` (`dnaDays`) | The festival's lab, not the player's |
| Ownership registered 30 days before a round | `balance.dart:309` | A rule against buying winners: paying past it would be fraud |
| A ban from the festivals (this edition and five more) | `balance.dart:400` | A penalty |
| A treatment's effect wearing off | `tampering.dart:38-113` (`lastsDays`) | Not a wait the player wants shortened |
| The seasons, the rains, the green pasture | `pasture.dart`, `balance.dart:180-186` | Weather |

The owner said "anything I do or build", and realism comes first: what money cannot hurry is put to him as a
question (Q1), with the recommendation that it is not rushed and that the calendar gets him there.

## 2. Rushing: the rule

- **Finishes now.** A rush command completes the thing in the handler at once, the same as the daily system would
  have done it: a facility stands (its room, tank or store added, `FacilityBuilt`), an order is delivered
  (`SupplyDelivered`, the tank filled to the top and the rest going back), a camel arrives (her `acquiredOn` moved so
  `onTheWay` is false). The events are the ones the day would have made, so every screen already knows them.
- **The price (a game choice, Q2):**
  - a facility: half its price for the three days, less as it nears its end: `price × 0.5 × days left / 3`, to the
    500 (the second pen with three days left: SAR 6,000; with one day left: SAR 2,000). Night work and a second crew
    at the overtime rate (art. 107's +50%) on the work;
  - a water tanker: half its price again (the 19 t one: SAR 100 more; the 6 t one: SAR 60);
  - a feed order: SAR 150 for the trip, whatever it carries (a truck sent today; the 6 t tanker adverts' SAR 100 to 150
    in Riyadh are essentially a short trip's price, research section 7);
  - a camel on the truck: half the trucking again, to the riyal's five (نجمة from Hail, trucking SAR 1,069: SAR 535).
- **Where it is offered:** on what is already under way: the building row in العزبة, the order on its way in الوايت
  and العلف, the camel on the truck in الحراج's answer card (Q4). One mechanic: what is on its way can be hurried.
- **What the player sees before he confirms:** the extra cost in riyals with its word on the row
  («يخلص بعد 3 أيام · الحين بـ 6,000 ريال زيادة»).
- **Two taps:** it cannot be undone, so it is asked twice, as الحراج's sale is: the first tap turns the button red
  («أكّد») and the row says what it does («يخلص الحين، وتدفع 6,000 ريال زيادة»); any other tap, or `SURE_FOR`, stands
  it down. The same guards as the sale (`phone.js:1049-1069`).
- **Money:** a rush is no necessity, so it is paid from cash only, never on the merchant's account (the owner's
  decisions 9 and 10: the account is for feed, water and the vet). Not enough cash: the button off and the row saying
  so («الاستعجال 6,000 ريال، ورصيدك 193»); below zero: `inDebt`, as building is (Q3).
- **The bank:** its own kind, «الاستعجال», each line what was hurried («شبك ثاني، خلص بيومه») (Q5).
- **Engine (part B):** one command, `Rush(actor, what)` with `what` a facility under construction, a delivery or a
  camel on the truck; refusals `notFound`, `insufficientFunds {needed}`, `inDebt {debt}`; one event
  `Rushed {what, fee}` before the thing's own event; `LedgerCategory.rush`. No new state, so no save version for
  rushing itself. Same seed on the VM and in JavaScript (a command like the others).

## 3. What goes wrong when days pass unattended (the engine's rules, measured)

Measured with `tool/proto_engine/bin/unattended.dart` (seed 4242, the game's start on 1 October 2026):

| Farm left alone | 7 days | 91 days | 365 days |
|---|---|---|---|
| The start (one nursing camel and her calf, a month of stores) | nothing | barley low on day 26, out day 30; alfalfa and water out day 31; **both camels die of thirst on day 42** | the same |
| Full farm (56 head, all facilities, 3 shepherds, tank and store full) | nothing | feed out day 18, water out day 31, wages on the 1st, **all 56 die of thirst on day 42** | the same; money below zero from day 151 (wages) |
| Full farm, kept stocked (a standing order) | – | 6 fell ill, **1 died untreated**; wages | 44 fell ill, **22 died untreated** (39%); money below zero from day 182 |
| Kept stocked, and every illness treated (a vet's contract) | – | 5 ill, all recovered | 1 calf lost (the first-year loss), **none to illness** |

The rules behind them, from the code:

- **Feed and water run out.** Nothing is ordered by itself; each day takes the ration and the water from the stores
  (`systems.dart:142-198`). The stores hold little: the start's 6,000 L tank and 1,000 kg shade about a month; the
  full farm's 36,000 L and 11,000 kg about **31 days of water and 18 of feed** at 56 head. A warning at 3 days
  (`balance.dart:191`, `SupplyLow`), another when a day goes short.
- **Thirst kills fast.** Past the days a camel can go without water (7 in summer, 8 in spring and autumn, 10 in
  winter, longer on green pasture: `balance.dart:169-174`), each camel dies with a chance that climbs by 15% a day
  (`systems.dart:400-407`): the whole herd goes within a few days.
- **An illness left untreated** kills after 10 days with a rising chance (`systems.dart:383-395`,
  `balance.dart:86-92`); a camel recovers by herself only after 25 days, at 3% a day. About half an illness a camel a
  year, more in the peak months (`balance.dart:80-84`).
- **The merchant's account** (feed, water, the vet) runs to a month of the herd's needs, at least SAR 5,000
  (`account.dart:24-36`); past it nothing more is ordered and the herd starves.
- **Wages** are taken on the 1st, below zero if need be (`systems.dart:76-92`, `CashNegative`); below zero no camel is
  bought and nothing built (`handlers.dart:56-62`).
- **A pregnant camel calves** on her day whatever the player does (`systems.dart:520-571`); a thin dam loses more
  calves (`balance.dart:54-55`), and a nursing camel drinks 42 L, so a calving shortens the water's days.
- **Offers expire** after 3 days (`balance.dart:295`, `systems.dart:617`), a listing after 45 (`systems.dart:597-615`).
- **A festival's registration closes** 7 days before it begins; late entry runs to 72 hours before the round, with
  SAR 1,000 a head (`balance.dart:322-325`). **The round's day** judges the entry at the day's start
  (`systems.dart:895-905`); the phone tells it stage by stage through the day (wt/t10's design). A jump over the day
  would leave the player only the result.
- **A treatment can be found** outside the festivals any day, more while the camel is listed (`systems.dart:723-826`,
  `balance.dart:404-408`): a fine of SAR 13,400.

## 4. What a jump costs (measured)

`tool/proto_engine/bin/jump_cost.dart`: the engine's own daily pipeline for each day of the stretch, then the save's
encoding and the screen's snapshot, as `EngineCore` does at the end of a catch-up (`engine_core.dart:261-317`).
Stores filled, so the herd lives. This machine (a shared desktop CPU, 4 cores under load from other agents), one run
each, after a warm-up; the slowest day in brackets.

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

The save at 10,000 head is 6.8 MB; at 56 head 0.16 MB. The events counts match between the VM and JavaScript (192,
3,721 and 14,216 at 10,000 head), the same seed giving the same world.

To repeat: `dart run tool/proto_engine/bin/jump_cost.dart` from the repository (PATH with /opt/flutter/bin and its
dart-sdk/bin), and `dart compile js -O2 tool/proto_engine/bin/jump_cost.dart -o jc.js && node jc.js`.

What it means for the phone (not measured on a phone: the owner's mid-range phone is not here):

- The game today lets a farm hold 56 head (GDD 4.1): **a year's jump is under a tenth of a second** of the engine's
  time on this desktop; a mid-range phone's core is perhaps two to three times slower (an estimate), well under a
  second. At the 10,000 head the engine allows, a year is 2.5 s on the VM here, so perhaps 5 to 8 s on the phone's
  isolate, the screen showing the days as they go.
- The work runs where the catch-up already runs: the engine's isolate on the phone (ADR 0002), the Web Worker in the
  prototype, never the UI thread; in slices of 6 ms with a yield between (`engine_core.dart:296-300`), so a command
  or a stop never waits behind it. **The 3D world is not drawn while the phone is open** (design/ui/README.md:
  «The 3D view stops drawing while the phone is open»), so a jump adds no frame work. The phone's progress screen is
  redrawn on the engine's progress pushes only (`CatchUpProgress`), at most a few times a second.
- One save at the end, not one a day (the catch-up already does this). Memory: the save's string once (6.8 MB at
  10,000 head, as any save); the jump's summary is counted as it goes (a few numbers and names), never a list of
  every event (14,216 at 10,000 head over a year).
- Heat: a few seconds of one core at the very largest herd, once per jump; nothing between jumps. A jump is not
  repeated by itself.
- The longest jump is a year, the catch-up's own cap (`engine_core.dart:52-55`, `maxCatchUpDays = 365`).

## 5. The calendar

### The app

«التقويم», the ninth app on the home screen (after the six, المزاين and المحادثات). Optional in every sense: a player
who never opens it plays the game as it is; it adds no work to a day of the engine and nothing to a frame; nothing
written over the game.

- **The year** (view 2): the twelve months from this one, each a strip of its days: the past pale, today a mark; the
  breeding season (November to April, `balance.dart:28`) a green line; each festival's registration window (light)
  and its days (amber), from the engine's own festivals (`Festival.opensOn/closesOn/startsOn/endsOn`); the player's
  own dated things: a pregnant camel's due day (`Camel.dueOn`, red), a milking's end (a year from calving, blue). The
  Najdi seasons by their days (phone.js's table). The hunting season is not built: the strips have room for its band.
- **What is coming** (view 3): the same things as rows by their day, each a target: «يبدأ وقت الضراب»،
  «تسجيل مزاين الجوف يقفل»، «مهرجان المزاين الكبير»، «المربعانية»، «حليب نورة يخلص»، «نورة تولد».
- **A day or season picked** (view 4): its month as a grid, the day ringed, what is on it, «امشِ لين …».

### The plan for a jump

**Before** (views 5 and 6), a card that says honestly what the stretch needs:

- The days each store lasts against the days asked, from today's need («الماء · يكفي 30 يوم»), and a button that
  fills it before leaving with the phone's own order (the tanker that fits; bags and bales in the ration's mix up to
  the shade's room), with what it costs and how long it then lasts («ويصير يكفي 115 يوم تقريبًا: يكفي»). If even
  full it cannot last, the card says when the jump will stop for an order («يوقف التقويم حوالي 15 نوفمبر عشان
  تطلب»). The figures are reckoned from today's need and say «تقريبًا»: the card never runs the engine forward to
  know (it would tell an illness or a death before it came).
- What falls due on the way: the breeding season's start and who can be bred; the festivals in the stretch and his
  entries; the milk's money a day; the wages on each 1st and whether the money covers them; a camel due to calve.
- What stops the jump (listed so nothing surprises him), and that everything else runs by itself and is told at
  the end.
- A camel sick and untreated when he leaves: the go button waits until she is treated (Q9).
- Forward only: «التقويم يمشي لقدام بس: الأيام اللي تمضي ما ترجع.» The go button takes two taps.

**Under way** (view 7): the day reached, a bar, the days done of the stretch, the milk's money so far, the days the
stores have left; «وقّف هنا» stops it at the day reached (the days passed stay passed).

**When it stops early and hands the game back** (view 8), at the first of these in a day's events (Q8):

| Stop | The engine's event | What the card offers |
|---|---|---|
| A camel falls ill | `FellSick` | «عالجها» (the vet, on the account as now) |
| A camel dies of illness or thirst | `Died` (cause illness, thirst) | look at the herd |
| A store comes down to 3 days, or a day goes short | `SupplyLow` | «اطلب وايت» / «اطلب علف» |
| Money goes below zero (the first time in the jump) | `CashNegative` | the bank |
| An offer on his listing (it lasts 3 days) | `OfferReceived` | الحراج's listings |
| His round's day | a round with his entry reaching its day (`Placed`, `EntryRemoved`, `DisqualifiedSick`, `ResultsPending` that day) | the day, told stage by stage (wt/t10) |
| A treatment found on his camel | `TamperingFound`, `SaleRefused` | what was found and the fine |

Not stops, told at the end: births and calves lost, pregnancies confirmed or failed, recoveries, deaths of old age
and the first-year losses of calves (routine at a large herd: 14 in 91 days at 10,000 head), wages, deliveries,
facilities finished, listings expired, festivals' registration opening.

How often it stops (`unattended.dart stops`, the "player" doing what each stop asks and going on):

| Farm, a jump of | 91 days | 365 days |
|---|---|---|
| The start | 2 stops (stores) | 16 (14 stores, 2 illnesses) |
| Full farm | 14 (8 stores, 4 illnesses, 2 money) | 42 |
| Full farm, standing order | 4 (illnesses) | 39 |
| Full farm, vet's contract | 8 (6 stores, 2 money) | 45 |
| Full farm, both | **0** | 8 (money, 1 death) |
| 10,000 head, standing order | 90: an illness **every day** | – |
| 10,000 head, both | 16 (deaths of old age and calves, money) | – |

So a calendar with only what the engine has today works for a small farm and stops every week or two at the full
one; at a large herd it cannot get past a day without a vet's contract. Hence Q6 and Q7.

**In the drawn game** (seed 4242 from 1 October, the target المربعانية's first day, 7 December, 67 days): the card
offers a 6 t tanker (SAR 120: water for about 115 days) and 2 bags and 12 bales (SAR 452: barley for about 48 days,
alfalfa 53), so it says the jump will stop about 15 November. Played on the fast clock with those orders and nothing
else, the engine's first stop came on Sunday 15 November: `SupplyLow` barley, 3 days left, on day 45; the milk had
brought SAR 851, three orders had come, three festivals had opened their registration, nothing fell ill.

**At the end** (view 9): what happened, by the engine's events and ledger, in the phone's words: the days and dates,
the milk's money, what was delivered, who fell ill and recovered or died, calves born, festivals opened, and why it
stopped if it did; the details in البنك and the herd.

**What the player can set before leaving:** today only what the engine has: orders placed ahead (filling the stores,
on the card), shepherds (`SetShepherds`, already in the engine), the calf's share of milk, the ration. Proposed
(questions): a standing order and a vet's contract.

### Engine (part B), as proposed

- `EngineCore.jumpTo(GameDay target)`: serialised like every operation; refuses a day not after today or more than
  365 ahead, or while a camel is sick untreated (Q9); runs the catch-up loop on the same pipeline day by day,
  yielding as now, checking each day's events against the stops; at a stop or the target it moves the clock's anchor
  back by the days jumped (`state.clockShiftMs -= days × 86,400,000 / 7`, the inverse of the cap's shift at
  `engine_core.dart:281`), so real time goes on from the new day at 7× and the world does not wait for the clock;
  saves once; pushes `JumpProgress {done, total}` and then `JumpEnded {from, to, target, stop?, summary}`.
- `stopJump()`: ends it at the day reached.
- The summary is counted from the events as they come (counts and a few names); the inbox's bounded history
  (`game_state.dart:171-177`) is not used for it.
- Rushing: `Rush` as in section 2.
- Save: the jump adds no state (the clock's shift already exists). A standing order or a vet's contract would add
  state and a save version (the director to name the number: wt/t10 takes v9).
- Online later: the server owns the clock (ADR 0001), so the calendar would show the year and not move time; the
  jump is the single-player game's.

## 6. Questions for the owner's proxy (recommendation first)

**Q1. What money cannot hurry in the real world** (a pregnancy, a calf growing, a recovery, a buyer's offer, a
festival's dates, the DNA results, the 30 days of ownership before a round).
- **A (recommended):** not rushed. The calendar is how the player gets to them sooner; the broker is the "sell now";
  late entry is the paid way after a closing. Realism first: paying to shorten a pregnancy is not the real thing.
- B: rushed at a price anyway (the owner's "anything"): unrealistic, and it would make the festivals' rules and the
  breeding seasons meaningless.

**Q2. The rush's price** (a game choice; no source prices a rush).
- **A (recommended):** half again: a facility `price × 0.5 × days left / 3` to the 500 (art. 107's overtime +50%),
  a water tanker +50%, a camel's trucking +50% (a second driver), a feed order SAR 150 for the trip.
- B: double (+100%) everywhere, a feed order SAR 300: dearer, so rushing stays rare.
- C: a quarter (+25%), a feed order SAR 100: cheap, close to the real overtime on the work alone.

**Q3. Paying for a rush.**
- **A (recommended):** cash only, never the merchant's account; refused below zero (`inDebt`). The account is for
  the herd's necessities (decisions 9 and 10); tomorrow's delivery is the necessity, today's is a convenience.
- B: on the account when the herd is already without water or feed.

**Q4. Where the rush is offered.**
- **A (recommended):** on what is already under way: the building row, the order on its way, the camel on the truck
  (one mechanic; ordering stays one tap).
- B: also a second button at the moment of ordering («ابنه اليوم»، «اطلب يوصل الحين»).

**Q5. The rush in البنك.**
- **A (recommended):** its own kind «الاستعجال», each line what was hurried: he sees what convenience cost him.
- B: folded into the thing's kind (البناء، الماء، العلف، النقل).

**Q6. A standing order (طلب ثابت) for feed and water.** Real farms keep a regular arrangement with the feed merchant
and the tanker; without one a jump past what the stores hold (18 days of feed at the full farm) stops for an order.
- **A (recommended):** yes, in part B: set in الوايت and العلف, the supplier sends a top-up when a store comes down
  to its last 3 days, paid like an order (cash, then the account to its limit). The jump then stops for a store only
  when the account is full. New state and a save version.
- B: no: the jump stops whenever a store is low (every two or three weeks at the full farm).

**Q7. A vet's contract (عقد بيطري).** GDD 4.2 already names it («تعاقد شهري بسياسة علاج تلقائي (لازمة مع الحلال
الكبير)», a game choice), and the engine has none. At 10,000 head an illness comes every day, so without it a jump
cannot get past one day; even at 56 head a year left alone loses 39% of the herd to illness.
- **A (recommended):** yes, in part B: a monthly fee (a game choice, no price found: proposed SAR 1,000 a month plus
  SAR 20 a head, to be put to him), each illness treated the day it comes at the treatment's own price, on the
  account as the vet is now. New state and a save version.
- B: later, with the vet's own screens; until then the jump stops at every illness.

**Q8. The stops** (section 5's table).
- **A (recommended):** an illness, a death of illness or thirst, a store at 3 days, money first below zero, an offer,
  his round's day, a treatment found; everything else told at the end.
- B: every death stops it too (at a large herd, old age and calves' losses stop it every few days).
- C: the player picks the stops on the card (more to read, more to get wrong).

**Q9. A camel already sick when he leaves.**
- **A (recommended):** the go button waits until she is treated (one tap on the card, the vet on account).
- B: allowed; the jump stops on the first day (it would stop at once anyway).

**Q10. How far.**
- **A (recommended):** any day up to a year ahead (the catch-up's own cap).
- B: only to the next season's first day.

**Q11. The app.**
- **A (recommended):** «التقويم», the ninth app on the home screen, the year's strips and the rows of what is coming.
- B: in البنك or the home's date line (tapping the date opens it): no new app.

**Q12. Online later.** The jump is offline only; online, the calendar shows the year and does not move time (ADR
0001). For the record, not a choice now.

## 7. GDD rows to add in part B (Arabic, as the GDD is written)

- الاستعجال: اللي ينبني أو بالطريق (منشأة، وايت، علف، ناقة على اللوري) يخلص الحين بسعر أعلى: المنشأة نص سعرها لو باقي
  لها 3 أيام وأقل كل ما قربت (الأوفرتايم +50%، نظام العمل المادة 107 **(واقعي)**، والنسبة **(اختيار لعب)**)، والوايت
  نص سعره زيادة، والعلف 150 ريال للمشوار، والناقة نص نقلها زيادة لسواق ثاني **(اختيار لعب)**. من الرصيد بس.
- التقويم: تطبيق اختياري في الجوال، يوري السنة ويمشي اللعبة لقدام لين يوم يختاره اللاعب، ويوقف لو صار شي يبيه
  **(اختيار لعب)**.

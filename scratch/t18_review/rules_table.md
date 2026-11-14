# T18 part A: the reviewer's own rules table (made 14 Nov 2026, before any of the worker's code was read)

Abbreviations (all paths under /home/user/WEDG at b079dce):
- HOD = docs/agents/hunting_owner_decisions.md; OD = docs/agents/owner_decisions_2026-11-14.md
- HSD = docs/proposals/hunting_season_design.md; PF = design/ui/phone_falcon.cjs; TR = design/hunt/trip.cjs; SE = design/hunt/season.cjs
- HM = docs/proposals/hunting.md; GHS = docs/proposals/gdd_hunting_section.md; RR = docs/research-realism.md
- PD = docs/agents/proxy_decisions.md; RC = docs/proposals/rush_and_calendar.md; AW = packages/marah_domain/lib/src/away.dart
- BR = docs/agents/T18_hunting_build.md (the brief)
"Owner" marks his own word; "proxy" a provisional answer the owner confirmed in OD where said; "GC" a game choice.
The last column is how phase 2 checks it (my own test or mutation, not the worker's).
**Q-n** marks a place where the documents disagree or are silent: a question for the owner, not the worker's to settle.

## A. Seasons and hours (both edges of each)

| # | Rule | Source | Check |
|---|---|---|---|
| A1 | Hunting season 1 Sep – 31 Jan, both inclusive; refused 31 Aug and 1 Feb | RR 241; PF 289; HSD 102; GHS 22 | cast on 31 Aug, 1 Sep, 31 Jan, 1 Feb (and the years' wrap: Jan of the next calendar year) |
| A2 | Autumn half to 30 Nov, winter from 1 Dec (own species lists) | RR 242, 250-253; PF 290-291 | quarry list on 30 Nov / 1 Dec |
| A3 | Hunting by day only: [135] says one hour after sunrise to one hour before sunset; the permit view says «بالنهار بس» | GHS 22; RR 247; PF 289 | cast at each edge minute ±1. **Q-1**: sunrise/sunset times (real for Qassim by date, or a fixed GC hour?) and whether the 1-hour margins (one source) are built |
| A4 | Trapping season 1 Oct – 30 Nov, both inclusive; refused 30 Sep and 1 Dec | RR 312; HSD 66, 103; PF 208, 292 | release pigeon on each edge day |
| A5 | Trapping hours: dawn to about 10:00, and a short evening hour before sunset of very low success | RR 343; PF 326 («من الفجر لين الساعة 10، وبالمسا ساعة») | per-hour odds at 09:59/10:00, evening hour. **Q-2**: at midday (10:00 to the evening hour), lawful by day: refused (with what words? none drawn), or allowed with near-zero odds? |
| A6 | No trapping by night or with lights: «بالليل وبالضو · ما فيه طرح» (whether the hunting rule binds trapping is unconfirmed; the game says it does) | PF 298; HSD 110-111; HM 430 | night release refused with words, state unchanged |
| A7 | The trapping auction runs 1 Oct – 30 Nov, nightly at Malham (it closed 15 Nov in 2020/22/24; the design uses 30 Nov) | RR 312; PF 190; HSD 66-67 | enter on 30 Sep / 1 Oct / 30 Nov / 1 Dec |
| A8 | Breeders' auction in August; the exhibition 1–10 Oct | PF 192; BR 44-45 | buy on 31 Jul / 1 Aug / 31 Aug / 1 Sep; 30 Sep / 1 Oct / 10 Oct / 11 Oct. **Q-3**: August whole month (PF 192, BR) or 5–25 Aug (SE 49, RR 293 [158])? |
| A9 | Release of a kept trapped peregrine «من فبراير» or kept through the year, his choice | OD 66-67 («مخير بين الاثنين»); HSD 264 | release 31 Jan refused, 1 Feb allowed. **Q-4**: from February until when (spring only, or any day after, in later years too)? |

## B. Permits

| # | Rule | Source | Check |
|---|---|---|---|
| B1 | Two permits in «تصريح الصيد»: hunting (صقار) and trapping (طرح) | PF 288-294; HSD 101-104 | each needed for its own act; one does not stand for the other |
| B2 | Hunting permit valid 1 Sep – 31 Jan, by day; personal, not given to another («شخصي · ما ينعطى لغيرك، وتشيله معك») | PF 289, 294; RR 245 | cast without it refused |
| B3 | Trapping permit 1 Oct – 30 Nov, trapping grounds only, 500 riyals (GC; issuer not found) | BR 39; PF 293; HSD 103-104 | price exactly 500; one per season; expiry 30 Nov. **Q-5**: may it be bought before 1 Oct? does it lapse each season? |
| B4 | The hunting permit's fee: none on the view; GHS 24 says no source (GC); SE money page uses 100 from a weak source [160] | PF 289; GHS 24; SE (string 'اختيار لعب (مصدر ضعيف يقول 100 [160])') | **Q-6**: free, 100, or another GC? |
| B5 | Falconry permits are tied to a falcon's passport or ownership certificate | RR 243; PF 270 («جوازه باسمك · هو إثبات الملكية») | **Q-7**: a trapped bird he keeps: does it get a registration/passport without being entered at the auction (the club's check is drawn only in the sale view, PF 223)? May he hunt with it without one? |
| B6 | The hunter must be 21+ (one source) | GHS 24; RR 244 | silent in the build brief: say "not built" or "the player is assumed of age" |

## C. Grounds and places

| # | Rule | Source | Check |
|---|---|---|---|
| C1 | Trapping grounds are real places: north (الحماد، أم خنصر، العويقيلة، رفحاء، حائل), north-east (الدبدبة/حفر الباطن، الخفجي، الجبيل), south (السليل، الربع الخالي، شرورة), west coast (الليث، القنفذة، المجيرمة، جازان، ينبع، الوجه) | GHS 109-113; HM 410-411; RR 328-332 | each in the catalogue with a real distance from the farm (Qassim yard 25.81 N 42.90 E, TR 23); الحماد ≈ 600 km (TR 23; PF 306). الحماد's place disagrees (W or E of Arar, RR 329): **Q-8** (which?) |
| C2 | Coastal grounds are the best («بلا منازع»); wind and visibility matter; October is the peak | RR 333; GHS 115 | ground weight coast > inland; month weight Oct > Nov; each weight a marked GC |
| C3 | Hunting banned in cities, villages, farms (his farm and around it), rest houses, reserves, royal reserves, giga-projects, the coast to 20 km | RR 264; GHS 28; PF 296 | cast at each refused with its words. **Q-9**: the radius of "around the farm" (GC) |
| C4 | The coast's exception «إلا أرض طرح بموسمها» is the game's choice, not a real rule; outside the season the coast is closed to trapping too | PF 296; HSD 106-108 | a coastal ground on 1 Dec refused |
| C5 | Houbara only in a licensed estate (المحازة) with a falcon; stone-curlew in open land with a falcon | GHS 27; PF 294; RR 252, 255 | cast at houbara in open land refused. **Q-10**: stone-curlew is on the autumn list [140]; may it be flown at in winter (1 Dec–31 Jan)? houbara in the estate: which dates (1 Nov–31 Jan in 2021 [143], or the whole season)? |
| C6 | A near ground allows a one-day outing (back the same evening); a far ground a trip of days with a camp; he chooses each time | HOD 45-46 (owner); HSD 258-261; TR 206-208 (طرف النفود 14 km) | the "near" cut-off distance is a GC: must be marked |
| C7 | The Empty Quarter: an old rule left it out of hunting (uncertain); it is also a trapping ground | RR 264, 331 | **Q-11** (low): falconry there? |
| C8 | Off a trapping ground the net's button warns: «هنا ما فيه طرح» / «مو أرض طرح» / «الطرح بأرض طرح بس وبموسمه، والشبك برا أرض الطرح غرامته 100,000 ريال.» | TR 345-346 | refusal words exact |
| C9 | By the farm the cast warns: «هنا ممنوع الصيد» / «قريب من المزارع والعزب» / «الصيد بالمزارع وحولها ممنوع، وغرامته 5,000 ريال لو انمسكت. ابعد عن العزب والقرى وأرسله.» | TR 349-350 | refusal words exact |

## D. What lands in the net, and its fate

| # | Rule | Source | Check |
|---|---|---|---|
| D1 | A passage peregrine of the year (فرخ شاهين بحري): sellable; card «فرخ شاهين بحري» / «طرحته · ينباع بمزاد الطرح» / length, width (in), weight (g) / «برقعه وحطه بالخيمة. تعرضه بمزاد الطرح بملهم خلال أيام، أو تخليه لك.» | TR 314-315; HM 415-419 | each species reachable; sizes in the sale pages' range (15–16 in, ~950–1,122 g [187][216]) |
| D2 | Mountain peregrine: released at once: «طلقته: الشاهين الجبلي طير مقيم، وطرحه ممنوع» | PD 70-72; PF 298; OD 28 (owner: his answer on the saker/قرناس, recorded as confirming items 3 and 4) | not in the room, not sellable, no money, the line word for word |
| D3 | Lanner: released at once: «طلقته: الوكري طير مقيم، وطرحه ممنوع» | PD 71-72; PF 298 | as D2 |
| D4 | Saker: released: «طلقته: الحر مهدد، والمزاد ما يقبل إلا فرخ الشاهين البحري» (owner: «ينطلق: اللعبة تطلقه على طول مع سطر يقول ليش») | OD 28 (owner); PD 75; PF 298; TR 319 | as D2 |
| D5 | A قرناس (a bird past its first moult): released: «طلقته: المزاد ما يقبل إلا الفرخ» (release a GC: no ban found) | OD 28 (owner); PD 73-76; PF 298 | as D2. **Q-12**: the line names no species: a قرناس of which species? (peregrine قرناس surely; a saker قرناس takes the saker's line?) |
| D6 | Mostly a فرخ شاهين بحري (GC); the mix of the others is a GC | GHS 118 | the species shares marked GC |
| D7 | The trapped bird goes hooded to the falcons' room | GHS 121; PF 222, 333 | **Q-13**: with no room, or the room full (4), what happens to a bird in the net? (refuse the trapping? release?) |
| D8 | The summary counts birds caught and released by day («طرحت فرخ شاهين بحري … اليوم السابع · بغرفة الصقور»; «طلقت حر … اليوم الثالث: المزاد ما يقبله») | PF 333-334 | summary lines |

## E. The trapping auction: what it takes, no fee, dates

| # | Rule | Source | Check |
|---|---|---|---|
| E1 | Takes only a فرخ شاهين بحري trapped in the Kingdom; refuses saker and قرناس | RR 314; PF 190, 193 («مزاد الطرح ما يقبل الحر ولا القرناس») | enter a bought saker, a bought peregrine, a kept bird after it moulted: refused |
| E2 | Enter the bird; the club's team checks it and documents the trapping and gives «وثيقة تسجيل طرح»; transport and lodging to Malham paid («النقل والسكن لملهم عليهم») | PF 223; RR 313, 323 | **Q-14**: does selling take him away (a trip to Malham, paid) or is it from the phone with no travel? |
| E3 | Bidders see length, width, weight and where trapped, nothing else («كل طير بطوله وعرضه ووزنه ومكان طرحه»; «وش يسوي بالصيد ما ينعرف ولا قيمته قبل المزاد: المزاد يقولها») | PF 198, 203, 228 | hidden-values check: no worth before the hammer |
| E4 | Opening bid 30,000–150,000 [217]; the sale view's example 70,000 | PF 225; RR 368 | opening inside the range |
| E5 | The hammer: «رسى بـ …» / «نزلت برصيدك كاملة، بدون رسوم» / «الحجل الإلكتروني والجواز للمشتري»; money in full, no fee, the bank's own kind | PF 233; RR 323; BR 64-65 | cash delta == hammer exactly; a new ledger category; no commission row |
| E6 | Alone: «تشاركه · لحالك: السعر كله لك» (partners not built) | PF 226; OD 26 (owner) | no split |
| E7 | Prices as the sources: about 50,000 up; 2025 sales 71–361k, median 112k; record 650k; season means 88k (2022) to 160k (2025); at least 6 of 40 at 300k+ | RR 355-368; BR 59-61 | section 3 of the report |
| E8 | Sold within days (dear ones in days [199]) | HM 419; GHS 123 | **Q-15**: any limit or loss for keeping a bird unsold for weeks? a bird caught on 30 Nov after the last night: kept by force? |
| E9 | An unsold lot (no bid at the opening)? | silent | **Q-16** |
| E10 | Buying at the trapping auction (a route to his own falcon, «تبيع فيه … أو تشتري»): how he buys is not drawn (the lots view has no bid button) | PF 190, 197-203 | **Q-17**: the buying mechanism (bid as الحراج, or the hammer price), cash or account |

## F. Buying a falcon (routes, terms)

| # | Rule | Source | Check |
|---|---|---|---|
| F1 | Three routes each in its month: breeders' auction (August, farm-bred saker about 19,000 [158]), exhibition (1–10 Oct, imported sakers, 700,000 and 100,000 [184]), trapping auction (1 Oct–30 Nov, peregrine of the year from about 50,000 [200]) | PF 192-193; HSD 86-89; PD 77-79 | refused outside each window with words; prices inside the sources; distribution marked GC |
| F2 | Cash or terms: no view says | BR 45-46 | **Q-18**: cash only, or on the merchant's account? (also for the gear, the room, the permit) |
| F3 | How each came is recorded: «اشتريته من مزاد الطرح 20 أكتوبر بـ 71,000»; «اشتريته من مزاد المزارع بأغسطس»; trapped: where and when («طرحته بالحماد 12 أكتوبر») | PF 222, 242-243 | the view's fields |
| F4 | A falcon needs a place: the room | HOD 18-19 (owner 5) | **Q-19**: buying with no room or a full room |

## G. Keeping, never reselling, releasing

| # | Rule | Source | Check |
|---|---|---|---|
| G1 | A trapped bird he keeps stays his; never resold: no command exists; the view says «الطير اللي تطرحه وتخليه لك ما ينعرض للبيع بعدين · ما لقينا له طريق نظامي» | OD 29-30 (owner); PF 244 | grep the command set; and: once kept, entering it at the auction is refused (if "keep" is a state, not just "not yet sold") |
| G2 | The design's older lines that a trained falcon's price rises "if you sell it" (GHS 25, 41) and SE's "sold at the next autumn's auction" header (SE 17-18) | GHS 25, 41; SE 17-18 | **Q-20**: may a BOUGHT falcon (breeders' or exhibition saker, a peregrine bought at the trapping auction) be resold? OD 8 speaks only of a trapped bird kept |
| G3 | Release of a kept trapped peregrine from February, or keep through the year (his command) | OD 66-67 (owner); BR 66-67 | A9's edges; release of a bought falcon refused (only "a kept trapped peregrine") |
| G4 | A فرخ becomes a قرناس after the moult («يقدر يدخل السنة الجاية قرناس»); the moult (المقيض) in summer, months not sourced (GC) | PF 282, 259; HSD 183-184; SE 12-13 | age class changes by a daily system keyed by date |

## H. Being away (the away call only; N3)

| # | Rule | Source | Check |
|---|---|---|---|
| H1 | One mechanism: the calendar's `away()`; nothing else advances days for a trip or camp | RC 239-242; HSD 136-138; BR 47 | grep for advanceDays/loops in the new code |
| H2 | N3: a camp's daily work (supplies used, falcon care, the camp's state) is a step of the daily pipeline keyed by state, never an AwayCounter/loop callback; a played day and a jumped day run the same code | RC 260-264; AW 1-5, 156-159 | my test: the same camp day advanced by `advanceDays(1)` and by `AwayRun.step()` gives the same state hash |
| H3 | The card before leaving is the calendar's card with the trip's lines under it: the ground and distance, the gear he has and lacks, the camp's supplies | HSD 139-143; PF 305-318 | the card's fields |
| H4 | The drive is the plan's travel (`AwayPlan.travel`, which the base does not have), with the stops still checked | RC 255-256; HSD 144 | stops fire during the drive |
| H5 | One night per «نام لين الفجر»: one call of `away()` to tomorrow, landing at the working hour's start (dawn for trapping; the morning flight for falconry) | HSD 147-150; RC 247-251 | landing minute per kind; **Q-21**: the minutes of "dawn" and of "the morning flight" (GC) |
| H6 | All the calendar's stops, plus the camp's own: supplies out («خلصت مؤونة المخيم»), the trapping season's end («خلص موسم الطرح»), the trip's chosen end | HSD 151-154; PF 325 | each stop fires on its day |
| H7 | A bird in the net is played live, not a stop | HSD 155 | no stop kind for it |
| H8 | Break camp at any time («فك المخيم وارجع») | HSD 146; TR 276, 324 | the command works on any day, any hour |
| H9 | The farm runs by its own rules; no new risk invented | HOD 22-23, 33-35 (owner 7); PD 82-85 | an away game vs a same-days played game: same farm state |
| H10 | The summary is the calendar's with the trip's lines above (days out, birds caught and released, the camp's spending) | HSD 165-166; PF 330-341 | the summary's fields; nights counted, day 1 = the first day (HSD 160-161) |
| H11 | The away call's refusals still hold (a sick untreated camel without a vet's contract; his round's day today) | AW 214-239; RC 292-293 | leaving for camp with a sick camel refused |
| H12 | Falcon care's hook: RC 253 and 359 name `AwayStop.falconCare` (not in the base: only `AwayStopKind.extra`) | RC 253, 359; AW 55-57 | **Q-22**: what falconCare does in a jump: a stop when a falcon at the farm will step back (before 14 days without الدعو), or nothing when the falcon is with him? |

## I. The falcons' room

| # | Rule | Source | Check |
|---|---|---|---|
| I1 | A facility built in the yard (أوكار ومقيض), its own pin and card, like the pens and the tank | HOD 18-19 (owner 5); HSD 178-184 | a new Facility value (the base's `Facility.room` is the 60,000 sitting room: no collision of names or saves) |
| I2 | Holds 4 falcons (GC); price 18,000 (GC) in العزبة's build list | HSD 182; BR 38; PF 240 («صقرين من 4») | 4 fits, the 5th refused with words; price 18,000 |
| I3 | The card: how many falcons, which want الدعو today, the moult in summer; buttons «ادعهم» and «نادي الصقور» | HSD 180-182; TR 239-240 | the pin's data |
| I4 | How many rooms may he build? | silent | **Q-23** |

## J. الدعو (daily care) and neglect

| # | Rule | Source | Check |
|---|---|---|---|
| J1 | Once each time the game opens (GC); counts the days that passed («مرة وحدة كل ما تفتح اللعبة، وتنحسب لك الأيام اللي فاتت») | PF 259; HSD 183 | **Q-24**: one tap credits the days since the last? then what is neglect? |
| J2 | Left two weeks, it steps back («ولو تركته أسبوعين يرجع خطوة») | PF 259 | 13 / 14 / 15 days |
| J3 | A new falcon needs 4 weeks of الدعو before its first outing; five steps (البرقع والدس، ياكل على يدك، الملواح من قريب، من بعيد، جاهز للمقناص) | PF 250-256 | cast refused before ready, with words (**none drawn**: the worker's own line, for the owner) |
| J4 | No الدعو during the moult in summer («وبالمقيض بالصيف ما فيه دعو») | PF 259 | moult months a GC |
| J5 | Weighed daily before feeding («تزنه كل يوم قبل أكله») shown in grams | PF 257 | weight is shown (not hidden) |
| J6 | Training raises skill; skill never shown as a number, only through results | GHS 25, 37 | hidden-values check |
| J7 | Falcon's feed 20 riyals a day (GC) in SE's money page | SE ('اختيار لعب: 20 ريال باليوم') | **Q-25**: is there a daily upkeep for a falcon (not in the brief)? |

## K. Falconry: the cast, quarry, the lost falcon

| # | Rule | Source | Check |
|---|---|---|---|
| K1 | The cast by his hand, from the map, on a hunting ground, in season, by day, with a permit; result from the falcon, the ground and luck | HOD 7-8 (owner 1); BR 68-69 | each condition's refusal |
| K2 | Hunted game is never sold (no money from quarry) | RR 271; PF 301; TR (caption «الصيد ما ينباع») | no income row |
| K3 | Hunting from a moving vehicle is fined 100,000: the cast only when parked | RR 272; PF 300; GHS 26 | **Q-26** (to the director): is "parked" the engine's check (a command field) or the map's (part C)? |
| K4 | Lost falcon: rare; searched with the tracker; mostly found, sometimes gone; the tracker lowers the risk | HOD 20-21 (owner 6); TR 292-293 («تدوّره بالسيارة على إشارة الجهاز: غالبًا تلقاه، وأحيانًا يروح.») | rates marked GC; with tracker loss < without; "gone" removes it for good |
| K5 | The tracker's price, and whether it is per falcon | silent | **Q-27** |
| K6 | Result card: «نزل على الكروان عند الطعس. أكّله من صيده وارجعه للدس.» | TR 287-288 | words |

## L. Refusals: warn and do nothing

| # | Rule | Source | Check |
|---|---|---|---|
| L1 | In a banned place or time the button warns and says why, and nothing is sent | HOD 16-17 (owner 4) | every refusal: the state's canonical JSON identical before/after (no pigeon spent, no draw consumed, no ledger row, no fine) |
| L2 | No fine can follow from a refused command (the fines stay listed on the permit only) | BR 62-63; PF 34-35 | no fine event or ledger row on any refusal |
| L3 | Every refusal has its words (Gulf Arabic), from the design where drawn | BR 92-94 | Arabic check |

## M. The odds (see the report's section 3)

| # | Rule | Source | Check |
|---|---|---|---|
| M1 | Twice the sources' range: a bare beginner about one season in 6, a well-equipped and well-placed trapper two seasons in 3, never beyond; written as a GC departing from the sources (0.08–0.336) | OD 23-25, 31-35 (owner); BR 57-60 | my run on the built engine |
| M2 | The share of dear birds and the prices as in the sources | OD 32-33 (owner) | as above |
| M3 | Gear, pigeons, ground, month, hour move him along the range; each weight a marked GC | BR 59-60; HM 389-401 | a sweep of setups: none above the top |
| M4 | No hidden help, no pity timer: a season can end with nothing | BR 62 | independence of days and seasons |
| M5 | **Q-28**: may a season yield two sellable birds? The owner counts seasons with a bird; the sources' 0.08–0.336 are birds per trapper. If two are allowed, 2/3 of seasons with a bird means about 1.1 birds a season (Poisson), beyond twice the sources' 0.336 | OD 31 vs HM 374-376 | report both figures |

## N. Rules of the build (from the brief)

| # | Rule | Source | Check |
|---|---|---|---|
| N1 | A game that never touches falcons is unchanged, same seed, same state hash week for week, VM and JS; no existing stream gains or loses a draw | BR 80-82 | my driver (base's bot) on the worker's engine, the new keys stripped |
| N2 | Save version: the next after the branch's (12 if T16 lands 12 first), behind one constant; migration tested on a real base save played a season forward | BR 83-85 | my base save of seed 7 (baseline/save_base_seed7_104w.txt) loaded and played on |
| N3 | Budgets: a day's step and the snapshot at 10,000 head not beyond noise | BR 86-88 | r_timing_test.dart back to back |
| N4 | Every number in docs/GDD.md's hunting section with its source or "اختيار لعب" | BR 89-91 | numbers in new code vs GDD |
| N5 | Not built: contests and festival, partners, air rifle, Kalashnikov, wolves and dogs, anything on the phone or map; said so in the GDD section | BR 74-76 | grep |
| N6 | Every line a player can read in Gulf Arabic, word for word from the design where drawn; counting nouns and sex forms as the phone's standards | BR 92-94 | baseline/design_lines.txt against the worker's strings |

## O. The director's answers to Q-1..Q-28 (docs/agents/T18_answers.md, commit a7bc877): what phase 2 now checks

Kind: S = source, GC = game choice (must be in docs/GDD.md's hunting section as «اختيار لعب», one constant), OW = the
owner's, built provisionally behind ONE switch (check: flipping that one constant gives the other answer, nothing else).

| Q | Kind | Answer to build to | Phase-2 check |
|---|---|---|---|
| 1 | S [135] | sunrise+60 min to sunset−60 min; the engine's sun, else a monthly table for the farm's latitude, each row sourced/computed and marked | cast at each edge ±1 min, several months; the table's rows vs the standard formula |
| 2 | GC | trapping lawful all daylight; hour a weight (high dawn–10:00 and the evening hour, low between); night refused (marked unconfirmed) | midday not refused; night refused with words, state unchanged; GDD marks |
| 3 | S [158] | breeders' auction 5–25 Aug | 4/5 Aug and 25/26 Aug |
| 4 | OW | release 1 Feb–30 Apr (end GC unless dated), any later year | 31 Jan / 1 Feb / 30 Apr / 1 May, a later year; one switch |
| 5 | GC | permits bought any day, valid one season (open or next), lapse 30 Nov (trapping) / 31 Jan (hunting) | bought in Sep valid 1 Oct; lapses; GDD |
| 6 | GC | hunting permit 100, "weak source" [160] | price; GDD mark |
| 7 | S [190-192] | keeping goes through the club's check too (no sale); registration+passport before it may be flown | cast with an unregistered kept bird refused |
| 8 | - | الحماد NW of Arar (director's knowledge, marked); distance a marked estimate | catalogue marks |
| 9 | S or GC | the research's distance from dwellings if any, else GC in the GDD | GDD |
| 10 | S strictly | each species only on its source's dates; unlisted refused; report what is huntable by month | each species' dates both edges |
| 11 | - | Empty Quarter a trapping ground; the old rule noted in the GDD | GDD |
| 12 | - | saker قرناس takes the saker's line; the قرناس line for a peregrine past فرخ | species rule tested first |
| 13/15 | OW | sellable bird held at camp/farm without a room until sold; entered any open night; keeping needs a free room place; unsold+unkept at the auction's close released with a line; net-after-auction-close asserted impossible | each path; one switch |
| 14 | - | selling from the phone, no trip; hammer the same night | no away run on sale |
| 16 | GC | an accepted bird always sells; no floor below the lowest sale read | GDD; price minimum |
| 17 | - | engine offers the night's lots, a buy command at the hammer price the lot will reach | buy price == that lot's hammer; no hidden price leaks before purchase (the view shows openings only) |
| 18 | OW | all hunting purchases cash only, refused in debt | each purchase on negative cash refused; one switch |
| 19 | - | buying with no room or the room full refused with words (worker's own lines, listed) | refusal, state unchanged |
| 20 | OW | no resale command for a bought falcon; older GDD lines withdrawn | command set; GDD lines gone; one switch |
| 21 | GC | trapping lands at civil dawn; falconry at sunrise+60 | landing minutes |
| 22 | - | falconCare = a state-based stop: the morning of the day a falcon at the farm would step back; no loop callback | stop day exact; N3 hash test |
| 23 | GC | one falcons' room (4) | second build refused |
| 24 | - | one tap = today's care for every falcon in the room; neglect = days since last cared for or flown; flying on a trip counts | 13/14/15-day edges; trip day counts |
| 25 | GC | 20 riyals a day per falcon, daily system, own ledger kind | daily charge; jumped day == played day |
| 26 | - | cast carries the car's state from the map; moving car refused with words; no fine | refusal |
| 27 | GC | one tracker per falcon; price GC | GDD |
| 28 | OW | target = share of seasons with >=1 sellable bird (1/6 .. 2/3); a second bird possible by the same daily chance, no cap, no help; report mean birds a season beside it; "one bird at most" is one switch | measure both figures; flip the switch and re-measure |
| oddity | - | Facility.room stays; the falcons' room a new value; season.cjs header stale | save of a base game with the sitting room loads |

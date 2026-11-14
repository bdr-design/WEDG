# T18B reviewer's table (phase 1, made before the worker's code): every view and command path the brief asks for,
# the design's words (design/ui/phone_falcon.cjs), the engine fact each needs (base wt/t18 7478a54), given or not

Legend: ✓ the engine gives it · ✗ it does not (a fact to add to the engine's view, with a test, never worked out in
phone.js) · D a place where the approved picture and the engine disagree, or the picture does not cover the engine:
**the owner's to answer, not the worker's choice** (the brief's "Design first" list is D1–D4; D5 on are found here).
Engine sources: packages/marah_domain/lib/src/views/falcon_view.dart (falconFacts in snapshot.falcons; falconCatalogOf
via the worker op falconCatalog), catalog/falcon_lines.dart (FalconLines), catalog/falconry.dart, handlers/falconry.dart,
systems/falconry_system.dart, trips.dart (Trips.card via op tripCard; Trips.night via op tripNight), away.dart.
NOTE design/prototype3d/engine.js at the base has no wrapper for falconCatalog, tripCard or tripNight: the worker adds them.

## Home (view 1)
Design: the home's apps plus «نادي الصقور» (badge 1, ringed .ic.new) and «تصريح الصيد». The brief: the two new apps only
(the rule of 13 Nov; the base home already shows 9: الوايت العلف الحليب العزبة الحراج البنك المزاين المحادثات التقويم).
- badge on «نادي الصقور»: the design draws 1; what it counts is not said. ✗ the engine keeps no "untold" hunt news
  (a hammer fallen, a lot lost, a bird freed at the close, a falcon to care for): only the snapshot's last 40
  recentEvents carry FalconFate/FalconLotLost, and they scroll out. **D5**: what the badge counts (the brief: "a notice
  is the badge, as الحراج's offers"), and the engine fact for it (e.g. falconFacts.untold).
- the ring (.ic.new) is a design marker of a new app: not to be built (or the owner's).

## «نادي الصقور» · المزاد (view 2: the auctions told apart)
Words: tab bar «المزاد | صقوري | الطرح | المهرجان» (المهرجان not built: the tab must go, **D6**: three tabs or the bar
redrawn); card «مفتوح الحين» «مزاد الطرح» «ملهم · من 1 أكتوبر لين 30 نوفمبر، كل ليلة» «فروخ الشاهين البحري المطروحة بالمملكة
بس» «تبيع فيه طيرك اللي طرحته، أو تشتري»; «وصقرك له ثلاث طرق، كل وحدة بشهرها»; rows «مزاد الطرح · فرخ شاهين بحري · من حوالي
50,000 · الحين», «معرض الصقور · حر مستورد، وأسعاره عالية · لين 10 أكتوبر», «مزاد صقور المزارع · ملهم · حر فرخ إنتاج مزارع ·
أغسطس»; tank «مزاد الطرح ما يقبل الحر ولا القرناس» «حرين مستوردة بالمعرض 700,000 و100,000 ريال» «حر المزارع حوالي 19,000 ريال».
- open now / dates: ✓ falcons.open, catalog.routes (from/to). Closed words ✓ catalog.lines.refusals['routeClosed.*'].
- «ملهم», «من حوالي 50,000», «700,000 و100,000», «حوالي 19,000»: ✗ not in the catalog (sourced figures [184][158][200]
  that would be typed into phone.js). Ask the worker to carry them in the catalog (or say why not).
- the state in other months (Dec–Jul all closed; Aug breeders open; 1–10 Oct two open): **D7** the picture draws 1 Oct
  only (low risk: same layout; the words of the card when the trapping auction is closed are new).

## مزاد الليلة (view 3: tonight's lots) and buying one
Words: title «مزاد الليلة»; note «مزاد الطرح · ملهم · كل طير بطوله وعرضه ووزنه ومكان طرحه»; each lot «فرخ شاهين» /
«الحماد · 15 × 15½ إنش · 1,010 غرام» / opening «70,000» «الافتتاح» / «شاهين بحري · طرح قبل يومين» (أمس); rows «وش يسوي بالصيد
ما ينعرف · ولا قيمته قبل المزاد: المزاد يقولها», «ما فيه رسوم · لا على البايع ولا على المشتري».
- ✓ falcons.lots[]: lot, route, species, age, female, size («15 × 15½»), weight, opening, ground, trappedDaysAgo, gone.
- exhibition (1–10 Oct) and breeders' lots: no ground, saker: **D7** not drawn (rows for them are new words).
- buying with his ceiling: **D1** (design-first): the stepper (phone's own: the sell page's «سعرك [−] … [+]»), two taps,
  bought → FalconBought {falcon, name, price} in the reply's events; lost → FalconLotLost {lot, price} in the reply.
- what the row shows after: ✗ falcons.lots[].gone is a bare true for BOTH bought-by-him and gone-to-another, and the
  told price of a lost lot is in the reply only (lost on reload or after the day). Engine fact needed: the lot's end
  (mine / another's at price). **D1** also: the words of each outcome.
- refusals (each on screen and in the live region): routeClosed (closed(route)), notALot «هالطير مو من طيور اليوم» (a
  lot of yesterday after midnight), lotGone «هالطير انباع، شوف طيور اليوم», noRoom «ابنِ غرفة الصقور أول: الصقر يبي مكانه
  بالعزبة», roomFull «غرفة الصقور مليانة: تاخذ 4 صقور بس», invalidAmount, inDebt, insufficientFunds (ceiling > cash: the
  stepper's top must be his cash; the phone's own money words).
- At the game's start there is NO falcons' room: every lot is refused noRoom until the room (18,000, built in days) is
  up. The view must say so before the ceiling is asked (falcons.room.cannot ✓ 'noRoom'/'roomFull').

## الطرح (view 4: the trapping permit and the gear)
Words: «تصريح الطرح · ساري لين 30 نوفمبر · بأراضي الطرح بس · عندك»; «عدة الطاروح · السعر بالريال»; «الحمام · عندك 6 حمامات ·
الحمامة 50 · عندك»; «شبك الحمام · الشبك على ظهر الحمامة · عندك»; «شبك الطيور والجربوع · لو الصقر ما يبي الحمام · 1,200»;
«الدربيل · تشوف الصقر من بعيد · 900»; «الخيمة المتنقلة · تلحق الصقور لأرض ثانية · 6,500»; «مؤونة المخيم · ماء وأكل وبنزين ·
150 لليوم · تكفي 10 أيام»; button «اشتر الناقص بـ 8,600»; note «العدة تقرّبك من الطير وما تضمنه: أغلب المواسم تخلص بدون طير.»
- ✓ falcons.permits[trapping] (held, valid, closes), falcons.gear[g] = [has, onTheWay, room], catalog.gear (name,
  price, most), catalog.deliveryDays (1).
- pigeonNet's price (300, the engine's game choice) is not drawn (the picture shows it held). Fine once unheld.
- **D8** «اشتر الناقص بـ 8,600»: the engine has no basket command: OrderGear(gear, units) one kind at a time, each its
  own cash check (a partial purchase is possible). And how many pigeons / days of supplies «الناقص» means is not said
  (pigeons up to 20, supplies up to 60 days). Per-item buttons with the stepper, or the basket: the owner's.
- «has coming» (ordered, arrives tomorrow) is not drawn: **D8** its words (e.g. «يوصل بكرة»).
- the tracker (جهاز التتبع, 2,500, one per falcon, Gear.tracker, booked under «الصقور وأجهزة التتبع»): not drawn
  anywhere in the 18 views: **D9** where it is bought and shown (the brief: each falcon «its tracker»).
- refusals: gearFull «ما تقدر تطلب أكثر منها» / «تقدر تطلب N بس», invalidAmount, inDebt, insufficientFunds; permit not
  held: «تصريح الطرح» row then shows what? (bought in «تصريح الصيد»): **D10** with view 13's buy.
- what each item does in words: the design's words, static (fine: words, not rules).

## اعرض طيرك (view 5: a held bird entered), the hammer (view 6), keeping it, the close
View 5 words: title «اعرض طيرك»; «براق · فرخ شاهين بحري» «طرحته بالحماد 12 أكتوبر» «15 × 15½ إنش · 1,010 غرام» «بالبرقع بغرفة
الصقور»; «فريق النادي يفحصه ويوثّق الطرح · ويعطيك وثيقة تسجيل طرح»; «النقل والسكن لملهم عليهم · وما فيه رسوم على البيع»; tank
«يدخل مزاد الليلة» «سوم الافتتاح 70,000 ريال» «تشاركه · لحالك: السعر كله لك»; button «اعرضه الليلة»; note «المزايدين يشوفون
طوله وعرضه ووزنه ومكان طرحه، وقيمته ما تنعرف إلا بالمزاد. وتقدر تخليه لك بدل ما تبيعه.»
View 6 words: «رسى المزاد»; «براق» «رسى بـ 112,000 ريال» «نزلت برصيدك كاملة، بدون رسوم» «الحجل الإلكتروني والجواز للمشتري»;
«آخر الأسوام · بالريال»; bidders «بو فهد 112,000 رسى عليه» «بو ناصر 110,000 سام» «بو سعد 95,000 سام»; note «هذا مثال: …».
- ✓ falcons.held[] (id, name, species, age, ground, on, size, weight, trapDoc after the club's check, entered).
- «سوم الافتتاح 70,000 ريال» for HIS bird: ✗ the engine draws no opening for a held bird (lots have one; held do not).
  **D11**: drop the line, or the engine gives an opening (with the same "tells nothing of the worth" test as the lots').
- «تشاركه · لحالك»: partners are not built (the brief): **D11** drop the row or keep «لحالك» (the owner's item 6).
- «بالبرقع بغرفة الصقور»: wrong when he has no room (owner's item 22: held at camp or the farm without a room). ✗ the
  engine does not say where a held bird is. **D11** the words.
- the three ways **D2** (design-first): enter tonight (EnterTrapAuction: refusals notHeld «هالطير مو للبيع»,
  auctionClosed «مزاد الطرح من 1 أكتوبر لين 30 نوفمبر بس»); keep (KeepBird: refusals notHeld, noRoom, roomFull, with the
  room's state shown first); the close (the bird freed on 1 Dec morning, FalconFate freedAtClose, line ✓
  catalog.lines.release.freedAtClose «طلقته: خلص مزاد الطرح وما بعته ولا خليته لك»). Entered then kept is allowed by the
  engine (KeepBird removes the entry): the view must say it or not offer it.
- the hammer: falls in the next morning's day tick (FalconrySystem._auction): FalconFate {fate: sold, price} reaches the
  page only in snapshot.recentEvents (last 40; the held bird is gone from falcons.held). ✗ no lasting fact: the hammer
  view, if opened later, has nothing to read (D5's untold list would carry it). Money ✓ in the bank (falconSale).
- the bidders «بو فهد / بو ناصر / بو سعد» and their bids: ✗ the engine has no bidders. **D12**: drop the list or the
  engine makes them (a made-up list in phone.js is a rule copied and a fake number).
- «هذا مثال» note: right in a mock, wrong on a real sale: **D12** the note's words on the built view.

## صقوري (view 7: his falcons)
Words: «بغرفة الصقور · صقرين من 4»; «سهيل · شاهين بحري فرخ» «اشتريته من مزاد الطرح 20 أكتوبر بـ 71,000» «جوازه باسمك · الطلعات:
صاد حبارى بالمحازة مرة»; «غيث · حر فرخ» «اشتريته من مزاد المزارع بأغسطس» «جوازه باسمك · الملواح 18.906 ثانية»; row «الطير اللي
تطرحه وتخليه لك ما ينعرض للبيع بعدين · ما لقينا له طريق نظامي»; button «ادعهم اليوم».
- ✓ room.held / catalog.room.holds; falcons[] name, speciesName, age, how, route, on, price, ground, passport, ring,
  trapDoc, dauDays, ready, flights, taken {quarry label: n}, where, keep, tracker, stepsBackOn.
- «صاد حبارى بالمحازة»: ✗ taken has no place (quarry → count only). Words to adjust (minor).
- «الملواح 18.906 ثانية»: contests not built: must not show.
- a trapped and kept bird's line («طرحته بالحماد … وخليته لك»): not drawn: words new (list them).
- the tracker: **D9**. Releasing a kept trapped peregrine (ReleaseFalcon; window catalog.release [2,1,4,30], Q-4 still
  provisional): not drawn **D13** (button, two taps, the words before and after; refusals notKept «تطلق بس الشاهين اللي
  طرحته وخليته لك», releaseMonths «تطلقه من أول فبراير لين آخر أبريل»).
- a lost falcon (where 'lost'): part C (the flight); the row's words if one is lost are not drawn.

## الدعو (view 8)
Words: «الدعو · غيث»; «صقر جديد يبي 4 أسابيع دعو قبل أول طلعة»; steps «يرضى بالبرقع والدس · الأسبوع الأول · تم», «ياكل على يدك ·
الأسبوع الثاني · تم», «يجي للملواح من قريب · الأسبوع الثالث · الحين», «يجي للملواح من بعيد · الأسبوع الرابع · بعدين», «جاهز للمقناص ·
بعد الدعو · بعدين»; «الميزان · تزنه كل يوم قبل أكله · 1,120 غرام»; button «ادعه اليوم»; note «مرة وحدة كل ما تفتح اللعبة، وتنحسب
لك الأيام اللي فاتت. ولو تركته أسبوعين يرجع خطوة. وبالمقيض بالصيف ما فيه دعو.»
- ✓ dauDays, dauNeeded 28 (= 4 weeks), stepBackDays 14 and stepBack 7 (a week back), moult months 5–8 (room.moult),
  room.wantCare, stepsBackOn, caredOn.
- which week is «الحين»: ✗ (dauDays ÷ 7 worked out in the phone is a rule copy: ask for the engine's week or step).
- **D14** «مرة وحدة كل ما تفتح اللعبة» vs the engine: once a GAME DAY (caredOn != today), the days since counted up to 13,
  a 14-day gap counts 1. The note's words must follow the engine (or the owner changes the rule).
- **D14** the button «ادعه اليوم» on one falcon's page vs CareFalcons = every falcon in the room at once (Q-24).
- «الميزان … 1,120 غرام» daily weighing: the engine's weight is fixed (weightG); no weighing. Words only.
- refusals: falconAway (no falcons: «صقرك مو معك»), moult «بالمقيض ما فيه دعو». A second tap the same day: no
  refusal and no change (falcons cared today skipped): the button must show done.

## «تصريح الصيد» (views 13–15)
Words: tank «تصريح صقار · ساري · من 1 سبتمبر لين 31 يناير، بالنهار بس · فترة الخريف لين 30 نوفمبر · فترة الشتاء من 1 ديسمبر»;
tank «تصريح الطرح · ساري · من 1 أكتوبر لين 30 نوفمبر، بأراضي الطرح بس · الرسوم 500 ريال»; rows «المقناص بالصقر · الكروان بالبر،
والحبارى بالمحازة المرخصة بس», «الطرح · فرخ الشاهين البحري، بأرض طرح، بشبك على الحمام», «شخصي · ما ينعطى لغيرك، وتشيله معك»;
«ممنوع الصيد فيه»: «المدن والقرى والمزارع · يعني عزبتك وحولها، والاستراحات», «المحميات والمشاريع الكبرى · والمحميات الملكية
كلها», «الساحل · لين 20 كيلو داخل البر، إلا أرض طرح بموسمها»; «بالطرح: لو جا بالشبك»: the four release lines (✓ word for word
= catalog.lines.release: mountainPeregrine, lanner, saker.*, passagePeregrine.qarnas) + «بالليل وبالضو · ما فيه طرح»;
«الغرامات»: «صيد بدون تصريح 10,000», «صيد بمكان أو وقت ممنوع 5,000», «الشبك برا أرض الطرح 100,000», «الصيد من سيارة تمشي
100,000»; note «والصيد نفسه ما ينباع: بيع الصيد ممنوع. اللي ينباع فرخ الشاهين البحري المطروح، بمزاد الطرح بس.»
- ✓ permits[] kind, season, opens, closes, open, held, valid; catalog.permits fee (hunting 100, trapping 500).
- the fines' figures: ✗ not in the catalog (sourced [136]; typed into phone.js otherwise).
- **D10** the states the picture does not draw: not held (the buy button, its fee, two taps), held for the NEXT season
  (bought in Dec–Sep: valid false, held = next season), season closed, and the hunting permit's fee (100) which the
  picture leaves out; the refusal needsFalcon «تصريح الصقار يبي صقر جوازه باسمك» where the button warns; permitHeld
  «عندك هالتصريح لهالموسم».
- ✗ ENGINE BUG for the view: falcons.permits[].cannot = cannotBuyPermit(...)?.params['reason'] is null for inDebt and
  insufficientFunds (cashFor's errors have no 'reason'), so the facts say "can buy" when he cannot pay. Fix in the
  engine's view (reason ?? code.name) with a test; the phone must not compare cash and fee itself.

## العزبة's build list: the falcons' room; البنك's kinds
- ✗ presenter.dart:263–266 leaves Facility.falconRoom OUT of farm.facilities ("the phone's farm page has no row for it
  yet"): the worker must add it to the engine's view (with a test), and FAC in phone.js its name/icon/line.
  Its price 18,000 and the rush row as other facilities have them (RU().builds / buildNow: check falconRoom is in the
  rush facts). **D15** the row's words (not drawn in the 18 views).
- ✓ FalconLines.moneyKinds (catalog.lines.moneyKinds) for KIND in phone.js: «الصقور وأجهزة التتبع», «بيع الطرح»,
  «التصاريح», «عدة الطرح», «أكل الصقور». The line under each kind (e.g. a sale's bird and price) is not drawn: **D15**
  (ours: list). The base falls back to OTHER for an unknown kind.

## The calendar's card and summary with the trip's lines (views 16–18)
Card words: «قبل ما تمشي»; span «مخيم طرح بالحماد · لين 10 أكتوبر» «9 ليالي · من الخميس 1 أكتوبر · 600 كم، حوالي 7 ساعات
سواقة»; «يكفي 9 ليالي؟» water/feed rows (the calendar's own); «اللي يجي بالطريق»; «مخيمك»: «عدتك: 6 حمامات وشبك الحمام ·
ناقصك: الدربيل، الخيمة المتنقلة، شبك الطيور», «مؤونة المخيم · تكفي 10 أيام · ماء وأكل وبنزين»; end: stops list + «خلصت مؤونة
المخيم · خلص موسم الطرح»; note «وكل يوم بالمخيم يرجع لك من الفجر لين الساعة 10، وبالمسا ساعة…»; button «اطلع للمخيم».
Summary words: «اللي صار»; «9 ليالي · مخيم الحماد»; «طرحت فرخ شاهين بحري (مثال) · اليوم السابع · بغرفة الصقور»; «طلقت حر ·
اليوم الثالث: المزاد ما يقبله»; «المؤونة والبنزين · صرفت 1,350 ريال»; note «هذا مثال…».
- ✓ Trips.card: groundName, km, hours, nights, from, to, pigeons, has[], lacks[], supplyDays, suppliesEnough,
  oneDay(Possible), falcons (ready), refused. **D3** «600 كم، حوالي 7 ساعات» → the engine's 843 km and ~10 h.
- lacks[] gives «شبك الطيور والجربوع» (the picture shortens it «شبك الطيور»): words.
- the camp's stops: AwayStopKind.extra with extra = 'suppliesOut' | 'seasonEnd' | 'tripEnd' (campStop), and
  AwayStopKind.falconCare {name}: ✗ no words in FalconLines; base phone.js stopWords() has NO case for 'falconCare'
  or 'extra' (default «وقف التقويم» with no line). falconCare stops an ORDINARY calendar jump too (away.dart:364–380,
  any falcon at the farm with الدعو begun, outside the moult) — reachable in part B with no trip: the stop's words
  (and STOPS_TEXT's list on calCard) must be added; **D16** their words (not drawn: «صقرك يبي الدعو» etc.).
- summary.extra (✓ tripLines): counts only — nights, caught, released, stooped, flights, taken, suppliesUsed (DAYS of
  supplies, not riyals). ✗ the picture's «اليوم السابع», «طلقت حر», «اليوم الثالث», «بغرفة الصقور» (species and day) and
  «صرفت 1,350 ريال» (riyals = days × 150 would be worked out in the phone). **D17** the summary's words to the counts,
  or the engine gives day/species/riyals.
- the trip starts from the map (part C): the card's «اطلع للمخيم» must not be wired to StartTrip in part B; no
  temporary way to start a trip anywhere in the phone. Views 16–18 reachable only with a trip the harness starts by
  dispatch({type:'startTrip'}) — and then the calendar's jump must go by op tripNight, not away (check what the
  phone's calendar does on a trip: AwayRun on a trip of days without the camp's stops would skip them).

## NOT built (must be absent, nothing half-shown)
Views 9–12 (المهرجان, results), the «المهرجان» tab, partners («تشاركه»), the air rifle, «الملواح 18.906», the contests.

## The refusals' words (D4): every FalconLines.refusal line and the screen it can appear on in part B
routeClosed ×3 (closed(route)) — view 3 buy; lotGone, notALot — view 3; noRoom, roomFull — views 3, 5 (keep); permitHeld,
needsFalcon — view 13; gearFull ×2 — view 4; notHeld, auctionClosed — view 5; notKept, releaseMonths — view 7; falconAway,
moult — view 8 (and view 7's button). The trip/map ones (onTrip, notOnTrip, tooFar, noSupplies, noTent, offGround,
nearFarm, coast, reserve, notHuntingGround, outOfSeason ×2, noPermit ×2, night, notByDay, noQuarry, movingCar, notReady,
flownOut, noLure ×2, notLost) are part C's, except Trips.card.refused on the card (D3). Money: inDebt/insufficientFunds/
invalidAmount are the phone's own words (must say "cash only": owner's item 23, not "on the account").

## Sex forms
The engine's birds are female (trapping auction: females only; f.female true), the design's grammar is masculine
throughout (صقر/طير/شاهين: اشتريته، طرحته، جوازه، ادعه، يرضى، طلقته). The rule: ONE grammatical gender for the bird across
every line (masculine, as the design and the words صقر/طير). A line that switches to feminine for female birds
(اشتريتها) in some places only fails. (The design's own header: «القرموشة» and «الجير تبع» not species: no male names.)

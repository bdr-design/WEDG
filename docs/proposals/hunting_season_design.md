# The hunting season (موسم القنيص): design for the owner's approval

> **Status: design, awaiting the owner (13 Nov 2026).** Nothing here is built and nothing
> here is adopted. It draws the owner's decisions of 13 Nov (the top of
> [gdd_hunting_section.md](gdd_hunting_section.md), the draft of GDD section 13, and
> [hunting.md](hunting.md)) as pictures, and asks what is still his to decide.
> "[n]" is a source in [research-realism.md section 8](../research-realism.md). **Every figure
> there rests on search-result text only: no official page was opened.** "(game choice)" is ours.

## The pictures

| Picture | What it shows | GDD draft |
|---|---|---|
| `design/hunt/season_calendar.jpg` (`season.cjs`) | A year, Aug 2026 to Jul 2027: the falcons' lane, the season, the falcon festival's two disagreeing date ranges, the camels' lane from the engine; the new game's start and its first season; the two collisions | 13.1, 13.2 |
| `design/ui/phone_falcon.jpg` (`phone_falcon.cjs`, 13 views) | The home screen with ten apps; «نادي الصقور»: the auction, a falcon's page for a buyer and the bid, the player's falcon, الدعو, the festival, the race day, the race result, المزاين's result; «تصريح الصيد»: before it is taken, held (top and scrolled), and a violation | 13.1, 13.2 |
| `design/hunt/outing_1..9_*.jpg`, `outing_board.jpg` (`outing.cjs`) | The outing on real screenshots of the game: the two places as far pins, the place's card, driving out, parked, on foot with the falcon on the glove, the cast-off, the result, the banned place's warning, the fine after | 13.1 |
| `design/hunt/season_money.jpg` (`season.cjs`) | One season's costs against what it can bring, for a pastime and for a contest falcon | 13.1, 13.2 |

Each script's header lists every figure as real (with its source) or a game choice.

## What the views decide, and why

### The year, and a new game's first season

The season is 1 Sep – 31 Jan, autumn to 30 Nov, winter from 1 Dec [127][167]. الدعو is
September and early October [155]. Falcons are bought at the breeders' auction at Malham in
August [158] or at the national auction of wild-caught (طرح) birds, 1 Oct – 30 Nov [157].

**A new game starts on 1 October.** By then the season is a month old, Malham's auction is
past and most of the الدعو weeks are gone. So the first season is: buy a wild-caught bird at
the national auction (open), take its passport and the permit, give it الدعو for four weeks
(game choice: a falconer never flies a bird the week he bought it), and fly it from about
late October. In that same month the camel side asks for the grand festival's registration
(17 Oct – 24 Nov, from the engine).

The moult (المقيض) in spring and summer, when falcons are not flown, is drawn hatched: it is
not in our research yet (the reviewer's search only) and needs a source before it binds.

### The falcon festival's date, and where it collides

The 2026 edition is 17–30 Nov in two search summaries [157] and 25 Dec – 10 Jan in another
search [181]; 2025 was 25 Dec – 10 Jan [169][157]. The calendar shows both:
- **17–30 Nov:** its end meets مزاين الجوف (29 Nov – 2 Dec) and the last days of the grand
  festival's registration.
- **25 Dec – 10 Jan:** it falls inside the grand camel festival (1 Dec – 3 Jan).

The phone views draw the 2025 dates until the owner picks one or the club's page is read.

### Two apps, ten on the home screen

The owner named two: «تصريح الصيد» and «نادي الصقور». They stay two apps because they are two
real things: the permit is the state's, and it will also carry the air rifle's permit later;
the club holds the falcons, their passports, the auction and the contests. With the six apps
there now and the two approved and being built (المزاين, المحادثات: task T10), the home has
ten, in three rows of four. It fits the enlarged phone without scrolling (audited).

### الدعو (training)

One short care action each time the game opens, counting the days since (the draft's game
choice). What the player sees change is words, never a number: «يرضى بالبرقع والدس»، «ياكل على
يدك»، «يجي للملواح من قريب»، «يجي للملواح من بعيد»، «جاهز للمقناص» (the steps and their words are a
game choice; الدعو itself is real [155]). The scale (الميزان) shows the bird's weight in grams:
an observable a falconer reads daily [155], never standing in for skill. Two weeks untouched
loses a step (game choice). No الدعو in the moult.

### What a buyer sees, and what stays hidden

A falcon on the auction shows its species, age (فرخ under a year, قرناس over [169]), origin
(طرح or farm-bred), its span in inches (a saker at least 16 for the contests [169]) and its
weight: all things a buyer really sees. How it hunts and races is never shown: only its
outings and results tell, as with the camels' scores.

### The outing

1. The open hunting ground and the licensed estate (المحازة) are far pins on the map, as the
   mountains are. Open land west of the yard is the real Nafud edge; its exact place, the
   estate's place and their distances (14 and 22 km) are game choices, to check against a map
   for villages and farms at build.
2. The ground's card: what may be hunted there, the season, the distance. «روح بالجيب» takes
   the player there with the time passing (recommended; question 1).
3. Driving, from behind: the real HUD; only the gear while moving. The falcon rides hooded on
   its perch in the car, unseen.
4. Parked outside the farm and its surroundings, in season, by day, with a permit: the falcon's
   icon button joins the car's own row. **Parked is the law, not a game choice:** hunting from a
   moving vehicle is fined 100,000 [136]. Real falconers often slip from a car on the move; the
   game cannot.
5. On foot (first person, the owner's rule of 11 Nov): the hooded falcon on the glove, and one
   icon button at the edge: the hood comes off and the falcon is cast in one tap.
6. The flight: the falcon and the flushed stone-curlew; the lure (الملواح) button calls it back.
7. The result: a pin over the falcon where it came down; its card says caught or missed, the
   flight's time and distance (observables). Game is never sold [166]: nothing on the card is money.
8. A banned place (the farm and around it, towns, reserves, the coast to 20 km
   [127][134][135]), a closed season or night (an hour before sunset to an hour after sunrise
   [135], one source): the button shows in its warning colour; a tap opens the warning card with
   the fine in words (5,000 [136]); the player may still cast (as cheating at the festival).
9. Caught, the fine comes after, in the permit app (a badge on the phone button): «مخالفة».
   Who stops him is «الدورية»: the real body (الأمن البيئي) is not named (question 7).

**Why open land offers only الكروان:** the law. The stone-curlew is the falcon's quarry on the
open-land list [140]; houbara is confirmed only in the licensed estates [142], and whether it
may be hunted in open land this season was not found, so the game keeps it to the estate. A
falconer will ask why: this is why.

**The card in play** is new: today the place card is hidden in play (`body.playing #pop`).
The frames show it docked on the right, as on the map. On foot there is nothing else there;
in the car the card must sit below the car's row (a build note).

**What a frame costs:** the base of each frame was counted from the WebGL calls (main pass and
shadow pass, `design/hunt/outing_draws.txt`; SwiftShader at 956x440, the counts are the
phone's, the times are not). The new models are **estimates until task T11 measures them**:
the falcon about 2–3k triangles, 1 draw and 1 shadow draw (its 1 m span is over the 30 cm
rule); a stone-curlew about 2k and 1 draw.

| Frame | Base, measured (main + shadow) | With the new models (estimate) |
|---|---|---|
| 1 the map looking west | 118 draws / 155k | pins only: +0 |
| 3 driving, from behind | 72 / 143k | the falcon unseen in the car: +0 |
| 4 parked, from behind | 74 / 143k | +0 |
| 5 on foot, falcon on the glove | 58 / 227k | +2 draws, +3k (falcon and its shadow): 60 / 230k |
| 6 the flight | 34 / 104k | +3 draws, +5k (falcon, its shadow, a stone-curlew) |
| 7 the result | 34 / 104k | +3 draws, +5k |
| 8 on foot by the yard | 78 / 197k | +2 draws, +3k |

All far under the ADR's 200 draws and 400k triangles. (The base on foot here, 58 / 227k, is
lower than the 167 / 394k counted on foot by the car at the yard: out in the open there are no
pens, buildings or grass cells in view.)

None of the outing frames is near the herd: the hunting ground is kilometres away and the farm
is a banned place. The heaviest outing frame is on foot by the car with the falcon on the glove: about 60 draws and 230k triangles (estimate on a measured base).

### The contests

الملواح: a 400 m race from the release to the lure [169][171] (300 m in an older edition, 200 m
also reported [183]). Classes الملاك، الهواة، المحترفين، النخبة [169][171]; the player starts in
الملاك (game choice). The round's day in the phone, as the camels' round is: the times come in
through the day, the player's falcon flies, its time is told to three decimals like the real
ones. The first two of the owners' round are real (17.905 and 18.061 s, 2025 [182]); the game's
times run about 16.5–19 s (game choice inside the real 16.549 s reported as a record [183] and
the 2025 winners 17.653–18.061 s [182]). Prizes by place are a game choice (the real split is
unknown: [169] and [176] disagree), down to the 7th place (about seven prizes a round:
1,012 prizes over 139 rounds in 2025 [170][176]).

مزاين الصقور: classes الحر and الجير بيور, each فرخ and قرناس, شاهين بحري قرناس, حر فرخ إنتاج
محلي [172]; judged of 100 over seven parts by three judges [172][173], **scores never shown**:
places and prizes only. First three 300,000, 175,000, 100,000 [177] (one source); the 4th and
5th split the round's remaining 50,000 (uncertain: game choice). At most five falcons a round
[175] (one source; whether a round or a falconer is not clear). Beauty is the bird's own;
الدعو does not change it (game choice).

القرموشة and الجير تبع, in the race's species list [169], are likely sex or size classes (the
male saker is called مثلوث or قرموشة by different sources; تبع the male peregrine): they are
not drawn as species. Unresolved.

### Money (the owner's decision)

`season_money.jpg`: a wild-caught saker and a season of outings costs about 48,000 and returns
about 45,000 if sold (both game choices); hunting itself earns nothing [166]. Contests: about
one falcon in five wins anything (1,012 prizes [170][176] for more than 5,200 falcons [157]: an
estimate from two sources), so most seasons are a small loss and a rare one a large gain
(a third place at المزاين is 100,000 [177]).

## Where the later parts attach (not designed here)

- **The air rifle (الساكتون):** a second kind of permit in «تصريح الصيد», a rifle's licence, and
  a button in the car's row beside the falcon's.
- **The Kalashnikov:** never in these apps or on any lawful screen; bought through a secret
  chat in «المحادثات» as the festival's cheating is; if caught, seized, fined and reputation down
  (the owner's decision), told as the violation here is.
- **Wolves and stray dogs:** a rare night event at the pens, defended by the pen, the herdsman
  and a guard dog bought in «العزبة»; killing a wolf never lowers the danger (the owner's decision).

## Questions for the owner (recommendation first)

1. **How much of the outing the player plays.** *Recommended:* he drives within the ground,
   looks, parks and casts himself; the flight and its result come from the falcon's hidden
   skill, the ground and luck. *Other options:* (b) he also steers the falcon's stoop (closer to
   a game of skill, more on the phone: a chase camera on the bird); (c) a result worked out from
   the card alone, with no outing in 3D (lightest, loses the hunt).
   > الطلعة: تسوق بالبر وتدوّر وتوقف وترسل الصقر بنفسك، والنتيجة من الصقر والأرض والحظ؟ ولا تبي توجّه الصقر بنفسك وهو ينقض؟ ولا تطلع النتيجة من البطاقة بدون طلعة؟ نقترح الأولى.
   And the trip there: *recommended* «روح بالجيب» from the card, with the game's time passing;
   *or* drive all 14 km.
2. **The falcon at the farm.** *Recommended:* the falcon lives on its perch (الوكر) under the
   tent's shade (بيت الشعر) or the room's porch, seen only when the camera is near, with no pin
   of its own: its care is in the phone. Its cost near the herd: about 2–3k triangles and two
   draws when within sight, nothing when far (one static perched pose, no animation:
   estimate). *Or:* a mews as a place with its own pin and card (more to tap on the map; the
   map stays clear only if the pin shows when near).
   > الصقر بالعزبة: يقعد على وكره تحت بيت الشعر ويبان لما تقرّب، ورعايته من الجوال؟ ولا تبي له مكان بدبوس وبطاقة؟ نقترح الأولى.
3. **The camels while he is away.** *Recommended:* nothing stops: the herd goes on as it does
   when the player is anywhere else (feed, water and the herdsman as they are), and a trip takes
   game hours, not days. *Or:* a longer trip (a camp of days, as real falconers do [155][156])
   leaves the herd to the herdsman, and without one the herd's daily care waits.
   > الحلال وانت بالمقناص: يمشي مثل ما هو وكل شي على حاله، والطلعة ساعات؟ ولا تبي طلعات أيام بمخيم والراعي يمسك الحلال؟ نقترح الأولى.
4. **The falcon festival's date.** *Recommended:* the 2025 dates (25 Dec – 10 Jan), the last
   edition the sources agree on, inside the camel festival: the player chooses. *Or:* 17–30 Nov.
   Both stay a game choice until the club's own page is read.
   > مهرجان الصقور: نخليه 25 ديسمبر لين 10 يناير مثل آخر نسخة مؤكدة، ويصادف المهرجان الكبير للإبل؟ ولا 17 لين 30 نوفمبر؟ نقترح الأولى لين نقرا صفحة النادي.
5. **Pastime or second business.** *Recommended:* a pastime that costs, with a rare large prize,
   at the real odds (about one falcon in five wins anything).
   > الصقور هواية تصرف عليها ومعها فرصة نادرة بجايزة كبيرة، ولا تبيها تجارة ثانية؟ نقترح الأولى.
6. **A lost falcon.** Real: a falcon can fly off and be lost; falconers search by its tracker.
   *Recommended:* yes, rarely, when it is cast far or too heavy, with the tracker shown as a
   direction on the map until it is found or given up. *Or:* never lost.
   > الصقر ممكن يضيع بالواقع ويدورونه بجهاز التتبع: تبيه يضيع أحيان؟ نقترح نعم بس نادر.
7. **Who stops the player.** The real body is «الأمن البيئي». *Recommended:* the generic «الدورية»,
   as the names decision does for the apps. *Or:* the real name.
   > اللي يوقفك لو صدت بمكان ممنوع: نكتب «الدورية» عامة، ولا الاسم الحقيقي «الأمن البيئي»؟ نقترح «الدورية».
8. **Still open from the draft (13.6):** aiming with the air rifle (recommended: a tap on the
   flock, the result by chance and reach) and cheating in falcon contests (recommended: not now,
   until the Saudi penalty is found [179][180]). Unchanged by this design.

## Not sure

- The 30 species of this season, the bag limit and the permit's fee were not found; no list or
  limit is shown, and the fee (100) is a game choice.
- The moult's months, the word الهدد (two readings), and the Saudi words for the hand that carries
  the falcon and its sex names were not checked against a source; the left hand in the frames is
  a stand-in's pose, not a claim.
- Whether "five a round" [175] counts falcons per round or per falconer.
- The phone views' race and beauty results are samples (names, fields and places invented).

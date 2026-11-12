# Gameplay build plan

The owner chose to build the game itself next (12 Nov 2026), after approving
the GDD's eight decisions (GDD section 11). This plan turns the approved GDD
into play in the order that gives him something to try soonest. Every step is
built by Claude, checked by an independent review before it is shown or
committed as done, and every fix is reviewed again (CLAUDE.md).

## Where things stand

- **The rules engine** (`packages/marah_domain`, pure Dart, 39 tests passing)
  has camels with hidden genetics and judged traits, a market with listings,
  offers and quick sales, mating with own bulls and studs, illness and
  treatment, shepherds, farm expansion, contest rounds and judging, a daily
  pipeline, saves with migrations, and views that never show hidden values.
- **It predates several approved decisions** and contradicts them:
  - Seven colour families, with مغاتير as a family. The GDD says six, and
    مغاتير is only an umbrella name.
  - Age classes put لقي before حق, have no مخلول, and stop at فاطر. The GDD
    says حق then لقي, then ناب/عود; research section 2 adds هرش past 20.
  - Rounds are colour × sex × age year: the UAE/Qatar format. The GDD says
    the Saudi system: فردي دق/جل by colour, مفاريد, دق, الفحل وإنتاجه, الجمل,
    المنقية, الهجيج, الطبع, البداوة, with registration rules and six check
    stages.
  - Feed is a fixed weekly plan (`SetFeedPlan`). The GDD says barley, alfalfa
    and water are stocks that run out and are ordered.
  - There is no cheating. The GDD (7.1) allows it, with the real checks,
    fines and bans.
  - There are no auctions with computer bidders.
  - Judging weighs the traits its own way (head 0.16, nose 0.12, …), not the
    approved 25/20/15/10/30, and scores مجاهيم and مغاتير alike. Its ears
    trait asks for small ears; GDD 5.3 says مجاهيم ears are long.
  - Several numbers marked (field) disagree with the GDD's sources:
    - gestation 385 ± 10 days (377 on average, range 356–410);
    - first mating at 4 years (about 3.3);
    - a shepherd's wage of 2,200 (1,000–1,500);
    - 300 days' rest after calving (an interval of about 23 months, or 15
      when mated within 3 months);
    - the illness list lacks القراع, الجدري and البروسيلا;
    - a Tabuk festival in month 15 (the real one is in June).
- **The 3D prototype** (`design/prototype3d`) is the world the owner plays in
  on his iPhone. Its phone apps and place cards show fixed sample data.

## Steps

### G1. The rules engine to the approved GDD (no screens)

Each part comes with its tests and a save migration. Parts 1 to 3 come
first, then G2 and G3, so the owner has something to play before the rounds
and cheating (parts 4 and 5) are built.

1. **Catalog:**
   - Six colour families, with `isMaghateer` for the five light ones; the
     descriptions are taken from research-realism.md section 1.
   - Age classes from research section 2: حوار, مخلول, مفرود, حق, لقي, جذع,
     ثني, رباع, سديس, فاطر, ناب/عود, هرش.
   - Old saves map مغاتير to وضح, the white family it described.
2. **Judging and the (field) numbers:**
   - The approved weights: head and neck 25, hump and top line 20,
     forehand 15, hindquarters 10, overall look 30 (GDD 5.3).
   - The traits judged against the مجاهيم standard or the مغاتير one where
     the GDD says they differ: the ears, bone and feet, withers and back.
   - Every (field) number checked against the GDD and research, and changed
     or remarked as a game choice.
3. **Provisions:**
   - Barley (50 kg bags), alfalfa and water (litres in the tank) are stocks.
   - Daily use comes from each camel's need: 8–17 kg of dry matter and
     37–46 L for a nursing camel (real); water for the others is a game
     choice.
   - Orders have the real prices where sourced and a delivery delay (a game
     choice).
   - A shortage lowers body condition and raises illness, and body condition
     shows on judging day.
   - `SetFeedPlan` goes.
4. **The Saudi round system:**
   - Round types and who may enter each, from research section 2.
   - Registration rules from GDD 7: one فردي and one جمل entry per owner; no
     camel in both; colour and class fixed at closing; closing 72 hours
     before the round, with a late fee.
   - The six stages on the day, each able to remove an entry.
   - Prizes per round type stay game choices.
5. **Cheating (GDD 7.1):**
   - A secret treatment raises a judged trait. The types and their fine caps
     are real.
   - Detection by the tampering experts and the medical committee is a game
     choice and rises with the strength of the treatment.
   - If caught: disqualification, the fine, a ban on the owner and his camels
     for the current edition and five more, a reputation loss, and news.
   - A small chance of being caught outside festivals, in the market or
     through the vet (the 2018 MEWA fines, real).
   - Rivals cheat too.
6. **Auctions:** computer bidders with hidden ceilings drawn from each
   camel's valuation; the commission rule as in the market.

### G2. The engine inside the prototype

- The Dart engine is compiled to JavaScript (`dart compile js`) and run in a
  Web Worker, so the world's frames never wait for it.
- The page sends commands and receives the player's view (`GameView`, which
  never carries hidden values).
- The same file runs in the iPhone app and in the headless browser tests.
- **Saves go through the iPhone app to a file**, over a JavaScript channel.
  The page's own storage would be lost: the app serves the page on a new
  port each launch, so its origin, and the storage tied to it, changes; and
  a worker has no localStorage. In the browser tests a stand-in keeps them.
- The worker's entry point (it needs `dart:js_interop`) lives outside
  `marah_domain`, which stays pure Dart.
- CI compiles the domain to JavaScript and runs its tests there too
  (`dart test -p node`), and checks that a fixed seed plays the same on the
  native build and in JavaScript. Doubles are written to JSON differently by
  the two ("72" and "72.0"), so a save never moves between them.
- The Flutter game app keeps the native engine and SQLite store
  (ARCHITECTURE.md). This is only how the prototype gets the real rules.
- Measured: the worker's cost per game day, the bridge's message sizes, and
  the frame time with the engine running, so it is not guessed. These say
  nothing about the Flutter app's smoothness, which runs the native engine
  and its own runtime: ARCHITECTURE.md says so too.

### G3. The first things to play (the design shown before it is built)

- **The yard's camels are the engine's camels:** names, ages, colours,
  pregnancies and illnesses on their cards. One the player buys arrives by
  truck; one he sells leaves the same way.
- **Water and feed:** the tank and the store drop day by day, and are
  ordered from the phone's الوايت and العلف apps. The water truck drives in
  to the tank.
- **الحراج and the bank:** the engine's listings, buying with the
  commission, selling, and the balance and ledger.
- **Time:** a real day is a game week (approved). The date and season are
  shown in the phone.

### G4. Festivals

- Registration in the phone's المزاين app.
- The day's six stages and the results.
- Cheating as an action with its risk.

### G5. The rest of the approved GDD

- Breeding with own bulls and studs.
- The vet by visit or contract.
- Shepherds and the shepherd-to-herd ratio's effect on conception (real).
- More farms and facilities.
- The auctions' screens.
- Whatever the owner approves from GDD section 12.

## Not decided here

- The owner's choices in GDD section 12 (milk, embryo transfer, cloning,
  zakat, moving to spring pasture).
- Every new screen's layout: shown as pictures or a prototype first.

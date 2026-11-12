# Gameplay build plan

The owner chose to build the game itself next (12 Nov 2026), after approving
the GDD's eight decisions (GDD section 11). This plan turns the approved GDD
into play in the order that gives him something to try soonest. Every step is
built by Claude, checked by an independent review before it is shown or
committed as done, and every fix is reviewed again (CLAUDE.md).

## Where things stand

- **The rules engine** (`packages/marah_domain`, pure Dart, all tests passing)
  has camels with hidden genetics and judged traits, a market with listings,
  offers and quick sales, mating with own bulls and studs, illness and
  treatment, shepherds, farm expansion, contest rounds and judging, a daily
  pipeline, saves with migrations, and views that never show hidden values.
- **It predates several approved decisions** and contradicts them:
  - Seven colour families, with مغاتير as a family. The GDD says six, and
    مغاتير is only an umbrella name.
  - Age classes put لقي before حق, have no مخلول, and stop at فاطر. The GDD
    says حق then لقي, then ناب/عود and هرش. (Done: G1 part 1.)
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

**Progress (12 Nov 2026):** G1 parts 1 to 3 are built and reviewed: the six
colour families and the approved ages (save v2); judging by the approved
weights, the (field) numbers to their sources and the illnesses (saves v3,
v4); feed and water as stores that run out and are ordered (save v5).
G2 is built but for the phone's numbers:
- **The engine in the page:** compiled to JavaScript (`tool/proto_engine`,
  its worker 270 KB, 83 KB gzipped) and run in a Web Worker
  (`design/prototype3d/engine.js`), once the yard has loaded. It takes every
  command as JSON and sends the main screens' view (the player's snapshot)
  as JSON; the detail views (a camel, a festival, a page of the herd) get
  theirs with G3, which needs them.
- **The save:** in the iPhone app, files behind the app's own server
  (`/save`, a key per launch in the page's address), which the worker reads
  and writes itself, so the page's thread never holds the save's text; a
  request that does not answer within 15 s is cut off and counts as failed.
  Each write is numbered, and the app's server refuses one older than a
  write it has applied (a request cut off here can still arrive late).
  In the browser tests the page keeps it in localStorage and answers each
  write. Either way a write that fails reaches the engine, which reports it
  and tries again.
- **Same seed, same game:** two years of the scripted bot, with every
  command it does not send itself added, give the same state, hashed every
  four weeks, on the Dart VM and in node; the save JavaScript wrote reads
  back on the VM to the same state. The domain's tests also run in node. The
  save format's tests (marah_data) use files and do not; its migrations run
  in node only as far as the same-seed save shows.
- **Measured** (the worker's own work is on its thread, not the frame's): a
  new game or the saved one is up 0.1 to 1.8 s after the yard (desktop,
  software renderer); the snapshot is 25,000 characters and the save 59,000
  at the start, the snapshot read on the page's thread in under half a
  millisecond after the first. At 10,000 head, in
  node on a desktop: the save is 6.7 MB and takes 417 ms to write as text, a
  game day 24 ms, a snapshot 118 ms (22 ms on the Dart VM); with the request
  to the app's server a command at that size answered in 0.76 s in Chromium
  (the review's measure), the page's thread free all the while (no frame
  later than 17 ms). The frame meter (`#fps`) shows
  the page's side on the phone: reading each view and keeping the save.
  What the phone itself says is still to come.

## Steps

### G1. The rules engine to the approved GDD (no screens)

Each part comes with its tests and a save migration. Parts 1 to 3 come
first, then G2 and G3, so the owner has something to play before the rounds
and cheating (parts 4 and 5) are built; the auctions (part 6) come with G5.

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
   - The feed plan stays as the ration (how much each camel is fed a day),
     drawn from the stores instead of paid by the day.
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
- **Saves go through the iPhone app to a file**, over the app's own local
  server (the one that serves the page), which the worker calls itself. The page's own storage would be lost: the app serves the page on a new
  port each launch, so its origin, and the storage tied to it, changes; and
  a worker has no localStorage. In the browser tests a stand-in keeps them.
- The worker's entry point (it needs `dart:js_interop`) lives outside
  `marah_domain`, which stays pure Dart.
- CI compiles the domain to JavaScript and runs its tests there too
  (`dart test -p node`), and checks that a fixed seed plays the same on the
  native build and in JavaScript. Doubles are written to JSON differently by
  the two ("72" and "72.0"), so the check hashes a canonical form of the
  whole state, not the save's text; and the save JavaScript wrote is read on
  the Dart VM and must give the same state.
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

- Breeding with own bulls and studs; mating within 3 months of calving (a
  15-month interval, real) as the owner's choice with its cost, not every
  camel's (G1 part 2 review).
- The vet by visit or contract, with tests: brucellosis (البروسيلا) comes in
  with them, as it really is: spread by abortions and milk, causing abortion,
  not cured, the infected camels culled.
- Shepherds and the shepherd-to-herd ratio's effect on conception (real).
- More farms and facilities.
- The auctions' screens.
- From GDD section 12 (the owner, 12 Nov): milk, embryo transfer, moving to
  spring pasture, and zakat computed the way ZATCA computes it (its table
  and conditions taken from ZATCA's own guide when built). No cloning.

## Not decided here

- Every new screen's layout: shown as pictures or a prototype first.

# Task T10: build المزاين and «المحادثات» in the phone, on the festival engine

Read $SC/agents/GUIDE.md first (SC = /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad),
then /home/user/WEDG/CLAUDE.md. Base commit: the session branch's head at the time you start
(`git -C /home/user/WEDG rev-parse claude/vigilant-noether-nydua2`; it holds the festival engine, the bank, and the
approved design). Worker's worktree: /home/user/wt/t10, branch wt/t10. Reviewer's folder: $SC/t10_review.

## What the owner approved (13 Nov 2026)

- The nine views in design/ui/phone_mazayen.jpg, drawn by design/ui/phone_mazayen.cjs from real games (read the
  script whole: its header lists what the build needs from the engine; its code is the exact words and layout).
- Cheating lives in a secret dealer's chat, reached through a NEW «المحادثات» app in the phone; the dealer messages
  after a registration. The festival's own app never offers it.
- The round's day is told stage by stage through the day, with a notice at each stage (the hours a game choice).
- Every decision the owner made on festivals, cheating, debt and the account: $SC/agents/T3_T4_owner_decisions.md
  (read all 18; they bind every word). The rules themselves: docs/GDD.md sections 7, 7.1, 8, 9.

## Build (part A)

1. The engine's side first (packages/marah_domain, marah_runtime; tool/proto_engine; design/prototype3d/engine.js),
   so the phone copies nothing and probes nothing:
   - a festival(id) call on the page's engine (the design's script posts the worker's op itself);
   - result rows with the owner's name; the player's own camels that cannot enter a festival, each with its round
     and the refusal code and its parameters (the design probed with real entries: never do that in the app);
   - the whole herd for registering, camels still on the truck included;
   - each festival's top first prize over the rounds a player can enter, with the round's kind;
   - what the day's telling needs: each stage's outcome for the player's entry and the field left after it, in the
     six stages' order, and when each stage is told (the hours are a game choice: propose them from the game's day,
     write them in the GDD as a game choice). The round is still judged at once by the engine: the telling is a
     view over its result that reveals nothing early (no later stage's outcome may be in the snapshot or the page
     before its hour: the views never expose hidden values) and loses nothing if the phone was closed;
   - the dealer's message as something the engine raises after a registration (who he is: a generic name, a game
     choice), kept until read, not lost if the phone was closed or the app restarted;
   - findings outside a sale told from engine state, not the event list (today's phone scans the snapshot's last
     40 events and remembers in memory: a finding can be missed or told twice): an untold list in the snapshot
     (camel, kind, fine, whether he knew), marked told by a command;
   - the room left on the merchant's account and, for each order the phone can make (each tanker, the feed order's
     total), whether it goes through and how much lands on the account (today phone.js copies the rule);
   - reputation as a band or a word the GDD allows, not a number, wherever the screens say it rose or fell;
   - names: follow one practice for Arabic names of kinds, features, round kinds, stages, colours and refusal
     reasons (the phone's own word tables, as its other apps do, or the engine's catalog sent in the snapshot):
     choose, say why, and leave no third copy.
   Any new state goes into the save with a new version and a migration (the session branch writes v8 today; treat
   v8 as released: the owner's phone may hold one). Hidden values stay hidden; same seed on the VM and in
   JavaScript; the 10,000-head budgets; snapshot size before and after.
2. The phone (design/prototype3d/phone.js): المزاين as approved (the festivals list with the player's entries and
   withdrawal; a festival's page; registering with each camel's round or reason; the cost; the round's day told by
   stage; the result; the day a treatment is found, with the fine, the ban, the negative balance and the account's
   words) and «المحادثات» with the dealer's chat (the seven kinds, the strength, stacking, the full warning, the
   treatment bought). The phone's own pieces and guards as its other apps have: the screen-change tap guard, the
   order double-tap guard, two-tap confirmation for what cannot be undone (registering costs transport; a treatment
   is illegal and costs money: both confirm), keyboard focus kept across redraws, the live region, counting nouns
   in all four forms, numbers with their words, sex forms. A notice (a registration open, a stage told, the
   dealer's message, results) must follow the game's rule that nothing written floats over the game: use what the
   phone already uses for الحراج's offers (the badge), and say what you did.
   No per-frame work: an app redraws only when what it shows changed (count rebuilds on the fast clock).
3. Tests: domain and runtime tests for every new field and rule; proto_engine page checks; a page harness that plays
   real games (seed 4242 as the design did: an entry cut at the preliminary; a treatment found; and, on a seed or a
   herd where it can happen honestly, an entry that places) and shoots every view at 956x440 with the phone
   enlarged, set beside the approved picture view for view (say every difference); the layout audit
   ($SC/t4_review/h/audit.js) and the words lint the design's reviewer used ($SC/t4_review/h/) on every view.

## Design first, do not build (part B)

الحراج gained rules its screens do not show: a vet's check before buying (CheckListing, SAR 500, a second opinion on
another day, "checked N times, nothing found"); a listing declared as treated; a treated camel sold declared by an
owner who bought her unknowing (decision 15: at her natural price, no fine; refused for one who treated her
himself: ownTreatment; nothingToDeclare). The owner's rule is that a design is shown before it is adopted: draw
these as design views the way design/ui/phone_haraj.cjs and phone_mazayen.cjs do (real games, the phone's real
pieces), as design/ui/phone_haraj_vet.cjs / .jpg with a README row "awaiting the owner's approval", and bring the
questions that are the owner's with your recommendation first. Do not put them in phone.js.

## Measure and report

The guide's checks, all of them. Snapshot and festival-page size and build time at day one, one year, ten years and
at 10,000 head, before and after. Rebuild counts on the fast clock. The comparison pictures. Each new Arabic line
in full in the report. The GDD and design/prototype3d/README.md updated to what is built. What you did not do.

## Left open on purpose

- The group rounds (الجمل، المنقية، البداوة، الهجيج، الطبع): shown as coming later, as designed.
- Falcon contests and hunting. The ledger's folding (its own task, after this one: do not touch the ledger's form).
- A news list in the phone.

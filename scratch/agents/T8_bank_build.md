# Task T8: build the bank app on the engine (the owner approved the design, 13 Nov 2026)

Read $SC/agents/GUIDE.md first (SC = /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad).
Base commit: 23116d1 (the session branch's head; it holds the approved design: design/ui/phone_bank.cjs, .css, .json,
.jpg, phone_bank_data.dart). Worker's worktree: /home/user/wt/t8, branch wt/t8. Reviewer's folder: $SC/t8_review.

## The owner's decisions

- The design in design/ui/phone_bank.jpg is approved as drawn.
- The main screen's month rows are option B: each month says its biggest movement («أكبرها: ...»), not in/out totals.
  Option A is dropped: remove it from the design files' picture so the design folder shows what was adopted (redraw
  phone_bank.jpg with the adopted screens only, README row changed from "awaiting" to approved with the date).
- السعي is folded into its sale: the sale's row says what reached the player, with the price and the commission in
  its detail line, as the design draws it.

## What is wanted

البنك working in the game page's phone (design/prototype3d/phone.js), on the rules engine, exactly as the approved
picture: the main screen (balance, today's movement, the months with their biggest movement), a month opened (its
rows by kind, in and out apart, the net), and the day-one state. It is the phone's sixth app; whatever the approved
design says opens it (the balance on the home screen) opens it.

1. The engine's side. The snapshot JSON carries no ledger today. Add what the screens need, and only that
   (packages/marah_runtime: view_models.dart, presenter.dart, snapshot_json.dart; the domain's ledger is in
   packages/marah_domain model/player.dart and views.dart). design/ui/phone_bank_data.dart shows how the design's
   figures were derived from the engine: the snapshot must give the page the same figures without the page doing
   the engine's sums. If the ledger does not record something the approved rows show (which feed and how much, which
   camel, the price and commission of a sale), record it in the domain where the entry is written, with a save
   migration if the save format changes (see how earlier versions migrate; note T3, not yet integrated, also bumps
   the save to v8: say in your report which version you used so the director can order the two).
   Bounds: the ledger must not grow without limit in the save or the snapshot over a ten-year game (measure the
   save's size and the snapshot's size and build time at ten years, before and after; if entries must be folded
   into month summaries after some age, say what is kept and what is lost: losing a detail the player could see is
   the owner's decision, bring options).
2. The page's side: the app in phone.js with the phone's own pieces and words, the screens as approved. Keyboard and
   screen reader use as the other apps (focus, the live region). The guards the phone already has (the screen-change
   tap guard) apply. No per-frame work: the app redraws on a snapshot change only when what it shows changed.
3. Tests: domain/runtime tests for the ledger view (sums equal the balance's change; the biggest movement; the
   folded commission; month boundaries; the day-one state; a ten-year bound), the proto_engine page checks, and a
   page harness (like $SC/haraj/run.js) that plays a real game (seed 4242, fast clock or scripted through
   window.marahEngine) and shoots the three screens for comparison with the approved picture.

## Rules that bind it

Every figure the engine's own; Gulf Arabic as the phone speaks and the counting rule (GDD section 8); numbers keep
their word; no loans, transfers or interest (the GDD has none); no hidden values (nothing of another seller's
reserve, a camel's true value, etc. may ride in a ledger note); nothing written over the game.

## Measure and report

- The checks in the guide (all of them: you touch Dart), `dart run marah_domain:simulate 10 4`, same seed VM = JS.
- Snapshot size and build time, save size: day one, one year, ten years; before and after.
- The page: the three screens shot at 956x440 (phone enlarged) beside the approved picture; say every difference.
- docs: docs/GDD.md's bank lines and design/prototype3d/README.md updated to what is built.

## Left open on purpose

- Loans, transfers, zakat or any bank feature the GDD does not have.
- The festival engine's entries (T3) are not in this base; do not anticipate them beyond naming the kinds.

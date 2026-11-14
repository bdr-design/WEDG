# Task T18, part B: the hunting season in the phone, on the engine of part A

Read docs/agents/GUIDE.md first, then /home/user/WEDG/CLAUDE.md. Base: the commit the director names when you start
(the session branch with part A's engine on it, or wt/t18's head if part A has not landed yet). Worker's worktree:
/home/user/wt/t18b, branch wt/t18b. Reviewer's folder: $SC/t18b_review. Commit often. Never push.

## What the owner approved, and what is his word

- The design: design/ui/phone_falcon.cjs and .jpg (18 views; read the script whole: its code is the exact words and
  layout), docs/proposals/hunting_season_design.md. «اعتمده وابدأ البناء: … المحرك أول، ثم الجوال، ثم المخيم والمقناص
  بالخريطة. كل جزء يمر على مراجعه.»
- His decisions: docs/agents/hunting_owner_decisions.md; docs/agents/owner_decisions_2026-11-14.md items 5–9, 17–19,
  22–25; docs/agents/T18_answers.md (what the engine was built to, with the points still provisional).
- The engine: part A's report names every command, view and line (docs/GDD.md section 15; `falconFacts` in the
  snapshot's `falcons`; `falconCatalogOf` asked once by the worker op `falconCatalog`; `Trips.card` by `tripCard`;
  `tripNight`; `FalconLines`). The phone copies no rule and probes nothing: if a screen needs a fact the engine does
  not give, add it to the engine's view with a test (and say so), never compute it in phone.js.

## Build

Two new apps in the phone, by the owner's generic names: «نادي الصقور» and «تصريح الصيد».

1. «تصريح الصيد»: the two permits (season, open or closed, held, the fee, buying with two taps, the refusal's words:
   the hunting permit needs a falcon with its passport), where each is banned, what is released (the four lines word
   for word), the fines in words (views 13–15).
2. «نادي الصقور»:
   - the auctions told apart, each route in its dates, open or closed (view 2);
   - tonight's lots as the bidders see them (view 3), and buying one;
   - الطرح: the trapping permit's state and the gear he has, has coming and lacks, with prices, ordering (cash only,
     delivered next day), what each item does in words (view 4);
   - a held bird (trapped, not yet sold or kept): entering it at the auction (view 5), the hammer (view 6), keeping
     it (needs a place in the room), and what happens at the close;
   - his falcons (view 7): each with how it came, its passport, الدعو's state, its tracker; releasing a kept trapped
     peregrine in its dates;
   - الدعو (view 8) with the engine's rule (the days since count; two weeks left steps back; none in the moult).
3. The falcons' room in العزبة's build list (the facility table's new row; its price, the rush row as other
   facilities have it), and the bank's new kinds in the bank app («الصقور وأجهزة التتبع», «بيع الطرح», «التصاريح»,
   «عدة الطرح», «أكل الصقور»).
4. The calendar's card and summary with the trip's lines (views 16–18) wherever the phone already shows them; the
   trip itself starts from the map (part C): build no temporary way to start one.
5. NOT built (the views stay out, with nothing half-shown): the festival and the contests (views 9–12), partners,
   the air rifle. The home screen shows the two new apps only (the rule of 13 Nov: unbuilt apps are hidden).

## Design first where the approved pictures do not cover the engine (show before building in)

The engine differs from the approved pictures in a few places. For each, draw the view in the design's own manner
(add it to phone_falcon.cjs or a sibling script, from a real game on the engine), put the pictures in your FIRST
report, and build it behind the same code path so that the owner's answer changes words or layout only:
- buying a lot with his own ceiling («أعلى مبلغ تدفعه»): the ceiling's entry (the phone's own stepper, not a
  keyboard, unless the phone already has a number field pattern), the two taps, the two outcomes (bought at the
  hammer; gone to another bidder at a told price), and what the lot's row shows after;
- a held bird's three ways (enter tonight; keep; and what the close does), with no room or a full room;
- الحماد's card words (843 km and about 10 hours, not «600 كم، حوالي 7 ساعات»);
- the refusals' words where a button warns (about forty lines the engine's worker wrote: list every one with the
  screen it appears on, for the owner's eye).

## The phone's standards (as every build here)

The screen-change tap guard, the order double-tap guard, two taps for what cannot be undone or costs money, keyboard
focus kept across redraws, the live region, counting nouns in all four forms, numbers with their words, sex forms
(the falcon's grammatical gender held the same across every line), 'Marah Figures' for figures, keepTogether for a
figure and its word, no per-frame work (an app redraws only when what it shows changed: count rebuilds on the fast
clock), nothing written floating over the game (a notice is the badge, as الحراج's offers). The catalog is asked
once and kept; the snapshot's `falcons` is read as it is.

## Tests and measures

- A page harness that plays real games on the engine (the game opens on 1 October: the trapping auction is open;
  the calendar reaches August and the exhibition) and shoots every built view at 956x440 with the phone enlarged
  and small, beside the approved picture view for view; every difference listed with its reason.
- Each command's path: bought, refused with each reason's words on screen and in the live region, the two-tap
  guards, a double tap, a tap during a screen change.
- The layout audit, tool/page_checks (longpress, type_audit, keep_together, fonts_start, money_meter), the words
  lint; every other screen unmoved (the box comparison against the base on the phone's other apps).
- Weight: rebuild counts per snapshot on each new screen; the page's start time and draws unchanged; the catalog's
  size and when it is asked.
- Hidden values: nothing in the page's memory, the DOM or the live region gives a lot's worth or a falcon's skill
  before the engine tells it.
- The full CI; same seed unchanged; if the engine's views change, the budgets again.

## Report

The guide's report, with: the built views beside the approved ones; the design-first pictures and their questions
(recommendation first); every Arabic line that differs from the design and why; the measures; what is owed; the
steps for the owner's phone test, in Gulf Arabic.

## For the reviewer

Phase 1: the baseline of the phone's other screens (boxes, texts, rebuild counts, draws at start) at the base; a
table of every view and every command path the brief asks for, with the design's words for each (from
phone_falcon.cjs) and the engine's facts each needs; the checks you will run. Phase 2: each view against the design
and the engine by your own harness; the standards above; hidden values; the unmoved screens; weight.

# Task T15, part B: build rushing and the calendar, on a side branch, off the owner's phone build

For the same pair as part A (worker's worktree /home/user/wt/t15, branch wt/t15; reviewer's folder
$SC/t15_review). Read docs/agents/GUIDE.md again, the part-A brief docs/agents/T15_rush_and_calendar.md, your own
note docs/proposals/rush_and_calendar.md as revised, and docs/agents/proxy_decisions.md batches 4, 4b and 4c.

## The rule for tonight (the proxy's answer, batch 4 item 12)

Build it tonight, fully reviewed, on wt/t15. It is NOT brought onto the session branch (and so not onto the owner's
phone build) until the owner has seen the design and said so. Keep wt/t15 rebased on the session branch so that
his word is one fast-forward away. The design pictures and the built thing are shown to him side by side.

## Save version

The session branch is at save version 9. Another pair (T14: money without limit for testing) will reach his phone
first and may take version 10. Develop your migration as "the next version" behind one constant; before you report,
rebase onto the session branch as it then is and number yours after whatever it holds (10 if T14 took none, else
11). Test the migration on a copy of a real save written by the session branch's build (and on one with a camel on
the truck at the moment of migrating): nothing lost, played forward a week after.

## What to build, engine first

1. Rush commands (domain, runtime, worker): a facility being built; a water or feed delivery on a day the herd
   went short (the same-day make-good exactly as your note states it); a bought camel on the truck; and the rush
   offered at the moment of ordering or building. Cash only, refused in debt, never on the merchant's account;
   the bank's own kind «الاستعجال».
2. The away call (the one mechanism the hunting design will reuse): a target day, a landing minute as a parameter,
   stops as conditions on the game's state checked after each day (the full list in your note, with the proxy's
   additions), a caller's extra stop conditions and extra card and summary lines, the summary counted as it runs,
   a cancel flag outside the queue, progress pushes, one save at the end and that save marked good.
3. The standing order for feed and water; the vet contract; the treatment command reachable from the phone.
4. The phone: the rush rows and the line at ordering; «التقويم» as the ninth app (the year, a day picked, the card
   before, the jump under way with «وقّف هنا», the early stops, the summary); the treatment screen in العزبة; the
   standing order's and the contract's switches. The phone's standards as in every build here (guards, keyboard,
   the live region, counting nouns, sex forms, no per-frame work, the layout audit and words lint).
5. The early pregnancy scan (proxy batch 4b item 6) only if the phone has a place for it without a new screen;
   otherwise leave it written up and say so.

## Rules the second review fixed (they are not in the design note: put them in the note and build to them)

- N1. Today's milk stands after a make-good: the dawn's litres are kept in the day's record and the الحليب view
  reads them (the view must not recompute a fed day's litres while the bank holds the short day's money).
- N2. The truck's hour is stamped or checked by EngineCore from its own clock; the hour is never trusted from the
  page. The price seen is the price paid (this hour or the one before accepted); after the day turns a stale
  confirm is refused.
- N3. The standing order and the vet contract run as steps of the engine's own daily systems, one code path for a
  played day and a jumped day; never in the jump loop. The same holds for anything a caller adds later (a camp's
  daily work must be a daily system keyed by state, not a loop callback): write that in section 5.
- N4. The vet contract's billing and signing: as the proxy answers in batch 4c (docs/agents/proxy_decisions.md;
  if it is not there yet when you reach this, build the rest first and ask).
- N5. The treatment's quote is keyed by the illness (its first day), not by today: a player cannot shop for a
  cheap day while she is sick.
- N6, N7. Correct the note's two reasons (a thirst death at dawn; "exact because linear" is exact up to Care's
  rounding to 0.01 and its clamp).
- N8. A purchase clears arrivedOn.
- N9. The early-stop and summary pictures come from a run made before the registration stop existed (under the
  revised stops the first stop would come three days before a festival's registration closes): re-make them from
  the built thing, or caption them, before the owner sees them.
- The pens outgrown: the warning on the card and the stop; if the stop cannot be built tonight, the warning and a
  summary line, and the stop listed plainly as owed to the owner.
- Readers of acquiredOn and onTheWay: follow the reviewer's list (phase2_round2.txt, section C): which follow the
  new arrival and which must keep acquiredOn.

## Tests the reviewer will demand first (write them first)

1. A played day equals a jumped day (the same final state, on the VM and in JavaScript) across: a short day with
   a rush; a delivery; a build; a calving; his round's day (six separate tellings after a 06:00 landing); a wages
   day; the standing order and the contract switched on; the season's planning around 2 July.
2. The truck: the hour from EngineCore; acquiredOn unchanged; a purchase clears arrivedOn; the 30-day ownership
   rule unaffected by a rush.
3. The make-good: water to full, half and under half; feed; condition within 0.01; today's milk unchanged in the
   view and the ledger; nothing gained by under-watering and rushing against ordering in time.
4. The anchor: the next catch-up after a jump runs 0 days and the minute is the landing minute; cancel lands
   within one day; the save is marked good after; openPrevious cannot undo a jump.
5. The vet contract: billing, signing with a camel already sick, refusal at the account's limit.
6. The migration on a copy of a real save, including a camel on the truck.
7. A year's jump at 10,000 head in JavaScript with the progress view; the budgets; same seed on the VM and in
   JavaScript unchanged for a game that never rushes or jumps (a game that never opens the calendar is unchanged).
8. The layout audit and words lint on the built screens; the phone's rebuild counts; no per-frame work.
The full CI.

## Report

The guide's report, plus: the built screens beside the design's pictures; every Arabic line that differs from the
design and why; the measurements (a jump's cost by herd size on the VM and in JavaScript; the page's start; the
save's size); what is owed (anything not built tonight); the steps for the owner's phone test of a long jump, in
Gulf Arabic, for when he approves it.

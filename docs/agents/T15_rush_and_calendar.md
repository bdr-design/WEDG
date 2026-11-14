# Task T15: rushing and the calendar: design first, then build

Read docs/agents/GUIDE.md first (in it, $SC is the work machine's scratch folder:
/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad), then /home/user/WEDG/CLAUDE.md.
Base: the session branch's head when you start. Worker's worktree: /home/user/wt/t15, branch wt/t15. Reviewer's
folder: $SC/t15_review. Commit often: the machine was restarted once tonight (disk kept, processes lost).

## What the owner asked (docs/agents/owner_instructions_2026-11-14_night.md, word for word)

- «اي شي اسويه او ابنيه اقدر اسرعه يبني بنفس اللحظة بتكلفه اعلى»: anything he does or builds can be hurried to finish at
  once, for a higher cost.
- «بخطه مدروسه ومحكمه خليني اقدر انتقل بين المواسم بنفسي يعني تقويم وهكذا موجود اختياري»: with a well-studied, tight plan,
  let him move between the seasons himself: a calendar, optional.
- He wants to wake to work with no errors, nothing heavy on the phone, thought through.

The owner sleeps. A proxy agent answers the questions that are his (docs/agents/PROXY.md): you bring each question
with its options, the facts and your recommendation first; the director puts it to the proxy and sends you the
answer. The rule stands that a design is shown before it is adopted: PART A is design only.

## Part A: the design (pictures, words, rules, measurements)

1. Rushing. Find every thing in the engine that takes game time after the player decides it (read the domain:
   facilities under construction and their doneOn; a feed or water order's delivery; a bought camel on the truck
   (camelTruckDays); a listing waiting for offers; a pregnancy; a treatment; anything in the festival engine;
   whatever else: list them all with file:line). For each say whether hurrying it makes sense in the real world
   (a contractor paid to bring more men; a tanker sent today; a truck that drives through the night) or cannot be
   hurried by money (a pregnancy, a calf growing, a festival's date, a sick camel's recovery, an offer from a
   buyer): the owner's word is "anything I do or build", and realism comes first, so what money cannot hurry in the
   real world is a question for him (through the proxy) with your recommendation, not a silent yes or no. For what
   can be hurried: the rule (finishes now), the price (how much more: propose it with reasoning; a game choice
   written in the GDD), what the player sees before he confirms (the extra cost in riyals, with its word), the
   two-tap confirmation the phone uses for what cannot be undone, what happens when cash does not cover it (the
   owner's rule: only feed, water and the vet go on the merchant's account), and how it reads in the bank.
   Draw it in the screens that exist (العزبة's build rows, الوايت, العلف, الحراج's camel on the way), in the manner of
   the approved designs (design/ui/phone_haraj.cjs, phone_bank.cjs, phone_mazayen.cjs: real games, the phone's real
   pieces, 956x440 with the phone enlarged), every figure the engine's own or a marked game choice.
2. The calendar. An optional app in the phone: the year at a glance from the engine's own calendar (the seasons the
   phone already names, the breeding season, the festivals with their registration windows, the milk and wages
   days; the hunting season is not built: leave it room), today marked; and moving the game forward to a day or a
   season the player chooses. Study it tightly, as he asked:
   - what the engine does today when time passes without the player (a month away catches up in slices; the fast
     clock; the worker): what it costs to simulate a week, a season, a year at a small herd and at the largest the
     game allows, on the VM and in JavaScript (measure), and what the player sees meanwhile (no frozen screen);
   - what goes wrong if days pass unattended, with the engine's real rules: feed and water running out (the
     account's limit), a sick camel untreated, a pregnant camel calving, offers expiring, a festival's registration
     closing or its round's day arriving (the day is told stage by stage: what a jump over it does), wages, debt:
     list them from the code;
   - the plan: before the jump, a card that says honestly what the stretch needs (how many days the feed and water
     last against the days asked, what is due in between) and what the player can set before leaving (orders
     placed ahead, a shepherd: only what the engine has or what you propose, each a question); when the jump stops
     early and hands the game back (the cases above), and what it tells him then; a summary at the end (what
     happened, in the phone's words, by the engine's events);
   - only forward: a game cannot go back in time; say how the calendar says that;
   - optional: the game is unchanged for a player who never opens it; no per-frame work; nothing written over the
     game.
   Draw the app's views the same way (the year, a day or season picked, the card before the jump, the jump under
   way, the early stop, the summary), with the home screen as it will be with the apps already approved or built
   (the six there; المزاين and المحادثات being built in /home/user/wt/t10: read that branch for the home grid).
3. Deliver: design/ui/phone_rush.cjs / .jpg and design/ui/phone_calendar.cjs / .jpg with README rows "awaiting
   approval", a design note docs/proposals/rush_and_calendar.md (English: the rules, the list of what can and
   cannot be hurried, the measurements, the plan for the jump, the questions for the owner's proxy with your
   recommendation first). Report with every view's Arabic words in full.

## Part B: the build (only after the director sends the proxy's answers and the reviewer's findings on part A)

Engine first (the rush commands and their prices, the jump with its stops and summary: domain, runtime, worker,
tests, the save's new version if state is added: the session branch's save version is being raised by the المزاين
build in wt/t10 to v9: ask the director which number to take before you write a migration), then the phone. The
same standards as every phone build here: guards, keyboard, the live region, counting nouns, sex forms, no
per-frame work, the layout audit and words lint (the tools in $SC/t4_review/h/), the 10,000-head budgets, same seed
on the VM and in JavaScript, the full CI.

## Left open on purpose

- A god mode for money and the phone's typography and long-press fault: another pair's task.
- Anything about hunting.

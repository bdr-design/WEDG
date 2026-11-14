# Task T18: build the hunting season. Part A: the engine

Read docs/agents/GUIDE.md first, then /home/user/WEDG/CLAUDE.md. Base: the session branch's head when you start.
Worker's worktree: /home/user/wt/t18, branch wt/t18. Reviewer's folder: $SC/t18_review. Commit often. Never push.

## What the owner decided

He approved the design on 14 Nov 2026: «اعتمده وابدأ البناء: يبدأ البناء على أجوبتك هنا: المحرك أول، ثم الجوال، ثم
المخيم والمقناص بالخريطة. كل جزء يمر على مراجعه.» This task is the first of the three: the engine. The phone (part B)
and the camp and outing on the map (part C) are later tasks on top of it; build nothing of them here, but give them
everything they need (commands, views, the words of every refusal).

Read, in this order, and build to them. Where two disagree, the later-dated word of the owner wins; where the
design note and the owner disagree, the owner wins; where you cannot tell, ask (your report's questions), do not
choose.
1. docs/agents/hunting_owner_decisions.md (his seven decisions, «خل الطلعة ايام مافي مشكلة», the approval's four
   answers).
2. docs/agents/owner_decisions_2026-11-14.md items 5–9 and 17–19 (the odds at twice the sources; alone first; a saker
   or a قرناس released; a kept bird not resold; no cheating in falcon contests yet; the air rifle aimed by hand: not
   in this task; a kept trapped peregrine released from February or kept, his choice).
3. docs/proposals/hunting_season_design.md (the approved design; its "proxy" marks are now the owner's where the file
   above confirms them), design/ui/phone_falcon.cjs and .jpg (the 18 views: every figure and every Arabic line the
   phone will show must come from a view of yours), design/hunt/trip_*.jpg and season_*.jpg.
4. docs/proposals/hunting.md (sections 9 and 10), docs/proposals/gdd_hunting_section.md, docs/research-realism.md
   section 8 (the sources by number).
5. docs/agents/proxy_decisions.md batch 3 (the release lines word for word, including the lanner's).
6. docs/proposals/rush_and_calendar.md section 5 and packages/marah_domain/lib/src/away.dart (the away call: the one
   way of being away; the rule N3: a camp's daily work is a daily system keyed by state, never a loop callback).

## What to build (domain, runtime, worker; engine only)

Order: 1 and 2 first (they stand alone and the phone can be built on them), then 3, 4, 5, then 6.

1. **State and catalog.** The falcons he owns (species, sex, age class, how each came: bought at which auction, or
   trapped where and when; its passport/registration as the research has it; its training state and results; what
   the player may know and what is hidden: the views never expose hidden values); the falcons' room as a facility
   (holds 4, costs 18,000: game choices as the design marks them) with its pin's data; the two permits (hunting:
   1 Sep–31 Jan, by day; trapping: 1 Oct–30 Nov, trapping grounds only, 500 riyals a game choice) and what each
   allows; the trapping gear as stock (pigeons, the net on the pigeon, the bird nets, the jerboa, binoculars, the
   mobile tent, the camp's supplies), bought from «نادي الصقور» → «الطرح» and delivered to the farm like feed (the
   same delivery machinery, the same rush rules if they apply without new code: say); the grounds (hunting and
   trapping: real places from the research, each with its distance from the farm, what is found there, and whether
   it is near enough for a one-day outing).
2. **Buying a falcon**, each route in its month: the breeders' auction in August, the exhibition 1–10 October, the
   trapping auction 1 Oct–30 Nov (prices from the research's figures; the distribution a marked game choice on real
   numbers). Cash only or on what terms: as the design's views say; if they do not say, ask.
3. **Being away**, by the away call and nothing else: the one-day outing to a near ground (back the same evening)
   and the trip of days with a camp (both for falconry and for trapping): the card before leaving (the calendar's
   card with the trip's lines: the ground and distance, the gear he has and lacks, the camp's supplies), the drive
   as the plan's travel, one night per «نام لين الفجر» landing at the working hour's start, every calendar stop plus
   the camp's own (supplies out, the season's end, the trip's chosen end), breaking camp at any time, the summary
   with the trip's lines. The farm runs by its own rules meanwhile, as on any day.
4. **Trapping**, a day at camp played by his hands with the result worked out (his answer 3): the commands the map
   will send (spot with the binoculars, choose the lure, release the pigeon) and the engine's answer (nothing came;
   a falcon stooped and was not held; a bird in the net, and what it is). What lands in the net follows the
   research: a passage peregrine of the year (sellable); a mountain peregrine or a lanner (released at once, with
   its line); a saker or a قرناس (released, with its line). The chance of a sellable bird over a season: twice the
   sources' range, as he chose («الضعف»): a bare beginner about one season in 6, a well-equipped and well-placed
   trapper two seasons in 3, never beyond; what moves him along the range (gear, pigeons, ground, month, hour) as
   the design says, each weight a marked game choice. The share of dear birds and the prices stay as in the sources
   (at least 6 of 40 at 300,000 or more; the 2025 sales read). No hidden help and no pity timer: a season can end
   with nothing. Banned place or time: the command is refused with the reason's words (his decision 4), and nothing
   happens; no fine can follow from a refused command.
5. **A trapped bird's fate.** Sell at the trapping auction (enter the bird, the club's check, the bidders see what
   the sale pages give, the hammer, the money in full with no fee, the bank's own kind); or keep it (for hunting
   and, later, contests; never resold: no command exists for it); a kept trapped peregrine may be released from
   February or kept through the year, by his own command.
6. **Falconry.** The cast by his hand (a command from the map, on a hunting ground, in season, by day, with a
   permit): the result from the falcon, the ground and luck; the quarry by the rules (what may be taken, when; the
   houbara and the stone-curlew as the research has them); the rare lost falcon and the tracker (mostly found,
   sometimes gone; the tracker lowers the risk); الدعو as the daily care (the away call's `falconCare` hook), and
   what neglect costs. The banned place or time refused with its words, as in 4.

Not in this task (say so in the GDD section, do not half-build): the falcon contests and the festival (the date is
still the owner's to choose; contests are built clean, later), partners in trapping, the air rifle, the Kalashnikov,
wolves and dogs, anything on the phone or the map.

## Rules for the build

- **A game that never touches falcons is unchanged**: same seed, same state hash week for week, on the VM and in
  JavaScript, against the base. Every new draw of chance comes from its own keyed stream; no existing stream gains
  or loses a draw.
- **Save version**: the session branch is at 11; another task (T16) lands 12 first. Develop yours as "the next
  version" behind one constant and number it after whatever the session branch holds when you rebase before your
  report. Test the migration on a copy of a real save written by the base's build, played forward a season.
- **The budgets** (packages/marah_runtime budget tests; run that package with `--concurrency=1` on this machine): a
  day's step and the snapshot at 10,000 head must not grow beyond noise; measure back to back against the base and
  give both figures.
- **Every number** in the code is in docs/GDD.md's hunting section (write it from gdd_hunting_section.md, corrected
  to the owner's decisions) with its source number, or the words "game choice"; the doubled odds are written as a
  game choice that departs from the sources, with the sources' range beside them.
- **Arabic**: every line a player can read (refusals, release lines, card lines, ledger kinds) in Gulf Arabic, taken
  word for word from the approved design where it has them; list in your report every line you had to write
  yourself, for the owner's eye. Counting nouns and sex forms as the phone's standards have them.
- **Tests first**, and the reviewer will mutate: each rule above has a test that fails when the rule is broken
  (seasons' and hours' edges on both sides; each ground; each permit; each species in the net; the odds' two ends).
- **The odds, measured**: a seeded run of at least 20,000 seasons at each end of the range (and one middle setup)
  reporting the share of seasons with a sellable bird, the share with a dear one, the price's mean and median, the
  season's net money; beside the targets. The script committed under tool/ or the package's tool folder.
- The full CI ($SC/haraj/ci.sh pointed at your worktree) and `dart test` in each package before you report.

## Report

The guide's report, plus: the commands and views added (names, fields: what part B's phone and part C's map will
call and read); the rules table (rule, where it comes from, the test that holds it); the odds as measured; the
budgets before and after; the save's size before and after; every Arabic line of your own; what the design could not
settle, as questions for the owner with your recommendation first.

## For the reviewer

Phase 1: the baseline at the base (the same-seed state hashes for a year, the budgets, the save's size), a table of
every rule in the six documents above that the engine must hold (your own reading, made before you see the worker's),
and your own independent measure of the odds' targets from the owner's words and the sources (what the two ends
must come to, and the dear birds' share). Phase 2: each rule against the build by your own tests and mutations;
the unchanged-game proof by your own hashes; the odds by your own run on the built engine; the views for hidden
values; the Arabic against the design's words; the GDD's numbers against the code.

# T18 part A, the fix round: brief for its two reviewers (after the fix)

The owner's rule of 17 Nov 2026 (CLAUDE.md): Claude builds and fixes everything; two reviewer agents check each
piece of work, before the fix and after it; only two agents run at a time.

## What was fixed, and where

The hunting engine (docs/agents/T18_hunting_build.md; answers docs/agents/T18_answers.md) was reviewed in full and
sent back with ten findings (listed below). A worker began the fixes and was stopped; Claude finished them. Branch
wt/t18 (worktree /home/user/wt/t18), on the session branch's c820ded:

- 5563626, 7500bdd, 7478a54: the engine as first reviewed.
- 7f052f5, d92e552: the stopped worker's unfinished edits (the drive legs, DayWork per day, flights per falcon, the
  tracker per falcon, the lost falcon's days, الدعو at the farm, reworded lines).
- 3f57e31: the tests brought to the new rules.
- b6a2acf: the odds retuned to the design's bare beginner; the odds script with the drive as game time; pins.
- d3666e4: the same-seed hunting run covering every path (seed 261), with a test.
- 611035d: GDD section 15 to the code.

Claude's own measures (to be checked, not trusted): the full local CI green (`bash /home/user/WEDG/tool/dev/
ci_local.sh /home/user/wt/t18`), same seed 221658 / 213733673 on VM and JS, the hunt lines equal on both; domain 285
tests, proto 58, runtime 46, data 44; the odds over 20,000 seasons each: the design's bare beginner (السليل, 20 days
from 15 October, 6 pigeons and the pigeon net, no binoculars, dawn and evening) 0.1585; the middle (رفحاء, 45 days,
binoculars, dawn) 0.389; the well equipped (الليث, 61 days, all gear, all windows) 0.641 with 1.02 birds a season.

## The ten findings, each to be confirmed fixed

1. The drive out and home are game time through the away call (the calendar's stops on the way); arriving lands at
   the ground's working hour on the day the drive reaches it; ending a far trip is the drive home; a day's outing
   must fit its drives inside the day; the day's trapping state per player per day; one trapping ground a day. The
   `hop` strategy (EndTrip, StartTrip, Spot/Release on every ground in each window) must gain nothing.
2. A cast needs a falconry trip at that ground (the page's ground claim never trusted); flights per falcon per day;
   the draw keyed by falcon, day and flight (no hour, no re-roll by waiting or reloading).
3. The design's bare beginner (hunting.md 9.3) about 0.16 of seasons with a sellable bird; the best setup about
   0.65, never above 2 in 3; no setup or strategy above it.
4. CareFalcons only at the farm (refused from a camp or the road).
5. GDD 15 lists passCoast, the net's species mix, the skill formulas, each marked.
6. No opening-bid band of 10,000 reads out the worth (dear share at most about 0.3 in any band).
7. Pinned: 3 tries, 3 flights a day, November's factor, a falconry trip with no ready falcon refused, the net at a
   hunting ground giving the off-ground words.
8. The same-seed hunting run covers: netted, entered and sold; kept then freed in February; unsold freed at the
   close; a saker and a resident released; a lost falcon searched for; refusals of many kinds; the falcon-care and
   supplies-out stops.
9. Six Arabic lines reworded (the counted gear «تقدر تطلب N حمامات بس» in its four forms; «عندك كفايتك منها»;
   «مخيمك مو هنا»; «انت طالع الحين: ارجع أول»; «ما عندك صقور»; «الطير اللي تخليه لك ما ينعرض للبيع»).
10. A lost falcon gone after three days, the chance halving each day; a tracker fitted to a named falcon.

## Always

- A game that never touches falcons is unchanged: same seed, the whole state hashed week by week for a year, on
  the VM and in JavaScript, against c820ded.
- Every refusal changes nothing; no fine is written; the views and the catalog show no hidden value (a lot's
  worth, a falcon's skill); the save migrates from real v11 and v12 saves; the 10,000-head budgets unchanged.
- New exploits the fix might have opened: a save made mid-drive; a trip started, ended and restarted the same day;
  MoveCamp to gain a ground or a day; a day's outing used to skip the drive; the farm's day or the calendar's stops
  skipped by a leg.

## Practical

SC = /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad. Reviewer A's earlier scripts and
rules table: $SC/t18_review (scripts/r_*.dart, rules_table.md, b2/, mut/). Work on your own copy (`git -C
/home/user/WEDG archive wt/t18 | tar -x -C <your folder>`, plus .dart_tool copied from /home/user/WEDG); never edit
tracked files, never commit, never push. `export PATH=/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:$PATH`;
packages/marah_runtime tests with `--concurrency=1`. 4 shared cores, about 4.5 GB of disk: one copy each; delete it
when done; leave nothing running. Do not get around a network refusal.

Reviewer A: findings 1, 2, 3, 6, 10 and the exploits, by your own harness (the odds and `hop`, mutations).
Reviewer B: findings 4, 5, 7, 8, 9, the unchanged game, the migration, the budgets, hidden values, the Arabic and
the GDD against the code.

Report: findings ranked, each with file:line, how reproduced, the fix you suggest; what is sound; a verdict: fit to
land on the session branch (the engine only; the phone and the map come after), or what must go back.

# Marah (مراح): handover, 14 Nov 2026

The owner stopped the work on 14 Nov 2026 and asked for everything to be pushed and for this memo of what remains.
Every agent was stopped mid-task; nothing was left running. Where this memo says "reviewed", a reviewer agent
checked it and the director re-ran the checks; where it says "unreviewed", nobody has.

## 1. Where everything is

| What | Where |
|---|---|
| The game, as the owner's phone has it | branch `claude/vigilant-noether-nydua2` (this branch) |
| The owner's latest iPhone build | GitHub Actions, workflow "iOS prototype app", run 68 (id 43597882803), artifact `marah-proto-ipa`, built from c820ded. Later commits on this branch are documents and one script only. |
| Unmerged work, stopped mid-task | side branches `wip/t12`, `wip/t16`, `wip/t17`, `wip/t18`, `wip/t18b` (section 3) |
| Earlier tasks' branches, already merged | `wip/t1`, `t2`, `t4`, `t6`, `t8`, `t10`, `t11`, `t13`, `t14`, `t15` (kept as backups; nothing to take from them); `wip/t14-sizes` is the larger-text experiment the owner declined |
| Reviewers' scripts, notes, baselines | branch `wip/handover-scratch` (text only; its README lists the folders) |
| The owner's rules | `CLAUDE.md` |
| The rules of the game, every number sourced or a game choice | `docs/GDD.md`, `docs/research-realism.md` |
| The owner's decisions, in his words | `docs/agents/owner_decisions_2026-11-14.md` (items 1–27), `docs/agents/hunting_owner_decisions.md`, `docs/agents/T3_T4_owner_decisions.md`, `docs/agents/owner_instructions_2026-11-14_night.md` |
| Answers given for him while he slept (provisional unless he confirmed them) | `docs/agents/proxy_decisions.md` |
| How the work is done (agents build, each with a reviewer; the session directs) | `docs/agents/GUIDE.md`, `docs/agents/README.md`, the briefs `docs/agents/T*.md` |

Not in the repository, and lost when the work machine is reclaimed:
- **The camel's source inputs** (`$SC/camel/`: the mask, the reference fill, the high mesh, the joints, the two
  .blend files, the two 2048 px maps; about 12 MB of the folder's 126 MB). The game works without them, but the
  camel's levels, rig, clips and textures cannot be rebuilt from code alone. Some derive from the owner's
  photograph and the repository is public: he was asked twice whether to commit them or make the repository
  private first, and had not answered. `tool/camel3d/README.md`, "Where the inputs are".
- The older car work's downloads and the pictures shown to the owner (renders; all can be made again from code).

## 2. What is on this branch (built, reviewed, on the owner's phone)

The 3D farm prototype (`design/prototype3d/`, bundled by `tool/proto_app/assemble.py` into the iOS app) on the rules
engine (`packages/marah_domain`, `marah_data`, `marah_store`, `marah_runtime`; compiled to JavaScript by
`tool/proto_engine`). Save version 12. In the in-game phone: الوايت, العلف, الحراج (with the vet's check, the
declared sale and the compact camel's page), البنك, المزاين, المحادثات, العزبة, التقويم; rushing; the standing order and
the vet's contract; test money (two taps on the meter's «فلوس بلا حد»); the phone's typography, fonts and figures.
The herd: the 4k middle level, the footfall dust in one draw, a 40-head test herd for the phone test.
Models built by code: the camel, the LC300, the man, the Kalashnikov (`tool/weapon3d`, `assets_src/weapons`), the
saker, the houbara and the stone-curlew as static poses (`tool/bird3d`, `assets_src/birds`).
Designs approved by the owner and not yet built: the hunting season (`design/ui/phone_falcon.jpg`,
`design/hunt/`, `docs/proposals/hunting_season_design.md`).

Checks: `tool/dev/ci_local.sh` (what CI runs), then `dart test` in `packages/marah_data`, `marah_store`, and
`marah_runtime` with `--concurrency=1`; the page checks in `tool/page_checks/` (assemble the page, serve
`tool/proto_app/assets/web`, `PORT=<port> NODE_PATH=$(npm root -g) node tool/page_checks/<name>.cjs`). The same-seed
result that must not change for a game that uses nothing new: length 221658, hash 213733673 (seed 7, week 104).

## 3. Work stopped mid-task (in the order to pick it up)

Each `wip/<task>` branch ends, where the worker was mid-edit, with a commit named "WIP at the handover": that commit
is unreviewed and may not build.

### 3.1 الحراج: the two pages that still scrolled (`wip/t16`, 2 commits on a6912a2)
The owner's items 26 and 27. 3597789 puts the seller's answer inside the سوم block; b1b2905 makes the suckling
calf's note a line of the refusal card. **Unreviewed.** To do: the reviewer's pass (scroll at 956x440 in every state,
other screens unmoved, the page checks), the local CI, fast-forward onto this branch, and the push builds his IPA.
Small and close to done.

### 3.2 The hunting season, part A: the engine (`wip/t18`, on c820ded)
Brief `docs/agents/T18_hunting_build.md`; answers to its open points `docs/agents/T18_answers.md`.
- 5563626, 7500bdd, 7478a54: all six items (catalog, permits, gear, the falcons' room, buying a falcon with a
  ceiling, trips by the away call, trapping, the trapped bird's fate, falconry), the odds script, GDD section 15,
  save version 13. **Reviewed in full: sent back, not landed.** A game that never touches falcons is unchanged, CI
  and budgets hold, saves migrate. The findings to fix:
  1. Critical: the drive costs no time and a remade camp gives a fresh day. Hopping between grounds nets a bird in
     every season (about 14 a season) against the owner's cap of two seasons in three. Fix: the drive out and home
     are game time through the away call; the day's trapping state per player per day; one trapping ground a day.
  2. High: casts made off a trip are unlimited and repeat the same draw within the hour. Fix: a cast needs a
     falconry trip at that ground; flights counted per falcon per day; the draw keyed by falcon, day and count.
  3. The low end of the odds: the design's own bare beginner (hunting.md 9.3) gets 0.087 a season, not the owner's
     «طير كل 6 مواسم تقريباً». Retune so that beginner comes to about 0.16; the top stays about 0.65, never past 2 in 3.
  4. الدعو is accepted from any distance. Fix: only at the farm, for the falcons left there.
  5. to 10: numbers missing from the GDD; the opening bid's top band still hints at the worth; five test gaps; the
     same-seed hunting run exercises nothing; six Arabic lines to reword; a lost falcon never expires; one tracker is
     not tied to a named falcon.
- 7f052f5 (WIP): the worker's fixes in progress when stopped. **Unreviewed.**
- The reviewer's scripts to re-run after the fixes: `wip/handover-scratch`, `scratch/t18_review/scripts`
  (`r_odds.dart` with the `hop` strategy, `r_hunt_b_test.dart`, `r_hidden2_test.dart`, `r_migrate_test.dart`),
  the rules table `scratch/t18_review/rules_table.md`.
- Still the owner's: until when a kept trapped peregrine may be released (built as 1 Feb–30 Apr); whether a male
  peregrine of the year is ever netted or sold (built as females only); the changed card: الحماد is about 843 km
  and 10 hours by road, not the approved card's «600 كم، حوالي 7 ساعات» (he was told, and has not objected or agreed).

### 3.3 The hunting season, part B: the phone (`wip/t18b`, on part A's 7478a54)
Brief `docs/agents/T18B_hunting_phone.md`. Two apps: «نادي الصقور» and «تصريح الصيد». 7673691 adds the falcons' room
to the farm's facilities view; 151879d is the WIP (phone.js, engine.js, a design-saves script). **Unreviewed, early.**
It must be rebased once part A's fixes land (trips, الدعو and the tracker change shape). The brief's "design first"
views (buying a lot with a ceiling; a held bird's three ways; الحماد's card words; the refusal lines) have to be
shown to the owner before they are built in.

### 3.4 The hunting season, part C: the camp and the outing on the map (not started, no brief)
Needs parts A and B, the birds' rigs (3.5), and models not yet built: the mobile tent, the pigeon cage, the camp's
supplies, the nets, the falcons' room building and its perches, the binoculars' view, and the man's arm carrying a
falcon (fist above the elbow, so the tail clears the forearm). Costs are estimated in
`docs/proposals/hunting_season_design.md`, "What it costs to draw".

### 3.5 The birds' rigs, the peregrine, the pigeon (`wip/t17`, on 546d808; none of it is on this branch)
Brief `docs/agents/T17_birds_rig_and_peregrine.md`.
- The saker: 49 bones, 13 clips. **Reviewed: fit to show.** Shown to the owner on 14 Nov as motion (two small GIFs
  and six sheets); **awaiting his approval of the motion.** Listed gaps: a wrist crease on the upstroke; the hood
  clips held back until the man's hand exists; the left tarsus 3.2 mm into the cuff.
- The houbara and the stone-curlew: rigged, five clips each. **Reviewed: go back.** Must fix: both fly in their
  standing pose (the flight loops key only the wings). Should fix: wingtips through the ground at take-off; the
  houbara's toes in the ground while running; the perched poses not matching across clips; the saker's hood clips
  placed 385 mm off the cuff pose; the README's rule for the hood's visibility.
- 3d7a58e and 5b4d032 (WIP): the peregrine of the year and the trapping pigeon, begun. **Unreviewed.**
- The static birds changed slightly on this branch of work (the bill's base, the houbara's crest); the reviewer
  found nothing the owner approved changed for the worse.

### 3.6 The wolf and the dogs (`wip/t12`, on a7bc877; none of it is on this branch)
Brief `docs/agents/T12_wolf_dogs.md`. `tool/canid3d`, 16 GLBs, pictures in `design/canids`.
- Round 6 (3639604): **reviewed: fit to show.** Shown to the owner on 14 Nov; **awaiting his approval of the look**
  and his answers to five questions (the look; the wolf's coat; the guard dog's type; the collar; the saluki):
  `tool/canid3d/README.md`, "Questions for the owner".
- Round 7 (c8abb9f): the noses, eyes and face planes as the game's renderer draws them. **Unreviewed**; the worker
  was stopped before reporting, so the GLBs and pictures may not match the code.
- No rig yet. The danger's rules in the engine (the wolf at night, the guard dog bought and fed, the fence) are a
  later task.

## 4. Waiting on the owner

Phone tests of builds he has:
- The herd's drawing, three ways, six screenshots of the meter: `docs/phone_tests/herd_draw_test.md` (build 67 on).
- The long press that selected the screen; the fonts and figures; test money; rushing and the calendar (builds
  64–66); الحراج's vet views (build 68).
- The long jump at 10,000 head: `docs/phone_tests/long_jump_test.md` (needs a test build with a bundled save: not made).

Decisions asked and not answered:
- The camel's source inputs: into the public repository, or make it private first (section 1).
- The saker's motion; the wolf's and dogs' look and their five questions.
- The repository is public and a signed IPA carries his devices' identifiers and his team: he was advised to make it
  private; his call.

Decisions not yet put to him: the points in 3.2; the falcon festival's date (the sources give two); what «العرض» in
inches measures; partners in trapping (after the camp is played); the look of the Kalashnikov; the durations of
treatments and the debt's deadline.

## 5. Queued, never started

- T5: the truck driving in with a bought camel, and selling from a camel's card.
- T9: folding the ledger's old months in the save.
- The falcons' contests and festival (built clean: no cheating until the real penalty is found); the air rifle,
  aimed by hand (his choice); the Kalashnikov's place through a secret chat; the early pregnancy scan from day 15
  (when a breeding screen exists).
- Shaders still compiled in play (the eight vehicle programs, the facilities, the selection ring, the cabin): warm
  them at load. ADR 0005 has the list.
- The app's minimum iOS: the project says 15.0, the page already needs 16.4 (import maps).
- A release build must drop the frame meter and the test-money command.
- `design/ui/README.md` still marks the rush, calendar and hunting designs "awaiting the owner's approval": he
  approved them on 14 Nov; correct the rows.

Older items still open in the session's task list, by title only (their state was not re-checked for this memo;
read the code and the git log before trusting any of them): the GDD's remaining sections; the map-centred HUD's
review; the engine bake-off (flutter_scene against Thermion); walking and driving the LC300; the phone's small and
enlarged forms; the LC300's interior (cabin, wheel, seats, dashboard); the car's buttons; driving physics; the
weight audit; the chase and map cameras; the frame drops by the herd on his phone (the herd test above is its
measurement); the rules engine against the whole GDD; a signed IPA from CI (it works: section 1).

## 6. Things that will bite

- **Save versions land in order.** This branch writes 12. The hunting engine is 13. Anything else that changes the
  save numbers itself after whatever this branch holds when it lands.
- **A game that uses nothing new must stay byte-identical** on the same seed, on the VM and in JavaScript. Every new
  draw of chance takes its own keyed stream.
- **The views never expose hidden values** (a camel's quality, a falcon's skill, a lot's worth).
- **The work machine** has 4 cores and a small disk; `packages/marah_runtime`'s 10,000-head budget tests fail under
  parallel load there and pass on GitHub. Many outside hosts are refused: do not work around a refusal.
- **Every push to this branch that touches the app** builds his iPhone app and runs CI.
- **Secrets** (`IOS_P12_BASE64`, `IOS_P12_PASSWORD`, `IOS_PROFILE_BASE64`) are the owner's to add; never in chat,
  never in the repository.

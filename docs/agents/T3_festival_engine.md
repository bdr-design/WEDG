# Task T3: the festivals in the rules engine, to the approved GDD (the Saudi round system and cheating)

Read $SC/agents/GUIDE.md first. Base commit: a20b49d. Worker's worktree: /home/user/wt/t3, branch wt/t3.

## What is wanted

docs/GDD.md section 7 (المهرجانات بالنظام السعودي) and 7.1 (الغش), approved by the owner, and docs/plan-gameplay.md G1
parts 4 and 5, say what the engine must do. docs/research-realism.md has the sources. The engine (packages/marah_domain:
model/contest.dart, systems, handlers, rules/eligibility.dart, rules/judging.dart, world_gen.dart, views.dart; the
commands EnterRound and WithdrawEntry exist) has festivals already, from before the GDD was approved.

1. Audit first: for every rule in GDD 7 and 7.1 and plan G1 parts 4 and 5, say whether the engine does it, does it
   differently, or lacks it (file:line). Put the table in your report.
2. Build what is missing or different, to the GDD:
   - The round types and who may enter each; registration (one فردي and one جمل entry per owner, no camel in both, the
     colour and class fixed at closing, closing 72 hours before the round with a late fee).
   - The six stages of the day, each able to remove an entry, with events the screens can tell as a story.
   - Cheating: a secret treatment that raises a judged trait, its types and fine caps as the GDD has them; detection
     that rises with the treatment's strength; if caught: disqualification, the fine, the ban (the edition and five
     more), the reputation loss, news; a small chance of being caught outside festivals; rivals cheat too.
   - Prizes per round type stay game choices: mark them so.
   Every number sourced (cite research-realism.md) or marked "(balance)"/a game choice in the code and the GDD, as
   the rest of Balance is. Where the GDD is silent or two readings are possible, do not guess: list it for the owner.
3. The views and the runtime: what a player may see of a festival, a round, his entries, the day's stages and results,
   a treatment and its risk (never another owner's secret, never hidden values): GameView, the Presenter's cards and
   SnapshotJson, so the phone's المزاين app (designed in a task beside this one) can be built on them. Commands in
   tool/proto_engine/lib/commands_json.dart for whatever a player can order.
4. Saves: any new state in the save with a version bump and a migration (packages/marah_data/lib/src/save_codec.dart:
   read how v6 to v7 was done, and its golden fixtures), the change-detection tests kept true.
5. Tests for every rule you build or change (packages/marah_domain/test), the bot (testing/bot.dart) playing festivals
   so `simulate 10 4` and the same-seed check exercise them, and the extras list in tool/proto_engine/bin/same_seed.dart
   and .github/workflows/ci.yml for commands the bot never sends.

It must stay light: the day's cost at 10,000 head and the snapshot's cost (packages/marah_runtime/test/budget_test.dart,
on the VM and on node) measured before and after. All the guide's checks green before you report.

## Left for other tasks (do not build here)

Auctions (plan G1 part 6). The phone's screens (another task draws their design). The 3D festival ground.

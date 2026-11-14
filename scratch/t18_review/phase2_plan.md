# Phase 2 plan (reviewer, T18 A)
1. Copy: git -C /home/user/wt/t18 archive <commit> | tar -x -C $SC/t18_review/work (delete base/ first if disk is short; keep baseline/).
   Copy .dart_tool. Copy scripts/r_same_seed.dart -> tool/proto_engine/bin/, fill `strip` with the worker's new state keys
   (from its toJson diff), run VM and JS; diff "strip" columns and cmd/ref/ext/cash/day against baseline/vm_base.txt; raw columns may differ only by the new empty keys.
2. Timing: scripts/r_timing_test.dart in base and work, alternating base/work/base/work, --concurrency=1, report fastest+median.
3. Save: size after the year (same driver) vs 196,665/191,179/187,625; load baseline/save_base_seed7_104w.txt with the new SaveCodec, play a season forward (a trapping season with a camp), check no throw and state invariants.
4. Rules: my own tests per rules_table.md row (edges both sides), written in work/ as test/r_*_test.dart (untracked copy only).
5. Mutations: python script applying one textual change at a time to the worker's source (season/hour edges, permit checks, ground checks, species fates, release lines, auction fee/dates/acceptance, room capacity/price, odds cap/floor, pity, per-day cap, tracker direction, الدعو thresholds, N3 move into a counter, refusal side effects); run the worker's tests; list survivors.
6. Odds: my own harness through the real commands (camp, spot, lure, release; away() for nights) at the bare-beginner end, the best setup, a middle setup: 20,000 seasons each (distinct seeds) if the full path costs < ~10 min each, else 20,000 at the rule level plus >= 2,000 full-path seasons to show they agree. Exploit sweep for the top: max gear, every ground, every month/hour, command spam, break/remake camp, moving the tent. Independence across days and seasons (pity).
7. Hidden values: games with each falcon route, a trapped bird kept/entered/sold, a lost falcon; dump every new view and the worker's snapshot JSON; grep keys (skill, value, worth, price before hammer, chance, odds, luck, seed, lost fate) and scan for each hidden number (exact, rounded to 1,000, x100) and for ordering by a hidden value.
8. Arabic: every Arabic string in the diff against baseline/design_lines.txt (exact / near / new), counting nouns and sex forms.
9. GDD: every numeric literal in the new code vs docs/GDD.md's hunting section (source number or اختيار لعب).
10. CI: $SC/haraj/ci.sh copied, pointed at work/.

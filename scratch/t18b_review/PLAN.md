# T18B reviewer: baseline (base wt/t18 7478a54) and the phase-2 checks

Folder $SC/t18b_review: base/ (the base, page built in base/tool/proto_app/assets/web), h/ (scripts), baseline/
(results at the base), saves/ (falcon_states.dart's saves), TABLE.md (views, words, engine facts, D-list).

## Scripts (h/), each run the same way on the worker's build copy
- boxes.cjs: every phone screen reachable from home, big and small (and scrolled end), seed 4242 on 1 Oct with the
  clock paused: texts and boxes → baseline/boxes_base.json (45 surfaces). cmp_boxes.cjs base build [ignore] lists
  every text and box that changed. Phase 2: every surface but home must be the same (home: only the two new apps).
- weight.cjs: start (ms to first snapshot / status hidden), draws+tris closed/small/big, snapshot chars and its
  `falcons` part, worker ops counted (the catalog asked once?), and rebuilds per snapshot on the fast clock for each
  screen in SCREENS (phase 2 adds the new screens by path) → baseline/weight_base.json.
- probe.cjs: per save, snapshot.falcons, the hunt's recentEvents, the catalog (its size), a trip card, and a search of
  the held bird's hidden worth and skill in the snapshot, the DOM, the live region and localStorage.
- falcon_states.dart: the saves (oct1_none, oct1_ready, held_noroom, held_room, held_full, entered, sold, close_last,
  close_after, mine_mid, mine_permit, feb_kept, moult, debt).
- page checks from the checkout's own tool/page_checks: keep_together, longpress, fonts_start, money_meter,
  type_audit (PHASES new,short,found,day; SAVES=$SC/t10/saves) and type_table.cjs base build.

## Phase 2 checks
1. Each built view vs the design (my own shots at 956x440, big and small) and vs TABLE.md's words: every Arabic line
   that differs listed with the reason; D-items: built behind one path so the owner's answer changes words/layout only.
2. Each command path in TABLE.md driven in the page through the phone's own buttons (not dispatch): bought; each
   refusal's words on screen AND in the live region (.sr); two taps for money/undoable (permit, gear, buy, enter,
   keep, release; الدعو one tap); a double tap (two clicks < DOUBLE_TAP) sends ONE command (count dispatches by
   wrapping marahEngine.dispatch); a tap during a screen change is not taken; keyboard Enter/Space, focus kept on the
   same control across a redraw (the fast clock running), key repeat ignored; the stepper (ceiling) at its ends
   (0, cash, cash+1), a stale lot after midnight (notALot), the room built while the screen is open.
3. Standards: counting nouns in 4 forms for every new noun (صقر، حمامة، ليلة، يوم، طير، جهاز، تصريح) at 1, 2, 3–10, 11+;
   numbers with their words (keepTogether, the type audit's split/prepNum); 'Marah Figures' / the figures' face on
   every figure; one grammatical gender for the bird on every line; no Arabic-Indic digits; nothing written outside
   the phone (no toast over the map); the badge as the notice.
4. Hidden values: the held bird's worth and skill, and each lot's worth (FalconMarket value: computed in a Dart probe
   for the page's day and lots) searched as numbers in snapshot JSON, the phone's DOM (innerHTML, aria-labels), the
   live region, the phone's JS state reachable from window, the worker's replies (dispatch events before the hammer).
   (Known at the base, not the worker's: the save in localStorage holds skill and value; the page reads it.)
5. The catalog: asked once per session (count op 'falconCatalog' over a session with screens opened again and the
   game started over), its size; snapshot.falcons read as it is (no recomputation: grep phone.js for HuntBalance-like
   constants: 28, 14, 7, 20, 18000, 500, 100, month numbers 5–8, 2/1, 4/30, 150, km/hours).
6. Weight: rebuilds per snapshot on each new screen (a screen whose facts did not change must not rebuild: e.g. تصريح
   الصيد mid-season, الطرح with nothing ordered; tonight's lots once a day), start time and draws vs the base (back to
   back, same load), snapshot growth.
7. Unmoved: cmp_boxes on every other screen; the page checks' results vs baseline/; the calendar's stop words
   (falconCare reachable with no trip); the bank with the five kinds.
8. Engine changes (if any): tests added, same seed unchanged (tool/proto_engine same_seed VM and JS), budgets again;
   the full CI ($SC/haraj/ci.sh pointed at a copy).

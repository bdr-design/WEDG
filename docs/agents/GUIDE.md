# Guide for agents working on Marah (read first)

You work for the director of this session (the main Claude session). The owner's rules are in /home/user/WEDG/CLAUDE.md:
read it. The ones that bind every task: smoothness on a mid-range phone and realism come first (measured, not guessed);
every number is sourced or marked a game choice (docs/GDD.md); player-facing text is Gulf Arabic, code/commits/docs
English; nothing written floats over the game; the views never expose hidden values. Decisions that are the owner's
(layout, scope, a trade-off between realism and weight) are NOT yours to make: build what loses nothing, and for a
trade-off bring the options with measurements and pictures in your report.

SC = /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad

## Two roles

WORKER (builds or fixes):
- Work only in your own git worktree, never in /home/user/WEDG itself (others read it) and never in another agent's
  folder. Create it from the base commit your brief names:
    git -C /home/user/WEDG worktree add /home/user/wt/<name> -b wt/<name> <base>
  For Dart: copy /home/user/WEDG/.dart_tool into the worktree root if it has none (or `flutter pub get --offline` there).
- Commit there in small commits with clear English messages (what and why, measured results in the message). End each
  commit message with the attribution lines your own session's instructions give for commits; if you were given none,
  end with: `Claude-Session: https://claude.ai/code/session_01MLonhqocXpQK4avaG2Yu99`. Never push, never open a PR,
  never rewrite the session branch.
- Before you report: run the checks that cover what you touched (see "Checks"), and measure what your brief asks.
- Report (your final message, to the director): the worktree path and branch, the commits (hash and one line each), what
  changed and why, the measurements before and after (how taken, so they can be repeated), what you are unsure of,
  and any decision that is the owner's, with its options. Say plainly what you did not do or could not verify.
- You may be sent your reviewer's findings later: reproduce each before fixing it; fix in the same worktree; report again.

REVIEWER (a worker's own reviewer, started alongside it):
- You review only: no edits to tracked files, no commits, no pushes. Work on your own copies
  (`git -C /home/user/WEDG archive <commit> | tar -x -C <your folder>`, or read the worker's worktree without writing).
- Phase 1 (while the worker builds): read the brief, take the baseline at the base commit the way the brief measures
  it, and write the checks you will run (scripts in your folder). Report the baseline and your plan, then stop: you
  will be sent the worker's commits.
- Phase 2 (when sent the commits): check that the work does what the brief asks, measured or reproduced, that nothing
  near it broke, and the owner's rules above. Report a ranked list: each finding with file:line, how you reproduced or
  measured it, and the fix you suggest; and what you checked and found sound. Do not report what the brief lists as
  left open on purpose unless the work made it worse.
- Your scratch folder: $SC/<your name>/ (make it). Do not use /home/user/WEDG for scratch.

## Environment

- export PATH=/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:$PATH   (dart, flutter)
- The machine has 4 cores, shared with other agents: keep browser runs short, never leave servers or browsers running.
- The 3D prototype page: design/prototype3d/ (farm.html, world.js, play.js, phone.js, engine.js). Build a servable copy:
    THREE_DIR=$SC/three/package python3 tool/proto_app/assemble.py     (writes tool/proto_app/assets/web in THAT checkout)
  Serve it on a port of your own (pick one from 8900-8999 that is free; 8765 is the director's; never stop a server
  you did not start): `python3 -m http.server <port> --bind 127.0.0.1 -d <web folder>`.
- Browser: Playwright is installed (never run "playwright install"). `NODE_PATH=$(npm root -g) node script.js`, with
  chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] }), viewport
  956x440 (the owner's phone, landscape). SwiftShader frame TIMES are not the phone's: count draws and triangles
  (per draw call, shadow pass included), do not judge by milliseconds here. Screenshots at deviceScaleFactor 2 are
  slow; hold requestAnimationFrame (queue the callbacks and release them) around a shot.
- The page's hooks: window.marahEngine (the rules engine; .snapshot is the game), window.__farm.setGame(snapshot) (the
  farm drawn from a snapshot: fake facilities and camels through it), window.__phone (toggle(), enlarge(), shrink()).
  The phone is in a shadow root. A faster game clock: rewrite index.html's `startEngine({ onSnapshot:` to pass
  `timeScale: 20000` (a game day in about 0.6 s); a fixed game: `newGame: { seed: 4242 }`.
- Earlier harnesses to read and reuse (do not edit them in place: copy): $SC/review_de2/ (draws.js: draws and triangles
  at the start, all built, 40 camels; abdiff.js: pixel compare; pins.js; obst2.js; ui.js), $SC/rr_c153/, $SC/rv_ae90/h/
  (keys.cjs, r1..r7.cjs), $SC/haraj/run.js (the market's whole flow, with shots).

## Checks (what CI runs: .github/workflows/ci.yml)

- dart format --output=none --set-exit-if-changed packages apps/marah/lib apps/marah/test tool/proto_engine
- dart analyze --fatal-infos in packages/marah_domain, marah_data, marah_runtime, marah_store, tool/proto_engine
- dart test in each of those (domain also `-p node`; tool/proto_engine `-p vm,node`)
- the "Prototype engine" step (same seed on the VM and in JavaScript, the worker smoke test, the engine page)
- packages/marah_domain: `dart run marah_domain:simulate 10 4`
A script that runs them all in a checkout: $SC/haraj/ci.sh (it has /home/user/WEDG hard-coded: copy and point it at
your checkout).

## Disk

The disk allowance is small (about 6 GB free, shared by every agent). Do not keep more than one extracted copy of the
repository or one built copy of the page; delete build outputs, node caches and big intermediate files when you are
done with them; never download large files. Check `df -h /home/user` if a write fails.

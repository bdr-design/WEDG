# Marah architecture

Marah is a realistic camel-owner game (Arabic, Saudi audience) for iOS and
Android. The web build is paused (owner decision, 2026-11-08). It ships offline first and is built so it can move to
online play (shared market, live auctions, tournaments) without a rewrite.

## Layers

```
apps/marah/              Flutter app: screens, picks the engine per platform, lifecycle
packages/marah_runtime/  runs the engine off the UI thread; view models for screens
packages/marah_store/    SQLite save on devices: incremental, transactional, backups
packages/marah_data/     save interface, JSON envelope and migrations (tests, tools)
packages/marah_domain/   rules and simulation, pure Dart (no Flutter)
docs/                    this file, ADRs, game design, realism sources
tool/                    benchmarks and CI helpers
```

Dependencies point down only: app → runtime → store → data → domain. The domain package does
not import Flutter, so the same rules can run in a worker isolate today and
in a Dart service on a server later.

## Domain (`packages/marah_domain`)

| Part | What it does |
|---|---|
| `common/` | `GameDay`, `WorldClock` (ADR 0001), typed ids, `Riyal`, keyed `Rng`, `Result`/`DomainError` |
| `catalog/` | Colour families, age classes, judged traits, illnesses, regions |
| `model/` | `WorldState` (shared world) and `PlayerState` (one player's farm and money), camel registry, market, contests |
| `commands.dart` | Every player action as a typed command (ids and amounts only) |
| `events.dart` | Everything that can happen, as typed events with values, no text |
| `handlers/` | One handler per command: validate, change state, emit events |
| `systems/` | The daily pipeline: calendar → upkeep → care → health → breeding → market → contests |
| `rules/` | Balance numbers, genetics, judging, valuation, eligibility, contest rules |
| `views/` | What one player may see (observed looks, estimates; never genes or reserve prices) |
| `game.dart` | `Game`: create a world, `dispatch(command)`, `advanceTo(day)` |
| `invariants.dart` | Rules that must always hold (cash = sum of ledger, no stale listings or entries, ...) |

Rules of the road:

- Only handlers and systems change state. Screens read `GameView` and send
  commands.
- Commands never carry prices or offers the server should look up; the
  engine looks them up by id.
- Every random draw comes from `Rng.keyed(seed, [day, system, subject])`.
- Every tunable number lives in `rules/balance.dart` or `rules/contest_rules.dart`,
  marked (field) for real-world values or (balance) for game choices.
- The domain produces no display text. The app turns events and error codes
  into Arabic.

## Saving (`packages/marah_store`, `packages/marah_data`)

On devices the save is a SQLite file (`SqliteGameStore`, ADR 0004): a
save writes only the camels and documents that changed, in one
transaction, and rows keep the in-memory order so a reloaded game replays
identically. Every command is saved before the player is told it worked.
Measured at 10,000 head (desktop): a command's save 8 ms, a day's save
213 ms, reopen 164 ms, 8.7 MB on disk.

Nothing ever destroys a save:

- The fallback (`backups/prev.db`, `prev2.db`) is refreshed only after the
  engine has opened the game, brought it up to date and saved it.
- A file that fails to open, or is replaced by a restore or a new game, is
  first kept as a dated copy in `backups/`; dated copies are never
  overwritten. An upgrade keeps the original (`backups/v<N>-…`) and rebuilds
  the file in the new shape.
- If this version of the game fails to resume a save (a bug), the save is
  reported and left untouched, not locked.
- If a bug leaves the in-memory game half-changed, the engine reloads the
  last save; if the same day keeps failing, it stops the world and says so.
- Android backups include the live save and skip `backups/`.

The JSON store below is kept for tests and tools.

`SaveCodec` writes and reads the save envelope and runs migrations.
`SaveStore` never overwrites a save it could not read, keeps the previous
good save, and serialises writes. See ADR 0003.

## Threading (`packages/marah_runtime`)

Nothing heavy runs on the UI thread (ADR 0002):

- iOS and Android: one long-lived worker isolate owns the game, the saves
  and the clock timers. The UI sends commands and receives ready-made
  `PlayerSnapshot`s; it never decodes JSON or computes views.
- Web (paused): the same `EngineCore` can run time-sliced
  (`InlineEngineClient`, also used in tests); a real Web Worker with OPFS
  storage is the path if the web returns.
- Screens talk only to `EngineClient`.

## Quality gates (CI)

Every push runs, and must pass:

1. `dart format` check
2. `analyze --fatal-infos` with strict casts, inference and raw types
3. domain tests with a line-coverage floor of 85%
4. save-format tests: saves from released versions must load forever
5. runtime tests (core, real worker isolate, atomic files, web slicing)
6. app tests
7. a 10-year simulation of four worlds with a scripted player, checking the
   invariants every game week
8. builds: Android (debug APK) and iOS (simulator, unsigned)

## Online later

What must become server-authoritative: money and ledger, ownership, listings,
offers and reserve prices, auctions and bids, stud services, contest entries
and judging, pregnancy outcomes, genes, illness and death, the NPC market, and
the world clock. The command/event shape, typed ids, and the split between
`WorldState` and `PlayerState` are there for that move.

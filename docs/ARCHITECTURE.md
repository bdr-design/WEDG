# Marah architecture

Marah is a realistic camel-owner game (Arabic, Saudi audience) for iOS,
Android and the web. It ships offline first and is built so it can move to
online play (shared market, live auctions, tournaments) without a rewrite.

## Layers

```
apps/marah/              Flutter app: screens, platform storage, app lifecycle
packages/marah_data/     save format: versioned envelope, migrations, safe store
packages/marah_domain/   rules and simulation, pure Dart (no Flutter)
docs/                    this file, ADRs, game design, realism sources
tool/                    benchmarks and CI helpers
```

Dependencies point down only: app → data → domain. The domain package does
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

## Data (`packages/marah_data`)

`SaveCodec` writes and reads the save envelope and runs migrations.
`SaveStore` never overwrites a save it could not read, keeps the previous
good save, and serialises writes. See ADR 0003.

## Threading

Nothing heavy runs on the UI thread. See ADR 0002 (worker isolate).

## Quality gates (CI)

Every push runs, and must pass:

1. `dart format` check
2. `analyze --fatal-infos` with strict casts, inference and raw types
3. domain tests with a line-coverage floor of 85%
4. save-format tests: saves from released versions must load forever
5. app tests
6. a 10-year simulation of four worlds with a scripted player, checking the
   invariants every game week
7. builds: web, Android (debug APK) and iOS (simulator, unsigned)

## Online later

What must become server-authoritative: money and ledger, ownership, listings,
offers and reserve prices, auctions and bids, stud services, contest entries
and judging, pregnancy outcomes, genes, illness and death, the NPC market, and
the world clock. The command/event shape, typed ids, and the split between
`WorldState` and `PlayerState` are there for that move.

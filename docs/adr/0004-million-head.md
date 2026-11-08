# ADR 0004: One million camels per player, on the phone

- Status: proposed (owner requirement 2026-11-08: "a million head for one
  player"); design to be reviewed before implementation
- Evidence: [../research-scale.md](../research-scale.md) (sourced brief with
  measurements), benchmarks in this repo's history (SQLite, 1M rows)

## Context

The current engine keeps every camel as a Dart object and saves the whole
world as one JSON document. Measured on a desktop CPU:

| herd | game day | save | snapshot |
|---|---|---|---|
| 10,000 | 15 ms | 6 MB | 73 ms |
| 50,000 | 35 ms | 30 MB | 232 ms |
| 1,000,000 (extrapolated) | ~0.5 s | ~600 MB | ~5 s |

One million camel objects would need about 600 MB of RAM (measured 607 B
per camel as objects), close to the kill point of 3 GB iPhones (~1.4 GB).
That design cannot reach one million head.

## Decision

### 1. Store: SQLite through `package:sqlite3` (3.9.x)

- Synchronous FFI, bundled for iOS and Android by build hooks, and runs on
  a plain Dart server too, so the engine package stays server-ready.
- One write connection, owned by the engine isolate. WAL,
  `synchronous=NORMAL`, keyset paging (never `OFFSET`).
- The save **is** the database. Schema changes use `PRAGMA user_version`
  migrations. A good open is followed by a backup copy (`VACUUM INTO`), the
  equivalent of today's `.prev`; a failed open or `integrity_check` keeps
  the file untouched and reports it.
- Every command and every simulated day runs in a transaction: an
  exception rolls back, so a half-applied command can never be saved.

Measured for 1M rows: insert 1.6 s, 74–86 MB on disk, page of 50 in 0.1 ms,
point lookup 6 µs, farm summary 2 ms.

### 2. Compact camel rows; side tables for what is rare

`camel(id INTEGER PRIMARY KEY, owner, farm, sex, category, born, status,
name, sire, dam, traits BLOB(20), cond, cond_day, base_quality)`

- Traits: 10 breeding values + 10 deviations quantised to one byte each
  (resolution 0.4 points on 0–100; quantised at birth, so saves stay exact).
- Rare data in side tables: `illness`, `pregnancy`, `placing`,
  `custom_name`, `listing`, `entry`. Most camels have none.
- Records are never deleted. Dead and sold camels keep their row with a
  status; this keeps pedigrees and history (review finding).

Measured: one 20-byte BLOB costs 56 B/row against 224 B/row for 20 REAL
columns.

### 3. Days are simulated by events, not by visiting every camel

- **Strata:** camels are grouped by farm × sex × age class × state
  (healthy, sick, pregnant). Each stratum keeps its member ids in an
  `Int32List` in memory (≈4 MB for 1M).
- **How many:** for each stratum, day and event type, draw the count
  exactly from Binomial(n, p) (inversion for small np, BTPE above). No
  Poisson approximation: its error is not negligible at these sizes.
- **Which ones:** Floyd's algorithm picks k distinct members with k random
  draws. Risk that differs per camel (age, condition, genes) uses thinning.
- **Randomness:** keyed by (world seed, day, stratum, event), so catching up
  in one go or in steps gives the same world.
- **Body condition** is not updated daily. Each camel stores an anchor
  (value, day); the current value is the closed form
  `target + (c0 − target)·e^(−k·t)` evaluated on read, where the target comes
  from the farm's policy timeline. Changing a farm's feed writes one policy
  row, not a million camel rows.
- **Writes:** the day's changes are appended to an event journal table
  (measured 1 ms for 3,000 events) and folded into camel rows in one sorted
  batch at the end of a catch-up chunk (measured 0.47 s for 300k camels).
  In-place random updates were measured at 64–70 ms per day.

Expected load at 1M head (rates from Saudi field data in the brief): about
840 births, 110–190 deaths, 575 sales and 1,400 illnesses per day.

### 4. Screens page, they never load the herd

- The snapshot carries summaries (counts per farm, category, age; money;
  alerts) with a revision per section, so only changed sections rebuild.
- Lists are keyset pages of 50 from indexed queries (by quality, age,
  farm). A camel's page is a point lookup.
- Views are projections that never expose breeding values, reserve
  prices, or another player's unchecked pregnancies (review finding).

### 5. Memory budget

Engine isolate ≤ 150 MB steady, ≤ 250 MB peak: SQLite page cache 8–16 MB,
strata id arrays ≈ 4 MB, optional trait columns for samplers ≈ 20 MB.
Never materialise one Dart object per camel.

### 6. Management at scale (needs the owner's approval in the game design)

No one can treat 1,400 sick camels a day by hand. A 1M holding is run like
the real large operations: many farms (عزب), staff per farm (herder ratio
affects conception: 95% below 1:25, 80% at 1:25–50, 73% above 1:50 in a
study of Saudi herds), vets, and standing policies (auto-treat, breeding
plan, culling and sales). Individual camels still matter: champions,
breeding stock and contest entries are followed one by one. 1M is ~45% of
the Kingdom's 2.24M camels (GASTAT 2024), so the game should present it as
a national-scale holding, not a family farm.

## Consequences

- The domain gets a `CamelStore` interface: an in-memory store for tests
  and small worlds, a SQLite store for devices and later a server.
- Systems are rewritten from "for each camel" to "for each stratum".
- The JSON save remains only for tests and tools; the device save is the
  SQLite file (save format v2).
- Performance budgets move to a 1M-head world (catch-up per real day,
  page query, memory), measured in CI on desktop and checked on a low-end
  phone before release.
- Web stays paused; when it returns, SQLite runs in a dedicated Web
  Worker with OPFS storage.

## Plan

1. Typed events, a per-player inbox, and non-leaking views (independent of
   storage; review findings).
2. `CamelStore` interface with an in-memory implementation; strata,
   binomial sampling and closed-form condition; all tests and the 10-year
   simulation pass on it.
3. SQLite store: schema, event journal and fold, transactions, migrations,
   backup rotation; a 1M-head benchmark in CI.
4. Management layer (farms, staff, policies) after the owner approves the
   game design.

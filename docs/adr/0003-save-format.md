# ADR 0003: Save format and safe loading

- Status: accepted
- Deciders: Claude, reviewed by an independent architecture review

## Context

The first draft lost a player's whole farm whenever a load failed: errors
were swallowed, the app showed onboarding, and the next save overwrote the
old one. Values were also rounded on save, so a save/load changed later
results.

## Decision

1. A save is an envelope: `{"format": "marah-save", "version": N,
   "savedAt": ..., "data": {...}}` (`packages/marah_data`).
2. Every change to the shape of the state bumps `SaveCodec.currentVersion`
   and adds a migration step `migrations[N-1]` that upgrades plain JSON from
   the previous version. Migrations never use today's model classes.
3. Saves written by released versions are kept as fixtures in
   `packages/marah_data/test/fixtures/` and must load forever. Until the
   first public release the v1 fixture may be regenerated; after that,
   never.
4. A save that cannot be read is copied to `<slot>.broken`, the slot is
   locked, and the app asks the player what to do. It is never overwritten
   automatically. Every write keeps the previous good save as `<slot>.prev`.
5. Saves are exact: traits and body condition are kept at 2 decimals in
   memory, so the JSON round trip is lossless and a game replays the same
   with or without save/reload in between (tested).
6. The save stays small: camels that left the world are dropped unless a
   player's camel descends from them, prize tables are derived instead of
   stored, rounds without entries are dropped once judged, and the activity
   log keeps the last 400 events.

## Measurements (4 game-years of active play, desktop CPU)

| | before | after |
|---|---|---|
| save size | 745 KB | 166 KB |
| encode | 13.4 ms | 8.1 ms |
| decode | 15.8 ms | 9.9 ms |

Phones are several times slower, so encoding and writing happen off the UI
thread (ADR 0002).

# ADR 0001: Time model

- Status: accepted (owner chose "one real day = one game week", 2026-11-08)
- Deciders: owner, Claude

## Context

The game must feel real: breeding happens in the cool months, gestation is
about 13 months, contests run from October to March, and a herd needs care
every day. Played in real time, a pregnancy would take a year. Played with a
"next day" button, the game cannot become online later, because a shared
market, live auctions and tournaments need one clock that everyone shares.

## Decision

1. The world advances in whole **game days** (`GameDay`, an int counted from
   1 January 2026). Dates use the Gregorian calendar so seasons fall where
   they do in Saudi Arabia.
2. Time is **real time at 7×**: one real day is one game week, so one game
   day lasts 3 h 25 min 43 s. A pregnancy takes about 55 real days; a full
   year of seasons takes 52 real days.
3. The clock is an interface, `WorldClock`:
   - offline: `RealTimeClock`, anchored to the device time when the game
     started. A device clock moved backwards never rewinds the world;
   - online (later): the server's clock. Clients never advance time.
4. The world keeps running while the app is closed. On open and on resume,
   the engine **catches up** day by day to `clock.today()`; each day runs
   the same ordered pipeline of systems (calendar, upkeep, care, health,
   breeding, market, contests).
5. Randomness is keyed by day and subject (`Rng.keyed(seed, [day, 'health',
   camelId])`), so catching up in one go or in many small steps gives the
   same world.

## Consequences

- A player who is away for a month returns to 210 simulated days. The
  catch-up must not run on the UI thread (see ADR 0002).
- Offline, changing the device clock forward is possible. That only cheats
  a single-player game; online the server clock removes it.
- Tests and tools use `ManualClock` and `Game.advanceDays`.

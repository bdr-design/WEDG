# ADR 0002: Nothing heavy on the UI thread

- Status: accepted. Web paused by the owner on 2026-11-08: the app
  targets iOS and Android only until the web is picked up again.
- Deciders: owner ("no load on the main thread"), Claude; design brief with
  sources in [../research-threading.md](../research-threading.md)

## Context

Measured on a desktop CPU after 4 game-years of active play (phones are
several times slower):

| work | time |
|---|---|
| encode save (166 KB) | 8.1 ms |
| decode save | 9.9 ms |
| catch up 210 game days (a month away) | 14.6 ms |
| build all views | < 0.2 ms |

A frame has about 16 ms at 60 Hz and 8 ms at 120 Hz. On a phone, encoding,
decoding or catching up on the UI thread would drop frames.

## Decision

1. **iOS and Android: one long-lived worker isolate** (`IsolateEngineClient`,
   `packages/marah_runtime`). It owns the `Game`, the save store and the
   clock timers. Long-lived because the engine is stateful and its state
   should never cross threads (`SendPort.send` copies the whole object
   graph at send time).
2. **Only small, ready-made data crosses.** UI → worker: commands with ids
   and amounts. Worker → UI: `Reply`, `Failure`, and pushes:
   `PlayerSnapshot` (everything the main screens show, built by `Presenter`
   in the worker), `CatchUpProgress`. Details (one camel, one festival) are
   fetched on demand. The UI never decodes JSON or computes views.
3. **Saving happens in the worker** with plain `dart:io`: the save folder is
   looked up once on the UI isolate (`path_provider`) and passed in. Files
   are written atomically: a uniquely named temp file, flushed, then renamed over the old
   file. Autosave runs 1.5 s after a change, after every catch-up, and when
   the app is hidden.
4. **Web (paused).** Notes kept for when it resumes: **no isolates.** `InlineEngineClient` runs the same `EngineCore` on
   the main thread in slices of about 1 ms, each scheduled between frames
   with `SchedulerBinding.scheduleTask`. Measured: 420 game days caught up
   in 65 ms with the longest stall 6.9 ms, including the final save. A real
   Web Worker (separately compiled entry point) is the upgrade path if the
   web becomes a main platform. Web saves use `shared_preferences`
   (`localStorage`, synchronous); IndexedDB from a worker is the upgrade.
5. **Operations are serialised** inside `EngineCore`: a command never lands
   in the middle of a catch-up.
6. **Lifecycle:** `AppLifecycleListener.onHide` saves and stops timers;
   `onShow` catches up with the clock. While open, a one-shot timer fires at
   the next game-day boundary (every 3 h 25 min 43 s).
7. **Failures:** every request is answered with `Reply` or `Failure`. If the
   worker dies, all pending calls fail and the client reports it; the last
   atomic save is intact.

## Consequences

- One client interface (`EngineClient`) hides the platform: screens are the
  same everywhere.
- Snapshots grow with the herd and the market; keep them to what screens
  show and fetch details on demand.
- Tests cover the core, the real worker isolate (spawn, play, save to disk,
  reopen), atomic file writes, and a timing test that the sliced web path
  keeps the event loop running.

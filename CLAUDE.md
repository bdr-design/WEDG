# Working with the owner of Marah (مراح)

These are the owner's standing rules for this project. Follow them in every session.

## How we work

- **Claude builds everything itself; agents only review.**
  - Do not hand building or fixing to agents.
  - Independent review agents check every piece of work, and every fix,
    before it is shown to the owner or committed as done.
  - Re-measure or reproduce each finding before acting on it.
- **Show the design before adopting it.** Present screenshots or a published
  prototype. Decisions that are the owner's (layout rules, scope, trade-offs
  between realism and weight) are asked, not assumed.
- **Talk to the owner in Gulf Arabic.** Code, commits and technical docs stay
  in English. Player-facing text is Arabic.

## What the game must be

**Smoothness in play and realism come first, ahead of every other goal.**
Every change is judged on both:
- **Smoothness in play.** On a mid-range phone during play: frame time,
  stutter, memory pressure and heat over a long session, measured rather than
  guessed.
- **Realism.** Whether it matches the real thing.

**App download size does not matter to the owner.** Never trade smoothness
or realism for a smaller app.

- **Realism above all:** real geography, real camel anatomy and gait, real
  Saudi market and festival rules. Every number is either sourced or marked as
  a game choice (see `docs/GDD.md`).
- **Light on the phone:** see the budget in `docs/adr/0005-3d-world.md`
  (draws, triangles, texture memory, skinned camels, shadows).
- **The map is the centre of play:**
  - Nothing permanent covers it: no menus and no bottom bar.
  - Nothing written floats over the game: icon buttons at the screen's edges
    only, and icon pins on the places. Words appear only in a card the player
    opened.
  - Places are reached by tapping them on the map, and a small card opens
    beside the place.
  - Landscape only (the owner's decision of 11 Nov 2026). A phone held
    upright shows the game turned a quarter turn.
- **Models are built by code** from the owner's photos (`tool/camel3d`,
  `tool/vehicle3d`, `tool/terrain3d`).

## Repository

- Develop on the branch the session names, commit with clear messages, push
  to that branch only, and open no pull request unless asked.
- Flutter workspace:
  - `apps/marah`
  - `packages/marah_domain`, `marah_data`, `marah_store`, `marah_runtime`
- 3D design prototypes are in `design/prototype3d/`.

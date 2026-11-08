# Working with the owner of Marah (مراح)

These are the owner's standing rules for this project. Follow them in every session.

## How we work

- **Agents in every step.** Independent agents take part in building, reviewing,
  fixing and checking the fix. Nothing is shown to the owner or committed as
  done until an independent agent has reviewed it, and each finding has been
  re-measured or reproduced before it is acted on.
- **Show the design before adopting it.** Present screenshots or a published
  prototype. Decisions that are the owner's (layout rules, scope, trade-offs
  between realism and weight) are asked, not assumed.
- **Talk to the owner in Gulf Arabic.** Code, commits and technical docs stay
  in English. Player-facing text is Arabic.

## What the game must be

**Lightness and realism come first, ahead of every other goal.** Every change
is judged on both:
- What it costs a mid-range phone per frame and in memory, measured rather
  than guessed.
- Whether it matches the real thing.

- **Realism above all:** real geography, real camel anatomy and gait, real
  Saudi market and festival rules. Every number is either sourced or marked as
  a game choice (see `docs/GDD.md`).
- **Light on the phone:** see the budget in `docs/adr/0005-3d-world.md`
  (draws, triangles, texture memory, skinned camels, shadows).
- **The map is the centre of play:**
  - Nothing permanent covers it: no menus and no bottom bar.
  - Places are reached by tapping them on the map, and a small card opens
    beside the place.
  - Both portrait and landscape are supported.
- **Models are built by code** from the owner's photos (`tool/camel3d`,
  `tool/vehicle3d`, `tool/terrain3d`).

## Repository

- Develop on the branch the session names, commit with clear messages, push
  to that branch only, and open no pull request unless asked.
- Flutter workspace:
  - `apps/marah`
  - `packages/marah_domain`, `marah_data`, `marah_store`, `marah_runtime`
- 3D design prototypes are in `design/prototype3d/`.

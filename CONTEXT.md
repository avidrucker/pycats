# pycats — project context

Orientation for newcomers (human contributors **and** coding agents). Kept short
and stable: the ubiquitous language and the invariants that don't change often.
For *how to run / test* see [README.md](./README.md); for *conventions* see
[RULES.md](./RULES.md); for the detailed architecture/layer map and scores see the
review doc linked below.

## Ubiquitous language

The domain vocabulary, shared by the code, the tests, and the issue tracker. The
**mechanics** terms (hitbox, hurtbox, knockback/BKB/KBG, hitstun, shield, dodge, prone,
dizzy, ledge-hang, KO, startup/active/recovery, …) are defined once in the
**[glossary](./docs/glossary.md)** — don't restate them here. Below are the
**pycats-specific** terms that tie those mechanics to *this* codebase:

- **fighter** — a combatant's pure domain state/rules (`Fighter`), independent of how it's drawn or controlled.
- **player** — the thin pygame `Sprite` adapter wrapping a `Fighter` for the live game.
- **percent** — accumulated damage (≥ 0); higher percent ⇒ more knockback.
- **stock / fall** — a life; losing one (the KO itself is in the [glossary](./docs/glossary.md)).
- **fighter states** — the FSM labels the statechart emits (`idle`/`run`/`jump`/`fall`/`shield`/`dodge`/`hurt`/`prone`/`ledge_hang`/…); each mechanic is in the glossary, the state graph in [`pm-reference/fighter-states.md`](./docs/pm-reference/fighter-states.md).
- **MoveClock** — the single source of "where are we in the current move" (replaced the old triple representation).
- **golden** — a recorded deterministic snapshot used as the regression oracle (`tests/golden/`).

## Determinism / headless contract

The reason the test oracle works — preserve these when changing the core:

- The **rules core is Sprite-free + display-free**: `combat/`, `statecharts/`, `systems/`, `sim/controllers`, `characters/`, `config`, `stats_print`, `core/physics` use pygame **only** for `Vector2`/`Rect` value types (deterministic, headless) — never `Sprite`/`Surface`/`display`/`event`/`draw` (sanctioned by [ADR-0004](./docs/adr/0004-pygame-math-value-types-sanctioned.md); guard #339).
- **Frame-counter timing, no wall-clock**: timing is counted in frames, never `pygame.time` / real clock.
- **No RNG in the core**: the sim is deterministic, so golden snapshots reproduce exactly. Any randomness (e.g. AI seeding) is an injected seam, not ambient `random`.
- **Headless by design**: the suite runs under `SDL_VIDEODRIVER=dummy`; the core never *requires* a display.
- **Present layer is separate**: rendering (`render_*`), the `Player` sprite, input polling (`core/input` `poll()`), and `game.py` are adapters around the core; `settings.py` / `runtime_settings.py` are present-layer only and never read by the sim/golden path.

## Architecture / layer map

The full layer map, port/adapter analysis, and DDD/hexagonal/spec scores live in
the architecture review. Latest: **[`docs/research/architecture-review-2026-06b.md`](./docs/research/architecture-review-2026-06b.md)**
(re-review, #252 — DDD ~8.5 · Hexagonal ~7 · BDD ~8.5), building on the original
[`architecture-review-2026-06.md`](./docs/research/architecture-review-2026-06.md) (#56).
(Linked, not duplicated, so the two don't drift.)

## Decisions

Architecture decisions are recorded as ADRs — see [`docs/adr/`](./docs/adr/).

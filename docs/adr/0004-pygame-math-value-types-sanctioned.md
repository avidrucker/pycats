# ADR-0004 — Sanction pygame.math (Vector2/Rect) as value types in the rules core

- **Status:** Accepted
- **Date:** 2026-06-30

## Context

pycats keeps its rules/sim core **headless and deterministic**: `combat/`,
`statecharts/`, `systems/`, `sim/controllers`, `characters/`, `config`,
`stats_print` (and the physics in `core/physics.py`) run under
`SDL_VIDEODRIVER=dummy` with no display, no RNG, and frame-counter timing. That is
what lets the golden snapshots reproduce byte-for-byte.

Those modules do, however, use pygame's `Vector2` and `Rect` as **value types** —
`core/physics.py` alone has `pg.Rect`×7, `pg.Vector2`×9, and Rect's collision API
(`.colliderect`, `.centerx`, `.copy`); `systems/movement.py` and `entities/fighter.py`
use `Vector2`/`Rect` too. The 2026-06 re-review (#264, finding **H4**) flagged this
and asked: should the core keep `pygame.math`, or move to a project-owned pure
`Vec2`/`Rect` so it imports no pygame at all? It also noted `CONTEXT.md` was
inaccurate — it claimed `systems/` imports no pygame, but `systems/movement.py`
imports `pygame.Vector2`.

Forces:
- `Vector2`/`Rect` are **deterministic** (plain float/int math, no RNG, no
  wall-clock) and **display-free** — they do not require SDL or a window.
- `pygame-ce` is a **hard, declared dependency** of the project (rendering needs
  it regardless), so "importable without pygame installed" — the only thing a
  pure clone would buy — is moot.
- Replacing `Rect` means reimplementing its geometry/collision API (used across
  `core/physics.py`) and keeping a `Rect` clone in sync, at real risk to the
  byte-identical goldens, for a negligible purity gain.

## Decision

We will **sanction `pygame.math`'s `Vector2` and `Rect` as value types** in the
rules/sim core. The core's headless-determinism invariant is stated as
**Sprite-free and display-free** — the core may use pygame only for `Vector2`/`Rect`
value types, and must not touch the pygame *framework* (`Sprite`, `Surface`,
`display`, `event`, `draw`, `font`, `image`, `transform`, `mixer`). We will **not**
introduce a project-owned pure `Vec2`/`Rect`.

## Consequences

- **Easier:** no churn to `core/physics.py`/`movement.py`/`fighter.py`; the
  goldens stay byte-identical; the deterministic-value-type usage is now
  documented as intentional rather than a smell.
- **`CONTEXT.md` corrected:** its determinism contract now reads "Sprite-free +
  display-free; uses pygame only for `Vector2`/`Rect` value types" instead of the
  inaccurate "imports no pygame."
- **Boundary enforced:** the sanctioned line (value types OK; framework NOT) is
  made able-to-fail by an AST guard over the core modules — filed as **#339**.
- **Explicitly ruled out:** a pure `Vec2`/`Rect` reimplementation of the core
  geometry types.

Decided in a pair-work session (2026-06-30); see the ruling on #320.

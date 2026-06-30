# ADR-0002 — Dual-backend endgame: finish the statechart migration, delete legacy

- **Status:** Accepted
- **Date:** 2026-06-29

## Context

pycats has shipped **two parallel implementations** of its fighter FSM
(`LegacyEngine` in `systems/state_engine.py` vs `StatechartEngine` in
`systems/state_engine_sc.py`) and its match loop (`LegacyMatchEngine` vs
`StatechartMatchEngine` in `systems/match_engine.py`), selected at runtime
(`make_state_engine` / `make_match_engine`; `PYCATS_STATE_BACKEND` / `--backend`).
This was deliberate migration scaffolding: `tests/test_parity.py` asserts the two
backends produce **byte-identical** per-frame snapshots, and the statechart engine
is already the default for the live game, `watch.py`, and `bench_render.py`. Legacy
has been the "frozen classic baseline."

Maintaining two byte-identical engines indefinitely is an ongoing tax: every
fighter/match-rules change must land in both. The migration was always meant to
*finish*. Decision tracked as #174 (doc item #11 of the #56 review).

## Decision

We **finish the migration and remove the legacy backend.** `statecharts-py`
becomes the **sole** fighter-FSM and match engine. We delete `LegacyEngine`,
`LegacyMatchEngine`, the `--backend legacy` / `PYCATS_STATE_BACKEND` selection
plumbing, and the now-single-valued `backend` parameters.

The equivalence guard is **preserved, not discarded**: before removing legacy, its
byte-output is captured as a recorded golden so `test_parity` converts from
*legacy-vs-statechart* into *statechart-vs-frozen-golden*. We therefore keep the
regression coverage without keeping a second live engine.

This is safe because parity is currently green — the statechart engine is proven
byte-identical to legacy, so nothing is "only correct in legacy"; the removal is
behaviour-neutral.

## Consequences

- **Easier:** one engine to maintain; no more dual-landing of every rules change;
  simpler `Player`/`sim/runner`/`game.py` (no backend branching).
- **Accepted cost:** `statecharts-py` (sibling repo) becomes a **hard** runtime
  dependency, and we lose the independent second-implementation oracle. The recorded
  golden replaces most of that safety value (regression, though not "two independent
  authors agree").
- **Follow-up (separate DEV tickets, filed after this ADR; lazy decomposition):**
  1. Freeze legacy's current output as a golden and repoint `test_parity` to
     statechart-vs-golden (do this **first**, so coverage never lapses).
  2. Delete `LegacyEngine` + `LegacyMatchEngine` and the legacy branches in
     `make_state_engine` / `make_match_engine`.
  3. Remove the `--backend` flag, `PYCATS_STATE_BACKEND`, and collapse the now
     single-valued `backend`/`state_backend` parameters (`entities/player.py`,
     `sim/runner.py`, `game.py`, `watch.py`).
  Each ships with a green suite; ordering matters (1 before 2).
- **Reversal:** would require a new ADR superseding this one (and resurrecting
  legacy from git history).

## Addendum — extends to the screen backend (epic #100)

Applies equally to the screen backend (`systems/fsm.py` / `LegacyScreenEngine`, epic
#100): retire it on the same golden-freeze→delete→strip-plumbing path (slices 4a/4b/4c,
#234/#235/#236), with `tests/test_screen_parity.py` + `tests/golden/screen_parity.json`
as the screen-flow analogue of the fighter golden gate.

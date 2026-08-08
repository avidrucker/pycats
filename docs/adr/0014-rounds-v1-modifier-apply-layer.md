# ADR-0014 — ROUNDS v1 modifier apply-layer: load-time `FighterData` patch, card-owned cancellation

## Status

Accepted — 2026-08-02. Resolves the **ROUNDS Mode v1 wayfinder map** (#1096) decision
#1102 ("modifier mechanism — how a card patches Fighter/MoveData deterministically").
Downstream of **ADR-0013** (per-seam modifier *shapes*); epic #347.

## Context

ADR-0013 fixed *what each seam becomes* as a card knob (weight → multiplicative %,
jump count → additive ±N, velocities round-on-apply, …) but explicitly left *where and
how a delta applies* to #1102. This ADR settles that apply/stack layer. It picks the
**approach**, per #1102's scope; the detailed stacking math is downstream DEV/design fog.

Grounding facts, read from source 2026-08-02:

- **`Fighter.__init__` copies each seam into an instance attribute** — `entities/fighter.py`:
  `self.weight = fighter_data.weight`, `self.jump_vel = fighter_data.jump_vel`,
  `self.move_speed`, `self.dash_speed`, `self.run_speed`, `self.gravity`, `self.max_jumps`,
  `self.max_fall_speed`, `self.stand_size`, the hurtboxes, …. It does **not** re-read
  `fighter_data` per frame. Consumers read the cached copy (`combat/knockback.py::knockback`
  takes `weight`; jump logic reads `self.jump_vel`).
- **`loadout/build_fighter.py::build_fighter(Selection) → BuiltFighter`** is the single seam
  that hands a `FighterData` to *both* the headless sim (`sim/runner.py`) and the live game,
  via `resolvers.fighter_data_of(character) → combat.data.load_fighter_data(character.key)`.
  There is no `if` on the character key — every fighter flows through it.
- **`combat/provenance.py` is not a runtime value-drift mechanism.** It is a static,
  data-only citation registry — one `Provenance(value, unit, source, status, issue,
  derivation)` row per **global `config` scalar**, mirrored against `config` for the
  `tests/test_tuning_provenance.py` drift-guard. It explicitly excludes per-fighter/per-move
  data ("Per-character/move data in `characters/*.py` is a later slice") and has no
  apply/delta facility.
- ROUNDS lets players **delete cards between rounds** (`docs/research/2026-08-02-rounds-game-mechanics-findings.md`,
  #1075), so the apply-layer must make active modifiers *trackable and cancellable*, not
  merely additive.

## Decision

### 1. Apply timing — load-time patch, not a per-tick stack

A card loadout rewrites the `FighterData` **once, at the `build_fighter` seam**, before
`Fighter.__init__` copies its fields. Every downstream read then sees the patched value for
free — zero per-frame cost, trivial determinism (the patch precedes the first tick).

A per-tick modifier stack was rejected: every seam ADR-0013 named is a *static* per-match
stat, so a per-tick stack pays a whole-architecture cost — converting every cached
`self.<seam>` read into a live stack re-evaluation — to serve zero v1 modifiers. Time-varying
effects (the novel %-per-second family, #1111) compose *on top* as their own per-tick systems
on a single field (`percent`); they do not pull the stat layer into per-tick evaluation.

### 2. Delta record — bare, provenance-free

A modifier is a bare `(seam, op, value)` record — `op` is one of ADR-0013's fixed operations
(`mult_pct` / `add_n`), nothing more. **No** `Provenance`-shaped source/status/derivation
sidecar: provenance answers "why is this game value what it is" (a canon citation), which is
meaningless for a *drafted* card whose "why" is "the player picked it" — already captured by
the card's catalog id (#1101) and the draft seed (#1099). A second sourced registry would
only add a `test_tuning_provenance`-style lock-step burden for no design payoff.

### 3. Cancellation — card-owned, recompute-from-baseline (model C1)

Active state is the **drafted card list** (`list[Card]`), not a flat delta list. A pure
`card → [Modifier]` function derives the bare deltas; effective stats are always
`apply(baseline_FighterData, all_derived_deltas) → new FighterData`. Because ROUNDS deletes
**cards** (never individual stat deltas), the card is the unit of tracking and cancellation:

- **Delete a card** → drop it from the list → re-derive → recompute from the pristine
  baseline. Exact, free, no per-delta owner id.

**Invariant — the patch is functional.** `apply(baseline, deltas)` returns a *new*
`FighterData`; it never mutates the baseline in place. This is what makes card deletion
reversible: dropping a card and recomputing from the immutable baseline always lands the
correct stats. Mutate-in-place would make deletion irreversible and is prohibited.

The recompute runs **once per round** at the `build_fighter` seam — which is exactly ROUNDS'
card-deletion / redraft boundary — so the load-time apply and cancellation share one seam.

## Consequences

- The apply-layer is a **pure function over `(baseline FighterData, list[Card])`** — seedable
  and golden-stable per #1099 (no RNG in `apply`; the draft that *produces* the card list owns
  the seed). Adds no per-frame cost and no new determinism surface to the tick loop.
- A card that must change a stat *mid-stock* (e.g. ramp weight over a round) cannot be
  expressed by this layer — it needs its own per-tick hook, like #1111. ADR-0013 deferred
  every time-varying stat seam, so this cost is zero for v1.
- Per-delta audit ("which card moved this stat, this match") is reconstructable from the
  drafted card list + seed rather than read off a modifier; a live debug overlay wanting it
  is a downstream ticket (owner-tagged deltas, model C2), not the core layer.
- **Stacking math** (multiple cards on one seam: sum-percents-then-apply vs multiply-factors;
  floor/round rules) is downstream DEV/design fog, not fixed here — #1102 picked the
  *approach*. ADR-0013's round-on-apply rule for int seams governs the final coercion.

## Follow-up

- Downstream DEV child (post-map): implement `apply(baseline, cards)` + the `card → [Modifier]`
  derivation at the `build_fighter` seam, with the functional-patch invariant under test.
- The novel %-per-second seam (#1111) stays a separate per-tick system, not part of this
  stat-patch layer.
- The map's "exact per-card magnitudes + stacking math" fog graduates via the swinginess
  policy (#1100) + the starter card set (#1101).

## Relationships

- Downstream of **ADR-0013** (per-seam modifier shapes) — this ADR is its apply-layer half.
- Resolves **#1102** (modifier mechanism), a child of the **ROUNDS Mode v1 wayfinder map**
  (#1096), epic **#347**.
- Consistent with **#1099** (seeding contract — `apply` is RNG-free, the draft owns the seed),
  **#1075 / #1076** (ROUNDS mechanics + PM-fit premortem — card deletion between rounds),
  **#1101** (card catalog — the `Card` identity + `card → [Modifier]` source), **#1111**
  (novel %-per-second — separate per-tick system).
- Grounded in: `entities/fighter.py` (seam caching), `loadout/build_fighter.py` +
  `loadout/resolvers.py` (the apply seam), `combat/provenance.py` (why it is *not* reused),
  `combat/knockback.py` (a `weight` consumer).

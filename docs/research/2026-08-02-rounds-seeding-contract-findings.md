# ROUNDS-mode draft — seeding contract against the #166 seam — findings

**Ticket:** #1099 (RESEARCH · AFK · `area:combat`) · **Date:** 2026-08-02 · **Agent:** FIG
**Wayfinder map:** *ROUNDS Mode v1 — wayfinder map* (#1096) · **Parent epic:** #347.
**Question:** can a ROUNDS-mode card *draft* be made reproducible for the golden tests by riding the #166 seeded-RNG seam, and what exactly would it call? **Findings only** — the seeding *decision* it feeds (how to derive an independent draft stream) belongs to the downstream modifier-mechanism (#1102) and draft-screen (#1103) decisions.

> **Headline:** the draft **can** be deterministic, **but not by reusing the controller RNG.** The #166 seam is a single flat `random.Random` per controller, shared by reference in call order, with **no multi-stream / spawn / derivation facility**. A draft must own its **own independent** `random.Random`, seeded independently of the controller RNG — and *how* to derive that independent stream from the user-facing `--seed` is a contract that **does not exist yet** and must be defined.

All claims below were verified against source in worktree `wt-fig-pycats-1099` (branch base) — landmarks cited by `file::symbol`.

---

## 1. Where the seam lives + its API

The #166 seam is a **per-controller injected `random.Random`**, not a central RNG service or config module — it lives at the controller edge:

- `pycats/sim/controllers.py::BaseController.__init__` takes `rng=None`; when `None` it falls back to `random.Random(DEFAULT_CONTROLLER_SEED)`:
  > `self.rng = rng if rng is not None else random.Random(DEFAULT_CONTROLLER_SEED)`
- `pycats/sim/controllers.py::DEFAULT_CONTROLLER_SEED` = **0**. (Minor: the constant is defined **twice** with the same value — a harmless duplicate worth cleaning up someday, not here.)
- Subclasses forward the kwarg: `AttackerController.__init__`, `IdlerController.__init__`, `FollowerController.__init__` each accept `rng=None` and pass `super().__init__(..., rng=rng)`.
- Stdlib `random` only — **no** numpy, `default_rng`, or `SeedSequence` anywhere in `pycats/sim/` or `watch.py` (grep returned nothing).

## 2. How a caller obtains a deterministic RNG — and where fixed-vs-clocktime is chosen

The RNG is **caller-injected**; the **seed choice lives at the CLI edge**, not in the controllers:

- `watch.py::main`:
  > `rng = random.Random(args.seed) if args.seed is not None else random.Random()`
  with the in-code note *"Seed home is this CLI edge (#166): an explicit --seed is reproducible; absent is clocktime."* The `--seed` arg is defined in `watch.py`'s arg parser.
- That **single** `rng` instance is then injected into every controller for the match — so all players **share one `random.Random` by reference**, consumed in call order. The only draws today are `self.rng.random()` probability checks inside `AttackerController.decide` and `IdlerController.decide`.

## 3. How the goldens get determinism from it

Two ways, both leaning on the fixed-seed default (seed **0**):

- **Explicit pin** — the live two-NPC golden pins the seed verbatim (`tests/test_golden.py`, two_npc case):
  > `a = AttackerController(attacker_num=1, rng=random.Random(0))`
  > `f = FollowerController(attacker_num=2, rng=random.Random(0))`
- **Seed-invariance** — the default live-battle archetypes don't draw `rng` at their default knobs, so their bytes are seed-independent; guarded by `tests/test_controller_rng.py` (`test_attacker_ignores_rng_so_goldens_are_seed_invariant`, `test_default_rng_is_fixed_seed_deterministic`).
- `tests/golden_util.py::check_or_update` is RNG-agnostic — it byte-compares snapshots and never touches seeding.

## 4. How a draft RNG stream would plug in — the constraint that becomes a decision

Stated as **observations from the seam's shape**, not a design (the design is #1102/#1103's call):

1. **The draft needs its own independent `random.Random`.** The pattern-consistent move mirrors `BaseController.__init__`: a draft owner holds `self.rng = rng if rng is not None else random.Random(<default>)`, with a fixed default keeping goldens green.
2. **It must NOT consume from the shared controller RNG.** Today's single `random.Random(args.seed)` is shared across controllers by reference in call order. If the draft drew from that same instance, then **adding or removing any AI `rng.random()` call would shift the draft sequence** — every draft-bearing golden would churn on unrelated AI tuning. So the draft stream must be **independent**.
3. **Deriving an independent stream from the one user `--seed` is a contract that doesn't exist yet.** The stdlib `random.Random` seam has **no `spawn` / `SeedSequence` / sub-stream / seed-offset facility**. To keep a single user-facing `--seed` while giving the draft an independent, stable sequence, a **new derivation step** is required — e.g. seed the draft from a fixed offset of the base seed, or from an independent named seed, or spawn a child generator (which would mean introducing a spawn-capable generator). **Defining that derivation is exactly the seeding sub-decision** the modifier-mechanism / draft-screen decisions must settle.

There is **no existing card-draft / deal / shuffle code** to anchor against (the only "draft" token in the tree is a game-window caption string in `pycats/game.py`).

---

## 5. What this hands downstream

- **Confirmed:** a ROUNDS draft *can* be golden-reproducible on the existing infrastructure — the seam's fixed-seed pattern is exactly the right shape.
- **Decision owed (small, but real):** the **draft-seed derivation contract** — how the draft gets an *independent* deterministic stream from the user `--seed` without coupling to controller draw order. Owned by the modifier-mechanism (#1102) and/or draft-screen (#1103) decisions; **not** free reuse of the seam.
- **Non-blocker:** nothing here blocks the format (#1098) or survivability (#1097) decisions; it constrains how the eventual draft is *built*, deterministically.

## Sources

- `pycats/sim/controllers.py::BaseController.__init__`, `::DEFAULT_CONTROLLER_SEED`, `::AttackerController`, `::IdlerController`, `::FollowerController`
- `watch.py::main` (the `--seed` CLI edge, #166)
- `tests/test_golden.py` (two_npc seed pin), `tests/test_controller_rng.py` (seed-invariance + default-seed determinism), `tests/golden_util.py::check_or_update`
- #166 (CLOSED) — the seeded-RNG seam this builds on.

*Gathered by a read-only research subagent and re-verified against source before writing. Every `file::symbol` above was confirmed to resolve as described (incl. the empty `SeedSequence`/`spawn` grep) on 2026-08-02.*

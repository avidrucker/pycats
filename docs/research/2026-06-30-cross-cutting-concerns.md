# Cross-cutting concerns — catalog (#281)

> A read-only inventory of pycats' **cross-cutting concerns** (CCCs) — aspects that span
> many modules rather than living in one place. **Catalog only**: each entry records *what
> it is, where it's scattered, how it's handled today, and the coupling it causes.* It does
> **not** propose or rank refactors — selecting which to act on is a **separate follow-up
> ticket** (per #281). Date: 2026-06-30. Agent: DRAGONFRUIT. `area:docs`.
>
> **Builds on, doesn't restate,** the architecture reviews
> ([`architecture-review-2026-06b.md`](./architecture-review-2026-06b.md) #252,
> [`architecture-review-2026-06.md`](./architecture-review-2026-06.md) #56): those score the
> codebase through DDD / Hexagonal / BDD lenses; this re-cuts the same evidence (plus new
> sweeps) through a **cross-cutting** lens and adds concerns those reviews didn't frame as
> CCCs. Terms link to the [glossary](../glossary.md) / [`CONTEXT.md`](../../CONTEXT.md) per
> the #278 convention — not re-defined here.

## Summary

| # | Concern | Spread (evidence) | Already tracked? |
|---|---|---|---|
| C1 | Determinism / headless contract | ~58 files reference it | ✅ documented (`CONTEXT.md`); review H4 nit |
| C2 | Sim state×time — timer/flag proliferation + scattered ticking | ~60 timer/flag fields on `Fighter`, ~25 tick sites in `player.update` | ✅ review **N1/N2** + slice plan (#264/#270) |
| C3 | Stringly-typed FSM state labels | ~48 `state ==`/`in_state` sites; `LABELS` consumed by 4 modules | ⚠ **not** framed as a CCC yet |
| C4 | Golden / parity coupling | ~24 test files touch goldens/snapshots | ✅ review **S4**; `REGEN_PROTOCOL.md` |
| C5 | Unit scaling (`PX_PER_UNIT` ≈ 5.4) | ~23 files | ✅ **#195** (named-const), ADR-0003 |
| C6 | Tuning-data provenance | values+citations across config/characters/docs/issues | ✅ **ADR-0003 / #226 / #233**, review S5 |
| C7 | Present↔sim layering (ports & adapters) | rendering port half-built; `Tail`→adapter import | ✅ review **H1–H4**; decisions #9/#10 |
| C8 | Facing / mirroring | ~57 `facing_right` reads across 13 files | ⚠ **not** framed as a CCC yet |
| C9 | Input gating ("can this state act?") | ~11 gate sites across `player.update` + `fighter_input` | ⚠ **not** framed as a CCC yet |
| C10 | Diagnostics / logging + error handling | ~53 bare `print()`s (6 files), **0** logging, ~13 `raise`s | ⚠ **not** framed as a CCC yet |
| C11 | `config.py` constants god-module | ~142 constants, all domains in one file | ◐ partial (#233 touches provenance) |

The review→follow-up loop already owns the *structural* CCCs (C2, C4, C6, C7). The ones **not
yet framed as cross-cutting** (C3, C8, C9, C10, and C11's non-provenance half) are this
catalog's main new contribution.

---

## C1 — Determinism / headless contract
- **What:** the invariant that the rules core is pure, frame-timed, RNG-free, and display-free
  so the golden oracle reproduces byte-for-byte.
- **Where:** ~58 files reference `SDL_VIDEODRIVER`/determinism/no-RNG/wall-clock; codified in
  [`CONTEXT.md`](../../CONTEXT.md) "Determinism / headless contract"; enforced indirectly by
  the goldens (C4) and `conftest.py` autouse resets.
- **How handled:** convention + documentation + the golden suite catching violations after the
  fact. RNG appears only as an injected seeded seam (`sim/controllers.py`).
- **Coupling / pain:** every core change must preserve it; a stray `pygame.time`, ambient
  `random`, or pygame import in a "pure" module silently breaks reproducibility. Review **H4**
  notes the `CONTEXT.md` "`systems/` imports no pygame" wording is already slightly off
  (`systems/movement.py` imports `pygame` for `Vector2` — see C7).
- **Refs:** `CONTEXT.md`, review H4, C4 (goldens), C7 (the pygame-in-pure-modules leak).

## C2 — Sim state × time (timer/flag proliferation + scattered ticking)
- **What:** fighter behaviour is driven by a large bag of per-frame timers/flags, advanced by
  hand in the adapter rather than by the aggregate that owns them.
- **Where:** ~60 timer/flag fields on `Fighter` (`*_timer`, `invulnerable`, `*_attempting`,
  `air_dodge_active`, `wavedash_armed`, `grabbed_ledge`, …); ~25 decrement/check sites in
  `entities/player.py::update`.
- **How handled:** `player.update()` ticks each timer and toggles flags; the statechart guards
  read them. Documented as review findings **N1** (`Fighter`↔`Player` bidirectional `owner`
  back-ref) and **N2** (`player.update()` ticks domain timers).
- **Coupling / pain:** state×time is entangled — adding one fighter state (e.g. ledge-hang,
  #14) touches `Fighter` fields **+** `player.update` tick logic **+** the chart **+** `LABELS`
  (C3) **+** input gating (C9). Per-frame domain behaviour lives in the adapter.
- **Refs:** review **N1/N2** + the **F1+F2 slice plan** (review appendix, #264 / scoping #270).
  This catalog does **not** re-plan it — that work is already scoped.

## C3 — Stringly-typed FSM state labels
- **What:** fighter (and screen) states are bare strings duplicated across the chart, the label
  registry, the adapter's gating logic, and every consumer — with no single enum/constant.
- **Where:** ~48 `self.state ==` / `in_state("…")` / `state not in (…)` sites; the flat
  `LABELS` tuple in `systems/state_engine_sc.py` is consumed by `charts/fighter_chart.py`,
  `systems/match_engine.py`, `systems/screen_engine.py`. A label string (e.g. `"ledge_hang"`)
  is repeated as the chart leaf `id`, a `LABELS` entry, `player.update` exclusion-tuple members,
  and render/stats switches.
- **How handled:** convention — "leaf id == flat label"; `LABELS` is the canonical list;
  reviewers keep them in sync by hand.
- **Coupling / pain:** adding or renaming a state requires **synchronized edits in ≥4 places**
  (chart leaf, `LABELS`, the `player.update` action-gate exclusion list, and any consumer that
  switches on the label) with no compiler/test forcing them together — a missed site fails
  silently or at runtime. (Observed first-hand adding `ledge_hang` in #14.)
- **Refs:** `systems/state_engine_sc.py` `LABELS`; `charts/fighter_chart.py`. **Not** previously
  cataloged as a CCC.

## C4 — Golden / parity coupling
- **What:** behaviour is pinned by recorded per-frame goldens, so any sim-affecting change
  ripples into the golden baselines.
- **Where:** ~24 test files touch goldens/snapshots/summaries; `tests/golden/*` (+ `*.summary.json`),
  `tests/golden_util.py`, `tests/golden/REGEN_PROTOCOL.md`.
- **How handled:** segmented goldens + reviewable summary digests + the `REGEN_PROTOCOL`
  reviewer checklist (review **S4**, "de-risked"). Parity is now statechart-vs-frozen-golden.
- **Coupling / pain:** a feature touching the sim cascades into a reviewed golden regen — e.g.
  ledge-hang (#14) changed three goldens (fighters now survive launches by grabbing edges). The
  coupling is *intended* (it's the oracle) but it means "small" sim changes have a docs-review
  tail, and the snapshot **tuple layout** is positionally depended on in a few tests (review
  **B-b**).
- **Refs:** review S4 / B-b; `REGEN_PROTOCOL.md`; C1 (determinism is what makes it work).

## C5 — Unit scaling (`PX_PER_UNIT` ≈ 5.4)
- **What:** PM spatial units are mapped to pixels by a single ~5.4 factor that is a magic number
  in comments, not a named constant.
- **Where:** ~23 files mention `PX_PER_UNIT` / `5.4` / `× 5.4` (chiefly `characters/*.py`
  radius/position derivations, `combat/data.py`, docs).
- **How handled:** by convention — combat numbers entered raw, spatial values hand-multiplied by
  ~5.4 with an inline comment (`pm-reference/00-overview.md` unit convention).
- **Coupling / pain:** the scale lives in scattered comments/derivations rather than one named
  constant, so it can't be referenced, changed, or machine-checked in one place; intertwined
  with provenance (C6).
- **Refs:** **#195** (promote to a named constant), ADR-0003 derivation-guard (C6).

## C6 — Tuning-data provenance
- **What:** authored numeric values and *why they are what they are* (their cited source) are
  spread across five places with nothing enforcing value↔source agreement.
- **Where:** `config.py` comments, `characters/*.py` docstrings, `GUESSED_VALUES_TO_RESEARCH.md`,
  `docs/research/*`, and issue comments; ~20 `⚠`/GUESS markers across ~7 files (review **S5**).
- **How handled:** **governed but not yet enforced** — ADR-0003 (Proposed) specifies a sidecar
  provenance registry + a drift-guard; not built.
- **Coupling / pain:** a value can silently drift from its citation; the same value's rationale
  appears in multiple docs. (This is the concern ADR-0003 / #226 spun out.)
- **Refs:** **ADR-0003**, **#226** (spike), **#233** (refactor, `blocked`), review S5.

## C7 — Present ↔ sim layering (ports & adapters)
- **What:** the boundary between the pure sim core and the pygame present layer (render / input /
  geometry value types) is mostly clean but leaks in specific, known spots.
- **Where:** rendering port half-built — `Attack`/`Platform`/`Tail` still own `Surface`/`image.fill`/
  self-draw (review **H1**); `entities/tail.py` imports the **adapter** (`from ..render_battle
  import tinted`) — a layering inversion (review **H2**); `core/input.py` binds the pure
  `InputFrame` port to the `poll()` pygame adapter in one module (review **H3**); `Vector2`/`Rect`
  value types `import pygame` in `physics`/`movement`/`fighter` (review **H4**, decision #10).
- **How handled:** the #69 decomposition extracted `Player` rendering into `render_battle`; the
  rest is tracked as open Hexagonal follow-ups + two architect decisions (#9 input split, #10
  `pygame.math`).
- **Coupling / pain:** presentation concerns reach into entity classes; the `Tail`→render import
  points the dependency the wrong way; pygame transitively loads into otherwise-pure consumers.
- **Refs:** review **H1–H4**, decisions **#9 / #10**.

## C8 — Facing / mirroring
- **What:** all entity geometry is authored facing-right-relative, and **every** spatial consumer
  must mirror it for a left-facing fighter.
- **Where:** ~57 `facing_right` reads across ~13 files — `combat/geometry.py`, `combat/data.py`
  (Circle offsets), `entities/attack.py`, `entities/tail.py`, `render_battle.py`,
  `entities/fighter*.py`, `systems/movement.py`.
- **How handled:** convention — "offsets are facing-RIGHT-relative; consumers mirror for left"
  (stated in `combat/data.py` docstrings); each consumer applies the flip itself.
- **Coupling / pain:** the mirroring rule is replicated at every consumer rather than centralized;
  a consumer that forgets to mirror produces a left/right-asymmetric bug that goldens only catch
  if the scenario exercises a left-facing fighter. No single "to world coords" helper owns it.
- **Refs:** `combat/data.py` (facing-relative convention). **Not** previously cataloged as a CCC.

## C9 — Input gating ("can this state act?")
- **What:** which states may read movement/attack input is decided by scattered ad-hoc guards
  rather than a single state→capability table.
- **Where:** ~11 gate sites — `player.update`'s action-gate exclusion tuple (`state not in
  ("dodge","hurt","stun","prone","getup_roll","getup_attack","ledge_hang")`) plus
  `in_hitstun`/`in_shieldstun`/`in_landing_lag`/`grabbed_ledge` flag checks, and further gating
  in `entities/fighter_input.py`.
- **How handled:** each new locked state appends itself to the exclusion tuple and/or adds a flag
  check; the gate logic is duplicated between `player.update` and `fighter_input`.
- **Coupling / pain:** "is this state actionable?" has no single source — adding a non-actionable
  state means remembering to extend a growing string tuple in multiple places (done for
  `ledge_hang` in #14); easy to miss one and let a locked fighter act. Closely tied to C2/C3.
- **Refs:** `entities/player.py::update`, `entities/fighter_input.py`. **Not** previously cataloged.

## C10 — Diagnostics / logging + error handling
- **What:** no consistent diagnostics or error-handling strategy — ad-hoc `print()` for debug,
  bare `raise` for validation, no log levels or toggles.
- **Where:** ~53 `print()` calls across 6 modules (`entities/player.py`, `entities/fighter.py`,
  `entities/fighter_input.py`, `game.py`, `text_utils.py`, and the legitimate `stats_print.py`);
  **no** `logging` import anywhere; ~13 `raise` sites (a mix of real invariant enforcement — C2's
  value-object validation — and ad-hoc errors).
- **How handled:** prints are mostly commented-out debug left in domain code; `stats_print.py` is
  intentional CLI output; validation raises are deliberate (review S3). No framework.
- **Coupling / pain:** debug prints sit inside the deterministic core (mixing presentation/IO into
  pure modules, brushing C1); no way to enable/disable diagnostics by level or area; no separation
  of "intended output" (`stats_print`) from "leftover debug".
- **Refs:** the 6 print-bearing modules; review S3 (the validation-raise half is healthy).
  **Not** previously cataloged.

## C11 — `config.py` constants god-module
- **What:** one module holds ~142 constants spanning unrelated domains.
- **Where:** `pycats/config.py` — physics/combat tuning, render/UI sizes, colours, cat-feature
  geometry, tail physics, menu/screen layout, blast zones — all intermixed (#-section comments
  only).
- **How handled:** section comments group constants; everything imports from the one module.
- **Coupling / pain:** sim-critical tuning (C5/C6) is interleaved with pure-presentation constants
  (colours, menu sizes); no boundary between golden-affecting and render-only values; the
  provenance concern (C6) has to carve its in-scope subset out of this grab-bag by hand.
- **Refs:** `config.py`; C5 (unit scaling), C6 (provenance — ADR-0003 must curate the tuning
  subset out of this file). Only the provenance half is tracked.

---

## Notes for the (deferred) action-selection ticket
- **Already scoped — don't re-spike:** C2 (slice plan in the review appendix, #264/#270), C6
  (ADR-0003 / #226 / #233), C7 (H1–H4 + decisions #9/#10), C4/B-b, C5 (#195).
- **Newly surfaced here — candidates for their own scoping:** C3 (state-label enum/registry),
  C8 (a single facing→world-coords helper), C9 (a state→capability table), C10 (a diagnostics
  policy), C11's render-vs-sim constant split.
- Several concerns **interlock**: C2+C3+C9 are three faces of "adding a fighter state touches too
  many places"; C5+C6+C11 are three faces of "tuning data + its home"; C1+C4+C7 are the
  determinism/oracle/layering triad. The action ticket should weigh them in those clusters.

**Out of scope (per #281):** deciding or doing any refactor. No code changed by this catalog.

# Birky Final Cutter — phase-model decision rationale + canon prior-art

> **Role:** WRITER · `area:combat` · **Closes #1080** · **Date:** 2026-08-02 · **Agent:** CHERRY
> **Records:** the rationale + primary sourcing behind the **#1066** ruling (phase model **C**).
> **Sibling of:** `docs/research/2026-08-01-birky-up-b-full-gap-findings.md` (the #1062 gap + A/B/C
> option space this decision descends from) and `docs/research/2026-07-31-birky-final-cutter-sourcing.md`
> (the PM 3.6 datamine).
> **Feeds:** the implementation tickets **#973** (plunge velocity flip) and **#974** (landing shockwave
> spawn); **#566** stays the archetype tracker.

## Purpose

The #1066 ARC/decision ticket ratified how Birky's full three-phase up-B (Kirby's Final Cutter:
rising slash → descending plunge + spike → landing shockwave beam) is modeled. The ruling rests on a
four-angle research pass whose analysis lived only in the session transcript. This doc persists that
analysis so the reasoning — especially the primary canon sourcing — survives past the session.

## The ruling (as ratified on #1066)

| Q | Decision |
|---|---|
| **Q1 — phase model** | **C, converged hybrid** — reuse the existing `helpless` / `landing_lag` chart states; at most **one** coarse named `up_special` state (deferred until a roster special needs distinct gating); per-frame behavior (velocity flip, spike windows) stays `MoveData` + `MoveClock`; shockwave via a touchdown hook. |
| **Q2 — triggers** | **Mixed** — rise→plunge velocity flip on a fixed integer `MoveClock.move_frame` threshold; plunge→landing shockwave on a **touchdown event** at `Fighter._handle_landing`. Apex-velocity detection ruled out. |
| **Q3 — exit** | Touchdown → spawn shockwave → **`landing_lag`** (datamined **35 f**) → **`idle`**; `helpless` reserved for the off-stage no-land case (special-fall). |
| **Q4 — tracking** | **#566 stays the tracker**, no new umbrella; scope folded into **#973** + **#974**; generalization to Nalio SJP (#956) / Narz recorded as a constraint on those tickets. |

## Why C, and why not A or pure-B

Four research angles (internal blast-radius, external canon engines, software-design, parity/determinism)
converged on the same shape once the A/B/C framing was stripped down.

### A (a 5-leaf nested statechart region) — rejected

- **Over-models a globally-shared structure.** `build_fighter_chart` (`pycats/charts/fighter_chart.py`)
  is shared by every fighter; the chart's states are cross-cutting *modes* (`idle`, `attacking`,
  `helpless`, `landing_lag`, …), not per-move choreography. Adding five Birky-Final-Cutter-specific
  leaves puts move-instance sequencing into the one structure every character constructs.
- **No mechanical payoff.** The fighter chart is **pure-guard** — it imports only `on/parallel/state/
  statechart/transition` and has no `on_enter` actions (unlike the screen engine). A chart leaf
  therefore *cannot itself* flip velocity or spawn a projectile; those live in imperative hooks no
  matter how many states exist. So A pays the full statechart cost **and still needs** the #973/#974
  hooks.
- **Highest golden blast radius.** New leaves require new `LABELS` entries or a second collapse in
  `StatechartEngine.state` (`pycats/systems/state_engine_sc.py`), which `raise`s on an unknown leaf —
  any wiring gap throws on every up-B frame. It also generalizes *poorly*: Narz would need its own
  sub-region, the opposite of reuse.
- **Canon doesn't require deep nesting.** The reference engines model the phases as **peer** states,
  not a deep sub-region (see prior-art below).

### Pure-B (a frame-count-only data timeline) — rejected

- **Cannot faithfully model the landing phase.** In canon the plunge→landing transition is
  **touchdown-triggered**, not frame-count-triggered (see prior-art). A fixed frame count desyncs the
  shockwave whenever the plunge-to-floor distance varies (off a ledge, on a taller stage).
- **The literal "imperative branches across three files" form is an anti-pattern.** Hand-written
  `if move_frame >= plunge_frame` smeared across `fighter_input.py` / `player.py` / `fighter.py`
  re-implements an ad-hoc state machine and leaks the phase decision across modules. (Its *data-driven*
  form — new `MoveData` fields applied at the existing `MoveClock` → `_spawn_move_hitbox` seam — is
  fine, and is exactly what C keeps.)

### C (converged hybrid) — chosen

- **Lowest blast radius that still satisfies canon.** Reuses `helpless` (airborne descent) and
  `landing_lag` (ground shockwave + end-lag) — both already in `LABELS`, already routed, already
  input-locking, already tested. Per-frame behavior stays data on `MoveData`, applied at the single
  existing consumption seam. The plunge is a later `MoveClock` window; the flip is a physics
  side-effect — the "one move = one startup/active/recovery envelope" invariant holds.
- **Matches the existing grain.** pycats already separates "which action mode am I in" (the chart)
  from "where am I in this move" (`MoveClock`, whose docstring calls itself the SSOT for exactly that)
  from "what happens this frame" (`Player._spawn_move_hitbox`, data-driven). C extends those seams
  rather than cutting across them.
- **Generalizes.** It extends the same data-only recovery seam (`grants_recovery` / `recovery_vy` /
  `recovery_vx`) that already carries Nalio's Super Jump Punch (#956) and Birky's phase-1 with **zero
  per-cat Python**, so Narz's future recovery special inherits "multi-phase recovery" for free.

## Triggers and determinism (Q2)

- **Velocity flip = integer `move_frame` threshold.** A `MoveClock.move_frame` guard is a pure function
  of the integer clock (which advances one tick per `Player.update` and freezes in lockstep with
  physics during hitlag), so it is golden-deterministic and immune to velocity perturbation.
- **Apex-velocity detection ruled out.** Firing the plunge when `vy` crosses 0 couples the phase
  boundary to the *entire* `vy` history, not the move clock. Anything that writes velocity — knockback
  on being hit mid-rise, a platform collision, `max_fall_speed` clamping — would fire the detector on
  the wrong trajectory. That is a correctness bug and a golden fragility, independent of float
  precision.
- **Landing shockwave = touchdown event.** Canon-required (below); fired at `Fighter._handle_landing`,
  not a frame count.

### The pycats-arc caveat (author to ~f37, not datamined f19)

The datamine (`SpecialAirHi2`) puts the source's per-frame root-motion apex at f18 and the plunge at
f19. **pycats models the rise differently** — a single upward burst (`recovery_vy = -15.7`) plus
gravity, a parabola whose apex is at `recovery_vy / g ≈ 15.7 / 0.42 ≈ frame 37`. So the datamined
absolute plunge frame (f19) fires *mid-rise* against the pycats trajectory. The plunge-flip frame must
therefore be a **labeled pycats modeling choice pinned to the ~f37 burst apex** (⚠ playtest starting
point, ADR-0003 class — the same status `recovery_vy` already carries), not the raw datamined f19.

## Exit sequence (Q3)

Plunge touchdown → spawn shockwave → `landing_lag` (timer = datamined **35 f**, `SpecialAirHi4`, a
FOUND value) → `idle`. `helpless` is reserved for the plunge carrying Birky off-stage without landing
(canon special-fall). Both target states already exist; `_handle_landing` already arms a landing-lag
timer (built for waveland #202) and clears `recovery_active` — the reuse seam. The phase-1-only build
routes straight to `helpless` on landing because its 20-frame move ends near apex while airborne; the
full move must instead stay live through the plunge and route touchdown → `landing_lag`.

### Shared implementation note — the "pending up-B landing" flag

By touchdown the move has typically ended (`current_move is None`, already routed to `helpless`), and
`_handle_landing` clears `recovery_active` before the chart ticks. So the phase-3 spawn must key off a
small flag set when the up-B starts and consumed in `_handle_landing`, **not** off `current_move`.
This applies to #974 regardless of the chart-state question.

## Canonical prior-art (primary sources)

The load-bearing parity finding — **the landing phase is event-driven (touchdown), not a frame count** —
comes from reading the reference engines directly, not from reasoning.

### Melee decompilation (doldecomp/melee) — the canon authority

Kirby's Final Cutter is **four action-states per air/ground family** (`SpecialHi1/2/3/4`,
`SpecialAirHi1..4`) in `src/melee/ft/chara/ftKirby/ftkirbyspecialhi.c` / `.h`, each with the standard
Melee per-action-state callback bundle (`_Anim`, `_IASA`, `_Phys`, `_Coll`). Transitions split cleanly:

- **Time-driven (animation end):** `ftKb_SpecialHi1_Anim` → `if (!ftAnim_IsFramesRemaining(...))
  Fighter_ChangeMotionState(..., SpecialAirHi2, ...)`. The rise→apex→descent progression is
  "when this phase's animation runs out, enter the next."
- **Event-driven (ground contact = the landing shockwave phase):** `ftKb_SpecialHi2_Coll` and
  `ftKb_SpecialHi3_Coll` both do `if (ft_CheckGroundAndLedge(...)) { Fighter_ChangeMotionState(...,
  SpecialAirHi4, ...); self_vel = 0; gr_vel = 0; }`. The plunge→landing transition is a **collision
  callback that zeroes velocity on touchdown**, not a frame counter. `SpecialHi3_Anim` is an empty
  `{}` — that phase's identity is the *state* (falling `_Phys` + land-detecting `_Coll`), not a script
  step.

So canon uses a **graph of peer action-states** with a **mix** of timer and collision transitions —
which is why pure-B (a data timeline) cannot model the landing faithfully, and why "distinct named
phases" (the C part) matches.

### meleelight — independent Melee reimplementation (corroboration)

Local clone at `~/Documents/Study/JavaScript/meleelight`. No Kirby, but Fox's Firefox and Falcon's
Raptor Boost are the same multi-phase-special shape and confirm the model in an independent codebase:
each phase is a separate action-state object (`UPSPECIAL.js` → `UPSPECIALCHARGE.js` →
`UPSPECIALLAUNCH.js` → `FIREFOXBOUNCE.js`) with explicit `NextState.init(...)` transitions fired by
time (`interrupt` when `timer > 42`), **touchdown** (`UPSPECIALLAUNCH.land` branches to
`FIREFOXBOUNCE.init`), and hit (`onPlayerHit`). Within a state, behavior is flat frame-threshold /
data-array hooks — mirroring the C split (named states outside, per-frame data inside).

### brawllib_rs PM 3.6 datamine (phase *data*)

Recorded in `docs/research/2026-07-31-birky-final-cutter-sourcing.md`: PM 3.6 Kirby's air Final Cutter
is four subactions — `SpecialAirHi` (23 f startup), `SpecialAirHi2` (36 f rise + slash + descent),
`SpecialAirHi3` (6 f stationary shockwave hitbox), `SpecialAirHi4` (35 f landing lag). This corroborates
the decomp's four-phase split at the PM-3.6 data layer and sources the 35 f landing lag. The subaction
model exposes per-move hitbox/velocity *events* only; it is silent on the action-state graph — that
graph is what the decomp/meleelight supply.

### Source-tier labels

- Melee decomp `ftkirbyspecialhi.c`: **primary** (authoritative engine model). Melee→PM is
  **[inference]**, strengthened by the PM 3.6 datamine showing the identical four-subaction split.
- meleelight: **primary reimplementation** (Melee); independent corroboration. Has known bugs — read,
  don't assume perfect.
- brawllib PM datamine (via the sourcing doc): **primary** for PM 3.6 phase *data*; silent on the
  action-state graph.
- The "distinct states + touchdown transition" conclusion is **read directly from source**. The pycats
  A/B/C → C mapping is a design **[inference/recommendation]** on that read plus the current
  `fighter_chart.py` structure.

## Key landmarks

- `pycats/charts/fighter_chart.py` — `build_fighter_chart`: the `attacking` startup/active/recovery
  region with `_mf_gt` frame-threshold guards; the `recovery_active → helpless` exits; `helpless`,
  `landing_lag` leaves.
- `pycats/systems/state_engine_sc.py` — `StatechartEngine.state` / `LABELS` (collapses `attacking` →
  `"attack"`; raises on an unknown leaf).
- `pycats/combat/move_clock.py` — `MoveClock` (per-move sequencing SSOT), `MoveTick`, `_compute_windows`
  (#204 / #951).
- `pycats/combat/data.py` — frozen `MoveData` (the defaulted golden-safe field ledger;
  `grants_recovery` / `recovery_v*`).
- `pycats/entities/fighter_input.py` — `handle_actions`: the start-of-move `grants_recovery` velocity
  SET (the flip mirrors it mid-move).
- `pycats/entities/fighter.py` — `_handle_landing` (touchdown seam; clears `recovery_active`, arms the
  landing-lag timer — the #974 reuse seam).
- `pycats/entities/player.py` — `Player.update` phase order; `_spawn_move_hitbox` (`Projectile` / `Attack`
  spawn, #223 / #951).
- `pycats/characters/birky_cat.py` `_BIRKY_FINAL_CUTTER` / `pycats/characters/nalio_cat.py`
  `_SUPER_JUMP_PUNCH` — both ride the recovery hook as data only.

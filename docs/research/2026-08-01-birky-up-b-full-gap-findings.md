# Birky up-B (Kirby Final Cutter) — full-implementation gap + phase-model option space

> **Role:** RESEARCH · `area:combat` · **Closes #1062** · **Date:** 2026-08-01 · **Agent:** CHERRY
> **Feeds:** a follow-on **ARC/decision** ticket (the model choice below is *not* made here).
> **Primary sources:** the pycats source at HEAD (`birky_cat.py`, `combat/data.py`,
> `entities/fighter_input.py`, `entities/fighter.py`, `entities/player.py`, `combat/move_clock.py`,
> `charts/fighter_chart.py`, `systems/state_engine_sc.py`), the datamine sourcing doc
> `docs/research/2026-07-31-birky-final-cutter-sourcing.md`, and the already-open engine tickets
> #973 / #974. Related: #969 (shipped phase 1), #578 (recovery hook), #566 (archetype tracker),
> Nalio SJP #956 (the other recovery special).

## TL;DR

Final Cutter is a **three-phase** move; #969 shipped **phase 1 only** (rising slash + a single
upward recovery burst). The remaining gap is **two new engine capabilities that are already
ticketed** — a mid-move velocity flip (#973) and a landing-triggered projectile spawn (#974) —
**plus one un-ticketed cross-cutting decision**: how the phases are *sequenced*, and where
`helpless` / landing-lag sits, and whether that sequencing lives in the **statechart** (option A),
in a **flat extension** of the recovery hook + `MoveClock` frame windows (option B), or a **hybrid**
(option C). The move's *parameters* are already data (`MoveData`, serialized to `birky.json`); every
missing piece is *sequencing/behavior* engine code. This doc enumerates the full gap and lays out
A/B/C with tradeoffs — **no recommendation**.

## 1. What ships today (#969, CLOSED)

`_BIRKY_FINAL_CUTTER` (`characters/birky_cat.py`) is wired into `moves["up_b"]` as **data only**,
riding the #578 recovery hook:

- **Rising slash** — 4 hitboxes, active f3–4, all one set (`first-box-wins`, #130) → one 8% hit.
- **Upward burst** — `grants_recovery=True`, `recovery_vy=-15.7`, `recovery_vx=0.0`. On a
  `grants_recovery` move, `fighter_input.py` **SETs** `vel.y = recovery_vy` and
  `vel.x = recovery_vx * facing` **once, at move start**, and arms `fighter.recovery_active`.
- **Exit** — the `attacking` sub-region in `fighter_chart.py` routes a recovery move's airborne exit
  to `helpless` (not `fall`); `recovery_active` is cleared on landing (`fighter.py`), and `helpless`
  recovers to `idle` on touchdown.

So today the whole move is: one slash window, one upward velocity set, then **natural gravity** until
landing → `helpless` → `idle`. This is the **rise-only** scope Avi ratified 2026-07-31.

Serialization is proven: `characters/data/birky.json` carries `"grants_recovery": true`,
`"recovery_vy": -15.7` — recovery parameters already round-trip as data through the frozen
`MoveData` dataclass.

## 2. Complete remaining-gap enumeration

### 2.1 Phase 2 — descending plunge + spike (#973, OPEN)

Canon: at/after the rise apex, Final Cutter **flips to a fast downward plunge** carrying a spike
hitbox. Two sub-gaps:

- **Velocity flip (engine).** The recovery hook sets velocity **exactly once, at move start**
  (`fighter_input.py`). There is no mechanism to **re-set** velocity mid-move, nor any apex/frame
  trigger to fire one. This is the substance of #973.
- **Spike hitbox (mostly data).** A downward-angled hitbox active only during the descent window
  is expressible today: `MoveClock` already honours per-hitbox `active_start`/`active_end`
  windows (`combat/move_clock.py`), and the datamine puts the plunge boxes at f19–36. So the
  *hitbox* is authorable as data **once the move's frame count is extended past the current f3–4
  slash + short recovery** — but it is inert without the velocity flip that defines the phase.

### 2.2 Phase 3 — landing shockwave beam (#974, OPEN)

Canon: on touchdown from the plunge, a **shockwave projectile** travels along the ground.

- **The projectile primitive exists.** `class Projectile(Attack)` (`entities/attack.py`) +
  `MoveData.projectile_speed` / `projectile_lifetime` (`combat/data.py`), spawned in `player.py`
  when `projectile_speed is not None`. So this is **not** a projectile-system-from-scratch.
- **The gap is the *trigger*.** Today a projectile spawns on the move's **mid-move active hitbox
  frame** (`player.py`, the #223 path). The shockwave must instead spawn **on landing** — a
  **touchdown-triggered spawn hook** that does not exist. This is the substance of #974.

### 2.3 Un-ticketed cross-cutting gaps (the reason #1062 exists)

Beyond the two engine hooks, full Final Cutter needs decisions that #973/#974 do not individually
own:

- **Phase-transition trigger model.** Rise→plunge and plunge→landing must be sequenced. Canon is a
  **single input** with automatic progression, so the triggers are **frame-timed or state-driven**,
  not input-driven. Which one (fixed frame counts from the datamine `SpecialAirHi2`, an
  apex-velocity detector, or a chart state) is open.
- **`helpless` / landing-lag entry timing.** The datamine shows a separate `SpecialAirHi4` (35 f
  **landing lag**) after the shockwave. Today the move routes to `helpless` directly on landing;
  with a plunge + a ground shockwave + landing lag, the exit sequence
  (`plunge → land → spawn shockwave → landing-lag → idle/helpless`) must be defined. `landing_lag`
  already exists as a chart state (used by waveland #202) and is a candidate reuse.
- **System interactions to hold invariant.** `MoveClock` window math (`startup+active+recovery`
  == move duration), `first-box-wins` (#130), ledge-grab-during-recovery, and the fast-fall /
  action lockout during `helpless` must all still behave. A longer, phase-changing up-B stresses the
  `MoveClock` "one move = one startup/active/recovery envelope" assumption.
- **Determinism.** The sim is golden-tested and must stay deterministic; any apex-detection or
  velocity-flip logic has to be a pure function of frame/state, not of floating-point wall-clock or
  render state.

## 3. Phase-model option space (no decision)

### Option A — model the up-B as a nested statechart region

Give Final Cutter its own sub-states inside `fighter_chart.py` /
`systems/state_engine_sc.py`: e.g. `rise → apex → plunge → land_shockwave → landing_lag`, mirroring
how `attacking` already splits into `startup/active/recovery` and how `helpless`/`landing_lag`/`prone`
are first-class states today.

- **For:** the engine already *is* a statechart; multi-phase sequencing is exactly what charts model;
  transitions become explicit and inspectable; `helpless`/`landing_lag` reuse is natural; new
  `LABELS` entries make the phase visible to the HUD/state-engine.
- **Against:** the chart is shared by **all** fighters and states — adding a Birky-specific region
  risks bloating a global structure for one move; every new leaf needs golden-safe guards; the
  `state_engine_sc.py` `LABELS` tuple and the flat-FSM parity both grow.

### Option B — flat extension of the recovery hook + `MoveClock` windows

Keep `recovery_active` + `MoveData` fields; add the two engine hooks (#973 velocity flip, #974
landing spawn) driven by **frame thresholds** read from `MoveClock` (`move_frame` vs authored
phase boundaries), plus new `MoveData` fields (e.g. a `plunge_vy` + a `plunge_start` frame, a
`landing_projectile` descriptor). No new chart states.

- **For:** smallest blast radius; stays inside the data-driven authoring model the whole roster uses;
  no global chart change; phase params are serialisable data (like `recovery_vy` already is).
- **Against:** sequencing logic becomes imperative `if move_frame >= X` branches scattered across
  `fighter_input.py` / `player.py` / `fighter.py` rather than one declarative place; the phase is not
  a named state (harder to test/inspect); risks re-implementing a mini state machine ad hoc.

### Option C — hybrid

The **chart owns entry/exit and the coarse states** (e.g. a single `up_special` state that replaces
the current `helpless` routing, plus reuse of `landing_lag`), while **flat per-frame hooks own the
fine behavior** (velocity flip at the authored frame, hitbox windows via `MoveClock`, landing spawn
on touchdown). Splits "where am I in the move" (chart) from "what happens this frame" (data + hooks).

- **For:** keeps the global chart change minimal (one state, not five) while still making the up-B a
  named, testable state; per-frame behavior stays data-authorable and reusable.
- **Against:** two homes for the move's logic (a boundary to get right); the least obviously-correct
  of the three without a worked example.

### Tradeoff summary

| Axis | A — nested statechart | B — flat hooks + windows | C — hybrid |
|---|---|---|---|
| Global chart change | large (≈5 states) | none | small (≈1 state) |
| Sequencing clarity | declarative, inspectable | imperative, scattered | split |
| Data-authorability | low (logic in chart) | high (params as data) | mixed |
| `helpless`/`landing_lag` reuse | natural | manual flag juggling | natural |
| Blast radius / golden risk | highest | lowest | medium |
| Reuse for other specials (§5) | strong if generalised | per-move fields | strong |

## 4. Data ↔ engine seam

- **Stays data** (frozen `MoveData`, serialised to `<cat>.json`): all hitbox scalars/geometry, frame
  counts, the existing `grants_recovery`/`recovery_vy`/`recovery_vx`, and any *new* phase parameters
  chosen (plunge velocity, phase-boundary frames, a landing-projectile descriptor). Precedent:
  `recovery_vy` already round-trips through `birky.json`.
- **Needs engine code** (not expressible as data today): the **mid-move velocity re-set** (#973),
  the **touchdown-triggered projectile spawn** (#974), and the **phase-sequencing/exit routing**
  (§2.3) — whichever of A/B/C is chosen. The ARC ticket's job is to fix this boundary so #973/#974
  are built against an agreed model.

## 5. Reuse / prior art

- **The recovery hook is already a shared seam.** Nalio's Super Jump Punch (#956) uses the identical
  `grants_recovery` / `recovery_vy` / `recovery_vx` fields (`nalio_cat.py`), so any phase-model
  extension should be evaluated for whether it generalises to **other** recovery specials, not just
  Birky. A statechart region or a set of `MoveData` phase fields both *could* generalise; an ad-hoc
  pile of Birky-specific branches would not.
- **Narz** (the third selectable archetype, #566) will need its own recovery special; a generalised
  phase model pays off across all three.
- The `Projectile` primitive (#223) and `landing_lag`/`helpless` chart states are existing building
  blocks the model should compose rather than duplicate.

## 6. Open questions for the ARC/decision ticket

1. Which phase model — **A / B / C** — and why (weigh §3 tradeoffs against the roster-wide reuse in
   §5)?
2. Phase-transition triggers: fixed datamined frame counts vs apex-velocity detection vs chart
   states?
3. Exit sequence: does the shockwave + landing lag route through the existing `landing_lag` state, and
   does the move end in `helpless` or recover directly?
4. Scope of the follow-on: build #973 + #974 under the chosen model, and does the model warrant a new
   umbrella or does #566 remain the tracker?

**This doc is option-space only.** The model is chosen in the follow-on ARC/decision ticket with the
human, per the research → decision split.

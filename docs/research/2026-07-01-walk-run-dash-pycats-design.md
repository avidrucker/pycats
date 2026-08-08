# Walk / dash / run — pycats parity design (digital input) (#374)

> ⚠️ **SUPERSEDED IN PART (2026-07-20, #801).** D2/D3 below ratified double-tap-dash
> **AND** mod-key-run as *complementary, both permanently on, with no flag*. That
> additive model is **superseded** by the #801 ruling (child of umbrella #799): the
> dash/run trigger is now **exactly one of {shift-mod, double-tap} at a time —
> mutually exclusive (XOR), mode-selected, never both**, with **shift-mod the default**
> and double-tap the opt-in alternate. The `dash_trigger_mode` selector lives in the
> **control/keybind layer** (an explicit sim input), not `runtime_settings`. The rest of
> this doc (the walk/dash/run *state* model, speeds, the `run`→`walk` rename, golden-safety
> reasoning) still stands. See #801 and `docs/research/2026-07-20-shift-mod-dash-run-findings.md`
> (#800). Implementers of #388 slice 4 must follow #801's XOR model, **not** D2's both-on.

> Design/architect ratification (#374, the design half of the movement-parity work;
> the PM facts are #373's `docs/research/2026-07-01-pm-walk-run-dash-mechanics.md`).
> Records the reporter-ratified scheme for adding PM's grounded-movement layer to a
> keyboard-driven pycats. **Design/spec only — implementation is the follow-up tracker
> (filed below).** Date: 2026-07-01. Agent: FIG. Ratified by: avidrucker (#374, pair-work).

## Decisions (ratified)

**D1 — Scope: build the BASIC layer; explore the advanced tech separately.**
This ticket's design covers **walk + dash + run + skid/turnaround**. The advanced
*analog-window* tech — **dash-dance, foxtrot, pivot** — is split to a research/spike
ticket (does a keyboard port even need it for "full PM parity"?), because it maps
poorly to digital input and is not a basic movement.

**D2 — Input scheme: double-tap-dash (B) + mod-key-run (C), with hold = walk.**
> ⚠️ **SUPERSEDED by #801 (2026-07-20):** the two triggers are NOT both-on/complementary.
> They are **mutually exclusive (XOR), mode-selected** (default shift-mod). The table below
> describes the *retired* additive scheme — read it as history, not the current design.

PM's walk↔dash split is analog stick magnitude, which a keyboard lacks, so the split is
invented as:

| Input | Result | Notes |
|-------|--------|-------|
| **Hold a direction** | **Walk** | = today's `MOVE_SPEED`; the *default* grounded move is unchanged → golden-safe |
| **Double-tap a direction** | **Dash** → **Run** | tap-burst (dash); keep holding → transitions to run after the dash window (the Smash-faithful dash→run) |
| **Mod-key + direction** | **Run** (direct) | the modifier route straight into sustained run, skipping the dash burst |

**D3 — Full basic parity, and it stays golden-safe *without* a flag.**
> ⚠️ **PARTLY SUPERSEDED by #801:** a `dash_trigger_mode` selector now DOES exist (the
> XOR mode-switch). Golden-safety is unchanged and still needs no *golden* flag — the sim
> emits neither trigger under either mode — but the "no flag at all" framing is retired.

The reporter wants walking + running + dashing (not a reduced/gated model). Because the
faster states are reached **only** through *new* inputs (double-tap / mod-key) that the
scripted goldens and the default controller never emit, plain-hold stays walk = today's
speed → `tests/golden/` byte-identical with **no** opt-in flag. Full parity and clean
goldens coexist here precisely because the new inputs are additive.

## Why dash ≠ run (the distinction this design honours)

From #373: **dash** is the agile tap-burst state (dash-dance/foxtrot/turnaround-able,
its own "initial dash velocity"); **run** is the committed sustained state entered by
holding past the dash window (must skid/pivot to reverse, its own "run max velocity").
The natural chain is **tap → dash → (hold) → run**. So dash and run are distinct *states*
with distinct speeds and turn rules — the design adds both, not one "fast" speed.

## Target values (PM Mario reference, from #373)

| State | PM Mario (u/f) | × 5.4 → px/f | pycats scalar |
|-------|---------------:|-------------:|---------------|
| Walk | 1.1 | 5.9 | `MOVE_SPEED = 6` (exists — this *is* the walk) |
| Dash (initial) | 1.5 | 8.1 | new `dash_speed` |
| Run (max) | 1.55 | 8.4 | new `run_speed` |

Per-character values come from rukaidata when #117's archetypes are built; Mario is the
reference. Walk:dash ≈ 0.73.

## States & migration (the sharp edge)

pycats' current grounded-movement leaf is **named `run`** but moves at *walk* speed
(`vel.x != 0 and on_ground`). The migration must not silently keep a mislabelled state:

1. **Rename** the current `run` leaf → **`walk`** (it is the walk). Update
   `fighter_chart.py`, `_DODGEABLE_STATES` (controllers), and any `state == "run"`
   readers. This is a pure rename of an existing behaviour → goldens unaffected (the
   *label* changes, not the speed; verify the render-parity test, which is label-blind).
2. **Add** a new **`dash`** state (agile burst, `dash_speed`) and a new **`run`** state
   (committed, `run_speed`), plus **`skid`** (turnaround decel out of run).
3. **Speed scalars:** add per-fighter `dash_speed` / `run_speed` (default to Mario's
   8.1 / 8.4 px, i.e. `dash_speed`/`run_speed` fields on `FighterData` like `move_speed`).

## Ordered follow-up DEV slices (for the implementation tracker)

Sketch only — decompose for real when picked up (don't pre-file all children):

1. **Rename `run`→`walk`** (state-label migration; behaviour-preserving; goldens clean).
2. **Double-tap detection + `dash` state + `dash_speed`** (the burst; input edge-timing in `fighter_input`).
3. **Dash→run transition + `run` state + `run_speed`** (hold past the dash window).
4. **Mod-key → run** (the D2-C direct-run input).
5. **Skid/turnaround** (reverse-out-of-run decel).
6. **AI-controller awareness** (bots choose walk/dash/run; ties to #370's timer-gate lesson — read timers, not just labels).

## Golden-safety recap

Default hold = walk = `MOVE_SPEED` unchanged; the new states are reached only via new
inputs the goldens never emit → byte-identical, no flag. The one migration risk is the
`run`→`walk` **rename** touching label-readers (incl. the render-parity oracle, which is
label-blind for speed but renders state) — slice 1 verifies it.

## Non-goals

- **Dash-dance / foxtrot / pivot** — the advanced analog tech; its own research/spike (filed).
- Analog-stick support; air-speed / fast-fall (#229); wavedash (#202); per-character balance (#117).

## Cross-refs

Facts: #373 (`docs/research/2026-07-01-pm-walk-run-dash-mechanics.md`). Movement model:
`docs/pm-reference/movement-and-tech.md` (#147). Files the implementation will touch:
`pycats/charts/fighter_chart.py` (states), `pycats/entities/fighter_input.py`
(input scheme, `step_horizontal`), `pycats/systems/movement.py`, `pycats/config.py`
(`MOVE_SPEED`), `pycats/combat/data.py` (`FighterData` scalars), `pycats/sim/controllers.py`
(AI awareness + `_DODGEABLE_STATES`). Per-character scalars #126/#229. Orientation map #185.

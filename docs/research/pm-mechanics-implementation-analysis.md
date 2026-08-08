# Implementing PM core fighting mechanics with statecharts-py — analysis & roadmap

> Bridges research → implementation. Reads the three research/benchmark inputs
> and the current code, then proposes how to build the full Project-M core
> fighting model on statecharts-py, with a phased roadmap and the architectural
> decisions to make first.
>
> Inputs:
> - [brawl-projectm-fighter-states.md](./brawl-projectm-fighter-states.md) (states, shield rule, PSA event model)
> - [pm-framerate-fidelity.md](./pm-framerate-fidelity.md) (60 Hz fixed timestep, integer-frame data)
> - [BACKLOG.md](./BACKLOG.md) (open research threads a/b/c + collision algorithm)
> - statecharts benchmark [spec](../superpowers/specs/2026-06-21-statecharts-benchmark-design.md) / [plan](../superpowers/plans/2026-06-21-statecharts-benchmark.md) (the seam + parity harness + perf result)
> - Current model: `pycats/entities/player.py::_build_fsm`, `pycats/statecharts/fighter_chart.py`, `pycats/config.py`
> Date: 2026-06-21.

## 1. Where we stand

- A **swappable `StateEngine` seam** exists; the fighter action-FSM runs as either
  the hand-rolled FSM (`legacy`) or a flat statecharts-py chart (`statechart`),
  proven **byte-identical** over a real headless battle (incl. a full match to
  defeat). Performance is a non-issue: the statechart adds ~0.06% of the 60 Hz
  frame budget; the renderer (now tail/body-cached) has ~50× headroom.
- So the question is **not "can statecharts-py do this / is it fast enough"** — both
  are answered yes. The question is **how to structure the full PM model** on it,
  and **what we still need to research** before certain mechanics are faithful.

## 2. What "full PM core fighting mechanics" comprises

A working inventory (the core fighting model, excluding menus/CSS/items/stages):

1. **Moveset / attack system** — per-character moves: jab(s), tilts (f/u/d),
   smashes (f/u/d, chargeable), dash attack, aerials (n/f/b/u/d-air), specials
   (neutral/side/up/down-B), each with **frame data** (startup / active / recovery)
   and ground vs air variants.
2. **Hitbox / hurtbox system** — multiple hitboxes per move; per-hitbox damage,
   angle, base knockback, knockback growth; clank/trade/priority; **hitlag/freeze
   frames**; **stale-move negation**; shield-priority *geometry* (from the states
   doc: contact decided by geometry, not HP).
3. **Knockback & hitstun** — the real Brawl/PM knockback formula (not today's
   `base + scale·percent`); **hitstun as a function of knockback**; launch
   trajectory; **DI / SDI**; **tumble**, **knockdown/prone**, **getup**, **tech**.
4. **Shield (full)** — shieldstun `floor(damage × 0.345)`; **shield pushback**
   (defender + attacker); **shield poke** (geometry); **shield break → stun**;
   out-of-shield options (shield-grab, jump/up-B OOS); PM **powershield / parry**.
5. **Grabs & throws** — grab → grabbed/held; pummel; f/b/u/d throws; grab release;
   mash escape.
6. **Movement & tech** — dash vs run, dash-dance, pivot, crouch, fast-fall, short
   hop vs full hop, double-jump-cancel, **ledge mechanics** (grab/getup/roll/jump/
   drop + ledge intangibility), platform drop-through; PM signatures: **wavedash**
   (directional air-dodge into ground), **L-cancel**.
7. **Hitstun/KO states** — hurt, tumble, knockdown, getup, star/screen KO.

## 3. What pycats has today

From `_build_fsm` (10 labels) + `config.py`:

- States: `idle, run, jump, fall, shield, dodge, ko, hurt, stun` (unreachable),
  `attack`.
- **One generic attack** (12-frame, single hitbox, fixed 10 dmg, angle 0).
- **Knockback**: simplified `base_kb + kb_scale·percent` (NOT the PM formula).
- **Shield**: HP 50, linear deplete/regen 0.2/frame, shield state; shield-break →
  `stun` is *intended but unwired* (`stun` is unreachable — a preserved quirk).
- **Dodge**: spot / air / roll with intangibility; edge-aware.
- **Jumps**: double jump (`MAX_JUMPS = 2`); fast-fall not implemented.
- **Stocks** (3), blast-zone KO, respawn; percent tracked.

## 4. The gap (mechanic → status)

| PM mechanic | pycats today | Gap |
| --- | --- | --- |
| Multi-move moveset + frame data | one generic attack | **large** — needs move table + per-move startup/active/recovery |
| Multi-hitbox, per-hitbox data | single fixed hitbox | **large** |
| Hitlag / freeze frames | none | medium |
| Stale-move negation | none | small-medium |
| Real knockback formula | simplified | medium (formula known-ish) |
| Hitstun from knockback | fixed `HURT_TIME` | medium |
| DI / SDI | none | medium |
| Tumble / knockdown / getup / tech | none (`hurt` only) | medium-large |
| Shieldstun | none (stun unwired) | small (formula known) |
| Shield pushback | none | **blocked** — formula refuted (thread b) |
| Shield poke (geometry) | n/a (no real hitbox geo) | medium |
| Shield break → stun | unwired | small |
| OOS options | none | medium |
| Powershield / parry | none | **blocked** — PM-specific (thread c) |
| Grabs / throws / pummel | none | large |
| Dash-dance / pivot / crouch | run only | medium |
| Fast-fall / short hop / DJC | double jump only | small-medium |
| Ledge mechanics | none | large |
| Wavedash | none | **blocked-ish** — depends on PM air-dodge physics (thread c) |
| L-cancel | none | **blocked-ish** — PM-specific (thread c) |

## 5. Why statecharts-py fits PM's model

The states doc found PM/Brawl is **not** a numeric transition table — it's an
**event-based PSA system**: action → subaction → per-frame events, with hitboxes
spawned by hitbox-creation events on specific frames. statecharts-py maps onto
this far better than the current flat chart:

- **Hierarchy (nested states).** Group states so shared transitions live once at
  the parent: e.g. `grounded { stand{idle,walk,run,crouch}, shield, attack… }`
  vs `airborne { jump, fall, … }`, and `actionable` vs `hitstun`. "From any
  grounded actionable state you may shield/jump/grab/attack" becomes parent-level
  transitions instead of being repeated on every leaf (today they are repeated).
- **Parallel regions (orthogonal concerns).** A fighter has concurrent aspects
  that the current single-FSM cannot express cleanly: **action region** (what move)
  ∥ **shield region** (HP/regen/stun) ∥ **intangibility/armor region** ∥ **jump-
  count region**. Parallel regions model these independently and avoid the
  combinatorial state blowup.
- **Per-move sub-statecharts = PSA actions.** Each move is a small chart
  `startup → active → recovery`, where entry to `active` is the **hitbox-spawn
  event** (entry action) and transitions fire on frame thresholds. This is a
  direct analogue of action→subaction→hitbox-events.
- **Frame-driven transitions on the existing `"tick"`.** pycats is fixed-timestep
  (see fidelity doc); the established "one hop per `send('tick')`" pattern extends
  to hierarchical/parallel charts: each tick increments per-state frame counters
  and guards compare against integer frame-data thresholds.
- **Data-driven character data.** Keep frame data + hitbox data in **tables**
  (the "PSA data") separate from the chart **structure** (the "engine"). One
  generic move sub-chart parameterized by a move-data row → many moves without new
  chart code. This mirrors how Brawl separates engine from per-character scripts.

statecharts-py provides the needed primitives (confirmed available: `statechart`,
`state`, `parallel`, `transition`, `on`, `initial`, `final`, `history`, entry/exit
actions, datamodel, guards; `Session.in_state`/`send`/`configuration`).

## 6. Architectural decisions to make first

1. **Statechart becomes the primary engine; legacy FSM is frozen.** Once real PM
   mechanics land, the simple legacy FSM can no longer match — so **strict
   cross-backend byte-identical parity will end**. Decision needed:
   - Keep `legacy` as a frozen "classic mode" + benchmark baseline, and
   - Replace cross-backend parity with **statechart self-regression snapshots**
     (record golden per-frame snapshots of scripted scenarios; assert stability
     across refactors). The existing headless runner + snapshot harness is reused
     wholesale — only the oracle changes (vs-legacy → vs-golden).
2. **Move/hitbox data format.** Define a data schema (dataclasses or tables) for
   moves (startup/active/recovery, per-hitbox damage/angle/BKB/KBG, ground/air,
   shieldstun) — the single source character data reads from. This is the highest-
   leverage early artifact; everything else parameterizes off it.
3. **Hierarchy + parallel layout.** Commit to the region decomposition (action ∥
   shield ∥ intangibility ∥ jumps) before writing per-move charts, so shared
   transitions and timers have a home.
4. **Keep determinism + integer frames** (fidelity doc): no RNG; all timing in
   whole frames; one tick per frame.
5. **Geometry-based collision.** Shield contact and poke are decided by hit/hurt/
   shield **geometry** (states doc), so a real hitbox/hurtbox/shield-bubble
   overlap test must replace today's rect-only attack. This is a physics/collision
   workstream that runs alongside the statechart work.

## 7. Research gaps that gate specific mechanics

Resolve before implementing the gated mechanics (link back to [BACKLOG.md](./BACKLOG.md)):

- **Thread b — shield pushback formulas**: previously proposed formula **refuted**.
  → *Blocks faithful shield pushback.* Implement shieldstun/break first; defer
  pushback magnitudes, or ship an explicit placeholder flagged as non-faithful.
- **Thread c — PM/Project+ deviations + powershield/parry**: no PM-specific
  authoritative source found yet. → *Blocks powershield/parry, and informs
  wavedash/L-cancel and PM air-dodge physics.* Defer PM signatures until c lands.
- **Thread a — state-to-state transition graph**: none published; it lives in code.
  → *Not a blocker* — **our statechart *is* the transition graph.** We design it
  (informed by the action-ID list), rather than transcribing a published one.
- **Collision-resolution algorithm** (bonus thread): decomp only ~1% complete.
  → We implement our own resolution order; shield-priority geometry is the one
  firm rule we have.

**Net:** the well-established mechanics (moveset+frame data, multi-hitbox, real
knockback/hitstun, shieldstun, grabs, basic movement tech, ledges) are buildable
now; the **PM-signature/under-documented** ones (shield pushback magnitudes,
powershield/parry, wavedash, L-cancel) should wait on threads b/c.

## 8. Proposed phased roadmap

Each phase keeps the game runnable, adds tests, and re-runs the benchmark. Parity
flips from "vs legacy" to "vs golden snapshot" at Phase 0.

- **Phase 0 — Foundation (refactor, no new mechanics).** Make the chart
  hierarchical + parallel; introduce the move/hitbox **data schema** and a generic
  data-driven move sub-chart; switch the regression oracle to golden snapshots.
  Exit: current behavior reproduced, now data-driven.
- **Phase 1 — Combat core.** Real knockback formula; hitstun-from-knockback;
  multi-hitbox attacks with per-hitbox data; hitlag/freeze; ground/air attack
  split; shieldstun + shield-break→stun. (Uses only known formulas.)
- **Phase 2 — Moveset.** Tilts, chargeable smashes, dash attack, aerials, specials
  scaffold — all parameterized off the data tables; stale-move negation.
- **Phase 3 — Defense & hitstun states.** Tumble/knockdown/getup/tech; DI/SDI;
  OOS options; shield poke geometry. (Shield *pushback* deferred → thread b.)
- **Phase 4 — Grabs & throws.** Grab/grabbed/pummel/throws/release/mash-escape.
- **Phase 5 — Movement tech + PM signatures.** Dash-dance, pivot, crouch,
  fast-fall, short hop, DJC, full ledge mechanics; then (gated on thread c)
  wavedash, L-cancel, powershield/parry.

Cross-cutting throughout: golden-snapshot regression, per-phase benchmark, and a
geometry collision workstream feeding Phases 1–3.

## 9. Recommended next concrete step

Do **Phase 0** as a brainstorm → spec → plan (it has the highest leverage and the
one irreversible decision: the parity-oracle flip and the data schema). Before
writing that spec, run a focused **brainstorming** pass on two questions:
(1) the exact move/hitbox **data schema**, and (2) the **region decomposition**
(which orthogonal concerns become parallel statechart regions). Everything after
Phase 0 parameterizes off those two choices.

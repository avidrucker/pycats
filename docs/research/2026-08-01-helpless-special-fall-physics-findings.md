# Does the helpless / special-fall state (after up-B or air-dodge) alter fall speed or air physics? — findings

**Ticket:** #1061 (RESEARCH · `area:combat` / `combat:physics`) · **Date:** 2026-08-01 · **Agent:** APPLE
**Deliverable:** this doc. **No implementation** — any change is a downstream decision/DEV ticket, filed one at a time (research never produces a spec).
**Cluster:** sits beside #980 (up-B/helpless/midair-jump), #987 (hitstun↔helpless overlap), #988 (PM Tier-1 spike), #990 (decision queue). This one isolates the **movement physics** during helpless, which those did not.

---

## 1. TL;DR — the headline answer

**Fall speed: NO — helpless does not change it.** In both canon (Melee, Tier-2) and pycats, a fighter in special-fall/helpless descends under its **normal gravity toward its normal terminal fall speed** — the same numbers as an ordinary `fall`. No state-specific gravity, no altered cap.

**Air physics: YES — but only in pycats, and only on the horizontal axis.** pycats **removes directional air control (drift)** while helpless: `step_horizontal` is called with `locked=True` for the state, so left/right does nothing and only air friction bleeds off any existing horizontal velocity. **Canon does the opposite** — special-fall calls the *standard* `airDrift`, so you keep full aerial mobility; you simply can't *act* (jump/attack/air-dodge). So pycats' helpless is a **drift-less straight-down fall**, whereas canon's is a **normally-steerable fall you can't act out of**. That horizontal-control removal is the one genuine helpless-specific physics divergence.

**Fast-fall: not a helpless-specific question in pycats.** pycats models **no fast-fall anywhere** (single global fall speed — the #120/#261 gap), so it cannot represent fast-fall in helpless *or* in normal fall. (Aside: the Tier-2 source shows Melee special-fall *does* run the fast-fall path — see §3.3, flagged as counterintuitive and Tier-1-pending.)

---

## 2. The question, restated

> When a fighter finishes its Up+B (or air-dodges) and enters `helpless` / special-fall, does that state change fall speed or air physics — and if so, how exactly? Establish the PM 3.6 behavior, then compare to what pycats does.

Broken into the axes the ticket named: **fall speed / gravity · fast-fall · air drift / horizontal mobility · duration / exit · pycats delta per axis.**

**Evidence ladder** (inherited from #980/#987): **Tier-1** = actual Melee DOL / PM `.rel` disassembly — *not consulted here*; **Tier-2** = meleelight, a faithful Melee-engine reimplementation in JS; **Tier-3** = SmashWiki. **PM 3.6 runtime = inferred from Brawl/Melee inheritance** unless the open **#988** Tier-1 spike resolves it. Every canon claim below is labeled with its tier.

---

## 3. Canon — special-fall is action-locked, not physics-changed (Tier-2)

**Source:** meleelight (`~/Documents/Study/JavaScript/meleelight`). The special-fall action state is `FALLSPECIAL`.

### 3.1 The per-frame body runs the *standard* airborne physics

`src/characters/shared/moves/FALLSPECIAL.js` — `main`:

```js
main : function(p,input){
  player[p].timer++;
  if (!actionStates[characterSelections[p]].FALLSPECIAL.interrupt(p,input)){
    fastfall(p,input);   // gravity → terminalV, + optional down-flick fast-fall
    airDrift(p,input);   // full stick-driven aerial mobility
  }
}
```

There is **no gravity or fall-speed override** in `FALLSPECIAL`. It calls the same two shortcuts every airborne state uses. `interrupt` merely re-inits the state when its animation timer laps (special-fall **loops** — it persists until land / ledge / grab / hit), and `land` routes to `LANDINGFALLSPECIAL` (landing lag).

### 3.2 Air drift is full and identical to a normal fall (Tier-2)

`airDrift` (`src/physics/actionStateShortcuts.js:224`) reads the control stick `lsX`, accelerates by `airMobA·lsX + sign·airMobB` toward the `aerialHmaxV` cap, and decays with `airFriction` when the stick is neutral. It is the **shared** air-mobility function — special-fall gets the character's normal aerial DI/drift, unmodified. **A fighter in special-fall can steer horizontally exactly as in a normal fall.**

### 3.3 Fall speed = normal gravity → normal terminal; fast-fall path is present (Tier-2, counterintuitive → Tier-1-pending)

`fastfall` (`actionStateShortcuts.js:265`) applies `gravity` toward `terminalV` each frame, and on a fresh down-flick (`lsY < -0.65`) sets `cVel.y = -fastFallV`. Because `FALLSPECIAL.main` calls it, the Tier-2 model has special-fall descend under **normal gravity to normal terminal velocity, with fast-fall available.** The base fall speed being normal is well-attested; **fast-fall being available in special-fall is counterintuitive** (common lore says helpless disables fast-fall). Flagged as a **Tier-2-only** claim — fold into the #988 Tier-1 confirmation; it does not affect pycats today (no fast-fall mechanic exists).

### 3.4 What special-fall *does* change: actionability, not physics (Tier-2 / Tier-3)

The state's identity is the **action lock** — no jump, no double-jump, no attack, no air-dodge — plus `wallJumpAble:false` and front-only ledge grab (`canGrabLedge:[true,false]`). Exit is by **landing, grabbing a ledge, being grabbed, or being hit** (Tier-3 SmashWiki "Helpless"/"Special fall"; the hit-exit is the #987/#990 C1 thread). None of these are fall-speed/gravity effects.

**Canon conclusion:** special-fall alters *what you can do*, **not how you fall**. Gravity, terminal fall speed, and air drift are the fighter's normal airborne values.

---

## 4. pycats — normal gravity kept, but horizontal drift is removed

pycats implements helpless as a real statechart state (#184 air-dodge route, #578 up-B route), gated in `pycats/charts/fighter_chart.py` and `pycats/entities/fighter_input.py`.

### 4.1 Fall speed / gravity — MATCHES canon

`step_physics` (`pycats/entities/fighter_physics.py`) applies gravity through a single unconditional call — no branch on state:

```python
apply_gravity(p.fighter.vel, p.fighter.gravity, p.fighter.max_fall_speed)
```

The helpless statechart comment states the same intent: *"the fighter falls under normal gravity and only recovers on landing."* So helpless descends at the fighter's normal `gravity` (default `GRAVITY=0.5`) toward `max_fall_speed` (default `MAX_FALL_SPEED=13`) — identical to a normal `fall`. ✅ **No divergence on the vertical axis.**

### 4.2 Air drift / horizontal mobility — DIVERGES from canon

`handle_move` (`pycats/entities/fighter_input.py`) calls `step_horizontal` with `locked` true for helpless:

```python
locked = p.state in ("shield", "crouch", "helpless", "smash_charge")
```

In `step_horizontal` (`pycats/systems/movement.py`), `locked=True` means air friction still runs but the directional press is skipped entirely:

```python
vel = apply_horizontal_friction(vel, on_ground)   # always
if not locked:
    if press_left:  vel.x = -move_speed ...        # SKIPPED when helpless
```

**Consequence:** during helpless, left/right input is ignored and any horizontal velocity (e.g. the up-B's launch burst) decays to zero under air friction. The fighter drops straight down. **This is stricter than canon, where `airDrift` keeps full stick-driven steering.** ❌ **Divergence — the one genuine helpless-specific physics difference.**

Note the grouping: `helpless` is `locked` alongside `shield`/`crouch`/`smash_charge` — grounded, rooted states where "no walking" is correct. Applying the same lock to an **airborne** state also suppresses **air drift**, which canon does not. Whether that is an intended simplification or an over-broad lock is a **decision for a follow-on ticket**, not ruled here.

### 4.3 Fast-fall — absent everywhere (not helpless-specific)

pycats has no fast-fall mechanic. `pycats/combat/provenance.py` records the divergence: *"pycats uses a single global fall speed … the Melee/PM base 1.7 / fast-fall 2.3 split is not modelled (#120)."* So "can you fast-fall in helpless?" is moot — you can't fast-fall anywhere. This folds into the existing global fast-fall gap (#120/#261), **not** a helpless-specific item.

### 4.4 Duration / exit — matches on land; hit-exit is a separate thread

pycats helpless has no timer and no self-initiated transition; it recovers to `idle` (or `landing_lag` if a waveland window is armed) **only on landing**. Actions are locked (fighter_input gates + the state). It lacks the canon **hit-exit** (a hit does not swap helpless→hurt) — but that is the **#987 overlap / #990 C1** thread, not a fall-physics question, so it is out of scope for #1061 beyond this cross-reference.

---

## 5. Answer to #1061 — per axis

| Axis | Canon (Tier-2 Melee; PM inferred) | pycats today | Verdict |
|---|---|---|---|
| **Fall speed / gravity** | normal gravity → normal terminal; **unchanged** by special-fall | normal `gravity` → `max_fall_speed`, no state branch | ✅ **match — helpless does NOT change fall speed** |
| **Fast-fall** | present (Tier-2, ⚠ counterintuitive, Tier-1-pending #988) | **absent globally** (#120/#261) — N/A in any state | ⚠ pycats can't represent it anywhere; not helpless-specific |
| **Air drift / horizontal** | **full** stick-driven drift (`airDrift`, same as normal fall) | **removed** — `locked=True` → only air friction decay | ❌ **divergence — pycats strips drift in helpless** |
| **Duration / exit** | loops until land / ledge / grab / **hit** | until **land** only (no hit-exit — #987/#990) | partial (hit-exit tracked elsewhere) |
| **Actionability** | fully action-locked (no jump/attack/air-dodge/wall-jump) | fully action-locked (state + timer gates) | ✅ match |

**So, directly:** helpless does **not** affect *fall speed* (both keep normal gravity/terminal). It **does** affect *air physics in pycats* on one axis — pycats zeroes horizontal air control (drift) during helpless, which canon retains. Everything else about helpless is an **action lock**, not a physics change.

---

## 6. Option space for a follow-up (listed, NOT filed, NOT decided)

If the §4.2 drift divergence is judged worth acting on, a downstream **decision/DEV** ticket would choose among:

- **A — restore canon drift:** drop `"helpless"` from the `locked` set in `step_horizontal`, so a helpless fighter keeps directional air control (crudely, pycats' set-to-`move_speed` model) while remaining action-locked. Minimal, one-line-ish; needs a regression test (helpless + left/right → horizontal velocity) and an eyeball on feel.
- **B — declare it a deliberate DIVERGENCE:** keep the drift-lock as a documented simplification (add a `provenance.py` entry + a note on the helpless state), no behavior change. Cheapest; records intent.
- **C — reduced/partial drift:** allow attenuated air control in helpless (a middle ground). More faithful to some game-feel targets, more tuning surface.

Whichever is chosen is a **game-designer / architecture call** with the human (per RULES → "Changing values" and the research-never-produces-a-spec rule). The fast-fall gap (§4.3) is **not** part of this — it belongs to the existing #120/#261 global fast-fall work.

---

## 7. Method / limits / sources

- **pycats (this repo, primary):** `pycats/entities/fighter_physics.py` (`step_physics` gravity), `pycats/systems/movement.py` (`step_horizontal` `locked`), `pycats/entities/fighter_input.py` (`handle_move` locked set + action gates), `pycats/charts/fighter_chart.py` (`helpless` state + comment), `pycats/config/physics.py` (`GRAVITY`, `MAX_FALL_SPEED`), `pycats/combat/provenance.py` (fast-fall divergence). Fully grounded in source.
- **Canon (Tier-2, Melee runtime):** meleelight — `src/characters/shared/moves/FALLSPECIAL.js`; `src/physics/actionStateShortcuts.js` `airDrift` (:224) + `fastfall` (:265). Verbatim quotes in §3. **Brawl/PM 3.6 = inherited inference.**
- **Cross-check (Tier-3):** SmashWiki "Helpless" / "Special fall" (exit conditions, action-lock). Agrees.
- **NOT consulted (Tier-1):** Melee DOL / PM `.rel` disassembly — the PM-exact confirmation is the open **#988** spike. The counterintuitive §3.3 "fast-fall available in special-fall" claim is Tier-2-only and should ride #988.
- **Evidence sufficiency is the human's call** — this doc labels each claim's tier and flags the two soft spots (PM-vs-Melee inheritance; fast-fall-in-special-fall). Go/no-go on acting sits with the human.

## 8. Refs

Up-B remaining jumps **#980-adjacent (2026-08-01)** · hitstun↔helpless overlap **#987** · PM Tier-1 spike **#988** · decision queue **#990** · helpless air-dodge route **#184** · up-B recovery hook **#578** · fast-fall gap **#120 / #261** · PM fall physics **#528** (`docs/research/2026-07-04-pm-fall-physics.md`) · fighter-states reference (`docs/pm-reference/fighter-states.md`).

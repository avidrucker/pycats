# Hitstun vs. helpless (special-fall): overlap or mutually exclusive? — findings

**Ticket:** #987 (RESEARCH · `area:combat`) · **Date:** 2026-08-01 · **Agent:** CHERRY
**Sequenced with:** #980 (up-B / helpless / midair-jump findings — this drills into its divergence #2)
**Deliverable:** this doc. **No implementation** — any fix is a downstream DEV/decision ticket, filed one at a time.

---

## 1. TL;DR

- **Canon (Melee, Tier-2 primary — meleelight):** hitstun and special-fall are **mutually exclusive STATES.** A fighter has exactly one `actionState`; getting hit **overwrites** `FALLSPECIAL` with a damage state (`DAMAGEN2` / `DAMAGEFLYN`). You are never both at once. Hitstun magnitude is a **separate scalar** (`hit.hitstun`) that the damage state counts down. Brawl/PM 3.6 inferred the same (Tier-1 confirmation is the open #988 spike).
- **pycats today:** they **DO overlap.** The `helpless` statechart state **persists** while `hurt_timer > 0` runs *underneath* it, for the full hitstun duration. The chart never swaps `helpless → hurt`, because — alone among the interruptible states — `helpless` carries **no `hurt_timer > 0 → "hurt"` exit.** Reproduced live (§4).
- **Is the overlap harmful today?** It is **latent, not crashing.** Both the helpless STATE-gate and the hitstun TIMER-gate independently lock jump/attack/walk, and physics reads the timers, so knockback still launches correctly. The overlap has exactly **one** wrong-vs-canon consequence: after hitstun ends mid-air, pycats keeps the fighter **helpless** (locked, unspent jump frozen until landing), whereas canon has swapped it into a damage state that — once hitstun ends — permits jump/aerial. **That is #980's divergence #2 (== C1 in #990).**
- **Conflation risk for the future:** the codebase already treats state-label and hitstun-timer as *deliberately* distinct (input is gated on the TIMER, not the label — #370). The helpless case just makes that gap **persistent (≈22 frames) instead of the usual 1 frame.** No seam currently reads the *wrong* one of the two, but §5 lists three surfaces an eventual C1 fix must handle.

---

## 2. The question, restated

> Can **hitstun** (`hurt`/`stun`) and **helpless / special-fall** overlap on the same fighter at the same time, or are they mutually exclusive? The concern: pycats must not **conflate** "getting hit" with "falling helpless" — different mechanics that happen to both lock jumping.

Two distinct sub-questions fall out of that:

- **(Q-state)** Are they mutually exclusive *states* — can a fighter be `helpless` **and** in hitstun simultaneously?
- **(Q-behavior)** If they can co-exist, does any behavior (jump, knockback, actionability, render, logging) get computed from the *wrong* one of the two?

---

## 3. Canon: mutually exclusive states (Melee, Tier-2 primary)

**Source:** meleelight (`~/Documents/Study/JavaScript/meleelight`) — a faithful Melee-engine reimplementation in JS. Tier-2 per #980's evidence ladder (Tier-1 = actual DOL/`.rel` disassembly, not consulted; Tier-2 = this reimpl; Tier-3 = SmashWiki). Melee runtime; **Brawl/PM 3.6 = inherited inference** unless #988 resolves it.

### 3.1 There is exactly one `actionState` per fighter

Special-fall is the `FALLSPECIAL` action state. Its `init` **assigns** the single `actionState` slot (`src/characters/shared/moves/FALLSPECIAL.js`):

```js
name : "FALLSPECIAL",
canPassThrough : true,          // falls through soft platforms
canGrabLedge   : [true,false],  // CAN grab the ledge (front only)
wallJumpAble   : false,         // CANNOT wall-jump
canBeGrabbed   : true,
init : function(p,input){
    player[p].actionState = "FALLSPECIAL";   // <-- single slot, overwritten
    player[p].timer = 0;
    actionStates[characterSelections[p]].FALLSPECIAL.main(p,input);
},
```

### 3.2 A hit OVERWRITES that slot with a damage state

On a connecting hit, the victim `v` is unconditionally routed into a damage state (`src/physics/hitDetection.js`, hit-resolution block):

```js
player[v].hit.hitstun = getHitstun(player[v].hit.knockback);   // hitstun = a SCALAR

if (jabReset) {
    actionStates[characterSelections[v]].DOWNDAMAGE.init(v,input);
} else if (player[v].hit.knockback >= 80 || isThrow) {
    actionStates[characterSelections[v]].DAMAGEFLYN.init(v,input, !isThrow);
} else {
    actionStates[characterSelections[v]].DAMAGEN2.init(v,input);   // <-- replaces FALLSPECIAL
}
```

`DAMAGEN2.init` / `DAMAGEFLYN.init` each **re-assign the same single slot** (`src/characters/shared/moves/DAMAGEN2.js`):

```js
init : function(p,input){
    player[p].actionState = "DAMAGEN2";   // <-- FALLSPECIAL is GONE; there is no overlay
    player[p].timer = 0;
    ...
}
```

**Conclusion (Q-state, canon):** because `player[p].actionState` is a single string and the hit re-assigns it, being hit **replaces** `FALLSPECIAL` outright — there is no second slot for a special-fall status to persist in. Hitstun and special-fall are **mutually exclusive states**; the hitstun *magnitude* lives in a separate `hit.hitstun` scalar that the damage state consumes. This is a full state swap, not an overlay.

### 3.3 The damage state re-enables actions once hitstun ends (the "freed jump")

`DAMAGEN2` imports and runs `checkForJump` / `checkForDoubleJump` / `checkForAerials` interrupts in its `main` (`src/characters/shared/moves/DAMAGEN2.js` imports). So once `hit.hitstun` counts down, the victim can jump / aerial straight out of the damage state — **even airborne** — which is exactly how a hit "frees" a fighter from what was special-fall. This is the canon behavior #980 named as divergence #2.

*(Cross-check, Tier-3: SmashWiki "Helpless" / "Special fall" — a fighter leaves special fall by landing, grabbing the ledge, being grabbed, or **being hit**; hitstun and special fall are described as distinct states throughout. Agrees with Tier-2. PM 3.6 specifically: inferred, pending #988.)*

---

## 4. pycats: they overlap — the `helpless` state persists under a live hitstun timer

### 4.1 The structural cause

Every interruptible pycats state carries a hitstun interrupt — `idle`, `walk`, `dash`, `run`, `crouch`, `jump`, `fall`, `smash_charge` each have `_tick(lambda …: p.fighter.hurt_timer > 0, "hurt")` (`pycats/charts/fighter_chart.py`). **`helpless` does not.** Its only two exits are both grounded:

```python
helpless = state(
    {"id": "helpless"},
    _tick(lambda e, d: p.fighter.on_ground and p.fighter.landing_lag_timer > 0, "landing_lag"),
    _tick(lambda e, d: p.fighter.on_ground, "idle"),
)
```

There is no `hurt_timer`/`stun_timer` exit and the `action` parent has no `force_hurt`. So a hit taken in `helpless` sets `hurt_timer` (via `Fighter.receive_hit`) but **cannot move the chart out of `helpless`** — the state and the timer disagree for the whole hitstun window.

### 4.2 Reproduced live

`repros/repro_987.py` (gitignored, local re-run) drives a fighter into `helpless` (air-dodge route, #184), gives it one **unspent** midair jump, hits it, then holds jump every frame and watches state vs. timer:

```
in helpless (pre-hit)      state=helpless   hurt_timer=  0  jumps=1  on_ground=False  vy=  8.5
right after receive_hit    state=helpless   hurt_timer= 22  jumps=1  on_ground=False  vy= -3.4   <- launched UP, still 'helpless'
tick 1  (jump held)        state=helpless   hurt_timer= 22  jumps=1  ...
...
tick 29 (jump held)        state=helpless   hurt_timer=  1  jumps=1  vy=  7.1
tick 30 (jump held)        state=helpless   hurt_timer=  0  jumps=1  vy=  7.6   <- hitstun ENDED, still 'helpless', jump still locked
...
tick 39 (jump held)        state=helpless   hurt_timer=  0  jumps=1  vy= 12.1   <- falling helpless, unspent jump frozen
```

- The hit **applied knockback** (`vy` +8.5 → −3.4 = launched upward) and **set `hurt_timer=22`**, but `state` stayed `helpless` — the chart never swapped to `hurt`.
- The hitstun timer **counted down under the helpless state** (22 → 0 over ~30 frames).
- After hitstun ended (tick 30+), the fighter is **still `helpless`** with its unspent jump (`jumps=1`) **frozen**, falling until it lands. In canon it would be in a damage state that, at tick 30, permits the jump.

**Conclusion (Q-state, pycats):** they overlap. `helpless` (STATE) and `hurt_timer > 0` (hitstun TIMER) co-exist for the full hitstun duration.

---

## 5. Conflation audit — every seam that reads `helpless` OR `hurt`/`stun`

Two families of seam: **STATE-label readers** and **hitstun-TIMER readers.** The audit checks whether any seam assumes the two are mutually exclusive when they are not. Verdict per seam:

| Seam (landmark) | Reads | Behavior during helpless+hitstun overlap | Verdict |
|---|---|---|---|
| jump gate — `fighter_input.handle_input` (`state not in ("dodge","hurt","stun","helpless")`) | STATE | `helpless` blocks jump; independently `handle_actions` is skipped while `hurt_timer>0`. Both agree "no jump." | ✅ no bug (both lock) |
| walk gate — `fighter_input` (`… "helpless" …`) | STATE | blocked by `helpless`. | ✅ |
| attack gate — `fighter_input` (`state not in ("shield","dodge","helpless")`) | STATE | `helpless` blocks; hitstun also skips `handle_actions`. | ✅ |
| hitstun input-lock — `fighter_input.handle_actions` (`hurt_timer==0 and stun_timer==0`) | TIMER | early-returns while hitstun runs, regardless of state (#370 — deliberately timer-driven). | ✅ (this is the mechanism) |
| action/movement dispatch — `player._run_actions_and_movement` (`in_hitstun` + `state not in (…)`) | BOTH | `helpless` is **absent** from the exclusion list, but `in_hitstun` (timer) skips the whole block during overlap; after hitstun ends, the inner `handle_actions` gates re-block on the `helpless` label. | ✅ no bug — but see note below |
| hitstun velocity decay — `fighter_physics` (`in_hitstun = hurt_timer>0 or stun_timer>0`) | TIMER | applies knockback decay while `state==helpless` — this is why the launch works. | ✅ (timer-correct) |
| render tint — `systems/status_model` "hurt"/"stun" sources (`active on hurt_timer>0` / `stun_timer>0`) | TIMER | the red hurt-flash / dizzy overlay **render correctly** during overlap, even though the state label is `helpless`. | ✅ (timer-driven) |
| dizzy stars — `render/battle` + `render/status` (`stun_timer>0`) | TIMER | correct. | ✅ |
| CPU controller — `sim/controllers` (`hurt_timer==0 and stun_timer==0`, #8/#370) | TIMER | reads timer, not label — correct by design. | ✅ |
| battle log — `sim/battle_log.NOTABLE_STATES` (`{"ko","hurt","helpless","dizzy","shield","dodge"}`) | STATE | a hit-in-helpless **logs as `helpless`, never `hurt`** — the state never flips. | ⚠️ observability gap |

**Audit conclusion:** **no seam currently computes a behavior from the wrong one of the two.** The overlap is benign because (a) input/actions are gated on the hitstun **timer** independent of the state label (the #370 design already assumes label≠timer), and (b) knockback/physics/render read the **timer**, so the launch and the hurt-flash both work. The only current fallout is the **battle-log observability gap** (a hit-in-helpless is logged as `helpless`) and the **canon divergence** (fighter stays locked-helpless after hitstun instead of being freed).

---

## 6. Surfaces an eventual C1 fix must handle (not fixed here)

If #990's C1 is ruled V1 (make a hit free the fighter from helpless, canon-style), the implementer inherits three coupled facts surfaced by this research — flagged, not resolved:

1. **The minimal structural change** is that `helpless` lacks the `_tick(hurt_timer>0, "hurt")` exit every other interruptible state has. Adding it swaps `helpless → hurt` on a hit, matching canon's state swap.
2. **Stale recovery flags.** `Fighter.receive_hit` does **not** clear `air_dodge_active` / `recovery_active` (only landing/respawn do). After a hypothetical `helpless → hurt → fall`, the `fall` exit does **not** re-check those flags (only the `attacking`/`dodge` exits route to helpless), so there's no accidental bounce-back to helpless — **but the implementer must confirm that and decide whether a hit should clear those flags.**
3. **Jump-refresh semantics.** #980 established up-B **locks** (does not zero) the jump counter, so an unspent jump survives. Freeing the fighter via a hit must therefore make that unspent jump usable again — the C1 fix is not just the state swap but the decision about what `jumps_remaining` means once freed (this is exactly the #980 "lock vs. zero-out" distinction).

These are **inputs to the C1 decision/DEV ticket**, not scope here.

---

## 7. Answer to #987

- **Canon:** mutually exclusive states — a hit **replaces** special-fall with a damage state (Tier-2 primary; Brawl/PM inferred, #988 pending).
- **pycats:** **they overlap** — `helpless` persists with `hurt_timer` live underneath, because `helpless` has no hitstun exit. Proven live (§4).
- **Is it a conflation bug today?** Latent, not active: no seam reads the wrong source, but the overlap is the mechanism behind #980 divergence #2 and it leaves a battle-log observability gap. Resolving it is **C1 in #990** — gated on this finding, now unblocked.

---

## 8. Sources & method

- **Tier-2 primary (Melee runtime):** meleelight — `src/characters/shared/moves/FALLSPECIAL.js`, `DAMAGEN2.js`, `DAMAGEFLYN.js`; `src/physics/hitDetection.js` (hit-resolution → damage-state init); `src/physics/physics.js` `land()`. Verbatim quotes in §3.
- **Tier-3 cross-check:** SmashWiki "Helpless" / "Special fall" (all-games, proxy). Agrees.
- **pycats source (this repo):** `pycats/charts/fighter_chart.py` (`helpless`, `hurt`, `stun` states), `pycats/entities/fighter.py` (`receive_hit`, timers), `pycats/entities/fighter_input.py` (gates), `pycats/entities/player.py` (`_run_actions_and_movement`), `pycats/entities/fighter_physics.py`, `pycats/systems/status_model.py`, `pycats/sim/battle_log.py`, `pycats/sim/controllers.py`, `pycats/render/{battle,status}.py`.
- **Live reproduction:** `repros/repro_987.py` (gitignored, local re-run) (air-dodge → helpless → hit → per-frame state/timer trace). Output in §4.2.
- **PM 3.6 posture:** runtime rules inferred from Brawl/Melee inheritance; the Tier-1 confirmation is the open **#988** spike. No PM-primary source consulted here.

## 9. Refs

Up-B/helpless findings **#980** (§9 divergences, §12 chart dump) · decision queue **#990** (C1 gated on this) · PM Tier-1 spike **#988** · helpless **#184** · recovery hook **#578** · label-lags-timer design **#370**.

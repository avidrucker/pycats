# meleelight fighter action-state graph — states, transitions, priority order

**Ticket:** #1011 (child 1 of statechart epic #1009) · **Role:** RESEARCH · `area:entities`
**Evidence tier:** **Tier-2** — a faithful Melee-engine *reimplementation* in readable JS
(`meleelight`, local at `~/Documents/Study/JavaScript/meleelight`), **not** Melee
disassembly (Tier-1). Every edge below is grounded in a verbatim source excerpt or a
`file:line` citation captured on 2026-08-01. This is the first (cheapest) source of the
epic because the transitions are plain code, not a DOL dump.
**Deliverable scope:** the action-state graph only — no implementation, no pycats changes.

---

## 1. TL;DR

- meleelight models a fighter as **one `player[p].actionState` string slot** (a flat FSM,
  not a hierarchy). Exactly one state is active at a time; entering a state overwrites the
  slot.
- Each state is a module (`shared/moves/<NAME>.js`) with `init` / `main` / `interrupt`
  (and sometimes `land`). Once per frame the engine calls the **active state's `main`**,
  which calls **`interrupt` first** — and `interrupt`'s `if / else-if` chain **is** the
  priority-ordered list of player-initiated exits (top = highest priority). If no interrupt
  fires, `main` applies the state's physics and may auto-transition on a **timer**.
- Transitions come from **three mechanisms**, not one: (1) **interrupt** (player action,
  priority-ordered, in the state module), (2) **timer/auto** (state completes, in `main`),
  (3) **collision/engine** (land / wall / ceiling / ledge / hit — driven by `physics.js`
  and `hitDetection.js`, *outside* the state module).
- **Hitstun and helpless (FALLSPECIAL) are mutually-exclusive states.** A hit
  unconditionally overwrites the actionState with `DAMAGEN2` / `DAMAGEFLYN` / `DOWNDAMAGE`
  — there is no guard on the prior state, so getting hit while helpless replaces helpless.
  Hitstun *magnitude* is a separate scalar `player[p].hit.hitstun = floor(knockback*0.4)`.
  This is the Tier-2 confirmation of the canon claim in #987/#980.
- **Character structure is shared; character data and attacks differ.** Every fighter's
  state table is `{...baseActionStates, ...Char.moves}` deep-copied. The ~80 shared "engine"
  states (WAIT/FALL/GUARD/DAMAGE*/…) are structurally identical across fighters; only
  **attacks/specials/throws/ledge-getup** are per-character modules, plus a handful of
  **per-character numeric data overrides** (roll/tech velocities, ledge offset) on otherwise
  shared states. This 3-tier split is the direct input to the architecture question in #1010.

---

## 2. The dispatch model (how the graph is executed)

### 2.1 One flat state slot
`player[p].actionState` is a single string. Every state module's `init` hard-assigns it,
e.g. `WAIT.js`:
```js
init : function(p,input){
  player[p].actionState = "WAIT";        // WAIT.js:15
  player[p].timer = 1;
  actionStates[characterSelections[p]].WAIT.main(p,input);
}
```
There is **no state hierarchy / no orthogonal regions** — it is a classic flat FSM with one
active node. (Contrast pycats, whose `build_fighter_chart` uses a compound chart with a
hitstun sub-machine.)

### 2.2 The per-frame driver (`physics.js`)
When a fighter is **not** in a hitlag freeze, the engine advances the active state once per
frame (`physics.js`, the `else` of the hitlag branch):
```js
player[i].prevActionState = player[i].actionState;                        // physics.js:564
actionStates[characterSelections[i]][player[i].actionState].main(i, input); // :565
```
`main` runs `interrupt` first; a canonical shape (`WAIT.js:19-27`):
```js
main : function(p,input){
  player[p].timer += 1;
  if (!actionStates[characterSelections[p]].WAIT.interrupt(p,input)){   // interrupt wins if it returns true
    reduceByTraction(p,false);
    if (player[p].timer > framesData[characterSelections[p]].WAIT){     // else timer auto-transition
      actionStates[characterSelections[p]].WAIT.init(p,input);
    }
  }
}
```
While `hit.hitlag > 0` the state is frozen (no `main` runs); `hitlagSwitchUpdate`
(`physics.js:458`) counts hitlag down and, at hitlag=0 with knockback, applies the launch
velocity/DI.

### 2.3 Three transition classes
Not every edge lives in a state's `interrupt`. The graph has three edge sources:

| Class | Where it lives | Trigger | Examples |
|---|---|---|---|
| **Interrupt** | state module `interrupt` | player input, priority-ordered | WAIT→KNEEBEND (jump), GUARD→ESCAPEF (roll) |
| **Timer / auto** | state module `main` | state duration elapsed | KNEEBEND→JUMPF, DASH→RUN, CLIFFCATCH→CLIFFWAIT |
| **Collision / engine** | `physics.js`, `hitDetection.js` | environment/hit | land()→WAIT/LANDING/TECH, ledge→CLIFFCATCH, hit→DAMAGE* |

The collision/engine edges are the ones a pygame port most easily misses, because they are
**not** visible in the state modules:
- **`land()`** (`physics.js:394`) — on ground contact; see §2.4.
- **`dealWithWallCollision`** (`physics.js:77`) → WALLTECH / WALLTECHJUMP / WALLDAMAGE / WALLJUMP.
- **`dealWithCeilingCollision`** (`physics.js:343`) → TECHU (tech) / STOPCEIL (bonk).
- **`dealWithLedges`** (`physics.js:866`) → CLIFFCATCH (see §2.5).
- **Hit resolution** (`hitDetection.js`) → DAMAGE* / DOWNDAMAGE / CAPTURE* (see §6).

### 2.4 `land()` — the landing dispatcher + jump-counter reset
Every landing runs `land()` (`physics.js:394-455`), which **unconditionally resets air
bookkeeping** then routes on the landing state's `landType`:
```js
player[i].phys.doubleJumped = false;   // :399
player[i].phys.jumpsUsed    = 0;       // :400  ← jump counter reset to FULL on every landing
player[i].phys.fastfalled   = false;   // :402
player[i].phys.wallJumpCount = 0;      // :405
...
switch (actionStates[characterSelections[i]][player[i].actionState].landType) {   // :421
  case 0: player[i].phys.cVel.y >= -1 ? WAIT.init : LANDING.init;   // soft vs hard land
  case 1: actionStates[...][actionState].land(i, input);           // OWN FN (aerials, FALLSPECIAL)
  case 2: techTimer>0 ? (TECHF|TECHB|TECHN by stick) : DOWNBOUND.init;  // knockdown/tech
  default: LANDING.init;
}
player[i].hit.hitstun = 0;             // :454  ← landing also clears the hitstun scalar
```
So `landType` is a **per-state tag** that selects the landing edge: neutral airborne states
use type 0 (→WAIT/LANDING), aerials & FALLSPECIAL use type 1 (own `land` → LANDINGATTACKAIR* /
LANDINGFALLSPECIAL), tumble states use type 2 (→TECH*/DOWNBOUND).

### 2.5 Ledge grab is a hitstun-gated collision edge
`dealWithLedges` (`physics.js:866-920`) grabs a ledge only when, in priority:
```js
player[i].phys.onLedge === -1 && !player[i].phys.ledgeRegrabCount   // :894  not already on/regrab-cooldown
&& ledgeAvailable && !player[i].phys.grounded && player[i].hit.hitstun <= 0   // :906  airborne, NOT in hitstun
&& actionStates[...][actionState].canGrabLedge[dir]                  // :916/:919  per-state flag
```
Two things worth carrying to pycats: the **`canGrabLedge` per-state flag** (FALLSPECIAL is
`[true,false]` — can grab facing the ledge), and the **`hit.hitstun <= 0` scalar gate** —
hitstun suppresses ledge-grab regardless of which fall-state the chart is in.

### 2.6 Turbo interrupt (non-default) — a universal IASA layer
`turboGroundedInterrupt` / `turboAirborneInterrupt` (`actionStateShortcuts.js:527-610`)
implement "cancel-anything-after-a-hit", but they run **only** under `gameSettings.turbo`
(`physics.js:595`). They are **not** part of the default Melee statechart; noted here so a
reader doesn't mistake them for baseline priority.

---

## 3. Character-dependence: the 3-tier taxonomy (feeds #1010)

This is the load-bearing architectural finding. meleelight builds each fighter's state table
by **spread-merging** a shared base with the character's own moves, then deep-copying
(`marth/index.js:18-21`):
```js
setupActionStates(CHARIDS.MARTH_ID, {
  ...baseActionStates,   // shared/moves/index.js — the ~80 shared "engine" states
  ...Marth.moves,        // characters/marth/moves — attacks/specials/throws/ledge-getup/appeal
});
// setupActionStates(i,val) = actionStates[i] = deepCopyObject(true, val)   (actionStateShortcuts.js:613)
```
Then a few **per-character numeric overrides** are stamped onto otherwise-shared states
(`marth/index.js:24-31`):
```js
actionStates[MARTH_ID].ESCAPEB.setVelocities   = [ ... ];   // roll trajectory
actionStates[MARTH_ID].TECHB.setVelocities     = [ ... ];   // tech-roll trajectory
actionStates[MARTH_ID].DOWNSTANDF.setVelocities= [ ... ];   // getup-roll trajectory
actionStates[MARTH_ID].CLIFFCATCH.posOffset    = [ ... ];   // ledge-hang offset
```

So the char-dependence splits cleanly into **three tiers**:

| Tier | What | How it varies | Members |
|---|---|---|---|
| **T1 — fully shared** | structure **and** logic identical across fighters (deep-copied from one base) | only via `framesData[char].STATE` **durations** | WAIT, WALK, DASH, RUN, RUNBRAKE, RUNTURN, SMASHTURN, TILTTURN, SQUAT(/WAIT/RV), KNEEBEND, PASS, OTTOTTO(/WAIT), MISSFOOT, JUMPF/B, JUMPAERIALF/B, FALL, FALLAERIAL, **FALLSPECIAL**, LANDING, LANDINGFALLSPECIAL, GUARDON/GUARD/GUARDOFF, ESCAPEN, ESCAPEAIR, SHIELDBREAK*, WALL*, DAMAGEN2/DAMAGEFLYN/DAMAGEFALL/DOWNDAMAGE, DOWNBOUND/WAIT, DOWNSTANDN, TECHN/TECHU, FURA*/SLEEP, CLIFFCATCH/CLIFFWAIT, DEAD*/REBIRTH(/WAIT)/ENTRANCE, CAPTURE*/CATCHCUT/CATCHWAIT, STOPCEIL |
| **T2 — shared structure, per-char DATA** | same module, but a **numeric array** is overridden per fighter | scripted velocity/offset arrays | ESCAPEB/ESCAPEF `setVelocities`, TECHB/TECHF `setVelocities`, DOWNSTANDB/DOWNSTANDF `setVelocities`, CLIFFCATCH `posOffset` |
| **T3 — fully character-specific** | its own module under `characters/<char>/moves/` | entire move | all **attacks** (JAB1/2, F/U/D-TILT, F/U/D-SMASH, ATTACKDASH, ATTACKAIRN/F/B/U/D), all **specials** (NEUTRAL/SIDE/UP/DOWN × ground/air, incl. multi-hit sub-states), **grab/throws** (GRAB, CATCHATTACK, THROW U/D/F/B, THROWN-by-X), **ledge-getup** options (CLIFFATTACK/ESCAPE/GETUP/JUMP × QUICK/SLOW), **APPEAL** |

Corroborating detail: aerial/special interrupt targets are re-dispatched **by character index**
— `checkForIASA` (`actionStateShortcuts.js:400-406`) hardcodes `MARTHMOVES[a[1]] /
PUFFMOVES / FOXMOVES`, and grounded interrupts re-dispatch the returned key through
`actionStates[characterSelections[p]][key]`. The **interrupt guards themselves**
(`checkForJump/Smashes/Tilts/Specials/Aerials/Dash/…`) are shared and character-independent;
only the *destination attack module* is per-character.

**Implication for #1010 (stated, not decided):** meleelight is essentially the
"**one general chart + per-character DATA/leaf-move injection**" design — the same shape
pycats already uses (`build_fighter_chart(player)` parameterized by Fighter). The transition
*topology* of the engine states is 100% shared; character identity enters only as (a) frame
durations, (b) a few scripted velocity arrays, and (c) the leaf attack/special/throw/getup
nodes. That is direct evidence for the general-with-injection option — but the ruling belongs
to #1010, not here.

---

## 4. State catalog — the graph, by family

Notation: `guard → TARGET` in priority order (top = checked first). "**Actionable**" = the
`interrupt` chain reads player input and can exit to player-chosen states; "**Locked**" =
`interrupt` has no input branches (timer/collision exit only). All dispatch is through
`actionStates[characterSelections[p]]` unless flagged. Frame counts are per-character
`framesData[char].STATE` unless a hardcoded literal is noted.

### 4.1 Grounded / standing (T1 structure)

**WAIT** (idle hub) — *actionable*. Entered from ~20 states + self-loop. Priority:
`jump → KNEEBEND` > `l/r or lA/rA (shield) → GUARDON` > `special → [b1]` > `smash → [s1]` >
`tilt → [t1]` > `taunt(du) → APPEAL` > `squat → SQUAT` > `dash → DASH` >
`smashTurn → SMASHTURN` > `tiltTurn → TILTTURN` > `|lsX|>0.3 → WALK`; timer→self (idle loop).
```js
// WAIT.js:43-89 (interrupt, priority order)
if (j[0] && !player[p].inCSS){ ...KNEEBEND.init(p,j[1],input); return true; }
else if (input[p][0].l || input[p][0].r){ ...GUARDON.init(p,input); return true; }
else if (b[0]){ ...[b[1]].init(p,input); return true; }        // special
else if (s[0]){ ...[s[1]].init(p,input); return true; }        // smash
else if (t[0]){ ...[t[1]].init(p,input); return true; }        // tilt
...
else if (Math.abs(input[p][0].lsX) > 0.3 ...){ ...WALK.init(p,true,input); return true; }
```

**WALK** — *actionable*. Same option menu as WAIT plus `lsX===0 → WAIT`; timer→self.
**DASH** — *actionable*. Adds dash-specific: early `a → FORWARDSMASH`/`GRAB`/`ATTACKDASH`,
`timer>dashFrameMin & lsX·face>0.62 → RUN`, dash-dance self-loop, `timer>DASH → WAIT`.
Uses per-fighter `charAttributes.dashFrameMin/Max`.
**RUN** — *actionable*. `a → GRAB/ATTACKDASH`, `jump → KNEEBEND`, sideB/downB, shield,
`|lsX|<0.62 → RUNBRAKE`, `lsX·face<-0.3 → RUNTURN`. No timer exit (animation loops).
**RUNBRAKE** — *limited*. `jump → KNEEBEND` > `squat → SQUAT` > `lsX·face<-0.3 → RUNTURN` >
`timer>RUNBRAKE → WAIT`. No attacks/shield.
**RUNTURN** — *locked except jump*. `jump → KNEEBEND` > `timer>RUNTURN →` (`lsX·face>0.6 ? RUN : WAIT`).
Flips `face` mid-state at per-fighter `runTurnBreakPoint`.
**SMASHTURN** — *actionable*. Flips `face` on init. jump/sideB/shield/smash/tilt/taunt,
`timer===2 & lsX·face>0.79 → DASH`, hardcoded `timer>11 → WAIT`.
**TILTTURN** — *actionable*. Reversed tilt check while `timer<6`; flips `face` at `timer===6`;
jump/sideB/shield/smash/tilt/taunt, `timer===6 & dashbuffer → DASH`, hardcoded `timer>11 → WAIT`.
**SQUAT** — *actionable* (crouch). `timer===4 & down-hold on soft platform → PASS`, shield,
special/smash/tilt, `timer>SQUAT → SQUATWAIT`, taunt, then `jump → KNEEBEND` (jump is
**demoted** below the SQUATWAIT auto-exit — notable priority quirk).
**SQUATWAIT** — *actionable* (crouch hold). `lsY>-0.61 → SQUATRV` > jump/shield/special/smash/
tilt/taunt/dash/smashTurn > timer→self. Also entered directly by per-character `DOWNTILT`.
**SQUATRV** — *actionable* (crouch stand-up). `timer>SQUATRV → WAIT` > jump/shield/special/
smash/tilt/taunt/smashTurn/`|lsX|>0.3 → WALK`.
**KNEEBEND** (jumpsquat) — *locked except grab/upsmash/upB*. `timer>charAttributes.jumpSquat →`
(`lsX·face>=-0.3 ? JUMPF : JUMPB`) > `a+shoulder → GRAB` > `up+a/cUp → UPSMASH` >
`up+b → UPSPECIAL`. This is the universal jump-squat funnel — entered from **every**
actionable ground state.
**PASS** (platform drop, airborne) — *actionable aerial*. `aerial → [a1]` > `l/r → ESCAPEAIR` >
`doubleJump → JUMPAERIALB/F` > `special → [b1]` > `timer>PASS → FALL`.
**OTTOTTO / OTTOTTOWAIT** (teeter) — *actionable*. Entered from `physics.js` edge-teeter.
Full ground menu; OTTOTTO→OTTOTTOWAIT on timer; OTTOTTOWAIT loops (no timed exit to WAIT).
**MISSFOOT** (walk-off-backward stumble, airborne) — *locked*. Only `timer>26 → DAMAGEFALL`;
`main` allows fastfall+drift but no action input.

### 4.2 Airborne / jump / landing (T1 structure)

**JUMPF / JUMPB** (rising jump) — *actionable*. Entered only from KNEEBEND. Priority:
`aerial → ATTACKAIR*` > `l/r → ESCAPEAIR` > `doubleJump → JUMPAERIALB/F` > `special → [b1]` >
`timer>JUMPF/B → FALL`. Landing via `land()` type 0.
**JUMPAERIALF / JUMPAERIALB** (air jump) — *actionable, no further jump for standard chars*.
Entered from the double-jump branch of **every** airborne state + wall/ledge/rebirth. `init`
sets `doubleJumped = true` (consumes the air jump). Exits: aerial/air-dodge/special/
`timer → FALLAERIAL`. No double-jump branch (already consumed; multi-jump chars re-enter via
the `jumpsUsed<5 && charAttributes.multiJump` guard elsewhere).
**FALL** (neutral fall) — *actionable* (or **locked** when entered with `disableInputs=true`,
e.g. grab-release / ledge-drop). Priority: aerial > air-dodge > doubleJump > special >
`timer>FALL → FALL` (self-loop). The workhorse fall state.
**FALLAERIAL** (fall after air-jump/aerial) — *actionable*. Same menu as FALL; self-loops.
**FALLSPECIAL** (helpless / special-fall) — **LOCKED**. Entered **only** from
`ESCAPEAIR` (air-dodge timeout). The entire `interrupt` is one timer branch — **no input
checks at all**:
```js
// FALLSPECIAL.js:26-30 (the complete interrupt)
if (player[p].timer > framesData[characterSelections[p]].FALLSPECIAL) {
  actionStates[characterSelections[p]].FALLSPECIAL.init(p,input);   // self re-init: loops until land
  return true;
}
else { return false; }
```
`main` runs **only** `fastfall(p,input)` and `airDrift(p,input)` — so FALLSPECIAL permits
**fastfall + horizontal drift only**, and **forbids** aerials, air-dodge, double-jump, and
specials. It exits solely by **landing** (`landType 1` → `LANDINGFALLSPECIAL`). Flags:
`wallJumpAble:false`, `canGrabLedge:[true,false]`. **This is Melee helpless**, and its only
exits are (a) land, (b) grab a ledge (the collision edge in §2.5), or (c) get hit (§6). It
holds no jump counter of its own — jumps were already spent; `land()` restores them.
**LANDING** — *locked frames 1-4, then a jump-cancel/act-out window 5-30, → WAIT at 30*.
The one landing state that is actionable mid-way (jump-cancel, shield, tilt/smash/special,
dash, `timer===5 & down → SQUATWAIT`).
**LANDINGFALLSPECIAL** — **locked**. `timer > 30 → WAIT`, advanced by
`timer += phys.landingMultiplier` (ESCAPEAIR sets `landingMultiplier=3`, so a wavedash's
landing lag burns ~10 frames). No input.
**LANDINGATTACKAIRN/F/B/D/U** — **locked** (per-aerial landing lag). Entered by each fighter's
`ATTACKAIR*` move on landing (landType 1). L-cancel halves the lag
(`landingLagScaling = phys.lCancel ? 2 : 1`). Only exit: `timer>LANDINGATTACKAIR* → WAIT`.
Timers are **per-fighter** (`framesData[char].LANDINGATTACKAIR*`).
**STOPCEIL** (ceiling bonk) — *mostly locked*. From `physics.js` ceiling collision.
`timer>5 & hitstun<=0 → FALL` > `timer>STOPCEIL → (hitstun<=0 ? DAMAGEFALL : bleed-hitstun)`;
`land` → tech/DOWNBOUND (if hitstun) or LANDING. Drift only, no action input.

### 4.3 Defense / shield / dodge / wall (T1 structure)

**GUARDON → GUARD → GUARDOFF** is the shield cycle:
- **GUARDON** (shield startup / powershield window) — *actionable OOS*. Entered from every
  grounded state on shield press. Powershield armed if a trigger is fully depressed at entry.
  Priority: `jump/cUp → KNEEBEND (jump OOS)` > `a → GRAB (shield-grab)` > `down → ESCAPEN
  (spotdodge)` > `fwd → ESCAPEF (roll-f)` > `back → ESCAPEB (roll-b)` > `down-hold on platform
  → PASS` > `timer>GUARDON → GUARD`.
- **GUARD** (full hold) — *actionable OOS*. Same OOS menu + `lA<0.3 & rA<0.3 → GUARDOFF
  (release)`; self-loops while held.
- **GUARDOFF** (release cooldown) — *jump-cancellable*. `jump → KNEEBEND` >
  `timer>GUARDOFF → WAIT`; if the release followed a **powershield**, it is action-cancellable
  into smashes/tilts/dash/walk (the powershield lag-cancel sub-tree).

**ESCAPEN** (spotdodge) — **locked**. `timer>ESCAPEN → WAIT`; intangible window, no cancel.
**ESCAPEF** (forward roll) — **locked**. `timer>ESCAPEF → WAIT` (flips `face`); scripted
`setVelocities` (**T2 per-char data**), intangible.
**ESCAPEB** (back roll) — **locked**. `timer>ESCAPEB → WAIT` (no face flip); scripted
`setVelocities` (**T2**), intangible.
**ESCAPEAIR** (air-dodge / wavedash) — **locked**. Entered from every airborne state on L/R.
Directional 3.1-speed dodge, then **`timer>49 → FALLSPECIAL`** (hardcoded 49, engine-global —
this is *the* helpless-inducing edge), or `land → LANDINGFALLSPECIAL` (the wavedash). Allows
airDrift/fastfall after `timer<30`, no input cancel. Note the 49-frame and 3.1 speed are
**hardcoded globals**, not per-move data (matches the "engine-hardcoded air-dodge velocity"
gap that per-move datamining can't answer — memory `rukaidata-engine-hardcoded-limit`).
**SHIELDBREAKFALL → SHIELDBREAKDOWNBOUND → SHIELDBREAKSTAND → FURAFURA** — all **locked stun**;
each is a pure `timer>STATE → next` chain ending in the mashable dizzy FURAFURA. Entered from
`shieldDepletion` (`actionStateShortcuts.js:297`) when shieldHP hits 0.
**WALLJUMP / WALLTECH / WALLTECHJUMP** — *actionable airborne after `timer>1`*: aerials /
air-dodge / double-jump / specials / `timer → FALL`. Engine-entered from wall collision.
(Quirk: `WALLTECHJUMP.main` calls `WALLTECH.interrupt`; its own interrupt reads
`framesData.WALLJUMP` — a naming inconsistency, flagged not resolved.)
**WALLDAMAGE** (wall-bonk hitstun) — **locked stun**. Reflects knockback off the wall ×0.8,
decrements `hit.hitstun`, `timer>WALLDAMAGE → DAMAGEFALL`.

### 4.4 Hitstun / knockdown / tech / dizzy (T1 structure) — see §6 for entry

**DAMAGEN2** (light hitstun, `knockback<80`) — **locked while `hitstun>0`, then actionable**.
While `hit.hitstun>0` the interrupt returns false / self-holds; at `hitstun<=0` it exposes the
**full act-out menu** (grounded: jump/shield/special/smash/tilt/squat/dash/turn/walk; airborne:
aerial/air-dodge/double-jump/special/fall). Jumps are **not** force-restored — exit reuses the
normal `checkForDoubleJump`. `land` → LANDING once hitstun spent.
**DAMAGEFLYN** (heavy hitstun / tumble, `knockback>=80 || isThrow`) — **locked, no in-state
menu**. Single exit `timer>1 & hitstun===0 → DAMAGEFALL`. Landing via `land()` type-2 tech
routing (TECH*/DOWNBOUND).
**DAMAGEFALL** (actionable tumble-fall) — *actionable*. The "hitstun spent, you can act but
haven't" fall: aerial/air-dodge/double-jump/special/`hard-flick → FALL`/`timer → self`. Drift
enabled. This is where DAMAGEFLYN drains to.
**DOWNDAMAGE** (jab-reset / hit-while-downed, `downed & damage<7`) — **locked ~13f**. `timer>13
→` (grounded: `hitstun<=0 ? DOWNSTANDN : DOWNWAIT`; air: `FALL`).
**DOWNBOUND → DOWNWAIT → DOWNSTAND{N,B,F}** the knockdown/getup chain:
- **DOWNBOUND** (knockdown bounce) — **locked**. `timer>DOWNBOUND → DOWNWAIT`.
- **DOWNWAIT** (lying down) — **locked until getup input, hitstun-gated**. Getup options
  (`lsX·face away → DOWNSTANDB`, `toward → DOWNSTANDF`, `up → DOWNSTANDN`, `a/b → DOWNATTACK`)
  fire only at `hitstun<=0`; else self-loops.
- **DOWNSTANDN/B/F** (getup/roll) — recovery to **WAIT** on timer; intangible; B/F scripted
  `setVelocities` (**T2 per-char data**). DOWNATTACK is per-character (**T3**).
**TECHN/TECHB/TECHF** (grounded tech) — recovery to **WAIT** on timer; intangible; B/F scripted
`setVelocities` (**T2**). Entered from `land()` type-2 when `techTimer>0`.
**TECHU** (ceiling tech) — **locked briefly**. `init` hard-clears `knockback`/`hitstun`;
`timer>TECHU → FALL`.
**FURAFURA** (dizzy) — **locked, mash to escape**. `stuckTimer=490` on init, drained by
`mashOut` (`stuckTimer -= 3`); `stuckTimer<=0 → WAIT`; not hitstun-driven.
**FURASLEEPSTART → FURASLEEPLOOP → FURASLEEPEND** (sleep) — **locked**; `stuckTimer` chain,
loop has no input escape; END → WAIT. Entered from a sleep-type hitbox (`type===5`).
**SLEEP** (star-KO / off-screen) — **terminally locked**. `interrupt` always returns false;
teleports off-screen; exit driven externally (revival). Entered from DEAD* when stocks depleted.

### 4.5 Ledge / death / spawn / grab

**CLIFFCATCH** (ledge grab incoming) — **locked**. Only edge from `dealWithLedges`. **Resets
the jump counter to full**: `doubleJumped=false; jumpsUsed=0` (`CLIFFCATCH.js:22-23`),
38-frame intangibility, snaps to ledge. `timer>CLIFFCATCH → CLIFFWAIT`. (Confirms #980
divergence #1: ledge grab restores jumps.)
**CLIFFWAIT** (ledge hang) — *actionable*, the ledge-getup menu in priority:
`away/down → FALL (release)` > `jump input → CLIFFJUMPQUICK/SLOW` > `toward/up → CLIFFGETUP
QUICK/SLOW` > `a/b/cUp → CLIFFATTACKQUICK/SLOW` > `shoulder/cToward → CLIFFESCAPEQUICK/SLOW` >
`ledgeHangTimer>600 → DAMAGEFALL` > timer→self. The QUICK/SLOW fork is `percent<100 ?
QUICK : SLOW`. All getup targets are **per-character** (**T3**).
**DEADLEFT/RIGHT/UP/DOWN** (blastzone death) — **locked**. `timer>60 →` (`stocks>0 ? REBIRTH :
SLEEP`). Reached by blastzone logic by name (no literal `.DEAD*.init` caller).
**REBIRTH** (respawn descent) — **locked**. Teleports to spawn, **resets all jump/air state**
(`doubleJumped=false; jumpsUsed=0; wallJumpCount=0`), `percent=0`, `shieldHP=60`. `timer>90 →
REBIRTHWAIT`.
**REBIRTHWAIT** (on spawn platform) — *actionable*. aerial/air-dodge/double-jump/special, plus
`spawnWaitTime>300 → FALL` and `|stick|>0.3 → FALL`. Spawn invincibility (`invincibleTimer=120`)
persists into the chosen action.
**ENTRANCE** (initial drop-in) — **locked**, and **defined-but-uninvoked** in the current tree
(`timer>60 → FALL`; no `.ENTRANCE.init` caller anywhere in `src/`).
**Grab sequence** — victim: **CAPTUREPULLED** (reeled in, locked) → **CAPTUREWAIT** (held,
locked, mash to escape) → optional **CAPTUREDAMAGE** (pummeled, locked, loops back to
CAPTUREWAIT) → **CAPTURECUT** (escaped → WAIT) or a per-character **THROWN\*** state.
Grabber: **CATCHWAIT** (holding — *actionable* throw menu: `a → CATCHATTACK`,
`up/down/back/fwd → THROW{UP,DOWN,BACK,FORWARD}`) → **CATCHCUT** (broken → WAIT). Throw/pummel
targets are per-character (**T3**). Entered from the grab-connect branch in `hitDetection.js`.
**THROWNFALCONDIVE** — **terminally locked, character-specific**. Entered only when the grabber
is in `UPSPECIAL` (Captain Falcon's Falcon Dive); `interrupt` always returns false; the victim
leaves only when Falcon's move script reassigns it. The one clearly **char-gated** engine edge.

---

## 5. Priority-order conventions (the reusable ranking)

Across the shared states, the interrupt priority is remarkably consistent. The **grounded**
ranking (WAIT/WALK/SQUAT*/OTTOTTO*/LANDING-window/DAMAGEN2-actionable) is:

1. **jump** (`checkForJump → KNEEBEND`) — almost always first (SQUAT is the deliberate exception,
   demoting jump below its SQUATWAIT auto-exit)
2. **shield** (`l/r` digital or `lA/rA` analog → GUARDON)
3. **special** (`b → [b1]`)
4. **smash** (`a`+strong-stick or c-stick → `[s1]`)
5. **tilt** (`a`+soft-stick → `[t1]`)
6. **taunt** (`du → APPEAL`)
7. **movement/posture** (squat → dash → smashTurn → tiltTurn → walk)

The **airborne** ranking (JUMPF/B, FALL, FALLAERIAL, PASS, DAMAGEFALL, REBIRTHWAIT) is:

1. **aerial** (`checkForAerials → ATTACKAIR*`)
2. **air-dodge** (new `l/r → ESCAPEAIR`)
3. **double-jump** (`checkForDoubleJump` & jump available → JUMPAERIALB/F)
4. **special** (`b → [b1]`)
5. **timer** (→ FALL / self-loop)

The guards are shared predicates in `actionStateShortcuts.js`
(`checkForJump/Smashes/Tilts/Specials/Aerials/Dash/SmashTurn/TiltTurn/Squat/DoubleJump/
MultiJump`); only the *destination attack module* varies by character. Several states omit a
`return true` on the tilt/smash branch (`SMASHTURN`, `TILTTURN`, `OTTOTTO*`), letting lower
branches re-evaluate the same frame — a fidelity detail worth noting for a port.

---

## 6. Hitstun ⟷ helpless: the mutual-exclusion answer (ties to #987 / #980)

The most load-bearing finding for pycats. In meleelight, **getting hit is a state transition,
and hitstun magnitude is a scalar** — the two are orthogonal representations, but the *state*
is single-slot, so **a hit and helpless cannot coexist**.

Entry site (`hitDetection.js:627-635`, `executeRegularHit`), verbatim:
```js
player[v].hit.hitstun = getHitstun(player[v].hit.knockback);   // scalar magnitude

if (jabReset) {
  actionStates[characterSelections[v]].DOWNDAMAGE.init(v,input);
} else if (player[v].hit.knockback >= 80 || isThrow) {
  actionStates[characterSelections[v]].DAMAGEFLYN.init(v,input, !isThrow);
} else {
  actionStates[characterSelections[v]].DAMAGEN2.init(v,input);
}
```
`getHitstun` is pure (`hitDetection.js:998-1003`): `return Math.floor(knockback * .4);`.
Each `DAMAGE*.init` **hard-assigns** the state with **no guard on the prior state**, e.g.
`DAMAGEN2.js:24-25`: `player[p].actionState = "DAMAGEN2";`. There is no
`if (actionState != "FALLSPECIAL")` anywhere in the resolution path — the only branch keys
are grab-state, `jabReset`, and knockback magnitude. **So a hit landed on a helpless
(FALLSPECIAL) fighter overwrites FALLSPECIAL with DAMAGEN2/DAMAGEFLYN.** Hitstun and helpless
are mutually exclusive; a hit always wins.

This is the Tier-2 primary confirmation of the canon claim that #987 extracted and that #980
recorded as divergence #2 / #990's C1: **canon = mutually-exclusive states; pycats = overlap**
(pycats keeps the chart in `helpless` and sets a separate `hurt_timer`). Nothing here changes
the pycats verdict — it *grounds* it at the source.

Two mechanics that ride the **scalar** (not the state), relevant to a C1 fix:
- **Ledge-grab gate** — `dealWithLedges` requires `hit.hitstun <= 0` (§2.5); hitstun
  suppresses ledge grab independent of the fall-state.
- **Landing** — `land()` sets `hit.hitstun = 0` and `DAMAGE*.land` only resolves once
  `hitstun<=0`; landing mid-hitstun is a no-op.
- **Jump exit** — DAMAGE* exits reuse the normal double-jump check; jumps are **not**
  force-restored by hitstun ending (only `land()`/ledge/respawn reset the counter). This
  refines #980's "flinch frees an unspent jump": in meleelight the jump isn't *granted* by the
  hit — the hit just returns you to an actionable air state (DAMAGEFALL) where a still-unspent
  double jump is usable.

---

## 7. What this feeds downstream

- **#1010 (architecture: general vs per-character vs hybrid):** §3's 3-tier taxonomy is the
  meleelight data point — the engine states are a fully shared topology; character identity is
  frame-data + a few scripted arrays + leaf attack/special/throw/getup nodes. meleelight *is*
  the "one general chart + per-character injection" design. (Evidence only; #1010 decides.)
- **#1009 (epic synthesis):** this is child 1 of 4. The Melee/Brawl/PM children (Tier-1
  disassembly) will confirm/correct: (a) whether the hit-overwrites-helpless rule is
  identical in Brawl/PM (expected yes — #988 is the open Tier-1 spike), (b) the exact
  FALLSPECIAL duration and air-dodge frame count per game (meleelight's 49 is Melee-tuned;
  PM air-dodge differs), (c) multi-jump handling (meleelight gates on `charAttributes.multiJump
  && jumpsUsed<5` — relevant to Birky).
- **Open cross-checks for later children:** the turbo IASA layer is Melee-mode-specific (not
  baseline); the `WALLTECHJUMP` framesData inconsistency is a meleelight quirk, not canon; and
  DI-at-hit is **not** modeled in meleelight's DAMAGE `main` (knockback is physics-carried with
  no per-frame stick read) — a Tier-1 child should confirm whether that's a meleelight
  simplification or faithful.

---

## 8. Method & limits

- **Sources read verbatim (2026-08-01):** all ~80 modules under
  `meleelight/src/characters/shared/moves/`, the dispatch infra
  (`physics/actionStateShortcuts.js`, `physics/physics.js`), the hit resolver
  (`physics/hitDetection.js`), and the character-merge wiring
  (`characters/marth/index.js`, `characters/marth/moves/index.js`). Extraction was fanned
  across 5 parallel readers (grounded / airborne / defense / hitstun / ledge-death-grab) plus a
  direct read of the dispatch backbone; every edge cites a `file:line`.
- **Tier-2 caveat:** meleelight is a faithful *reimplementation*, not Melee itself. Hardcoded
  literals (air-dodge 49f/3.1speed, SMASHTURN `timer>11`, MISSFOOT `timer>26`, FURAFURA
  `stuckTimer=490`) are the reimplementer's values and should be treated as Melee-approximate
  until a Tier-1 child confirms them. Roster is marth(0)/puff(1)/fox(2)/falco(3)/falcon(4);
  only marth/puff/fox have full T3 move sets in-tree.
- **Not in scope / not claimed:** no PM/Brawl values (those are the Tier-1 children #1009.2-4),
  no pycats mapping or changes, no architecture decision (#1010).

## 9. References
Epic **#1009** · architecture-options **#1010** · hitstun/helpless overlap **#987**
(FALLSPECIAL/DAMAGE swap first extracted) · up-B/helpless canon **#980** (divergences #1/#2) ·
PM Tier-1 confirmation spike **#988** · ADR queue **#990** (C1) · meleelight engine **#616** ·
generic taxonomy scaffold `docs/pm-reference/fighter-states.md` (#160).

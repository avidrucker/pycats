# PM per-action horizontal-movement model — findings (#939)

**Ticket:** #939 (RESEARCH · area:combat) — "Grounded-action 'root' movement model is unverified
against PM." Feeds **#930** Fork 4 (dash-attack momentum/slide) and re-examines **#898**'s
grounded-normal "root" as a *general* movement model.

**Scope:** findings + option space only — **no ratified spec** (memory `research-never-produces-spec`;
#930 / a follow-on ARC decides). Deciding pycats' movement model and authoring any per-move velocity
data are out of scope (downstream DEV).

---

## Sourcing / confidence key

| Tier | Meaning | Used for |
|------|---------|----------|
| **primary-reimpl** | meleelight — a line-level JS reimplementation of the **Melee** engine. Melee→PM is `(inference)` unless a PM datamine confirms. | the per-action velocity/traction *model* + Melee marth exemplar values |
| **repo-grounded** | pycats source read this session (`git show`-able). | what pycats does today |
| **secondary** | SmashWiki / Project+ wiki — a proxy, not PM 3.6 canon (memory `grounded-speeds-projectplus-not-pm36`). | corroboration only |
| **gap** | not answerable from a reachable primary this session. | flagged, never guessed (memory `pm-parity-cite-primary-not-inference`) |

The reachable primary for **engine per-action velocity logic** is **meleelight** (memory
`meleelight-engine-logic-source`) — the per-move brawllib datamine exposes *scripted* subaction data
but not the engine's traction/velocity state machine. meleelight is **Melee**; PM inherits Melee's
movement engine, so the *model* transfers with high confidence, but per-fighter **numbers** for the
pycats archetypes need the **brawllib_rs PM datamine** (labeled gaps below).

---

## TL;DR (the model, in one paragraph)

Melee/PM does **not** move a grounded fighter with a single global friction. It splits horizontal
velocity into **two channels** and applies a **per-character linear `traction`**, plus **per-subaction
velocity scripts** for moves that translate:

- **`cVel.x`** ("character velocity", self/controlled) — set by movement input (walk/dash/run) **and**
  by an attack's authored per-frame velocity script (dash attack). During in-place grounded normals it
  is **not** set from input; it is bled off by `reduceByTraction`.
- **`kVel.x`** (knockback/residual) — decays each grounded frame by the character's `traction`.
- **`traction`** is a **per-character** attribute (Melee fox `0.08` units/f), applied as a **linear
  subtraction** toward 0 (doubled while `|cVel| > maxWalk`), **not** a multiplicative factor.
- **Dash attack** is the exception: it **writes `cVel.x` from a scripted per-frame array** every frame
  (`ATTACKDASH.setVelocities`), so its slide is an **authored velocity curve**, not decayed entry
  momentum.

So #898's "suppress input + decay residual" root is the **correct shape for the jab/tilt/smash family**,
but it is the **wrong model for the dash attack** (which needs its own per-frame velocity), and even for
the tilt family pycats' *global multiplicative* `GROUND_FRICTION` differs from Melee's *per-character
linear* `traction`.

---

## Part A — What PM/Melee does (primary-reimpl: meleelight)

### A1. Two velocity channels + linear per-character traction

`src/physics/physics.js` decays the **residual** channel `kVel.x` every grounded frame by the
character's traction (linear, sign-clamped to 0):

```js
if (Math.abs(player[i].phys.kVel.x) > 0) {
  const oSign = Math.sign(player[i].phys.kVel.x);
  if (player[i].phys.grounded) {
    player[i].phys.kVel.x -= oSign * player[i].charAttributes.traction;   // linear, per-character
  } else {
    player[i].phys.kVel.x -= player[i].phys.kDec.x;
  }
  if (oSign !== Math.sign(player[i].phys.kVel.x)) player[i].phys.kVel.x = 0;
}
```

`traction` is a **per-character `charAttributes`** value — e.g. Melee fox `traction : 0.08`
(`src/characters/fox/attributes.js`). It is **not** a global constant.

### A2. The controlled channel during grounded normals — `reduceByTraction`

`src/physics/actionStateShortcuts.js::reduceByTraction(p, applyDouble)` bleeds `cVel.x` toward 0 by
`traction` (doubled above walk speed), sign-clamped:

```js
export function reduceByTraction (p, applyDouble){
  if (player[p].phys.cVel.x > 0){
    if (applyDouble && player[p].phys.cVel.x > player[p].charAttributes.maxWalk)
      player[p].phys.cVel.x -= player[p].charAttributes.traction * 2;   // 2× above walk
    else
      player[p].phys.cVel.x -= player[p].charAttributes.traction;
    if (player[p].phys.cVel.x < 0) player[p].phys.cVel.x = 0;
  } else { /* mirror for negative */ }
}
```

**Every grounded normal calls this and sets `cVel` from nothing else** — confirmed by reading marth's
`JAB1`, `FORWARDTILT`, `DOWNTILT`, `UPTILT`, `FORWARDSMASH`, `UPSMASH`, `DOWNSMASH` (all call
`reduceByTraction(p, true)` in `main`, none read held stick into `cVel`). Held left/right is **not**
applied as walk speed during the move — it only registers via the state's `interrupt()` for the *next*
action. `RUNBRAKE.js` (the run-skid) likewise just calls `reduceByTraction(p, true)` until it times out
to `WAIT`. **This is exactly pycats #898's "suppress input, let momentum bleed off" — same shape.**

### A3. The dash attack — an authored per-frame velocity curve (the exception)

`src/characters/marth/moves/ATTACKDASH.js` does **not** call `reduceByTraction`. It writes `cVel.x`
from a **49-frame authored array** each frame:

```js
setVelocities: [0.755, 1.962, 2.714, 3.010, 2.849, 2.232, 1.184, 0.542, 0.704, 1.325, 1.487,
                1.079, 0.666, 0.631, ... , 0.011, -0.783, -0.783, 0, 0, 0.001, 0.001, 0],
main: function (p, input) {
  player[p].timer++;
  if (!marth.ATTACKDASH.interrupt(p, input)) {
    player[p].phys.cVel.x = marth.ATTACKDASH.setVelocities[player[p].timer - 1] * player[p].phys.face;
    ...
```

Shape of marth's curve (units/frame, forward = +): ramp **0.755 → peak 3.010 (f4)**, decay to ~0.54
(f8), a **second hump ~1.49 (f11)**, long taper toward 0, then **two braking frames −0.783 (f43–44)**,
settle 0. So the dash-attack slide is a **scripted subaction self-velocity**, per-character, authored
frame-by-frame — **not** decayed dash momentum and **not** a friction product. (For scale only, not a
pycats value: marth's `3.010` units/f × pycats `PX_PER_UNIT 5.4` ≈ **16 px/f** peak — comparable to the
air-dodge burst `DODGE_AIR_SPEED 17`. marth is not a cat archetype and this is Melee, so treat purely as
an order-of-magnitude anchor.)

---

## Part B — The five ticket questions, answered

**Q1 — PM's per-action horizontal-velocity model.** *(primary-reimpl)* Per-**subaction velocity
commands** written to `cVel.x` (dash attack) **plus** a **per-character linear `traction`** decaying
both `cVel` (via `reduceByTraction` in in-place normals) and the residual `kVel`. An action's forward
translation comes from **either** its authored velocity script (dash attack) **or** carried-in momentum
decaying by traction (everything else). It is emphatically **not** one global friction.

**Q2 — Which grounded actions carry vs stop.** *(primary-reimpl, Melee marth)*

| Action | Horizontal-velocity handling | Net |
|--------|------------------------------|-----|
| **Dash attack** | `cVel.x = setVelocities[f] * face` each frame (authored curve) | **strong scripted slide**, then two braking frames → 0 |
| **Jab, all tilts, all smashes** | `reduceByTraction(p, true)` each frame; no input read | carried-in momentum **decays linearly by traction (2× above walk)**; ends planted |
| **Run-brake / skid (RUNBRAKE)** | `reduceByTraction(p, true)` until timeout → WAIT | decays run momentum by traction |
| **Grab (from dash — dash grab)** | dash-attack `interrupt` clamps `cVel` to `dMaxV` then `GRAB.init` | carries clamped dash momentum |
| **Knockback residual (`kVel`)** | `kVel.x -= sign·traction` grounded | decays by traction |

No grounded normal **hard-zeros** velocity on entry; they all rely on traction decay. The dash attack is
the only one that **injects** velocity.

**Q3 — Does pycats reproduce this?** *(repo-grounded vs primary-reimpl)* **Partly.**
- pycats today (`entities/fighter_input.py::handle_move` → `core/physics.step_horizontal`): while
  `attack_timer > 0 and on_ground`, held walk input is **suppressed** and `apply_horizontal_friction`
  multiplies `vel.x *= GROUND_FRICTION (0.5)` each frame. **This matches the Melee tilt/jab/smash family
  in *shape*** (suppress input + decay residual).
- **Divergences:** (a) pycats friction is **global multiplicative ×0.5**; Melee is **per-character
  linear traction** (fox 0.08 units/f, doubled above walk) — different decay *curve* and no per-character
  variation. `GROUND_FRICTION` provenance itself records it as a *"deliberate design knob, no PM
  equivalent"* (`combat/provenance.py`), i.e. pycats never claimed parity here. (b) pycats has **no
  authored dash-attack velocity curve** — a dash attack would decay under the same global friction
  instead of following a scripted slide, so **dash-attack translation is not reproduced**.

**Q4 — Is the #898 "root" the right abstraction?** *(analysis over primary-reimpl + repo-grounded)*
- **For in-place normals (jab/tilts/smashes/run-brake): yes, in shape.** "Suppress held input, let
  residual momentum bleed off" is precisely what Melee does via `reduceByTraction`. #898 is a faithful
  *local* model for that family. The only fidelity gaps are the decay *curve* (multiplicative-global vs
  linear-per-character) and the lack of per-character traction.
- **For the dash attack: no.** The dash attack needs its **own per-frame velocity**, which a global
  suppress+friction rule cannot express. So #898 is a correct patch for the family it targeted but is
  **not** a sufficient *general* per-action model — it has no channel for a move that *drives* the
  fighter. `MoveData` already carries a precedent for per-move set-velocity (`recovery_vx`/`recovery_vy`
  for up-B, `combat/data.py`), so a per-move ground-movement field is not architecturally novel.

**Q5 — Dash-attack initial velocity + decay per archetype (direct #930 Fork 4 feed).**
*(primary-reimpl gives the shape + a Melee exemplar; per-archetype numbers are a **gap**)*
- **Shape (high confidence):** a **per-fighter authored per-frame velocity array** (`face`-signed),
  front-loaded with a peak in the first few frames, a small secondary hump, a long taper, and a short
  braking tail. Melee marth exemplar: peak **3.010 units/f (frame 4)**, full 49-frame curve transcribed
  in A3.
- **Per-archetype numbers (nalio/birky/gnok/narz): GAP.** meleelight ships only marth/fox/falco/falcon/
  puff — none are the pycats cat archetypes, and these are Melee values (PM = inference). The true PM
  per-fighter dash-attack velocity curves require the **brawllib_rs PM datamine** of each fighter's
  `AttackDash` subaction velocity commands (memory `brawllib-datamine-env-live`) — a datamine slice, not
  answerable from meleelight. Recommend this rides the **5a** IASA/interrupt datamine (same brawllib
  run reads subaction velocity + IASA) or a dedicated velocity-datamine child.

---

## Part C — Option space for #930 Fork 4 (no decision here)

**The movement-model fork** (how each grounded action translates):

- **Option A — keep #898's global root (status quo).** Suppress input + global multiplicative
  `GROUND_FRICTION` for all grounded normals. *Pro:* zero new data/code; matches the tilt-family shape;
  determinism-friendly. *Con:* no dash-attack slide (Fork 4 unmet); decay curve and per-character
  traction diverge from PM; a dash attack looks like a rooted tilt.
- **Option B — per-move movement field on `MoveData` (full fidelity).** Add an authored per-frame
  ground-velocity curve (mirroring Melee `setVelocities`), and/or a per-move traction, so each action's
  translation is data-driven; keep suppress-input as the "no curve authored" default. *Pro:* reproduces
  dash attack and any future translating move; extends the existing `recovery_vx` precedent. *Con:* most
  data to author (per-fighter curves ← the Q5 datamine gap) and the most code.
- **Option C — hybrid / minimal-for-V1 (recommended shape to put to the human).** Keep suppress+traction
  as the default for in-place normals (A), **add an optional single per-move ground-velocity field** used
  only by translating moves (dash attack) — an initial forward velocity + decay, or a short authored
  array. Meets Fork 4 with one new `MoveData` field and one authored curve per cat, no rework of the
  tilt family. *Con:* still needs the per-archetype datamine (Q5 gap) for real numbers; two code paths.

**A secondary, orthogonal fork** the architect may fold in or defer:
- **Traction fidelity:** replace global multiplicative `GROUND_FRICTION` with a **per-character linear
  traction** (Melee model). Higher parity for *all* grounded decay, but touches every cat's data and
  changes felt deceleration everywhere — a bigger blast radius than the dash-attack question and
  arguably its own ticket. Flag: `GROUND_FRICTION` is already labeled *"no PM equivalent"* provenance, so
  this is a deliberate-divergence-vs-parity call for the human, not a bug.

---

## Gaps (shipped as gaps, not guesses)

1. **Per-archetype dash-attack velocity curves** (nalio/birky/gnok/narz) — need the brawllib_rs PM
   `AttackDash` subaction-velocity datamine; meleelight has no cat archetypes and is Melee. (Q5)
2. **Melee→PM inference on the *model*.** PM inherits Melee's movement engine (high confidence), but no
   PM-specific primary was read this session confirming PM keeps the `cVel`/`kVel`/linear-traction split
   unchanged. Firm against a brawllib_rs / PM-codeset primary before any FOUND-tier number lands.
3. **Per-character traction values for the pycats archetypes** — Melee ships them per fighter; pycats has
   only a global `GROUND_FRICTION`. If the traction-fidelity fork is taken, each cat needs a datamined
   traction value.

---

## Provenance

- **primary-reimpl (Melee):** meleelight `src/physics/physics.js` (kVel traction decay, ll. ~612–620),
  `src/physics/actionStateShortcuts.js::reduceByTraction`, `src/characters/fox/attributes.js`
  (`traction: 0.08`, `maxWalk`), `src/characters/marth/moves/ATTACKDASH.js` (`setVelocities`),
  `.../moves/{JAB1,FORWARDTILT,DOWNTILT,UPTILT,FORWARDSMASH,UPSMASH,DOWNSMASH}.js` (all
  `reduceByTraction`), `src/characters/shared/moves/RUNBRAKE.js`.
- **repo-grounded (pycats):** `entities/fighter_input.py::handle_move` (#898 root),
  `core/physics.py::apply_horizontal_friction`, `config/physics.py::GROUND_FRICTION`,
  `combat/provenance.py::GROUND_FRICTION` ("no PM equivalent"), `combat/data.py::MoveData`
  (`recovery_vx`/`recovery_vy` precedent; no ground-movement field).
- **secondary:** SmashWiki traction / dash-attack (proxy; not transcribed as values here — the
  primary-reimpl was reachable and authoritative for the model).

## Cross-refs

#930 (architect — Fork 4 consumer) · #898 (the shipped grounded-normal root) · #937 (sibling: input
precedence) · #948 (dash-attack research epic) · 5a (IASA/interrupt datamine — natural home for the Q5
velocity datamine) · #388 (walk/dash/run epic) · #813/#814 (dash/run speed provenance).

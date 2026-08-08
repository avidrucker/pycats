# Fast-fall mechanics — activation, fall-speed effect, per-state availability, canon values — findings (#1069)

**Ticket:** #1069 (research · `area:combat` / `combat:physics` · **v1**) · first child of the
fast-fall V1 epic **#1068** (ruled in #1064 Q3).
**Questions:** (1) **Activation** — down-flick vs hold-down; timing/threshold; once-per-airtime or
re-triggerable? (2) **Fall-speed effect** — multiply the fall speed, or swap to a distinct
`fastFallV`; canon per-fighter numbers? (3) **Per-state availability** — which airborne states allow
fast-fall; specifically is it available *in* helpless / special-fall? (4) **Interactions** —
fast-fall vs hitstun / tumble, vs jump-squat, vs the existing global `MAX_FALL_SPEED` cap.
**Status:** all four answered. Engine *model* (activation, effect, per-state, once-per-airtime,
reset) confirmed from a **[SECONDARY]** faithful Melee reimplementation (meleelight); the **canon
numeric values** are **[SECONDARY]** (meleelight = SmashWiki Melee units) for the Melee cast and
**[TIER-3]** (SmashWiki PM) for PM Mario, both **inference** for the PM cast until the Tier-1 spike.
**Tier-1 (DOL / `.rel` disassembly) is deferred to #988 and is NOT covered here** — see *Blocked /
deferred source* below. **Research only — reports findings + the option space for the ARC child; it
does not decide the spec** (RULES → "research never produces the spec"). Any change is a follow-on
ARC/decision ticket with the human.

Confidence tiers used below:
- `[SECONDARY]` — meleelight (`~/Documents/Study/JavaScript/meleelight`), a faithful Melee
  reimplementation in JS. Not the ROM; the ticket's **Tier-2**.
- `[TIER-3]` — SmashWiki prose / value tables (the ticket's **Tier-3**).
- `[IN-REPO]` — current pycats source (the baseline the ARC child would change).
- `[INFERENCE]` — PM inheritance / reasoning, explicitly labelled, **not** confirmation.
- `[TIER-1 PENDING #988]` — would need DOL / `.rel` disasm; not gathered here.

---

## Per-question answer table

| # | Question | Answer (short) | Strongest evidence |
|---|----------|----------------|--------------------|
| 1 | Activation | **Down-flick** — a fresh downward stick push past a threshold, detected against a recently-neutral stick; **once per airtime** (a `fastfalled` flag, reset on landing). Not hold-down. | `[SECONDARY]` meleelight `fastfall` |
| 2 | Fall-speed effect | **Swap**, not multiply — velocity is *set* directly to a per-fighter `fastFallV` (which is `> terminalV`), not scaled off gravity/terminal. | `[SECONDARY]` meleelight `fastfall` |
| 3 | Per-state availability | Available from **most airborne states incl. special-fall/helpless (`FALLSPECIAL`) and post-tumble `DAMAGEFALL`**; **NOT** during active hitstun (`DAMAGEN2`/`DAMAGEFLYN`/…), grounded states (jump-squat `KNEEBEND`), `LANDINGFALLSPECIAL`, or `SHIELDBREAKFALL`. | `[SECONDARY]` meleelight call-site census |
| 4 | Interactions | Gated behind `!fastfalled` + a downward-velocity guard; no hitstun access (state gate); jump-squat is grounded so N/A; **pycats today has no fast-fall and a single `MAX_FALL_SPEED` cap** that already sits at ~PM-Mario-fast-fall, so a faithful split lowers the *base* rather than raising the peak. | `[SECONDARY]` + `[IN-REPO]` |

---

## Q1 — Activation

**Answer: down-flick, once per airtime. `[SECONDARY]`**

meleelight `fastfall` (`src/physics/actionStateShortcuts.js`, `fastfall` function):

```js
export function fastfall (p,input){
  if (!player[p].phys.fastfalled){
    player[p].phys.cVel.y -= player[p].charAttributes.gravity;
    if (player[p].phys.cVel.y < -player[p].charAttributes.terminalV) {
      player[p].phys.cVel.y = -player[p].charAttributes.terminalV;
    }
    if (input[p][0].lsY < -0.65 && input[p][3].lsY > -0.1 && player[p].phys.cVel.y < 0) {
      sounds.fastfall.play();
      player[p].phys.fastfalled = true;
      player[p].phys.cVel.y = -player[p].charAttributes.fastFallV;
    }
  }
}
```

(`cVel.y < 0` = moving downward — meleelight's y-axis is up-positive, so gravity/terminal/fastfall
are all applied as negative y.)

- **Down-flick, not hold.** The trigger is `input[p][0].lsY < -0.65` (current frame's stick-Y pushed
  down past **0.65**) **AND** `input[p][3].lsY > -0.1` (3 frames ago the stick was **near neutral**).
  That "was-neutral-then-down within the last 3 frames" pattern is a **flick**, not a sustained hold —
  a hold would have `input[p][3].lsY` already deep-negative and so would *fail* the second clause.
  Threshold: **|lsY| > 0.65** to arm, coming from a **> -0.1** (near-neutral) reading 3 frames prior.
- **Only while already descending.** The `cVel.y < 0` guard means you can only fast-fall once you are
  moving downward (past the jump apex), not on the way up.
- **Once per airtime.** The whole body is guarded by `!fastfalled`; on trigger, `fastfalled = true`.
  It is reset **only on landing** — meleelight `physics.js` land handler sets
  `player[i].phys.grounded = true; player[i].phys.jumpsUsed = 0; player[i].phys.fastfalled = false;`.
  So fast-fall is **not re-triggerable** within a single airborne period, even across an air-jump.

**PM note `[INFERENCE]`:** PM inherits Melee's down-flick fast-fall activation for the Melee-origin
cast; the exact threshold/flick-window are **assumed** equal pending `[TIER-1 PENDING #988]`.

---

## Q2 — Fall-speed effect + canon numbers

**Answer: swap to a distinct per-fighter `fastFallV` (> `terminalV`), not a multiplier. `[SECONDARY]`**

On trigger the code does `player[p].phys.cVel.y = -player[p].charAttributes.fastFallV` — an
**instantaneous set** to the fighter's `fastFallV`, replacing whatever downward velocity had
accumulated (which was clamped to `terminalV`). Because `fastFallV > terminalV` for every fighter, the
set is always a speed **increase**. There is no gravity-multiplier and no separate fast-fall
acceleration curve — the new terminal *is* `fastFallV`, held flat for the rest of the fall.

**Canon values `[SECONDARY]` (meleelight = SmashWiki Melee units):**

| Fighter | `gravity` | `terminalV` (normal fall) | `fastFallV` (fast fall) | ff ÷ normal |
|---------|-----------|---------------------------|-------------------------|-------------|
| Fox     | 0.23      | 2.8                       | 3.4                     | 1.21×       |
| Falco   | 0.17      | 3.1                       | 3.5                     | 1.13×       |
| Falcon  | 0.13      | 2.9                       | 3.5                     | 1.21×       |
| Marth   | 0.085     | 2.2                       | 2.5                     | 1.14×       |
| Puff    | 0.064     | 1.3                       | 1.6                     | 1.23×       |

Source: each `charAttributes` block — `src/characters/{fox,falco,falcon}/attributes.js`,
`src/characters/marth/marthAttributes.js`, `src/characters/puff/puffAttributes.js`. The ratio is
**per-fighter, ~1.1–1.25×**, i.e. NOT a shared global multiplier — which is why the swap-to-`fastFallV`
model matters (a single multiplier could not reproduce these).

**PM Mario `[TIER-3]` / `[IN-REPO]`:** pycats' own `combat/provenance.py` (the `MAX_FALL_SPEED`
Provenance entry) already cites SmashWiki PM Mario: **base fall 1.7 u/f, fast-fall 2.3 u/f** (ratio
~1.35×), sourced `SmashWiki:Mario_(PM)`, #120. So PM fast-fall is likewise a base→fast-fall **swap**
to a distinct value, and PM Mario's numbers differ from Melee Mario's — **PM has its own per-fighter
table**, which the ARC/DEV children will need per cat. Treat all PM per-fighter values as
`[TIER-3]`/`[INFERENCE]` until `[TIER-1 PENDING #988]`.

---

## Q3 — Per-state availability

**Answer: available from most airborne states — including special-fall / helpless (`FALLSPECIAL`)
and post-tumble `DAMAGEFALL` — but NOT during active hitstun, grounded states, landing lag, or
shield-break fall. `[SECONDARY]`**

meleelight wires fast-fall by **calling `fastfall(p,input)` from inside each action-state's `main`**.
So a state "allows fast-fall" iff it calls the shortcut. Census of the shared states
(`src/characters/shared/moves/`):

| State | Calls `fastfall`? | Meaning |
|-------|-------------------|---------|
| `FALL` (normal fall) | ✅ | yes |
| `FALLAERIAL` (fall after aerial) | ✅ | yes |
| **`FALLSPECIAL` (special-fall / helpless)** | **✅** | **yes — confirms #1061 §4.3** |
| **`DAMAGEFALL` (tumble → fall after knockback)** | **✅** | **yes** |
| all aerials / air-jumps / air-dodge (`ESCAPEAIR`) / up-B launch / passes / wall-jumps | ✅ | yes |
| `DAMAGEN2`, `DAMAGEFLYN`, `DOWNDAMAGE`, `CAPTUREDAMAGE`, `WALLDAMAGE` (**active hitstun**) | ❌ | **no** |
| `KNEEBEND` (**jump-squat**, grounded) | ❌ | no (grounded — see Q4) |
| `LANDINGFALLSPECIAL` (special-fall **landing lag**) | ❌ | no |
| `SHIELDBREAKFALL` | ❌ | no |

**The special-fall answer (the ticket's headline Q3):** `FALLSPECIAL.main` explicitly calls
`fastfall(p,input)` (then `airDrift`). So in meleelight you **can** fast-fall out of helpless /
special-fall. This is the counterintuitive behavior flagged in #1061 §4.3.

**Caveats:**
- "State calls the shortcut" only means fast-fall is *reachable* there; it still requires the Q1
  down-flick + `!fastfalled` + descending guard to actually fire.
- **`[TIER-1 PENDING #988]`:** whether retail PM special-fall truly permits fast-fall is exactly the
  Tier-1 confirmation #988 is scoped to settle — meleelight is `[SECONDARY]`, and this is the single
  most surprising claim in this doc, so **do not ship it as canon without #988**.

---

## Q4 — Interactions

**vs hitstun / tumble `[SECONDARY]`:** No fast-fall during **active hitstun** — the hitstun states
(`DAMAGEN2`/`DAMAGEFLYN`/`DOWNDAMAGE`/`CAPTUREDAMAGE`/`WALLDAMAGE`) do not call the shortcut. Fast-fall
only becomes available once knockback resolves into the **`DAMAGEFALL`** tumble-fall state. So the
gate is entirely by *which state you are in*, plus the per-call `!fastfalled` + downward-velocity
guard.

**vs jump-squat `[SECONDARY]`:** N/A — jump-squat (`KNEEBEND`) is a **grounded** state (0 `fastfall`
calls). Fast-fall is a purely airborne mechanic; you cannot arm it before leaving the ground, and the
`fastfalled` flag is cleared on every landing.

**vs the global `MAX_FALL_SPEED` cap `[IN-REPO]` — the important one for pycats:**
- Today pycats has **no fast-fall at all**. `pycats/entities/player.py` carries only a TODO:
  *"implement fast fall by holding down which will cause the player to fall faster"* — note this TODO
  says **hold-down**, which **contradicts** the meleelight **down-flick** model (Q1). That
  hold-vs-flick discrepancy is a real decision for the ARC child, not a settled fact.
- Falling is a single clamp: `pycats/core/physics.py::apply_gravity` does
  `vel.y = min(vel.y + gravity, max_fall_speed)` — one terminal, no base/fast split.
- `pycats/config/physics.py` sets `MAX_FALL_SPEED = 13` (px/frame). `combat/provenance.py` documents
  this as a **known DIVERGENCE**: *"pycats uses a single global fall speed ~= PM Mario fast-fall
  2.3 u/f; the Melee/PM base 1.7 / fast-fall 2.3 split is not modelled (SmashWiki:Mario_(PM); #120)."*
  In other words the current single cap already sits at **≈ the fast-fall value**, so a faithful
  base/fast-fall split would **lower the normal-fall base**, not raise the fast-fall peak — otherwise
  every fighter's *normal* fall gets faster than intended. The ARC child must decide the base:fast
  ratio against the shipped `MAX_FALL_SPEED`, and mind `KNOCKDOWN_VY_THRESHOLD = 8.0` (a downward-speed
  gate in `config/physics.py`) which fast-fall velocities would cross.

---

## Option space for the ARC child (#1068 → ARC)

Not decisions — the choices the design ticket must make, with the faithful default noted.

1. **Activation input.** (a) meleelight-faithful **down-flick** (fresh down past ~0.65 from a
   near-neutral within ~3 frames); (b) the current TODO's **hold-down**; (c) hybrid. Faithful = (a);
   (b) is simpler but diverges from Melee/PM feel and would need its own basis.
2. **Effect model.** (a) **swap** current `vel.y` to a per-fighter `fast_fall_speed` (faithful);
   (b) multiply the existing `max_fall_speed`. Faithful = (a); note (b) cannot reproduce the
   per-fighter ~1.1–1.25× spread.
3. **Base vs cap re-basing.** Since `MAX_FALL_SPEED = 13` already ≈ PM Mario fast-fall, decide whether
   to (a) **lower each cat's normal fall** and keep 13-ish as the fast-fall peak, or (b) keep normal
   as-is and add a higher fast-fall (raising peak fall speed beyond today). (a) is the faithful
   split; (b) changes existing feel.
4. **Per-state availability.** (a) faithful — allow in `FALLSPECIAL`/helpless + `DAMAGEFALL`, block in
   active hitstun / grounded / landing-lag / shield-break; (b) block in helpless too (simpler, less
   faithful). **(a) depends on the #988 Tier-1 confirmation for the helpless case.**
5. **Once-per-airtime.** Faithful = a `fast_fell` flag reset on landing (mirror meleelight's
   `fastfalled`). Decide whether an air-jump resets it (Melee: **no**).
6. **Per-fighter values.** Author a `fast_fall_speed` per cat (like the per-fighter meleelight table),
   or a single shared value. Faithful = per-fighter; needs the PM per-cat numbers (`[TIER-1 PENDING
   #988]` / `[TIER-3]`).

---

## Sources & evidence ladder

- **`[SECONDARY]` meleelight** (`~/Documents/Study/JavaScript/meleelight`, a faithful Melee JS
  reimplementation — the ticket's Tier-2):
  - `src/physics/actionStateShortcuts.js` → `fastfall` (activation + effect + guards).
  - `src/physics/physics.js` land handler (`fastfalled = false` reset → once-per-airtime).
  - `src/characters/{fox,falco,falcon}/attributes.js`,
    `src/characters/marth/marthAttributes.js`, `src/characters/puff/puffAttributes.js`
    (`gravity` / `terminalV` / `fastFallV`).
  - `src/characters/shared/moves/*.js` + `src/characters/*/moves/*.js` (per-state `fastfall(p,input)`
    call-site census, incl. `FALLSPECIAL`, `DAMAGEFALL`, and the hitstun states that omit it).
- **`[TIER-3]` SmashWiki** — *Mario (PM)* fall / fast-fall 1.7 / 2.3 u/f, as **already cited in-repo**
  by `combat/provenance.py` (`MAX_FALL_SPEED` entry, #120).
- **`[IN-REPO]` pycats** — `core/physics.py::apply_gravity`, `config/physics.py`
  (`MAX_FALL_SPEED = 13`, `KNOCKDOWN_VY_THRESHOLD = 8.0`), `combat/provenance.py` (`MAX_FALL_SPEED`
  DIVERGENCE), `entities/player.py` (the hold-down TODO).

### Blocked / deferred source
- **Tier-1 (DOL / `ft_*.rel` disassembly) — NOT gathered here; scoped to #988.** The retail-code
  confirmations that this doc could not reach on its own: (a) exact PM down-flick threshold/window;
  (b) whether retail PM special-fall/helpless truly permits fast-fall (Q3's surprising claim); (c) the
  PM per-fighter `fastFallV`/base table. Everything PM in this doc is `[SECONDARY]`/`[TIER-3]`/
  `[INFERENCE]` until #988 lands. No fetch was attempted; this is a deliberate scope boundary, not a
  blocked-access failure.

## Cross-refs
Parent **#1068** (fast-fall V1 epic) · **#1064** Q3 (the ruling that scoped the epic) · **#1061**
findings (§4.3 special-fall fast-fall flag) · **#120** / **#261** (prior fast-fall threads) · **#988**
(PM Tier-1 spike — supplies the confirmations deferred above).

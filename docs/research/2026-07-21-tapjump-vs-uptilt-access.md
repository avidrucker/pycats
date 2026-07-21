# Tap-jump vs up-tilt / up-air access — how PM 3.6 / Melee resolve Up + A, and pycats' options

**Ticket:** #864 (research · `area:combat`) · consumes #845 (`docs/research/2026-07-21-uptilt-multikey-input-findings.md`)
**Date:** 2026-07-21 · **Agent:** banana
**Feeds:** #865 (decision, blocked on this doc) → downstream DEV

**Question:** With tap-jump ON, how does a real PM 3.6 / Melee player get a grounded **up-tilt** (rather than a jump) and an airborne **up-air** (rather than a double-jump when a jump is banked)? Does PM expose a tap-jump toggle? Does jumpsquat buffer an A into a tilt? And what are pycats' options?

**Answer in one line:** In Melee/PM the stick's **jump input is a rising edge** (a fast flick up), not "up is held" — so once the stick is *held* up, pressing A yields the up-tilt/up-air, and the jump doesn't re-fire. pycats reproduces this for the grounded case (hold-Up-then-A tilts) but has no analog rising-edge notion and, more importantly, applies the same jump-eats-fresh-Up branch **airborne**, so Up+A with a jump banked double-jumps. PM/Brawl also expose a **tap-jump OFF** control option that removes the ambiguity entirely — the single most common real-world answer.

---

## Sources & confidence

| Source | Kind | Used for |
|---|---|---|
| SmashWiki, *Tap jump* (ssbwiki.com/Tap_jump) | primary (canonical wiki) | what tap jump is; the up-tilt/up-air interference; toggle exists Brawl-onward |
| meleelight (`~/Documents/Study/JavaScript/meleelight`, #616) | primary (Melee-accurate engine reimplementation; Melee-inherited PM globals) | the exact input→action resolution: rising-edge jump, tilt/aerial checks, jumpsquat interrupts, the `tapJumpOff` gate |
| PM 3.6 = Brawl mod | **inference** (labeled) | that the Brawl-onward tap-jump toggle carries into PM 3.6 — not a verbatim PM primary; see the gap note |

Per [[pm-parity-cite-primary-not-inference]]: meleelight is Melee, and PM 3.6 inherits Melee's action-state/input engine, so its input-resolution logic is a strong primary for the *engine mechanic*. The one PM-3.6-specific claim resting on inference (the toggle) is flagged below, not asserted as canon.

## Q1 — PM/Melee reality: getting up-tilt (grounded) and up-air (airborne) with tap-jump ON

### The load-bearing fact: the stick's jump input is a RISING EDGE

meleelight `checkForJump` (grounded, `src/physics/actionStateShortcuts.js`):

```js
export function checkForJump (p,input){
  if ((input[p][0].x && !input[p][1].x) || (input[p][0].y && !input[p][1].y)) {
    return [true, 0];                                        // jump BUTTON (X/Y), fresh press
  } else if (gameSettings["tapJumpOffp" + (p + 1)] == false   // tap-jump ON
             && (input[p][0].lsY > 0.66 && input[p][3].lsY < 0.2)) {  // stick Y rose from <0.2 (3 frames ago) to >0.66 (now)
    return [true, 1];
  } else { return [false, false]; }
}
```

The tap-jump branch fires only when the stick **crossed** from `lsY < 0.2` (three frames ago, `input[p][3]`) to `lsY > 0.66` (this frame) — a fast upward flick. A stick that is merely **held** up (already past the top, no fresh crossing) returns `[false, false]`.

`WAIT.interrupt` (standing) checks these in order — **jump before tilts**:

```js
const s = checkForSmashes(p,input);
const j = checkForJump(p,input);
...
if (j[0] && !player[p].inCSS){ KNEEBEND.init(...); return true; }   // jump wins if the rising edge fired
...
else if (t[0]){ [t[1]].init(...); return true; }                    // else tilts (UPTILT)
```

`checkForTilts` returns `UPTILT` for a fresh A-press with `lsY > 0.3`. So the grounded up-tilt recipe with tap-jump ON is: **hold the stick up (past the flick), then press A** — `checkForJump` sees no rising edge, falls through, `checkForTilts` fires UPTILT. A simultaneous fast-flick-up + A **jumps** (the rising edge wins in the ordering). This is the canonical "tilt out of a held-up stick" technique.

> SmashWiki, *Tap jump*: "it can lead to accidental jumps when attempting to perform up tilts or up aerials" — the exact failure this ticket is about.

### Airborne: c-stick, and aerials are checked before the double-jump

Airborne, the unambiguous aerial input is the **c-stick** — `checkForAerials` reads `csY`/`csX` and returns `ATTACKAIRU` for `csY >= 0.3` with no jump involved at all. With the *control* stick + A, meleelight's airborne interrupt (`turboAirborneInterrupt`) checks **aerials first, double-jump last**:

```js
var a = checkForAerials(p,input);
if (a[0] && a[1] != player[p].actionState) { ... [a[1]].init(...); return true; }   // aerial first
else if (airdodge) { ... }
else if (((fresh X/Y) || (lsY > 0.7 && input[p][1].lsY <= 0.7))  // then double-jump (rising edge)
         && (!doubleJumped || multiJump)) { ... }
```

So airborne, a **held-up + A → up-air**; the double-jump only fires on a fresh X/Y press or a stick **rising edge** with no aerial input. The up-air stays accessible with a jump banked. `checkForDoubleJump` confirms the air rising-edge (`lsY > 0.69 && input[p][1].lsY <= 0.69`).

**Confidence:** FOUND (meleelight primary for the engine logic; SmashWiki primary for the symptom). The rising-edge-jump + held-up-tilt behavior is Melee-canonical and inherited by PM 3.6.

## Q2 — Tap-jump toggle: yes, and it's the common real answer

> SmashWiki, *Tap jump*: "From *Super Smash Bros. Brawl* onward, tapping up to jump can be disabled in the Controls menu." "it can lead to accidental jumps when attempting to perform up tilts or up aerials," which is why "most players prefer disabling Tap Jump."

meleelight models this as a per-player setting `tapJumpOffp1..4` (`src/settings.js`), toggled in its gameplay menu, and consumed in `checkForJump` / `checkForDoubleJump` / `checkForMultiJump`. With tap-jump **OFF**, the stick-jump branch is disabled entirely: `up` on the stick never jumps, so up-tilt (grounded) and up-air (airborne) become trivially accessible via stick-up + A, and only the X/Y jump buttons jump.

- **What OFF changes:** stick-up stops being a jump input; nothing else. Up-smash / up-special out of shield then require the jump *button* (some players keep tap-jump ON precisely to JC-upsmash/up-B out of shield without a button — SmashWiki notes both camps).
- **PM 3.6 specifically:** **[inference]** PM 3.6 is a Brawl mod and inherits Brawl's Controls-menu tap-jump toggle; SmashWiki's "Brawl onward" covers Brawl but does not name PM. **Gap:** no verbatim PM-3.6 primary (in-game controller-config screenshot / PM manual) was pinned here. This is the one claim a reader should treat as inheritance-inference, not canon. Confidence: GUESS→likely. If the decision hinges on it, pin a PM controller-config primary first.

## Q3 — Jumpsquat / buffering: no A→up-tilt conversion

meleelight `KNEEBEND` (jumpsquat) `interrupt`:

```js
if (timer > jumpSquat) { JUMPF/JUMPB.init(...); return true; }         // the jump commits
else if (A fresh && analog trigger held) { GRAB.init(...); }           // JC grab
else if ((A fresh && lsY>=0.8 rising) || (cStick up)) { UPSMASH.init(...); }  // JC up-smash
else if (B fresh && lsY>0.58) { UPSPECIAL.init(...); }                 // JC up-special
```

Once in jumpsquat, an A press converts to an **up-smash** (the jump-cancel up-smash), an up-special, or a grab — **never a grounded up-tilt**. The frame is committed to the jump unless jump-cancelled into one of those. So "press A during jumpsquat to get an up-tilt" is **not** a mechanic; a rising up-air comes from actually leaving the ground and pressing A airborne. (`jumpType` short/full-hop is set by whether the stick stays above `0.67` through jumpsquat — orthogonal to this question.)

**Confidence:** FOUND (meleelight primary).

## pycats today (from #845 + `entities/fighter_input.py :: handle_actions`)

- Discrete keys, no analog stick, **no rising-edge notion**: a *fresh* Up key-press is the jump input. The `handle_actions` jump branch fires on `self._pressed(pressed, "up")` and `return`s before the attack branch.
- **Not gated on `on_ground`** — the same branch spends a **double-jump** airborne whenever `jumps_remaining` is truthy.
- Grounded, this reproduces Melee's *observable* result (hold-Up-then-A tilts; fresh-Up+A jumps) — faithful to tap-jump-ON. Airborne, it diverges: Melee checks aerials before the double-jump, so held-Up+A gives an up-air; pycats fires the double-jump first, swallowing the up-air until `jumps_remaining == 0`.
- **No tap-jump toggle**, **no jumpsquat** (jumps are instantaneous `vel.y = jump_vel`), and the `smash` key is **ground-only** (`ground_smash = _pressed(pressed,"smash") and on_ground`) — pycats has no c-stick-equivalent unambiguous aerial input.

## Q4 — pycats option matrix (each scored against BOTH access paths)

Legend — Grounded u-tilt · Airborne u-air (jump banked) · Faithfulness to PM/Melee · Config surface · Golden/test impact · Tap-jump-user impact.

| Option | Grounded u-tilt | Airborne u-air | Faithful? | Config | Golden/test | Notes |
|---|---|---|---|---|---|---|
| **A. Leave as-is** | Accessible only via hold-Up-then-A | **Still swallowed** while jumps remain | Grounded: yes (tap-jump-ON). Airborne: **no** — Melee checks aerials before DJ | none | none | Does not fix the airborne half at all. Honest "no-op" baseline. |
| **B. Tap-jump toggle** (setting; when off, Up never jumps) | Trivially accessible when OFF | Trivially accessible when OFF | **Most faithful** — mirrors the real PM/Brawl option and how most players actually solve this | one bool setting (+persist, +Options UI row) | New default = keep tap-jump ON → goldens unchanged; OFF path needs its own tests | Matches SmashWiki "most players disable it." Doesn't help a player who *keeps* tap-jump on (they still hold-Up-then-A / need a c-stick). Largest UX surface. |
| **C. Jumpsquat A→u-tilt buffer** | Would fire u-tilt from the jump frame | n/a (grounded only) | **Un-faithful** — in Melee jumpsquat+A is a JC **up-smash**, never an up-tilt (Q3) | none | changes jump-frame semantics; golden risk | Rejected on faithfulness: it invents a mechanic Melee doesn't have and collides with the (future) JC-upsmash. |
| **D. Reorder input priority** (grounded held-Up + fresh-A resolves u-tilt before the jump branch; airborne held-Up + fresh-A resolves u-air before the double-jump branch) | Held-Up+A tilts; fresh-Up alone still jumps | Held-Up+A gives u-air; fresh-Up alone still double-jumps | **Faithful to the airborne ordering** (aerials-before-DJ) and preserves grounded tap-jump-ON feel | none (behavioral) | airborne change can shift sim/goldens where a bot holds Up while attacking | Directly fixes the airborne swallow by matching Melee's aerial-before-double-jump order. Keyboard has no c-stick, so "held-Up + A" is the pycats analog of Melee's held-stick tilt/aerial. Smallest surface that fixes **both**. |
| **E. Separate jump button / c-stick-style attack input** | u-tilt via stick+A once Up isn't the only jump | u-air via a dedicated attack-direction input | Faithful (Melee has X/Y jump + c-stick) | new binding(s) (+Options, +controls legend) | new input path needs tests; goldens unchanged if default bindings unchanged | Biggest input-model change; also the most complete (unblocks up-smash-in-air etc.). Overlaps with making `smash` work airborne. |

### Reading of the matrix (advisory — the ruling is #865's)

- **A alone leaves the airborne up-air broken** — the facet that motivated re-scoping this ticket. It is only defensible as "grounded is faithful, airborne is a known gap we accept for now."
- **B (tap-jump toggle)** is the most PM-faithful and the real-world answer most players use; its cost is UX surface (a setting + Options row) and it doesn't help tap-jump-ON players.
- **D (reorder)** is the smallest change that fixes **both** paths and is faithful to Melee's airborne aerial-before-double-jump ordering; its cost is possible sim/golden shifts where an AI holds Up while attacking.
- **B + D compose** — a toggle for players who want stick-up to stop jumping, plus the reorder so tap-jump-ON players still reach u-air/u-tilt by holding Up. That pairing matches Melee/PM most closely.
- **C is rejected** on faithfulness (jumpsquat+A is a JC up-smash, not a tilt).
- **E** is the largest and most complete, and naturally folds in "make the `smash` key work airborne."

## Deliverable status

This doc answers Q1–Q4 with primary citations (meleelight + SmashWiki), labels the one PM-3.6-specific inference (the toggle), and hands #865 a decision-ready option matrix scored against both the grounded up-tilt and the airborne up-air. **No code changed.**

## Out of scope

Ruling on which option to take (#865). Implementing any change (post-decision DEV). Re-deriving the pycats-side characterization (#845 owns it).

## Refs
#845 (characterized gap) · #865 (decision, consumes this) · `entities/fighter_input.py :: handle_actions` (the un-`on_ground`-gated jump branch) · meleelight `checkForJump`/`checkForTilts`/`checkForAerials`/`KNEEBEND`/`settings.js` (#616) · SmashWiki *Tap jump* · [[meleelight-engine-logic-source]] · [[pm-parity-cite-primary-not-inference]].

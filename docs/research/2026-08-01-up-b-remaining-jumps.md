# Does up-B consume remaining midair jumps, or just lock them? — Melee / Brawl / PM 3.6

**Ticket:** #980 (RESEARCH · `area:combat`) · **Date:** 2026-08-01 · **Agent:** cherry
**Deliverable:** this findings doc. No implementation here — any pycats change is a downstream ticket (see §9).

---

## 1. TL;DR — the canonical rule

Using an up-special (up-B) that induces the **helpless / special-fall** state does **not** consume, remove, or
zero a character's remaining midair jumps. The jumps are **locked out by the state**, not spent: while helpless,
the engine simply offers no jump transition. The midair-jump counter is left untouched and is only reset to full
on **landing**, **grabbing a ledge**, or **respawning** — and access to any *unspent* jumps is restored if the
character is **knocked out of helpless by a hit (flinch)**.

This is **lock, not consume.** It holds identically for single-jump characters (Marth, Fox) and multi-jump
characters (Jigglypuff — and by inheritance Kirby / pycats' Birky, `max_jumps 6`): helpless locks *all* leftover
jumps at once; it does not remove them.

The distinct, often-confused fact: a midair jump you have **already used** (by jumping) is *not* refunded by
getting hit — but that is jump *expenditure by jumping*, not by up-B. Up-B itself expends nothing.

**Direct answer to the originating question** ("does using Up+B use up / remove all a player's remaining jumps?"):
**No.** It locks them behind the helpless state until you land, grab a ledge, respawn, or get hit out of helpless.

---

## 2. Method & sources (local primary + online cross-check)

Per the pycats "cite primary, not inference" rule, the runtime mechanic (a *state-machine* question, not per-move
static data) is grounded in an **engine reimplementation**, then cross-checked against the datamine and the wiki.

| Source | Type | Role here |
|---|---|---|
| **meleelight** (`~/Documents/Study/JavaScript/meleelight`) | Local · Melee engine reimplementation (JS) | **PRIMARY** for the runtime state machine (jump counter, special fall, jump gate) |
| **brawllib_rs** (`~/Documents/Study/Rust/brawllib_rs`) + **pm-data** (PM 3.6 Kirby `.pac`) | Local · Brawl/PM datamine | Confirms the *static* Brawl/PM machinery (action IDs, `num_jumps`) and the **datamine boundary** — it cannot compute the runtime counter |
| **SmashWiki** (ssbwiki.com: *Helpless*, *Special fall*, *Midair jump*, *Up special move*) | Online · community reference | **Labelled proxy / cross-check** — never the sole basis; used to corroborate the engine finding across all games |

The three agree wherever they overlap (see §4 corroboration table).

---

## 3. The canonical rule, with primary evidence

### 3a. meleelight (PRIMARY — Melee engine logic)

Up-B ends in the special-fall action state `FALLSPECIAL`, whose `init` sets only the action name + timer — it
**never touches** the jump counter (`doubleJumped` / `jumpsUsed`):

- `src/characters/marth/moves/UPSPECIAL.js` (Dolphin Slash) → `FALLSPECIAL.init(p, input)` on completion.
- `src/characters/fox/moves/FIREFOXBOUNCE.js` (Firefox) → `FALLSPECIAL.init(p, input)`.
- `src/characters/shared/moves/FALLSPECIAL.js` `init` sets `actionState` + `timer` only.

The crux is the **jump input gate**. Normal fall offers a jump transition, gated by the counter:

```js
// src/characters/shared/moves/FALL.js
else if (checkForDoubleJump(p,input) && (!player[p].phys.doubleJumped
        || (player[p].phys.jumpsUsed < 5 && player[p].charAttributes.multiJump))) {
    ... JUMPAERIALF.init(p,input); return true;
}
```

Special fall has **no jump branch at all** — its entire `interrupt` only loops itself when the timer expires:

```js
// src/characters/shared/moves/FALLSPECIAL.js
interrupt : function(p,input){
    if (player[p].timer > framesData[characterSelections[p]].FALLSPECIAL){
        actionStates[...].FALLSPECIAL.init(p,input); return true;
    } else { return false; }
}
```

So the jump is **locked out by being in `FALLSPECIAL`**, not by counter exhaustion. The counter is reset to fresh
in exactly three places — none of them is "used up-B":

```js
// src/physics/physics.js  land()
player[i].phys.doubleJumped = false;
player[i].phys.jumpsUsed = 0;
// src/characters/shared/moves/CLIFFCATCH.js  (ledge grab)  → same two lines
// src/characters/shared/moves/REBIRTH.js     (respawn)     → same two lines
```

Being hit does not itself reset the counter, but the damage-fall states (`DAMAGEN2`, `DAMAGEFALL`) *permit* a
jump if `doubleJumped` is still false — i.e. an unspent jump survives a flinch and becomes usable again once
you're out of helpless. Multi-jump Jigglypuff (`puffAttributes.js: multiJump: true`, cap hardcoded `jumpsUsed < 5`)
routes through the **same** `FALLSPECIAL`; its leftover jumps are locked identically and `jumpsUsed` is untouched.
(Kirby is not implemented in meleelight; Jigglypuff is the multi-jump exemplar.)

### 3b. SmashWiki (online cross-check)

- *Special fall*: while helpless "characters are unable to take any action, with the exception of grabbing a ledge,
  maneuvering left/right, fastfalling, or climbing a ladder, until they land on the ground or pass a blast line."
  Midair jumps are **not** in the allowed list — "The state doesn't consume jumps — it simply prevents their use
  until special fall ends."
- *Helpless*: helplessness "ends upon landing on the ground or being KO'd, although it also ends if characters
  flinch, allowing them to attack or re-use their triple jump." → unspent jumps survive; a flinch frees them.
- *Midair jump*: "A character's double jump(s) are restored upon landing, grabbing a ledge, being KO'd and
  respawning, or being grabbed by an opposing character." Kirby / Jigglypuff = **5 midair jumps** (all games),
  "no special recovery interactions beyond normal mechanics."

### 3c. brawllib_rs + pm-data (datamine — Brawl/PM, boundary confirmed)

The datamine confirms the **static** Brawl/PM machinery exists but **cannot** compute the runtime counter:

- Action IDs (`src/action_names.rs`): `0x010 => "FallSpecial"`, `0x019 => "LandingFallSpecial"` — the helpless
  airborne state and its landing lag. A subaction ending in these *is* the helpless landing.
- IASA / interruptibility (`src/script_ast/mod.rs`, `src/high_level_fighter.rs`): `AllowInterrupts` (event
  `0x64 0x00`) sets when a move becomes actionable; exposed as `HighLevelSubaction.iasa`.
- Static jump ceiling (`src/sakurai/fighter_data/mod.rs`): `num_jumps: u32` at offset `0x60` — total jumps a
  character has; `air_jump_x_mult` / `air_jump_y_mult` scale midair-jump velocity.
- **Runtime counter is inert in the datamine.** `script_runner.rs` models a `jumps_used: i32` slot
  (`LongtermAccessInt` index `01`, readable by scripts) but **initializes it to 0 and never writes it** — grep of
  `jumps_used` shows only the init and a single read. So *"does the up-B consume/lock the jump"* is **engine
  runtime logic, outside what per-move Brawl/PM data can answer.** The datamine can show a move ends in
  `FallSpecial`/`LandingFallSpecial` and reads `JumpsUsed`; the counter arithmetic lives in the engine.
- pm-data holds raw PM 3.6 binaries (`pf/fighter/kirby/FitKirbyMotionEtc.pac`, `ft_kirby.rel`), no extracted JSON.

---

## 4. Cross-source corroboration

| Claim | meleelight (engine) | SmashWiki (proxy) | brawllib_rs (datamine) |
|---|---|---|---|
| Up-B **does not consume** midair jumps | ✅ `FALLSPECIAL.init` never touches counter | ✅ "doesn't consume jumps" | ◻ out of scope (runtime) — but consistent: move data never mutates `JumpsUsed` |
| Jumps **locked by state**, not by counter | ✅ `FALLSPECIAL.interrupt` has no jump branch | ✅ "prevents their use until special fall ends" | ◻ out of scope; `FallSpecial`/`LandingFallSpecial` actions exist |
| Reset on **landing** | ✅ `physics.js land()` | ✅ | ◻ engine |
| Reset on **ledge grab** | ✅ `CLIFFCATCH.js` | ✅ | ◻ engine |
| Reset on **respawn** / KO | ✅ `REBIRTH.js` | ✅ (+ "being grabbed") | ◻ engine |
| **Flinch** frees an unspent jump | ✅ damage states permit jump if `doubleJumped` false | ✅ "flinch … re-use their triple jump" | ◻ engine |
| Multi-jump chars **no exception** | ✅ Puff → same `FALLSPECIAL` | ✅ Kirby/Jiggs 5 jumps, no special interaction | ✅ `num_jumps` is a static ceiling only |

No contradictions. The one apparent tension — wiki's "double jumps are not given back upon hitstun" vs. "flinch …
re-use their jump" — resolves cleanly: an **already-spent** jump is not refunded by a hit, whereas an **unspent**
jump (helpless was entered without jumping first) survives and is re-enabled when the flinch ends helpless. Up-B
never spends a jump, so up-B → flinch leaves the jump available.

---

## 5. Special-fall vs. non-helpless up-Bs (don't over-generalize)

Most up-Bs induce helpless, but not all — and those that don't leave jumps immediately usable:

- **Jigglypuff's Sing** (up-B): in meleelight, grounded → `WAIT` (actionable); airborne → `FALLSPECIAL`. Wiki:
  Sing "does not put Jigglypuff into a state of helplessness" (it is not a recovery move).
- **Yoshi's up-B (Egg Throw)**: "does not put Yoshi into a state of helplessness."
- Later-game examples (Banjo & Kazooie up-B, Min Min grounded) also skip helplessness.

Takeaway: "up-B ⇒ helpless ⇒ no jumps" is the *common* case, not a universal law. Whether a given move locks jumps
is a property of *whether that move enters special fall*, which the datamine surfaces via the `FallSpecial` /
`LandingFallSpecial` action transition (§3c).

---

## 6. Multi-jump characters (Kirby / Jigglypuff — the Birky case)

Kirby and Jigglypuff have **5 midair jumps** in Melee (SmashWiki; `num_jumps` in the datamine is the Brawl/PM
static ceiling). The recovery interaction is **identical to single-jump characters**: their up-B (Kirby's Final
Cutter; Jigglypuff has no true up-B recovery and relies on its 5 jumps + Pound) routes through the same helpless
state, which locks *all* remaining jumps at once. Being multi-jump does not let them keep tapping jumps mid-helpless,
and up-B does not remove their stock — it is restored in full on land/ledge/respawn.

This is the directly relevant precedent for **Birky** (`max_jumps 6`, PM Kirby archetype): after Final Cutter
(#969), Birky's remaining jumps should be *locked while helpless and restored on landing*, not removed.

---

## 7. Order of operations & jump-refresh points

- **Jump then up-B:** the jump is already spent by jumping; up-B then goes helpless. Net: you spent a jump *and*
  are helpless.
- **Up-B without jumping:** the unspent jump is *locked* while helpless; a flinch out of helpless makes it usable
  again (§4). This is why "save your jump, up-B, then get hit → you still have a jump" works in Melee.
- **Refresh points (full reset of the counter):** landing, ledge grab, respawn/KO, being grabbed (per wiki).
- No up-B in the surveyed set *refreshes* the counter by itself. (Jump-restoring moves exist — Bayonetta's Witch
  Twist, Melee Falcon/Ganon after Falcon Kick / Wizard's Foot — but those are not the recovery-helpless case.)

---

## 8. Project M 3.6 evidentiary posture

There is **no PM-specific primary runtime evidence** available locally: the datamine cannot compute the runtime
counter (§3c), and there is no PM engine reimplementation on hand (meleelight is Melee). PM 3.6 is built on
**Brawl's engine**, which shares Melee's helpless/special-fall lock model; the wiki treats the "locked, not
consumed; restored on land/ledge/KO" behavior as consistent across all pre-Ultimate games. Accordingly the PM 3.6
rule here is **Brawl/Melee-inherited (labelled inference), not a PM primary measurement** — the same evidentiary
posture pycats uses elsewhere for engine-globals the per-move datamine can't reach (cf. the meleelight
engine-logic basis). If a PM-primary confirmation is ever required, it needs a PM engine reimplementation or a
DOL/`ft_kirby.rel` disassembly, which is out of scope for this ticket.

---

## 9. pycats implication

**pycats' current model matches canon on the core rule.** The jump input gate blocks jumping while helpless, and
up-B never decrements the counter:

```python
# pycats/entities/fighter_input.py  (jump seam)
if (jump_pressed and not wants_up_special and not attack_wins_over_jump
        and p.fighter.jumps_remaining
        and p.state not in ("dodge", "hurt", "stun", "helpless")):  # helpless locks jump (#184)
    p.fighter.vel.y = p.fighter.jump_vel
    p.fighter.jumps_remaining -= 1        # decrement happens ONLY on an actual jump
```

```python
# pycats/entities/fighter.py  (landing)
self.jumps_remaining = self.max_jumps     # reset jumps when landing
self.air_dodge_active = False             # landing ends helpless/special-fall (#184)
self.recovery_active = False              # landing ends up-B recovery/helpless (#578)
```

- ✅ **Lock, not consume:** up-B routes to helpless via `recovery_active`; the gate blocks the jump; the counter is
  untouched. Matches meleelight `FALLSPECIAL`.
- ✅ **Reset on landing:** `jumps_remaining = max_jumps` on land. Matches `physics.js land()`.
- ✅ **Reset on respawn:** `respawn` clears both flags + resets jumps (`fighter.py`). Matches `REBIRTH.js`.

**Candidate divergences (to VERIFY downstream, not asserted as bugs here):**

1. **Ledge grab does not reset jumps / clear helpless.** The grab moment
   (`Player` ledge-catch in `pycats/entities/player.py`, where `grabbed_ledge` is set) zeroes velocity and sets
   intangibility but does **not** set `jumps_remaining = max_jumps` nor clear `recovery_active` /
   `air_dodge_active`. Canon (meleelight `CLIFFCATCH`, wiki) restores jumps on ledge grab. Whether this is
   observable in pycats depends on how ledge-getup/ledge-jump reads the counter — needs a repro.
2. **A hit does not end helpless (flinch → freed jump) — PROVEN from the built chart, not merely inferred.** The
   `helpless` state has **only two exits, both `on_ground`** (`landing_lag` / `idle`); it has no `hurt_timer` /
   `stun_timer` exit, and the `action` parent has no `force_hurt` (only `force_ko/idle/prone/ledge_grab/smash_charge`).
   So a non-KO hit while helpless leaves the fighter **in helpless** until landing — the opposite of canon, where a
   flinch forces the victim into a damage state (meleelight `hitDetection.js` → `DAMAGEN2.init`/`DAMAGEFLYN.init`)
   and re-permits an unspent jump. See the chart dump in the appendix (§12) for the exact exits. (KO still leaves
   helpless via `force_ko`; ledge-grab leaves it via `force_ledge_grab`, which `_try_ledge_grab` fires without a
   state gate.) This is the **one concrete, proven pycats/canon divergence** in this whole investigation.

Divergence #1 is a model gap in the "restore" direction (pycats never over-restores or consumes); divergence #2 is
a proven state-machine difference. Neither the size of #1's effect nor #2's exact runtime consequence is a *bug*
verdict yet — each needs a reproduction (and #2 also needs the hitstun-vs-helpless overlap question resolved, filed
separately) before any DEV work, per the repro/spec-first rule.

## 10. Suggested downstream follow-ups (NOT filed — one at a time, human-gated)

- A `research`/repro ticket to reproduce candidate divergence #1 (ledge-grab jump reset) and #2 (flinch frees an
  unspent jump) against the pycats state machine, before deciding whether either warrants a fix.
- If reproduced, a DEV ticket each: reset `jumps_remaining` + clear helpless flags on ledge grab; clear helpless
  flags on `receive_hit` so a flinch frees an unspent jump.

---

## 11. Evidence tiers (how much to trust each claim)

| Tier | Source | Consulted? | Covers |
|---|---|---|---|
| 1 — ground truth | Actual game disassembly (Melee DOL / PM `ft_*.rel`) | **No** — not available locally in usable form | would settle PM 3.6 exactly |
| 2 — faithful reimpl | **meleelight** (Melee engine, JS) — files read directly this session | **Yes** | Melee runtime state machine |
| 3 — documentation | **SmashWiki** (verbatim quotes below) | **Yes** | cross-check, all games (proxy) |
| static only | **brawllib_rs** datamine + pm-data | **Yes** | Brawl/PM *move* data; cannot compute the runtime jump counter |

**Melee** claims below rest on Tier 2 + Tier 3 agreeing. **PM 3.6** runtime claims are **inference from Brawl/Melee
inheritance** (no Tier-1/2 PM source) — a Tier-1 PM-confirmation spike is filed as a separate ticket.

## 12. Primary-source appendix (verbatim)

### (i) Up-B does not consume jumps — Melee (Tier 2, meleelight)
`src/characters/shared/moves/FALLSPECIAL.js:13-17` — `init` sets only action name + timer; never assigns
`doubleJumped`/`jumpsUsed`:
```js
init : function(p,input){
    player[p].actionState = "FALLSPECIAL";
    player[p].timer = 0;
    actionStates[characterSelections[p]].FALLSPECIAL.main(p,input);
}
```
The counter is zeroed only on landing — `src/physics/physics.js:399-400` (function `land()`):
```js
player[i].phys.doubleJumped = false;
player[i].phys.jumpsUsed = 0;
```

### (ii) What you can do while helpless — Melee (Tier 2, meleelight)
`FALLSPECIAL.js:6-24` — allowed actions are declared as state flags; `main` runs air control; `interrupt` offers
no jump/attack/special branch:
```js
canPassThrough : true,          // fall through soft platforms
canGrabLedge   : [true,false],  // CAN grab the ledge (front only)
wallJumpAble   : false,         // CANNOT wall jump
canBeGrabbed   : true,          // an opponent can grab you
// main(): when not interrupting ->
fastfall(p,input);  airDrift(p,input);   // CAN fastfall + drift left/right
// interrupt(): only re-loops on the timer — no jump/attack/special/airdodge
```
Cross-check — SmashWiki *Helpless* (Tier 3, verbatim): *"a state in which characters are unable to take any
action, with the exception of grabbing a ledge, maneuvering left/right, fastfalling, or climbing a ladder, until
they land on the ground or pass a blast line."*

### (iii) What ends helpless — Melee (Tier 2, meleelight)
- **Landing** — `FALLSPECIAL.js:34-36`: `land : function(p,input){ ...LANDINGFALLSPECIAL.init(p,input); }`.
- **Getting hit (flinch)** — `src/physics/hitDetection.js:404 / :632 / :634`: the resolver forces the victim into a
  damage state regardless of prior state: `actionStates[characterSelections[v]].DAMAGEN2.init(v,input)` /
  `...DAMAGEFLYN.init(v,input, !isThrow)`. The damage states then re-permit an unspent jump.
- **Ledge grab** (`canGrabLedge` above) and **KO / blast line**.

Cross-check — SmashWiki *Helpless* (Tier 3, verbatim): *"Helplessness most commonly ends upon landing on the
ground or being KO'd, although it also ends if characters flinch, allowing them to attack or re-use their triple
jump."*

### pycats current transitions (deterministic — dumped from the built `statecharts` chart)
Generated by walking `statecharts.chart.make_chart(build_fighter_chart(...))` and recovering each guard via
`inspect.getsource` (guards are lambdas). Verbatim output for the helpless-relevant states:
```
[startup] / [active] / [recovery]      # up-B (any attack), airborne exit
    --tick--> helpless   when: done_attacking and not on_ground and recovery_active
    --tick--> fall       when: done_attacking and not on_ground
[dodge]                                 # air dodge
    --tick--> helpless   when: dodge_timer <= 0 and not on_ground and air_dodge_active
[helpless]                              # ONLY TWO EXITS — both grounded
    --tick--> landing_lag when: on_ground and landing_lag_timer > 0
    --tick--> idle        when: on_ground
```
Plus, applying to every child of the `action` parent (so reachable from `helpless`): `on("force_ledge_grab",
"ledge_hang")` and `on("force_ko", "ko")`; `_try_ledge_grab` (`entities/player.py`) fires `force_ledge_grab`
without a state gate. There is **no** `force_hurt`, and `helpless` carries no `hurt_timer`/`stun_timer` exit — the
proof behind divergence #2.

Render it yourself: `PYTHONPATH=. .venv/bin/python -c` around `statecharts.viz.to_mermaid(build_fighter_chart(stub))`
for the full topology diagram (guards render as generic `[guard]`), or the guard-source dump for conditions.

---

## Refs
Recovery hook **#578** · helpless **#184** · Birky physics **#229** (`max_jumps 6`) · up-B recovery data:
Nalio **#954** / Birky **#969** · engine-logic source **meleelight #616** · datamine env (brawllib_rs / pm-data).
Code seams: `entities/fighter_input.py` (jump gate), `entities/fighter.py` (`jumps_remaining`, land/respawn reset,
`receive_hit`), `entities/player.py` (ledge catch).

## Sources
- meleelight (local): `src/characters/shared/moves/{FALL,FALLSPECIAL,CLIFFCATCH,REBIRTH}.js`,
  `src/physics/physics.js` (`land()`), `src/characters/{marth,fox,puff}/moves/*UPSPECIAL*`, `src/characters/puff/puffAttributes.js`.
- brawllib_rs (local): `src/action_names.rs`, `src/high_level_fighter.rs`, `src/script_ast/{mod,variable_ast}.rs`,
  `src/script_runner.rs`, `src/sakurai/fighter_data/mod.rs`; pm-data `pf/fighter/kirby/FitKirbyMotionEtc.pac`.
- SmashWiki (labelled proxy): [Helpless](https://www.ssbwiki.com/Helpless),
  [Special fall](https://www.ssbwiki.com/Special_fall), [Midair jump](https://www.ssbwiki.com/Midair_jump),
  [Up special move](https://www.ssbwiki.com/Up_special_move).

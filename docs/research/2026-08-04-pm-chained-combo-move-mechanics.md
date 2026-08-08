# Project M chained / combo-input move mechanics — class survey (research #1198)

Research for **#1198** (related to #1193 Dancing-Blade ARC / #1185 Dancing-Blade spike / #1058
Narz specials umbrella). Surveys the **class** of moves that advance or rebranch on repeated
input — jab strings, rapid jab, Marth's Dancing Blade — to answer whether PM models them as
**one shared mechanism** or **per-move bespoke logic**, and to feed #1193's Q1 (reuse-a-carve-out
vs. a shared chain primitive) and Q3 (the step-2 branch mapping). **Findings + option space only** —
no shape is ruled here (per RULES → "research never produces a spec").

## TL;DR

- **The player-facing shape is identical across the class.** A jab string and Dancing Blade both
  advance the same way: **press attack/special again inside a "continuable window" just after the
  active frames**, branched (for Dancing Blade) by held stick — else the string ends into recovery.
  This is documented (SmashWiki) and confirmed in both engine references.
- **Two engine references, two answers to "one mechanism or many":**
  - **PM / Brawl (brawllib_rs subaction scripts) = ONE mechanism.** Jab-string and
    Dancing-Blade-step transitions are the **same** script command — `CreateInterrupt` — differing
    only by an interrupt-**type** tag and a button/stick **test** expression. `FOUND`.
  - **Melee (meleelight) = per-move hand-coding.** Jab uses an inline `jabCombo` boolean; Dancing
    Blade uses a **separate**, Marth-only `dancingBlade` helper with an extra early-press latch. No
    shared chain primitive. `FOUND`.
  - For **PM 3.6 parity** (pycats' target), the faithful model is a **single conditional
    "advance-on-input-test" primitive reused across moves**, not a Dancing-Blade-only special case.
- **Corrects the #1185 step-2 gloss.** #1185 read PM's `SpecialS2{Hi,Lw}` as "up/down only." The
  animation-name inventory does **not** carry the stick→subaction mapping; meleelight's Dancing
  Blade branches step 2 on `lsY > 0.56 → UP else FORWARD` — i.e. **{up, forward}** (Melee canon),
  not up/down. The exact **PM** step-2 stick test is unsourced (it lives in the PM side-B
  `CreateInterrupt.test` expressions — datamine-able, not yet dumped).
- **pycats has none of this today.** A move is one `MoveData` → one `MoveClock`; the only "multi"
  mechanisms are `rehit_rate` (#213, a looping single hitbox) and re-dispatching the same move
  after `current_move is None` (#1087) — neither is input-branched chaining.

---

## 1. What pycats models today (`Verified` — in-repo)

- **One move = one dispatch.** `combat/move_select.py` maps `(direction × ground/air × A/B/smash)`
  to a single move key; `_GROUND_A["neutral"] = "jab"`, `_SPECIAL` collapses forward/back to one
  `side_b`. No per-step or per-press branching.
- **`rehit_rate` (#213, `entities/attack.py`)** — a looping **single** hitbox within one move
  (multi-*hit*, e.g. rapid-jab-style damage), no input, no branch. Wrong tool for a directional chain.
- **Repeated-jab (`sim/showcase.py`)** — three A-presses re-fire the *same* `jab` move, but only
  *after* the previous ends (the #1087 `current_move is None` gate). narz's `jab` is a plain 4/2/8,
  one hitbox. Chains only **after** a move completes — the opposite of a mid-move chain advance.

So the whole class (input-gated, mid-move, direction-branched advance) is unbuilt.

## 2. The player-facing shape (`FOUND` — SmashWiki, documented)

- **Jab strings** (`ssbwiki.com/Neutral_attack`): "Pressing the attack button again (or holding it
  from *Brawl* onward) during a **continuable window, typically in the short moment after the active
  frames**, will directly transition into the next part." The infinite/rapid jab "can be
  indefinitely looped by pressing the attack button repeatedly in *SSB* and *Melee*, or by simply
  holding it from *Brawl* onward."
- **Dancing Blade** (`ssbwiki.com/Dancing_Blade`): "up to four consecutive hits… with repeated
  button presses." Step 1 neutral; **step 2 = forward or up**; steps 3–4 = up/forward/down (18
  combos). **Timing:** *Melee* "requires timing on each blow"; *Brawl* onward "the timing no longer
  matters, so it can be performed easily" (holdable).

Both moves are the same design pattern: **re-press within a post-active window → advance (branched
by stick) → else end.**

## 3. Engine model A — Melee (meleelight): per-move hand-coding (`FOUND`)

Local ref `/home/avi/Documents/Study/JavaScript/meleelight`. Every action-state is an
`init`/`main`/`interrupt` object; `interrupt` is the per-frame transition check. There is **no**
generic chain engine — each move re-implements the idea with its own boolean flag.

- **Jab** (`src/characters/{fox,marth}/moves/JAB1.js`): a fresh A-press in a timer window arms an
  inline `jabCombo` flag, checked in `interrupt`:
  ```js
  // JAB1.main:   if (timer>2 && timer<32 && a && !prev.a) phys.jabCombo = true;
  // JAB1.interrupt: if (timer>5 && phys.jabCombo) JAB2.init(); else if (timer>17) WAIT.init();
  ```
  The rapid jab (Fox `JAB3`) self-loops by rewinding its own `timer` (`timer=7`) while re-arming
  the flag each cycle. String ends by falling through to `WAIT`.
- **Dancing Blade** (`src/characters/marth/moves/SIDESPECIALGROUND*.js` + `dancingBladeCombo.js`):
  a **separate** `dancingBlade` flag set by a **Marth-only** helper on a fresh A **or** B press in
  `[min,max]`, plus a `dancingBladeDisable` early-press latch jab lacks. The **held-stick branch**
  reads `lsY` in `interrupt`:
  ```js
  // step 1→2:  if (lsY > 0.56) SIDESPECIALGROUND2UP else SIDESPECIALGROUND2FORWARD
  // step 2→3:  if (lsY>0.56) …3UP; else if (lsY<-0.56) …3DOWN; else …3FORWARD
  ```

`jabCombo` and `dancingBlade` are two independent implementations — no common `chain()` routine.

## 4. Engine model B — PM / Brawl (brawllib_rs): one shared primitive (`FOUND`)

Local ref `/home/avi/Documents/Study/Rust/brawllib_rs` decodes subaction bytecode to an `EventAst`
enum (`src/script_ast/mod.rs`) run by `src/script_runner.rs`. Subaction-to-subaction transitions
are a **real script command**, and it is the **same** command for jab and Dancing Blade:

```rust
// src/script_ast/mod.rs
pub struct Interrupt { pub interrupt_id: Option<i32>, pub action: i32, pub test: Expression }
CreateInterrupt(Interrupt),   // "the current action will change upon test being true"
```

- The runner arms each `CreateInterrupt` into a per-frame-rechecked list; the first whose `test`
  (a button/stick expression) passes sets `change_subaction`.
- The **only** difference between a jab continuation and a Dancing-Blade-step continuation is
  **data, not command kind**: the `InterruptType` of the target action and the `test` —
  `0x01 → GroundSpecial` (side-B / Dancing Blade), `0x04 → GroundAttack` (jab string).
- There is also an **unconditional** advance (`ChangeSubaction` / `ChangeSubactionRestartFrame`)
  and window enable/disable commands (`AllowInterrupts`/`DisallowInterrupts`,
  `EnableInterrupt`/`DisableInterrupt`, `EnableInterruptGroup`).

So **at the script level PM/Brawl treats the whole class as one mechanism**: a conditional
"create-interrupt → change action on test," parameterized by interrupt-type + a button/stick test.

> Caveat: brawllib_rs notes it "operate[s] at the subaction level… the best we can do" — it
> approximates the engine's finer action model, but the decoded AST reflects the actual bytecode.

## 5. Step-2 branch mapping — corrects #1185 (bears on #1193 Q3)

- #1185 read PM's step-2 subactions `SpecialS2{Hi,Lw}` as "**up/down** only." That is an inference
  from the animation **names**; the frame-length manifest (`docs/pm-reference/marth-gif-index.md`)
  carries the animation **inventory**, **not** the stick→subaction mapping.
- The actual mapping lives in the special's action-state test. **Melee** (meleelight) branches step
  2 on `lsY > 0.56 → UP, else → FORWARD` — **{up, forward}**, matching SmashWiki's "forward or up,"
  **not** up/down. So the naive "Hi=up, Lw=down" reading is unsupported.
- The exact **PM 3.6** step-2 stick test is **unsourced**: it is the `test` Expression on Marth's
  PM side-B `CreateInterrupt` events (datamine-able via brawllib_rs, not yet dumped). Whether PM's
  `Hi`/`Lw` correspond to up/forward (Melee) or something else is an open value for the DEV — it is
  a **direction-mapping value distinct from hitbox data**, and must not be guessed.

## 6. The timing / advance-window value (`unsourced` — same as #1185 §3)

- Melee = precise per-hit window; Brawl-onward = lenient / holdable. PM 3.6 is Brawl-based, so it
  **inherits** the lenient/holdable behavior **unless** PM reverted to Melee timing (PM frequently
  restores Melee feel — must be checked, not assumed).
- meleelight's Melee windows are concrete (`timer>2 && timer<32` for jab; `[min,max]` per Dancing
  Blade step) but are **Melee** values, not PM. The **PM** per-step window frames remain the
  `GUESS`/`decision`-under-#530 value #1185 §3 flagged; neither doc guesses it.

## 7. Implications for pycats (option space — not a ruling)

Two things follow for **#1193**:

**Q1 (how the mechanic seats).** The evidence widens the fork the #1185 spike posed:

- **Option 1 — Dancing-Blade-only carve-out** (the #1185 "reuse three seams": a
  `chain_advance_window` timer + a `{step:{direction:key}}` table + a narrow exception to the
  #1087 drop). Smallest surface; faithful to *behavior*, but bespoke to one move.
- **Option 2 — a small shared "advance-on-input" primitive** modeled on PM's `CreateInterrupt`: a
  reusable "while an interrupt window is open, if the input test passes, change to move X (branched
  by stick)." This is what PM's engine actually does, and it would **also** serve jab strings
  (currently single-hit in pycats) and any future chained move. Moderately larger than Option 1;
  far smaller than a bytecode VM.
- **Option 3 — port the interrupt model wholesale** (a `CreateInterrupt`-style event list on
  moves). Most faithful to PM internals, largest blast radius; unwarranted for pycats' `MoveData`
  model. Not recommended by this survey.

The survey does **not** rule Q1; it establishes that **a shared primitive (Option 2) is the
PM-faithful shape**, so the fork is genuinely "Dancing-Blade-only carve-out vs. a small shared
chain primitive," not "reuse-seams vs. a heavyweight bespoke object."

**Q3 (step-2 branch).** §5 shows the DEV cannot assume Hi=up/Lw=down; the PM stick→subaction map
is a distinct unsourced value (datamine the PM side-B `CreateInterrupt.test` expressions, or take
Melee's up/forward as the ruling basis).

**Not in scope of any ruling from this doc:** building jab strings, Dancing Blade, or the shared
primitive; sourcing per-branch hitbox/damage/angle/KB (the DEV sourcing pass, #530).

## 8. Confidence / provenance

| Claim | Status | Basis |
|---|---|---|
| pycats has no input-branched chain today; only `rehit_rate` + repeated-jab | **Verified** | `combat/move_select.py`, `entities/attack.py`, `sim/showcase.py`, narz.json (read) |
| Jab + Dancing Blade share the same player-facing "re-press in a post-active window" shape | **`FOUND`** | SmashWiki *Neutral attack* / *Dancing Blade* |
| Melee models the class **per-move** (separate `jabCombo` / `dancingBlade` flags) | **`FOUND`** | meleelight `JAB*.js`, `dancingBladeCombo.js`, `SIDESPECIALGROUND*.js` |
| PM/Brawl models the class as **one** `CreateInterrupt` command (type + test data only) | **`FOUND`** | brawllib_rs `src/script_ast/mod.rs`, `src/script_runner.rs` |
| Step 2 branches **{up, forward}** (Melee), not up/down; `Hi`/`Lw` names ≠ stick map | **`FOUND` (Melee) / corrects #1185 inference** | meleelight `lsY>0.56→UP else FORWARD`; manifest carries names only |
| PM 3.6 exact step-2 stick test + per-step advance-window frames | **Not sourced** | needs PM side-B `CreateInterrupt.test` dump / PM frame data (#530) |
| A shared "advance-on-input" primitive is the PM-faithful pycats shape | **Inference from FOUND** | PM = one mechanism (§4); pycats parity target is PM 3.6 |

## Refs

#1193 (Dancing-Blade ARC) · #1185 (`docs/research/2026-08-04-dancing-blade-mechanic.md`) · #1058 ·
#294 · #213 (`rehit_rate`) · #1087 (`current_move is None` drop) · #530 (value routing) ·
`combat/move_select.py` · `entities/attack.py` · `docs/pm-reference/marth-gif-index.md` ·
meleelight `/home/avi/Documents/Study/JavaScript/meleelight` (`src/characters/{fox,marth}/moves/`,
`src/characters/marth/dancingBladeCombo.js`) · brawllib_rs
`/home/avi/Documents/Study/Rust/brawllib_rs` (`src/script_ast/mod.rs`, `src/script_runner.rs`) ·
SmashWiki *Neutral attack*, *Dancing Blade*.

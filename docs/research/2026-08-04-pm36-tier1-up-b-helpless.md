# Tier-1 PM 3.6 confirmation of up-B / helpless / jump runtime — and a correction to #980

**Ticket:** #988 (RESEARCH · `area:combat`) · **Date:** 2026-08-04 · **Agent:** apple
**Sequenced after:** #980 (this confirms/corrects #980's PM-inferred claims).
**Deliverable:** this findings doc. No implementation — any pycats change is a downstream ticket (§7).

---

## 1. TL;DR — #980's PM 3.6 inference was WRONG on the headline rule

#980 concluded, from Melee/Brawl inheritance (labelled inference, no PM primary), that up-B / special
fall **locks** a character's remaining midair jumps but does **not consume** them ("lock, not consume"),
and that a flinch out of helpless frees an **unspent** jump.

**A PM 3.6 Tier-1 primary source contradicts this for PM specifically.** PM 3.6 ships a codeset patch —
**"Special Fall Depletes Jumps" [Magus]** — that hooks the common special-fall subroutine and sets the
midair-jump counter to its maximum on entry to special fall. In PM 3.6, **entering special fall consumes
ALL remaining midair jumps** (`JumpsUsed := MaxJumpCount`). The patch is present in the compiled
`RSBE01.gct` that PM 3.6 boots (§3), so it is shipped behavior, not a dev-only draft.

Consequences for #980's three rules, for **PM 3.6**:

| Rule (#980, for PM by inference) | PM 3.6 Tier-1 verdict |
|---|---|
| **1. Up-B does not consume jumps (lock, not consume)** | **CORRECTED → consumes.** Special fall sets `JumpsUsed = MaxJumpCount`; up-B (which enters special fall) leaves **zero** midair jumps. |
| **2. Helpless permits ledge-grab / drift / fastfall; blocks jump/attack/special/airdodge** | **No PM override found** among 436 named PM codes → Brawl-inherited (unchanged); the action-permission set is not modified by PM 3.6. |
| **3. Flinch out of helpless frees an *unspent* jump** | **Practically moot in PM 3.6.** Special fall already depleted the jumps, so after up-B there is no unspent jump to recover even if a flinch ends helpless. |

This applies to **every fighter**, including multi-jump Kirby (pycats' **Birky**, `max_jumps 6`): the hook
is a *common* subroutine and reads each fighter's own `MaxJumpCount`, so Birky's 6 jumps are all consumed
on entering special fall after Final Cutter.

---

## 2. Method & sources

Per the pycats "cite primary, not inference" rule (#520→#537), and because #980 flagged the runtime
mechanic as engine-side and unreachable from the per-move datamine, this spike went to PM 3.6's **engine
patch layer** — the shipped gecko/PSA codeset — which is the authoritative place a PM override of a Brawl
engine behavior lives.

| Source | Type | Role here |
|---|---|---|
| **Project-M-CC** `[Dev Resources]/codes-dev.txt` | Local · PM 3.6 dev codeset, 436 **named** gameplay codes with author tags | **PRIMARY** — the readable form of PM's engine patches (titles + hex bodies) |
| **`repros/pm36-codeset/extracted/codes/RSBE01.gct`** | Local · the **compiled** codeset PM 3.6 actually boots | **Shipping proof** — a dev code is only PM 3.6 behavior if its bytes are in the gct |
| **brawllib_rs** on PM 3.6 `FitKirbyMotionEtc.pac` | Local · PM Kirby move datamine | Confirms the **datamine boundary** on PM data (§4) — the PSA never touches the jump counter |
| **pm-data** PM `ft_kirby.rel` (PM-patched Tier-1 binary) | Local · byte-differs from Brawl's | Present but **not disassembled** — the codeset answered the question first (§6) |
| **capstone 5.0.7** (PPC32 big-endian) | Local · disassembler (approved install, isolated scratch venv) | Used to sanity-decode PPC payloads; the depletion patch is PSA bytecode, hand-decoded + gct-verified |

Encoding note: `codes-dev.txt` is UTF-16LE/CRLF; `codes-cc-3_6.txt` (the shipped CC export) is UTF-16 too.
The CC export omits most dev **titles**, so a title-only search of it misses gameplay codes — the depletion
patch's *bytes* are in `codes-cc-3_6.txt` and the gct even though its title is not.

---

## 3. The correction, with primary evidence — "Special Fall Depletes Jumps" [Magus]

### 3a. The shipped code (verbatim, `codes-dev.txt`)

```
Special Fall Depletes Jumps [Magus]
* 4A000000 90000000     ; Gecko: set base address ba = 0x90000000
* 1619D680 00000030     ; write 0x30 bytes to ba+0x19D680 = 0x9019D680 (an injected PSA subroutine)
* 00000005 000059DB     ;   arg[0] : type 5 (Variable) -> InternalConstantInt 23003 = MaxJumpCount
* 00000005 10000001     ;   arg[1] : type 5 (Variable) -> LongtermAccessInt index 1 = JumpsUsed
* 00000002 9019D698     ;   arg[2] : type 2 (Pointer)  -> 0x9019D698 (entry of the event list below)
* 04000100 80FAE664     ;   event 0x04,0x00 (1 arg) -> call/keep displaced original at 0x80FAE664
* 12000200 9019D680     ;   event 0x12,0x00 (2 args @0x9019D680) = IntVariableSet(JumpsUsed = MaxJumpCount)
* 00080000 00000000     ;   event 0x00,0x08 = Return
* 06FC1B88 00000008     ; write 8 bytes to 0x80FC1B88 (the common special-fall subroutine's hook slot)
* 00070100 9019D690     ;   -> Subroutine(0x9019D690) : redirect into the injected list above
```

### 3b. Decode (grounded in brawllib_rs's own PSA tables)

- **`0x12,0x00` = `IntVariableSet { value, variable }`** — verbatim from brawllib `src/script_ast/mod.rs`
  (`(0x12, 0x00, Some(Value(v0)), Some(Variable(v1)), None) => EventAst::IntVariableSet`).
- **`0x000059DB` = 23003 = `InternalConstantInt::MaxJumpCount`** — brawllib `src/script_ast/variable_ast.rs`
  (`23003 => InternalConstantInt::MaxJumpCount`).
- **`0x10000001` → `LongtermAccessInt::JumpsUsed`** — brawllib `variable_ast.rs`
  (`01 => LongtermAccessInt::JumpsUsed`); the `0x1_______` prefix is the LA-Int memory type, index `0001`.

So the injected event sets **`JumpsUsed := MaxJumpCount`** — the used-jumps counter is driven to the
fighter's maximum, i.e. **no midair jumps remain**. The hook overwrites the common special-fall
subroutine's slot at `0x80FC1B88`, calling the displaced original (`0x80FAE664`) first, then depleting the
jumps, then returning — the standard "keep original behavior, add mine" PSA hook shape.

### 3c. Shipping proof — the bytes are in the compiled `RSBE01.gct`

The patch's signature words all appear in the compiled codeset PM 3.6 boots (and in the shipped CC export):

```
RSBE01.gct :  1619D680 FOUND(1) · 80FAE664 FOUND(1) · 000059DB FOUND(3) · 06FC1B88 FOUND(1) · 9019D698 FOUND(1)
codes-cc-3_6.txt (shipped CC export) : 1619D680 (1) · 000059DB (3) · 06FC1B88 (1)
```

(`000059DB` = MaxJumpCount appears 3× — the depletion patch plus the two `Meteor Cancel Multijump Fix`
writes at §5, all referencing the same constant.) This is shipped PM 3.6 behavior.

---

## 4. Why the per-move datamine could not have shown this (boundary re-grounded on PM data)

Before reaching the codeset, brawllib_rs was run on PM 3.6 Kirby's actual move data (`FitKirbyMotionEtc.pac`)
to test whether the answer lived in the PSA. It does not:

- The whole aerial Final Cutter — `SpecialAirHi` (rise), `SpecialAirHi2` (apex), `SpecialAirHi3` (sword
  descent, pure `CreateHitBox`), `SpecialAirHi4`, `LandingAirHi` — contains **no read or write of
  `JumpsUsed`** and **no self-driven `ChangeSubaction`/special-fall transition**.
- **Positive control:** `JumpsUsed` is also absent from the actual jump moves (`JumpAerialF` / `JumpF` /
  `JumpB`). The counter is engine-managed; *no* subaction PSA touches it.

This confirms #980's datamine-boundary claim (its §3c) directly on PM 3.6 data — the jump-counter
arithmetic is engine-side — and it is exactly why the depletion is expressed as an engine **codeset hook**
into the special-fall subroutine, not as a move-script event. (Dumper: `scripts/brawllib/script_dump.rs`,
a throwaway sibling of `hitbox_dump.rs`, copied transiently into the brawllib_rs clone's `examples/`.)

---

## 5. Adjacent PM 3.6 jump/special-fall codes (context, not the headline)

Named, shipped PM 3.6 codes that touch the same machinery — they corroborate that PM actively re-worked
jump/special-fall handling (so a change to the deplete/lock behavior is in-character, not surprising):

- **Grab and Special Grab Single Jump Return [Phantom Wings, Magus]** — on being grabbed, returns **one**
  jump (a PPC `C2` hook at `0x809131B0` testing capture action-ids `0x3D/0xCC/…`). PM makes grab-return a
  *single* jump, not a full reset — narrower than Brawl/Melee's "double jumps restored on being grabbed."
- **Meteor Cancel Multijump Fix [Magus, standardtoaster]** — two writes referencing `MaxJumpCount`
  (`0x59DB`); governs meteor-cancel vs the jump counter.
- **Melee Air Dodge v7.0 / v5.3** — PM 3.6 air dodge is Melee-style (directional, actionable), i.e. air
  dodge does **not** route into special fall (a PM/Brawl delta) — so the depletion patch's "special fall"
  trigger is up-B/recovery-style helpless, plus **Zair Goes into Special Fall** (Shanus), not air dodge.
- **NonTumble Hitstun Canceling / Store Variables into Hitstun CILs / Jab Reset Hitstun Linker** — PM's
  hitstun handling is reworked, but none of the 436 named codes modifies the **special-fall
  action-permission table** (rule 2) or adds a "flinch frees a jump" path — consistent with rule 2 staying
  Brawl-inherited and rule 3's jump-recovery being moot once jumps are depleted.

---

## 6. What was NOT done, and residual uncertainty (honest bounds)

- **`ft_kirby.rel` / DOL were not disassembled.** capstone (PPC32-BE) was installed and available, but the
  codeset answered rule 1 cleanly and at lower risk than symbol-less REL/DOL reverse engineering (no PM/Brawl
  symbol map is on disk). The `.rel` remains a deeper Tier-1 avenue if a future question needs it.
- **Trigger scope of the depletion hook.** The `JumpsUsed := MaxJumpCount` event is unambiguous; the claim
  that it fires on *entering special fall generally* rests on the code's title + the hook target
  (`0x80FC1B88`, identified as the common special-fall subroutine from title/context, not a symbol map). The
  precise set of states routed through that subroutine (all special-fall entries vs a subset) is the one
  residual — it does not affect the up-B/recovery case, which is squarely special fall.
- **Rule 2** rests on a **negative** search (no PM code among 436 named ones changes the helpless
  action-permission set). Negatives from a named-title corpus are strong but not exhaustive; a differently
  labelled patch could exist. Scope-honest: "no override found in the 436 named PM 3.6 codes," not "provably
  none."
- Rule 3's helpless **exit conditions** themselves (land / ledge / KO / flinch-ends-helpless) were not
  independently re-confirmed for PM; only the **jump-recovery consequence** is settled (moot — no unspent
  jump survives special fall in PM 3.6).

---

## 7. pycats implication (suggest, don't act — repro/spec-first)

#980 §9 read pycats as **matching canon** on "up-B locks but does not consume jumps," and flagged a
candidate divergence that pycats never restores jumps on ledge-grab. **This PM 3.6 correction inverts the
target for the PM-parity build:**

- pycats' Birky up-B currently (per #980) leaves the jump counter untouched (lock, not consume). **PM 3.6
  depletes it.** So for PM parity, entering helpless/special-fall (after Final Cutter) should set
  `jumps_remaining = 0` (consume all), then restore on land/ledge/respawn — the opposite of #980's "don't
  consume" reading. Seams: `entities/fighter_input.py` (jump gate), `entities/fighter.py`
  (`jumps_remaining`, land/respawn reset).
- The #980 "flinch frees an unspent jump" divergence hinge is **not a PM parity target** — in PM 3.6 there
  is no unspent jump after special fall.

**Suggested downstream follow-ups (NOT filed — one at a time, human-gated):**
1. A `research`/repro ticket to pin the pycats observable: after Birky Final Cutter, does `jumps_remaining`
   stay full (current) — and should it be 0 for PM 3.6 parity?
2. If confirmed, a DEV ticket: deplete `jumps_remaining` on entering helpless/special-fall (PM 3.6 parity),
   restored on land/ledge/respawn.
3. Update #980's §8/§9/§11 PM posture from "Brawl-inherited inference (lock, not consume)" to "PM 3.6
   Tier-1: special fall **depletes** jumps (this doc)."

---

## 8. Refs

#980 (the inference this corrects) · overlap #987 · helpless #184 · recovery hook #578 · Birky physics
#229 (`max_jumps 6`) · Birky up-B #969 · engine-logic source meleelight #616 · datamine env brawllib_rs +
pm-data. Primary sources: `Project-M-CC/[Dev Resources]/codes-dev.txt` ("Special Fall Depletes Jumps"
[Magus]); compiled `repros/pm36-codeset/extracted/codes/RSBE01.gct`; brawllib_rs `src/script_ast/mod.rs`
(`IntVariableSet`), `src/script_ast/variable_ast.rs` (`MaxJumpCount 23003`, `JumpsUsed 01`); PM 3.6
`FitKirbyMotionEtc.pac` (Kirby `SpecialAirHi*`). Method helper: `scripts/brawllib/script_dump.rs`.

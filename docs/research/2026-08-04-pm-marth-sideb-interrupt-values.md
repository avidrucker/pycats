# PM 3.6 Marth side-B (Dancing Blade) — advance-window + stick-branch values (research #1205)

Sourcing spike for **#1205** (child of Narz-specials umbrella **#1058**; the value-sourcing gate for
the Dancing Blade DEV). Consumes the #1193 ruling and the #1198 class survey. Supplies, per step
transition, the two values the DEV needs and #1198 flagged as unsourced: **(a) the advance-input
window** and **(b) the stick→variant threshold**. **Findings + provenance only** — no shape or spec is
decided here (RULES → "research never produces a spec").

## TL;DR

- **The exact per-step advance-window frames do NOT exist as an extractable number in the PM 3.6
  data — not because brawllib won't decode the chain, but because the chain, once decoded, contains
  no frame literals.** PM implements the Dancing Blade re-press window as a **per-frame engine thread**
  (`CallEveryFrame` thread 9), evaluated every frame and gated by engine **bools** (`Address(17)` latch,
  `EnableActionTransition`), **not** as a `[min, max]` frame range in any subaction or fragment script.
  The v3 datamine **followed the thread into subroutine `184140` and decoded the whole tester** (§1a) —
  it has zero `SyncWait`/frame gating. So the window's open/close **frames** are engine-timed and
  un-pinnable from the `.pac`. `FOUND` (structural — the *absence* of a frame literal is itself the
  result).
- **The stick→variant branch STRUCTURE is now PM-CONFIRMED and matches Melee exactly.** The decoded
  tester branches on **`ControlStickYAxis ≥ Address(3186)` → up**, else **`ControlStickYAxisReverse ≥
  Address(3186)` → down**, else **forward** — Y-axis only, one symmetric magnitude for up and down,
  `lsX` never consulted (§1a). This is structurally identical to Melee's `lsY > 0.56 → up / lsY < −0.56
  → down / else forward`, so #1193 Q3's Melee mapping is now **corroborated by PM's own bytecode**, not
  merely adopted as a blind fallback. The re-press input is likewise PM-confirmed: **attack (button 0)
  or special (button 1)** — matching meleelight's `a || b`.
- **The stick-threshold NUMBER stays un-pinned.** The compared magnitude is `Address(3186)`, an engine
  data-section constant brawllib does not resolve to a float — the same class as the air-dodge/charge
  globals the datamine recipe excludes. PM uses a **single symmetric magnitude** (up and down compare
  the same `Address(3186)`), exactly Melee's shape; the numeric value (Melee's `0.56`) is the only
  available figure. `FOUND` (structural: single symmetric address).
- **Net for the DEV:** (b) the stick map is now **PM-confirmed in structure**, Melee-sourced only for
  the numeric cutoff. (a) the window frames are **Melee-sourced and cannot be otherwise** — PM stores
  no frame number here, so the Melee `[min, max]` table is the sole source and PM's engine timing may
  differ from it. Route both under #530 as below.
- **One PM-`FOUND` frame datum does land:** the per-step generic **IASA frame** (`AllowInterrupts`) from
  the subaction main scripts (S1 f29, S2 f40, S3 f43–46, S4 f50). That is the end-of-move interruptible
  point, **not** the chain-advance window (which the thread-9 tester opens earlier) — reported below so
  the DEV does not mistake one for the other.

---

## 1. What was datamined (brawllib_rs PM 3.6) and how

Env: the live datamine env (`docs/tooling-brawllib-rs-datamine-recipe.md`; clone
`~/Documents/Study/Rust/brawllib_rs @ e8dc833`, PM 3.6 `.pac` at `~/Documents/Study/Rust/pm-data/`).
Reproduce with the throwaway example added for this ticket (a sibling of the `subaction_flags_dump.rs`
/ `subaction_lengths` diagnostics, no new deps):

```bash
. ~/.cargo/env
cargo run --release --example dancing_blade_interrupts -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd -f Marth
```

It walks each **named action**'s entry script (via `HighLevelFighter::new`) and each subaction main
script, printing every interrupt / subaction-change / branch event with a running frame counter, **and
recursively resolves every `Subroutine` / `Goto` / `CallEveryFrame` offset against the fragment-script
pool** (`get_fighter_sakurai().fragment_scripts`, 415 entries) so the chain can be followed into the
engine subroutines rather than left as raw offsets.

### 1a. The chain, decoded: a per-frame tester with a Melee-shaped stick branch and no frame window (`FOUND`)

The `SpecialS` action's entry script installs the chain and sets the opener subaction indices:

```text
SpecialS (action 0x113) script_entry:
  Subroutine -> 187076        # (empty when decoded)
  Subroutine -> 119480        # (empty when decoded)
  IntVariableSet ThrowDataParam1 = 282
  CallEveryFrame thread=9 -> 119528     # the per-frame chain tester (below)
  Subroutine -> 119960                  # installs the AnimationEnd→Wait/Fall end interrupts
  IntVariableSet Address(0) = 470       # 470 = SpecialS1  (ground opener)
  IntVariableSet Address(1) = 479       # 479 = SpecialAirS1 (air opener)
  Subroutine -> 119688                  # EnableActionTransition gate (ground/air)
```

Following `CallEveryFrame(thread 9) → 119528 → Subroutine 184140` decodes the **actual chain tester**
that runs every frame (verbatim structure from the dump; all events at frame `0.0` because it is a
per-frame thread with no `SyncWait`):

```text
fragment 184140  (CallEveryFrame thread 9 body — evaluated every frame):
  IF NOT RandomAccessBool(EnableGlide)
  AND NOT RandomAccessBool(SpecialsMovement):
    IF ButtonPress(0)                       # button 0 = Attack (A)
       AND NOT ButtonPress(15)
       OR  ButtonPress(1):                  # button 1 = Special (B)
      IF RandomAccessBool(Address(17)):      # engine latch — the "window is open" gate
        IF ControlStickYAxis        >= Address(3186):   # → UP variant   (SxHi)
        ELSE
        IF ControlStickYAxisReverse >= Address(3186):   # → DOWN variant (SxLw)
                                                        # (neither ⇒ FORWARD variant, SxS)
      ELSE ...
```

Two facts fall out of this decode:

1. **No frame window exists as a literal.** The re-press is accepted by a `CallEveryFrame` thread, gated
   by the engine bool `RandomAccessBool(Address(17))` (the open/close latch) and `EnableActionTransition`
   — **not** by a `[min, max]` frame range anywhere in the script. There is nothing to read as "the
   window is frames X–Y"; the timing is engine-side. This is the decisive result: the exact advance-window
   frames are **not extractable from the PM `.pac`**, and now by decode, not by brawllib's limits.
2. **The stick branch is PM-confirmed and Melee-shaped.** It tests **only** the Y axis
   (`ControlStickYAxis` for up, `ControlStickYAxisReverse` for down), against **one symmetric magnitude**
   `Address(3186)`, and never consults `lsX`. That is exactly Melee's `lsY > c → up / lsY < −c → down /
   else forward`. The re-press input is **attack (0) or special (1)** — meleelight's `a || b`. So §3b's
   Melee mapping is corroborated by PM's own bytecode; only the numeric `c` (§1b) stays un-pinned.

Contrast: the sibling special actions decode the same way — `SpecialN` (`0x112`) creates its
button-tested charge/release interrupts inline; `SpecialLw` (Counter, `0x115`) creates its
`AnimationEnd → Wait/Fall` interrupts inline. `SpecialS` differs only in that its per-frame re-press
test is factored into the thread-9 subroutine above — which this datamine now decodes.

### 1b. The stick threshold is an engine constant by address, never a script literal (`FOUND`)

The DB chain tester's own stick branch (§1a) compares against `Address(3186)`:

```text
Binary(left: Variable(InternalConstantInt(ControlStickYAxis)),
       right: Variable(InternalConstantInt(Address(3186))),  # engine constant, value NOT resolved
       operator: GreaterThanOrEqual)
```

The compared-against magnitude is an `Address(NNNN)` engine constant — the same shape seen across
Marth's other decoded stick branches (observed elsewhere: `3133`, `3138`, `3141`, `3158`), **never** a
`Scalar(f32)` literal. brawllib resolves the *address*, not the *value* stored there, so the numeric
cutoff is an unresolved engine global — the same limitation the recipe's "⚠ moves/hitboxes ONLY, NOT
engine globals" boundary describes. What the decode **does** pin: up and down compare **the same
`Address(3186)`**, i.e. PM uses a single symmetric magnitude (Melee's shape), not two independent
cutoffs.

### 1c. The one PM-`FOUND` *timeline frame*: per-step generic IASA (`AllowInterrupts`)

From the subaction **main** scripts (the only interrupt datum they carry). This is the frame the step
becomes generically interruptible (end-of-move IASA), **not** the chain-advance window:

| Step subaction | `AllowInterrupts` frame | anim length (manifest) |
|---|---|---|
| `SpecialS1` | 29 | 30 |
| `SpecialS2Hi` / `SpecialS2Lw` | 40 | 45 |
| `SpecialS3Hi` / `SpecialS3S` | 46 | 52 / 51 |
| `SpecialS3Lw` | 43 | 45 |
| `SpecialS4Hi` / `SpecialS4S` | 50 | 51 / 66 |
| `SpecialS4Lw` | — (none) | 61 |
| `SpecialAirS1` | 29 | 30 |
| `SpecialAirS2*`…`S4*` | — (none in main) | — |

These land near the **end** of each animation (e.g. S1 at f29 of 30), which is why they cannot be the
follow-up window — Dancing Blade accepts the next press well before the step's animation ends. The
chain-advance interrupt is the earlier, engine-subroutine one (§1a). Reported so the DEV does not wire
the advance window to this frame.

## 2. SmashWiki (the other named primary) — also dry

Both reads returned "no per-step frame window, no numeric stick threshold" for **any** version:

- **`ssbwiki.com/Dancing_Blade`** — documents only the qualitative branch structure, verbatim:
  > "the second hit can be tilted forward or up, while the third and fourth hit can be tilted up,
  > forward or down."

  and confirms no timing/threshold numbers exist on the page for Melee, Brawl, **or** Project M.
- **`ssbwiki.com/Marth_(PM)`** — side-B is described only as "A sequence of Falchion slashes with
  several variations based on the direction the control stick is tilted." No frame window, no stick
  threshold.

Note the wiki's **{up, forward}** step-2 branch corroborates #1198's correction: PM's `S2Hi`/`S2Lw`
subaction **names** are not "up/down" — step 2 is up-vs-**forward** (no down variant), so `S2Hi` = the
up slash and `S2Lw` = the forward/neutral slash.

## 3. The Melee fallback values (meleelight) — the ruled basis, labeled Melee-sourced

Per #1193 Q3 ("adopt Melee's mapping if the PM dump is dry"). Source:
`~/Documents/Study/JavaScript/meleelight/src/characters/marth/` — `dancingBladeCombo.js` (the window
latch) and the `SIDESPECIAL{GROUND,AIR}*` state `interrupt` handlers (the stick branch). All values
below are **Melee, not PM-confirmed.**

### 3a. (a) Advance-input window — per step, `[min, max]` frames

`dancingBladeCombo(p, min, max, input)` sets `dancingBlade = true` on a fresh A **or** B press when the
current step's `timer ∈ [min, max]`; a press **before `min`** instead sets `dancingBladeDisable`
(an anti-mash latch that forfeits that step's follow-up). The window is on the **current** step:

| Transition | Ground state (min, max) | Air state (min, max) |
|---|---|---|
| **S1 → S2** | `SIDESPECIALGROUND` **(8, 26)** | `SIDESPECIALAIR` **(8, 26)** |
| **S2 → S3** (from up) | `…GROUND2UP` **(17, 32)** | `…AIR2UP` **(17, 32)** |
| **S2 → S3** (from forward) | `…GROUND2FORWARD` **(17, 33)** | `…AIR2FORWARD` **(17, 33)** |
| **S3 → S4** (from up) | `…GROUND3UP` **(18, 38)** | `…AIR3UP` **(18, 38)** |
| **S3 → S4** (from forward) | `…GROUND3FORWARD` **(16, 37)** | `…AIR3FORWARD` **(16, 37)** |
| **S3 → S4** (from down) | `…GROUND3DOWN` **(19, 35)** | `…AIR3DOWN` **(19, 35)** |
| **S4 → —** | terminal (no `dancingBladeCombo` call) | terminal |

Ground and air windows are identical. If the DEV wants a single scalar per step (the #1185 §3 model),
the coarse read is **S1 ≈ [8,26], S2 ≈ [17,32], S3 ≈ [16,38]** — with the pre-`min` **disable latch**
as a distinct Melee nuance the DEV may adopt or drop.

### 3b. (b) Stick→variant threshold — Melee `lsY` cutoffs

From each step state's `interrupt` handler (verbatim thresholds):

- **S1 → S2** (2-way, no down at step 2): `if lsY > 0.56 → UP (S2Hi); else → FORWARD (S2Lw)`.
- **S2 → S3 and S3 → S4** (3-way): `if lsY > 0.56 → UP; else if lsY < −0.56 → DOWN; else → FORWARD`.

So the single Melee rule is **`lsY > 0.56` → up, `lsY < −0.56` → down, otherwise forward**, with step 2
lacking a down branch (a forward/down press at step 2 both resolve to the forward `S2Lw` slash). `lsX`
is not consulted for the variant. Subaction-name mapping for the DEV: `S2Hi`=up, `S2Lw`=forward;
`S3Hi/S4Hi`=up, `S3S/S4S`=forward, `S3Lw/S4Lw`=down.

**PM corroborates this rule's structure** (§1a): PM's decoded thread-9 tester branches on
`ControlStickYAxis ≥ Address(3186)` → up / `ControlStickYAxisReverse ≥ Address(3186)` → down / else
forward — Y-axis only, one symmetric magnitude, `lsX` ignored. So only the **numeric cutoff** (`0.56`)
is Melee-sourced; the **branch shape** is now PM-confirmed. If PM's `Address(3186)` were ever resolved
to a float it would slot straight into this rule.

## 4. Provenance routing (per #530)

| Value | Status | Basis |
|---|---|---|
| DB chain runs via `CallEveryFrame(thread 9) → 184140`, a per-frame tester; opener idx `Address(0)=470`, `Address(1)=479` | **`FOUND`** | brawllib_rs `SpecialS` entry + decoded thread-9 fragment (§1a) |
| **(b-structure) stick branch tests Y-axis only, one symmetric magnitude `Address(3186)`, `lsX` ignored; re-press = attack(0) or special(1)** | **`FOUND`** | brawllib_rs decoded fragment 184140 (§1a) — matches Melee shape |
| Stick-threshold *number* is `Address(3186)`, an engine constant, not a script literal | **`FOUND`** (address only) | brawllib_rs decoded stick test (§1b); value unresolved |
| Advance-window frames are **not** script literals — engine-timed via `Address(17)` latch + `CallEveryFrame` | **`FOUND`** (absence) | brawllib_rs decoded fragment 184140 (§1a); no `SyncWait` gating |
| Per-step generic IASA (`AllowInterrupts`) frames | **`FOUND`** | brawllib_rs subaction main scripts (§1c) |
| **(a) per-step advance-window `[min,max]` frames** | **`decision` (Melee-sourced)** | meleelight `dancingBladeCombo.js` callers (§3a); PM stores no frame literal (§1a); ratified by #1193 Q3 |
| **(b-number) stick→variant `lsY` cutoff (0.56 / −0.56)** | **`decision` (Melee-sourced)** | meleelight `SIDESPECIAL*` interrupts (§3b); PM value is the unresolved `Address(3186)`; ratified by #1193 Q3 |

The **structure** of (b) is now `FOUND` from PM's own bytecode (Y-only, symmetric, `lsX`-ignored,
attack-or-special re-press). What remains Melee-sourced is narrower than the first pass concluded:
only the **numeric stick cutoff** and the **`[min,max]` window frames** — and the window frames are
Melee-sourced *by necessity*, since the decode proves PM stores no frame literal for them (the timing
is a `CallEveryFrame` gated by the `Address(17)` engine latch). Both enter under #530 as **`decision`s
carrying the Melee citation**, which #1193 Q3 pre-authorized. To promote either to a PM `FOUND` a
future source would have to resolve the engine data-section values (`Address(3186)`, `Address(17)`) —
a DOL/RAM dump or a PM decomp, out of scope for the subaction datamine (recipe's engine-globals
boundary). A PMDT changelog or frame-lab count could independently pin the window timing.

## 5. What this unblocks / does not

- **Unblocks the Dancing Blade DEV** on its two gating values: **(a) windows** — Melee `[min,max]`
  basis, #1193-ratified, and now known to be the *only* possible source (PM stores no frame literal),
  with the disable-latch nuance surfaced; **(b) stick map** — **PM-confirmed in structure** (Y-only,
  symmetric, `lsX`-ignored, attack-or-special re-press) with the numeric cutoff Melee-sourced.
- **Out of scope (unchanged):** per-branch hitbox / damage / angle / KB (Spike 2, #1147/#1150); the
  step-2 forward/default fallback policy (already ruled #1193 Q3b); building the move or the shared
  primitive (the DEV, downstream); general mid-move IASA (#1089).

## Refs

#1193 (ruling) · #1185 (`docs/research/2026-08-04-dancing-blade-mechanic.md`) · #1198
(`docs/research/2026-08-04-pm-chained-combo-move-mechanics.md`) · #1058 · #294 · #530 · datamine recipe
`docs/tooling-brawllib-rs-datamine-recipe.md` · brawllib_rs `~/Documents/Study/Rust/brawllib_rs`
(`examples/dancing_blade_interrupts.rs`, `src/script_ast/mod.rs`, `src/high_level_fighter.rs`) ·
`src/sakurai/mod.rs` (`fragment_scripts` pool, resolved via `get_fighter_sakurai`)) · meleelight
`~/Documents/Study/JavaScript/meleelight/src/characters/marth/` (`dancingBladeCombo.js`,
`SIDESPECIAL{GROUND,AIR}*.js`) · SmashWiki *Dancing Blade*, *Marth (PM)* · Project-M-CC codeset
(`~/Documents/Study/reference/Project-M-CC` — Gecko codesets only, no per-move script; dry for this).

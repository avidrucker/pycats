# PM 3.6 Marth side-B (Dancing Blade) — advance-window + stick-branch values (research #1205)

Sourcing spike for **#1205** (child of Narz-specials umbrella **#1058**; the value-sourcing gate for
the Dancing Blade DEV). Consumes the #1193 ruling and the #1198 class survey. Supplies, per step
transition, the two values the DEV needs and #1198 flagged as unsourced: **(a) the advance-input
window** and **(b) the stick→variant threshold**. **Findings + provenance only** — no shape or spec is
decided here (RULES → "research never produces a spec").

## TL;DR

- **The PM 3.6 values are NOT datamine-able from brawllib_rs, and NOT documented on SmashWiki.** Both
  named primary sources came up dry for these two specific values. This is a sourced negative, not an
  un-run check — the datamine and the wiki reads are below.
- **Why the brawllib dump is dry:** Marth's `SpecialS` action (`0x113`) does **not** carry the chain
  in its decoded script. Its entry script sets the opener subaction indices into scratch variables
  (`Address(0) = 470` = `SpecialS1`, `Address(1) = 479` = `SpecialAirS1`) and then hands the whole
  chain to engine **`Subroutine` + `CallEveryFrame` (thread 9)** calls whose bodies brawllib_rs stores
  as **raw offsets and does not decode** into the AST. So the per-step interrupt windows and the
  stick-branch tests live in engine subroutines the tool does not expose. `FOUND` (structural).
- **Even where Marth's stick tests ARE in decoded scripts** (tilts/smashes), the threshold is a
  `Variable(InternalConstantInt(Address(NNNN)))` **engine constant** (e.g. `3141`, `3158`, `3186`),
  **never a script float literal** — so the numeric stick cutoff is engine-hardcoded and unresolved by
  brawllib, the same class as the air-dodge/charge globals the datamine recipe excludes. `FOUND`
  (structural).
- **The ruled fallback applies.** #1193 Q3 adopts **Melee's** mapping "if the PM dump is dry." It is
  dry. So the DEV's basis for both values is **meleelight** (`dancingBladeCombo.js` + the
  `SIDESPECIAL*` states), tabulated below and labeled **Melee-sourced (not PM-confirmed)**. Route each
  under #530 as a **`decision`** carrying the Melee citation + the #1193 ratification — **not** `FOUND`
  (no PM primary exists to mark it `FOUND`).
- **One PM-`FOUND` datum does land:** the per-step generic **IASA frame** (`AllowInterrupts`) from the
  subaction main scripts (S1 f29, S2 f40, S3 f43–46, S4 f50). But that is the end-of-move
  interruptible point, **not** the chain-advance window (which opens earlier, in the undecoded engine
  subroutine) — reported below so the DEV does not mistake one for the other.

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
script, printing every interrupt / subaction-change / branch event with a running frame counter.

### 1a. The chain is engine-subroutine-driven, not in the decoded script (`FOUND`, structural)

The `SpecialS` action's raw entry script (verbatim from the dump):

```text
SpecialS (action 0x113) script_entry:
  Subroutine(Offset { offset: 187076, .. })
  BoolVariableSetFalse { EnableActionTransition }
  Posture(3) / Posture(4)
  Subroutine(Offset { offset: 119480, .. })
  IntVariableSet { value: 282, variable: ThrowDataParam1 }
  CallEveryFrame { thread_id: 9, offset: Offset { offset: 119528, .. } }
  Subroutine(Offset { offset: 119960, .. })
  IntVariableSet { value: 470, variable: Address(0) }   # 470 = SpecialS1  (ground opener)
  IntVariableSet { value: 479, variable: Address(1) }   # 479 = SpecialAirS1 (air opener)
  Subroutine(Offset { offset: 119688, .. })
```

Contrast: the sibling special actions **do** decode fully — `SpecialN` (`0x112`) creates its
button-tested charge/release interrupts and `ChangeSubaction`s to its subaction; `SpecialLw`
(Counter, `0x115`) creates its `AnimationEnd → Wait/Fall` interrupts and `ChangeSubaction`s. Only
`SpecialS` is empty of decoded interrupts — its logic is the `Subroutine` + `CallEveryFrame(thread 9)`
offsets above, which brawllib_rs stores as raw offsets and never decodes. **The advance windows and
stick tests are inside those undecoded engine subroutines.** They are not obtainable from this tool
without a bespoke bytecode decoder at those offsets (out of scope for this spike, and arguably for
brawllib, which "operates at the subaction level… the best we can do").

### 1b. Stick thresholds are engine constants by address, never script literals (`FOUND`, structural)

Across Marth's fully-decoded scripts (tilts/smashes/aerials), every control-stick branch has the shape:

```text
Binary(left: Variable(InternalConstantInt(ControlStickYAxis)),
       right: Variable(InternalConstantInt(Address(3141))),  # engine constant, value NOT resolved
       operator: GreaterThanOrEqual)
```

The compared-against magnitude is always an `Address(NNNN)` engine constant (observed: `3133`, `3138`,
`3141`, `3158`, `3186`), **never** a `Scalar(f32)` literal. So even if the DB chain test were decoded,
the numeric cutoff would still be an unresolved engine global. This is the same limitation the recipe's
"⚠ moves/hitboxes ONLY, NOT engine globals" boundary describes.

### 1c. The one PM-`FOUND` value: per-step generic IASA (`AllowInterrupts`)

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

## 4. Provenance routing (per #530)

| Value | Status | Basis |
|---|---|---|
| DB chain is engine-subroutine-driven; opener subaction idx `Address(0)=470`, `Address(1)=479` | **`FOUND`** | brawllib_rs `SpecialS` action raw script (§1a) |
| PM stick thresholds are `Address(NNNN)` engine constants, not script literals | **`FOUND`** | brawllib_rs decoded stick tests (§1b) |
| Per-step generic IASA (`AllowInterrupts`) frames | **`FOUND`** | brawllib_rs subaction main scripts (§1c) |
| **(a) per-step advance-window frames** | **`decision` (Melee-sourced)** | meleelight `dancingBladeCombo.js` callers (§3a); PM primary dry (§1–2); ratified by #1193 Q3 |
| **(b) stick→variant `lsY` thresholds (0.56 / −0.56)** | **`decision` (Melee-sourced)** | meleelight `SIDESPECIAL*` interrupts (§3b); PM primary dry; ratified by #1193 Q3 |

Neither (a) nor (b) is `FOUND`: no PM primary states them (both named sources checked and dry). They
enter as **`decision`s carrying the Melee citation**, which #1193 Q3 pre-authorized. If a PM-specific
source later surfaces (a PMDT changelog line, a decompiled subroutine, a frame-lab video count), the
DEV should re-pin and promote to `FOUND`; until then the Melee basis is the ratified stand-in.

## 5. What this unblocks / does not

- **Unblocks the Dancing Blade DEV** on its two gating values: (a) windows and (b) stick map, both now
  sourced (Melee basis, #1193-ratified) with the disable-latch nuance surfaced.
- **Out of scope (unchanged):** per-branch hitbox / damage / angle / KB (Spike 2, #1147/#1150); the
  step-2 forward/default fallback policy (already ruled #1193 Q3b); building the move or the shared
  primitive (the DEV, downstream); general mid-move IASA (#1089).

## Refs

#1193 (ruling) · #1185 (`docs/research/2026-08-04-dancing-blade-mechanic.md`) · #1198
(`docs/research/2026-08-04-pm-chained-combo-move-mechanics.md`) · #1058 · #294 · #530 · datamine recipe
`docs/tooling-brawllib-rs-datamine-recipe.md` · brawllib_rs `~/Documents/Study/Rust/brawllib_rs`
(`examples/dancing_blade_interrupts.rs`, `src/script_ast/mod.rs`, `src/high_level_fighter.rs`) ·
meleelight `~/Documents/Study/JavaScript/meleelight/src/characters/marth/`
(`dancingBladeCombo.js`, `SIDESPECIAL{GROUND,AIR}*.js`) · SmashWiki *Dancing Blade*, *Marth (PM)*.

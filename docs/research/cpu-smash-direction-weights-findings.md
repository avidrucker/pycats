# CPU per-direction smash weights — decode from Melee `ftcpuattack.c` (findings)

**Ticket:** #1223 (research) · feeds the Q5 direction model on decision #1219 and the direction
implementation #916 · parent CPU epic #231 · CPU-fidelity epic #925 · source research #915.
**Date:** 2026-08-04 · **Agent:** banana (opus-4.8).
**Purpose:** resolve, from primary decomp source, (1) the opcode→move mapping for the smash
directions (fsmash/usmash/dsmash) in the CPU attack-selection list, (2) the relative `.weight` each
smash direction carries, (3) whether direction is purely reach-gated + weighted-RNG or has positional
bias beyond the SmashWiki "target-above ⇒ up-smash" cue.

**Primary source:** `doldecomp/melee` at commit **`51890e0`** (2026-08-02), files
`src/melee/ft/ftcpuattack.c`, `src/melee/ft/ftcpuattack.h`, `src/melee/ft/fighter.h`,
`src/melee/ft/fighter.c`, `src/melee/ft/ftcmdscript.c`. All line numbers below are at that SHA.

**Provenance convention (per the #1240 standard).** Every **`PRIMARY-MELEE`** tag below means:
**T1 (primary) · `doldecomp/melee`@`51890e0` · rung 3 (Melee) · inference-for-PM** — the citation
column gives the exact `file:line`. This is decompiled **Melee** code, not Project M, and never a
PM value; it is used here only to establish the *mechanism*.

**Lineage reframe (why the weights are not sourced here).** pycats targets **PM 3.6**, whose CPU AI
**descends from Brawl** (PM is built on Brawl), so the weight numbers pycats should use are **PM's
(rung 1)**, or failing that **Brawl's (rung 2** — the direct AI ancestor, dumpable from a legally-owned
Brawl ISO**)**, or **meleelight's (rung 4)** — **not Melee's**. Which of those is obtainable is
catalogued in **#1239**. This doc supplies the Melee *mechanism shape* (rung 3); it does not, and
should not, hand pycats the direction weights.

---

## TL;DR

- **The selection *mechanism* is fully decoded** (reach-box filter → weighted-RNG). Direction is
  **not** arbitrary RNG and **not** a hardcoded "target-above ⇒ up-smash" rule — each candidate
  carries a **reach box** tested against the target's *ballistically predicted* position, and only
  geometrically-eligible entries enter the weighted roll. The "target-above ⇒ up-smash" behaviour is
  an *emergent consequence* of that box test, not a separate branch.
- **The per-direction `.cmd` opcode values and `.weight` numbers are NOT in the C source.** They live
  in a **per-character binary data table** (`Fighter_804D64FC->x10[fp->kind]`, the annotated "smash
  attack tables") that Melee loads at runtime from the fighter `.dat` data. The decomp reads that
  blob as an array of `ftCo_AttackEntry` structs; it never spells out the values. **NOT-DECODED from
  source** — and even if read, these would be **Melee** weights (rung 3), which are **not** what
  pycats wants: the target is PM/Brawl weights (see the lineage reframe above; obtainability →
  **#1239**).
- **Cross-cutting finding (relevant to #1224 / #1219, flagged not acted on):** the dedicated smash
  table is consulted **only** when `cpu->level > 5` **and the *target* is shielding**. `level` is
  **0-indexed** (proven below), so `> 5` = in-game **Lv7–Lv9**, and the trigger is opponent-**shield**
  (not shield-*break*). This bears on the #1219 Q1/Q4 shield-punish ruling and the #1224 threshold-N
  question.

---

## 1. The selection mechanism (fully decoded — PRIMARY-MELEE)

### The candidate struct

`ftCo_AttackEntry` (`ftcpuattack.c:99-108`) — a 0x24-byte record; the attack tables are arrays of it,
terminated by a `cmd == 0` sentinel (`while (list->cmd)`, `:256`):

| Field | Off | Meaning (from how the code reads it) |
|---|---|---|
| `cmd`    | +00 | **attack opcode** = a `script_idx` into the per-character cmdscript table (see §2). `0` terminates the list. |
| `x04`    | +04 | look-ahead time `t` in frames — used to *predict* the target's future position. |
| `x08`,`x0C` | +08,+0C | the entry's **reach direction vector** (forward/back extents), scaled by fighter scale + `halfRange`. |
| `x10`,`x14` | +10,+14 | the entry's **vertical reach bounds** (lower/upper), same scaling. |
| `weight` | +18 | **selection weight** for the weighted-RNG roll. |
| `x1C`    | +1C | modulo divisor — periodicity gate `cpu->x80 % x1C == 0` (`:356`). |
| `x20`    | +20 | **per-entry min-level unlock** — `if (x20 > cpu->level) skip` (`:260`). |

### The filter → roll (function `ftCo_800B4AB0`, `:256-388`; 3 more copies at `:461`, `:650`, `:786`)

For each entry in the passed-in table:

1. **Min-level unlock** — `if (list->x20 > cpu->level) { list++; continue; }` (`:260`). Low levels
   never see high-`x20` entries.
2. **Exclusion list** — skip if `cmd` is in the recently-used / disallowed set (`xCC_array`, `:265`).
3. **Reach-box test** (`:346`) — compute the target's predicted position `t = x04` frames out using a
   full ballistic model (gravity, terminal velocity; `:280-334`), giving `relPredY` (predicted
   vertical offset) and `relx` (horizontal offset). The entry's box — `x08/x0C` horizontally,
   `x10/x14` vertically, each × `fp->x34_scale.y` × `halfRange` where `halfRange = 0.5*cpu->x570+0.5`
   (`:231`) — must contain that predicted point:
   `upper > relPredY && lower < relPredY + x568 && dirx < relx + rangeF && diry > relx - rangeB`.
   Survivors are copied into the candidate buffer `sp3C[]`.
4. **Weighted-RNG select** (`:366-385`) — `sum = Σ weight`; roll `r = HSD_Randf()` ∈ [0,1);
   walk the survivors accumulating `acc += weight`; return the first where `acc / sum >= r`.
   The returned value is `entry->cmd` (`ftCo_CpuSelectAttack`, `:165-174`).

**So direction selection = "which smash's reach box covers where the target will be, weighted by each
box's `.weight`, decided by one RNG roll."** A target directly above makes only the up-smash's
(upward) box eligible → up-smash fires; a target at mid-range in front makes the fsmash box (and maybe
others) eligible → weighted roll among them. This is the decoded, primary answer to deliverable (3):
**reach-box-gated by predicted position, then weighted-RNG among the geometrically eligible** — the
SmashWiki cue is a special case, not a distinct code path.

---

## 2. Why the opcodes + weights are NOT in the source (NOT-DECODED)

`entry->cmd` is an **index into a per-character table**, not a global enum. The dispatcher
(`ftcmdscript.c:355-370`) is explicit:

```c
/** Runs an existing command script from a table loaded from .dat */
void ftCo_800B4880(Fighter* fp, int script_idx) {
    u8* cmd = Fighter_804D64FC->cmdscripts[script_idx];   // per-character byte-program
    ...
}
```

`cmdscripts[script_idx]` is a byte-program of stick/button ops (`CpuCmd_SetLstickY`, `CpuCmd_PressA`,
`CpuCmd_WaitFor`, …) that *performs* the move. Which `script_idx` produces forward- vs up- vs
down-smash is defined **per character in the loaded `.dat`**, not in C. (The character-signature
special-move opcodes that *are* hardcoded — e.g. Mario `0x35`, Fox `0x3D`, Falcon `0x39/0x3A` at
`:1111-1136` — confirm these values are per-character, with no shared "this-is-fsmash" legend.)

The attack tables themselves are runtime data: `Fighter_804D64FC = pData[22]` (`fighter.c:217`), and
`Fighter_804D64FC->x10` is annotated **"smash attack tables (per character)"** (`fighter.h:15-26`).
`x10[fp->kind]` is a `void*` to an `ftCo_AttackEntry[]` blob. The decomp iterates it; it does not
list its bytes. **Therefore the fsmash/usmash/dsmash `.cmd` values, their `.weight`s, and their
reach-box geometry cannot be read off the source** — they are data, not code.

### Artifact needed to finish the decode

Note the lineage reframe at the top: the **Melee** weights below are rung 3 and **not** pycats's
target. The routes pycats should prefer (obtainability catalogued in **#1239**):

- **Rung 1 — PM 3.6:** a PM CPU-AI datamine, if one exists / is buildable (`rukaidata` / `brawllib_rs`
  expose per-move subaction data, not CPU-AI decision tables — #915 found no published PM CPU-AI
  datamine; #1239 re-tests this).
- **Rung 2 — Brawl:** Brawl's CPU-AI data — the closest ancestor to PM's — from OpenSA/dantarion or a
  datamine of a **legally-owned Brawl ISO**.
- **Rung 4 — meleelight:** if its reimplementation encodes a smash-direction choice.

The **Melee** route remains only as a last-rung reference: read the per-character smash table from a
Melee `GALE01` DOL / RAM dump — resolve `Fighter_804D64FC` (symbol `.sbss:0x804D64FC`,
`config/GALE01/symbols.txt`), follow `+0x10` to the smash-table pointer array, index by fighter kind,
read the `ftCo_AttackEntry[]` (0x24-byte stride) until `cmd == 0`; each record gives `cmd`, the reach
box, and `weight`. Even decoded, these are Melee-inference-for-PM, not a PM value.
2. **The extracted fighter `.dat` (`PlXx.dat` / common data)** parsed with the same struct layout.

Neither ships with the decomp source tree (the tables are external data), so this is the hard
boundary of a source-only decode. **This is a data-availability ceiling, not incomplete
searching.**

---

## 3. Cross-cutting finding — the smash-table gate (FLAGGED for #1224 / #1219)

The dedicated smash table (`->x10`) is read at exactly **one** call site (`ftcpuattack.c:1889-1892`):

```c
if (cpu->level > 5 && ftCo_800B9F6C(target)) {
    result = ftCo_800B4AB0(fp, target, ((void**) Fighter_804D64FC->x10)[fp->kind]);
    ...
}
```

- `ftCo_800B9F6C(target)` (`:2359-2364`) returns true **iff** `target->motion_id` is `ftCo_MS_GuardOn`
  or `ftCo_MS_Guard` — i.e. **the opponent is shielding** (holding shield), *not* shield-broken/dizzy.
- **`level` is 0-indexed** — proven by the wait table `ftCo_800B63D8` (`:869-914`), a
  `switch (level)` with `case 0` (= in-game Lv1) … `case 8` (= Lv9), no `case 9`, comment *"Level 9
  doesn't wait at all."* So `cpu->level > 5` ⇒ level ∈ {6,7,8} ⇒ **in-game Lv7, Lv8, Lv9**.

**Two consequences worth the human's attention (I am flagging, not acting):**

1. **Melee's dedicated-smash-table unlock threshold is Lv7+**, matching the "older reference table
   said Lv7" note in #1224's body — and **contradicting the interim `N = Lv5`** wired into DEV #1225.
   This is a Melee *primary* for the #1224 threshold-N question (still not a PM primary — PM inherits
   Brawl's AI, undatamined).
2. **The Melee smash trigger is opponent-*shielding*, not shield-*break* dizzy.** The #1219 Q1/Q4
   ruling adopted a "shield-break dizzy-punish" trigger sourced from SmashWiki's Brawl prose. The
   Melee code shows the mechanism is broader (any shielding opponent) and the "fully charged on a
   broken shield" wiki line is a Brawl-era refinement on top. This does not overturn the ruling
   (pycats can choose either), but the human may want to reconcile the two before #1225 implements.

Caveat: smashes could *also* be emittable via the general ground table (`->x4`, read unconditionally
at `:1925`) — its `.cmd` contents are the same undecoded data blob, so I cannot confirm or exclude
that from source. The dedicated smash table is unambiguously the shielding-opponent path.

---

## 4. Provenance ceiling

Per #915, **no published PM / Brawl CPU-AI datamine was found** — #1239 re-tests this, including a
route #915 lacked: a datamine of a **legally-owned Brawl ISO** (rung 2, PM's direct AI ancestor).
Everything in this doc is **Melee-sourced** (rung 3); applying it to PM is inference. Per
[[pm-parity-cite-primary-not-inference]] the mechanism is `PRIMARY-MELEE`
(T1 `doldecomp/melee`@`51890e0`); any per-direction *number* is **NOT-DECODED**, and even once read
from Melee would be **Melee-inference-for-PM**, never a PM value. Evidence sufficiency is the human's
call ([[evidence-sufficiency-is-the-humans-call]]).

---

## 5. Recommendation for the Q5 model (#916) — findings only, not a decision

The decode says the faithful direction model is **reach-box-gated + weighted-RNG**, not a positional
`if target-above`. Given the weights are NOT-DECODED, the option space #916 chooses from:

- **(a) Geometry-faithful, weights = uniform** — implement the reach-box eligibility (up-smash box
  covers above, fsmash box covers front, dsmash box covers low/both sides) and roll *uniformly* among
  eligible smashes. Captures the behaviour's *shape* without inventing weight numbers; label the
  uniform weights `PROVISIONAL`/`TUNED` (decision, not sourced), converge to sourced weights later.
- **(b) Geometry-faithful, weights from a higher-rung source** — same, but block #916 on reading the
  per-direction `.weight`s from PM/Brawl/meleelight (the §2 routes, obtainability via #1239). Highest
  fidelity; highest cost.
- **(c) Positional heuristic** — the SmashWiki "target-above ⇒ up-smash, else forward" shortcut.
  Cheapest; a coarse approximation of (a).

This doc does not pick one — that is #916's (or a follow-on decision's) call with the human.

---

## Provenance table

| Claim | Tier | Citation (@ `51890e0`) |
|---|---|---|
| Attack entry is a 0x24-byte struct with `cmd`/reach-box/`weight`/`x20` | PRIMARY-MELEE | `ftcpuattack.c:99-108` |
| Selection = reach-box filter then weighted-RNG; returns `entry->cmd` | PRIMARY-MELEE | `ftcpuattack.c:256-388`, `:165-174` |
| Reach box tested vs ballistically-predicted target position | PRIMARY-MELEE | `ftcpuattack.c:280-346` |
| Per-entry min-level unlock `x20 > level` | PRIMARY-MELEE | `ftcpuattack.c:260` |
| `cmd` is a per-character `cmdscripts[]` index, loaded from `.dat` | PRIMARY-MELEE | `ftcmdscript.c:355-370` |
| `->x10` = "smash attack tables (per character)"; loaded from `pData[22]` | PRIMARY-MELEE | `fighter.h:15-26`, `fighter.c:217` |
| Smash table gated on `level > 5` AND target shielding | PRIMARY-MELEE | `ftcpuattack.c:1889-1892`, `:2359-2364` |
| `level` is 0-indexed (Lv1=0 … Lv9=8) → `>5` = Lv7+ | PRIMARY-MELEE | `ftcpuattack.c:869-914` |
| **Per-direction `.cmd` / `.weight` / reach-box values** | **NOT-DECODED** | data blob `->x10[kind]`; not the target lineage — PM/Brawl weights via #1239 (§2) |
| No published PM/Brawl CPU-AI datamine (Brawl-ISO route untried) | NOT-FOUND | #915 sourced-negative; #1239 re-tests |

---

**Downstream:** provenance conventions ratified in **#1240** (lineage ladder / `PROVISIONAL` /
`FOUND`-split). Source obtainability (PM / Brawl-ISO / meleelight) catalogued in **#1239**. A
follow-up ticket to source the PM/Brawl direction weights should be filed once #1239 names the
obtainable route. Direction model consumes this: **#916** (may start on `PROVISIONAL` uniform
weights). Parent CPU epic **#231**; CPU-fidelity epic **#925**; source research **#915**; decision
**#1219**.

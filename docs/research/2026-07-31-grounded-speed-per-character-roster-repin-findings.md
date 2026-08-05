# Grounded walk/dash/run: re-pin the whole current roster to PM 3.6 — per-character stats, not global constants

**Ticket:** #950 (RESEARCH, child 2 of #813) · **Sibling:** #814 (roster survey) · **Consumer:** #808 (`RUN_SPEED`)
**Date:** 2026-07-31 · **Agent:** FIG

> Written one atomic piece at a time, plain English first. Each finding is self-contained.

---

## Piece 1 — the model: a speed is a per-character stat, not a global setting

### What pycats does today (plain English)

pycats keeps two grounded-speed numbers as **global settings** in `pycats/config.py`:

- `MOVE_SPEED = 6` — the walk speed, for **every** character.
- `DASH_SPEED = 8` — the dash speed, for **every** character.

There is one knob per motion, and turning it moves the whole roster at once. #808 was going
to add a third knob the same way: a global `RUN_SPEED`.

`pycats/combat/data.py::FighterData` *does* carry per-character `move_speed` / `dash_speed`
fields — but they **default to those global constants**, and no cat overrides the default, so
in practice every cat runs at the same 6 / 8. The per-character *home* exists in the struct;
the global constant is what actually fills it.

### Why that model is wrong (the evidence)

#814 datamined PM 3.6's fighter attribute table (via `brawllib_rs`) and found walk, dash, and
run are **three independent per-character attributes** — and the relationship between dash and
run is **not fixed**; it flips from character to character:

| Character (archetype) | walk | dash | run | dash→run |
|---|---|---|---|---|
| Mario (**Nalio**) | 1.1 | 1.5 | 1.5 | **equal** |
| Fox | 1.6 | 1.9 | 2.2 | run **faster** |
| Sonic | 1.4 | 1.7 | 4.0 | run **much faster** |
| Samus | 1.0 | 1.86 | 1.55 | run **slower** |
| Jigglypuff (Purin) | 0.7 | 1.4 | 1.1 | run **slower** |

(units = u/frame; full 40-fighter table in `docs/research/2026-07-31-pm36-per-character-grounded-speeds-findings.md`.)

A **single global number cannot express this table.** One global `DASH_SPEED` and one global
`RUN_SPEED` force every character onto the same two values — but PM 3.6 has Fox running faster
than he dashes, Samus dashing faster than she runs, and Mario doing both at the same speed.
The dash/run relationship is a **per-character fact**, so the value has to live **on the
character**, not in a global config knob.

### What this implies (option space — the decision is downstream, not here)

The finding points at one model change: **grounded speeds belong in per-character data**
(the `FighterData` triple / the cat's `<key>.json`), and the global `config.py` constants
should become at most a *fallback default*, not the source of truth.

- **Option A — per-character data is the source of truth.** Each cat's JSON carries its own
  `walk` / `dash` / `run`. Matches the #814 reality directly; kills the "add a global
  `RUN_SPEED`" plan.
- **Option B — keep global constants, add per-character overrides later.** Ship `RUN_SPEED`
  as a global now, differentiate per character in a future ticket. Faster to land, but bakes
  in the exact model #814 says is wrong and defers the un-braiding.

**Owner ruling (2026-07-31, game-designer):** **Option A, and `config.py` keeps NO fallback
constant** — per-character data is the *only* source of truth. This aligns with the existing
raise-on-unknown behavior (`load_fighter_data` raises `UnknownCharacter` rather than
substituting a default, since #887): a cat with no grounded-speed data is an error to fix in
data, not a silent 6/8. The formal spec + the #808 rework are downstream tickets (an ARC and a
DEV); this research records the ruling as their input.

---

## Piece 2 — Nalio's grounded triple, re-pinned to a PM 3.6 primary

### The re-pin (plain English)

Nalio is the Mario archetype (the worked example here; the **whole roster** is groundable —
Piece 5). PM 3.6 Mario's datamined attributes (#814, from `brawllib_rs`'s fighter attribute
table) give the triple:

| Motion | PM 3.6 attribute (u/frame) | × `PX_PER_UNIT` (5.4) | pixels (rounded) |
|---|---|---|---|
| walk | `walk_max_vel` = **1.1** | 5.94 | **6** |
| dash | `dash_init_vel` = **1.5** | 8.10 | **8** |
| run  | `dash_run_term_vel` = **1.5** | 8.10 | **8** |

These are **`FOUND`** values — read from the PM 3.6 primary via the datamine, not community
lore.

### What actually changes vs. the old proxy

The old numbers came from SmashWiki's **Project+** table (`docs/research-120-smash-units-and-sources.md`),
which lists walk 1.1 / dash 1.5 / **run 1.55**. Comparing:

- **walk (1.1) and dash (1.5) are unchanged** — the Project+ figures happened to match PM 3.6.
- **run changes 1.55 → 1.5 u** — the only value that moves. This is the retirement of the
  Project+ proxy for a PM 3.6 primary.
- **In pixels, nothing on screen moves.** 1.55 × 5.4 = 8.37 → 8, and 1.5 × 5.4 = 8.1 → 8 —
  both round to the same 8 px. So the re-pin is a **provenance** fix (proxy → primary), not a
  visible speed change.

### Provenance rows (ADR-0003 / #233 registry — to be written by the downstream DEV)

Each value becomes a registry row with **status `FOUND`**, source = the #814 PM 3.6 datamine:

```
nalio.walk : 1.1 u (6 px)  — FOUND — PM 3.6 Mario walk_max_vel, brawllib_rs attr table (#814)
nalio.dash : 1.5 u (8 px)  — FOUND — PM 3.6 Mario dash_init_vel, brawllib_rs attr table (#814)
nalio.run  : 1.5 u (8 px)  — FOUND — PM 3.6 Mario dash_run_term_vel, brawllib_rs attr table (#814)
```

(This research ticket *records* the values + basis; **writing** them into `nalio.json` and the
registry is a downstream DEV, gated on the Option-A model landing. Storage form is Piece 3.)

---

## Piece 3 — how the value is stored: integer px, via the conversion seam, rounded

### Movement speeds must be **integers** (verified)

Position is a `pygame.Rect`, which stores **integers only**, and the integrator
`pycats/core/physics.py::move_rect` does `rect.x += vel.x` with **no sub-pixel accumulator** —
so any fraction in a constant speed is truncated *every frame* and never carries over. Measured
(pygame-ce 2.5.7):

| stored speed | ships as |
|---|---|
| `8.0` | 8 px/frame |
| `8.1` (`vel(1.5)`) | **8 px/frame** — the `.1` is discarded each frame |
| `5.94` (`vel(1.1)`) | **5 px/frame** — loses a whole pixel |
| `6.0` | 6 px/frame |

A fractional (float) speed therefore does **not** render faithfully — it floors to
`int(vel.x)`. So grounded walk/dash/run are **integer** px values.

### Use the conversion seam, not manual `× 5.4`

`pycats/combat/units.py` already owns the one unit→px seam. For an **integer** movement speed
the right helper is **`u()`** (`round(units × PX_PER_UNIT)`), authored raw-first so the source
unit stays visible in the code and the 5.4 factor lives in exactly one place:

```python
walk = u(1.1)   # 6
dash = u(1.5)   # 8
run  = u(1.5)   # 8
```

This is the #785 raw-first convention (Gnok is its first consumer). Hand-writing `round(1.1 *
5.4)` at each call — or worse, a bare `6` — is the error this seam exists to prevent (DRY,
one source of the factor).

### round, not floor (owner ruling 2026-07-31)

`round` and `floor` **agree** for dash and run (`1.5 × 5.4 = 8.1` → 8 either way). They differ
for **only one value, walk**: `1.1 × 5.4 = 5.94` → `round` = **6**, `floor` = **5**. Ruling:
**round** (which is what `u()` already does), because:

1. **Convention** — every other unit→px value in the codebase rounds (`u()`, #120 / ADR-0003);
   floor would make movement the lone exception.
2. **Faithfulness** — `round`→6 is off the true 5.94 by 0.06; `floor`→5 is off by 0.94. floor
   systematically under-shoots.
3. **Byte-identical** — round keeps walk at today's 6 (no golden regen); floor would drop Nalio
   to 5 px/frame (17% slower, flips movement goldens) for no faithfulness gain.

The per-frame truncation in `move_rect` is not a reason to floor at authoring time: it only
floors the sub-pixel *remainder of accumulation*, which is zero when the stored speed is already
an integer.

---

## Piece 4 — the dash≠run-speed premise: for Nalio it's state, not speed

#808 / #374 designed movement on the premise **"dash ≠ run: distinct states *and* speeds"** —
i.e. add a separate `RUN_SPEED` number alongside `DASH_SPEED`. For **Nalio that premise's
*speed* half is false**: PM 3.6 Mario's `dash_init_vel` and `dash_run_term_vel` are **both
1.5 u** — equal at the source float, not merely after rounding — so dash and run are **both 8
px**. There is no distinct run *number* to source for Nalio.

So the dash/run distinction for Nalio can only be **state / behavior**, not px: dash is the
short initial burst; run is the *sustained* state you reach by holding past the burst window,
at the **same** 8 px. The difference is "does the speed persist or decay," not "is one faster."
(For other characters the *speed* half is real — Fox's run > dash, Samus's run < dash — which is
exactly why the value is per-character, Piece 1.)

**Bearing on #808:** its planned global `RUN_SPEED` constant is doubly wrong for Nalio — wrong
*home* (global, not per-character; Piece 1) **and** redundant *value* (it would just equal
`DASH_SPEED = 8`). #808's ⚠ open sub-problem ("dash 8 and run 8 collapse — resolve before
shipping") resolves toward its third listed option: **model dash≠run as state/turn-rules, not a
raw-px delta.** That is a #808 design decision; this research hands it the fact.

---

## Piece 5 — the whole roster is groundable (all four cats are mapped)

All four cats already carry a **ratified PM archetype** in their character-file headers, and
each archetype is one of the fighters #814 datamined — so every cat has a PM 3.6 primary to pin
to, not just Nalio. Grounded triples via `u()` (`round(unit × 5.4)`, Piece 3):

| Cat | Archetype (source: `<cat>_cat.py` header) | walk | dash | run |
|---|---|---|---|---|
| `nalio` | Mario (#117/#119) | `u(1.1)` = **6** | `u(1.5)` = **8** | `u(1.5)` = **8** |
| `birky` | Kirby (#228/#229) | `u(0.85)` = **5** | `u(1.5)` = **8** | `u(1.5)` = **8** |
| `gnok`  | Donkey Kong (#779) | `u(1.2)` = **6** | `u(1.8)` = **10** | `u(1.8)` = **10** |
| `narz`  | Marth (#294) | `u(1.6)` = **9** | `u(1.5)` = **8** | `u(1.8)` = **10** |

(PM 3.6 units from #814: Mario 1.1/1.5/1.5 · Kirby 0.85/1.5/1.5 · Donkey 1.2/1.8/1.8 · Marth
1.6/1.5/1.8. Marth and DK are "run > dash" fighters — genuine per-character `run ≠ dash`,
exactly the spread Piece 1 says the value has to live per-cat for.)

### Design nuance — pinning surfaces real changes for some cats (a decision, not decided here)

The cats' *current* movement scalars are game-tuned/approximated, not their archetype's PM
values (the `#229` "pin/playtest later" caveat). Pinning to PM 3.6 keeps some byte-identical but
changes others:

- **`nalio` walk 6, `birky` walk 5, `gnok` walk 6** — already equal to today's values (no change).
- **`narz` walk 6 → 9** — Narz currently defaults to Mario-baseline 6; Marth's walk is 1.6 u = 9.
- **`gnok` dash 9 → 10** — Gnok currently authors `dash_speed = vel(1.8) = 9.72`, which *ships*
  as 9 (Piece-3 truncation); the integer-faithful `u(1.8)` is 10.

Whether to pin every cat exactly to its archetype vs. keep an intentional divergence is a
per-cat **design call** (some divergences are deliberate identity choices, e.g. Birky's
featherweight lean). This research reports that the data exists for all four; the owner rules
which cats get pinned as-is.

---

## Downstream (filed one-at-a-time after this doc — not decided here)

1. **ARC / decision** — formalize the per-character speed-home model (Piece 1, Option A, no
   fallback) as the spec that reshapes #808 and the `FighterData`/config layout.
2. **#808 rework** — drop the global `RUN_SPEED` plan; add `run` as a per-character value (Nalio
   = 8) and model dash≠run as state, not a px delta (Piece 4).
3. **DEV — the re-pin itself** — write the grounded triples into the cat JSONs + the
   ADR-0003/#233 registry (Piece 2/3), gated on the model landing. Nalio is byte-identical
   (6/8/8); per Piece 5 the owner decides per cat whether to pin exactly (e.g. `narz` walk
   6→9, `gnok` dash 9→10) or keep a deliberate divergence — the ones that change need golden
   review.
4. **#957** (already filed) — a conformance test asserting each character's `FOUND` JSON value
   equals `conversion(source_unit)`, so a value can't drift off its provenance without a red test.
5. **Observation (may warrant its own ticket)** — Gnok authors `dash_speed = vel(1.8) = 9.72`,
   which by the Piece-3 truncation actually ships as **9 px/frame**, not 9.72. Possibly
   unintended; flagged for a separate look.

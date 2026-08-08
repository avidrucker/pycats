# ADR-0011 — Per-character grounded movement speeds: raw PM units in JSON, integer px derived at load

- **Status:** Accepted  *(2026-07-31 — owner ruling on #962; the load-time-conversion schema ratified with sign-off)*
- **Date:** 2026-07-31

## Context

Walk / dash / run are **three independent per-character attributes** in PM 3.6 — no
fixed ratio (Fox run > dash, Samus run < dash, Mario run == dash). pycats today
expresses two of them as **global constants** — `MOVE_SPEED = 6` (the walk),
`DASH_SPEED = 8` — in `pycats/config/physics.py`, used as the `FighterData` field
defaults (`pycats/combat/data.py`). A cat that omits a value inherits the global; run
was to arrive as a third global, `RUN_SPEED` (#808).

Two problems, established by the #813 research umbrella and its findings (#814 roster
survey; #950 re-pin, `docs/research/2026-07-31-grounded-speed-per-character-roster-repin-findings.md`):

1. **A global can't express a per-character relationship.** One `DASH_SPEED`/`RUN_SPEED`
   pair cannot hold a roster where the dash/run ordering flips per cat.
2. **The stored values are inconsistent and partly ungrounded.** `birky.json` stores the
   derived pixel `5`; `gnok.json` stores the `vel()`-float `9.72`; `narz` stores nothing
   and rides the `6` default. Nothing ties a shipped number to the PM datamine it claims.

The **home** of these values (global constant vs. per-character data) and how they're
**stored** (raw source unit vs. derived pixel) are the two questions this ADR settles,
so #808 can ship `run` without re-opening them.

## Decision

**1 — Per-character data is the sole source of truth; no config fallback.** Remove the
`MOVE_SPEED` / `DASH_SPEED` globals and the planned `RUN_SPEED`. Each cat carries its own
walk / dash / run; a cat with no speed data is an **error**, not a default (matches
`load_fighter_data` raising on an unknown key, #887). *(Carried from #950.)*

**2 — Pin the whole roster exactly to PM 3.6.** Every cat takes its archetype's datamined
walk / dash / run — no deliberate divergences.

**3 — JSON stores the raw PM unit; the pixel is derived at load.** Each `<cat>.json` holds
the #814 unit values **verbatim**. The load seam applies `round(PX_PER_UNIT × unit)`
(= `pycats/combat/units.py::u()`) to produce the integer pixel the movement code uses.
Constant movement speeds (walk / dash / run) use the **integer** `round` conversion —
`pygame.Rect` truncates fractions each frame (#80), so a fractional walk speed is
meaningless. Accelerating velocities (gravity / jump) keep the **float** `vel()`: they
accumulate, so sub-pixel precision matters there.

**Resulting values** (raw unit → derived px):

| Cat | archetype | walk | dash | run |
|---|---|---|---|---|
| nalio | Mario | 1.1 → 6 | 1.5 → 8 | 1.5 → 8 |
| birky | Kirby | 0.85 → 5 | 1.5 → 8 | 1.5 → 8 |
| gnok | Donkey Kong | 1.2 → 6 | 1.8 → 10 | 1.8 → 10 |
| narz | Marth | 1.6 → 9 | 1.5 → 8 | 1.8 → 10 |

**4 — dash ≠ run is a state distinction, not a speed one.** nalio's dash and run are the
same raw unit (1.5 u each), so — derived the same way as every other speed (Decision 3:
`round(PX_PER_UNIT × 1.5) = 8`) — they land on the identical pixel. The `8` is a *derived*
value, not a literal; it is not baked in anywhere. The dash/run distinction #374/#808
designed on is therefore **behaviour** — sustained-at-dash vs. decay-to-walk — not a pixel
delta. #808's run-state model must encode the state machine, not a second number that
happens to differ. (This holds only where a cat's dash and run units are equal; where they
differ — narz, 1.5 u vs. 1.8 u — the two states derive different pixels, 8 vs. 10, by the
same conversion.)

## Consequences

- **Player-visible changes needing golden + eyeball review:** **narz walk 6 → 9** (was
  riding the removed default; its sourced 1.6 u derives `round(PX_PER_UNIT × 1.6) = 9`) and
  **gnok dash 9 → 10** (its sourced 1.8 u derives `round(PX_PER_UNIT × 1.8) = 10`; today's
  `vel(1.8) = 9.72` truncates to 9). Both new pixels arrive the Decision-3 way — the raw
  unit in JSON through `round(PX_PER_UNIT × unit)` — never a hand-entered literal. nalio /
  birky are byte-identical to today.
- **Easier:** speeds become groundable and greppable per cat; the dash/run ordering is free
  to vary; a value's provenance is one `round(PX_PER_UNIT × unit)` from its cited source.
- **Accepted cost:** the load path gains a conversion step (units in JSON, px in
  `FighterData`), and every cat must now carry all three speeds — no silent default absorbs
  an omission.
- **Ruled out:** global speed constants (1); deliberate per-cat divergence from PM 3.6 (2);
  storing the derived pixel in JSON (3).

### Follow-up DEV tickets (ordered; filed one-at-a-time downstream, on ratification)

1. **Run-state rework (reshapes #808).** Add a per-character `run`; drop the global-`RUN_SPEED`
   plan; model dash ≠ run as **state** (sustained vs. decay), per Decision 4.
2. **The re-pin.** Write the raw PM units into each `<cat>.json`; add the load-time
   `round(PX_PER_UNIT × unit)` conversion; remove the `MOVE_SPEED`/`DASH_SPEED` globals;
   add ADR-0003 / #233 provenance rows (`FOUND`, source = #814 datamine). narz + gnok change
   → regenerate their goldens per `REGEN_PROTOCOL.md` (author ≠ reviewer) + eyeball.
3. **Conformance test (#957)**, sequenced after the schema lands: assert each cat's `FOUND`
   JSON unit converts to its shipped px (`u(1.1) == 6`, …), so a value can't drift off its
   source without a red test.

### Relationships

Downstream of #950 (findings) / #813 (umbrella) / #814 (roster survey). Reshapes #808.
Design lineage #374 (walk/dash/run), #126/#229 (per-fighter scalars). Provenance method:
ADR-0003 / #233. Conversion seam: `combat/units.py` (#785).

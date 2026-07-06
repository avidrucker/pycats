# Project M rules by category

High-level index of the PM mechanics pycats has researched. Each row points to the detailed
local doc + the primary citation — this file is the map, the local docs are the territory.
PM canon = **Project M 3.6**. Status per ADR-0003 provenance (FOUND / GUESS / TUNED / DIVERGENCE).

> Complements `docs/pm-reference/00-overview.md` (prose overview); this file is the greppable
> by-category pointer table. One line per entry; detail lives in the linked doc. Append a row when
> a mechanic is researched/validated (spikes #538, #539, …).

The **`Constant`** column names the bare `combat/provenance.py` key for rows that map 1:1 to a single
constant (blank for compound/mechanic rows). `tests/test_tuning_provenance.py` gates it: a keyed row's
`Status` must match the registry's `status` for that key (#635, the #575 Tier-1 consistency gate).

| Category | Mechanic | Status | Constant | pycats value(s) | Local doc | Primary source |
|---|---|---|---|---|---|---|
| Ledge | Ledge-grab intangibility (fixed burst) | FOUND | `LEDGE_INVULN_BASE_FRAMES` | `LEDGE_INVULN_BASE_FRAMES = 23` | [pm-reference/ledge-mechanics.md](./pm-reference/ledge-mechanics.md) → "Validation (#538)" | [SmashWiki — Ledge](https://www.ssbwiki.com/Ledge) / [Edge recovery](https://www.ssbwiki.com/Edge_recovery) |
| Ledge | Ledge intangibility **percent-scaling** (magnitude) | DIVERGENCE → aligning (#543) |  | `+0.3/%` cap `60` (#311) | [pm-reference/ledge-mechanics.md](./pm-reference/ledge-mechanics.md) → "Validation (#538)" | none — PM %-dependence is getup **speed** (≥100%) + hang time, not intangibility magnitude |

> **Flagged discrepancy (→ #536):** the percent-scaling row is a compound (`LEDGE_INVULN_PER_PERCENT`
> `+0.3/%`, cap `LEDGE_INVULN_MAX_FRAMES` `60`), so it carries no single `Constant` key. Note the tag
> mismatch it would otherwise surface: the registry tags `LEDGE_INVULN_PER_PERCENT` **TUNED**, while this
> row reads **DIVERGENCE → aligning (#543)**. Reconciling that tag belongs to #536/#543 (content), not the
> gate — left blank so the gate neither hides nor unilaterally resolves it.

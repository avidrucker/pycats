# Project M rules by category

High-level index of the PM mechanics pycats has researched. Each row points to the detailed
local doc + the primary citation — this file is the map, the local docs are the territory.
PM canon = **Project M 3.6**. Status per ADR-0003 provenance (FOUND / GUESS / TUNED / DIVERGENCE).

> Complements `docs/pm-reference/00-overview.md` (prose overview); this file is the greppable
> by-category pointer table. One line per entry; detail lives in the linked doc. Append a row when
> a mechanic is researched/validated (spikes #538, #539, …).

| Category | Mechanic | Status | pycats value(s) | Local doc | Primary source |
|---|---|---|---|---|---|
| Ledge | Ledge-grab intangibility (fixed burst) | FOUND | `LEDGE_INVULN_BASE_FRAMES = 23` | [pm-reference/ledge-mechanics.md](./pm-reference/ledge-mechanics.md) → "Validation (#538)" | [SmashWiki — Ledge](https://www.ssbwiki.com/Ledge) / [Edge recovery](https://www.ssbwiki.com/Edge_recovery) |
| Ledge | Ledge intangibility **percent-scaling** (magnitude) | DIVERGENCE → aligning (#543) | `+0.3/%` cap `60` (#311) | [pm-reference/ledge-mechanics.md](./pm-reference/ledge-mechanics.md) → "Validation (#538)" | none — PM %-dependence is getup **speed** (≥100%) + hang time, not intangibility magnitude |

# PM-citation coverage gate — findings (#575)

**Role:** RESEARCH / SPIKE · no code. **Ticket:** #575 (detective complement to #571).
**Question:** how to catch PM-touching artifacts whose claims aren't sourced — or that contradict the
provenance registry — systematically, not by luck.

Grounded in the actual repo state (counts below are live as of this spike), and reconciled with the
grill review's F2 (`docs/superpowers/specs/2026-07-05-grounded-claim-protocol-grill.md`), which
pre-answered the two-tier shape. The ratified rule **#562** ("Read the source before asserting") is the
*proactive* half; this is the *detective* backstop.

## The surface, measured

| Surface | State | Gate-able? |
|---|---|---|
| **Value registry** (`combat/provenance.py`) | **~60 constants, all tagged** (23 FOUND / 27 TUNED / 9 GUESS / 5 DIVERGENCE); 4 guards in `test_tuning_provenance.py` (registry↔config drift/orphans/derivation) | **Already gated** — but only registry↔config, nothing touches docs |
| **By-category manifest** (`project-m-rules-by-category.md`) | **~2 mechanic rows** (ledge only); constant sits *inside* a free-form "pycats value(s)" cell (`LEDGE_INVULN_BASE_FRAMES = 23`), not a clean key | **Gate-able after a key column is added** — see Q2 |
| **`pm-reference/` prose** (16 docs) | free-text PM claims; the ledge mislabel lived here | **Audit-only** (lint, false-positive-prone) |
| **Code comments** (~87 "Project M/Melee/Brawl/SmashWiki/PMDT" mentions in `pycats/*.py`) | free-text | **Audit-only** |
| **Ticket bodies** | free-text PM claims | **Audit-only** (out of any test harness) |

**Key measured finding:** the registry is the *strong* store (fully tagged, already guarded); the
manifest is the *weak* one (sparse — 2 rows — and its constant key is embedded in prose, not a field).
The prose/comment surface (~87 + 16) is large and only auditable, not gate-able. This matches grill F2:
the ledge bug lived in prose, which no field-comparison can see.

## Q1 — the PM-touching surface: gate-able vs audit-only
- **Gate-able (deterministic test):** registry↔config (exists); **registry↔manifest** status
  consistency (new, once the manifest has a joinable key).
- **Audit-only (lint + human review):** `pm-reference/` prose, code comments, ticket bodies. A lint can
  *flag candidates* ("PM-name + a claim, no adjacent citation/tag") but will raise false positives —
  review aid, not a hard gate.

## Q2 — extend the existing gate? Yes, in two steps
1. **Add a machine-readable key to the manifest.** Today the constant is buried in the "pycats
   value(s)" cell. Add a dedicated **`Constant`** column (bare `provenance.py` key, or empty for
   mechanics with no single constant). This is the join key Tier-1 needs.
2. **New test (Tier-1) extending `test_tuning_provenance.py`:** for every manifest row that names a
   constant, assert **manifest `Status` == registry `status`** for that key; and a
   `TUNED`/`DIVERGENCE`/`GUESS` constant's manifest row **may not** present a canon (T1) primary-source.
   Deterministic, low false-positive, able-to-fail. Grows in value as the manifest grows.

## Q3 — detection mechanisms compared
| Mechanism | Catches | False-positive | Verdict |
|---|---|---|---|
| **Tier-1 structured test** (registry↔manifest) | store-vs-store status drift | ~none | **Build** — cheap, deterministic; the real automatable win |
| **Tier-2 prose/comment lint** ("PM-name + claim, no nearby cite/tag") | un-cited prose PM claims | **high** (87+16 surface, many legitimate) | **Audit, not gate** — periodic, human-reviewed; opt-in, not CI-blocking |
| **CI-blocking lint on prose** | same | high → blocks legit work | **Reject** — false-positive rate makes it noise |
| **Divergences tracker** (Q4) | standing list of non-canon / contradicting claims | n/a | **Build cheaply** — see Q4 |

**Honest scope (grill F2, restated):** neither tier would have caught the ledge *prose* bug
retroactively — at the time, registry said `TUNED` and the manifest Status also read non-canon; the lie
was in `ledge-mechanics.md` prose. What *prevents* that is the **proactive** rule #562 + the
`grounded-claim` skill (#624) at authoring time. Tier-1's value is **drift** (keeping the stores honest
as they grow); Tier-2's value is **surfacing candidates** for the human, not catching them automatically.

## Q4 — where uncovered / contradictory items go
A **divergences view generated from the manifest**, not a new hand-maintained store: filter the manifest
(and registry) for `Status != FOUND` → the standing list of pycats-invented / diverging / unsourced PM
values. The registry already carries these tags; the manifest already has a Status column. A tiny
generator (or a section in the by-category doc) makes "what do we knowingly diverge on?" a query, not a
lucky find. Un-sourced `GUESS` rows are the debt list (#319 territory).

## Recommendation — seeds a DEV (one, small)

**DEV: Tier-1 registry↔manifest consistency gate** —
1. add a `Constant` column to `project-m-rules-by-category.md` (backfill the ledge rows);
2. extend `tests/test_tuning_provenance.py` with a test asserting, per keyed manifest row,
   `manifest Status == registry status` and no canon-source on a non-FOUND constant (able-to-fail via a
   deliberately mismatched row);
3. add a generated **divergences view** (Status != FOUND) as the Q4 tracker.

**Defer (not now — grill F5, no guessed need):**
- **Tier-2 prose/comment lint** — the 87+16 surface is real but the false-positive rate makes a
  hard gate counter-productive; build only as an *opt-in periodic audit* if drift recurs. The proactive
  rule #562 already covers authoring-time prose.

## Reconciliation (no duplication)
- **#571 / #624** — the proactive skill + config (authoring-time). This is the detective backstop.
- **#562** (ratified) — the rule this gate mechanizes for the *structured* stores.
- **#535** — the citation register (content); Tier-2's tags would cite into it.
- **#536** — owns the ledge content instance; not re-audited here.
- **ADR-0003 / `test_tuning_provenance.py`** — the existing narrow gate Tier-1 extends.

## Out of scope
Implementing the gate (the seeded DEV). Re-auditing `pm-reference/` prose (#536). The register (#535).

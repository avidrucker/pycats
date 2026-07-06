# PM-parity labeling — legend & key

The quick reference for the **three-axis PM-parity labeling system**. If you hit a
`⚠`/`🔬`/`❓` in source, a `FOUND`/`GUESS`/`TUNED`/`DIVERGENCE` in the provenance
registry, or a 🟢/🟡/🔴 in the parity report and want to know *what it means and where
it belongs* — this is the page.

- **Audience:** contributors/agents at write-time. It answers "I have an unsourced
  value / an open question — what do I write, and where?" with no further reading.
- **This is the key, not the reasoning.** The *why* (council analysis, de-confliction,
  pre-mortem) lives in the design-of-record, [`docs/research/analysis-brainstorming-research-233.md`](./research/analysis-brainstorming-research-233.md)
  (#448). Rollout is tracked by the umbrella **#451**.

Each axis has **one emoji/label family** and **one home**. Never mix them.

---

## Axis A — open work (inline, greppable)

Marks values/decisions still **unresolved vs Project M**, written inline at the code
site so `grep` can find them. Home: **source comments**.

| Glyph | Codepoint | Name | Means |
|---|---|---|---|
| `⚠` | U+26A0 | guessed | value present but **unconfirmed** vs PM |
| `🔬` | U+1F52C | needs research | a concrete sourcing/derivation is **queued** |
| `❓` | U+2753 | open question | an **undecided** design/behaviour point |

Usage rules (full text in [RULES.md](../RULES.md) → "PM-parity markers"):

- **`⚠` and `🔬` co-occur** (`⚠🔬`) on a guessed value that is *also* queued for
  sourcing. `grep ⚠` = every unpinned value; `grep 🔬` = the subset with an active
  sourcing action.
- **Mark only unresolved things.** A value whose provenance is *resolved* (a
  `FOUND`/`TUNED`/`DIVERGENCE` row on Axis B) gets **no** marker — the registry
  classification is the resolution.
- **Convention once.** Mark a documented, repeated convention in one place (a module
  docstring), not on every repetition — repeated markers become noise ("marker soup").
- **An `❓` cites its ticket** where one exists (`❓ … — see #466`), so the code points
  at the discussion instead of duplicating it.

---

## Axis B — provenance (the #233 registry, machine-tracked)

Records **where each tuning value came from** — one row per constant in
[`pycats/combat/provenance.py`](../pycats/combat/provenance.py), guarded against drift.
Home: **the registry** (text status on each `Provenance(...)` entry). These are *text
statuses, never emojis.*

| Status | Means |
|---|---|
| `FOUND` | traced to a **cited canon value** (rukaidata / SmashWiki / a PM changelog / an in-repo `docs/research/*` finding) |
| `GUESS` | **unsourced** / placeholder — the value stands but no source backs it yet |
| `TUNED` | a **deliberate design value**, not seeking canon (a game-designer decision) |
| `DIVERGENCE` | an **intentional departure** from PM, documented as such |

A value change lands its basis here as `FOUND` (sourced) or `TUNED` (designer-chosen) —
never presented as sourced when it is a guess. See [RULES.md](../RULES.md) →
"Changing values" and ADR-0003.

---

## Axis C — parity light (generated report only, derived from B)

An **at-a-glance status** rendered *from Axis B* into a generated report — never written
by hand. Home: **the generated [`parity-status.md`](parity-status.md) report** (Pass C;
run `python parity_report.py` to regenerate it from the registry).

| Circle | Means | Derived from B |
|---|---|---|
| 🟢 | valid + checked | `FOUND` |
| 🟡 | inferred / good-enough | `TUNED` or `GUESS` |
| 🔴 | unchecked / invalid | `DIVERGENCE` or **absent** (no registry row) |

---

## The three invariants (from #448)

1. **One emoji family per axis, one home each.** A (`⚠🔬❓`) lives inline; B (text
   statuses) lives in the #233 registry; C (`🟢🟡🔴`) lives in the generated report.
2. **Colored circles never appear in source.** 🟢/🟡/🔴 are *report-only* — a green
   is *computed* from a cited `FOUND` row, never hand-stamped. (Pre-mortem risk #1:
   "green rot" — a hand-typed green that outlives its source.)
3. **C is derived from B, not authored.** The report is regenerated from the registry;
   if a status changes on B, C changes on the next render. No parallel hand-maintained
   status.

---

## How to grep each axis

```bash
grep -rn '⚠'  pycats/                       # Axis A: every unpinned value
grep -rn '🔬' pycats/                       # Axis A: the sourcing backlog
grep -rn '❓'  pycats/                       # Axis A: open design questions
grep -nE 'FOUND|GUESS|TUNED|DIVERGENCE' pycats/combat/provenance.py   # Axis B: provenance rows
# Axis C: read the generated parity-status.md report (do not grep source for circles)
```

---

## Which do I use? (decision hint)

- **Unconfirmed value, no action queued** → `⚠` inline.
- **Value queued for sourcing/derivation** → `🔬` (with `⚠` if the value is also a guess).
- **Undecided design/behaviour point** → `❓`, citing its decision/research ticket.
- **Recording where a value came from** → a `FOUND`/`GUESS`/`TUNED`/`DIVERGENCE` row in
  the #233 registry (`combat/provenance.py`).
- **Want the at-a-glance status** → read the generated parity report (Axis C); don't
  hand-write a circle.

---

## See also

- [`docs/research/analysis-brainstorming-research-233.md`](./research/analysis-brainstorming-research-233.md) — design-of-record (#448): the reasoning, de-confliction, pre-mortem.
- [RULES.md](../RULES.md) → "PM-parity markers" and "Changing values" — the enforced conventions.
- [`docs/project-m-parity.md`](./project-m-parity.md) — where pycats deliberately diverges from Project M.
- [`docs/current-parity-progress-report.md`](./current-parity-progress-report.md) — the standing parity progress narrative.
- Umbrella **#451** (rollout), Axis A **#408**, Axis B **#233** (registry + ADR-0003).

# Grounded-Claim Protocol — grill review (critical, code-grounded)

**Status:** COMPLETE · **Date:** 2026-07-05 · **Reviewer:** FIG (opus-4.8) · via `/grill-with-docs`
**Subject:** `2026-07-05-grounded-claim-protocol-design.md` (#611) · **Revisions applied:** #620

A relentless critical pass over the design spec, each finding grounded in the actual code
(`pycats/combat/provenance.py`, `docs/project-m-rules-by-category.md`) rather than assumption. Five
substantive findings; all five resolved and folded back into the spec. Kept as a reference so a future
reader sees *why* the spec reads the way it does — and which of its claims were walked back.

## Method
Explored the code before grilling, so each challenge cites evidence. Two of the spec's load-bearing
claims did not survive contact with the registry's real data model.

---

## Finding 1 — the quote test contradicts the existence of TUNED/DIVERGENCE values
**Evidence.** `provenance.py`: `MAX_FALL_SPEED` (DIVERGENCE) `source` = *"DIVERGENCE: pycats uses…the
split is not modelled"*; `LEDGE_INVULN_PER_PERCENT` = **TUNED**, *"pycats percent-scaling…no single
canon curve."* These values have **no primary source by construction.**
**Problem.** The headline hardening *"grounded = a verbatim supporting sentence"* is **impossible** for
them. Literally applied, the fast path forces every use of a TUNED value through the consent gate
forever — the guaranteed consent-fatigue death the pre-mortem warned about.
**Resolution (accepted).** **Two grounding authorities:**
- *Canon-grounded* (external-canon claims, `FOUND` values) → authority = a **verbatim primary quote**;
  quote test applies.
- *Decision-grounded* (`TUNED`/`DIVERGENCE`/pycats-invented) → authority = the **provenance record +
  deciding issue** (e.g. "TUNED, #543"), not a canon quote; the claim carries its non-canon tag but
  does **not** gate.
- The gate fires only when a claim is **neither** — no quote *and* no record — i.e. genuinely from
  memory. That "neither" bucket **is** `GUESS`, and it is a **debt to drive to zero** (every governed
  value should end up in one of the two authorities; cf. the #319 value-sourcing pass).

## Finding 2 — the consistency check (#575) would NOT have caught the bug that motivated it
**Evidence.** At the time of the ledge bug: registry `LEDGE_INVULN_PER_PERCENT` = **TUNED** (correct);
manifest Status column = **DIVERGENCE → aligning** (also non-canon). The lie lived only in **prose**
(`ledge-mechanics.md` + the #311 commit framed percent-scaling as *"true PM edge-hog"*).
**Problem.** A structured status-vs-status join finds **nothing** — both structured fields already read
"non-canon." The gate as specced does not catch the exact thing it was born from. Overclaiming it is
the retrieval-trust "citations make wrong answers credible" trap, aimed at ourselves.
**Resolution (accepted).** Split #575, and **drop the overclaim**:
- *Tier 1 — structured drift test* (mechanizable; extends `test_tuning_provenance.py`): per constant,
  manifest Status == registry status; a TUNED/DIVERGENCE/GUESS constant's manifest row can't present a
  canon primary-source. Catches **store-vs-store drift**.
- *Tier 2 — prose-tag convention + heuristic lint* (the bug's real territory): every PM-mechanic
  *sentence* in `pm-reference/` carries an inline tag or a manifest-row citation; a lint flags
  "canon-word near a mechanic/constant with no adjacent tag" for **human review** (audit, not a hard
  gate — false-positive-prone).
- **Named truth:** what *prevents* the prose-mislabel is the **proactive quote test at authoring time**
  (#571), not the detective gate. #575's real value = drift-catch + enforcing the tagging convention.

## Finding 3 — the consent gate assumes a human is watching; fleet mode has none
**Evidence.** pycats runs fleet mode (parallel worktrees; `.claude/orchestrate.json`); the gate says
*"emit block, WAIT for yes/no."*
**Problem.** With no human on that agent, the spec defines no behavior — block-forever (deadlock),
proceed-with-GUESS (theater), or silent-drop (work lost) are all possible and none is chosen.
**Resolution (accepted).** Gate = **halt-and-record, never block-forever**, degrading by mode:
- *Interactive* → synchronous proceed / cite / drop (as specced).
- *Autonomous/fleet* → may **not** proceed with the ungrounded claim; either grounds it, or
  **withholds + records a grounding-debt row** (GUESS entry / ticket comment / log line) for async
  review. Default = withhold + record.
- **The deviation log = the async consent queue = the gate-fire tally store** (one store, not three).

## Finding 4 — "in-repo fact" is too broad; literally it governs every coding turn
**Evidence.** Governed scope includes in-repo facts; agents assert about code on nearly every edit.
**Problem.** If all such assertions are governed, friction is crushing and fatigue guaranteed; the spec
never defines when an in-repo claim *becomes* governed.
**Resolution (accepted).** Govern an in-repo claim only when **BOTH**: (1) **not in view** — asserted
from memory/inference, not a file being read; **and** (2) **decision- or artifact-bearing** — feeds a
commit, ticket, doc, classification, or closing summary. That is exactly the **#363** shape (a v1
classification from a remembered title). Normal reasoning about an open file is fast-path, not gated.

## Finding 5 — proportionality: two observed failures, a five-piece build
**Problem.** Applying the spec's own "no building on guessed need" rule to its roadmap: only **skill +
RULES line** prevent the two observed failures. #575 prevents neither (Finding 2). **Freshness
metadata** mitigates stale-evidence, which has **not** bitten — building it now is building on guessed
need. The **gate-fire tally** can't be measured before a gate exists.
**Resolution (accepted).** **Sequence, don't bundle:**
1. *MVP* — `grounded-claim` skill + RULES line (prevents both observed failures).
2. *Next* — #575 (Tier-1 test; Tier-2 lint audit).
3. *Deferred, evidence-gated* — freshness metadata (until a stale-evidence incident) + gate-fire tally
   (until the gate fires enough to measure fatigue). The roadmap obeys the protocol's own rule.

---

## Data-model correction (folded into the spec)
The spec's Store interface `{tag, quote, source, doc, const, last_validated, ticket}` **overstated**
what exists. Real `Provenance` fields: **`value, unit, source, status, issue, derivation`** — no
`quote`, no `last_validated`, no `doc`. And `source` is a **reference** ("SmashWiki:Mario_(PM); #120"),
**not** a verbatim sentence. Implication: **canon-grounding's verbatim quote does not live in the
registry** — it lives in the `pm-reference/` doc the `source` points at (or the #535 citation register).
The skill must fetch the quote *there*, not from `provenance.py`.

## Open nit (deferred to writing-plans)
**Where the reflex RULES line lives.** The spec said "fold into *Changing values*," but #562
(cite-primary-for-mechanics) is arguably the more natural host, and the general "read the source before
asserting" is broader than either. Placement, not substance — decide during planning.

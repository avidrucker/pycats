# ADR-0007 — Append-only Decision Log ledger for game-design rulings

- **Status:** Accepted
- **Date:** 2026-07-07

## Context

pycats records decisions in two places today. **ADRs** (`docs/adr/`, per ADR-0001) hold
significant *architecture/design* decisions as one full-prose file each. **`pycats/combat/
provenance.py`** (per ADR-0003) holds *per-value tuning provenance* — `FOUND` / `TUNED` /
`DIVERGENCE` rows, one per constant, with the deciding issue.

Neither covers a large middle class: **game-design `decision:` ticket rulings** — a tuning
*direction*, a surrogate-value pick (e.g. #491), a divergence choice (e.g. #543), the CPU
human-error direction (#704). These are deliberately not ADR-worthy (they're rulings, not
architecture) and don't always pin a single value, so they have been recorded only inside the
ratified ticket. The result: **no scannable, chronological history** of what game-design
rulings were made, when, and where each full record lives. ADR-0001 named this exact gap —
it cites the #56 architecture review's recommendation to "seed a decision log" — but only the
per-file ADR mechanism was built; the index never was.

## Decision

We will keep an **append-only Decision Log** at `docs/decisions-ledger.md`: one row per
ratified `decision:` ticket — `Date · Decision (issue #) · Area · Ruling (one line) · Record`
— newest-last. The row is appended **in the same change that closes** the `decision:` ticket
(wired into RULES → *Closing work*); because that row is a committed artifact, such a ticket
closes via the normal `Closes #N` + `pmtools close` path rather than the commit-less no-code
path.

It is an **index, not a replacement**: full-prose architecture decisions stay in ADRs, and
per-value provenance stays in `provenance.py`; the ledger's `Record` column points at whichever
holds the full decision. As with ADRs, a row is never edited to reverse a decision — a reversal
is a **new row** citing the superseded issue.

## Consequences

- **Easier:** one chronological answer to "what game-design rulings have we made, when, and
  where is each recorded?" — closing the discoverability gap ADR-0001 / #56 named.
- **Harder (upkeep):** closing a `decision:` ticket now carries a ledger-append step; a ruling
  is not fully recorded until its row lands. Decision tickets thereby gain a committed artifact
  (their ledger row) and close via `pmtools close`, not the commit-less `gh issue close` +
  `pmtools release` path (which remains for research / comment-only tickets).
- **Explicitly not:** a back-fill of past rulings (following ADR-0001's no-back-fill precedent —
  only rulings from this convention forward are logged; the seed rows #705 and #704 are the
  start), and not a replacement for ADRs or `provenance.py`.

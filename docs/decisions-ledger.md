# Decision Log

> Append-only ledger of ratified **game-design `decision:` tickets** — the chronological
> history [ADR-0001](adr/0001-record-architecture-decisions.md) recommended (via #56) but
> never built. **Newest-last.** See [ADR-0007](adr/0007-decision-ledger.md) for why this
> exists.
>
> **What belongs here:** a ratified `decision:` ticket — a game-design ruling the human
> designer made (a tuning direction, a surrogate-value pick, a divergence choice). This is
> the *index*; the full record lives wherever the `Record` column points.
>
> **What does NOT belong here:** architecture decisions (those are full-prose **ADRs** in
> [`docs/adr/`](adr/)) and per-value tuning provenance (those are `FOUND`/`TUNED` entries in
> [`pycats/combat/provenance.py`](../pycats/combat/provenance.py), ADR-0003). This ledger
> **complements** both.
>
> **Append-only rule:** never edit a row to reverse a decision; a reversal is a **new row**
> citing the superseded issue (mirrors ADR-0001's supersede rule). Append the row **in the
> same change that closes** the `decision:` ticket (RULES → *Closing work*).

| Date | Decision (issue #) | Area | Ruling | Record |
|---|---|---|---|---|
| 2026-07-07 | [#705](https://github.com/avidrucker/pycats/issues/705) | area:tracker | Establish this append-only Decision Log ledger (+ ADR-0007 + RULES wiring) | [ADR-0007](adr/0007-decision-ledger.md) |
| 2026-07-07 | [#704](https://github.com/avidrucker/pycats/issues/704) | area:combat | Approve near-miss + accidental-press + per-character CPU tuning as pycats-custom difficulty flavor (not PM parity) | [#704 ruling](https://github.com/avidrucker/pycats/issues/704#issuecomment-4910662301); `provenance.py` `TUNED` as each DEV lands (#702 follow-ups) |

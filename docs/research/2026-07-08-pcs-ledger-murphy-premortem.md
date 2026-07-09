# PCS claim-ledger — murphy-jutsu pre-mortem (RAW INPUT)

> ⚠️ **Status: raw, unvalidated pre-mortem input — NOT a finding.** This is the unreviewed
> output of a single `murphy-jutsu` pass (2026-07-07/08 session) on the idea of formalizing the
> grounded claim/question ledger (`PCS-*` IDs + evidence tiers + falsifiability screen) into a
> pycats process. It exists to give **#712** a durable source for its "map the risk register →
> mitigations" acceptance criterion. The likelihoods, blast ratings, and mitigations here are
> **first-pass judgments that #712 must reshape, verify, and validate** — do not cite any line
> below as settled. Committed (rather than left in the gitignored ledger) only so it travels to
> whoever claims #712, including a fleet worktree.

**Target of the pre-mortem:** formalize the PCS claim-ledger into a repeatable pycats skill/process.
**Success:** agents ground claims fast and the ledger stays trustworthy.
**Catastrophe:** it becomes an authoritative-looking graveyard of unverified/stale claims that
decisions quietly ride on.

**Lenses applied:** `murphy-retrieval-trust` (the ledger *is* a citation store), `murphy-hallucinated-output`
(misread citations), `murphy-complexity-invoice` (hand-maintained notes system), `murphy-context-rot`
(ledger-as-memory), plus the domain checklist (people/ops, scope-vs-GitHub-SOT).

---

## Risk register (first-pass — to be validated by #712)

### 🔴 High (act before proceeding)

**R1 — Verification backlog → authoritative graveyard.** likelihood: H · blast: H
- **How:** asserting is cheap and front-loaded; verifying is tedious and back-loaded. The
  asymmetry guarantees `unverified` grows and the verified ratio rots. Readers then treat the
  ledger's existence as authority and cite T2/T3 claims as settled.
- **Warning signs:** unverified count climbs monotonically; tickets reference claims still at T2/T3.
- **Mitigation:** a discharge gate — a research ticket can't *close* while a claim it **rests-on**
  is unverified; surface verified/unverified counts; make `rests-on` links first-class so a
  decision flags its own soft premises.

**R2 — Stale citation pinned to a moving ref.** likelihood: H (over months) · blast: H
- **How:** citations point at `master`; upstream edits the line; the ledger still reads "verified
  TRUE" against text that no longer says it — the RAG "cited a source that says the opposite"
  failure, aimed at our own store. (We already have this gap: every current citation says `master`.)
- **Mitigation:** pin every citation to a **commit SHA** + keep the verbatim quote inline; a
  periodic re-verify that flags drift; treat `master`-pinned citations as expiring.

**R3 — Misread-but-marked-verified (false T1).** likelihood: M–H · blast: H
- **How:** right file, wrong read — a dropped negation or an over-generalized scoped sentence gets
  stamped T1. Already happened this session (C-001's literal-names over-claim; caught by luck).
- **Mitigation:** enforce "verified requires the verbatim quote pasted, and the quote must
  *entail* the claim"; independent re-read (author ≠ verifier) for load-bearing claims.

### 🟡 Medium (mitigate or schedule)

**R4 — Maintenance ceremony → abandonment (complexity invoice).** likelihood: H · blast: M
- Hand-maintained IDs + moving entries across 5+ files + tiers + dates outweighs payoff for small
  spikes → agents skip it or it rots (the "4000 useless notes" second-brain).
- **Mitigation:** single registry + generated views; a lint script; a **lightweight mode** scaled to stakes.

**R5 — PCS-ID races across fleet agents.** likelihood: M · blast: M
- Two concurrent sessions mint `PCS-C-029` at once (the pmtools ticket-number race, again).
- **Mitigation:** monotonic counter file with a lock, or namespace IDs per agent (`PCS-FIG-C-001`).

**R6 — Shadow issue tracker.** likelihood: M · blast: M
- Claims/questions accrete assignees/TODOs/priorities and start competing with GitHub issues,
  violating "GitHub is the single source of truth."
- **Mitigation:** hard scope — ledger holds claims/questions/evidence only; no assignee/due-date/
  work-priority fields; anything actionable graduates to a GitHub issue; stays gitignored/throwaway.

**R7 — Composite-claim loophole.** likelihood: M · blast: M
- Composites asserted directly ("it's TRUE") when only some children are verified.
- **Mitigation:** composite verdict is purely **derived** (TRUE iff all children verified-TRUE;
  FALSE if any child FALSE; else PENDING); composites carry no independent verdict field;
  verification only ever happens at the atomic child.

**R8 — Ledger drifts from reality.** likelihood: M · blast: M
- Claims about pmtools/git-bug captured, tools change, ledger not re-checked; decisions ride on
  outdated verified claims.
- **Mitigation:** dating (`asserted` / `verified` / citation `as-of` SHA) + a staleness horizon
  after which `verified` auto-demotes to `re-verify`.

### 🟢 Low / Accepted
- **Tier-gaming** (mark T3 as T1) — L; the verbatim-quote requirement makes faking visible.
- **Over-fit to git-bug** — L/M; validate the schema on a second, different topic before adopting.
- **Accepted:** the 2026-07-06 GitHub-egress incident (ledger PCS-C-027) stays REPORTED/unverifiable
  — context, not load-bearing.

**Most-likely-to-actually-bite:** R1 (backlog) and R2 (stale citations) — slow failures that look
fine until a decision cites a rotted claim. R4 (abandonment) is the likeliest way it just dies.

---

## Two design decisions this pre-mortem informed (also for #712 to ratify)

- **Composite claims** — a `composite` type (`PCS-CC-###`) listing atomic child IDs, verdict
  **derived only** (see R7). Gives a readable rollup without reopening the boolean ambiguity the
  falsifiability screen just closed.
- **Dating** — three dates: `asserted:` (first recorded), `verified:`/`refuted:` (verdict reached),
  and per-citation `as-of:` a **commit SHA** (not a moving ref — see R2). Questions get
  `opened:`/`answered:`.

## Provenance
`murphy-jutsu` + sub-lenses (`retrieval-trust`, `hallucinated-output`, `complexity-invoice`,
`context-rot`). Worked example / first ledger: the gitignored `git-bug-pmtools-research/`. Drives
**#712** (formalize the ledger). Reconcile with the `grounded-claim` skill + RULES → "Read the
source before asserting."

**Canonical source of this content:** the pre-mortem comment on **#712**
(`github.com/avidrucker/pycats/issues/712#issuecomment-4920453625`); this doc is the durable
committed copy filed via **#713** (a faithful persist — validation/reshaping happens in #712).

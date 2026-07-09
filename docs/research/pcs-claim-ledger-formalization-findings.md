# PCS claim-ledger — formalization findings & decision

**Ticket:** #712 (RESEARCH) · **Role:** RESEARCH · no production code lands here.
**Inputs:** the worked-example ledger `git-bug-pmtools-research/` (gitignored); the `murphy-jutsu`
pre-mortem (`docs/research/2026-07-08-pcs-ledger-murphy-premortem.md`, #713); the `grounded-claim`
skill (`~/.claude/skills/grounded-claim/SKILL.md`) + `.claude/evidence.json`; RULES → "Read the
source before asserting" (#562).

---

## TL;DR — recommendation

Adopt the PCS claim-ledger as a **sibling skill (`claim-ledger`) that depends on and reuses
`grounded-claim`'s authority model and config** — **not** a fork, **not** folded into
grounded-claim's fast path (Q7). Concrete schema:

- **One registry table** (status column) as source of truth, not entries moved between files (Q1) — kills the maintenance/abandonment risk.
- **`PCS-<TYPE>-<NNN>`** IDs (`C` claim / `Q` question / `CC` composite), **per-agent-namespaced when a ledger is fleet-shared** (Q2).
- **Composite claims** (`PCS-CC-###`) carry a **derived-only** verdict — never asserted (Q3).
- **Three dates + SHA-pinned citations + a staleness horizon** (Q4).
- **"Verified" is enforced**: verbatim quote inline, quote must *entail* the claim, citation pinned to a **commit SHA**, author ≠ verifier for load-bearing claims (Q5).
- **Epistemic-only scope**: no assignee/due-date/work-priority fields; actionable items graduate to GitHub issues; ledger stays gitignored/throwaway (Q6).
- **Two modes**: a lightweight single-file mode for small spikes, the full registry for multi-session/>~10-claim investigations (Q8).

This is a decision doc; the skill + lint script are a **downstream ticket**, named below, not built here.

---

## Q7 (framing) — extend `grounded-claim`, don't fork it

**Ruling: a new sibling skill `claim-ledger` that *reuses* `grounded-claim`'s definitions and
`.claude/evidence.json` config.** Grounding for the ruling (read this session, not recalled):

| | `grounded-claim` (exists) | `claim-ledger` (proposed) |
|---|---|---|
| **Unit** | one assertion, at the moment you make it | many claims/questions, accumulated over an investigation |
| **Lifetime** | ephemeral (cite-or-gate, then done) | durable (IDs persist, discharged over time) |
| **Trigger** | "about to assert/classify a governed fact" | "running a multi-claim research investigation" |
| **Output** | a cited claim, or an `EVIDENCE-DEVIATION` gate | a persistent ledger + a findings doc |

They are **complementary halves of one discipline**, and the ledger is best read as the durable
substrate grounded-claim already gestures at:

- grounded-claim §4 says an ungrounded claim in fleet mode should **"withhold + log a grounding-debt
  row (a `GUESS` … note) for async review."** The PCS ledger's **`unverified` bucket is exactly that
  grounding-debt log, made first-class and structured.**
- grounded-claim's two authorities — **(1) verbatim primary quote; (2) provenance record + deciding
  issue** — are the ledger's **T1 tier**. The ledger's T1/T2/T3 *grades* grounded-claim's binary
  "authority in hand / not in hand."
- grounded-claim's `GUESS` / `EVIDENCE-DEVIATION` gate ≈ the ledger's `unverified` / `REPORTED` /
  `INFERENCE` statuses.
- Both are **config-driven off `.claude/evidence.json`** (`canon`, `evidence_map`, `value_registry`,
  `governed_domains`). The ledger **must reuse that file**, not invent a parallel config.

**Why sibling, not folded in:** grounded-claim's value is a *fast per-assertion reflex* ("authority
in hand → cite inline and proceed. No gate. keep it fast"). Bolting a multi-claim ledger schema onto
it would bloat the hot path. **Why not a fork:** a rival skill with its own grounding rules would
diverge from #562 — the exact failure the discipline exists to prevent. So: separate trigger, shared
vocabulary + config; `claim-ledger`'s SKILL.md references grounded-claim for the authority
definitions rather than restating them.

---

## Q3 — Composite claims (derived verdict only)

**Allow composites; make the verdict computed, never asserted.**

- A composite `PCS-CC-###` stores a statement + an ordered list of **atomic child claim IDs**. It has
  **no independent verdict field.**
- **Derived verdict:** `TRUE` iff every child is `verified-TRUE`; `FALSE` if any child is
  `verified-FALSE`; else `PENDING`.
- Verification only ever happens at the **atomic child**. A composite is a **readable rollup**, not a
  claim you can prove directly.

This restores the convenience of a high-level claim ("git-bug is a workable offline mirror") without
reopening the boolean ambiguity the falsifiability screen closed — the rigor stays at the leaves.
Directly mitigates risk **R7** (composite loophole).

*Example:* `PCS-CC-001 "git-bug replicates over plain git" := {PCS-C-001, PCS-C-002, PCS-C-003}` →
all three verified-TRUE → composite reads TRUE, derived.

---

## Q4 — Dating & staleness

**Three dates + SHA-pinned citations + a staleness horizon.**

- Per claim: **`asserted:`** (first recorded) and **`verified:` / `refuted:`** (verdict reached).
- Per question: **`opened:` / `answered:`**.
- **Per citation: `as-of:` a commit SHA** (or immutable permalink), **never a moving ref like
  `master`.** This is the single most important field — it is what makes a stale citation
  *detectable*. (The current worked-example ledger cites `master` throughout — a live instance of
  risk **R2**.)
- **Staleness horizon:** a `verified` claim whose citation is (a) pinned to a moving ref, or (b) older
  than a set horizon (recommend **90 days**) without re-check, auto-demotes to **`re-verify`**. This
  makes drift (**R8**) visible instead of silent.

---

## Q5 — Evidence-tier enforcement (make "verified" hard to fake or misread)

Tiers: **T1** primary verbatim · **T2** official secondary (paraphrase) · **T3** memory/inference.
**Only T1 promotes a claim to `verified`.** Enforcement rules (mitigating **R3**):

1. **Verbatim quote inline** — a verified claim must carry the exact supporting sentence, not a source
   name/URL (grounded-claim's rule: "A source *name* or URL is **not** enough — you must hold the
   sentence").
2. **The quote must *entail* the claim** — reviewer confirms the sentence actually supports the
   assertion (catches the misread-but-verified failure that already bit `PCS-C-001` this session).
3. **Citation pinned to a commit SHA** (Q4).
4. **Author ≠ verifier** for load-bearing claims — the person who asserted it doesn't get to stamp it
   verified (role separation; grounded-claim's detective backstop #575 is the after-the-fact half).

A small **lint script** (downstream) enforces the mechanical subset: no duplicate IDs, no ID in two
statuses, every `verified` row has a quote + SHA, every `INFERENCE` lists the premises it rests on.

Status vocabulary (earned by the worked example): `unverified` · `verified{TRUE|FALSE}` · `bad`
(archived, failed the falsifiability screen) · **`INFERENCE`** (sound but premises unverified) ·
**`REPORTED`** (objective + falsifiable-in-principle but not reproducible by the agent — e.g. a
second-hand incident; distinct from TRUE/FALSE so it doesn't masquerade as checkable).

---

## Q6 — Coexistence with GitHub-issues-as-source-of-truth (no shadow tracker)

**The ledger is epistemic-only.** It stores **claims, questions, and evidence** — *what is true and
how we know it*. It must **not** carry:

- **assignee**, **due-date**, **work-priority**, or **work-status** (todo/doing/done) fields.

The tripwire (mitigating **R6**): the moment an entry describes *work someone should do*, it
**graduates to a GitHub issue** (the single source of truth per RULES → Work tracking). The ledger
stays **gitignored / throwaway by default**; its one committed graduation artifact is the **findings
doc** (like this one). A research question's *investigative* priority (P1/P2/P3, "which to answer
next") is fine — that is epistemic sequencing, not work assignment.

---

## Q1 — Registry model (one file with a status column)

**One registry table as source of truth; not entries physically moved between
verified/unverified/open/answered files.** Rationale (mitigating **R4** maintenance-abandonment and
the dup-ID risk the worked example surfaced): moving entries between files loses the all-IDs-at-a-
glance view and invites an ID living in two files. A single table keyed by ID, with a **status
column**, keeps integrity checkable and "what's left to verify" is just a filter.

Recommended columns: `ID | type | statement | status | tier | verdict | asserted | verified |
citation(SHA + quote) | rests-on`. Separate human-readable *views* (e.g. an "open questions" render)
are **generated** from the registry, never hand-maintained in parallel. `bad-claims` stays a separate
archive (it's out of the live set by design), and `scratchpad` / `meta-process-notes` stay free-form.

---

## Q8 — Lightweight vs heavyweight mode (scale ceremony to stakes)

Two modes so small spikes aren't taxed into abandonment (**R4**):

- **Lightweight (default for small spikes):** a single `claims.md` with inline tags —
  `- [T1✓] <claim> — <quote> @<sha>` / `- [unverified] <claim> — how-to-verify`. No separate files,
  no composites, no dating beyond a header date. Escalate when it grows.
- **Heavyweight (multi-session, or >~10 claims, or feeds a decision):** the full registry table +
  composites + dating + staleness + lint + author≠verifier.

Escalation trigger: cross ~10 live claims **or** span more than one session **or** the ledger will
feed a ratified decision → switch to heavyweight.

---

## Risk register → mitigation map (from the #713 pre-mortem)

| Risk (pre-mortem) | Mitigation in this schema |
|---|---|
| **R1** backlog → authoritative graveyard | A research ticket can't **close** while a claim it `rests-on` is unverified; registry surfaces verified/unverified counts. |
| **R2** stale `master`-pinned citation | Q4: citations pinned to a **commit SHA** + verbatim quote; staleness horizon auto-demotes to `re-verify`. |
| **R3** misread-but-verified | Q5: quote-must-entail-claim + author ≠ verifier. |
| **R4** maintenance → abandonment | Q1 single registry + generated views; Q8 lightweight mode; lint script. |
| **R5** PCS-ID races (fleet) | Q2: per-agent-namespaced IDs (`PCS-FIG-C-001`) when fleet-shared, or a locked counter. |
| **R6** shadow issue tracker | Q6: epistemic-only fields; actionable → GitHub issue; gitignored. |
| **R7** composite loophole | Q3: composite verdict **derived only**, no independent verdict field. |
| **R8** ledger drifts from reality | Q4: dating + staleness horizon → `re-verify`. |
| Tier-gaming / over-fit (Low) | Verbatim-quote requirement makes faking visible; validate the schema on a **second topic** before adoption. |

---

## Reconciliation with `grounded-claim` + RULES #562

No conflict — the ledger is a faithful extension of the ratified reflex:

- RULES #562 "**label inference as inference**" → the ledger's **`INFERENCE`** status.
- RULES #562 "**never issue a refuted/confirmed verdict from a chain of reasoning over secondary
  facts**" → the ledger's rule that **only a T1 primary quote promotes a claim to
  `verified{TRUE|FALSE}`**; T2/T3 stay `unverified`/`INFERENCE`.
- RULES #562 primary-source **T1/T2 tiers** → the ledger's **T1/T2/T3** grades (it adds T3 for
  memory/inference).
- grounded-claim's **`GUESS` grounding-debt** → the ledger's **`unverified`** bucket.
- grounded-claim's **`.claude/evidence.json`** config (`governed_domains: ["canon","in-repo-fact"]`)
  → **reused** by `claim-ledger`; no parallel config.

---

## Downstream tickets (named, not filed — one at a time, after this doc)

1. **DEV/docs — build the `claim-ledger` skill** — `SKILL.md` (sibling to grounded-claim, references
   its authority model) + the registry template + the lint script. The load-bearing slice.
2. **docs — extend `.claude/evidence.json` (or a sibling `ledger.json`) schema** for ledger config
   (modes, staleness horizon), only if the skill needs config beyond what evidence.json already holds.
3. **research(validation) — dry-run the schema on a second, different investigation** (not git-bug)
   before promoting `claim-ledger` from proposal to standard — guards the over-fit risk.

## Out of scope (per #712)
Building the skill; migrating the throwaway `git-bug-pmtools-research/` ledger; changing RULES or the
`grounded-claim` skill (this doc only recommends); the git-bug ↔ pmtools investigation itself (#654's
tracks — used here only as the worked example).

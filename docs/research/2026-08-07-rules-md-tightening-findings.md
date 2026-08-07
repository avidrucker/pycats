# RULES.md tightening — findings & dedup log (#1285)

**Date:** 2026-08-07 · **Ticket:** #1285 (`chore(docs): review + tighten RULES.md`) · **Agent:** banana

Method: an author-assess (self-audit) prose pass over `RULES.md`, followed by a `/grill-with-docs`
interview to fix the scope of the tightening with the owner one decision at a time. This doc is the
ticket's required "findings list + every weakened/moved rule named" artifact.

## 1. Scope reality

`RULES.md` is ~95% normative-directive prose ("do X", "never Y") defended by argument and named
precedent. Normative rules are not empirical claims, so the author-assess engine (construct-match,
tier-vs-hedge) bites only on the *"Why:"* justification clauses that smuggle a factual/causal claim.
The larger wins the ticket targets (over-length, redundancy) are structural — handled by the dedup
pass in §3, not the claim audit.

Decision (owner, grilling): **medium pass** — dedup + tighten, no section reorder, no precedent
citations cut, **zero rules dropped**. Every merge named below.

## 2. Author-assess findings

Severity: 🔴 must-fix · 🟠 should-fix · ⚪ note. Disposition records the owner's grilling verdict.

| # | Sev | Location | Finding | Disposition |
|---|-----|----------|---------|-------------|
| 🟠1 | 🟠 | *Relationship labels* → "When to apply" → **Why:** | "GitHub's native sub-issue links … don't surface in the issue **list** view" is a bare-present-tense claim about a third-party UI with no as-of anchor — it decays if GitHub changes. Its neighbor does it right ("`pmtools status` … **today** (#171)"). | **APPLIED** — added "(as of GitHub's 2026 UI)". |
| 🟠2 | 🟠 | *Referencing code & docs* → first bullet | "Line numbers drift **the moment a file changes**" over-states the mechanism — only edits *above* the referenced line shift it. | **DECLINED by owner** — keep "the moment a file changes". Recorded for the record; not a defect that blocks. |
| ⚪3 | ⚪ | *Fixing bugs* → able-to-fail bullet | "A test that has never been red **proves nothing**" reads as an unscoped universal; a never-red test's real gap is that it may not guard *this fix*. | **APPLIED (owner wording)** — expanded to "(it may assert the wrong thing, never reach the intended branch, nor whether a given fix is even guarded against regressions)". |
| ⚪4 | ⚪ | *Fixing bugs* → able-to-fail bullet | "a footgun that **has recurred repeatedly**" — unquantified frequency vs. the doc's precise-count habit elsewhere ("bit **thrice**"). | **DROPPED by owner** — the `#791` findings doc is already cited two lines away; the change added little. |
| ⚪5 | ⚪ | doc-wide (pattern) | A few rules cite `(#N)` precedent as their *only* stated basis ("bit twice/thrice"); keeping the one-line mechanism next to the precedent makes the rule survive without opening the issue. | **DROPPED by owner** — consistency note only; most sections already do this. No edit. |

No 🔴 findings. The doc's load-bearing rules are backed by named precedent; the two 🟠s were
staleness/over-breadth in *rationale* clauses only.

## 3. Dedup log — every merged / moved rule named

Consolidation style (owner, grilling): **state-once + specialize** — the shared principle stays in
one canonical home; each other site keeps only its context-specific delta + its own precedents,
replacing the re-explanation with a cross-ref. Nothing lost.

### 3.1 "able-to-fail / revert-check" — one principle, specialized three ways

The principle appeared in three sections applied to different test kinds. Canonical home:
**Fixing bugs → "The test must be able to fail"** (unit-test mechanism, restore-by-inverse-Edit
footgun, #791) — **unchanged**.

- **Testing** ("AI / behavioral integration tests …"): dropped the parenthetical
  "(mutate the feature off, confirm the test goes red)" that restated the Fixing-bugs mechanism;
  kept the integration-specific instruction (drive `run_battle`, not `decide()`) and precedents
  **#413 / #409**. Now leads with the cross-ref.
- **Process lessons** ("An identity refactor needs …"): dropped "and that evidence must be shown to
  *fail* when behaviour does" (mechanism restated); kept the render-hash-for-thin-goldens
  specialization and precedents **#420 / #433 / #450**. Now leads with the cross-ref.

No precedent or context-specific instruction was removed — only two sentences that duplicated the
canonical mechanism.

### 3.2 "Surfacing run/sim commands" — three shell blocks → recipe + one expansion

The "Full paths …" bullet spelled out the `REPO=/PY=/WT=` block three times (full merged block,
full unmerged section, a third "raw block below is what that expands to"). Replaced with:
`make run-cmd WHAT=<N>` as the recipe (already the "mistake-proof default"), then **one** compressed
"what it expands to" block folding merged/unmerged into the `cd` line. Preserved: the
"interpreter is always the main-repo venv; cwd selects the code" fact, the `WT=`-footgun rationale
(#763), and the untouched "Pick the command that shows the change" and "no `main.py`" bullets.

### 3.3 Considered, not done

- "A question/suggestion is not authorization" (*Filing work*) and "reconcile-before-filing / merged
  ≠ your tree" (*Filing work* / *Closing work*) initially looked like dedup targets but are **already
  single-homed with cross-refs** — no change needed.

## 4. Not touched

- Any inbound doc that links into `RULES.md` (per #1285 scope + the owner's standing rule that
  deleting/editing one doc does not license editing others).
- Section ordering; precedent `(#N)` citations; any rule's force or applicability.

## 5. Verification

- Full suite green after edits (docs-only change; a test could assert `RULES.md` content/links).
- Owner reviewed the diff before close.

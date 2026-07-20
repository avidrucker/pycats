# TIL 2026-07-19 — BANANA

**Context:** A single ticket — #759, syncing pycats' `worktreeBranchPattern` +
`RULES.md` to the pmtools #128 "standard" branch/worktree shape — but the session's
real lessons came from everything *around* the fix: reviewing the ticket before
claiming it, hitting a pre-existing red on `main` (`test_ledger_config.py`) that
belonged to a different ticket (#757, fixed as #762), root-causing it with `git
blame`/`git log`, and twice being reminded to check ticket *state* before asserting
it (pmtools#135).

---

## 1. Prove a ticket's acceptance at review time, before you claim it

**What happened:** Reviewing #759 (an `issue-review-skill` pass), the ticket shipped a
concrete replacement regex for `worktreeBranchPattern` and an acceptance criterion:
"parses `br-apple/pycats-757` → `(apple, 757)` **and** `br-apple/pycats-py-issue-754`
→ `(apple, 754)`". Rather than eyeball the pattern, I pasted it into a throwaway
`python3` snippet (converting JS named-groups `(?<name>` → `(?P<name>` for `re`) and
ran it against the acceptance inputs — plus my own future claim branch. All four
parsed correctly. Only then did I recommend READY.

**What I learned:** A regex (or any acceptance predicate) that *looks* right is a
guess until it's run. Executing the ticket's own acceptance during review turns
"probably" into "verified," and it costs 30 seconds. It also front-loads the work:
by claim time I already knew the deliverable was achievable and correct.

**The rule:** **When a ticket ships a machine-checkable acceptance, run it during
review — don't approve a predicate you haven't executed.**

---

## 2. Run the suite right after claiming — and a pre-existing red is not yours to fix silently

**What happened:** Immediately after `pmtools claim 759`, I ran the full suite (from the
main repo's `.venv`, since worktrees have no venv). One failure:
`test_ledger_config.py::test_config_has_required_keys` — `missing keys: {'evidenceDir'}`.
I re-ran it on `main` itself: also red. So it was pre-existing, not caused by #759. The
"right" fix was ambiguous — either the config data was wrong or the test was stale — and
it sat in the `verify-claims` schema domain, not mine. I did **not** patch it. I surfaced
it to the human with a grounded diagnosis and options. It was resolved cleanly as its own
ticket, **#762**.

**What I learned:** The fleet merge-race rule ("run the suite right after claiming") is
what caught this before I could misattribute it to my own change. And the discipline
doesn't stop at *detecting* the red — it extends to *not owning* it. Silently fixing an
adjacent, ambiguous failure would have (a) bundled unrelated work into #759 and (b) made
a schema decision that wasn't mine to make.

**The rule:** **Run the full suite the moment you claim; if it's red on `main` too, it's a
pre-existing defect — surface it as its own ticket, don't fold an ambiguous fix into
yours.**

---

## 3. `git blame`/`git log` the red, and read the close record — a self-certified "green" can be mechanically impossible

**What happened:** Asked to trace how the ledger test went red, I walked the history.
`git log` showed two commits: `04b22f4` (#739) added `.claude/ledger.json` *with*
`evidenceDir` **and** the test asserting it — born green. `1cc6ddb` (#757) then migrated
the config to drop the now-defunct `evidenceDir` (correct — the `verify-claims` ADR-0001
retires it) but touched **only** `.claude/ledger.json`, leaving the guarding test still
demanding the key. `git blame` confirmed the `REQUIRED_KEYS` line hadn't moved since
birth. An incomplete migration. Then the sharp part: the #757 close comment self-certified
*"Suite green (1367 passed, 1 xfailed)"* — mechanically impossible for the committed
state, since dropping the key **forces** that assertion red. It merged red because pycats'
`pmtools close` verify gate is **ruff-only on `pycats/`** and never runs pytest; the
migration touched only `.claude/`, so ruff passed.

**What I learned:** The close gate and "the suite passes" are different claims. The gate
proves formatting/lint on a scoped path; it does not prove the suite is green. A close
comment that says "Suite green" is only as true as whether pytest actually ran against the
*final* commit — and here it didn't (or a subset that skipped the test did).

**The rule:** **A migration that changes data must update the test that guards its shape in
the same commit; and "Suite green" in a close comment is worth nothing unless pytest ran
against the committed state — the ruff-only close gate won't catch a red suite.**

---

## 4. Re-check a ticket's open/closed state before asserting it — memory and issue bodies both lie

**What happened:** Twice I stated ticket state from something other than a live lookup. In
my #759 close summary I wrote that the companion `avidrucker/pmtools#135` was "still open"
— sourced from the #759 body's out-of-scope note, not a fresh check. When the human asked
me to verify, `gh issue view 135` returned **CLOSED (COMPLETED)**. The resolver fix had
already landed. This is a repeat of my known failure mode: asserting ticket state from
memory or from a proxy (a ticket body) instead of the source of truth.

**What I learned:** A ticket body records what was true *when it was written*. Its
out-of-scope and "blocked by" notes rot the moment the referenced ticket moves. The only
authority for open/closed is `gh issue view <N>` at the moment you speak.

**The rule:** **Never state a ticket's open/closed status from memory or from another
ticket's body — run `gh issue view <N>` first.** (Reinforces the existing "verify ticket
state before blocker claims" and "verify ticket numbers before stating them" rules.)

---

## 5. When a stated fact contradicts the tree, check and report the discrepancy — don't build on it

**What happened:** Mid-session the human said "759 is closed." I hadn't run `pmtools
close` and nothing else had. Instead of proceeding on that premise, I ran `gh issue view
759` (OPEN) and `git log origin/main` (my commit unmerged, pattern still legacy) and
reported plainly: not closed, here's the evidence, nothing has changed. The premise was
simply wrong, and acting on it would have skipped the actual close.

**What I learned:** A confidently stated fact from the human is still a claim to verify
when it's cheaply checkable and it drives what I do next. Reporting the contradiction
faithfully — with the two commands that show it — is more useful than either silently
agreeing or silently disagreeing.

**The rule:** **When a stated fact contradicts the repository state, verify it and report
the discrepancy with evidence — never build the next step on an unchecked premise.**

---

## What landed

| Artifact | Change |
|---|---|
| `.claude/orchestrate.json` | `worktreeBranchPattern` → pmtools #128 standard/old-canonical/legacy-tolerant form (#759) |
| `RULES.md` | Claiming/Closing worktree examples → #128 shape + branch-column-vs-`wt-`-dir distinction (#759) |

## Open threads

- The `pmtools close` verify gate is ruff-only and won't catch a red pytest suite (see
  lesson 3). I flagged this as an open question during the session; it turns out APPLE
  reached the same conclusion independently on #762 and the rule is now codified as
  **#764** ("a green close is not a green suite") — so this thread is already closed
  upstream, not by me.

## Related artifacts

- Issue #759 (the ticket), #757 → #762 (the ledger red and its fix), `avidrucker/pmtools#135` (companion resolver fix, closed)
- [Sibling TIL, same day](./today-i-learned-2026-07-19-grape.md)

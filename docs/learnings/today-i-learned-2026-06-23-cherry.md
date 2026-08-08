# TIL 2026-06-23 — CHERRY

**Context:** A small docs-hygiene session. The user asked what to do about a tracked
planning doc, `docs/superpowers/plans/2026-06-22-pm-skills-master-index.md`. I
investigated, found it stale, removed it (#nonum — ad-hoc cleanup, commit `f647db6`),
and integrated it to `main`. The lessons here are about *agent working discipline* —
trusting live state over a snapshot, inspecting before deleting, and not confusing a
local commit with finished work — more than about pycats internals.

---

## 1. The session-start git snapshot is a photo, not a live feed

**What happened:** The harness handed me a start-of-session git status showing the file
as **untracked** (`?? docs/superpowers/plans/2026-06-22-pm-skills-master-index.md`). If
I'd acted on that, my whole framing ("should we commit this new file?") would have been
wrong. Running `git log`, `git ls-files`, and `git status --short` live showed the
opposite: the file was **already committed** (in `afa59e2`, ref #25) and the tree was
**clean** — nothing to commit at all.

**What I learned:** The snapshot in the prompt is explicitly a point-in-time capture
that "will not update during the conversation." Between when it was taken and when I act,
the world can already be different. The user's question even inherited the snapshot's
framing ("commit/save?"), so trusting it would have produced a confidently wrong answer.

**The rule:** **Re-derive git state live before acting on it — the session-start status block is stale by definition, never the source of truth.**

---

## 2. Inspect the target before deleting; let its contents — not its label — decide

**What happened:** The file *called itself* a "Master Plan Index" for active work. But
reading it, every goal it described had already shipped (pycats is on GitHub issues,
`pmtools` exists, `.claude/orchestrate.json` drives fleet mode), and the three child
plans it linked to (`plan-a/b/c`) **were not in the repo** — dead links. So the doc was
a finished plan's index whose contents contradicted its own "active plan" framing.

**What I learned:** "Should we toss this?" is answerable only by opening it and checking
its claims against reality, not by trusting its title or the user's description. The doc
*looked* load-bearing and was actually inert. Confirming the child plans were gone and
the goals were live is what turned a guess into a defensible recommendation.

**The rule:** **Before deleting a doc, read it and verify its claims against the current repo; recommend removal only once its contents prove it's stale.**

---

## 3. "Committed" is not "closed out" — name the integration state

**What happened:** After I removed the file on a branch, the user asked: *"are you stuck,
did you finish and fully close out?"* An honest audit said no: the commit existed only on
`chore/remove-stale-pm-skills-index`, **not merged** to `main` (`git log main..HEAD`
showed it pending) and **not pushed** (no remote-tracking branch). The work *felt* done
because a commit existed, but nothing was integrated. Only after an explicit
`git merge --ff-only` + `git push` was it actually closed out.

**What I learned:** A green commit is the most seductive false finish — the diff is
right, so the brain files it as "done." Integration (merge + push) is a separate,
reportable step. When asked "is it closed out," the answer must enumerate merge state,
push state, and tracking-ticket state, not just "I committed it."

**The rule:** **Report completion as a checklist — committed / merged / pushed / ticket-closed — never collapse "I committed it" into "it's done."**

---

## 4. A committed markdown planning doc fights the issues-as-source-of-truth rule

**What happened:** Part of why removal was the right call: RULES.md says work tracking is
**GitHub issues, not markdown TODO files.** A committed planning index is exactly the
artifact that rule moved away from — and its design rationale already lived elsewhere, in
the still-tracked spec (`specs/2026-06-22-config-driven-pm-skills-design.md`). So removal
lost nothing recoverable (history keeps it at `afa59e2`) and realigned the tree with the
project's own convention.

**What I learned:** When deciding keep-vs-toss for a doc, the project's tracking
philosophy is a tiebreaker. Specs (durable "why") earn their place in the tree; plan
*indexes* (transient "what next") are the kind of thing issues are supposed to hold.

**The rule:** **Keep durable specs in-tree; let transient plan indexes live in issues and git history — consistent with RULES.md's issues-as-source-of-truth.** *(Reinforces existing RULES.md, no new rule minted.)*

---

## Open threads

- **Stale claim ref `refs/claims/issue-25`** resurfaced during this `pmtools claim`
  (issue #25 is CLOSED). BANANA flagged the same one earlier today and it's still
  unswept — one-liner fix: `git push origin :refs/claims/issue-25`.

## Related artifacts

- Removal commit `f647db6`; original add `afa59e2` (#25)
- [Sibling TIL — BANANA](./today-i-learned-2026-06-23-banana.md)
- Issue #27

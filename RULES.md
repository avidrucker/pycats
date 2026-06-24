# pycats — project conventions

## Work tracking

- **Single source of truth: GitHub issues.** Actionable work lives in the issue
  tracker (`gh issue list`), not in markdown TODO files. (`TODOS.md` was retired
  into issues on 2026-06-22; the original list is preserved in git history.)
- pycats runs the **fleet** orchestration workflow (`.claude/orchestrate.json`,
  `mode: "fleet"`). Triage + assignment via the `/fruit-agent-orchestrate` skill;
  agents claim work with `pmtools claim <issue> --as <fruit>` and close it with
  `pmtools close <issue>` (see [Closing work](#closing-work)).

## Labels & priority

- **`severity:*` is for DEFECTS ONLY** (bugs). It describes the *impact of a
  defect*: `high` = data corruption / broken output / blocking; `medium` = real,
  visible defect; `low` = cosmetic or latent.
- **Features / enhancements do NOT get a `severity:*` label.** They carry
  `enhancement` and rank *below* triaged bugs in the work queue — this is
  intentional: fix what's broken before adding more. To pull a specific feature
  forward, **assign it directly** — the ranked queue is advisory and the human
  orchestrator overrides it.
- **`blocked`** encodes real dependencies (e.g. a feature gated on a
  prerequisite). Prefer it over faking severity to express ordering.
- The label taxonomy is a **shared cross-project convention** created by
  `scripts/create-standard-labels.sh`. Don't invent project-local severity
  meanings — keep labels identical across repos.

## Filing work

- Shape every ticket as a complaint: **have X / should have Y / repro**
  (yegor-bdd).
- **Repro/spec-first for unclear bugs.** If a bug's symptom isn't crisp enough to
  write have/should/repro, file a **`research`** ticket to validate / spec /
  reproduce it first, then create the DEV bug ticket once the repro is known.
  Never file a half-specified DEV ticket.
- **Lazy decomposition for research epics.** A multi-thread investigation gets
  ONE umbrella `research` tracker issue listing the threads; file each child
  thread **one at a time**, finishing it before filing the next sibling. This
  avoids premature decomposition (yegor: only decompose when about to start work).

## Closing work

The fleet closes via **`pmtools close`**, which owns the racy push to `main` and
the gated worktree teardown. Follow this order — do **not** improvise:

1. **Work in your claimed worktree.** `pmtools claim <N> --as <fruit>` created it
   under `.claude/worktrees/<fruit>-issue-N` on branch `<fruit>/issue-N`.
2. **Commit on the feature branch, with `Closes #N` in the commit _body_.** The
   subject may keep the repo's `type(scope): summary (#N)` style, but the body
   MUST carry the `Closes #N` keyword: it is both the GitHub auto-close trigger
   *and* exactly what `pmtools close` scans for (and recovers on). `git log
   --oneline` only shows the subject — put the keyword in the body, not the title.
3. **Land + tear down with `pmtools close <N>`, run from inside the worktree.** It
   loops fetch → rebase `origin/main` → push `HEAD:main` until it lands, then —
   and only after confirming the commit reached `origin/main` — deletes the claim
   ref, closes the issue, and removes the worktree + branch.

**Never `git push` to `main` directly, and never manually `git merge` your feature
branch into `main`.** `pmtools close` exists to make the close atomic and
race-safe: a hand-typed push-then-teardown can tear down a worktree *after* a
race-rejected push, destroying work that is still only local (the lccjs "#200
incident"). Hand-closing also leaves a dangling `refs/claims/issue-N` that
`pmtools close` would otherwise sweep.

**pycats specifics (differences from lccjs):**

- **Velocity is off** (`storage.velocity.enabled = false`) — no velocity CSV row
  rides in the close commit.
- **No code markers** — pycats does not use `@todo`/`@inprogress #N` markers, so
  there is nothing to delete in the close commit; just include `Closes #N`.
- **Fallback only if `pmtools` is unavailable:** `gh issue close <N>` plus a
  closing comment. Prefer the tool whenever it is installed.

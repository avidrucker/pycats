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

### Area labels (`area:*`)

- **Every ticket gets exactly one `area:*` label at filing time.** Unlike the
  shared `severity:*` taxonomy, areas are **project-local** — they name *this*
  codebase's subsystems. The current set:
  - `area:display` — rendering, fullscreen, zoom, resolution, display preferences
  - `area:combat` — knockback, hitstun, hitboxes, dodges, attacks, off-stage mechanics
  - `area:entities` — Fighter/Player state machine (dizzy, prone, ledge-hang, decomposition)
  - `area:screens` — screen system/manager, start/win-loss screens, menus, skins, input feedback
  - `area:watch` — `--watch` / `--vs` spectator battles
  - `area:tracker` — ticket discipline, TODO reconciliation, rules/process docs
- **One area per issue.** If a ticket spans two areas, pick the dominant one — the
  orchestrator uses the *first-listed* `area:*` when several are present. Split the
  ticket if it genuinely needs two lanes.
- **Why it matters:** `/fruit-agent-orchestrate` partitions the backlog into
  per-agent lanes by `area:*`, assigning at most one cluster per agent, so a ticket
  with no area label falls into the wildcard pool and weakens the same-file
  collision guard. Reproducible label *creation* (vs today's hand-created repo
  labels) is tracked in `avidrucker/pmtools#69`.

## Filing work

- **A question or suggestion is not authorization to create work.** "Have you done
  X?", "did you Y?", "is Z done?", or "this would be good" asks for an *answer* or
  surfaces an *option* — it is not a cue to file an issue, claim a worktree, or
  start coding. Answer the question (or present the option) and **stop**;
  file/claim/execute only after an explicit go-ahead ("yes, do it", "take that
  ticket", "go ahead"). Filing-and-claiming is outward-facing and costly to
  unwind — when unsure whether you've been authorized, ask. (Front-end mirror of
  "surface the contradiction before an outward-facing close" under *Fixing bugs*.)
- Shape every ticket as a complaint: **have X / should have Y / repro**
  (yegor-bdd).
- **Repro/spec-first for unclear bugs.** If a bug's symptom isn't crisp enough to
  write have/should/repro, file a **`research`** ticket to validate / spec /
  reproduce it first, then create the DEV bug ticket once the repro is known.
  Never file a half-specified DEV ticket.
- **Reconcile a worktree-found failure against current `origin/main` before filing
  it.** `pmtools claim` guarantees a fresh base *at claim time* (it fetches and
  hard-blocks a claim when local `main` is behind `origin/main`), but sibling agents
  keep merging *during* your session, so a long-lived worktree base drifts behind and
  a failure you see may already be fixed upstream. Before filing a regression found
  in a worktree, `git fetch origin main` and check the open-issue list / `git log
  origin/main` — confirm it still reproduces on **current** `origin/main`, not just
  your (possibly stale) base. The claim-time guard cannot cover mid-session drift, and
  `pmtools status` does not surface it today (#171). (Cousin of "merged ≠ what your
  tree has" under *Closing work* and the stale-tracker caution.)
- **Lazy decomposition for research epics.** A multi-thread investigation gets
  ONE umbrella `research` tracker issue listing the threads; file each child
  thread **one at a time**, finishing it before filing the next sibling. This
  avoids premature decomposition (yegor: only decompose when about to start work).

## Fixing bugs

- **Every bugfix lands a regression test in the same commit.** A fix without a
  test is not done — the test is what stops the bug from coming back (and from
  being *re-filed*: #7's original fix `b480ae0` shipped with no test, so the
  behavior looked broken a year later and was re-filed and re-investigated from
  scratch). This is the repo's expression of yegor-bdd (a bug is a failing test).
- **The test must be able to fail.** Before claiming the fix works, confirm the
  new test is **red without the fix and green with it** — revert the fix (or stub
  it), watch the test fail, then restore. A test that has never been red proves
  nothing (it may assert the wrong thing or never reach the branch). See
  `docs/learnings/today-i-learned-2026-06-23-dragonfruit.md` §1 & §4.
- **Already-fixed / non-reproducing bug?** If a reported bug does not reproduce on
  current `main`, the deliverable is still the *missing* regression test (find the
  commit that fixed it, add the can-fail guard), not a no-op close. Surface the
  contradiction to the reporter before an outward-facing close.

## Surfacing run/sim commands

When a change would **benefit from or require a live run or simulation** to verify
— anything observable: the running game loop, rendering/scaling, input, screens or
menus, audio, or sim output — the agent's **final response MUST include the exact
command(s) to run it, with full absolute paths**, so the human can copy-paste and
manually test (the agent can't drive the GUI). **pycats-only** — other repos in the
Study tree do not inherit this rule.

- **When it applies:** the change is runnable/observable. A pure-internal refactor
  with full test coverage and no behaviour change doesn't strictly need it, though a
  run command is still welcome.
- **Full paths, not `python -m pycats.game` alone.** Worktrees have no `.venv`, so
  point the interpreter at the **main repo's** `.venv` and run from the checkout.
  Present it as a `REPO=` / `PY=` variable block (one assignment per line), not an
  opaque one-liner:

      REPO=/abs/path/to/pycats                   # the checkout (main repo or worktree)
      PY=/abs/path/to/pycats/.venv/bin/python    # ALWAYS the main repo's venv
      cd "$REPO" && "$PY" -m pycats.game

- **Pick the command that shows the change:** the live game (`-m pycats.game`), a
  replay/match (`watch.py`, `watch.py --match`), or a recorded video
  (`watch.py --match --video media/clip.mp4`). The README "How to Run" section and
  the `watch.py` commands are the canonical sources — cite the one that exercises
  the change, with absolute paths filled in.
- **There is no `main.py` or top-level launcher — never invent `python main.py`.**
  The only entry points, all run from the repo root, are `-m pycats.game` (live
  game), `watch.py` (replay/match), and `bench.py` (benchmark). `python main.py`
  fails with `No such file or directory`. If unsure, the README "How to Run"
  section is authoritative — read it rather than guessing a conventional path.

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

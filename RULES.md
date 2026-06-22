# pycats — project conventions

## Work tracking

- **Single source of truth: GitHub issues.** Actionable work lives in the issue
  tracker (`gh issue list`), not in markdown TODO files. (`TODOS.md` was retired
  into issues on 2026-06-22; the original list is preserved in git history.)
- pycats runs the **fleet** orchestration workflow (`.claude/orchestrate.json`,
  `mode: "fleet"`). Triage + assignment via the `/fruit-agent-orchestrate` skill;
  agents claim work with `pmtools`
  (`python3 ~/code/pmtools/py/claim.py <issue> --as <fruit>`).

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

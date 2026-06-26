# pycats — agent guide

Full conventions: **[RULES.md](./RULES.md)** — read it before filing or labeling work.

Critical rules:

- **Work tracking is GitHub issues** (single source of truth), not markdown TODO files.
- **`severity:*` labels are for DEFECTS (bugs) only.** Features = `enhancement`
  with no severity; use `blocked` for dependencies. Don't fake severity to express
  feature priority — assign features directly instead.
- **A question/suggestion is not authorization to create work** — answer first;
  file/claim/code only on an explicit go-ahead. See [RULES.md](./RULES.md) → "Filing work".
- **Repro/spec-first:** if a bug's symptom isn't crisp, file a `research` ticket to
  reproduce/spec it before a DEV ticket.
- **Every bugfix lands a regression test in the same commit**, and that test must
  be **able to fail** (red without the fix, green with it — revert-the-fix check).
  See [RULES.md](./RULES.md) → "Fixing bugs".
- **Research epics:** one umbrella `research` tracker; file child threads one at a
  time, finishing each before filing the next.
- pycats runs **fleet** mode (`.claude/orchestrate.json`); claim work via
  `pmtools claim <issue> --as <fruit>`.
- **Closing work:** commit with **`Closes #N` in the body**, then close via
  **`pmtools close <N>`** from the worktree. Never `git push` to `main` or
  `git merge` your branch into `main` by hand — the tool owns the race-safe push
  + teardown. See [RULES.md](./RULES.md) → "Closing work".

Run & test: see [README.md](./README.md).

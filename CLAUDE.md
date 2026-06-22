# pycats — agent guide

Full conventions: **[RULES.md](./RULES.md)** — read it before filing or labeling work.

Critical rules:

- **Work tracking is GitHub issues** (single source of truth), not markdown TODO files.
- **`severity:*` labels are for DEFECTS (bugs) only.** Features = `enhancement`
  with no severity; use `blocked` for dependencies. Don't fake severity to express
  feature priority — assign features directly instead.
- **Repro/spec-first:** if a bug's symptom isn't crisp, file a `research` ticket to
  reproduce/spec it before a DEV ticket.
- **Research epics:** one umbrella `research` tracker; file child threads one at a
  time, finishing each before filing the next.
- pycats runs **fleet** mode (`.claude/orchestrate.json`); claim work via `pmtools`
  (`python3 ~/code/pmtools/py/claim.py <issue> --as <fruit>`).

Run & test: see [README.md](./README.md).

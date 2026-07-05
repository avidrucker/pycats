# pycats — agent guide

Full conventions: **[RULES.md](./RULES.md)** — read it before filing or labeling work.

Critical rules:

- **Work tracking is GitHub issues** (single source of truth), not markdown TODO files.
- **`severity:*` labels are for DEFECTS (bugs) only.** Features = `enhancement`
  with no severity; use `blocked` for dependencies. Don't fake severity to express
  feature priority — assign features directly instead.
- **A question/suggestion is not authorization to create work** — answer first;
  file/claim/code only on an explicit go-ahead. See [RULES.md](./RULES.md) → "Filing work".
- **No unprompted research** — when asked for a narrow action (file/log/label/claim/edit),
  do exactly that; ask before any unrequested grep/read/issue-list. Resolving the action's
  minimal required input (incl. reading the file you're about to edit) is fine. See
  [RULES.md](./RULES.md) → "Filing work".
- **Installing a new dependency needs explicit human approval** — `pip install` (even
  into a dev `.venv`), manifests/lockfiles, `npm`, system packages. Using a declared
  dep is fine; *adding* one (incl. a "harmless" dev tool) is gated — propose, don't
  install. See [RULES.md](./RULES.md) → "Dependencies".
- **Repro/spec-first:** if a bug's symptom isn't specific, file a `research` ticket to
  reproduce/spec it before a DEV ticket.
- **Every bugfix lands a regression test in the same commit**, and that test must
  be **able to fail** (red without the fix, green with it — revert-the-fix check).
  See [RULES.md](./RULES.md) → "Fixing bugs".
- **Changing a game value needs a basis** — a tuning/balance/config number changes only
  with a **research/data citation** or a **game-designer decision** (design doc / ratified
  `decision:` ticket); bare game-feel is declined `wont-do`/`vapid`. Record it as
  `FOUND`/`TUNED`, not as sourced-when-guessed. See [RULES.md](./RULES.md) → "Changing values".
- **Research epics:** one umbrella `research` tracker; file child threads one at a
  time, finishing each before filing the next.
- pycats runs **fleet** mode (`.claude/orchestrate.json`); claim work via
  `pmtools claim <issue> --as <fruit>`.
- **Closing work:** commit with **`Closes #N` in the body**, then close from the
  **main checkout** with **`cd <main> && pmtools close <N>`** (pmtools#104: `close`
  resolves the worktree by issue #, so it runs from main and your shell is never
  stranded). Never `git push` to `main` or `git merge` your branch into `main` by
  hand — the tool owns the race-safe push + teardown. From main, `close` exits **0**
  and you comment in place; running it from *inside* the worktree still works but
  exits 1 (deleted cwd) and strands your shell. No-code (decision/research) tickets
  close via `gh issue close` + **`pmtools release`**. Before posting the closing
  comment, **run the pre-close error self-audit** (re-read the session, log any
  missed rows via `pmtools error log`) and state `error self-audit: N row(s) logged
  (#…)` or `error self-audit: no loggable errors this session` in the comment — see
  the **log-error** skill. See [RULES.md](./RULES.md) → "Closing work". And **run the
  suite right after claiming** (fleet merge race) — see "Claiming work".
- **Surface the run/sim command for runnable changes.** Any change to the live
  game / render / input / screens / sim must end the final response with the exact
  full-path run command — a `REPO=`/`PY=` block pointing at the main repo's venv,
  ending in `"$PY" -m pycats.game`. **There is no `main.py`** (entry points are
  `-m pycats.game`, `watch.py`, `bench.py`); never emit `python main.py`.
  See [RULES.md](./RULES.md) → "Surfacing run/sim commands".
- **Banned words in ALL output** (replies, tickets, commits, docs): avoid **crisp**
  and **honest / honestly / honesty** — they read as vague filler / throat-clearing.
  Name the concrete quality instead (crisp → specific / precise / clean; honest →
  plain / direct / candid / faithful). Proofread the closing line, where they slip in.
  Full list + replacements: [docs/banned_words.md](./docs/banned_words.md).

Run & test: see [README.md](./README.md).

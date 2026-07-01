# pycats — agent guide

Full conventions: **[RULES.md](./RULES.md)** — read it before filing or labeling work.

Critical rules:

- **Work tracking is GitHub issues** (single source of truth), not markdown TODO files.
- **`severity:*` labels are for DEFECTS (bugs) only.** Features = `enhancement`
  with no severity; use `blocked` for dependencies. Don't fake severity to express
  feature priority — assign features directly instead.
- **A question/suggestion is not authorization to create work** — answer first;
  file/claim/code only on an explicit go-ahead. See [RULES.md](./RULES.md) → "Filing work".
- **Installing a new dependency needs explicit human approval** — `pip install` (even
  into a dev `.venv`), manifests/lockfiles, `npm`, system packages. Using a declared
  dep is fine; *adding* one (incl. a "harmless" dev tool) is gated — propose, don't
  install. See [RULES.md](./RULES.md) → "Dependencies".
- **Repro/spec-first:** if a bug's symptom isn't specific, file a `research` ticket to
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
  + teardown. **Trust the `CLOSE OK` banner — `close` exits 1 after success (cwd
  deleted); post the closing comment from the main checkout.** No-code
  (decision/research) tickets close via `gh issue close` + **`pmtools release`**.
  See [RULES.md](./RULES.md) → "Closing work". And **run the suite right after
  claiming** (fleet merge race) — see "Claiming work".
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

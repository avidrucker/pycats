# Research: stale-carryover audit of the 2026-06-22 TODO→issues migration (#33)

**Question:** the `TODOS.md`→GitHub-issues migration (2026-06-22) imported bug
tickets without re-validating them against current `main`. At least one (#7) was
*already fixed* before it was filed. How many others were stale carryovers, and
does the migration need a systematic re-audit before agents claim its tickets?

**Method (read-only):** for every migrated bug issue (#2–#9), compare the
issue's `createdAt` (all 2026-06-22, the migration point) against the date and
nature of the commit that closed it. A *stale carryover* is a bug whose fixing
commit predates the issue itself (the symptom was already gone at filing time);
a *genuine* bug is one fixed by real work after filing.

## Results

All six closed migrated bugs were filed 2026-06-22T21:4x. Verdicts:

| # | Title (abbrev.) | Closed by | Date | Verdict |
|---|---|---|---|---|
| #2 | faces wrong way after ground dodge roll | `8fd127c` fix(dodge) | 2026-06-24 | **genuine** |
| #5 | thick-platform sides not solid | `4c95b65` fix(physics) | 2026-06-23 | **genuine** |
| #6 | spot-dodge when down held before shield | `e10d1d8` fix(input) | 2026-06-23 | **genuine** |
| #7 | respawn keeps prior facing | `052b055` **test-only**; real fix `b480ae0` | 2025-07-07 | **STALE CARRYOVER** |
| #8 | knockback zeroed when defender moving | `d613d91` fix(combat) | 2026-06-23 | **genuine** |
| #9 | new round leaves rects damaged | `d3a1fd9` fix(respawn) | 2026-06-24 | **genuine** |

Still OPEN: **#3, #4** (tail physics) — in-flight with CHERRY at audit time.
Both describe currently-missing tail behavior (gravity/collision, clean
turn-snap), i.e. genuine open work, not already-fixed; not independently
re-reproduced here to avoid duplicating active investigation.

## Finding

The migration was **high quality**: exactly **1 of 6** closed migrated bugs
(#7) was a stale already-fixed carryover, and it was caught during normal work
(see `docs/learnings/today-i-learned-2026-06-23-dragonfruit.md` §1). No
additional stale carryovers were found; no other wasted fix-effort is evident.

#7 slipped through for a specific, fixable reason: its original fix (`b480ae0`,
Jul 2025) shipped **with no regression test**, so a year later the behavior
*looked* broken and was re-filed. The mitigation is already captured as #35
(require a can-fail regression test with every bugfix) — landing that closes the
exact gap that produced the only carryover.

## Recommendation

- **No systematic re-audit of the migration is warranted** — the 1/6 carryover
  rate is low and the single instance is already resolved.
- **Land #35** (regression-test-with-every-bugfix) as the durable fix for the
  root cause; it is higher-leverage than re-checking already-resolved tickets.
- **Lightweight habit for any future migration:** reproduce a migrated bug
  against `main` before claiming it as DEV work (the #7 pattern). One cheap
  reproduction attempt at claim time is enough; a standing audit is overkill.
- No new fix tickets filed — every genuinely-broken migrated bug already has a
  closed ticket, and the open tail bugs (#3/#4) are actively owned.

Related: #7 (the carryover), #35 (root-cause mitigation), #34 (reset-path
consolidation surfaced by #9/#31).

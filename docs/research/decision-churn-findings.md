# Decision / value churn — cost per settled value (findings)

**Ticket:** #632 (Child A of umbrella #631). **Role:** RESEARCH. **Scope:** measure only —
no guardrails proposed here (that is Child B, gated by #631). Read-only mining of git
history, GitHub issues, and the pmtools SQLite store as of **2026-07-06**.

## TL;DR

- Of **60** tuning constants in the provenance registry, **8** ever had their *value*
  revised in `config.py`. The other 52 were set once and never changed.
- **Config-value churn and decision/effort churn are different metrics and rank
  differently.** The most value-revised constant (`DODGE_SPEED`, 3 values) cost almost
  nothing to settle (ad-hoc 2025 commits, no tickets). The costliest value to settle
  (`SMASH_CHARGE_*`) changed in config **once**, but consumed **5 tickets, 11 issue
  comments, and 2 logged errors** — because it was first registered *wrong-but-labelled-
  sourced*, then had to be re-researched and corrected.
- **Two eras.** 2025 churn was process-less: bare commits ("fix adjust physics
  constants") flipping values with no ticket, no citation. 2026 churn is ticket-tracked
  and citation-driven — which makes it *visible and auditable*, but also *more expensive
  per value* because each change carries research + registration + correction + test tickets.
- So the answer to "how many issues/tokens to settle one value?" is **bimodal**: near-zero
  for pre-discipline game-feel flips, and **up to ~5 tickets** for a post-discipline
  sourced value that was booked wrong the first time.

## Method (reproducible)

Two churn *types*, measured differently (they don't share a handle):

- **Value churn** (config numbers) — has a code handle. For each of the 60 constants in
  `pycats/combat/provenance.py::TUNING_CONSTANT_NAMES`:
  ```
  git log --reverse -G"^<NAME> = " -p -- pycats/config.py
  ```
  then read the constant's value at each touching commit via `git show <sha>:pycats/config.py`
  and **compress consecutive-equal values**. A constant is a churn case iff it took ≥2
  distinct values over history.
  - **False-positive filter (important):** a raw `-G` commit count over-reports churn.
    Two whole-file commits touch *every* assignment line without changing any value — the
    ruff reformat (`a0304b5`, "adopt ruff format — one-time whole-tree reformat", #505) and
    the Axis-A annotation pass (`6793673`, config ⚠🔬 upgrades, #408). A naive count of
    assignment-touching commits flagged **27** constants as ≥2-touch "churned"; value-
    compression reduced the true set to **8**.
- **Decision churn** (a ruling reversed) — no code handle; evidence is the issue/comment
  thread and the registry's own `supersedes` language. Detected via `supersede|corrected|
  Brawl-era|base-game` in `provenance.py` (only the smash-charge rows carry it) and the
  ticket cross-references.

**Effort proxy.** The `velocity` table in `~/.pmtools/pycats/pmtools.db` is **empty**
(velocity logging is disabled in pycats — 0 rows), so `actual_min`/token minutes are
**unrecoverable**. Substituted with what exists: **`errors`-table rows keyed to each case's
tickets** (`SELECT … FROM errors WHERE ticket IN (…)`, 92 rows total) plus **issue count**
and **issue-comment count**. Raw prompt/token counts are recorded nowhere — flagged
unrecoverable, not invented.

## Per-case table

Ranking key: **# distinct values, ties broken by # tickets.** "type": V = config value,
D = decision/effort overlay on the same value.

| rank | case | type | # values | revisions | tickets | commits (value-change) | span | effort proxy |
|---|---|---|---|---|---|---|---|---|
| 1 | `DODGE_SPEED` | V | 3 (28→22→14) | 2 | 0 | 2 | 10 d (2025-06-27→07-07) | none — ad-hoc, no ticket/errors |
| 1 | `GROUND_FRICTION` | V | 3 (0.2→0.9→0.5) | 2 | 0 | 2 | 1 d (2025-06-26→06-27) | none; one rev was a *bugfix* ("friction applied twice") not indecision |
| 3 | `SMASH_CHARGE_FRAMES` | V+D | 2 (60→59) | 1 | **5** | 1 | 5 d config / 4 d decision arc | **11 comments, 2 errors** — see worst-offender |
| 3 | `SMASH_CHARGE_SCALE` | V+D | 2 (1.4→1.3671) | 1 | **5** | 1 | 5 d config / 4 d decision arc | shares the #426/#581/#595/#599/#627 arc |
| 5 | `MAX_FALL_SPEED` | V | 2 (12→13) | 1 | 0 | 1 | 1 d (2025) | none — ad-hoc |
| 5 | `MOVE_SPEED` | V | 2 (5→6) | 1 | 0 | 1 | 1 d (2025) | none — ad-hoc |
| 5 | `AIR_FRICTION` | V | 2 (0.05→0.85) | 1 | 0 | 1 | 1 d (2025) | none — ad-hoc |
| 5 | `DODGE_AIR_SPEED` | V | 2 (14→17) | 1 | 2 (#184,#222) | 2 | 0 d (same day) | 2 tickets, 0 errors — fast, tracked |

Measured vs estimated vs unrecoverable:
- **Measured** (from git/gh/DB): # values, revisions, commits, tickets, comments, errors, spans.
- **Estimated:** none — all figures above are direct counts.
- **Unrecoverable:** prompt/token counts, wall-clock minutes (velocity disabled); the *human*
  deliberation time behind each change.

## Worst offender — the smash-charge saga (most effort to settle one value)

By config-value revisions `SMASH_CHARGE_*` is mid-pack (one change), but by **tickets-to-
settle** it is the clear worst: **one value, five tickets, ~4-day arc, all 2026-07-02→07-06.**

| date | ticket | what happened |
|---|---|---|
| 2026-06-30 | (feat `c95ca7f`/`c64a877`) | smash charge lands: `FRAMES=60`, `SCALE=1.4` (base-game/Brawl numbers) |
| 2026-07-02 | #426 (research, closed) | confirmed PM/Melee smash *formula* + how charge scales it |
| 2026-07-05 | #581 (DEV, closed) | **registered `60` / `1.4` into the provenance registry as `FOUND`** — i.e. booked the base-game/Brawl values as if sourced |
| 2026-07-06 | #595 (research, closed) | holdability research; surfaced that the registered values were the *wrong game's* |
| 2026-07-06 | #599 (DEV, closed, 6 comments) | **corrected `60→59`, `1.4→1.3671`** to the PM values (commit `37af6ba`); registry now says "supersedes the base-game 60 #581 registered" / "supersedes #581 Brawl-era 1.4"; logged error #82 (repo-wide ruff format) |
| 2026-07-06 | #627 (test, closed) | hardened the now-tautological charge-bar assertion the value change exposed; logged error #86 (stale-pyc, 6 false failures) |

**Root pattern:** the value was **committed as `FOUND`/sourced while actually wrong**
(#581 booked Brawl/base-game numbers), so the cost wasn't one decision — it was a
registration, a *reversal*, and the cleanup the reversal triggered (a test that had been
written against the wrong value). This is the churn the umbrella (#631) is chasing:
not the code flipping back and forth, but a *decision* booked prematurely-confident and
then unwound across multiple tickets.

## Key findings

1. **Value-revision count is a poor proxy for churn cost.** The two most value-revised
   constants (`DODGE_SPEED`, `GROUND_FRICTION`) were the *cheapest* to settle; the costliest
   (`SMASH_CHARGE_*`) changed value once. Rank by tickets-to-settle, not by config diffs.
2. **The expensive failure mode is "sourced-when-guessed."** #581 registering `60`/`1.4` as
   `FOUND` is exactly the anti-pattern RULES.md → "Changing values" warns against, and it is
   what turned a one-line correction into a five-ticket arc. (Directly relevant to Child B.)
3. **Discipline moved churn from invisible to expensive-but-auditable.** 2025's churn cost
   ~nothing in process but left no trace (bare "fix adjust physics constants" commits);
   2026's churn is fully traceable but pays a per-value ticket tax. The goal for Child B is
   the middle: traceable *without* the re-litigation tax.
4. **One "churn" was a bugfix, not indecision** (`GROUND_FRICTION` 0.9→0.5, "friction applied
   twice"). Not all value changes are decision churn — distinguish correction-of-a-defect
   from reversal-of-a-decision when counting.

## Gaps / caveats (for Child B, not resolved here)

- **Pure decision reversals with no config value** (e.g. a `decision:` ticket that reversed
  a labelling/scope ruling) are **not fully censused** — only value-backed churn and the
  registry-flagged smash-charge decision were in reliable reach. A broader reversal census
  (mining closed `decision:`/`research` tickets for "supersedes/reverses #N") is a candidate
  Child-B input.
- **Per-character move data** (`characters/*.py`) is outside the registry and was not mined.
- **Token/deliberation cost is unrecoverable** with current instrumentation; if Child B wants
  a real token figure, that is a *new instrumentation* ask, out of scope for this umbrella.

## Refs

Umbrella #631. Motivating case: smash-charge #426 / #581 / #595 / #599 / #627. Provenance
registry #233 / ADR-0003 (`pycats/combat/provenance.py`). Findings-doc rule #618.
Anti-pattern basis: RULES.md → "Changing values" (sourced-when-guessed).

# Plan — Expand ruff beyond `--select F` (slice 5 of #492)

**Status:** planning / discretionary · **Owner epic:** [#505](https://github.com/avidrucker/pycats/issues/505) · **Parent:** [#492](https://github.com/avidrucker/pycats/issues/492) · **Decision of record:** [ADR-0006](../../adr/0006-adopt-ruff-lint-format.md) · **Date:** 2026-07-04

> **This is discretionary.** The mandatory arc of #492 is **done**: ruff is adopted, `ruff check --select F pycats/` is clean, and the `#502` pre-commit hook enforces it. Everything below is *optional polish* — pursue the cheap wins if/when wanted; do not let "it's an epic" pressure the expensive parts.

## Why this is an epic
Slice 5 is not one task — it is a **container** of ~4 independent cleanups + 2 policy decisions + 1 setup step. Only its children are units of work (per the epic discipline). File children **one at a time**, finishing each before filing the next; do not pre-file the whole tree.

## Measured backlog — ruff 0.15.20, `pycats/`, 2026-07-04
| Rule | Count | Fix | Character |
|---|---:|---|---|
| **E501** line-too-long | **390** | manual | **Policy decision, not a chore** (Decision 1) |
| I001 unsorted-imports | 40 | `[*]` auto | tidiness; cheap |
| UP045 `Optional[X]`→`X \| None` | 22 | `[*]` auto | needs py3.10+ |
| UP006 `List[X]`→`list[X]` | 18 | `[*]` auto | needs py3.9+ |
| E402 import-not-at-top | 13 | manual | mostly **deliberate** (config.py etc.) → `# noqa`, don't restructure |
| UP035 deprecated-import | 13 | `[-]` unsafe | review each |
| E722 bare-except | 5 | manual | **real correctness win** |
| E702 semicolons | 3 | manual | trivial |
| UP015 redundant-open-modes | 3 | `[*]` auto | |
| UP037 quoted-annotation | 2 | `[*]` auto | |
| W (pycodestyle warnings) | 0 | — | already clean |

Non-E501 total: **119** (87 auto-fixable). With E501: 509. `ruff format` (black-compatible): **64 of 78 files would reformat** (~82%).

**Reframe:** the big numbers are the *least* work. E501 (390) = one `line-length` setting. `ruff format` (64) = one command. The genuine by-hand work is small: E722 (5) + E402/E702 (~16). The auto-fixable I (40) + most UP (58) are "run `--fix`, run the suite."

## Child sequence (file one at a time; recommended order)
0. **Config home (prerequisite).** Create a ruff config file so rules-with-options (line-length, per-file ignores) have a home. **`ruff.toml`** (lighter, no packaging metadata) vs **`pyproject.toml`** (modern standard, hosts other tooling too). This is the config-home choice **deferred from slice 2** (#499) — it comes due here. *Everything below writes to this file; do it first.*
1. **Decision 1 — E501 line-length.** See Decisions. Land the chosen `line-length` in the config; the 390 mostly evaporate. (Fold into child 0 if desired.)
2. **`I` import-sort (40, auto).** `ruff check --select I --fix pycats/`. ⚠ Re-verify deliberate import order after — esp. `game.py` / `config.py` (post-#490 star-import removal) and any cycle-breaking late imports; run the full suite (an import-order dependency surfaces there). Then add `I` to the #502 hook's `--select`.
3. **`E722` bare-except (5, by hand).** Name the caught exception — worth doing on its own regardless of the rest. Add `E722` to the hook.
4. **`E702` / `E402` (~16, by hand / noqa).** `# noqa: E402` the deliberate late imports (don't restructure); E702 trivial.
5. **`UP` pyupgrade (58).** Auto-fix UP006/UP045/UP015/UP037; **review UP035 (unsafe fix)**. ⚠ Confirm the Python floor first (`X | None` = 3.10+, `list[...]` = 3.9+) before committing to pep604/585. Add `UP` to the hook.
6. **Decision 2 — adopt `ruff format`?** See Decisions.

Each child: drive `ruff check --select <F,…>` to 0 for its rule **and** widen the #502 hook's `--select` so the new rule is enforced, not just cleaned once.

## The two decisions (policy — need a human call; recommend a `decision:` ticket each)
- **Decision 1 — E501 line-length (390).** ruff default is 88; the codebase writes longer. Options: **(a) relax `line-length` to ~100–120** (matches the real style, drops most/all 390) — *recommended*; (b) exclude E501; (c) reflow 390 lines (big churn, low value — avoid). Decide **before** enabling E-rules broadly or E501 floods every run.
- **Decision 2 — adopt `ruff format` (64/78 files).** ADR-0006 left it optional. Adopting = a one-time whole-repo diff (~82% of files): ends style bikeshedding, but churns `git blame` and is a large review. If yes: land as a **single mechanical PR in a quiet fleet window** (merge-conflict risk), verified against the full suite + a golden run. Pairs with Decision 1 (the formatter enforces a line-length).

## Cross-cutting caveats
- **Hook coupling:** every rule enabled must widen `.pre-commit-config.yaml`'s `--select` (#502), else it's cleaned but not enforced.
- **Determinism / goldens:** I / UP / E fixes are behavior-preserving → goldens unaffected. `ruff format` is also behavior-preserving, but verify the big diff against the full suite + `PYCATS_UPDATE_GOLDENS` run.
- **Fleet timing:** the auto-fix passes and especially `ruff format` touch many files — land them when few sibling branches are open, to avoid merge conflicts.
- **Python floor:** UP006/UP045 assume 3.9/3.10 syntax — confirm the supported floor before adopting.

## Recommended first wave (cheap, high value)
Config home (child 0) + Decision 1 (line-length) + `I` (child 2) + `E722` (child 3). That alone buys sorted imports, a sane line-length, and real bare-except fixes for little effort. Leave `UP` sweep and `ruff format` as optional later.

## Status
| Child | Ticket | State |
|---|---|---|
| This plan doc | #509 | in progress |
| 0. ruff config home | — | not filed |
| 1. Decision: E501 line-length | — | not filed |
| 2. `I` import-sort | — | not filed |
| 3. `E722` bare-except | — | not filed |
| 4. `E702`/`E402` | — | not filed |
| 5. `UP` pyupgrade | — | not filed |
| 6. Decision: `ruff format` | — | not filed |

_Update this table as children are filed / closed._

## Refs
Epic #505 · parent #492 · ADR-0006 (#498) · pre-commit hook #502 · ruff declared #499 · config-home deferred from #499. Measured on ruff 0.15.20, 2026-07-04.

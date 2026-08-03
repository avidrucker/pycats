# ADR-0006 — Adopt ruff as the lint tool (supersede pyflakes; reject black)

- **Status:** Accepted
- **Date:** 2026-07-03
- **Supersedes:** [ADR-0005](0005-adopt-pyflakes-quality-gate.md) (adopt pyflakes). The pyflakes *adoption verdict* is reversed in favor of ruff; the enforcement model and the backlog-cleanup work carry over unchanged (see below).
- **Tracked by:** epic [#492](https://github.com/avidrucker/pycats/issues/492) (this ADR is its slice 1). Approval to declare the dependency is [#197](https://github.com/avidrucker/pycats/issues/197) (granted in #492).

## Context

ADR-0005 adopted `pyflakes` as pycats' codebase-quality tool (pre-commit + on-demand, no CI gate), and work began: `game.py`'s star-import was removed so the undefined-name check could see it ([#490](https://github.com/avidrucker/pycats/issues/490)), and 37 dead imports were cleared ([#495](https://github.com/avidrucker/pycats/issues/495)), taking `pyflakes pycats/` from ~52 to ~15 findings.

The [#487 library/framework survey](../research/2026-07-03-library-framework-survey.md) then found that **ruff dominates pyflakes**: ruff's `F` rule category **reimplements pyflakes' entire check set** (F401 unused-import, F811 redefinition, F821 undefined-name), so `ruff check --select F pycats/` produces the *same* findings — as one fast binary, with per-rule config, and (unlike pyflakes) **inline `# noqa` suppression**. ruff also extends to import-sort (`I`), pycodestyle (`E`/`W`), and pyupgrade (`UP`), and ships a black-compatible `ruff format`. The human decision ([#492](https://github.com/avidrucker/pycats/issues/492), 2026-07-03) is to flip the tool choice to ruff and **reject** both pyflakes and black.

Because ruff's `F` rules ≡ pyflakes, **none of the #490/#495 work is wasted** — it is a down payment on the same backlog, now cleaned under ruff instead. Only the *tool decision* changes.

## Decision

1. **Adopt `ruff`** as the lint tool (and, if autoformatting is later wanted, `ruff format`). This ADR is the #197 "yes" for declaring ruff. **Reject `pyflakes`** (subsumed by ruff's `F` rules) and **`black`** (subsumed by `ruff format`).
2. **Initial rule scope: `--select F`** — the pyflakes-equivalent set, so the in-progress cleanup (#495 → ~15 findings left) carries over directly. Expanding to `I`/`E`/`W`/`UP` is deferred to a later slice, per-rule and incremental.
3. **Enforcement: pre-commit + on-demand** — inherited unchanged from ADR-0005 (the human's enforcement choice is tool-independent); **no CI gate** (the repo has none to build on; revisit if CI is introduced). Slice 4 of #492 wires it.
4. **The `core/physics.py:149` `list["Player"]` false positive** (a string forward-ref under `from __future__ import annotations`, flagged as undefined-name) is now handled with an inline **`# noqa: F821` plus a rationale comment** — an option pyflakes did not offer. A `TYPE_CHECKING` import remains an acceptable alternative if cleaner.
5. **`pyflakes` is dropped.** It was never declared (installed ad-hoc in #193), so there is no manifest entry to unwind — only an optional `pip uninstall pyflakes`.

## Execution (epic #492 slices — file/claim one at a time)

1. **This ADR** (slice 1) — record the decision; mark ADR-0005 Superseded.
2. **Declare ruff** + document the run command (`ruff check --select F pycats/`) in the README dev section.
3. **Clean the backlog to 0** — starting from the ~15 findings left after #495 (fix or `# noqa`-with-rationale, incl. the physics.py false positive), so `ruff check --select F` is clean.
4. **Enforcement** — wire pre-commit (and/or a minimal CI gate for pytest + ruff).
5. *(later, optional)* **Expand rules** — `I`/`E`/`W`/`UP`; adopt `ruff format` if formatting is wanted.

## Consequences

- **Positive:** one tool covers the ADR-0005 goal *and* future lint/format/import-sort wants; `# noqa` gives per-line suppression pyflakes lacked (so re-exports and the physics.py false positive no longer force structural workarounds); the #490/#495 work carries over intact.
- **Negative / cost:** a new declared dev dependency (ruff) instead of pyflakes; a larger opinion surface as rules are expanded (mitigated by starting at `--select F` only); the ~15-finding cleanup still to finish (slice 3).
- **Residual:** the enforcement wiring (slice 4) and any rule expansion (slice 5) remain decisions of their own; `ruff format` adoption is explicitly out of scope here.

## Alternatives considered

- **Keep pyflakes (ADR-0005):** minimal single-purpose tool, but no inline suppression and no path to import-sort/format — superseded by ruff on capability at equal dependency cost.
- **Add black for formatting:** rejected — `ruff format` is black-compatible, so a second tool is redundant.
- **mypy / pyright (typing):** catches the undefined-name/type class that `--select F` cannot, but is a separate, larger adoption — deferred to its own #487 shortlist decision, not folded in here.

## Lineage

[#198](https://github.com/avidrucker/pycats/issues/198) (do-not-adopt pyflakes research) → [ADR-0005](0005-adopt-pyflakes-quality-gate.md) / [#486](https://github.com/avidrucker/pycats/issues/486) (adopt pyflakes) → **ADR-0006 / #492 (adopt ruff)**. The #198 evidence (backlog shape, the now-resolved `game.py` blind spot) still stands; the #487 survey supplies the ruff-over-pyflakes finding.

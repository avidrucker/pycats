# ADR-0005 — Adopt pyflakes as a codebase-quality tool (pre-commit + on-demand)

> **⚠ SUPERSEDED by [ADR-0006](0006-adopt-ruff-lint-format.md) (2026-07-03).** pycats adopts
> **ruff** instead — ruff's `F` rules reimplement pyflakes' checks, with `# noqa` and a path to
> import-sort/format. This ADR is retained as the decision record; the *adopt-pyflakes verdict*
> no longer holds, but its **enforcement model (pre-commit + on-demand, no CI gate) and the
> backlog-cleanup work (#490, #495) carry over unchanged** under ruff.

- **Status:** Superseded by [ADR-0006](0006-adopt-ruff-lint-format.md) (2026-07-03)
- **Date:** 2026-07-03
- **Supersedes:** the keep/adopt **verdict** of research #198 (`docs/research/2026-06-29-pyflakes-tradeoffs.md`). The research *evidence* stands; only its "do not adopt" recommendation is reversed.
- **Tracked by:** epic [#486](https://github.com/avidrucker/pycats/issues/486) (this ADR is its slice 1). Approval to declare the dependency is [#197](https://github.com/avidrucker/pycats/issues/197) (granted in #486).

## Context

`pyflakes` was installed ad-hoc into the `.venv` during #193 (a `NameError` hunt) but was **never declared** — pycats has no manifest; deps live as README prose (`pygame-ce`, `pytest`, `statecharts-py`). Research **#198** (ELDERBERRY) then evaluated whether to formally adopt it and recommended **not** to, on this evidence:

- `pyflakes pycats/` reported **141 findings**: ~57 imported-but-unused, ~6 unused locals, ~8 redefinition/f-string/other, and **1 undefined-name that is a false positive** (`core/physics.py`'s `list["Player"]` string forward-ref under `from __future__ import annotations`, with no type-checker present).
- Its flagship check (undefined-name detection) found **zero real bugs** in the repo.
- It is **blind in the one file it was reached for**: `game.py:26`'s `from .config import *` makes pyflakes emit "unable to detect undefined names" for `game.py` — the single module with no test coverage (its loop runs at import). So today pyflakes cannot catch the `NameError` class that motivated #193.
- The research named **`ruff`** as the higher-leverage alternative (pyflakes' checks + pycodestyle + import-sort in one fast tool), but likewise a new dependency needing #197 approval.

The human decision (2026-07-03, avidrucker, recorded in #486) **reverses** that verdict: pycats **will** adopt pyflakes. The unused-import hygiene and a *coverable* undefined-name check (once `game.py` is unblocked) are judged worth the modest cost, and the star-import removal that unlocks the real value is independently `(READY)`.

## Decision

1. **Adopt `pyflakes`** as a declared **dev/quality dependency** with a documented, reproducible run recipe (`pyflakes pycats/`). This ADR is the #197 "yes".
2. **Enforcement model: pre-commit hook + on-demand.** A local pre-commit hook runs `pyflakes pycats/`; the same command is documented in `README`/`RULES` for manual runs. **No CI gate** — the repo has **no CI** to build on, and standing one up is out of scope (and arguably its own epic). Revisit a CI gate only if/when CI is introduced.
3. **Drive `pyflakes pycats/` to 0 findings** before the hook is turned on, so future findings are signal, not noise: remove genuinely-unused imports, rework or suppress the `core/physics.py` false positive, and allowlist any intentional case with an inline rationale.
4. **Remove `game.py:26`'s `from .config import *`** (explicit imports) so pyflakes' undefined-name check actually covers `game.py` — the value the tool was reached for.
5. **`ruff` remains the noted alternative**, deliberately **not** adopted here; a future ADR may revisit consolidating onto ruff (it subsumes pyflakes' checks). Adopting pyflakes now does not foreclose that.

## Execution (epic #486 slices — file/claim one at a time)

1. **This ADR** (slice 1).
2. **Unblock `game.py`** — replace the star-import with explicit imports (its own child; no ticket exists yet — the TODO is inline `(READY)`).
3. **Clean the backlog** — `pyflakes pycats/` → 0 (fix/suppress/allowlist; split if the diff is large).
4. **Declare the dep** — choose the home (`requirements-dev.txt` vs README prose vs introducing `pyproject.toml`) + a run recipe in `README`/`RULES`.
5. **Wire the pre-commit hook** (per this decision) so the clean state can't silently regress.

## Consequences

- **Positive:** unused-import drift becomes visible; once slice 2 lands, `game.py` gains a real undefined-name guard on the one untested module; the clean-state invariant is protected at commit time without new infra.
- **Negative / cost:** a one-time ~141-finding cleanup (slice 3); a new declared dev dependency to maintain; the pre-commit hook adds friction to commits (mitigated — `--no-verify` remains available for emergencies, and there is no CI to hard-block).
- **Residual:** the `core/physics.py` false positive must be handled explicitly (suppress or rework the annotation) or it blocks the "0 findings" goal. If the team later adopts a type-checker or `ruff`, revisit both the false positive and this ADR.

## Alternatives considered

- **On-demand only (no hook):** lightest, but the clean state can regress silently between manual runs — rejected in favor of a local guard.
- **CI gate:** strongest anti-regression, but requires standing up CI first (none exists) — deferred, not rejected; revisit when CI arrives.
- **`ruff` instead of pyflakes:** higher leverage long-term, but a larger config surface and still a new dep; out of scope for this decision, noted for a future ADR.

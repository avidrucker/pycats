# pyflakes trade-offs — keep, adopt, or remove?

**Research findings (#198).** Date: 2026-06-29. Agent: ELDERBERRY.
Feeds a human keep/remove decision; **no dependency change made in this ticket** (per
#197). Evidence gathered by running `pyflakes` across `pycats/` on this commit.

## TL;DR / recommendation

**Do not formally adopt pyflakes as a declared dependency or a CI gate right now.**
Its flagship value (undefined-name detection) found **zero real bugs** in this repo,
produced **one false positive**, and is **blinded in the exact file it was wanted for**
(`game.py`, by a `from .config import *`). What remains is unused-import linting, which
the codebase currently does not enforce (57 pre-existing unused imports). 

If lightweight linting is wanted later, the higher-leverage move is **`ruff`** (one
tool: pyflakes' checks + pycodestyle + import-sorting, fast, per-rule config) — but
that is also a new dependency and a `#197` approval decision. Either way, the
**prerequisite that actually unlocks value is removing the `game.py:26` star-import**
(already TODO'd "READY"); until then any pyflakes/ruff undefined-name check is blind
where it matters most.

Pragmatic option: keep pyflakes as an **on-demand, undeclared dev convenience** (run
manually when refactoring an import-time-only module like `game.py`), with no manifest
entry and no CI. That matches how it was used in #193 and costs nothing to the project.

---

## Q1 — What does pyflakes catch that pytest + py_compile don't?

`pyflakes pycats/` → **141 findings**, by category:

| Category | Count | Value |
|---|---|---|
| `imported but unused` | 57 | low — mostly pre-existing (`EAR_*`, `STRIPE_*`, `stats_print`, …) |
| `assigned to but never used` (locals) | 6 | low–medium |
| redefinition / f-string / other | ~8 | low |
| `from … import *` blind-spot notice | 1 | n/a (it's a *limitation*, not a finding) |
| **`undefined name`** (the flagship: catches NameErrors) | **1** | **false positive** (see Q2) |

`python -m py_compile` catches syntax errors only (not undefined names / unused). The
full `pytest` suite (450 passing) exercises runtime behaviour but **does not import
`game.py`** (it runs its `while running:` loop at import), so game.py has no test
coverage — the one place static analysis could add unique value.

## Q2 — How much of the flagship value is actually available? (Answer: almost none)

The single `undefined name` finding is **`pycats/core/physics.py:138: undefined name
'Player'`**, from `def resolve_player_push(players: list["Player"])`. This is a **false
positive**: `Player` appears only inside a **string forward-reference annotation**,
and physics.py has `from __future__ import annotations` (annotations never evaluated),
and the repo runs **no type-checker** (no mypy). So it is neither a runtime bug nor a
type-check failure — pyflakes flags a benign cosmetic annotation.

Meanwhile the **only star-import in the repo** is `game.py:26 from .config import *`,
which makes pyflakes emit *"unable to detect undefined names"* for game.py — i.e. it is
**blind in the one module that most needs undefined-name checking** (no test coverage,
de-globalized in #193). During #193, pyflakes' undefined-name detection did **not**
protect the game.py edit; what actually caught issues was grep (every read is
`battle.*`) + `py_compile` + a headless render smoke. The genuinely useful pyflakes
output in #193 was the **unused-import list** (it confirmed `combat` / `winner_loser` /
`resolve_player_push` became unused) — real but minor.

## Q3 — Signal vs noise / surfaced backlog

Adopting pyflakes as a gate would immediately surface a **~63-item backlog** (57 unused
imports + 6 unused locals) of *pre-existing* issues, almost all benign. That is a
one-time cleanup or a permanent allowlist to maintain — cost with little safety payoff.
The codebase clearly does not currently track unused imports (the star-import line even
carries a "replace all global imports … (READY)" TODO that has not been actioned).

## Q4 — Costs / risks of adopting

- New dependency to declare + pin (and there is **no manifest today** — see Q5 — so
  adoption also means *creating* a dependency-declaration mechanism).
- CI step + the 63-item baseline to clean or allowlist; ongoing false-positive triage
  (the physics.py annotation case will recur with forward-ref annotations).
- Supply-chain + reproducibility surface, exactly the concern behind #197.

## Q5 — Alternatives

| Option | Notes |
|---|---|
| **none** (status quo) | `pytest` (runtime) + `py_compile` (syntax) + targeted grep on refactors. Zero deps. What the project uses today. |
| **pyflakes** | Undefined-name + unused checks; blinded by star-imports; no autofix; no style. |
| **ruff** | Supersets pyflakes (F-rules) + pycodestyle + isort + autofix; very fast; per-rule enable/disable; single binary. Best value *if* linting is wanted. Still a #197 decision. |
| **flake8** | Wraps pyflakes + pycodestyle; older, slower than ruff; plugin sprawl. |

There is **no dependency manifest** in the repo (`requirements*.txt` / `pyproject.toml`
/ `setup.*` absent); dependencies are documented as README prose (`pip install
pygame-ce`, `pip install pytest pygame-ce`). `ruff`/`flake8` are **not installed**;
only `pyflakes` is (added ad-hoc in #193).

## Q6 — Recommendation (for the human keep/remove call)

1. **Remove from any "adopt" path** — do not declare it, do not CI-gate it. Its unique
   value (undefined names) is a false positive + a star-import blind spot here.
2. **Optionally keep it as an undeclared, on-demand dev tool** (manual runs when
   refactoring import-time-only modules). It is gitignored in `.venv`, changes no
   tracked file, and costs the project nothing. This is the lowest-friction outcome and
   matches the #193 usage. (If you'd rather not have it in your `.venv` at all,
   `pip uninstall pyflakes` — nothing depends on it.)
3. **The real prerequisite for value:** action the `game.py:26` star-import TODO
   (`from .config import *` → explicit imports). *Then* any F-checker (pyflakes or ruff)
   can actually catch undefined names in game.py — the place it matters. Consider
   filing that as its own small ticket; re-evaluate linting after.
4. If linting is genuinely wanted, prefer **ruff** over pyflakes (one fast tool,
   autofix, configurable) — but that is its own #197 approval.

**Net:** keep-as-optional-or-remove; **do not adopt/declare/CI-gate**. No safety is lost
versus today's `pytest` + `py_compile` + refactor-time grep.

---

### Sources / evidence
- `pyflakes pycats/` on this commit (141 findings; categories above).
- `pycats/core/physics.py:5,138` (the `__future__` annotations + string-annotation FP).
- `pycats/game.py:26` (the only star-import; "READY" TODO to replace it).
- Repo has no dependency manifest; deps in `README.md:17-43`.
- Incident + prior usage: #193 (pyflakes installed into `.venv`). Rule it informs: #197.

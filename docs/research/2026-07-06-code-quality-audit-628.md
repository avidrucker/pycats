# Code-quality audit — pycats v1 scorecard (#628)

**Role:** RESEARCH (audit) · 2026-07-06 · Agent: ELDERBERRY · `area:tracker`. **No production code changed.**

Ran the `avi-code-quality` tool (`assess.bb`) against pycats — a re-runnable per-concern
scorecard replacing scattered ad-hoc checks. This doc records the v1 baseline; re-run to
compare.

## How to re-run

```bash
CQ=/home/avi/Documents/Study/AI/avi_drucker/code-quality-analysis   # CODE_QUALITY_DIR
cd "$CQ" && ./assess.bb examples/pycats.edn
```

The config — **13 checks across 7 concerns** — lives at `$CQ/examples/pycats.edn` (in the
`code-quality-analysis` repo, **not** pycats; commit it there to version it). It encodes
pycats specifics: no `pyproject.toml` (deps in `requirements*.txt`, Python floor + ruff rules
in `ruff.toml`), no CI (the gate is the `.pre-commit-config.yaml` hook), and the SDL-dummy +
`PYTHONPATH=.` + repo-venv test invocation.

## Scorecard — 11 PASS / 2 FAIL

| Concern | Level | Pass | Fail | Verdict |
|---|---|---|---|---|
| correctness | first-order | 3 | 0 | ✅ PASS |
| delivery-safety | first-order | 3 | 0 | ✅ PASS |
| performance | first-order | 1 | 0 | ✅ PASS |
| security | first-order | 1 | 0 | ✅ PASS |
| maintainability | second-order | 1 | 0 | ✅ PASS |
| readability | second-order | 1 | 1 | ⚠ WARN |
| testability | second-order | 1 | 1 | ⚠ WARN |

| Check | Concern | Severity | Status |
|---|---|---|---|
| unit-tests-pass | correctness | required | ✅ PASS |
| no-fixme-in-src | correctness | advisory | ✅ PASS |
| golden-fixtures-exist | correctness | advisory | ✅ PASS |
| test-suite-time-bound (≤120 s) | performance | advisory | ✅ PASS |
| no-committed-secrets | security | recommended | ✅ PASS |
| python-floor-declared (ruff.toml) | delivery-safety | recommended | ✅ PASS |
| dependency-manifests-present | delivery-safety | recommended | ✅ PASS |
| precommit-hook-configured | delivery-safety | recommended | ✅ PASS |
| ruff-lint-clean | readability | recommended | ✅ PASS |
| **ruff-format-clean** | readability | recommended | ❌ **FAIL** |
| largest-module-size-bound (≤1300) | maintainability | advisory | ✅ PASS |
| **no-skipped-tests** | testability | advisory | ❌ **FAIL** |
| tests-present (≥50) | testability | advisory | ✅ PASS |

## The two failures

### 1. `ruff-format-clean` — ⚠ action-worthy (recommended)

`ruff format --check pycats/` reports **2 files drifted** from the format gate:

```
Would reformat: pycats/characters/birky_cat.py
Would reformat: pycats/sim/presenters.py
2 files would be reformatted, 77 files already formatted
```

The pre-commit hook only formats **changed** files, so files committed before the hook (or
via a `--no-verify` bypass) can drift and stay drifted. The one-line fix is
`ruff format pycats/`, but that is **out of scope for this audit** (#628 files remediation
separately). Recommend a small remediation ticket. *(Note: `birky_cat.py` traces to the
#589 crouch-geometry change — a real prior format slip this audit caught.)*

### 2. `no-skipped-tests` — benign, no action

The only marker is a **deliberate, documented `xfail`** in `tests/test_no_free_form_todos.py`
(the free-form-TODO-count guard — the `xfail` is designed to flip green when the count hits 0,
the #424 able-to-fail pattern). The second grep hit is docstring text describing that marker,
not a marker. **Not a disabled test** — no remediation. The check is advisory precisely because
pycats uses `xfail` deliberately; the count is a review signal, not a gate.

## Bottom line

pycats' quality baseline is strong: every **first-order** concern (correctness, delivery-safety,
performance, security) passes, tests are green (1207 passed / 1 xfailed), lint is clean, and the
render god-module sits just under the size alarm. The **one real gap** is whole-tree format drift
(2 files) — a symptom of the per-changed-file hook, worth a periodic `ruff format pycats/` sweep
or a CI/hook check over the full tree. Follow-up remediation is filed separately per this ticket's
scope.

## Refs

Audit ticket #628. Tool: `avi-code-quality` skill (`assess.bb` + `$CQ/examples/pycats.edn`).
Consolidates the existing gates: ruff lint+format (ADR-0006, #505/#529), pytest suite, the #502
pre-commit hook. Format-drift file `birky_cat.py` ← #589.

> Pls do a thorough code review of my github.com/avidrucker/pycats/ project. The focus of this code review is strictly test coverage and test quality - are the test thorough, robust, and well-written? I want there to be regression tests, unit tests, and anything else you recommend. After you review and analyze, pls make suggestions to improve the tests, their coverage, and note any gaps/problems you can identify.

I cloned the repo at `734227f`, installed the runtime deps, and ran the suite several ways — full, isolated per file, randomized order, with branch coverage, and with a custom mutation harness against the core combat modules. Here's what I found.

## Baseline numbers

| Metric | Value |
|---|---|
| Test files / test functions | 297 / 1841 |
| Tests collected & run | 2174 passed, 1 failed, 1 skipped, 1 xfailed |
| Test LOC vs source LOC | 34,563 vs 19,570 (1.77:1) |
| Wall time (`-m "not slow"`) | ~29s |
| Statement coverage | 93% (469/7046 missed) |
| Branch coverage | 85% (318 missing, 206 partial) |
| Files at 100% statement coverage | 76 of 119 |
| Tests with no `assert` / `pytest.raises` | 10 |
| Tests asserting on a constant | 0 |

That is, by the raw numbers, a strong suite — and the 29-second runtime is the single most valuable property it has, because it means the suite is actually runnable on every change. Most projects this size are 10× slower. The conftest design (headless SDL forced at session scope, autouse `_reset_runtime_settings`, the `_no_fake_fonts_leaked` teardown guard) shows real care about global-state hygiene, which is unusual and worth preserving.

The problems are not in the quantity. They're in a handful of places where the suite reports green for reasons other than the code being correct.

---

## Finding 1 — A test that passes only because an earlier test warmed a cache (false green)

`tests/test_main_menu_title.py::test_start_screen_renders_cat_fight_title` **fails when run on its own**:

```
$ pytest -q tests/test_main_menu_title.py
AttributeError: '_DummyFont' object has no attribute 'get_ascent'
1 failed in 0.15s
```

It also fails in the full suite under `--randomly-seed=4`. Mechanism: the test's `_DummyFont` implements only `size()` and `render()`. The render path reaches `draw_menu_screen -> draw_menu_button -> render_mixed_centered -> _compose_mixed`, which calls `unicode_font.get_ascent()`. In the default alphabetical ordering, an earlier test has already populated `text_renderer._mixed_surface_cache`, so `_compose_mixed` short-circuits on a cache hit and never touches the stub. Cold cache, and the stub's incompleteness is exposed.

This is the same class of bug the `_no_fake_fonts_leaked` guard in `tests/conftest.py` was written for (#709) — but that guard only fires on teardown, so it catches the *pollution* and not the *dependence on pollution*. The test's own docstring claims it is "order-independent"; it isn't.

Two fixes, and I'd do both:

- Make `_DummyFont` implement the full font protocol the render path uses (`get_ascent`, `get_height`, `get_linesize`, `metrics`), or better, subclass/spy on a real `pygame.font.Font` rather than replacing it. A stub that under-implements the interface it stands in for is the root cause.
- Add an autouse fixture that clears `text_renderer._mixed_surface_cache` (alongside the caches `render_isolation` already clears) so no test can inherit a warm cache from a neighbour. Right now only `test_main_menu_title` clears it, and only in its own teardown.

**I'd also add a standing guard:** a `make test-isolated` target (or a scripted loop) that runs each `tests/test_*.py` in its own pytest process. I ran exactly that across all 297 files and this was the only genuine isolation failure — so the cost of keeping it green is near zero, and it would have caught this at filing time.

## Finding 2 — An environment-coupled test that cannot pass outside your machine

`tests/test_make_help_targets.py::test_make_help_lists_goldens` fails on a fresh clone:

```
/bin/sh: 1: <repo>/.git/../.venv/bin/python: not found
make: *** [Makefile:30: help] Error 127
```

The Makefile hardcodes `.venv/bin/python`, and the test asserts `result.returncode == 0` on a real `make help` subprocess. On any environment without that exact venv layout — a fresh clone, a container, and any CI runner you eventually add — it's red. Since the test's actual intent is "the help text lists the goldens row," it should assert on `result.stdout` (which *was* produced correctly, per the captured output) and not on the exit code, or invoke the target with `PYTHON=$(which python)` overridden. As written, it's the one test in the suite that will block a CI adoption on day one.

## Finding 3 — Mutation testing: strong on arithmetic, weak on flags and equality

Line coverage tells you code *ran*; it doesn't tell you an assertion would notice if the code were wrong. So I built a small AST mutation harness (operator swaps, comparison-boundary swaps, boolean flips, constant perturbation), used `--cov-context=test` to map each mutated line to the tests that actually execute it, and ran only that subset per mutant.

**`pycats/combat/knockback.py` — excellent.** 17 of 20 sampled mutants killed. I hand-checked all three survivors and two are *equivalent mutants* (genuinely undetectable): `kb <= LOW` → `kb < LOW` and `kb >= HIGH` → `kb > HIGH` in `sakurai_angle` both fall through to the interpolation branch and produce the same value at the boundary. This module's tests are doing real work.

**The one real survivor is worth fixing.** In `sakurai_angle`:

```python
frac = (kb - SAKURAI_GROUNDED_LOW_KB) / (SAKURAI_GROUNDED_HIGH_KB - SAKURAI_GROUNDED_LOW_KB)
```

Mutating the denominator `HIGH - LOW` (28.0) to `HIGH + LOW` (148.0) survives. `test_grounded_scales_monotonically_between_thresholds` asserts `0.0 <= a_lo < a_mid < a_hi <= MAX_DEG`, which a 5×-too-shallow ramp still satisfies. The docstring explains this as a deliberate choice — pin the mechanism, not brittle magic angles — and that instinct is right, but it leaves the *interpolation rate* completely unpinned. You can close the gap without hardcoding a magic number, because the midpoint of a linear ramp is analytically half the max:

```python
def test_grounded_midpoint_is_half_the_max():
    """Linear ramp: kb halfway between the thresholds gives half the max angle."""
    mid = (SAKURAI_GROUNDED_LOW_KB + SAKURAI_GROUNDED_HIGH_KB) / 2.0
    assert sakurai_angle(mid, on_ground=True) == pytest.approx(SAKURAI_GROUNDED_MAX_DEG / 2.0)
```

That's still constant-derived, still survives retuning of the thresholds, and kills the mutant.

**`pycats/systems/hit_resolution.py` — noticeably weaker.** Roughly 10 survivors out of 28 sampled, versus 3 (mostly equivalent) out of 20 for `knockback.py`. The survivors cluster into a clear pattern:

- **Boolean-literal flips survive** at four sites (lines ~30, ~60, ~123, ~181). Flipping a hardcoded `False` to `True` — the kind of thing that would be a returned flag or an early-return default — changes nothing any test observes.
- **`Eq` → `NotEq` survives** at two adjacent sites (~152, ~154), meaning an equality check in that block can be inverted undetected.
- **An off-by-one survives** at line ~64: both `Add`→`Sub` and the constant `1`→`0` on that line go unnoticed, despite 83 tests executing it.

Note the asymmetry: those lines are covered by 77–119 tests each. This is the clearest possible illustration that coverage and assertion strength are different things — the most-executed lines in the module are among the least-verified. The tests are exercising the resolution path end-to-end (does a hit land, does damage go up) without asserting on the specific flags and equality outcomes the function computes along the way.

I'd treat this module as the top priority for new tests: read each of those sites and ask "what observable behaviour changes if this flips?" — if the answer is "nothing," either the flag is dead and should be deleted, or a test is missing.

**Two caveats on my numbers.** I capped each mutant's test selection at 60 tests, so survivors on lines covered by 77–119 tests could be false survivors killed by a test outside the truncated set — those specific ones (~60, ~64, ~123, ~152, ~154) need re-verification before you act. And `pycats/combat/move_clock.py` was still running when I stopped; 11 of 11 mutants killed at that point, which is a good sign for that module.

Also: I've referred to hit_resolution sites by line number here, which cuts against your convention of naming landmarks. I did that because the harness reports line numbers and I didn't want to guess at function names from mutation output. Worth re-anchoring to function names when you file these.

## Finding 4 — Coverage gaps, ranked by risk

Files below 90% statement coverage:

| File | Stmts | Miss | Cov |
|---|---|---|---|
| `shell/input_poll.py` | 10 | 6 | 40% |
| `game.py` | 22 | 11 | 50% |
| `ui/text_utils.py` | 332 | 150 | 55% |
| `shell/screen_render.py` | 24 | 10 | 58% |
| `entities/fighter_physics.py` | 45 | 14 | 69% |
| `shell/app.py` | 66 | 19 | 71% |
| `combat/value_status_census.py` | 106 | 18 | 83% |
| `screens/char_select.py` | 376 | 51 | 86% |
| `sim/presenters.py` | 184 | 24 | 87% |

Two of these matter more than the rest.

**`ui/text_utils.py` at 55% is the big one** — 150 uncovered statements, with a contiguous unreached block at lines 520–635 and another at 703–739. This is not a peripheral module: it's the shared text renderer with the global caches that caused Finding 1, and it's imported by conftest itself. An under-tested module holding mutable global state that every render test depends on is the highest-leverage gap in the tree. It's also where your prior review flagged bare `except` clauses, which is exactly the construct that hides failures from tests.

**`entities/fighter_physics.py` at 69%** is the only *gameplay-logic* file in the low band — the rest are shell/IO/render plumbing, where lower coverage is a defensible tradeoff. 14 uncovered statements in physics is 14 behaviours that can regress silently.

The shell files (`input_poll`, `app`, `screen_render`, `game`) are the pygame boundary, and you already have `test_core_pygame_boundary.py` enforcing the layering. I'd leave those alone rather than write mock-heavy tests of little value.

**The 85% branch coverage with 206 partial branches is the more interesting number than the 93% statement figure.** I'd switch the default coverage invocation to `--cov-branch` so the metric you watch is the one that reflects untested paths rather than unexecuted lines.

## Finding 5 — Structural observations on the suite

**No CI gate.** You already know this (it's in the prior review, and `.pre-commit-config.yaml` documents it as a deliberate "pre-commit + on-demand, NOT a CI gate" model). But the combination of 26–57 commits/day from an agent fleet, no CI, and the two false greens above is the actual risk here — not any individual test. A 29-second suite is *precisely* the case where a CI gate is nearly free. Both findings 1 and 2 are things a GitHub Actions run on a clean checkout would have caught immediately, and finding 2 is the reason to fix that test before adding the workflow rather than after.

**297 top-level test files in one flat directory, with several naming schemes.** You have `test_1036_hurt_labels.py` / `test_1207_datamine_hitboxes.py` (issue-numbered), `test_clank_c006.py` / `test_multihit_c003.py` (case-numbered), and ~280 feature-named files. Finding "where are the knockback tests" requires knowing the convention that was in force when they were written. I'd suggest subdirectories mirroring the package reorg you already did (`tests/combat/`, `tests/render/`, `tests/screens/`, `tests/shell/`, `tests/loadout/`) — it costs one mechanical move commit and makes the suite navigable. The issue-numbered files in particular are opaque: `test_1036_hurt_labels.py` is fine, but a bare number as the primary identifier means the filename stops being self-describing the moment the issue is closed.

**Ten tests with no assertion.** Most are probably fine (delegating to an asserting helper), but three are worth a look because their names promise verification: `test_render_cache.py::test_body_cache_pixel_identical_both_players`, `test_render_cache.py::test_body_cache_pixel_identical_left_facing`, and `test_fighter_to_json.py::test_output_is_json_serializable`. A test named "pixel identical" with no assert in its body is either delegating correctly or vacuous, and it's cheap to confirm which.

## What's genuinely good, and worth not breaking

I want to be clear that this suite is well above average, and several things in it I'd hold up as models:

- **The golden-snapshot layer with a human-readable summary sidecar.** `golden_util.summarize()` distilling opaque frame dumps into a reviewable digest (states, lives, KO frames, percent max), plus `tests/golden/REGEN_PROTOCOL.md`, solves the hardest problem with golden tests — that nobody can review a regen diff, so regens get rubber-stamped. That design is the right answer.
- **`PlayerSnap(*row)` reading snapshot fields by name** so the tuple can grow without touching the summarizer. That's the difference between a golden suite that ossifies the code and one that doesn't.
- **Docstrings that record the *reasoning*, including able-to-fail notes.** `test_sakurai_angle.py` documenting that the repo's own reference doc had the behaviour inverted, and `test_main_menu_title.py` documenting the revert-check done at filing time, is exactly the practice that keeps a fast-moving repo honest. Most suites have no equivalent.
- **The `_no_fake_fonts_leaked` autouse guard that fails the *polluting* test by name** rather than a mystified downstream victim. That's a sophisticated piece of test infrastructure and the error message is better than most production code's.
- **Structural/meta tests** (`test_core_pygame_boundary.py`, `test_no_free_form_todos.py`, `test_doc_landmarks.py`, `test_packaging.py` pinning `pyproject` deps to `requirements.txt`) — enforcing conventions as tests rather than as prose in RULES.md is the correct move for an agent-driven repo, since agents read tests more reliably than they read docs.

## Recommended additions, in priority order

**1. Property-based tests for the pure combat math** (`hypothesis`). Your `knockback`, `set_knockback`, `sakurai_angle`, `hitstun_frames`, `hitlag_frames`, and `decay_velocity` are pure functions over floats with documented invariants — the ideal target. Invariants worth asserting over generated inputs: knockback is monotonic in percent and in damage, and antitonic in weight; `hitstun_frames` never returns below `HITSTUN_FLOOR`; `hitlag_frames` never exceeds `HITLAG_CAP`; `decay_velocity` never flips sign and never overshoots zero (the docstring states both, and only example-based tests check them now); `sakurai_angle` always lands in `[0, MAX_DEG]`. This is the highest-value gap in the suite — it's cheap, it targets your strongest-tested module in the places examples can't reach, and it fits the generative-testing interest you've explored elsewhere. Given your Malli background, `hypothesis` will feel familiar.

**2. Fix Finding 1 and Finding 2, then add the CI workflow.** In that order. Run `pytest` plus `pytest` per-file-isolated plus `ruff check` on a clean checkout. The suite's speed makes this trivially affordable.

**3. Add the missing assertions in `hit_resolution.py`** targeting the mutation survivors, after re-verifying the truncated ones.

**4. Add the `sakurai_angle` midpoint test** above — one line, kills a real survivor.

**5. Raise `ui/text_utils.py` from 55%**, focusing on the `_compose_mixed` path and the 520–635 block, and on the cache-eviction behaviour (`_MIXED_CACHE_CAP`) that no test currently exercises.

**6. Switch the default coverage report to `--cov-branch`** and consider a ratchet test in the style of `test_authored_value_ratchet.py` — you already have the ratchet pattern in the repo; applying it to branch coverage would stop the fleet from silently diluting it.

**7. Periodic mutation testing rather than continuous.** `mutmut` or `cosmic-ray` against `pycats/combat/` and `pycats/systems/` only, run manually before releases, not in CI. My harness is at `/tmp/mutate.py` in concept but you'd want a real tool. The signal is high but the runtime cost makes it a monthly exercise, not a gate.

One thing I'd explicitly *not* recommend: writing tests to lift `shell/` and `game.py` coverage. The pygame boundary is thin by design, you have a fitness test enforcing that thinness, and mock-heavy tests there would add maintenance cost without adding confidence. 93% overall with the shell excluded is the right shape.

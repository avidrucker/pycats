# Test-suite audit — quality, robustness, thoroughness, effectiveness (#470)

**Role:** RESEARCH (DRAGONFRUIT), 2026-07-03. Read-only breadth survey (H:60m); **no test
rewrites**. Findings feed follow-up tickets filed one at a time. Suite baseline at audit time:
**174 test files, ~1060 test functions, 1085 passed / 1 xfailed in ~49s.**

## TL;DR
The suite is **healthy overall** — assertions are real, mocks are rare (fakes/real objects
preferred), no meaningful-state isolation leak remains, and the showcase gates are model
behavior-over-snapshot tests. The highest-leverage gap is **no coverage measurement** (so the
known `game.py` uncovered-loop blind spot is unquantified), followed by a **change-detector
oracle ratio** that flips on benign changes, and some **mechanical cleanup** (redundant SDL
boilerplate). No finding is a correctness emergency.

## What's healthy (evidence)
- **Assertions are real.** An AST sweep flagged 8 "no-assert" tests; all 8 delegate to
  assertion helpers that genuinely assert (verified `_assert_tint_clears`
  (`test_hurt_tint_clears_when_moving_or_attacking.py:53` — 3 real asserts incl. setup guards)
  and `_assert_one_focused_at_selected` (`test_menu_widget_rollout.py`)). No silent-pass Liars found.
- **Fakes over mocks.** Only **1 of 174** files uses `unittest.mock`
  (`test_menu_widget_rollout.py`); 27 use `monkeypatch` (pytest fixture). Matches the
  fakes-over-mock-frameworks discipline.
- **Isolation is sound.** The `os.environ` writes at module top are all the benign
  `SDL_VIDEODRIVER/AUDIODRIVER = "dummy"` headless idiom — the meaningful-state import-time
  pollution class that broke ~15 tests in #345 is **absent**.
- **Behavior-over-snapshot exemplar.** `test_showcase_demo.py` binds each feature to its
  caption's frame window (window-bound gates, #397) rather than pinning pixels — the pattern to
  propagate.
- **Descriptive names + extracted assertion helpers** throughout.

## Findings by axis (ranked within)

### 1. Thoroughness / coverage — **medium (highest leverage)**
- **No coverage tool is installed**, so coverage is unmeasured. The one module with real risk —
  `game.py`, which runs its `while running` loop **at import** so tests never import it (the
  #386 Options-freeze root cause) — is structurally **uncovered**, and nothing quantifies it or
  other gaps. → **Follow-up A** (adopt `pytest-cov`; ties #487 shortlist item 3).
- Coverage-shaped gaps noted anecdotally: the `game.py` per-state dispatch; input edge-timing;
  FSM transition legality. A number would target these instead of guessing.

### 2. Robustness / brittleness — **low-medium**
- **~20 files are byte-identical "oracle" tests** (golden sim + render-parity — e.g.
  `test_battle_screen_render.py`, `test_golden.py`, `test_full_match.py`, `golden_util.py`).
  These are legitimate (the golden is the oracle) but are **change-detectors**: a benign render
  or default change flips them (observed first-hand shifting the showcase render in #432 and per
  the #410 render-hash note). **Nothing marks which tests are pure snapshots vs behavior**, so a
  legitimate flip reads as a regression and invites a reflexive baseline-overwrite. → **Follow-up C**
  (tag + document the oracle tests; add a semantic-diff-on-failure hint).

### 3. Effectiveness / able-to-fail — **low (structurally clean, unproven)**
- Structural checks pass (§"What's healthy"), but there is **no systematic proof** each test
  fails when its behavior breaks — no mutation-testing or sampled revert-check pass. The suite's
  own discipline (every bugfix ships an able-to-fail test) covers new tests, not the ~1060
  legacy ones. → **Follow-up D** (sampled mutation/revert-check on the highest-value modules —
  combat + sim goldens).

### 4. Quality / anti-patterns — **low**
- **1 Inspector/Mockery test:** `test_menu_widget_rollout.py` spies on captured render *calls*
  and asserts on them rather than on observable output. Isolated (the only mock file). →
  **Follow-up E** (low priority).
- **Giant candidates** (moderate, not egregious): `test_nalio_cat.py` (370 LOC),
  `test_prone.py` / `test_cpu_difficulty.py` (363), `test_status_timer_bar.py` (324). Organized
  by feature; flagged for watch, no action now.
- No Free Ride / Happy-Path-only patterns surfaced in the sampled reads.

### 5. Speed / isolation — **low**
- **4 seeded-AI battle tests dominate runtime (~25s of ~49s):**
  `test_reactive_spacing.py::test_reactive_spacing_changes_a_real_battle_trajectory` (6.6s),
  `test_bot_match_resolves.py` (5.95s + 5.30s), `test_reach_aware.py` (3.65s). Acceptable for a
  local suite; only matters if a CI budget appears. → **Follow-up F** (low; mark `slow` if CI lands).
- **Redundant SDL boilerplate:** `conftest.py` already sets headless SDL at session start, yet
  **39 test files repeat** `os.environ.setdefault("SDL_*")` at module top — dead DRY, not a
  correctness issue. → **Follow-up B** (mechanical removal; golden-safe).

## Proposed follow-up tickets (file one at a time; lazy decomposition)
Ranked by leverage-per-effort:

- **B (filed → #496):** `DEV: drop the redundant per-file SDL os.environ boilerplate — conftest
  already sets it` — mechanical, 39 files, golden-safe, immediately actionable.
- **A:** `decision: adopt pytest-cov + measure coverage (quantify the game.py blind spot)` —
  #197-gated dep, so a decision (ties #487 survey shortlist item 3). **Highest leverage.**
- **C:** `DEV/convention: tag + document the byte-identical oracle tests (render-parity /
  sim-golden) so a benign flip is expected, not alarming; add a semantic-diff-on-failure helper.`
- **D:** `research: sampled mutation / revert-check pass on the highest-value tests (combat +
  sim goldens) to prove able-to-fail.`
- **E (low):** `DEV: test_menu_widget_rollout.py — assert on rendered output, not spied render
  calls (Inspector anti-pattern).`
- **F (low):** `DEV: mark the 4 seeded-AI battle tests slow / opt-out — only if a CI time budget lands.`

## Method / limits (time-box)
- Breadth over exhaustion: AST no-assert sweep + grep heuristics (os.environ, mock/monkeypatch,
  golden/sha) across all 174 files, plus targeted reads of the flagged cases. **Not** a
  per-test grade of all ~1060, and **not** a mutation run — that depth is Follow-up D.
- No dependency installed (coverage would need `pytest-cov`, a #197 decision — Follow-up A).
- Verdicts are from structure + sampled reads, not a coverage number (none exists yet — the
  point of Follow-up A).

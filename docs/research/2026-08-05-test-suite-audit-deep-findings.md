# Test-suite audit — deep second pass (robustness + performance)

**Ticket:** #1244 (research) · **Sequenced after:** #1242 (first-pass two-axis audit)
**Input doc read first:** [`docs/research/test-suite-audit-findings.md`](./test-suite-audit-findings.md) (#1242)
**Scope:** read-only. No test written, deleted, or edited here. Findings + a prioritized
remediation option space only — remediation is decided in follow-on tickets with the human,
one at a time (research never produces a spec).

---

## Bottom line

The suite is in strong shape and this pass **confirms** that from a second angle: 293 of 294
`test_*.py` files pass in complete isolation, and no vacuous test turned up in the sample. The
new signal is concentrated in five places, three of them reproduced with in-repo evidence:

1. **One real isolation failure survives at HEAD** (`test_main_menu_title`) — #1242 Finding 1
   reproduces, and the isolation seam that should prevent it (`render_isolation`) has a hole:
   it never resets `TextRenderer._mixed_surface_cache` and is opt-in rather than autouse.
2. **One orphan non-test** lurks in `tests/`: `test_air_dodge_shield_physics.py` is a
   print-based debug script with zero `def test_` that runs `pygame.init()` + `Player(...)`
   at collection. (Also a dead-code item — cross-ref #1232/#1237.)
3. **An import-time env write leaks for the session** — `test_hold_esc_quit.py` sets
   `PYCATS_CONFIG_DIR` at module import and never restores it (the #345 class). Masked today,
   latent order-dependence hazard.
4. **~45% of the 85 s runtime is 5 sim/bot-match tests**, and the `slow` marker that would
   deselect them is applied to only **1** test file — so `-m "not slow"` yields no real fast
   inner loop at HEAD.
5. **The `text_utils.py` 55%-coverage gap IS dead code.** The uncovered blocks are exactly the
   three symbols #1232 inventoried as unused (`render_unicode_char` + two diagnostics), now
   pending disposition in #1237. Covering them collides with possibly deleting them.

Evidence-based able-to-fail check: **one concrete `hit_resolution`/`knockback` survivor
reproduced** — a 5.3×-too-shallow `sakurai_angle` ramp passes the entire 2180-test suite green.

**Tooling constraint (a finding in itself):** the repo's own `.venv` runs pytest 9.1.1 with
only `python-discovery` — **no `pytest-cov`, `pytest-randomly`, `hypothesis`, or a mutation
tool.** So #1242's headline numbers (93% statement / 85% branch coverage, the shuffle seeds,
the mutation survivor counts) are **not reproducible in-repo** without a dependency approval.
This pass used only what runs dependency-free: a per-file isolation sweep, `--durations`,
targeted reverts, and static reads.

---

## Method

- **HEAD:** `6f4428b` (the commit that landed #1242's doc). Suite baseline: **2180 passed, 1
  xfailed**, warm wall-clock **85–89 s** (3 runs: 89.4 s, 85.2 s, 77.6 s-under-mutation),
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, main-repo `.venv`, `-m pytest -q`.
- **(C) Isolation sweep** — each of 294 `tests/test_*.py` run in its own pytest process
  (`-p no:cacheprovider`), dependency-free (no `pytest-randomly` needed).
- **(D) Performance** — `--durations=25` on an unloaded machine (measured *after* the sweep so
  the numbers aren't skewed by concurrent load). Cross-references #810, which owns the full
  runtime profile — this is a quality-consequence callout, not that profile.
- **(A)/(B) deeper** — static reads of the #1242-flagged files, landmark re-anchoring of the
  mutation sites, and **one** in-repo mutation revert as an able-to-fail confirmation.

---

## (C) Robustness — the runtime-only properties #1242 held out of scope

### C1 — The suite is unusually isolation-clean (positive, reproduced)
The per-file sweep ran all 294 files each in a fresh process. Result: **293 clean; 1 real
isolation failure; 1 orphan file that collects no tests** (see C4). Combined with the strong
`conftest.py` hygiene (autouse `_reset_runtime_settings`, the `_no_fake_fonts_leaked` teardown
guard that fails the *polluting* test by name), the suite's global-state discipline is above
average and worth preserving.

### C2 — The one isolation failure, and the seam hole under it (deeper than #1242 F1)
| | |
|---|---|
| Axis | (C) robustness / (B) quality |
| Location | `tests/test_main_menu_title.py::test_start_screen_renders_cat_fight_title` |
| Evidence | Fails alone at HEAD: `AttributeError: '_DummyFont' object has no attribute 'get_ascent'` (`pycats/ui/text_utils.py:394`, inside `TextRenderer._compose_mixed`). Passes in the full suite only because an earlier test warmed `_mixed_surface_cache`. |
| Risk | tooling (false green — a stub that under-implements the font protocol) |

**What this pass adds beyond #1242.** The isolation seam that *should* prevent this has a hole:
- `TextRenderer._mixed_surface_cache` (a per-instance dict on the module-global
  `text_renderer` singleton) is cleared by **exactly one** place — `test_main_menu_title`'s own
  teardown (`tests/test_main_menu_title.py:61`). No autouse fixture resets it.
- The `render_isolation` fixture clears five caches (`font_cache`, `render_battle._body_cache`,
  `_body_layers_cache`, `_tail_seg_cache`, `_tail_outline_cache`) but **not**
  `_mixed_surface_cache`.
- `render_isolation` is **opt-in** (`pytestmark = usefixtures("render_isolation")`), not
  autouse. At least ten render tests reach `render_mixed` / `draw_menu` **without** opting in
  (e.g. `test_menu_font_scale_render.py`, `test_menu_button.py`, `test_options_grid.py`,
  `test_main_menu_title.py` itself).

So the fix #1242 proposed (complete the `_DummyFont` protocol) treats the symptom; the seam gap
(`_mixed_surface_cache` reachable across tests with no reset) is the deeper cause.

### C3 — Import-time env write that leaks for the session (#345 class)
| | |
|---|---|
| Axis | (C) robustness |
| Location | `tests/test_hold_esc_quit.py` (module top level) |
| Evidence | `os.environ["PYCATS_CONFIG_DIR"] = _TMP_CONFIG` at import, never restored; also `pygame.init()` at import. `PYCATS_CONFIG_DIR` **is** read by `pycats/storage/settings.py` (the `override` lookup). Every other test that touches it uses `monkeypatch.setenv` (auto-reverted): `test_options_keybind_sets.py`, `test_input_history_toggle.py`, `test_keybind_sets_menu.py`. |
| Risk | tooling (latent order-dependence — a later test that reads settings without setting the env inherits this stale tmp dir) |

No failure is observed today (nothing currently depends on the default config path after this
module is imported), so it is masked — but it is precisely the pattern that broke ~15 tests in
#345. The fix is to route the redirect through a fixture / `monkeypatch`, not an import-time
`os.environ` assignment.

### C4 — Orphan non-test script in `tests/` (cross-ref #1232/#1237)
| | |
|---|---|
| Axis | (C) robustness / (B) quality |
| Location | `tests/test_air_dodge_shield_physics.py` |
| Evidence | `#!/usr/bin/env python3` debug script: **0** `def test_`, 13 `print(...)`, `pygame.init()` + `Player(400, 250, ...)` executed at module import. pytest collects it (name matches `test_*.py`), runs its side-effectful import, and reports "no tests ran" for the file. |
| Risk | tooling (dead file — no assertion can ever fail; runs side effects every full collection) |

This is the same class as #1232's uncalled-code inventory. Route its removal through #1237's
dead-code disposition rather than deleting it here.

---

## (D) Performance — quality consequence (cross-ref #810 for the full profile)

`--durations=25`, top of the distribution:

| Rank | Test | Time |
|---|---|---|
| 1 | `test_archetypes.py::test_attacker_drives_the_ko_arc` | 9.69 s |
| 2 | `test_bot_match_resolves.py::test_no_fighter_is_juggled_past_a_sane_percent` | 8.89 s |
| 3 | `test_bot_match_resolves.py::test_l5_bot_converts_a_ko` | 8.78 s |
| 4 | `test_battle_log.py::test_events_from_real_seeded_run` | 6.02 s |
| 5 | `test_reach_aware.py::test_reach_aware_changes_leveled_sim_trajectory` | 5.44 s |
| | **Top 5 subtotal** | **≈ 38.8 s ≈ 45% of the 85 s wall-clock** |

All five are multi-frame **full-battle simulation / bot-match** tests. The tail (≈2155 tests)
is fast.

**Quality consequence — the fast-loop escape hatch is inert at HEAD.** `pytest.ini` registers
`slow: long-running benchmark tests (deselect with -m "not slow")`, but the marker is applied
to only **1** test file, and **none** of the five heavies above carry it. So `-m "not slow"`
removes almost nothing — there is no real sub-30 s inner loop today. (This differs from #1242's
`-m "not slow" ≈ 29 s` figure, which came from the reviewer's own clone; at HEAD the marker is
under-applied.) Tagging the five sim/bot-match heavies (or the sim class) `@pytest.mark.slow`
would restore a fast local loop — coordinate with #810, which owns the profiling numbers.

---

## Deeper on #1242's (A) coverage gaps and (B) quality

### A1 — The `text_utils.py` 55% gap **is** the #1232 dead code (synthesis)
| | |
|---|---|
| Axis | (A) gap |
| Location | `pycats/ui/text_utils.py` |
| Evidence | #1242's uncovered blocks (its lines 520–635 and 703–739) map exactly to `TextRenderer.render_unicode_char` (`text_utils.py:503`) and the two module diagnostics `run_font_diagnostics` (`:701`) + `quick_unicode_test` (`:706`) — the **same three symbols #1232 inventoried as unused** and #1237 is deciding whether to delete (D2 and D1 respectively). |
| Risk | none-to-cover / decision-blocked |

The 55%-coverage recommendation in #1242 (its rec #5, "raise `text_utils.py` from 55%") and
#1232's dead-code list are the **same finding from two angles**: the uncovered lines are the
dead code. **Resolve #1237 first.** Writing coverage tests for `render_unicode_char` before
that ruling means testing code that may be removed. Once #1237 rules "keep", the coverage work
is well-scoped; if it rules "drop", the gap closes by deletion.

### A2 — Broad `except Exception` handlers in `text_utils.py`
| | |
|---|---|
| Axis | (A) gap / (B) quality |
| Location | `pycats/ui/text_utils.py` — 12 `except Exception` sites (font selection/fallback paths, several on the uncovered lines) |
| Evidence | `grep -nE 'except\b'` → 12 hits (`:151, :158, :168, :210, :216, :250, :261, :410, :573, :621, :724, :736`) |
| Risk | tooling (broad handlers swallow failures, so an under-tested path can regress without a red test) |

Directional (the #1242 review flagged the class); pairs with A1 — much of this sits in the
dead/uncovered region, so #1237's ruling scopes how much matters.

### B1 — `hit_resolution.py` mutation survivors, re-anchored to landmarks
#1242 Finding 3 reported survivors by line number and asked they be re-anchored to function
names. At HEAD (`pycats/systems/hit_resolution.py`, 246 lines, functions `_attacks_overlap`,
`_clank_strength`, `_box_priority_key`, `_negate`, `_resolve_clanks`, `process_hits`), the
reported clusters map to:
- boolean-flip / off-by-one sites (#1242's ~60, ~64) → **`_resolve_clanks`**
- boolean-flip + `Eq`→`NotEq` sites (#1242's ~123, ~152, ~154, ~181) → **`process_hits`**

The exact per-line survival could not be re-verified in-repo (no coverage-context / mutation
tooling — see the tooling constraint), so treat the specific lines as directional; the
**concentration of assertion-weakness in `_resolve_clanks` and `process_hits`** is the
reproducible part and the right target for new assertions. Coordinate with #995/#1014 (fresh
combat-claim tests) so this doesn't duplicate that effort.

### B2 — Able-to-fail confirmed by evidence (one reproduced survivor)
| | |
|---|---|
| Axis | (B) quality |
| Location | `pycats/combat/knockback.py::sakurai_angle` (the grounded interpolation `frac`) |
| Evidence | Mutating the denominator `SAKURAI_GROUNDED_HIGH_KB - SAKURAI_GROUNDED_LOW_KB` → `HIGH + LOW` (a 5.3× shallower ramp) leaves **all 2180 tests green** (`test_sakurai_angle.py` + `test_knockback.py`: 20 passed; full suite: 2180 passed). Restored via `git checkout` after. |
| Risk | engine-correctness (the launch-angle interpolation *rate* is unpinned — only the endpoints and monotonicity are asserted) |

This is the one #1242 survivor confirmed with in-repo evidence rather than inspection. #1242's
proposed fix (a midpoint-is-half-the-max test, still constant-derived, no magic angle) would
kill it — a good candidate for the combat-test follow-up.

### B3 — Vacuous-assert candidates resolved as clean (no action)
#1242 flagged three "no explicit assert" tests as worth a look. Checked:
- `test_render_cache.py::test_body_cache_pixel_identical_{both_players,left_facing}` — delegate
  to `_compare(p)`, which asserts `_bytes(direct) == _bytes(cached)`. **Not vacuous.**
- `test_fighter_to_json.py::test_output_is_json_serializable` — `json.dumps(...)` with no
  assert is a valid **does-not-raise** test (fails if serialization breaks). **Not vacuous.**

No vacuous / can't-go-red test was found in the sample.

---

## Meta finding — the in-repo venv can't run the first-pass tooling

The repo's `.venv` (pytest 9.1.1, plugin `python-discovery` only) has no `pytest-cov`,
`pytest-randomly`, `hypothesis`, or mutation tool. Consequences:
- #1242's 93%/85% coverage figures, its shuffle seeds, and its mutation survivor counts are
  **not reproducible in-repo** — they were produced on the reviewer's own clone with dev deps.
- The dependency-free guards this pass leaned on (per-file isolation loop, `--durations`,
  targeted reverts) are the *only* robustness tooling available in-repo today.
- Property-based tests (#1242 rec #1) and a standing branch-coverage ratchet both require deps.

Adding `pytest-cov` + `pytest-randomly` (+ optionally `hypothesis`) as **dev** dependencies
would make coverage, shuffle-order, and property testing runnable in-repo — but that is
**gated on explicit human approval** (RULES.md → Dependencies). Proposed here, not installed.

---

## Prioritized remediation option space (candidates — none filed here)

Ranked by risk. Each is a one-line candidate for a downstream ticket, filed one-at-a-time with
the human; several are decision- or dependency-blocked.

1. **[robustness · player-tooling]** Close the render isolation hole: have `render_isolation`
   also clear `_mixed_surface_cache` (and/or make it autouse for render tests), and complete
   `_DummyFont` to the full font protocol (or spy a real `pygame.font.Font`). Fixes C2 at root.
2. **[tooling]** Add a standing per-file isolation guard (`make test-isolated` or a scripted
   loop). Near-zero cost — 1 real failure across 294 files — and catches order-dependence at
   filing time. (Its noise mode: pytest exit-5 "no tests collected" is not a failure; filter it.)
3. **[engine-correctness]** Strengthen `hit_resolution.py` assertions in `_resolve_clanks` /
   `process_hits`, and add the `sakurai_angle` midpoint test (kills the B2 survivor).
   Coordinate with #995/#1014 so it doesn't duplicate the combat-claim tests.
4. **[hygiene · cross-#1232]** Remove or relocate `test_air_dodge_shield_physics.py` (C4). Route
   through #1237's dead-code disposition.
5. **[robustness]** Restore the env in `test_hold_esc_quit.py` via a fixture / `monkeypatch`
   instead of an import-time `os.environ` write (C3).
6. **[perf · downstream of #810]** Tag the 5 sim/bot-match heavies (or the sim class)
   `@pytest.mark.slow` so `-m "not slow"` yields a real fast loop (D).
7. **[tooling · dependency-gated]** Add `pytest-cov` + `pytest-randomly` (+ `hypothesis`) as dev
   deps so coverage/branch/shuffle/property testing and a branch-coverage ratchet are runnable
   in-repo. Needs human dependency approval — propose, don't install.
8. **[decision-blocked]** Resolve #1237 (`render_unicode_char` + diagnostics keep/drop) **before**
   investing in `text_utils.py` coverage — the 55% gap is largely that dead code (A1). Not new
   work; a sequencing note.

---

## Out of scope (unchanged from the ticket)

- Writing, deleting, or editing any test — all remediation is downstream, one at a time.
- Re-deriving #1242's breadth inventory — cited and deepened, not repeated.
- Installing any coverage / test / profiling dependency (human-approval gated — see the meta
  finding).
- The full suite runtime profile — that is #810; its numbers are pulled/cross-referenced, not
  redone.
- Test-file consolidation implementation — that is #833 §7 / #1057.

## Refs

Input: **#1242** (first-pass two-axis audit). Adjacent, all OPEN: #810 (suite runtime profile) ·
#833 §7 / #1057 (test-file consolidation) · #995 / #1014 (fresh combat-claim tests) · #957
(sourced-JSON conversion-seam test). Cross-cutting: **#1232** (uncalled-code inventory) /
**#1237** (dead-code disposition — gates A1 and C4). Hazard origins: #345 (env-at-import, C3),
#386 (import-time dispatch), #709 (cached-fake-in-singleton, the guard behind C1). Discipline:
RULES "Fixing bugs" (every fix lands an able-to-fail test), "Dependencies" (the meta finding),
yegor-unit-tests.

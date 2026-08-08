# TIL 2026-07-02 — GRAPE

**Context:** A tracker + screens session. Closed the ICE-scoring research/spec (#199) and filed its follow-up (#449); then took a user request to "make Esc back out of every sub-menu" from a raw report all the way to shipped code — filing #453, pinning its exact behaviour in a `grill-me` session (spawning #460 as post-v1), then implementing #453 via TDD.

---

## 1. A user's bug report is a lead, not a spec — verify the mechanism against the code first

**What happened:** The ask was: "make Esc work in every sub-menu — it works in battle and the main menu but not character-select or stats." I almost filed that verbatim. Grepping first (`K_ESCAPE` across `pycats/`) showed the report's *mechanism* was wrong: Esc was never a back key anywhere. It was **hold-to-quit** (2s, `_tick_esc_quit_timer`) plus **tap-exits-fullscreen** in `game.py`; sub-menu back-out was on **B** ("Press B to go back"), and battle "pause" was on **P**. What the user read as "Esc works in battle" was the hold-to-quit arc. Filing their mental model as the ticket's premise would have baked a false "it used to work here" into #453.

**What I learned:** RULES.md already says *"Verify a delegated/audit finding in the code before filing or acting on it — a finding is a lead, not a fact."* That rule reads like it's about *subagent/audit* findings, but a **user's bug report is the same shape**: authoritative-sounding prose describing behaviour that the code may not actually implement. The fix is identical — open the named `file:func` and confirm before the report becomes a ticket. I filed #453 with the *accurate* current behaviour documented and the user's model noted as the reported-symptom, so the implementer wasn't misled.

**The rule:** **Before filing a user-reported bug, grep the handler and confirm the mechanism — the reporter's "it works like X" is a symptom, not a spec (RULES.md "verify a finding" applies to user reports too).**

---

## 2. `grill-me` before an FSM/navigation change pays for itself in the transition table

**What happened:** #453 looked simple ("Esc backs out one level"). A `grill-me` pass surfaced two genuine forks the ticket had glossed: (a) the stated model said `playing → char_select`, but the user also wanted end-of-battle stats shown on early quit — those contradict unless you decide whether hold-Esc routes *through* the stats screen; and (b) "no instant Esc anywhere" directly collides with the existing tap-Esc-exits-fullscreen binding. Both got resolved in conversation (choice B: hold-Esc never shows stats, stats stay on the pause `end_match` button; F11 becomes the sole fullscreen toggle) and written into a locked transition table before I touched code.

**What I learned:** For a state-machine change, the unit that must be unambiguous *before coding* isn't the feature description — it's the **full source→destination table, every node**. The ambiguities didn't live in the happy path; they lived at the awkward nodes (`pause`, `win_screen`, the fullscreen carve-out). Pinning all six rows up front turned the TDD loop mechanical — each row became one red→green test. This is the same architect-then-courier discipline the team already values (design in writing, then execute), applied to an FSM: the "design artifact" is the transition table.

**The rule:** **For any FSM/navigation change, lock the complete source→destination table (every state, including the awkward ones) before coding — grill the forks out first; the table is the spec each test asserts one row of.**

---

## 3. A failing test that mutated a global without a fixture poisoned ~19 unrelated tests

**What happened:** After I removed `_tick_esc_quit_timer` and renamed the setting, the full suite came back with **31 failures** — but only 3 were mine. The other ~19 were `KeyError` in `test_settings.py`, `test_input_history_toggle.py`, `test_show_controls_toggle.py` — files I never touched. The tell was exactly that: *failures in code I didn't change.* Root cause: the old `test_hold_esc_integration.py::test_toggle_off_prevents_quit` did a manual `settings_mod.load = lambda: {...}` and restored it on the **last line** of the test. My change made that test throw an `AttributeError` (calling the deleted `_tick_esc_quit_timer`) **before** reaching the restore line — so `settings.load` stayed stubbed to `{"esc_hold_to_navigate": False}` for every subsequent test in the session, and every downstream `load()["windowed_scale"]` blew up.

**What I learned:** This is the same failure family as my standing note on `os.environ` at a test-module top level (#345) — **global mutation in a test leaks past the test unless the restore is guaranteed**. A manual `x = orig; ...; x = orig` restore is *not* guaranteed: any exception before the restore line skips it. The `monkeypatch` fixture (or a `try/finally`) restores even on failure. The diagnostic reflex worth keeping: **when a change reddens tests in files it never touched, suspect a leaked global from a test that failed earlier in the run**, not your change touching those files. I deleted the offending file (its behaviour was subsumed — see #4) and the cascade vanished.

**The rule:** **Never restore a monkeypatched global by hand at the end of a test — use the `monkeypatch` fixture or `try/finally`, so a mid-test failure can't leak the stub into the rest of the session. Collateral failures in untouched files = a leaked global, not your diff.** (Added to RULES.md → Code conventions in this commit; cousin of the #345 `os.environ` pin.)

---

## 4. Deleting a test is legitimate when its coverage moves to a better public-interface test

**What happened:** `test_hold_esc_integration.py` poked internals — it built a stub engine (`type('Engine', (), {'state': ...})`) and called the private `_tick_esc_quit_timer` directly, asserting the old `esc_quit_to_menu` flag. I replaced it with `test_hold_esc_navigation.py`, which drives the **real** `ScreenStateManager` through its public `update()` / `get_state()` and asserts the whole transition ladder. The new file strictly subsumes the old (threshold, release-reset, setting-off, every per-state destination, main-menu quit) *and* tests the actual new behaviour the old one contradicted.

**What I learned:** Deleting a test file can look like dropping coverage, so it needs an explicit justification trail: name the replacement, confirm every old assertion has a home in it, and say so in the commit body. The win is that the replacement tests *behaviour through the public interface* rather than an internal method — so it survives the very refactor that broke the old one (I moved the tick out of `_tick_esc_quit_timer` into `update()`; a public-interface test doesn't care). Revert-check still applies: neutralising `esc_hold_complete()` reddened 7 of the new file's cases, proving they're coupled to the production change.

**The rule:** **A test that pokes a private method is a liability across a refactor — replace it with one that drives the public interface, and justify the deletion in the commit by naming the superseding test and its revert-check.**

---

## What landed

| Artifact | Change |
|---|---|
| `docs/research-spec-199-ice-scoring.md` | ICE-scoring spec: committed advisory CSV, lccjs rubric verbatim, slot-3 composition (#199, closed) |
| #449 | Filed — the ICE-scoring implementation follow-up (`stats/ice-scores.csv` + orchestrate wiring) |
| #453 | Filed → grilled → rewritten → **shipped**: unified hold-Esc (2s) ladder; `esc_hold_to_navigate` rename; pause `return_to_char_select`; F11-only fullscreen |
| #460 | Filed — post-v1 dedicated end-of-battle stats screen (subsumes `win_screen`) |
| `RULES.md` | Added the monkeypatch-restore-via-fixture bullet (lesson #3) |

## Related artifacts

- Issues #199, #449, #453, #460, #472
- Sibling env-leak pin: [TIL 2026-07-01 DRAGONFRUIT](./today-i-learned-2026-07-01-dragonfruit.md) (§ `os.environ.setdefault` at module top level, #345)
- Memory: `pytest-env-at-import-pollutes-session`, `confirm-before-closing-work`

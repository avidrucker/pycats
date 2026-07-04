# TIL 2026-07-04 — ELDERBERRY

**Context:** A screens/profiles session on epic #438's tail: shipped the keybinding-set Options UI (#463 — save/load/rename/delete) and the player-profile data + nickname render seam (#478). Then ran an orchestration round (`/fruit-agent-orchestrate`), cross-linked #470↔#497, filed the PDD-feasibility research ticket (#503), and — at the user's direction — committed a plain-language test-suite overview straight to `main`.

---

## 1. A function that only runs inside a cache needs its new input in the cache *key*

**What happened:** #478 adds a nickname above the fighter via `draw_player_name`. I changed the label to `nickname or char_name` and threaded `nickname` onto the `_CatShim` — then a grep reminded me `draw_player_name` is *never* called directly: its only call site is line 362 of `render_battle.py`, inside `_cat_body_surface`, which **memoises the whole body composite** keyed by `(char_color, stripe, eye, char_name, facing, tint, face_style, size)`. Threading the nickname onto the shim wasn't enough — a nickname change would keep serving the cached surface built with the old label.

**What I learned:** The fix had two halves, not one: add `nickname` to `_CatShim` *and* to the cache key. I wrote the able-to-fail proof deliberately — `test_body_composite_reflects_and_invalidates_on_nickname` renders, sets `p.nickname`, renders again, asserts the bytes differ. It goes red if the key omits nickname (stale hit). This is the same shape as CHERRY's #401 memo-cache-stale-text bug: a cache keyed on a subset of what the output depends on freezes the omitted dimension.

**The rule:** **When you add an input to a function that runs inside a memo/cache, add it to the cache key in the same change — and prove the invalidation with a test that reds on a stale hit.** (Precedent: [[today-i-learned-2026-07-01-cherry]] #401.)

---

## 2. Host new nav state in the adapter, not the collaborator whose tests lock its behaviour

**What happened:** #463 needed a "Schemes..." entry point on the keybind screen. The obvious place was `KeybindMenu.nav`, but `test_keybind_menu.py::test_nav_moves_the_focused_action_and_wraps` pins that `nav(-1)` from the first action wraps to the *last action* — extend that nav over an extra row and the test reddens. So I kept the trailing-row cursor (`keybind_on_schemes`) in the `OptionsMenu` *adapter* and only called `kb.nav` for the action range; `KeybindMenu`'s action-only nav (and all 7 of its tests) stayed byte-for-byte unchanged.

**What I learned:** The adapter/model split isn't only about testability — it's a seam that lets you add screen behaviour *around* a pure collaborator without perturbing the collaborator's locked invariants. The new row's whole lifecycle (nav wrap into it, activate opens the sub-mode, render highlights it) lives in the layer that owns the screen, where no existing test constrains it.

**The rule:** **When a new feature would break a collaborator's tested invariant, own the new state in the adapter that composes it — don't widen the collaborator.**

---

## 3. A cohesive unit can land ahead of some of its tests — recover the able-to-fail proof with a scoped mutation sweep

**What happened:** `KeybindSetsMenu` (#463) is one state machine (menu/list/text/confirm). I built the whole thing to green the first save test, which meant the load/rename/delete branches got code *before* their own failing test — a soft TDD violation. Rather than pretend, I neutralised the four `keybind_store` write/read calls in one mutation pass (a throwaway script), ran the suite, and confirmed exactly the **5 persistence-critical tests reddened while the 3 pure-logic tests (nav/back/empty-message) held** — then restored from a backup and re-greened.

**What I learned:** "Watched it fail" is the actual guarantee TDD sells; when the code precedes the test, a targeted mutation *reconstructs* that guarantee per-behaviour and even maps which test guards which branch. The 5-red/3-green split was the evidence the persistence tests weren't tautologies. This is the render-uncovered mutation-check discipline ([[render-hash-verify-uncovered]]) applied to logic.

**The rule:** **If a cohesive unit outran its tests, a scoped mutation sweep (break each behaviour, confirm the mapped tests red, restore) restores the able-to-fail proof — do it, don't hand-wave the cycle.**

---

## 4. The `area:*` lane is necessary but not sufficient — confirm file targets by grep before assigning

**What happened:** In the orchestration round I nearly co-scheduled #478 (`area:screens`), #469 and #336 (`area:display`) — different lanes, so the gate said fine. But a two-minute grep showed all three edit **`render_battle.py`**: #478 in `draw_player_name`, #469 in `draw_controls`, #336 in `draw_hud`. That's the 5a-bis same-file collision the lane gate can't see. I held #469/#336 (hard refusal) and moved the display agent off render entirely — rather than tell two agents to "coordinate" (the forbidden move that offloads a concurrency decision to runtime).

**What I learned:** Sub-theme separation (controls legend vs HUD vs name label) is not file separation. The worktree-per-task isolation model only holds if each assignment is executable alone; a shared file breaks that regardless of area label.

**The rule:** **Before finalizing parallel assignments, grep the plausible file targets — on any same-file overlap, hold one ticket; never resolve it by asking agents to coordinate.** (Codified: `fruit-agent-orchestrate` 5a-bis.)

---

## 5. The orchestration snapshot decays — a ticket assigned to me was already done

**What happened:** I was handed #497 (test-double policy research). `pmtools claim 497` returned `✗ #497 is CLOSED`. Another agent had finished it (`a7cae73`, closed ~15 min earlier) *while the assignment paragraph was in flight*. I read the delivered doc to confirm it was real (not a stub — full taxonomy + rubric + house rule), and **did not `--force` a re-do**. The assignment list was generated before that close and had already rotted.

**What I learned:** This is the exact freshness-decay the orchestrate skill's own banner warns about, and GRAPE hit it too (#413 taken minutes after assignment). The right response to a stale assignment naming a closed ticket is *verify-and-stop*, not redo — and to recommend re-running the triage rather than trusting the decayed snapshot.

**The rule:** **Verify ticket state at claim time; a stale assignment pointing at a CLOSED ticket means report the completed work and stop — re-triage, don't rebuild.** (Standing: [[verify-ticket-state-before-blocker-claims]]; precedent [[today-i-learned-2026-07-01-grape]] #413.)

---

## 6. An explicit owner directive overrides a workflow rule — but still rebase before pushing

**What happened:** The user asked me to save the test-suite overview as `docs/snapshot-current-tests-overview.md` and "commit it to main and push it." The standing rule is *never `git push` to `main` by hand — pmtools owns the race-safe push*. But that rule governs ticket work; this was a standalone doc the owner explicitly directed. User instructions take precedence over workflow conventions, so I committed to `main` directly — but `git pull --rebase origin main` **first** (it was up to date, but the point is to not clobber a sibling agent's push), then pushed.

**What I learned:** "Never push to main" is a *safety* rule about the fleet race, not a moral absolute — an explicit owner override is valid, and the way to honour both the directive and the fleet is to rebase-then-push, not to refuse.

**The rule:** **An explicit owner directive supersedes the tool-owned-push convention — but rebase-before-push so the manual commit still respects the fleet.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/keybind_sets_menu.py` + `options_menu.py` | Keybinding-set save/load/rename/delete UI (#463) — pure controller + thin adapter |
| `pycats/profile_store.py` + `entities/player.py` + `render_battle.py` | Profile store + `Player.nickname` + nickname render seam (#478) |
| `docs/snapshot-current-tests-overview.md` | Plain-language suite map (categories, `monkeypatch`, `xfail`) — pushed direct to `main` |
| GitHub | Cross-linked #470↔#497; filed #503 (PDD feasibility research); issue-review #503 (15/15 READY) |

## Open threads

- Lesson 1 (cache-key invalidation) recurs across the codebase (#401, now #478) but isn't a written rule — a candidate RULES.md line, not yet filed.
- #503 (PDD/`@todo`-puzzle feasibility) is filed and READY but unclaimed.

## Related artifacts

- [Prior session TIL](./today-i-learned-2026-07-03-elderberry.md) — the profiles/keybindings lane start (#439/#447/#455/#440/#471)
- [[today-i-learned-2026-07-01-cherry]] — #401 memo-cache-stale precedent
- Issues #463, #478, #497, #503, #510

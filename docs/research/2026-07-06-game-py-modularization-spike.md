# Spike: can `game.py`'s display/input shell + orchestration be modularized? — map + feasibility (#687)

**Role:** RESEARCH (spike) · read-only, no production code. **Drives:** the #280 shell-boundary decision.
**Method:** grounded read of `pycats/game.py` and its collaborators (`input_poll`, `display`,
`screen_render`, `screen_manager`, `options_menu`) + the existing tests that pin the current
boundary. Reconciled with #257 (hexagonal lens, `docs/research/architecture-review-2026-06b.md`)
and decision #9 (input port).

**Bottom line:** the shell is smaller and cleaner than #280 assumed — rendering, input polling, and
display math are *already* extracted. What remains is a **cohesive** display/window-state cluster plus
the module-level loop. Both are extractable at moderate churn with a large testability payoff.
Recommendation for #280: **option (b) — extract a testable shell-object**, sequenced in two load-bearing
slices, with a cheap `__name__`-guard first step available if a minimal move is preferred.

---

## 1. Map — what `game.py` actually owns today

`game.py` is 391 lines. Much of what #280's premise attributed to it has already moved out:

| Concern | Where it lives now | In `game.py`? |
|---|---|---|
| Entity draw (fighter/eye/HUD) | `render_battle.py` (#69) | no |
| Per-state render dispatch | `screen_render.render_active_screen` (importable, tested by `test_game_render_dispatch`) | no — `game.py` only *calls* it |
| Input polling adapter | `input_poll.poll()` (present layer) | no — `game.py` only *calls* it |
| Input value-type port | `core/input.InputFrame` / `merge_frames` (pygame-free) | no |
| Zoom/scale/letterbox **math** | `display.py` (`achievable_zoom_scales`, `window_size_for`, `scale_surface`, `cycle_preset`, `Toast`, labels — pure) | no — `game.py` only *calls* these |

**What genuinely remains in `game.py` (the shell), in five clusters:**

- **S1 — import-time bootstrap.** `pygame.init()`, `set_caption`, `platforms`, `P1_KEYS`/`P2_KEYS`,
  `battle`, `settings.load()` + `runtime_settings.seed`, the Unicode-font pick, the initial
  fullscreen-vs-windowed display-mode branch. All executes **at module import**.
- **S2 — display/window STATE + mutators (the fullscreen/zoom cluster).** Module globals
  `screen, display_surface, game_surface, scale_factor, offset_x, offset_y, is_fullscreen,
  windowed_scale, fullscreen_scales, fullscreen_zoom_index, zoom_toast`, mutated together by
  `toggle_fullscreen`, `set_windowed_scale`, `enter_fullscreen_zoom`, `set_fullscreen_zoom_index`,
  `save_prefs`, `get_render_surface`, `present_frame`. This is the largest and most defect-prone piece.
- **S3 — display hooks.** `_opt_cycle_windowed_scale`, `_opt_toggle_fullscreen`, and the
  `_display_hooks` dict — closures over S2 handed to `ScreenStateManager` → `OptionsMenu` so the
  Options rows apply live (the only outward escape of S2's state).
- **S4 — the main loop.** `while running:` — `clock.tick`, `inp.poll`, raw event dispatch
  (`QUIT`/`F11`/`F10`/`K_e`/`K_SEMICOLON`), `screen_manager.update`, quit check,
  `render_active_screen`, `present_frame`; then `pygame.quit(); sys.exit()`.
- **S5 — the Unicode-font selection block** (small, part of S1 but separable).

## 2. Known-unknown, resolved

The spike flagged one unknown: *how coupled are S2's module-level fullscreen/zoom globals?*

**Resolved: they are a single cohesive cluster.** Every one of them describes one thing — how the
fixed 960×540 view maps onto the OS window (magnification + centring + which surface is the draw
target). They are mutated **only** by the S2 functions and the loop's F10/F11 branch, and they
escape `game.py` **only** through the four `_display_hooks` closures (S3) and the loop's
`present_frame`/`get_render_surface` calls (S4). No other module reads them. That is a clean seam.

The one real wrinkle is mechanical: the S2 mutators use `global`, which is exactly what blocks a naive
"wrap the loop in `main()`" — `global` rebinding is module-scoped. Lifting S2 into an object dissolves
the `global`s and is therefore the enabling move for everything else. **Net: high extraction feasibility.**

## 3. Candidate modules — feasibility (risk / churn / testability gain / coupling)

> The candidates below are seeds; the map above lets them be merged/split. Ordered by value.

### C1 — `DisplayManager` (a viewport/window adapter object) — *load-bearing*
Own S2 as instance state + methods; `_display_hooks` become bound methods; keeps consuming `display.py`
(no math re-implemented). 
- **Testability gain: high.** Currently S2 is untestable (module globals + live window). As an object it
  is headless-unit-testable: toggle flips `is_fullscreen`, F10 zoom index wraps, `window_size_for` is
  selected correctly, `present_frame` picks the right blit path.
- **Coupling: severs** the S2/global tangle and the hook closures; **introduces** one plain object.
- **Risk: medium** — must preserve F10/F11 + Options-hook behavior. Guardable by the existing
  `settings`/`options_menu` tests plus a render-hash check on the `present_frame` path (screen-parity is
  FSM-trace, so a pixel check is warranted per the magic-number-audit precedent).
- **Churn: moderate** — one new class; rewire `game.py` + the hooks dict.

### C2 — `main()` + `if __name__ == "__main__"` guard — *the importability win*
Wrap S1 + S4 so importing `pycats.game` has no side effects.
- **Testability gain: high** — `game.py` becomes importable, so the loop *wiring* (event dispatch, quit
  check, the per-state branch selection) becomes coverable. This closes the **#386-class blindspot**
  (`test_game_render_dispatch` today can only cover the *extracted* dispatch, not the loop) and would let
  `test_game_no_star_import` relax from "must not import" to "imports cleanly."
- **Risk: LOW after C1, MEDIUM alone** — the `global` mutators (S2) are the blocker; once S2 is a
  `DisplayManager`, `main()` is a clean function with no `global`s.
- **Churn: low–moderate.**

### C3 — thin `App` / `GameShell` object — *the concrete "driving adapter" #280 names*
Owns `clock` + `DisplayManager` + `ScreenStateManager`; `run()` loops, `step(events, frame_input)` runs
one frame (an injectable seam).
- **Testability gain: high** — `step()` is unit-testable with a fake clock/poll; the whole edge becomes
  coverable without a live window.
- **Risk: low** — pure composition over C1/C2. **Churn: moderate.**

### C4 — event-dispatch handler (QUIT/F11/F10/E/;) — **fold into C3**
Small; naturally lands inside `App.step()`. Not worth a standalone module.

### C5 — Unicode-font-pick helper (S5) → `text_utils` — *optional, cosmetic*
Trivial move; minor tidy. Low value, low risk.

**Sequencing:** C1 → C2 → (C3, absorbing C4) → C5 optional. C1 is the enabler; C2 delivers the single
biggest testability win; C3 is the capstone that makes the edge fully coverable.

## 4. Recommendation, mapped onto #280's three options

| #280 option | Verdict | Why |
|---|---|---|
| **(a) keep shell in `game.py`** | Not recommended (but see minimal step) | Perpetuates the untestable module-level loop (the #386 blindspot) and the S2 global tangle. *Minimal step:* C2's `__name__` guard alone captures the importability win cheaply if a full extraction is deferred. |
| **(b) extract a testable shell-object** | **Recommended** | C1 (`DisplayManager`) + C2 (`main()`+guard) + C3 (`App`/`GameShell`). Two plain objects, no new framework; dissolves the globals, makes the edge importable and unit-testable. Moderate churn, high payoff. |
| **(c) full ports & adapters (display+input)** | Not recommended now | Formal display/input *ports* (protocols + adapters) are ceremony for a single, permanent pygame backend (YAGNI). The part of (c) that pays off — the input value-type split — is already tracked as **decision #9 / #257-H3**, independent of the shell. Revisit only if a second display/input backend ever appears. |

**Recommended ruling for #280: option (b), sequenced C1 → C2 → C3**, with **C1 as the first slice**
(it unlocks the rest). If the decision prefers a minimal move, ship **C2's `__name__` guard first** for
the immediate importability/coverage win, then decide on C1/C3.

## 5. Reconciliation with #257 and decision #9

The shell work is **orthogonal** to #257's open findings — no collision:
- **#257-H1** (rendering port half-built: `Attack`/`Platform`/`Tail` still self-draw) is entity-rendering,
  which `game.py` doesn't own. `DisplayManager` touches surfaces/scaling, not entity draw.
- **#257-H3 / decision #9** (split `core/input.py` into a pure port + a `poll()` adapter) is the input
  value-type layer. `input_poll` is *already* the adapter `game.py` calls; the shell doesn't need #9 to
  land and won't conflict with it. `DisplayManager`/`App` consume input the same way `game.py` does today.

`DisplayManager` must **consume `display.py`** (already pure) rather than re-implement any math.

## 6. Downstream DEV tickets (named, NOT filed — file one at a time *after* #280 rules)

- **DEV-1:** Extract `DisplayManager` (S2 → object; `_display_hooks` → bound methods; render-hash guard on `present_frame`). *(C1)*
- **DEV-2:** Add `main()` + `if __name__ == "__main__"` guard; make `pycats.game` importable; relax `test_game_no_star_import`; add loop-wiring coverage. *(C2)*
- **DEV-3 (optional):** `App`/`GameShell` with a `step()` seam + unit tests for the frame wiring. *(C3+C4)*
- **DEV-4 (optional):** move the Unicode-font pick into `text_utils`. *(C5)*

All are behavior-neutral refactors; each ships with the suite green + a before/after render-hash where it
touches the present path.

## 7. Answering the spike's questions

1. **Can it be modularized?** Yes. The shell is already thin; the remaining S2 cluster is cohesive and the
   loop is a standard extract-to-`main()`. No blocker beyond the `global` mutators, which C1 removes.
2. **Feasibility?** C1 medium-risk/moderate-churn/high-payoff; C2 low-risk after C1; C3 low-risk capstone.
3. **Recommendation?** #280 option (b), C1→C2→C3, C1 first; `__name__`-guard as the cheap minimal step.

**Out of scope (unchanged):** making the ruling (that is #280's); any production code; re-doing #257's
rendering/input-port review.

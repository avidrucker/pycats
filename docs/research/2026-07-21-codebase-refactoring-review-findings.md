# Codebase refactoring review — accretion cleanup (findings)

> **Ticket owner:** #834 (RESEARCH child of the refactoring epic **#833**).
> Its purpose is to **capture a whole-repo code review** as the durable basis for the epic's
> decomposition — one child ticket per "Suggested order" item below.
> **Compiled:** 2026-07-21. **Scope:** structure/organization only — no behavior change is proposed.
> **Relation:** complements the earlier [`2026-07-06-code-quality-audit-628.md`](./2026-07-06-code-quality-audit-628.md)
> (that one graded process/quality; this one proposes a concrete line-reducing refactor order).
>
> **Provenance / caveat.** This is a review of the repo tree as of the review session; the
> line-number spans quoted below (e.g. `Player.update` "~lines 290–594") are **as-of the review**
> and will drift — each downstream child ticket must re-anchor on the named function/class before
> editing. The estimates ("600–900 lines removed") are the reviewer's, unverified. Nothing here is
> a game-mechanic or value claim, so no PM/primary sourcing applies.
>
> **One-line summary:** the codebase is well-run but accreted — ~18k source lines against ~24k test
> lines — and the highest-value wins are collapsing near-verbatim duplication (menus, tests) and
> splitting three god-files (`render_battle.py`, `text_utils.py`, `Player.update`) into packages,
> all verifiable against the existing suite with no behavior change.

---

## Overall

This is a genuinely well-run codebase — clean ruff pass, 226 test files, ADRs, provenance registries, a Makefile SSOT, pre-commit. The problems are not sloppiness; they're **accretion**. 18k lines of source against 24k lines of tests, with the process discipline itself now generating volume. The wins below are mostly about collapsing repetition rather than fixing bugs.

---

## 1. The biggest structural win: menus are copy-paste siblings

`MainMenuManager` and `PauseMenuManager` are the same class. Identical `__init__` shape, identical `reset`, identical `get_action`, and an `update` that differs only in the options list and the select-key check. `OptionsMenu`, `keybind_menu`, `keybind_sets_menu`, and `win_screen` repeat the same cooldown/pulse/wrap-around navigation logic again.

Extract a `MenuController` base:

```python
class MenuController:
    def __init__(self, p1_controls, p2_controls, options):
        self.p1_controls, self.p2_controls = p1_controls, p2_controls
        self.options = options
        self.selected_option = 0
        self.input_cooldown = 0
        self.press_pulse = 0
        self.action_requested = None

    def reset(self): ...
    def update(self, pressed_keys): ...   # nav + select, calls self.on_select(index)
    def get_action(self): ...
```

Subclasses supply `options` and an `on_select`. `main_menu.py` and `pause_menu.py` drop to ~40 lines each (mostly `render`). Note also that `pause_menu` hardcodes `pygame.K_SLASH`/`pygame.K_v` for select while `main_menu` correctly reads `p1_controls["attack"]` — that's a live rebinding bug the dedup would fix by construction.

Similarly, the "draw title, draw button column, draw instruction lines, draw F11 hint" render sequence is repeated across five screens. `menu_widgets.py` is only 87 lines; push a `draw_menu_screen(surface, title, options, selected, pulse, hints)` helper into it and the render methods become one call plus screen-specific extras. **Estimated: 600–900 lines removed.**

---

## 2. `render_battle.py` (1439 lines) should be a package

It currently holds cat anatomy drawing, tint/cache logic, timer-bar spec computation, grab-dot logic, hitbox debug overlay, HUD, controls display, input history, and shell chrome. Split into `pycats/render/`:

- `body.py` — `draw_cat_features`, `draw_stripes`, `_cat_body_surface`, the cache
- `tint.py` — `active_tint`, `_blend`, `tinted`, `body_tint`
- `status.py` — `TimerBar`, `StatusSource`, `timer_bar_specs`, `draw_timer_bars`, `grabs_left_dots`
- `hud.py` — `hud_rows`, `draw_hud`, `draw_controls`, `draw_input_history`, `draw_shell_chrome`
- `debug.py` — `render_hitbox_overlay`
- `__init__.py` re-exports `render_battle` so imports don't churn

Note `timer_bar_specs` and `grabs_left_dots` are pure functions returning data — they're *model* logic living in the render module. Moving those to `pycats/systems/` would let you test them without touching pygame at all.

---

## 3. `text_utils.py`: a 739-line class with 3 module functions

`TextRenderer` spans lines 16–663. That's almost certainly font caching + unicode fallback + kaomoji handling + layout all in one. Split font-loading/caching from text-shaping/rendering. Also `run_font_diagnostics` and `quick_unicode_test` are dev tools — move them to `scripts/` so they aren't imported into the game process.

---

## 4. `Player.update()` is ~300 lines (lines 290–594)

You already have `fighter_input.py`, `fighter_physics.py`, and `systems/movement.py` — the decomposition pattern exists, it just hasn't been applied here. Break `update` into an explicit phase sequence:

```python
def update(self, input_frame, platforms, attack_group, ledges=()):
    self._tick_timers()
    intent = read_intent(self, input_frame)
    apply_movement(self, intent, platforms)
    apply_actions(self, intent, attack_group, ledges)
    self._apply_posture_geometry()
    self._resolve_collisions(platforms, ledges)
```

Each phase testable alone. This is the single highest-value refactor for "nicer to work in" — right now any combat change means reading 300 lines to find the right insertion point.

---

## 5. The `Fighter` / `Player` split is unclear

`Fighter` (675 lines) has state, timers, `receive_hit`, KO, respawn. `Player` (641 lines) subclasses `pygame.sprite.Sprite` and has input handling, movement, and *also* `reset_to_spawn` — which `Fighter` also defines. Two classes, ~1300 lines, overlapping responsibilities, and it isn't obvious from the outside which one owns what.

Worth writing down the contract explicitly (Fighter = pygame-free simulation state; Player = pygame binding + input), then enforcing it. You already have `test_core_pygame_boundary.py` — extend that guard to `entities/fighter.py`. Right now `fighter.py` imports pygame, so the boundary is already leaking.

---

## 6. The pygame boundary is leaking broadly

28 of ~95 source modules import pygame, including `core/physics.py`, `systems/movement.py`, `entities/fighter.py`, and `combat`-adjacent code. Usually this is just for `pygame.Rect` or key constants.

Two moves:
- Replace `pygame.Rect` in simulation code with a small frozen dataclass (or use it only at the render boundary). Rect's mutable in-place semantics are a recurring source of aliasing bugs anyway.
- Move key constants behind `core/keymap.py` so nothing in `systems/`, `combat/`, or `entities/` names `pygame.K_*` directly.

Then extend `test_core_pygame_boundary.py` to assert that `pycats.combat`, `pycats.systems`, and `pycats.core` import cleanly with pygame absent from `sys.modules`. That converts an aspiration into a gate.

---

## 7. `config.py`: 179 constants in one flat namespace

89 test files import from it directly, which means every constant is effectively public API and renaming anything is a 90-file change. Split it into a package with the same import surface:

```
pycats/config/__init__.py   # re-exports everything, nothing breaks
pycats/config/physics.py
pycats/config/render.py
pycats/config/menu.py
pycats/config/screen.py
```

Zero-churn migration, and the render/menu constants stop competing for attention with tuning values. Also: the five `#### TODO:` lines at the top of `config.py` (unique attacks, cooldowns, dodging, weight classes, combos) are stale — dodging and per-character data clearly exist now. Those belong in GitHub issues, not a header comment.

---

## 8. Test suite: 24k lines, and much of it is boilerplate

Your `conftest.py` is 9 lines. Meanwhile 69 test files construct a `Player` by hand, and many redefine the same `P1 = dict(left=pygame.K_a, ...)` control map and `_mk_player()` / `_ground()` helpers.

Push these into `conftest.py` as fixtures:

```python
@pytest.fixture
def p1_controls(): ...

@pytest.fixture
def player(p1_controls): ...

@pytest.fixture
def ground(): ...

@pytest.fixture
def two_fighters(): ...
```

Also add a `tests/helpers.py` for `advance(player, frames)`, `land_hit(a, b, move)`, and golden-comparison utilities. **Realistically 2000–4000 lines of test code disappear**, and new tests get shorter to write — which is the compounding benefit.

Two further test observations:
- 226 test files for ~95 source modules suggests one-file-per-issue rather than one-file-per-unit. Files like `test_hurt_tint_clears_when_moving_or_attacking.py`, `test_name_label_clears_ears.py`, and `test_jump_over_flush_adjacent.py` are single-behavior files. Consolidating by subject (`test_render_fighter.py`, `test_ledge.py`, `test_menus.py`) would cut file count roughly in half with no loss of coverage, and make it far easier to find where a behavior is tested.
- 51 files touch pygame init/SDL env despite `conftest.py` already handling it. That's removable duplication.

---

## 9. Comment density

Comments frequently exceed the code they describe, and nearly every one carries an issue number. Example from `main_menu.py`: a four-line comment block explaining a single `draw_menu_button` loop, citing #359/#360/#346/#402.

The issue references are genuinely valuable — but they belong in git blame and the ADRs, which you already maintain. Consider a rule: issue-number rationale goes in the commit message and the ADR; inline comments explain *why the code is non-obvious*, and nothing else. This is a large, low-risk line reduction across the whole codebase, and it makes the comments that remain actually load-bearing.

---

## 10. Smaller items

- **`sim/controllers.py` (891 lines)** — `AttackerController.decide` runs lines 542–826. Same treatment as `Player.update`: split into `_decide_recovery` / `_decide_edge_guard` / `_decide_approach` / `_decide_attack`, dispatched by a priority list. The 15 private helpers above it suggest the decomposition is half-done already.
- **`char_select.py` (768 lines)** and **`options_menu.py` (668 lines)** — both mix state machine, layout math, and rendering. Extract layout to `menu_layout.py` (currently only 37 lines and underused).
- **`win_screen.py` (538 lines)** — surprisingly large for one screen; likely absorbing stats-table rendering that belongs with `stats_print.py` or `charts/`.
- **Root scripts** — `bench.py`, `bench_render.py`, `watch.py`, `parity_report.py` sit at repo root. Move to `scripts/` (which already exists) or `pycats/tools/`.
- **`state_engine.py` / `state_engine_sc.py`** — the `_sc` suffix is opaque. Rename to something self-describing.
- **`RULES.md` at 603 lines** plus `JUDGEMENT_CALLS.md` at 223 and `CLAUDE.md` at 95 — 900 lines of process doc against 228 files in `docs/`. Worth auditing for rules that are now enforced by ruff/tests and can therefore be deleted rather than restated.

---

## Suggested order

1. Menu dedup (biggest ratio of lines removed to risk taken)
2. Test fixtures in `conftest.py` (makes every subsequent refactor cheaper to verify)
3. Split `render_battle.py` into a package
4. Decompose `Player.update` and `AttackerController.decide`
5. `config.py` → package
6. Tighten and enforce the pygame boundary
7. Comment-density pass and test-file consolidation

Steps 1–3 alone should take you from ~18k to roughly ~15k source lines with no behavior change, and every one of them is verifiable against your existing suite.

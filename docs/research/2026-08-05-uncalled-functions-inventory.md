# Uncalled-functions inventory (unused code) — 2026-08-05

**Ticket:** #1232 (RESEARCH) · **area:** cross-cutting · produces findings only (no code edits).

## Bottom line

The codebase is close to clean. Of **673** `def`s in `pycats/`, only **6** are real
**unused code** — defined, no caller, no dynamic reach, no entry point — and every one is a
thin superseded wrapper or a dev-diagnostic helper, not lost behaviour. **1** more is a
public-API method with no current production caller (a keep-or-drop call for a human). The
other **36** symbols that a naive "no direct call site" scan flags are all **false positives**:
FSM dispatch callbacks, an injected default-arg seam, dataclass hooks, the callable protocol,
and `@property` setters — every one reached by a path a call-graph doesn't see.

Notable correction: **#1226's seed example is stale.** #1226 named
`combat/charge.py::charge_multiplier` as an orphan-by-design ("defined, zero call sites,
smash-charge scaling not yet wired into `receive_hit`"). The real function is named
**`charge_factor`**, and the whole charge chain (`charge_factor` → `scale_hitboxes` →
`angle_smash_hitboxes`) **is wired** — called from `entities/player.py` at spawn and covered
by four test modules. There is **no orphan-by-design symbol** in the current tree.

## Method

Two home-grown AST passes over `pycats/` + `tests/` (scripts in the ticket's scratch, not
committed). **`vulture` was not used** — it is not an installed dependency and installing one
needs human approval (RULES.md → Dependencies); the AST passes cover the same ground with a
known false-positive profile.

- **Pass A — "never referenced at all":** flag any `def` whose bare name never appears as a
  Name-load, an `.attr` access, a string literal, a decorator, or an `__all__` export anywhere
  in either tree. Strongest dead-code signal; **12 hits** (6 non-dunder, 6 dunder).
  *Conservative:* any reference (even an import) counts as use, so it under-reports — it cannot
  see a symbol that is imported/referenced but never invoked.
- **Pass B — "zero call sites":** flag any non-dunder, non-`@property` `def` whose name never
  appears in a **call** position (`name(...)` or `.name(...)`), and print its non-call reference
  count. Catches the imported-but-never-invoked case Pass A misses; **37 hits**. *Noisier:* a
  callback passed by bare name, an injected default-arg, and a `@property` **setter** all have
  zero call sites yet are live — so each hit is hand-classified below.

The union, hand-resolved, is **43 candidate symbols**. Classification, not the raw list, is the
deliverable — a "no caller" result is never a delete verdict on its own.

## Summary counts

| Classification | Count | Verdict |
|---|---:|---|
| **unused** — no caller, no reach, no entry point | 6 | safe-to-remove (shortlist below) |
| **needs-a-decision** — public API, zero production caller | 1 | human call |
| false-positive: **dynamic** (FSM dispatch / hook dict / injected seam) | 27 | keep |
| false-positive: **framework/dunder** (dataclass hook, callable, setter) | 9 | keep |
| false-positive: **public/exported API** | 0 | — |
| orphan-by-design | 0 | (#1226's example is wired — see above) |
| **Total examined** | 43 | |

## Unused — the safe-to-remove shortlist (6)

Each is uncalled anywhere in `pycats/` + `tests/`, reached by no dynamic path, and behind no
entry point. All are leftovers of a superseded design or manual dev tooling — removing them
changes no behaviour. (Removal is out of scope here; it is a follow-up cleanup ticket, one
verdict at a time.)

| Landmark | Evidence | Verdict |
|---|---|---|
| `screens/char_select.py::CharacterSelector.can_start_game` | One-line wrapper returning `self.both_confirmed()`; zero references. `both_confirmed()` is the method actually called. | safe-to-remove |
| `shell/screen_manager.py::ScreenStateManager.set_stats_data` | Delegates to `win_screen_manager.set_match_data(..., from_pause=True)`; zero callers. The pause→stats flow now runs through the FSM guard `_guard_pause_to_stats` + `_on_enter_win_screen`. | safe-to-remove |
| `shell/screen_manager.py::ScreenStateManager.should_reset_game` | Zero callers; two in-repo mentions are **comments** ("replacing game.py's `should_reset_game` poll"). Superseded by the engine action `_update_char_select`. | safe-to-remove |
| `shell/screen_manager.py::ScreenStateManager.esc_quit_progress` | Redundant getter returning `self._esc_hold.progress`; the live render path (`render_esc_quit_progress`, called from `render`) reads `_esc_hold.progress` directly. A test comment calls it "the old `esc_quit_progress()`". | safe-to-remove |
| `ui/text_utils.py::run_font_diagnostics` | Module-level dev diagnostic; zero callers, no `__main__` block in `text_utils.py`, no entry point. | safe-to-remove |
| `ui/text_utils.py::quick_unicode_test` | Same — a manual dev-diagnostic helper, zero callers, no entry point. | safe-to-remove |

## Needs-a-decision (1)

| Landmark | Evidence | Verdict |
|---|---|---|
| `ui/text_utils.py::TextRenderer.render_unicode_char` | Public `TextRenderer` render method; **zero production call sites**. Tests reach it by string via `getattr`/`setattr` in the font-scale spy (`_RENDER_METHODS` tuple, `test_menu_font_scale_render.py`) and monkeypatch it in `test_main_menu_title.py`, but the spy *wraps* it — nothing invokes it during the suite. Its three siblings (`render_text_simple`/`render_text_mixed`/`render_mixed_centered`) **are** drawn through. Keep for API completeness, or drop it — a human call, because "the menus no longer draw any unicode char through it" is a product question, not a mechanical one. | keep-with-reason / decision |

## False positives — why the scan flagged them

**Dynamic (27) — reached through a table or an injected seam, never a literal call:**

- `shell/screen_manager.py` — **24** FSM handlers registered by reference into the
  `transitions` / `on_enter` / `on_update` dicts passed to `make_screen_engine`, then invoked
  through the engine: the 6 `_on_enter_*`, 6 `_update_*`, and 12 `_guard_*_to_*` methods. Each
  shows exactly one non-call reference — its single registration.
- `shell/app.py::App._opt_cycle_windowed_scale`, `App._opt_toggle_fullscreen` — registered in
  the `self._display_hooks` dict (`"cycle_windowed_scale": self._opt_cycle_windowed_scale`, …)
  and called by the options menu through that dict.
- `shell/input_poll.py::poll` — the real event poll, injected as a **default argument**
  (`App.__init__(self, prefs, poll=inp.poll, …)`), stored as `self._poll`, and called via
  `self._poll(...)`. The call site's name is `_poll`, so a name-keyed scan never links it.

**Framework/dunder (9) — the runtime calls them implicitly:**

- `combat/data.py` `Hitbox`/`VelocityPhase`/`LandingSpawn`/`MoveData`.`__post_init__` and
  `core/geometry.py::FrozenRect.__post_init__` — dataclass hooks run after `__init__`.
- `sim/controllers.py::BaseController.__call__` — the callable protocol (`controller(...)`).
- `entities/fighter.py` `Fighter.percent` / `shield_hp` / `lives` **setters** — invoked via
  attribute assignment (`fighter.percent = x`) through the descriptor protocol. (Pass B flags a
  `@x.setter` as a plain method because its decorator is `x.setter`, not `property`; this is the
  scan's one systematic blind spot, called out here so a reader doesn't chase it.)

## Scan false-positive profile (for the next run)

If this sweep is repeated: the name-keyed passes cannot see (a) callbacks dispatched through a
dict/registry, (b) a callable injected under a different parameter name, (c) `@property`
setters, (d) dataclass/protocol dunders. All four are enumerated above, so a future scan can
subtract them. Nothing here needs `vulture`; the two AST passes plus hand-classification were
sufficient at this repo size (673 defs).

## Refs

#1226 (inline-formulae inventory — named the now-stale `charge_multiplier` orphan; the wired
function is `charge_factor`) · RULES.md → Dependencies (`vulture` would need approval; not used)
· `combat/charge.py`, `shell/screen_manager.py`, `ui/text_utils.py` (the candidate homes).

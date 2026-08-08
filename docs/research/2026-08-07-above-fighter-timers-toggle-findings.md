# Above-fighter timers/displays toggle — menu control + test coverage

> **Agent:** APPLE · **Authored:** 2026-08-07 · **Ticket:** #1303

Source pinned at `cb8da66`.

## Question

Does a menu button exist to toggle the above-fighter timers/displays (the overlays
drawn above each fighter)? What does it toggle, what is its default, and is the toggle
tested?

## Answer (short)

**Yes — two toggles, both in the Options sub-menu** (`OptionsMenu`,
`pycats/screens/options_menu.py`; reached Main Menu → Options):

| Row label | Row key | Getter | Default | What it gates |
|---|---|---|---|---|
| **Status Bars** | `status_bars` | `runtime_settings.show_status_timer_bars()` | **ON** | The above-head **timer bars** *and* the **grabs-left dots** |
| **Movement Status** | `movement_status` | `runtime_settings.show_movement_status()` | **OFF** | A **HUD row** (`Movement: <State>`) — *not* an above-fighter overlay, despite its caption |

Both are covered by tests (menu-toggle flip+persist *and* the render gate). Coverage is
present and strong, **not** thin. One loose thread: the Movement Status caption claims
the state renders "above" the fighter, but the code renders it in the top HUD — a
wording/placement mismatch with no test guarding it (see *Loose thread*).

## The Status Bars toggle (the true above-fighter timers)

- **Control:** the `status_bars` row of `OptionsMenu`. `OptionsMenu._activate`
  (`pycats/screens/options_menu.py`) flips `show_status_timer_bars` live via
  `runtime_settings.set(...)` and persists it with `settings.save(...)`;
  `OptionsMenu._row_label` renders `"Status Bars: ON/OFF"`.
- **Default:** **ON** — `settings._DEFAULTS["show_status_timer_bars"] = True`
  (`pycats/storage/settings.py`).
- **What it toggles (two above-head overlays, one shared gate):**
  - **Timer bars** — the stacked shield/stun/hang/prone/lockout/intangibility bars drawn
    above a fighter's head. Drawer `render.status.draw_timer_bars`
    (`pycats/render/status.py`); shapes come from `systems.status_model.timer_bar_specs`,
    called at `render.battle.render_battle` (`pycats/render/battle.py`). The gate lives in
    the pure model: `timer_bar_specs` returns `[]` when the toggle is off, so the drawer
    paints nothing.
  - **Grabs-left dots (#657)** — the above-head ledge-regrab budget dots. Drawer
    `render.status.draw_grabs_left_dots`; count from `systems.status_model.grabs_left_dots`,
    which also `return 0` when `show_status_timer_bars()` is off. So one menu row gates
    both overlays.
- **Not gated by this toggle:** the **dizzy-star halo** (`render.status.draw_dizzy_stars`)
  is above-fighter but has **no** toggle — it draws whenever `stun_timer > 0`.

## The Movement Status toggle (labeled "above", renders in the HUD)

- **Control:** the `movement_status` row of `OptionsMenu`; same flip-live-and-persist path
  as Status Bars. Label renders `"Movement Status: ON/OFF"`.
- **Default:** **OFF** — `settings._DEFAULTS["show_movement_status"] = False`.
- **What it toggles:** a top-of-screen **HUD row** `Movement: <State>` appended under
  `Shield HP:` in `render.hud.hud_rows` (`pycats/render/hud.py`), gated by
  `show_movement_status()`. `hud_line_count` adjusts the row count for the same flag. This
  is a HUD line, **not** an overlay above the fighter's head.

## Test coverage — present, not thin

**Status Bars**
- Menu toggle: `tests/test_options_menu.py::test_status_bars_row_toggles_runtime_and_persists`
  — activating the row flips `runtime_settings` live and persists to disk.
- Render gate: `tests/test_status_timer_bar.py::test_toggle_off_suppresses_bar` and
  `::test_down_bar_suppressed_by_toggle` — `timer_bar_specs(...)` returns `[]` when the
  toggle is off.
- Grabs-left gate: exercised in `tests/test_grabs_left_dots.py` /
  `tests/test_ledge_invuln_bar.py` (both drive `show_status_timer_bars`).

**Movement Status** (`tests/test_movement_status.py`)
- Menu toggle: `::test_movement_status_row_toggles_runtime_and_persists` (live flip +
  persist); `::test_movement_status_row_present_and_described`;
  `::test_movement_status_row_label_reflects_state`.
- Defaults: `::test_show_movement_status_defaults_off`,
  `::test_runtime_movement_status_default_off`.
- Render gate: `::test_movement_row_absent_when_off`,
  `::test_movement_row_present_directly_under_shield_hp_when_on`,
  `::test_movement_row_capitalizes_each_state`.

Both toggles have a menu-activation test *and* a render-gate test. No regression test is
needed to fill a coverage gap for the toggles themselves.

## Loose thread (optional follow-up — not part of this research ticket)

The `movement_status` caption in `ROW_DESCRIPTIONS` (`pycats/screens/options_menu.py`)
reads *"Show each fighter's movement state (idle / walk / dash / run) **above it**."* — but
`render.hud.hud_rows` renders that state as a HUD row under `Shield HP:`, not above the
fighter's head. The wording implies an above-fighter overlay the code does not draw. No
test asserts caption↔render-location agreement. A future DEV ticket could either correct
the caption (e.g. "…in the HUD, under Shield HP") or move the render above the fighter to
match the caption — a product call, filed separately if desired.

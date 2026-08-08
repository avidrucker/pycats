"""Dev-HUD toggle (#1319, ruling C1–C4 on #1297) — the backtick/tilde master switch.

The in-battle HUD is redesigned around one runtime-only ``dev_hud`` toggle:

- OFF (the shipping default at every launch): a MINIMAL HUD — the player-name label
  plus the emphasized bottom-corner Lives / Damage % only. No jumps / Shield HP / FSM /
  Movement rows, no FPS, no raw input string, no input-history grid.
- ON: the COMPLETE dev HUD — the full secondary stat rows PLUS FPS + raw input + the
  input-history grid.

``dev_hud`` is the SOLE battle-HUD driver: ON shows the whole dev HUD regardless of the
legacy per-item flags (``show_dev_info`` / ``show_movement_status`` / ``show_input_history``);
OFF hides all of it. Those flags keep their Options rows this slice (re-homing to the F1
screen is #1311 slice 5) — they simply no longer affect the battle HUD.

The toggle is runtime-only + not persisted (survives a pause/resume — nothing on the
pause path resets it), and available to everyone (not ``dev_mode``-gated). The backtick
key wiring lives in ``tests/test_app_step.py``; the shell-chrome (FPS / raw input)
gating lives in ``tests/test_shell_chrome.py``.
"""

import types

import pygame  # noqa: E402

from pycats.render_battle import (  # noqa: E402
    HUD_FULL_LINE_COUNT,
    HUD_MINIMAL_LINE_COUNT,
    hud_emphasis_rows,
    hud_line_count,
    hud_rows,
)
from pycats.screens.pause_menu import PauseMenuManager  # noqa: E402
from pycats.storage import runtime_settings, settings  # noqa: E402


# --------------------------------------------------------------------------- #
# runtime_settings.py — the dev_hud accessor / setter / toggle
# --------------------------------------------------------------------------- #
def test_dev_hud_defaults_off():
    """Default OFF at boot — the shipping/default battle HUD is minimal."""
    assert runtime_settings.dev_hud() is False


def test_set_dev_hud_coerces_bool():
    runtime_settings.set_dev_hud(1)
    assert runtime_settings.dev_hud() is True
    runtime_settings.set_dev_hud(0)
    assert runtime_settings.dev_hud() is False


def test_toggle_dev_hud_flips_and_returns_new_state():
    assert runtime_settings.dev_hud() is False
    assert runtime_settings.toggle_dev_hud() is True
    assert runtime_settings.dev_hud() is True
    assert runtime_settings.toggle_dev_hud() is False
    assert runtime_settings.dev_hud() is False


def test_dev_hud_is_not_persisted_seed_does_not_reset_it():
    """dev_hud is a runtime-only module global NOT in _state, so re-seeding the live
    settings must NOT clear it. This is what "survives pause" rests on: the pause path
    never re-seeds, and even if it did the toggle would stand. Able-to-fail: move
    dev_hud into _state and seed() would reset it to the persisted default (False)."""
    runtime_settings.set_dev_hud(True)
    runtime_settings.seed(settings.defaults())  # what a fresh-prefs reload would do
    assert runtime_settings.dev_hud() is True


# --------------------------------------------------------------------------- #
# render.hud — dev_hud drives the secondary rows + line count
# --------------------------------------------------------------------------- #
def _fake_player(state="run", jumps=2, shield_hp=50, shield_attempting=False, lives=3, percent=42):
    return types.SimpleNamespace(
        state=state,
        fighter=types.SimpleNamespace(
            jumps_remaining=jumps,
            shield_hp=shield_hp,
            shield_attempting=shield_attempting,
            lives=lives,
            percent=percent,
        ),
    )


def test_dev_hud_off_collapses_secondary_rows_to_label_only():
    runtime_settings.set_dev_hud(False)
    rows = hud_rows("P1", _fake_player())
    assert rows == ["P1"]  # only the player-name label
    assert hud_line_count() == HUD_MINIMAL_LINE_COUNT


def test_dev_hud_on_renders_the_complete_secondary_group():
    runtime_settings.set_dev_hud(True)
    rows = hud_rows("P1", _fake_player(state="run"))
    assert rows[0] == "P1"
    assert any(r.startswith("FSM:") for r in rows)
    assert any("jump" in r for r in rows)
    assert any(r.startswith("Shield HP:") for r in rows)
    assert "Movement: Run" in rows
    assert any(r.startswith("Shield Attempting:") for r in rows)
    assert hud_line_count() == HUD_FULL_LINE_COUNT
    assert len(rows) == HUD_FULL_LINE_COUNT


def test_movement_row_directly_under_shield_hp_when_on():
    runtime_settings.set_dev_hud(True)
    rows = hud_rows("P1", _fake_player(state="dash"))
    shield_i = next(i for i, r in enumerate(rows) if r.startswith("Shield HP:"))
    move_i = next(i for i, r in enumerate(rows) if r.startswith("Movement:"))
    assert move_i == shield_i + 1


def test_emphasis_lives_and_damage_present_regardless_of_dev_hud():
    """Lives / Damage % are the emphasized corner rows — the essentials that stay in
    both the minimal (OFF) and full (ON) HUD."""
    for on in (False, True):
        runtime_settings.set_dev_hud(on)
        joined = "\n".join(hud_emphasis_rows(_fake_player(lives=3, percent=42)))
        assert "Lives:" in joined and "Damage:" in joined


# --------------------------------------------------------------------------- #
# dev_hud is the SOLE battle-HUD driver — it supersedes the legacy per-item flags
# --------------------------------------------------------------------------- #
def test_dev_hud_on_shows_full_hud_even_with_legacy_flags_off():
    """ON shows the COMPLETE dev HUD regardless of the legacy flags being off."""
    runtime_settings.set("show_dev_info", False)
    runtime_settings.set("show_movement_status", False)
    runtime_settings.set_dev_hud(True)
    rows = hud_rows("P1", _fake_player())
    assert any(r.startswith("FSM:") for r in rows)  # dev-info row present despite flag off
    assert any(r.startswith("Movement:") for r in rows)  # movement row present despite flag off
    assert len(rows) == HUD_FULL_LINE_COUNT


def test_dev_hud_off_hides_full_hud_even_with_legacy_flags_on():
    """OFF hides all of it regardless of the legacy flags being on."""
    runtime_settings.set("show_dev_info", True)
    runtime_settings.set("show_movement_status", True)
    runtime_settings.set_dev_hud(False)
    assert hud_rows("P1", _fake_player()) == ["P1"]
    assert hud_line_count() == HUD_MINIMAL_LINE_COUNT


# --------------------------------------------------------------------------- #
# pause_menu.py — the "Minimal HUD" row is removed; the rest are unchanged
# --------------------------------------------------------------------------- #
DEFAULT_P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v}
DEFAULT_P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH}


def test_pause_menu_has_no_minimal_hud_row():
    m = PauseMenuManager(DEFAULT_P1, DEFAULT_P2)
    assert m.options == ["Resume", "End Match", "Return to Character Select"]
    assert not any("Minimal HUD" in o for o in m.options)


def test_pause_menu_rows_map_to_actions():
    m = PauseMenuManager(DEFAULT_P1, DEFAULT_P2)
    assert m.on_select(0) == "resume"
    assert m.on_select(1) == "end_match"
    assert m.on_select(2) == "return_to_char_select"
    assert m.on_select(3) is None  # out of range

"""Minimal-HUD mode (#977) — a pause-menu toggle that declutters the battle HUD.

When on, the per-player secondary rows (jumps / Shield HP / Movement / dev-info)
are dropped; only the player-name label plus the essential emphasized Lives /
Damage % corners remain. Instruction hints keep their own toggles. Persisted,
default OFF (full HUD), flipped from the in-battle pause menu (not Options).
"""

import json
import types

import pygame  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.pause_menu import PauseMenuManager  # noqa: E402
from pycats.render_battle import (  # noqa: E402
    HUD_MINIMAL_LINE_COUNT,
    hud_emphasis_rows,
    hud_line_count,
    hud_rows,
)


# --------------------------------------------------------------------------- #
# settings.py — persisted default-OFF toggle
# --------------------------------------------------------------------------- #
def test_minimal_hud_defaults_off(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    assert settings.defaults()["minimal_hud"] is False
    assert settings.load()["minimal_hud"] is False  # missing file


def test_minimal_hud_round_trips_and_coerces_bool(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"minimal_hud": True})
    assert settings.load()["minimal_hud"] is True
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"minimal_hud": 1}))
    assert settings.load()["minimal_hud"] is True  # coerced from 1


def test_old_settings_without_key_still_load(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"windowed_scale": 1.0}))  # pre-feature file
    assert settings.load()["minimal_hud"] is False  # merged over default


# --------------------------------------------------------------------------- #
# runtime_settings.py — live accessor
# --------------------------------------------------------------------------- #
def test_runtime_minimal_hud_default_off():
    runtime_settings.seed(settings.defaults())
    assert runtime_settings.minimal_hud() is False


def test_runtime_minimal_hud_set():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("minimal_hud", True)
    assert runtime_settings.minimal_hud() is True


# --------------------------------------------------------------------------- #
# render.hud — minimal mode strips secondary rows, keeps the essentials
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


def test_minimal_hud_secondary_rows_collapse_to_label_only():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_movement_status", True)  # even with extras on…
    runtime_settings.set("show_dev_info", True)
    runtime_settings.set("minimal_hud", True)  # …minimal wins
    rows = hud_rows("P1", _fake_player())
    assert rows == ["P1"]  # only the player-name label
    assert hud_line_count() == HUD_MINIMAL_LINE_COUNT


def test_minimal_hud_keeps_essential_lives_and_damage():
    """Lives / Damage % are the emphasized corner rows — essential, never dropped."""
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("minimal_hud", True)
    emphasis = hud_emphasis_rows(_fake_player(lives=3, percent=42))
    joined = "\n".join(emphasis)
    assert "Lives:" in joined and "Damage:" in joined


def test_full_hud_restored_when_off():
    runtime_settings.seed(settings.defaults())  # minimal off by default
    rows = hud_rows("P1", _fake_player())
    assert "P1" in rows
    assert any(r.startswith("Shield HP:") for r in rows)  # secondary rows present
    assert any("jump" in r for r in rows)


# --------------------------------------------------------------------------- #
# pause_menu.py — the toggle button flips minimal_hud in place, no transition
# --------------------------------------------------------------------------- #
DEFAULT_P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v}
DEFAULT_P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH}


def test_pause_menu_has_minimal_hud_toggle_row():
    m = PauseMenuManager(DEFAULT_P1, DEFAULT_P2)
    assert len(m.options) == 4  # Resume, Minimal HUD, End Match, Return
    assert m._hud_toggle_label() == "Minimal HUD: OFF"


def test_toggle_row_flips_minimal_hud_in_place_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    runtime_settings.seed(settings.defaults())
    m = PauseMenuManager(DEFAULT_P1, DEFAULT_P2)
    m.selected_option = 1  # the Minimal HUD toggle
    m.update({pygame.K_v})  # P1 attack = select

    assert runtime_settings.minimal_hud() is True  # live flip
    assert settings.load()["minimal_hud"] is True  # persisted
    assert m.get_action() is None  # no screen transition — stays paused
    assert m._hud_toggle_label() == "Minimal HUD: ON"  # label tracks state


def test_toggle_row_flips_back_off(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("minimal_hud", True)
    m = PauseMenuManager(DEFAULT_P1, DEFAULT_P2)
    assert m.on_select(1) is None
    assert runtime_settings.minimal_hud() is False

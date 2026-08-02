"""Movement-status HUD indicator (#977).

A render-only DEV tool: a persisted, default-OFF toggle (mirroring the #219
hitbox-overlay toggle) that adds a "Movement:" row to each fighter's HUD, directly
under "Shield HP:", showing the live Player.state (idle/walk/dash/run and every
other FSM state) so a human can confirm the dash→run transition on screen (#967
added sustained run but no distinct run animation). Off → the battle render is
byte-identical; the sim is untouched.
"""

import json
import types

import pygame  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.render_battle import hud_rows  # noqa: E402
from pycats.screens.options_menu import ROW_DESCRIPTIONS, OptionsMenu  # noqa: E402


# --------------------------------------------------------------------------- #
# settings.py — persisted default-OFF toggle (mirrors show_hitbox_overlay)
# --------------------------------------------------------------------------- #
def test_show_movement_status_defaults_off(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    assert settings.defaults()["show_movement_status"] is False
    assert settings.load()["show_movement_status"] is False  # missing file


def test_show_movement_status_round_trips_and_coerces_bool(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"show_movement_status": True})
    assert settings.load()["show_movement_status"] is True
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"show_movement_status": 1}))
    assert settings.load()["show_movement_status"] is True  # coerced from 1


# --------------------------------------------------------------------------- #
# runtime_settings.py — live accessor the render path honours
# --------------------------------------------------------------------------- #
def test_runtime_movement_status_default_off():
    runtime_settings.seed(settings.defaults())
    assert runtime_settings.show_movement_status() is False


def test_runtime_movement_status_set():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_movement_status", True)
    assert runtime_settings.show_movement_status() is True


# --------------------------------------------------------------------------- #
# options_menu.py — Options row toggles live + persists (mirrors hitbox_overlay)
# --------------------------------------------------------------------------- #
P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v, "special": pygame.K_c}
P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH, "special": pygame.K_PERIOD}
ATTACK = pygame.K_v


def test_movement_status_row_present_and_described():
    m = OptionsMenu(P1, P2)
    assert "movement_status" in m.rows
    assert "movement_status" in ROW_DESCRIPTIONS  # test_focused_row_caption enforces this too


def test_movement_status_row_toggles_runtime_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_movement_status", False)  # known starting state
    m = OptionsMenu(P1, P2)
    m.selected_option = m.rows.index("movement_status")
    m.update({ATTACK})
    assert runtime_settings.show_movement_status() is True  # live flip
    assert settings.load()["show_movement_status"] is True  # persisted


def test_movement_status_row_label_reflects_state():
    runtime_settings.seed(settings.defaults())
    m = OptionsMenu(P1, P2)
    runtime_settings.set("show_movement_status", False)
    assert m._row_label("movement_status") == "Movement Status: OFF"
    runtime_settings.set("show_movement_status", True)
    assert m._row_label("movement_status") == "Movement Status: ON"


# --------------------------------------------------------------------------- #
# render.hud.hud_rows — the "Movement:" row under "Shield HP:"
# --------------------------------------------------------------------------- #
def _fake_player(state="dash", jumps=2, shield_hp=50, shield_attempting=False):
    return types.SimpleNamespace(
        state=state,
        fighter=types.SimpleNamespace(jumps_remaining=jumps, shield_hp=shield_hp, shield_attempting=shield_attempting),
    )


def test_movement_row_absent_when_off():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_movement_status", False)
    rows = hud_rows("P1", _fake_player(state="dash"))
    assert not any(r.startswith("Movement:") for r in rows)


def test_movement_row_present_directly_under_shield_hp_when_on():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_movement_status", True)
    rows = hud_rows("P1", _fake_player(state="run"))
    assert "Movement: Run" in rows
    shield_i = next(i for i, r in enumerate(rows) if r.startswith("Shield HP:"))
    move_i = next(i for i, r in enumerate(rows) if r.startswith("Movement:"))
    assert move_i == shield_i + 1  # directly underneath Shield HP


def test_movement_row_capitalizes_each_state():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_movement_status", True)
    for st, want in (("idle", "Movement: Idle"), ("walk", "Movement: Walk"), ("dash", "Movement: Dash")):
        assert want in hud_rows("P1", _fake_player(state=st))

"""Movement-status HUD indicator (#977), now a dev-HUD row (#1319) with its legacy
per-item flag retired (#1328).

The "Movement:" row shows each fighter's live Player.state (idle/walk/dash/run and every
other FSM state) directly under "Shield HP:". Since #1319 the dev-HUD toggle (`dev_hud`)
is the SOLE battle-HUD driver, so the row renders iff `dev_hud` is ON. #1328 retired the
old `show_movement_status` persisted flag / accessor / Options row entirely — it had been
a battle no-op since #1319. `hud_rows` is the testable seam the render path iterates.
"""

import types

import pygame  # noqa: E402

from pycats.render_battle import hud_rows  # noqa: E402
from pycats.screens.options_menu import ROW_DESCRIPTIONS, OptionsMenu  # noqa: E402
from pycats.storage import runtime_settings, settings  # noqa: E402

P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v, "special": pygame.K_c}
P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH, "special": pygame.K_PERIOD}


# --------------------------------------------------------------------------- #
# #1328 — the legacy show_movement_status flag + Options row are retired.
# Able-to-fail: re-add the setting / accessor / row and each assertion below flips.
# --------------------------------------------------------------------------- #
def test_show_movement_status_setting_retired():
    assert "show_movement_status" not in settings.defaults()
    assert not hasattr(runtime_settings, "show_movement_status")


def test_movement_status_row_absent_from_options():
    m = OptionsMenu(P1, P2)
    assert "movement_status" not in m.rows
    assert "movement_status" not in ROW_DESCRIPTIONS


# --------------------------------------------------------------------------- #
# render.hud.hud_rows — the "Movement:" row under "Shield HP:", driven by dev_hud.
# --------------------------------------------------------------------------- #
def _fake_player(state="dash", jumps=2, shield_hp=50, shield_attempting=False):
    return types.SimpleNamespace(
        state=state,
        fighter=types.SimpleNamespace(jumps_remaining=jumps, shield_hp=shield_hp, shield_attempting=shield_attempting),
    )


def test_movement_row_absent_when_dev_hud_off():
    runtime_settings.set_dev_hud(False)
    rows = hud_rows("P1", _fake_player(state="dash"))
    assert not any(r.startswith("Movement:") for r in rows)


def test_movement_row_present_directly_under_shield_hp_when_dev_hud_on():
    runtime_settings.set_dev_hud(True)
    rows = hud_rows("P1", _fake_player(state="run"))
    assert "Movement: Run" in rows
    shield_i = next(i for i, r in enumerate(rows) if r.startswith("Shield HP:"))
    move_i = next(i for i, r in enumerate(rows) if r.startswith("Movement:"))
    assert move_i == shield_i + 1  # directly underneath Shield HP


def test_movement_row_capitalizes_each_state():
    runtime_settings.set_dev_hud(True)
    for st, want in (("idle", "Movement: Idle"), ("walk", "Movement: Walk"), ("dash", "Movement: Dash")):
        assert want in hud_rows("P1", _fake_player(state=st))

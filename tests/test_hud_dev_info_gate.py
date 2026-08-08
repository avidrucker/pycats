"""#1319 superseded #545: the implementation-jargon HUD rows (``FSM:`` /
``Shield Attempting:``) now render iff the dev-HUD toggle is ON, NOT the old
``show_dev_info`` flag — ``dev_hud`` is the sole battle-HUD driver. This file keeps
the #545 acceptance shape (real BattleScreen player, ``hud_rows`` as the seam) but
pins the new driver: the jargon rows follow ``dev_hud`` and are unaffected by
``show_dev_info``; the emphasized Damage / Lives stats stay in both modes.

``hud_rows`` is the testable seam ``draw_hud`` iterates — asserting on the row
strings avoids pixel-diffing while covering exactly the acceptance criteria.
"""

import pygame

from pycats.render_battle import (
    HUD_FULL_LINE_COUNT,
    HUD_MINIMAL_LINE_COUNT,
    hud_emphasis_rows,
    hud_line_count,
    hud_rows,
)
from pycats.screens.battle_screen import BattleScreen
from pycats.storage import runtime_settings

_P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)
_P2 = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_PERIOD,
    special=pygame.K_SLASH,
    shield=pygame.K_RSHIFT,
)

_DEV_SUBSTRINGS = ("FSM:", "Shield Attempting:")
_STAT_SUBSTRINGS = ("Damage:", "Lives:")  # the emphasized corner rows (#550)


def _player():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("tabby", "calico")
    return bs.player1


def test_dev_hud_off_omits_dev_jargon_but_keeps_emphasized_stats():
    """dev_hud OFF (the default): no FSM:/Shield Attempting: rows; the emphasized
    Damage / Lives corners stay."""
    runtime_settings.set_dev_hud(False)
    p = _player()
    secondary = "\n".join(hud_rows("P1", p))
    for jargon in _DEV_SUBSTRINGS:
        assert jargon not in secondary, f"dev jargon {jargon!r} leaked with dev_hud off"
    assert hud_line_count() == HUD_MINIMAL_LINE_COUNT
    emphasis = "\n".join(hud_emphasis_rows(p))
    for stat in _STAT_SUBSTRINGS:
        assert stat in emphasis, f"emphasized stat {stat!r} missing with dev_hud off"


def test_dev_hud_on_restores_all_dev_lines():
    """dev_hud ON: both jargon rows return as part of the complete dev HUD."""
    runtime_settings.set_dev_hud(True)
    p = _player()
    secondary = "\n".join(hud_rows("P1", p))
    for jargon in _DEV_SUBSTRINGS:
        assert jargon in secondary, f"dev jargon {jargon!r} missing with dev_hud on"
    assert hud_line_count() == HUD_FULL_LINE_COUNT


def test_show_dev_info_no_longer_affects_the_battle_hud():
    """#1319: show_dev_info is superseded in battle — flipping it changes nothing while
    dev_hud is OFF (minimal) or ON (complete). Able-to-fail: re-gate hud_rows on
    show_dev_info and the OFF-with-flag-on branch would leak the jargon rows."""
    runtime_settings.set_dev_hud(False)
    p = _player()
    runtime_settings.set("show_dev_info", False)
    off_flag_off = hud_rows("P1", p)
    runtime_settings.set("show_dev_info", True)
    off_flag_on = hud_rows("P1", p)
    assert off_flag_off == off_flag_on == ["P1"]  # OFF stays minimal regardless

    runtime_settings.set_dev_hud(True)
    runtime_settings.set("show_dev_info", False)
    on_flag_off = hud_rows("P1", p)
    runtime_settings.set("show_dev_info", True)
    on_flag_on = hud_rows("P1", p)
    assert on_flag_off == on_flag_on  # ON stays complete regardless
    assert len(on_flag_on) == HUD_FULL_LINE_COUNT

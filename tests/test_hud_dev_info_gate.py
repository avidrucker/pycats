"""#545: the two implementation-jargon HUD rows (``FSM:`` / ``Shield Attempting:``)
render only when the dev-info flag is on. It defaults **off**, so a player never
sees them; the player-facing rows (Damage / Lives / Shield HP / jumps) always render.

``hud_rows`` is the testable seam ``draw_hud`` iterates — asserting on the row
strings avoids pixel-diffing while covering exactly the acceptance criteria.
"""
import pygame

from pycats import runtime_settings, settings
from pycats.battle_screen import BattleScreen
from pycats.render_battle import (
    HUD_DEV_LINE_COUNT,
    HUD_PLAYER_LINE_COUNT,
    hud_line_count,
    hud_rows,
)

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)

_DEV_SUBSTRINGS = ("FSM:", "Shield Attempting:")
_PLAYER_SUBSTRINGS = ("Damage:", "Lives:", "Shield HP:")


def _player():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("tabby", "calico")
    return bs.player1


def test_default_off_omits_dev_jargon_but_keeps_player_stats():
    """Flag off (the default): no FSM:/Shield Attempting: rows; player stats stay."""
    runtime_settings.seed(settings.defaults())
    assert not runtime_settings.show_dev_info()  # default off

    joined = "\n".join(hud_rows("P1", _player()))
    for jargon in _DEV_SUBSTRINGS:
        assert jargon not in joined, f"dev jargon {jargon!r} leaked with flag off"
    for stat in _PLAYER_SUBSTRINGS:
        assert stat in joined, f"player stat {stat!r} missing with flag off"


def test_flag_on_restores_all_lines():
    """Flag on: both jargon rows return, exactly as rendered before the gate."""
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_dev_info", True)

    joined = "\n".join(hud_rows("P1", _player()))
    for jargon in _DEV_SUBSTRINGS:
        assert jargon in joined, f"dev jargon {jargon!r} missing with flag on"
    for stat in _PLAYER_SUBSTRINGS:
        assert stat in joined, f"player stat {stat!r} missing with flag on"


def test_line_count_tracks_the_flag():
    """The controls/input-history blocks anchor below the HUD, so the drawn row
    count must shrink when the dev rows are gated off (default) and grow when on."""
    runtime_settings.seed(settings.defaults())
    assert hud_line_count() == HUD_PLAYER_LINE_COUNT  # off: player rows only

    runtime_settings.set("show_dev_info", True)
    assert hud_line_count() == HUD_PLAYER_LINE_COUNT + HUD_DEV_LINE_COUNT

    # row list length agrees with the advertised count in both modes
    runtime_settings.seed(settings.defaults())
    assert len(hud_rows("P1", _player())) == HUD_PLAYER_LINE_COUNT
    runtime_settings.set("show_dev_info", True)
    assert len(hud_rows("P1", _player())) == HUD_PLAYER_LINE_COUNT + HUD_DEV_LINE_COUNT

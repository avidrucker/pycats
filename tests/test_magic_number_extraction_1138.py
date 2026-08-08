"""
tests/test_magic_number_extraction_1138.py

Tier-2/3 render + UI layout magic-number extraction (#1138, child of the #1134
tracker; audit doc docs/research/2026-08-02-magic-number-audit-findings.md).

The bulk of #1138 is pixel-identical NAMING — guarded by the render-parity oracle
(test_battle_screen_render.py) and the sim goldens, which stay green because no value
changed. This module pins the parts a golden test can't see: the SSOT / de-dup intent,
where a regression is a value silently re-hardcoded at one of several coupled sites
rather than a changed pixel.

Every assertion is ABLE-TO-FAIL against pre-#1138 main: each constant below did not
exist there (the values were bare inline literals), so importing it errors, and the
coupling assertions fail if any consumer stops routing through the SSOT.
"""

import pygame
import pytest

from pycats.config import (
    HUD_HINT_FONT_PX,
    HUD_SPACING,
    SCREEN_HEIGHT,
    TAIL_BASE_TURN_STEP,
    TAIL_PINNED_SEGMENTS,
)
from pycats.render import hud
from pycats.shell.esc_hold import ESC_HOLD_FRAMES, EscHoldTimer

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


@pytest.fixture(autouse=True)
def _pygame(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    pygame.init()


def test_esc_hold_frames_is_one_ssot_across_all_three_sites():
    """The 2s esc-hold threshold was declared ×3 (EscHoldTimer default, back_hold_frames,
    esc_quit_hold_frames). All three must now route through the single ESC_HOLD_FRAMES,
    so they move together — re-hardcoding any one to a differing value reds this."""
    from pycats.shell.screen_manager import ScreenStateManager

    assert EscHoldTimer().hold_frames == ESC_HOLD_FRAMES  # default binds to the SSOT
    sm = ScreenStateManager(_P1, _P2)
    assert sm.back_hold_frames == ESC_HOLD_FRAMES
    assert sm.esc_quit_hold_frames == ESC_HOLD_FRAMES
    assert sm._esc_hold.hold_frames == ESC_HOLD_FRAMES


def test_hud_hint_font_px_extracted():
    """The shell hint font (bare 24 at three sites) is now the HUD_HINT_FONT_PX SSOT."""
    assert HUD_HINT_FONT_PX == 24


def test_pause_hint_row_couples_emphasis_baseline():
    """draw_pause_hint and the emphasized Damage%/Lives baseline both anchor on the same
    bottom slot. Naming it PAUSE_HINT_ROW_Y couples them: the emphasis baseline sits one
    HUD_BLOCK_GAP above the pause-hint row, so moving the row moves the baseline."""
    assert hud.PAUSE_HINT_ROW_Y == SCREEN_HEIGHT - HUD_SPACING * 3
    # emphasis_row_y's baseline (its last-row anchor) is PAUSE_HINT_ROW_Y - HUD_BLOCK_GAP.
    n = 2
    assert hud.emphasis_row_y(n, n) == hud.PAUSE_HINT_ROW_Y - hud.HUD_BLOCK_GAP


def test_tail_feel_knobs_sourced_from_config():
    """_PINNED / _BASE_TURN_STEP moved to config (TAIL_PINNED_SEGMENTS / TAIL_BASE_TURN_STEP)
    to sit with the other TAIL_* feel knobs; tail.py aliases must track them."""
    from pycats.entities import tail

    assert TAIL_PINNED_SEGMENTS == 2
    assert TAIL_BASE_TURN_STEP == 0.18
    assert tail._PINNED == TAIL_PINNED_SEGMENTS
    assert tail._BASE_TURN_STEP == TAIL_BASE_TURN_STEP

"""The fighter name label ("P1"/"P2") must sit fully above the ear tips (#573).

The ears reach EAR_HEIGHT px above the head top; the centered label is anchored
NAME_LABEL_OFFSET_Y px above the head top. If the label's glyph pixels drop into
the ear zone (bottom edge below `rect.top - EAR_HEIGHT`), the ears tangle the text.

Able-to-fail: revert NAME_LABEL_OFFSET_Y back to 25 and the label bottom drops over
the ears -> the clearance assertion fails.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from pycats import render_battle
from pycats.config import EAR_HEIGHT, SCREEN_HEIGHT, SCREEN_WIDTH

pytestmark = pytest.mark.usefixtures("render_isolation")


class _FakeP:
    """Minimal surface draw_player_name reads: a rect + char_name + nickname."""
    def __init__(self, char_name="P1", nickname=None):
        self.rect = pygame.Rect(200, 200, 40, 60)
        self.char_name = char_name
        self.nickname = nickname


def _label_bounds(p):
    """Return the label's glyph bounding rect drawn on a transparent surface."""
    pygame.init()
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    render_battle.draw_player_name(surf, p)
    return surf.get_bounding_rect()


def test_label_bottom_clears_the_ear_tips():
    p = _FakeP("P1")
    ear_tip_y = p.rect.top - EAR_HEIGHT
    bounds = _label_bounds(p)
    assert bounds.bottom <= ear_tip_y, (
        f"label bottom {bounds.bottom} overlaps ear zone (ear tip at {ear_tip_y})"
    )


def test_both_slots_clear_the_ears():
    for name in ("P1", "P2"):
        p = _FakeP(name)
        ear_tip_y = p.rect.top - EAR_HEIGHT
        assert _label_bounds(p).bottom <= ear_tip_y, f"{name} label overlaps the ears"


def test_offset_constant_leaves_room_for_the_label_above_the_ears():
    # The anchor must clear EAR_HEIGHT plus the label's own glyph height.
    p = _FakeP("P1")
    label_h = _label_bounds(p).height
    assert render_battle.NAME_LABEL_OFFSET_Y >= EAR_HEIGHT + label_h

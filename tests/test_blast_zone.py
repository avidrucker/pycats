"""Blast-zone KO boundary (#733).

TEMPORARY game-feel experiment: the *horizontal* KO blast zone is widened to
~100px off the left/right screen edge, while the *vertical* (top/bottom) KO
boundary stays at 50px. This is NOT a Project M-faithful value — an experimental
knob for playtesting horizontal recovery room.

Able-to-fail: at the old symmetric 50px boundary a fighter 75px off the side edge
would already be KO'd. These tests assert it survives, and pin the exact 100px
horizontal / 50px vertical thresholds — they red at the old 50px horizontal value.
"""

from pycats.combat.data import Circle, FighterData, Hurtbox
from pycats.config import (
    BLAST_PADDING,
    BLAST_PADDING_X,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from pycats.entities.fighter import Fighter

_HB = Hurtbox(circles=(Circle(0, 0, 1),))


def _fighter() -> Fighter:
    fd = FighterData(hurtbox=_HB, moves={})
    return Fighter(x=100, y=100, facing_right=True, fighter_data=fd)


def test_horizontal_blast_padding_is_wider_than_vertical():
    assert BLAST_PADDING_X == 100
    assert BLAST_PADDING == 50
    assert BLAST_PADDING_X > BLAST_PADDING


def test_right_edge_ko_at_100_not_50():
    f = _fighter()
    # 99px past the right edge: inside the widened blast zone (not KO).
    f.rect.left = SCREEN_WIDTH + 99
    assert not f._outside_blast_zone()
    # 101px past: outside (KO).
    f.rect.left = SCREEN_WIDTH + 101
    assert f._outside_blast_zone()


def test_left_edge_ko_at_100_not_50():
    f = _fighter()
    f.rect.right = -99
    assert not f._outside_blast_zone()
    f.rect.right = -101
    assert f._outside_blast_zone()


def test_horizontal_75px_off_edge_survives_reds_at_old_50():
    # The able-to-fail crux: at the old 50px horizontal boundary a fighter 75px off
    # the side edge would be KO'd. With the widened zone it survives both edges.
    f = _fighter()
    f.rect.left = SCREEN_WIDTH + 75  # 75px past the right edge
    assert not f._outside_blast_zone()
    g = _fighter()
    g.rect.right = -75  # 75px past the left edge
    assert not g._outside_blast_zone()


def test_vertical_ko_boundary_unchanged_at_50():
    # top/bottom stay on BLAST_PADDING (50): 49px off is safe, 51px off is KO.
    f = _fighter()
    f.rect.bottom = -49  # near the top edge
    assert not f._outside_blast_zone()
    f.rect.bottom = -51
    assert f._outside_blast_zone()
    g = _fighter()
    g.rect.top = SCREEN_HEIGHT + 49  # near the bottom edge
    assert not g._outside_blast_zone()
    g.rect.top = SCREEN_HEIGHT + 51
    assert g._outside_blast_zone()

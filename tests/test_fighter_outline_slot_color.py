"""#572: the fighter silhouette outline is coloured by player slot — P1 red
(P1_UI_COLOR), P2 blue (P2_UI_COLOR) — matching the name-label accent, instead of
the shared light-gray ring from #546/#564.

Owner decision (recorded on #572): the exact accent blue is used for P2's ring so
it matches the label, accepting that P2's ring measures 2.50:1 vs the dark bg
(below the #546 3:1 target). P1 red stays at 3.77:1.
"""
import pygame
import pytest

from pycats import render_battle as rb
from pycats.battle_screen import BattleScreen
from pycats.config import (
    FIGHTER_OUTLINE_COLOR,
    P1_UI_COLOR,
    P2_UI_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from pycats.render_battle import _BODY_PAD_TOP, _cat_body_surface, slot_accent_color

# Clear stale render caches between tests (surfaces go stale after a quit, #63).
pytestmark = pytest.mark.usefixtures("render_isolation")

_RED = tuple(P1_UI_COLOR)
_BLUE = tuple(P2_UI_COLOR)

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def _players():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("tabby", "void")
    return bs.player1, bs.player2


def _ring_counts(player):
    """(#P1-red pixels, #P2-blue pixels) in the fighter's **body region** (y at or
    below the body top). The ring is the only source of these colours there — no
    skin/stripe/eye/whisker uses them — so a count isolates the outline colour,
    robust to whisker/ear position (unlike a single edge pixel).

    Crucially the scan starts at the body top, EXCLUDING the name label above it —
    the label is drawn in the same slot colour, so counting the whole composite
    would pass even with a wrong (or missing) ring."""
    surf = _cat_body_surface(player)
    w, h = surf.get_size()
    red = blue = 0
    for x in range(w):
        for y in range(_BODY_PAD_TOP, h):  # body + below only; skip the label band
            px = tuple(surf.get_at((x, y)))[:3]
            if px == _RED:
                red += 1
            elif px == _BLUE:
                blue += 1
    return red, blue


def test_slot_accent_color_matches_the_ui_colours():
    p1, p2 = _players()
    assert slot_accent_color(p1) == P1_UI_COLOR
    assert slot_accent_color(p2) == P2_UI_COLOR


def test_p1_ring_is_red_p2_ring_is_blue():
    p1, p2 = _players()
    p1_red, p1_blue = _ring_counts(p1)
    p2_red, p2_blue = _ring_counts(p2)
    assert p1_red > 0 and p1_blue == 0, "P1 ring is not (only) red"
    assert p2_blue > 0 and p2_red == 0, "P2 ring is not (only) blue"


def test_body_cache_does_not_bleed_between_slots():
    """Each slot rings in its own colour — proving the body cache keys on the
    outline colour, not just skin/size (able-to-fail: drop the colour from the key
    and the second slot serves the first's cached ring)."""
    p1, p2 = _players()
    assert _ring_counts(p1)[0] > 0  # P1 has red
    assert _ring_counts(p2)[1] > 0  # P2 has blue
    assert _ring_counts(p1)[1] == 0 and _ring_counts(p2)[0] == 0  # no cross-slot bleed


def test_tail_outline_is_per_slot():
    """render_tail paints the tail ring in the slot colour it's handed, not the
    fixed light-gray constant."""
    p1, _ = _players()
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    rb.render_tail(surface, p1.tail, (20, 20, 20), P1_UI_COLOR)
    bb = surface.get_bounding_rect()
    reds = grays = 0
    for sx in range(bb.left, bb.right):
        for sy in range(bb.top, bb.bottom):
            px = tuple(surface.get_at((sx, sy)))[:3]
            if px == tuple(P1_UI_COLOR):
                reds += 1
            elif px == tuple(FIGHTER_OUTLINE_COLOR):
                grays += 1
    assert reds > 0, "tail ring is not the P1 slot colour"
    assert grays == 0, "tail ring still uses the fixed light-gray constant"

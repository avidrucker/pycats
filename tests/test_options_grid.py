"""Options menu: 2-column grid layout + centered button labels (#389).

The 8 option rows lay out as a 4x2 row-major grid (was a single tall column that
overflowed into the instruction line), navigable in 2D (up/down within a column,
left/right between columns). Labels are centered in their button rects on BOTH
axes (vertical centering was the visible defect — text sat low in the rect).
"""


import pygame  # noqa: E402

from pycats.options_menu import NCOLS, OptionsMenu  # noqa: E402
from pycats.text_utils import text_renderer  # noqa: E402

# Full control dicts (the grid needs left/right, unlike the old single column).
_P1 = dict(up=pygame.K_w, down=pygame.K_s, left=pygame.K_a, right=pygame.K_d,
           attack=pygame.K_v, special=pygame.K_c)
_P2 = dict(up=pygame.K_UP, down=pygame.K_DOWN, left=pygame.K_LEFT, right=pygame.K_RIGHT,
           attack=pygame.K_SLASH, special=pygame.K_PERIOD)

UP, DOWN, LEFT, RIGHT = pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d


def _opts():
    return OptionsMenu(_P1, _P2)


# ---- 2-column grid: layout ------------------------------------------------- #
def test_two_columns():
    assert NCOLS == 2


# ---- 2-column grid: navigation --------------------------------------------- #
def _nrows(m):
    return (len(m.rows) + NCOLS - 1) // NCOLS


def test_down_moves_within_column_by_a_full_row():
    """Down steps a full grid row within column 0 and wraps back to 0 (derived from
    the live row count so it survives rows being added — e.g. #345's font_scale)."""
    m = _opts()
    nrows = _nrows(m)
    expected = [(r % nrows) * NCOLS for r in range(1, nrows + 1)]  # col0 of each row
    assert m.selected_option == 0
    for want in expected:
        m.input_cooldown = 0
        m.update({DOWN})
        assert m.selected_option == want


def test_right_moves_to_the_other_column():
    m = _opts()  # index 0 = row0,col0
    m.update({RIGHT})
    assert m.selected_option == 1  # row0,col1


def test_up_from_top_wraps_to_the_bottom_row():
    m = _opts()  # index 0 = row0,col0
    m.update({UP})
    assert m.selected_option == (_nrows(m) - 1) * NCOLS  # bottom row, col0


def test_left_from_left_column_wraps_within_the_row():
    m = _opts()  # index 0 = row0,col0
    m.update({LEFT})
    assert m.selected_option == 1  # wraps to row0,col1


# ---- centered labels ------------------------------------------------------- #
def test_render_mixed_centered_centers_on_both_axes():
    """The button-label renderer centers the composed text on the point (both axes),
    unlike render_text_mixed which places the text top at the y (so it sat low)."""
    surf = pygame.Surface((240, 120))
    rect = text_renderer.render_mixed_centered("Status Bars: ON", 36, (255, 255, 255),
                                               surf, (120, 60))
    assert rect.center == (120, 60)

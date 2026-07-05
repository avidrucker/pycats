"""Options menu: scale-aware columns + scroll-to-selected (#402).

At large font scale the buttons are too wide for two columns and too many for one
screen, so the grid drops to a single scrollable column that keeps the focused row
visible. These assert the acceptance: adaptive column count, on-screen + non-
overlapping buttons, and scrolling that follows the selection.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import contextlib  # noqa: E402

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.config import MAIN_MENU_OPTION_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.menu_widgets import menu_button_size  # noqa: E402
from pycats.options_menu import OptionsMenu  # noqa: E402

_P1 = dict(up=pygame.K_w, down=pygame.K_s, left=pygame.K_a, right=pygame.K_d,
           attack=pygame.K_v, special=pygame.K_c)
_P2 = dict(up=pygame.K_UP, down=pygame.K_DOWN, left=pygame.K_LEFT, right=pygame.K_RIGHT,
           attack=pygame.K_SLASH, special=pygame.K_PERIOD)


@contextlib.contextmanager
def _scale(preset):
    prev = runtime_settings.get("font_scale")
    runtime_settings.set("font_scale", preset)
    try:
        yield
    finally:
        runtime_settings.set("font_scale", prev)


@pytest.fixture(autouse=True)
def _seed():
    runtime_settings.seed(settings.defaults())
    yield
    runtime_settings.set("font_scale", "standard")


def _rects(m):
    """The rendered button rects this frame (index -> pygame.Rect), plus layout meta."""
    placements, meta = m._layout()
    bw = meta["button_width"]
    rects = []
    for i, (cx, cy) in placements:
        _, bh = menu_button_size(m._row_label(m.rows[i]), MAIN_MENU_OPTION_SIZE,
                                 focused=True, min_width=bw)
        r = pygame.Rect(0, 0, bw, bh)
        r.center = (cx, cy)
        rects.append((i, r))
    return rects, meta


# ---- adaptive columns ------------------------------------------------------- #
def test_two_columns_at_standard():
    with _scale("standard"):
        assert OptionsMenu(_P1, _P2)._effective_cols() == 2


def test_one_column_at_large():
    with _scale("large"):
        assert OptionsMenu(_P1, _P2)._effective_cols() == 1


# ---- no clipping, no overlap ----------------------------------------------- #
def test_buttons_stay_on_screen_at_large():
    with _scale("large"):
        rects, _ = _rects(OptionsMenu(_P1, _P2))
        for i, r in rects:
            assert 0 <= r.left and r.right <= SCREEN_WIDTH, f"row {i} off-screen: {r}"
            assert 0 <= r.top and r.bottom <= SCREEN_HEIGHT, f"row {i} off-screen: {r}"


def test_no_two_visible_buttons_overlap_at_large():
    with _scale("large"):
        rects, _ = _rects(OptionsMenu(_P1, _P2))
        for a in range(len(rects)):
            for b in range(a + 1, len(rects)):
                assert not rects[a][1].colliderect(rects[b][1]), \
                    f"rows {rects[a][0]} and {rects[b][0]} overlap"


# ---- scrolling follows the selection --------------------------------------- #
def test_last_row_scrolls_into_view_at_large():
    with _scale("large"):
        m = OptionsMenu(_P1, _P2)
        m.selected_option = len(m.rows) - 1   # select "Back" (bottom of the list)
        rects, meta = _rects(m)
        visible = {i for i, _ in rects}
        assert (len(m.rows) - 1) in visible, "the selected bottom row must be visible"
        assert meta["more_above"], "scrolled to the bottom -> rows exist above"


def test_scrolling_back_up_reveals_the_top_row_at_large():
    with _scale("large"):
        m = OptionsMenu(_P1, _P2)
        m.selected_option = len(m.rows) - 1
        _rects(m)                              # scroll to the bottom
        m.selected_option = 0                  # jump back to the top
        rects, meta = _rects(m)
        assert 0 in {i for i, _ in rects}, "top row must scroll back into view"
        assert meta["more_below"], "at the top -> rows exist below"


def test_standard_scale_needs_no_scrolling():
    with _scale("standard"):
        m = OptionsMenu(_P1, _P2)
        m.selected_option = len(m.rows) - 1
        rects, meta = _rects(m)
        assert not meta["more_above"] and not meta["more_below"]
        assert len({i for i, _ in rects}) == len(m.rows), "all rows visible at standard"

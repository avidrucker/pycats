"""Pure layout math for scale-aware, scrollable menu grids (#402)."""
from pycats.menu_layout import effective_columns, grid_dims, scroll_to_visible


# ---- effective_columns: how many buttons fit across the screen -------------- #
def test_two_columns_when_buttons_are_narrow():
    # standard-ish: ~309px buttons, 2 fit in 960 (capped at max_cols=2)
    assert effective_columns(960, 309, max_cols=2) == 2


def test_one_column_when_buttons_are_wide():
    # large: ~546px buttons, only one fits across 960
    assert effective_columns(960, 546, max_cols=2) == 1


def test_capped_at_max_cols_even_if_more_fit():
    # tiny buttons could fit 3+, but the design caps at max_cols
    assert effective_columns(960, 120, max_cols=2) == 2


def test_never_returns_zero():
    assert effective_columns(960, 5000, max_cols=2) == 1


# ---- grid_dims -------------------------------------------------------------- #
def test_grid_dims_two_columns():
    assert grid_dims(9, 2) == (2, 5)   # 9 rows over 2 cols -> 5 grid rows


def test_grid_dims_one_column():
    assert grid_dims(9, 1) == (1, 9)


# ---- scroll_to_visible: keep the selected row on screen --------------------- #
def test_no_scroll_when_everything_fits():
    # 5 rows, 5 visible -> never scrolls
    assert scroll_to_visible(0, 4, visible_rows=5, nrows=5) == 0


def test_scrolls_down_to_reveal_selection_below_window():
    # window shows rows [0..4]; selecting row 6 scrolls so 6 is the bottom row
    assert scroll_to_visible(0, 6, visible_rows=5, nrows=9) == 2


def test_scrolls_up_to_reveal_selection_above_window():
    assert scroll_to_visible(4, 2, visible_rows=5, nrows=9) == 2


def test_keeps_selection_visible_without_moving_when_already_in_window():
    assert scroll_to_visible(2, 4, visible_rows=5, nrows=9) == 2


def test_clamped_to_last_page():
    # can't scroll past the bottom: max top = nrows - visible_rows = 4
    assert scroll_to_visible(0, 8, visible_rows=5, nrows=9) == 4
    assert scroll_to_visible(9, 8, visible_rows=5, nrows=9) == 4

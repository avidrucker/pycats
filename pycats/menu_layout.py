"""Pure layout math for scale-aware, scrollable menu grids (#402).

No pygame here — just the integer geometry the Options menu needs so it can be
unit-tested without a display. The menu measures its scaled button size (pygame)
and feeds the numbers in.
"""


def effective_columns(screen_width, button_width, max_cols, gutter=24):
    """How many `button_width` columns fit across `screen_width`, in [1, max_cols].

    At large font scale the buttons grow too wide for two columns, so this drops to
    one; at standard/small two fit (capped at the design's `max_cols`)."""
    if button_width <= 0:
        return max_cols
    fit = (screen_width - gutter) // (button_width + gutter)
    return max(1, min(max_cols, fit))


def grid_dims(n, ncols):
    """(ncols, nrows) for `n` row-major cells over `ncols` columns."""
    ncols = max(1, ncols)
    return ncols, (n + ncols - 1) // ncols


def scroll_to_visible(scroll_top, selected_row, visible_rows, nrows):
    """Smallest adjustment to `scroll_top` so `selected_row` is within the visible
    window of `visible_rows` rows, clamped to [0, nrows - visible_rows].

    Keeps the focused row on screen when the grid is taller than the viewport (the
    large-scale case), and never scrolls past the last page."""
    visible_rows = max(1, visible_rows)
    if selected_row < scroll_top:
        scroll_top = selected_row
    elif selected_row >= scroll_top + visible_rows:
        scroll_top = selected_row - visible_rows + 1
    return max(0, min(scroll_top, max(0, nrows - visible_rows)))

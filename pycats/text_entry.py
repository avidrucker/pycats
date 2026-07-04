# pycats/text_entry.py
#
# Reusable on-screen text-entry model (#471): a navigable character grid the player
# drives with pressed-nav to build a short string. Pure (no pygame) — the render is a
# separate thin function. Consumers (#463 set names, #441 nicknames) host it.
from __future__ import annotations

# Special (non-character) grid cells. Multi-char sentinels so they never collide with
# the single-character cells.
DEL = "DEL"
DONE = "DONE"

# Grid cells, in order: A-Z, 0-9, SPACE, DEL, DONE (spike #464). Uppercase.
_CELLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + [" ", DEL, DONE]


class TextEntry:
    def __init__(self, maxlen, cols=10):
        self.maxlen = maxlen
        self.cols = cols
        self.cells = list(_CELLS)
        self.cursor = 0        # index into cells; starts on the first cell ("A")
        self.text = ""
        self.confirmed = False

    def nav(self, dx, dy):
        """Move the grid cursor: dx steps a cell, dy steps a row (`cols`). Wraps."""
        self.cursor = (self.cursor + dx + dy * self.cols) % len(self.cells)

    def select(self):
        """Act on the focused cell: DONE confirms, DEL backspaces, a char appends it
        (a silent no-op once the buffer is at `maxlen`)."""
        cell = self.cells[self.cursor]
        if cell == DONE:
            self.confirmed = True
        elif cell == DEL:
            self.backspace()
        elif len(self.text) < self.maxlen:
            self.text += cell

    def backspace(self):
        """Remove the last character (safe when the buffer is empty)."""
        self.text = self.text[:-1]


def _cell_label(cell):
    return {" ": "SPC", DEL: "DEL", DONE: "OK"}.get(cell, cell)


def draw_text_entry(surface, entry, title="Enter name"):
    """Render the widget: title, the current buffer, and the char grid with the focused
    cell highlighted. Standalone (the model stays pygame-free) — pygame/render imports
    are local so importing the model doesn't pull them."""
    from .config import (
        MAIN_MENU_BG_COLOR,
        MAIN_MENU_OPTION_SIZE,
        MAIN_MENU_SELECTED_COLOR,
        MAIN_MENU_TITLE_COLOR,
        MAIN_MENU_TITLE_SIZE,
        SCREEN_WIDTH,
        WHITE,
    )
    from .text_utils import text_renderer

    surface.fill(MAIN_MENU_BG_COLOR)
    text_renderer.render_text_simple(title, MAIN_MENU_TITLE_SIZE, MAIN_MENU_TITLE_COLOR,
                                     surface, (SCREEN_WIDTH // 2, 40), center=True)
    text_renderer.render_text_simple(entry.text or "_", MAIN_MENU_OPTION_SIZE, WHITE,
                                     surface, (SCREEN_WIDTH // 2, 95), center=True)

    cols, cell_w, cell_h, top = entry.cols, 56, 40, 160
    x0 = (SCREEN_WIDTH - cols * cell_w) // 2 + cell_w // 2
    for i, cell in enumerate(entry.cells):
        row, col = divmod(i, cols)
        focused = (i == entry.cursor)
        text_renderer.render_text_simple(
            _cell_label(cell), MAIN_MENU_OPTION_SIZE,
            MAIN_MENU_SELECTED_COLOR if focused else WHITE, surface,
            (x0 + col * cell_w, top + row * cell_h), center=True)

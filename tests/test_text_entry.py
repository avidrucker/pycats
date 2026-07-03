"""Reusable on-screen text-entry model (#471).

A navigable character grid (A-Z, 0-9, SPACE, DEL, DONE) that builds a short string
from pressed-nav — pure (no pygame), so it's fully unit-tested here. Consumers
(#463 set names, #441 nicknames) host it; the render is a thin separate function.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pycats.text_entry import TextEntry, DEL, DONE, draw_text_entry


def test_new_text_entry_starts_empty_at_the_first_cell():
    te = TextEntry(maxlen=4)
    assert te.text == ""
    assert te.confirmed is False
    assert te.cells[te.cursor] == "A"   # cursor starts on the first cell


def test_select_appends_the_focused_char():
    te = TextEntry(maxlen=4)
    te.select()                          # cursor on 'A'
    assert te.text == "A"
    assert te.confirmed is False


def test_nav_moves_horizontally_and_wraps():
    te = TextEntry(maxlen=4)
    te.nav(1, 0)
    assert te.cells[te.cursor] == "B"    # right one cell
    te.nav(-1, 0)
    assert te.cells[te.cursor] == "A"    # left, back to A
    te.nav(-1, 0)
    assert te.cursor == len(te.cells) - 1  # left off the start wraps to the last cell


def test_nav_moves_vertically_by_a_row():
    te = TextEntry(maxlen=4, cols=10)
    te.nav(0, 1)
    assert te.cursor == 10               # down = +cols


def test_select_done_confirms_without_appending():
    te = TextEntry(maxlen=4)
    te.cursor = te.cells.index(DONE)
    te.select()
    assert te.confirmed is True
    assert te.text == ""                 # DONE is not a character


def test_select_del_removes_the_last_char():
    te = TextEntry(maxlen=4)
    te.select()                          # "A"
    te.nav(1, 0)
    te.select()                          # "AB"
    te.cursor = te.cells.index(DEL)
    te.select()
    assert te.text == "A"


def test_select_is_a_silent_noop_at_maxlen():
    te = TextEntry(maxlen=2)
    te.select(); te.select(); te.select()   # three appends of "A"
    assert te.text == "AA"               # capped at maxlen, no error


def test_backspace_removes_last_char_and_is_safe_when_empty():
    te = TextEntry(maxlen=4)
    te.select()                          # "A"
    te.backspace()
    assert te.text == ""
    te.backspace()                       # already empty — no crash
    assert te.text == ""


def test_draw_text_entry_renders_without_error():
    import pygame
    pygame.init()
    from pycats.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAIN_MENU_BG_COLOR
    te = TextEntry(maxlen=4)
    te.select()                          # "A" in the buffer
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    draw_text_entry(surf, te)            # must not raise
    assert surf.get_at((5, 5))[:3] == MAIN_MENU_BG_COLOR   # the view filled the bg

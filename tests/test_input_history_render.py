"""render_battle.draw_input_history — the HUD input GRID renders (#21, #875).

Smoke-level pixel checks (the byte-exact oracle is the render parity test in
test_battle_screen_render.py). Confirms the ● / │ cells actually draw for recorded
marks (an empty history draws only the header + row-glyph scaffold), and that the
right-aligned P2 path doesn't crash.
"""

import pygame  # noqa: E402

from pycats import render_battle as rb  # noqa: E402
from pycats.config import BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.shell.input_history import InputHistory  # noqa: E402

CONTROLS = {"up": 3, "attack": 5}


def _blank():
    pygame.font.init()
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.fill(BG_COLOR)
    return s


def _bytes(s):
    return pygame.image.tobytes(s, "RGB")


def _hist_with_marks():
    h = InputHistory()
    h.record({3, 5}, {3, 5}, CONTROLS)  # up + attack pressed (two ● cells)
    h.record(set(), {5}, CONTROLS)  # attack held (a │ cell)
    return h


def test_grid_cells_render_for_recorded_marks():
    """The ●/│ cells draw: a history WITH marks differs from an empty one (which
    draws only the header + 7 row-glyph labels). Able-to-fail: drop the cell loop
    and the two surfaces match."""
    empty = _blank()
    marked = _blank()
    rb.draw_input_history(empty, InputHistory(), "P1")
    rb.draw_input_history(marked, _hist_with_marks(), "P1")
    assert _bytes(marked) != _bytes(empty)


def test_draw_input_history_topright_path_does_not_crash():
    drawn = _blank()
    rb.draw_input_history(drawn, _hist_with_marks(), "P2", topright=True)  # right-aligned
    assert _bytes(drawn) != _bytes(_blank())

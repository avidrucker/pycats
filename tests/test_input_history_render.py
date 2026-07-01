"""render_battle.draw_input_history — the HUD input strip renders (#21).

Smoke-level pixel checks (the byte-exact oracle is the render golden in
test_battle_screen_render.py, re-baselined when this landed). Confirms the
strip actually draws and the right-aligned P2 path doesn't crash.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats import render_battle as rb  # noqa: E402
from pycats.config import BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.input_history import InputHistory  # noqa: E402


def _blank():
    pygame.font.init()
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.fill(BG_COLOR)
    return s


def _bytes(s):
    return pygame.image.tobytes(s, "RGB")


def test_draw_input_history_marks_the_surface_when_entries_present():
    drawn = _blank()
    h = InputHistory()
    h.push("↑A")
    h.push("B")
    rb.draw_input_history(drawn, h, "P1")
    assert _bytes(drawn) != _bytes(_blank())  # glyphs were drawn


def test_draw_input_history_topright_path_does_not_crash():
    drawn = _blank()
    h = InputHistory()
    h.push("→")
    rb.draw_input_history(drawn, h, "P2", topright=True)  # right-aligned; must not raise
    assert _bytes(drawn) != _bytes(_blank())

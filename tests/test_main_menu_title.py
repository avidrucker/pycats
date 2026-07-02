# tests/test_main_menu_title.py
"""Regression guard for #17 — the start screen shows the working title 'Cat Fight'.

The game's screen FSM starts in `main_menu` (screen_manager.py), so the first
screen the player sees is the main menu, and its title IS the start-screen title.
`MainMenuManager.render` already draws "Cat Fight" (added in e1f2e17); this test
pins that string so it can't silently regress or get the ticket re-filed.

Able-to-fail: change the title string in main_menu.render and this goes red
(asserted via revert-check at filing time).

The render path also calls font-dependent helpers (unicode arrows, mixed text,
SysFont); those are stubbed so the test is fast and order-independent and only
exercises the title.
"""
import pygame

from pycats import main_menu
from pycats.main_menu import MainMenuManager


class _DummyFont:
    def size(self, text):
        return (10, 10)

    def render(self, *args, **kwargs):
        return pygame.Surface((1, 1))


def test_start_screen_renders_cat_fight_title(monkeypatch):
    simple_calls = []

    # Spy on the title renderer; no-op the other text helpers and SysFont so the
    # test needs no font init and isolates the title string.
    monkeypatch.setattr(
        main_menu.text_renderer,
        "render_text_simple",
        lambda text, *a, **k: simple_calls.append(text),
    )
    monkeypatch.setattr(
        main_menu.text_renderer, "render_unicode_char", lambda *a, **k: None
    )
    monkeypatch.setattr(
        main_menu.text_renderer, "render_text_mixed", lambda *a, **k: None
    )
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **k: _DummyFont())

    # render() does not read the controls, so empty dicts suffice.
    menu = MainMenuManager({}, {})
    menu.render(pygame.Surface((800, 600)))

    assert "Cat Fight" in simple_calls, (
        f"start screen must render the working title 'Cat Fight'; "
        f"render_text_simple got {simple_calls!r}"
    )

# tests/test_render_isolation.py
"""Regression for #63: render tests must survive a prior test tearing down
global pygame.font state (e.g. a stray ``pygame.quit()``).

This is the revert-check for the ``render_isolation`` fixture (tests/conftest.py):
``test_a`` plays the role of a hostile earlier test that populates the font
cache and then quits the font module; ``test_b`` then renders and must succeed
because the fixture re-initialized font and dropped the stale caches first.

Revert-check: delete the ``pytestmark = pytest.mark.usefixtures(...)`` line below
(or empty out the fixture body) and ``test_b`` fails with
``pygame.error: Invalid font`` / ``font not initialized``.
"""
import pytest
import pygame

from pycats.config import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT
from pycats.sim.runner import build_stage, build_players
from pycats.core.input import InputFrame
from pycats import render_battle as rb
from pycats import text_utils

# The fixture under test — exactly what guards the real render modules.
pytestmark = pytest.mark.usefixtures("render_isolation")


@pytest.fixture(scope="module", autouse=True)
def _restore_global_font_state():
    """This module deliberately tears down global pygame.font to simulate a
    hostile prior test. Restore it (and drop dead cached Fonts) at module
    teardown so downstream test files — which assume font is initialized — are
    unaffected by our pollution."""
    yield
    if not pygame.font.get_init():
        pygame.font.init()
    text_utils.text_renderer.font_cache.clear()
    rb._body_cache.clear()


def _settle():
    platforms = build_stage()
    p1, p2, players = build_players("legacy")
    empty = InputFrame(set(), set(), set())
    for _ in range(10):
        for p in players:
            p.update(empty, platforms, pygame.sprite.Group())
    return players, platforms


def test_a_hostile_prior_test_tears_down_font():
    """Stand-in for the relocated font-detection scratch + pygame.quit() that
    broke the render tests in #59: render once so the singleton font cache holds
    a live Font, then quit the font module so that cached Font goes invalid and
    further Font(None, size) calls raise 'font not initialized'."""
    players, platforms = _settle()
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill(BG_COLOR)
    rb.render_battle(surface, players, platforms)  # populates font + body caches
    assert text_utils.text_renderer.font_cache, "expected a live cached Font"

    pygame.font.quit()  # the pollution: cached Font is now invalid; module down
    assert not pygame.font.get_init()


def test_b_render_survives_prior_font_teardown():
    """With render_isolation active, font is re-initialized and the stale font /
    body caches are cleared before this test, so a fresh render succeeds despite
    test_a's teardown."""
    players, platforms = _settle()
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill(BG_COLOR)
    rb.render_battle(surface, players, platforms)  # must not raise
    assert pygame.font.get_init()
    assert surface.get_at((0, 0)) is not None

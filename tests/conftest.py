# tests/conftest.py — fixtures shared across the test suite.
import pygame
import pytest

from pycats import render_battle as rb
from pycats import text_utils


@pytest.fixture
def render_isolation():
    """Isolate render tests from global pygame.font / cache pollution (#63).

    Another test earlier in the same process can tear down global state — e.g. a
    ``pygame.quit()`` deinitializes ``pygame.font``. After that, a subsequent
    render path breaks in three ways:

    * ``render_battle.draw_player_name -> pygame.font.Font(None, size)`` raises
      ``font not initialized`` when ``text_renderer.font_cache`` misses;
    * any ``Font`` cached in ``text_renderer.font_cache`` *before* the quit is now
      ``Invalid font (font module quit since font created)`` on a cache hit;
    * a ``render_battle._body_cache`` surface built under polluted state would be
      reused and yield wrong pixels.

    Re-initialize font and drop the two stale caches before each render test so
    they pass regardless of suite execution order. Opt in per render module with
    ``pytestmark = pytest.mark.usefixtures("render_isolation")``.
    """
    if not pygame.font.get_init():
        pygame.font.init()
    text_utils.text_renderer.font_cache.clear()
    rb._body_cache.clear()
    rb._body_layers_cache.clear()  # #585: split ring/body layers, same staleness
    rb._tail_seg_cache.clear()  # #330: rotated tail surfaces go stale after a quit
    rb._tail_outline_cache.clear()  # #564: tail outline halos, same staleness
    yield


@pytest.fixture(autouse=True)
def _reset_runtime_settings():
    """Reset the live (present-layer) settings to schema defaults before each test.

    runtime_settings._state is module-global (#121); a test that flips the HUD
    toggle would otherwise leak a False into later render tests that assume the
    on-by-default behaviour. Cheap, so applied automatically to every test."""
    from pycats import runtime_settings, settings

    runtime_settings.seed(settings.defaults())
    yield


@pytest.fixture(autouse=True)
def _no_fake_fonts_leaked():
    """Guard against the cached-fake-in-a-shared-singleton leak (#709; precedent #550).

    A test that monkeypatches a font factory (``pygame.font.SysFont`` / ``Font``) can
    leave the *fake it produced* in the **shared** ``text_renderer.font_cache``. The
    object outlives ``monkeypatch``'s revert — the cache holds the object, not the
    patched fn — so a later render reads it and crashes (``unicode_font=_DummyFont``
    -> no ``get_ascent``), reddening tests in files the diff never touched. See
    RULES.md "Never restore a monkeypatched global by hand" (the cached-fake variant).

    Assert on teardown that the shared font cache holds only real ``pygame.font.Font``
    objects, so a leak fails the **polluting** test by name instead of a mystified
    later victim. A test that legitimately injects a fake font MUST flush the shared
    caches in its own teardown (``text_renderer.font_cache.clear()``), as
    ``test_main_menu_title`` does."""
    yield
    cache = text_utils.text_renderer.font_cache
    leaked = [(key, type(val).__name__) for key, val in cache.items() if not isinstance(val, pygame.font.Font)]
    if leaked:
        cache.clear()  # evict the fake so it can't poison later tests (fail at the source, not a victim)
    assert not leaked, (
        "a non-pygame.font.Font object leaked into the shared text_renderer.font_cache "
        f"(a monkeypatched-font fake that outlived its patch?): {leaked}. Flush the "
        "shared caches in the offending test's teardown — see RULES.md 'Never restore a "
        "monkeypatched global by hand' (the cached-fake variant, #709)."
    )

# tests/conftest.py — fixtures shared across the test suite.
import pygame
import pytest
from helpers import P1, P2, mk_player
from helpers import ground as _ground

from pycats import render_battle as rb
from pycats.ui import text_utils


# --- shared construction fixtures (#884, Child 2 of #833) -------------------
# Thin wrappers over tests/helpers.py so both the fixture users and the files
# that import the helpers directly share one definition (no drift).
@pytest.fixture
def p1_controls():
    """Player-1 combat control map (8-key superset; see helpers.P1)."""
    return dict(P1)


@pytest.fixture
def p2_controls():
    """Player-2 combat control map (arrow cluster; see helpers.P2)."""
    return dict(P2)


@pytest.fixture
def player(p1_controls):
    """A Player at the canonical spawn (100, 100) with the P1 map."""
    return mk_player(controls=p1_controls)


@pytest.fixture
def ground():
    """A wide solid platform under the canonical spawn (its top at y=100)."""
    return _ground()


@pytest.fixture
def two_fighters(p1_controls, p2_controls):
    """P1 (facing right) and P2 (facing left) at the canonical spawn."""
    return (
        mk_player(controls=p1_controls, facing_right=True),
        mk_player(controls=p2_controls, facing_right=False),
    )


def _clear_render_caches():
    """Drop every stale render cache so the next render runs on the cold-cache path.

    The six caches below each go stale after a ``pygame.quit()`` or across test
    order (see ``render_isolation`` for the four failure modes). Extracted from the
    fixture body so a guard can call it directly and assert the caches are empty,
    without depending on fixture-setup ordering (#1274).
    """
    text_utils.text_renderer.font_cache.clear()
    text_utils.text_renderer._mixed_surface_cache.clear()  # #1256: stale mixed-glyph surfaces mask stub-font gaps
    rb._body_cache.clear()
    rb._body_layers_cache.clear()  # #585: split ring/body layers, same staleness
    rb._body_scaled_cache.clear()  # #1266: crouch/breath-rescaled layers, same staleness
    rb._tail_seg_cache.clear()  # #330: rotated tail surfaces go stale after a quit
    rb._tail_outline_cache.clear()  # #564: tail outline halos, same staleness
    rb._shield_bubble_cache.clear()  # #1266: shield bubbles, same staleness
    rb._attack_surface_cache.clear()  # #1266: attack hitbox visuals, same staleness


@pytest.fixture(autouse=True)
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

    A fourth, subtler mode is order-dependence rather than a quit: a mixed-glyph
    surface cached in ``text_renderer._mixed_surface_cache`` by an earlier test
    lets a later test's ``_compose_mixed`` return on a cache hit *before* it
    touches the fonts, masking an incomplete stub font (a fake missing
    ``get_ascent``) that a cold cache would expose. Clearing that cache too keeps
    every opted-in render test on the cold-cache path, so it can't false-green off
    a neighbour's cached surface (#1256).

    Re-initialize font and drop the stale caches before each render test so they
    pass regardless of suite execution order. Now ``autouse=True`` (#1274): every
    test starts on cold render caches, so a new render module can't reopen the hole
    by forgetting the old ``pytestmark = pytest.mark.usefixtures("render_isolation")``
    opt-in (the surviving opt-in lines are harmless no-ops, kept for provenance).
    The six clears live in ``_clear_render_caches()`` so a guard can exercise them
    without fighting fixture-setup order.
    """
    if not pygame.font.get_init():
        pygame.font.init()
    _clear_render_caches()
    yield


@pytest.fixture(autouse=True)
def _reset_runtime_settings():
    """Reset the live (present-layer) settings to schema defaults before each test.

    runtime_settings._state is module-global (#121); a test that flips the HUD
    toggle would otherwise leak a False into later render tests that assume the
    on-by-default behaviour. Cheap, so applied automatically to every test.

    dev_hud (#1319) and dev_mode (#1312) are separate module-globals NOT in _state, so
    seed() does not reset them — reset them here too, or a test that turns the dev HUD /
    dev mode ON leaks it into later tests: dev_hud into render/parity tests that assume
    the minimal default HUD, dev_mode into e.g. the char-select roster test (#1324), which
    sees the expanded dev roster when dev_mode is left True by an earlier test."""
    from pycats.storage import runtime_settings, settings

    runtime_settings.seed(settings.defaults())
    runtime_settings.set_dev_hud(False)
    runtime_settings.set_dev_mode(False)
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

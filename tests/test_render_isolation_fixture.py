# tests/test_render_isolation_fixture.py
"""Guard for the render_isolation fixture's cache-clearing contract (#1256).

render_isolation must drop text_renderer._mixed_surface_cache at setup, so an
opted-in render test never inherits a mixed-glyph surface a neighbour cached (the
staleness that let test_main_menu_title false-green off a warm cache). This pins
that clear directly, order-independently.

Able-to-fail: remove the `_mixed_surface_cache.clear()` line from render_isolation
in conftest.py and this goes red — the seeded sentinel survives into the test.
"""

import pytest

from pycats.ui import text_utils

_SENTINEL_KEY = ("__isolation_probe__", 0, (0, 0, 0))


@pytest.fixture
def _seed_mixed_cache():
    """Leave a sentinel in the shared singleton's mixed-surface cache.

    Requested BEFORE render_isolation in the test signature, so its setup runs
    first (same scope, no interdependency → left-to-right order); render_isolation
    then clears the cache, which is exactly what the test asserts.
    """
    text_utils.text_renderer._mixed_surface_cache[_SENTINEL_KEY] = "stale"
    yield


def test_render_isolation_clears_mixed_surface_cache(_seed_mixed_cache, render_isolation):
    assert _SENTINEL_KEY not in text_utils.text_renderer._mixed_surface_cache, (
        "render_isolation must clear text_renderer._mixed_surface_cache at setup "
        "(#1256); the sentinel a prior step seeded leaked through."
    )

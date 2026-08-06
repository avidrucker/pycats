# tests/test_render_isolation_fixture.py
"""Guard for the render-cache clearing contract (#1256, reworked in #1274).

``_clear_render_caches()`` (conftest.py) must drop every stale render cache —
in particular ``text_renderer._mixed_surface_cache`` — so a render test never
inherits a mixed-glyph surface a neighbour cached (the staleness that let
test_main_menu_title false-green off a warm cache).

This exercises the helper **directly** — seed a cache, call the helper, assert it
is empty — instead of the old seed-before-fixture signature-ordering trick. That
trick broke once ``render_isolation`` became ``autouse=True`` (#1274): an autouse
fixture sets up before explicitly-requested ones, so it cleared the sentinel
before the seed ran. Testing the helper has no fixture-ordering dependency, so it
also survives #1258's ``pytest-randomly`` shuffle.

Able-to-fail: drop the ``_mixed_surface_cache.clear()`` line from
``_clear_render_caches()`` and this goes red — the seeded sentinel survives.
"""

from conftest import _clear_render_caches
from pycats.ui import text_utils

_SENTINEL_KEY = ("__isolation_probe__", 0, (0, 0, 0))


def test_clear_render_caches_drops_mixed_surface_cache():
    text_utils.text_renderer._mixed_surface_cache[_SENTINEL_KEY] = "stale"

    _clear_render_caches()

    assert _SENTINEL_KEY not in text_utils.text_renderer._mixed_surface_cache, (
        "_clear_render_caches() must clear text_renderer._mixed_surface_cache "
        "(#1256); the seeded sentinel leaked through."
    )


def test_autouse_render_isolation_runs_cold_without_pytestmark():
    """No ``pytestmark`` line here — yet the mixed cache is empty at entry (#1274).

    Proves ``render_isolation`` is genuinely autouse: a module that never opts in
    still gets a cold cache before its first line runs, so it can't false-green off
    a neighbour's warm surface.
    """
    assert not text_utils.text_renderer._mixed_surface_cache, (
        "render_isolation (autouse) should have cleared _mixed_surface_cache before "
        "this test ran; a residual entry means autouse isn't in effect."
    )

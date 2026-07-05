"""Font sizes live in one place — config.py (#344).

A CHORE/REFACTOR guard: every UI/HUD text size resolves through config (the single
source), and the render/game/text-util modules that used to carry bare font-size
literals now reference the named constants. Values are unchanged (byte-identical
render), so the real safety net is the rest of the suite + the render-parity oracle;
these tests pin the single-source structure so a future re-scatter is caught.

cat_faces._MONO_SIZE is intentionally NOT centralised (a monospace FACE-render size,
not a UI text size) — a test pins that it stays local.
"""
import pathlib
import re

import pycats.cat_faces as cat_faces
from pycats import config, render_battle, text_utils

_PKG = pathlib.Path(config.__file__).parent


def test_config_holds_the_font_sizes():
    assert config.STATUS_BAR_SECONDS_SIZE == 16
    assert config.STATUS_BAR_LABEL_SIZE == 12
    assert config.GAME_HUD_FONT_SIZE == 24
    assert config.TEXT_PROBE_SIZE == 16


def test_consumers_resolve_through_config():
    # The bar sizes are reachable on render_battle (re-exported via the import) ...
    assert render_battle.STATUS_BAR_SECONDS_SIZE == config.STATUS_BAR_SECONDS_SIZE
    assert render_battle.STATUS_BAR_LABEL_SIZE == config.STATUS_BAR_LABEL_SIZE
    assert text_utils.TEXT_PROBE_SIZE == config.TEXT_PROBE_SIZE
    # ... and are NOT redefined locally (small-int `is` can't prove this — scan the
    # source: render_battle must import, not re-assign, the sizes).
    rb_src = (_PKG / "render_battle.py").read_text()
    assert not re.search(r"^\s*STATUS_BAR_SECONDS_SIZE\s*=", rb_src, re.M)
    assert not re.search(r"^\s*STATUS_BAR_LABEL_SIZE\s*=", rb_src, re.M)


def test_no_bare_font_size_literals_in_touched_modules():
    # A Font(...) / SysFont(...) call ending in a bare integer size is what #344
    # removed; only a named constant or a `size` variable should remain.
    bad = re.compile(r"(?:Font|SysFont)\([^)]*,\s*\d+\s*\)")
    for name in ("render_battle.py", "game.py", "text_utils.py"):
        src = (_PKG / name).read_text()
        hits = bad.findall(src)
        assert not hits, f"{name} still has a bare font-size literal: {hits}"


def test_cat_faces_mono_size_stays_local():
    # Deliberately NOT centralised (#344): a face-render size, not a UI text size.
    assert cat_faces._MONO_SIZE == 28
    assert not hasattr(config, "MONO_SIZE") and not hasattr(config, "FACE_MONO_SIZE")

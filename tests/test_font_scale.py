"""Global font-scale scalar (#345).

A persisted `font_scale` preset (small/standard/large) maps to a UI-text
multiplier (0.5/1.0/2.0) applied at the single text_utils font chokepoint. Standard
(1.0) is an exact identity, so the default render is byte-identical. Options-menu
cycles the preset; a MIN_FONT_PX clamp keeps a scaled-down size readable.
"""

# NB: do NOT set PYCATS_NO_PERSIST here — os.environ at import time leaks into the
# whole session and breaks other modules' save/load tests. These tests never do
# real I/O (they use _validated / in-memory set + a monkeypatched settings.save).

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import runtime_settings, settings, text_utils  # noqa: E402
from pycats.config import FONT_SCALES, MIN_FONT_PX  # noqa: E402
from pycats.options_menu import OptionsMenu  # noqa: E402


@pytest.fixture(autouse=True)
def _restore_scale():
    runtime_settings.seed(settings.defaults())   # start each test at "standard"
    yield
    runtime_settings.set("font_scale", "standard")


# ---- settings schema --------------------------------------------------------

def test_font_scale_defaults_to_standard():
    assert settings.defaults()["font_scale"] == "standard"


def test_validated_snaps_unknown_preset_to_standard():
    assert settings._validated({"font_scale": "huge"})["font_scale"] == "standard"
    assert settings._validated({"font_scale": "large"})["font_scale"] == "large"


# ---- resolver ---------------------------------------------------------------

def test_multiplier_per_preset():
    for name, mult in FONT_SCALES.items():
        runtime_settings.set("font_scale", name)
        assert runtime_settings.font_scale() == mult


def test_scaled_font_size_identity_at_standard():
    for base in (12, 16, 24, 36, 72):
        assert runtime_settings.scaled_font_size(base) == base   # byte-identity


def test_scaled_font_size_scales_and_clamps():
    runtime_settings.set("font_scale", "large")
    assert runtime_settings.scaled_font_size(24) == 48
    runtime_settings.set("font_scale", "small")
    assert runtime_settings.scaled_font_size(24) == 12
    assert runtime_settings.scaled_font_size(4) == MIN_FONT_PX   # never rounds to 0


# ---- applied at the text_utils chokepoint -----------------------------------

@pytest.mark.usefixtures("render_isolation")
def test_render_text_is_bigger_at_large_scale():
    surf = pygame.Surface((400, 200))
    runtime_settings.set("font_scale", "standard")
    std = text_utils.render_text(surf, "pycats", (10, 10), 20, (255, 255, 255))
    runtime_settings.set("font_scale", "large")
    big = text_utils.render_text(surf, "pycats", (10, 10), 20, (255, 255, 255))
    assert big.height > std.height and big.width > std.width


# ---- Options-menu cycle row -------------------------------------------------

def _menu():
    keys = dict(left=1, right=2, up=3, down=4, attack=5, special=6, shield=7)
    return OptionsMenu(keys, keys)


def test_options_row_cycles_small_standard_large(monkeypatch):
    saved = {}
    monkeypatch.setattr(settings, "save", lambda prefs: saved.update(prefs))
    om = _menu()
    # from standard -> large -> small -> standard (order small,standard,large)
    om._activate("font_scale")
    assert runtime_settings.get("font_scale") == "large"
    assert saved["font_scale"] == "large"          # persisted
    om._activate("font_scale")
    assert runtime_settings.get("font_scale") == "small"
    om._activate("font_scale")
    assert runtime_settings.get("font_scale") == "standard"


def test_options_row_label_reflects_current():
    om = _menu()
    runtime_settings.set("font_scale", "large")
    assert om._row_label("font_scale") == "Font Size: Large"
    runtime_settings.set("font_scale", "small")
    assert om._row_label("font_scale") == "Font Size: Small"

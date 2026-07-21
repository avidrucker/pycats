"""Font-scale coverage for the main menu + Options menu (#399).

Answers "do all the menu text fields resize with the font_scale preset, or are some
static?" by rendering each menu at small/standard/large and recording every text
field's rendered size. Assertion-based rather than byte-identical image goldens:
per the ticket, raw PNG goldens are brittle across host font stacks, so we assert
that each field's rendered height tracks the scalar (and flag geometry that doesn't).

This surfaced #401 (mixed-font text was frozen across a scale change because
_compose_mixed keyed its cache by the authored size, not the scaled one) and #402
(button/grid geometry is unscaled — overflow/overlap at large).
"""


import contextlib  # noqa: E402

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.main_menu import MainMenuManager  # noqa: E402
from pycats.options_menu import OptionsMenu  # noqa: E402
from pycats.text_utils import text_renderer  # noqa: E402

_P1 = dict(up=pygame.K_w, down=pygame.K_s, left=pygame.K_a, right=pygame.K_d,
           attack=pygame.K_v, special=pygame.K_c)
_P2 = dict(up=pygame.K_UP, down=pygame.K_DOWN, left=pygame.K_LEFT, right=pygame.K_RIGHT,
           attack=pygame.K_SLASH, special=pygame.K_PERIOD)

# Every TextRenderer entry point the menus draw through. sys_font(...).render (the
# main-menu F11 hint) is keyed by scaled size already, so it isn't part of the bug.
_RENDER_METHODS = ("render_text_simple", "render_text_mixed",
                   "render_mixed_centered", "render_unicode_char")


@contextlib.contextmanager
def _spy_text_sizes():
    """Record {text: (w, h)} for every string drawn via TextRenderer in the block."""
    rec = {}
    orig = {n: getattr(text_renderer, n) for n in _RENDER_METHODS}

    def mk(fn):
        def wrapper(*a, **k):
            rect = fn(*a, **k)
            try:
                rec[str(a[0])] = (rect.width, rect.height)
            except Exception:
                pass
            return rect
        return wrapper

    for n in _RENDER_METHODS:
        setattr(text_renderer, n, mk(orig[n]))
    try:
        yield rec
    finally:
        for n, fn in orig.items():
            setattr(text_renderer, n, fn)


@contextlib.contextmanager
def _font_scale(preset):
    prev = runtime_settings.get("font_scale")
    runtime_settings.set("font_scale", preset)
    try:
        yield
    finally:
        runtime_settings.set("font_scale", prev)


def _field_sizes(menu, preset):
    """Render `menu` at `preset` and return {text: (w, h)} for every drawn string."""
    runtime_settings.seed(settings.defaults())
    with _font_scale(preset), _spy_text_sizes() as rec:
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        menu_obj = MainMenuManager(_P1, _P2) if menu == "main" else OptionsMenu(_P1, _P2)
        menu_obj.render(surf)
    return dict(rec)


@pytest.fixture(autouse=True)
def _restore_scale():
    yield
    runtime_settings.set("font_scale", "standard")


# ---- every text field scales (the headline question) ----------------------- #
@pytest.mark.parametrize("menu", ["main", "options"])
def test_every_menu_text_field_grows_at_large_scale(menu):
    """Render standard then large through the SAME renderer; every text field shared
    by both must be taller at large. Able-to-fail: a field that ignores the scale
    (or is served a stale cached surface — #401) has equal heights and goes red."""
    std = _field_sizes(menu, "standard")
    lg = _field_sizes(menu, "large")
    shared = set(std) & set(lg)  # labels whose string changes with scale are skipped
    assert shared, f"no shared {menu}-menu text fields captured"
    static = {t: (std[t][1], lg[t][1]) for t in shared if lg[t][1] <= std[t][1]}
    assert not static, f"{menu}-menu text fields did NOT scale (std_h, large_h): {static}"


def test_mixed_text_resizes_when_font_scale_changes():
    """#401 regression: the same mixed string composed at two scales must differ in
    size. Able-to-fail: with _compose_mixed keyed by the authored size, the large
    render is served the cached standard surface and the heights match."""
    runtime_settings.seed(settings.defaults())
    surf = pygame.Surface((400, 200))
    with _font_scale("standard"):
        r_std = text_renderer.render_mixed_centered(
            "► Status Bars: ON", 36, (255, 255, 255), surf, (200, 100))
    with _font_scale("large"):
        r_lg = text_renderer.render_mixed_centered(
            "► Status Bars: ON", 36, (255, 255, 255), surf, (200, 100))
    assert r_lg.height > r_std.height


def test_main_menu_option_spacing_scales_with_font_scale():
    """#402: the main-menu option rows spread further apart at large scale. Options
    render through the menu-button widget (#360); since #837 the button loop lives in
    `menu_widgets.draw_menu_screen`, so capture the button centers by spying on
    `menu_widgets.draw_menu_button` (its call site). Able-to-fail: static spacing ->
    equal spans."""
    import pycats.menu_widgets as mw

    def option_span(scale):
        ys = {}

        def spy(surface, label, center, size, focused, **kw):
            ys[label] = center[1]
            return pygame.Rect(0, 0, 1, 1)

        orig = mw.draw_menu_button
        mw.draw_menu_button = spy
        try:
            with _font_scale(scale):
                MainMenuManager(_P1, _P2).render(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)))
        finally:
            mw.draw_menu_button = orig
        return ys["Quit"] - ys["Play"]

    assert option_span("large") > option_span("standard")


def test_small_scale_shrinks_text_below_standard():
    """The scalar cuts both ways: at small the fields are shorter than standard."""
    std = _field_sizes("options", "standard")
    sm = _field_sizes("options", "small")
    shared = set(std) & set(sm)
    bigger = {t: (sm[t][1], std[t][1]) for t in shared if sm[t][1] >= std[t][1]}
    assert not bigger, f"options fields not smaller at small scale: {bigger}"


# ---- geometry now scales: buttons fit their (adaptive) column at large (#402) - #
def test_options_buttons_fit_their_column_at_large_scale():
    """#402: at large the grid drops to a single column, so the (wide) scaled buttons
    fit their column's share of the screen instead of overlapping. Was xfail under
    #399; now a real assertion of the fixed geometry."""
    runtime_settings.seed(settings.defaults())
    with _font_scale("large"):
        om = OptionsMenu(_P1, _P2)
        ncols = om._effective_cols()
        col_budget = SCREEN_WIDTH // ncols
        bw = om._button_size()[0]
        assert bw <= col_budget, f"button {bw}px overflows {col_budget}px column ({ncols} cols)"

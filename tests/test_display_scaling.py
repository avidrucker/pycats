"""Windowed-scale preset helpers (#82).

These are pure-math tests for pycats.display — no pygame surface needed for the
sizing/mode/cycle logic. A separate test exercises a real surface scale to prove
the chosen blit mode actually produces the expected dimensions.
"""
import pytest

from pycats import display
from pycats.config import SCREEN_WIDTH, SCREEN_HEIGHT


@pytest.mark.parametrize(
    "scale, expected",
    [
        (1.0, (960, 540)),
        (1.5, (1440, 810)),
        (2.0, (1920, 1080)),
        (2.5, (2400, 1350)),
    ],
)
def test_window_size_for_preset_is_exact_integer_dims(scale, expected):
    assert display.window_size_for(scale) == expected


def test_every_preset_yields_integer_dims():
    # No fractional pixels for any shipped preset against the 960x540 base.
    for scale in display.WINDOWED_SCALE_PRESETS:
        w, h = display.window_size_for(scale)
        assert isinstance(w, int) and isinstance(h, int)
        assert w == round(SCREEN_WIDTH * scale)
        assert h == round(SCREEN_HEIGHT * scale)


@pytest.mark.parametrize(
    "scale, mode",
    [
        (1.0, "flip"),    # no scaling — blit/flip 1:1
        (1.5, "smooth"),  # fractional — anti-aliased smoothscale
        (2.0, "crisp"),   # clean integer — nearest, pixel-perfect
        (2.5, "smooth"),  # fractional — anti-aliased smoothscale
        (3.0, "crisp"),   # any whole multiple is crisp
    ],
)
def test_blit_mode_for_scale(scale, mode):
    assert display.blit_mode_for(scale) == mode


def test_cycle_preset_advances_and_wraps():
    assert display.cycle_preset(1.0) == 1.5
    assert display.cycle_preset(1.5) == 2.0
    assert display.cycle_preset(2.0) == 2.5
    assert display.cycle_preset(2.5) == 1.0  # wraps to the start


def test_cycle_preset_can_step_backwards():
    assert display.cycle_preset(1.0, step=-1) == 2.5  # wraps to the end
    assert display.cycle_preset(2.0, step=-1) == 1.5


def test_cycle_preset_from_unknown_scale_snaps_to_first():
    # A scale not in the preset list (e.g. a fullscreen-derived factor) returns
    # the first preset rather than raising.
    assert display.cycle_preset(2.66) == display.WINDOWED_SCALE_PRESETS[0]


@pytest.mark.parametrize(
    "display_size, expected",
    [
        ((1920, 1080), 2.0),   # 1080p: clean 2x integer fit
        ((2560, 1440), 2.0),   # 1440p: 2.66x possible, but fit prefers crisp 2x
        ((1366, 768), 1.0),    # common laptop: only 1x fits as an integer
        ((960, 540), 1.0),     # exactly the base
    ],
)
def test_fit_scale_prefers_largest_integer_that_fits(display_size, expected):
    assert display.fit_scale(display_size) == expected


def test_fit_scale_falls_back_to_fractional_when_smaller_than_base():
    # Display smaller than 960x540 in some axis: no integer >= 1 fits, so shrink
    # to the largest fractional scale that fits (the limiting axis wins).
    # 800/960 = 0.8333..., 480/540 = 0.8888... -> 0.8333...
    assert display.fit_scale((800, 480)) == pytest.approx(800 / 960)


@pytest.mark.parametrize(
    "scale, display_size, expected",
    [
        (2.5, (1920, 1080), 2.0),   # 2.5x would overflow 1080p -> clamp to fit (2x)
        (2.5, (2560, 1440), 2.5),   # 2.5x fits on 1440p -> unchanged
        (1.0, (1920, 1080), 1.0),   # well within -> unchanged
        (1.5, (1366, 768), pytest.approx(768 / 540)),  # clamp to the limiting axis
    ],
)
def test_clamp_scale_never_exceeds_what_the_display_can_show(scale, display_size, expected):
    assert display.clamp_scale(scale, display_size) == expected


@pytest.mark.parametrize("scale", [1.0, 1.5, 2.0, 2.5])
def test_scale_surface_produces_expected_dimensions(scale):
    import pygame

    pygame.init()
    src = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    out = display.scale_surface(src, scale)
    assert out.get_size() == display.window_size_for(scale)


def test_scale_surface_at_1x_returns_source_unchanged():
    import pygame

    pygame.init()
    src = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # 1x is the no-scale fast path — same surface object, no copy/transform.
    assert display.scale_surface(src, 1.0) is src


# --- zoom toast (#89): label formatting + countdown timer (both pure) ---


@pytest.mark.parametrize(
    "value, label",
    [
        (1.0, "1×"),
        (1.5, "1.5×"),
        (2.0, "2×"),
        (2.5, "2.5×"),
        ("fit", "Fit"),
    ],
)
def test_format_scale_label(value, label):
    assert display.format_scale_label(value) == label


def test_toast_starts_inactive():
    assert not display.Toast().active


def test_toast_show_activates_then_expires_after_its_frames():
    t = display.Toast()
    t.show("2×", frames=3)
    assert t.active and t.text == "2×"
    t.tick()
    t.tick()
    assert t.active  # 1 frame left
    t.tick()
    assert not t.active  # counted down to 0 -> gone


def test_toast_reshow_resets_the_timer_and_text():
    t = display.Toast()
    t.show("1×", frames=2)
    t.tick()  # 1 left
    t.show("2×", frames=2)  # re-show resets
    assert t.active and t.text == "2×"
    t.tick()
    assert t.active  # still 1 left because the timer reset


def test_toast_default_duration_is_three_seconds():
    from pycats.config import FPS

    assert display.TOAST_DURATION_FRAMES == 3 * FPS


# --- #92: dedupe fullscreen zoom cycle to distinct achievable sizes ---


@pytest.mark.parametrize(
    "display_size, expected",
    [
        ((1920, 1080), [1.0, 1.5, 2.0]),            # 2.5x & fit collapse onto 2x
        ((2560, 1440), [1.0, 1.5, 2.0, 2.5]),       # fit(2x) dedups with the 2x preset
        ((3840, 2160), [1.0, 1.5, 2.0, 2.5, 4.0]),  # fit=4x adds a fill step
    ],
)
def test_achievable_zoom_scales_are_distinct_and_sorted(display_size, expected):
    assert display.achievable_zoom_scales(display_size) == expected


def test_achievable_zoom_scales_small_display_collapses_to_two():
    # 1366x768: 1.5/2/2.5 all clamp to the limiting axis (768/540); fit=1.0.
    scales = display.achievable_zoom_scales((1366, 768))
    assert len(scales) == 2
    assert scales[0] == 1.0
    assert scales[1] == pytest.approx(768 / 540)


def test_achievable_zoom_scales_have_no_duplicates_and_all_fit():
    for d in [(1920, 1080), (2560, 1440), (1366, 768), (1280, 720), (800, 480)]:
        scales = display.achievable_zoom_scales(d)
        # every press distinct:
        assert len(scales) == len({round(s, 4) for s in scales})
        # never crops — base*scale fits the display:
        for s in scales:
            assert SCREEN_WIDTH * s <= d[0] + 1e-9
            assert SCREEN_HEIGHT * s <= d[1] + 1e-9


def test_fullscreen_zoom_label_marks_the_max_as_fit():
    scales = [1.0, 1.5, 2.0]
    assert display.fullscreen_zoom_label(2.0, scales) == "Fit"   # largest = "as big as fits"
    assert display.fullscreen_zoom_label(1.0, scales) == "1×"
    assert display.fullscreen_zoom_label(1.5, scales) == "1.5×"


def test_fullscreen_zoom_label_fit_can_be_a_clamped_fractional():
    scales = [1.0, 768 / 540]
    assert display.fullscreen_zoom_label(768 / 540, scales) == "Fit"
    assert display.fullscreen_zoom_label(1.0, scales) == "1×"

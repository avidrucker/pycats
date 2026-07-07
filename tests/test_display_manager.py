"""DisplayManager — the pure display/window object extracted from game.py (#698, C1 of #280).

game.py owned the "S2" display state (screen/game_surface/scale/offsets/fullscreen
flags/zoom toast) as ~11 module globals mutated together via `global` by
toggle_fullscreen/set_windowed_scale/enter_fullscreen_zoom/set_fullscreen_zoom_index/
present_frame/get_render_surface. Those globals + `global` mutators made the state
untestable and blocked making pycats.game importable. #280 ruled (option b) to dissolve
them into a `DisplayManager` instance.

These tests cover logic that had ZERO coverage before (game.py's loop runs on import,
so nothing exercised the display transitions). Two kinds:

- headless unit tests on the transitions (toggle flips is_fullscreen, windowed vs
  offscreen surface selection, fullscreen zoom index wrap + offset math);
- a render-hash guard: DisplayManager.present() must be byte-identical to the letterbox/
  scale contract present_frame implemented, across (windowed 1x, windowed >1x, fullscreen
  zoomed). Screen-parity is an FSM trace (not pixels), so this pixel check is the real
  safety net for the extraction (same technique as the #515 esc-arc extraction).

Compose-not-inject (ruled on #280): DisplayManager takes plain windowed_scale/
start_fullscreen values and knows nothing about `settings` — so these tests do zero
file I/O (no settings-file pollution, cf. #345).
"""

import pygame  # type: ignore

from pycats import display
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.display_manager import DisplayManager


def _paint(surface):
    """Fill a surface with a deterministic non-uniform pattern so a present() hash
    actually distinguishes correct letterbox/scale placement from a wrong one."""
    surface.fill((10, 20, 30))
    pygame.draw.rect(surface, (200, 40, 40), (0, 0, surface.get_width() // 2, surface.get_height() // 2))
    pygame.draw.rect(surface, (40, 200, 40), (surface.get_width() // 2, surface.get_height() // 2, 50, 50))


def _rgb(surface):
    return pygame.image.tobytes(surface, "RGB")


# --- construction / windowed state ---------------------------------------------


def test_windowed_1x_start_renders_straight_to_the_window():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    assert dm.is_fullscreen is False
    assert dm.windowed_scale == 1.0
    assert dm.scale_factor == 1.0
    assert dm.offset_x == 0 and dm.offset_y == 0
    # 1x fast path: no offscreen surface — the game renders straight to the window.
    assert dm.game_surface is dm.screen


def test_windowed_above_1x_start_uses_an_offscreen_960x540_surface():
    pygame.init()
    dm = DisplayManager(windowed_scale=2.0, start_fullscreen=False)
    assert dm.is_fullscreen is False
    assert dm.scale_factor == 2.0
    # >1x renders to an offscreen 960x540 surface that present() upscales.
    assert dm.game_surface is not dm.screen
    assert dm.game_surface.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT)
    assert dm.screen.get_size() == display.window_size_for(2.0)


def test_render_surface_returns_the_current_game_surface():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    assert dm.render_surface() is dm.game_surface


# --- transitions ---------------------------------------------------------------


def test_toggle_fullscreen_flips_is_fullscreen_both_ways():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    dm.toggle_fullscreen()
    assert dm.is_fullscreen is True
    # entering fullscreen computes this monitor's achievable zoom sizes (>=1 entry).
    assert len(dm.fullscreen_scales) >= 1
    dm.toggle_fullscreen()
    assert dm.is_fullscreen is False


def test_toggle_back_to_windowed_resets_to_1x():
    pygame.init()
    dm = DisplayManager(windowed_scale=2.0, start_fullscreen=False)
    dm.toggle_fullscreen()  # -> fullscreen
    dm.toggle_fullscreen()  # -> windowed, always back to a 1x window
    assert dm.is_fullscreen is False
    assert dm.windowed_scale == 1.0
    assert dm.scale_factor == 1.0
    assert dm.game_surface is dm.screen
    assert dm.offset_x == 0 and dm.offset_y == 0


def test_set_windowed_scale_selects_window_size_and_blit_path():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    dm.set_windowed_scale(2.5)
    assert dm.windowed_scale == 2.5
    assert dm.scale_factor == 2.5
    assert dm.is_fullscreen is False
    assert dm.screen.get_size() == display.window_size_for(2.5)
    assert dm.game_surface is not dm.screen  # fractional/>1x -> offscreen surface
    dm.set_windowed_scale(1.0)
    assert dm.game_surface is dm.screen  # back to the 1x no-scale fast path


def test_fullscreen_zoom_starts_at_fit_and_index_wraps():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    # Stand a known display size in for the fullscreen surface so the zoom math is
    # deterministic (real set_mode fullscreen size varies by host/headless driver).
    dm.screen = pygame.display.set_mode((1920, 1080))
    dm.is_fullscreen = True
    dm.enter_fullscreen_zoom()
    assert dm.fullscreen_scales == display.achievable_zoom_scales((1920, 1080))
    # starts at the largest achievable zoom ("Fit").
    assert dm.fullscreen_zoom_index == len(dm.fullscreen_scales) - 1
    assert dm.scale_factor == dm.fullscreen_scales[-1]
    # F10 advances with wraparound (the loop's (i+1) % len) back to the first size.
    n = len(dm.fullscreen_scales)
    dm.set_fullscreen_zoom_index((dm.fullscreen_zoom_index + 1) % n)
    assert dm.fullscreen_zoom_index == 0
    assert dm.scale_factor == dm.fullscreen_scales[0]


def test_set_fullscreen_zoom_index_centres_the_view():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    dm.screen = pygame.display.set_mode((1920, 1080))
    dm.is_fullscreen = True
    dm.enter_fullscreen_zoom()
    dm.set_fullscreen_zoom_index(0)  # smallest achievable = 1.0x here
    scaled_w, scaled_h = display.window_size_for(dm.scale_factor)
    assert dm.offset_x == (1920 - scaled_w) // 2
    assert dm.offset_y == (1080 - scaled_h) // 2


# --- render-hash guard: present() is byte-identical to the letterbox contract ---


def test_present_windowed_above_1x_upscales_offscreen_to_the_window():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    dm.set_windowed_scale(2.0)
    _paint(dm.game_surface)

    win_w, win_h = display.window_size_for(2.0)
    got = pygame.Surface((win_w, win_h))
    dm.present(display_target=got)

    # Reference: the windowed >1x contract — blit the offscreen surface, scaled up,
    # at the origin (the window is exactly window_size_for(scale), so no letterbox).
    want = pygame.Surface((win_w, win_h))
    want.blit(display.scale_surface(dm.game_surface, 2.0), (0, 0))

    assert _rgb(got) == _rgb(want)


def test_present_fullscreen_letterboxes_the_scaled_view_centred_on_black():
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    dm.screen = pygame.display.set_mode((1920, 1080))
    dm.is_fullscreen = True
    dm.enter_fullscreen_zoom()
    dm.set_fullscreen_zoom_index(0)  # a zoom that leaves a letterbox border
    _paint(dm.game_surface)

    got = pygame.Surface((1920, 1080))
    dm.present(display_target=got)

    # Reference: the fullscreen contract — clear to black, then blit the magnified
    # 960x540 view centred at (offset_x, offset_y).
    want = pygame.Surface((1920, 1080))
    want.fill((0, 0, 0))
    want.blit(display.scale_surface(dm.game_surface, dm.scale_factor), (dm.offset_x, dm.offset_y))

    assert _rgb(got) == _rgb(want)


def test_present_windowed_1x_leaves_the_frame_untouched():
    # At windowed 1x the game renders straight to the window; present() adds no
    # blit (game_surface IS the window), so the frame is presented as-is.
    pygame.init()
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    target = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    _paint(target)
    before = _rgb(target)
    dm.present(display_target=target)
    assert _rgb(target) == before

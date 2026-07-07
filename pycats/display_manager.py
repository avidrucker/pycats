"""
Purpose: The display/window shell object (#698, C1 of #280).

`DisplayManager` owns the "S2" display state that `game.py` used to hold as ~11 module
globals mutated together via `global` — the pygame window/surfaces, the current scale
and letterbox offsets, the windowed/fullscreen flags, the achievable fullscreen zoom
sizes, and the zoom toast. Dissolving those globals into instance state is what makes
`game.py` importable (a future `main()` can't rebind module globals) and makes the
display transitions unit-testable for the first time (the game loop runs at import, so
nothing exercised them before).

Compose, not inject (ruled on #280): this object knows nothing about `settings`. Its
constructor takes plain values (`windowed_scale`, `start_fullscreen`); the change-then-
persist composite and the Options `_display_hooks` stay in the `game.py` orchestration
layer, which calls a transition here and then saves. That keeps `DisplayManager`
headless-unit-testable with zero file I/O (cf. the #345 settings-file test trap).

The zoom/scale math is not re-implemented here — it is consumed from `pycats.display`
(`window_size_for`, `achievable_zoom_scales`, `scale_surface`, `Toast`, labels).
"""

import pygame  # type: ignore

from . import display, text_utils
from .config import HUD_PADDING, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE


class DisplayManager:
    """Owns the pygame window + present path for the 960x540 sim view.

    Windowed at 1x renders straight to the window (no scaling). Windowed at >1x renders
    to an offscreen 960x540 surface that `present()` upscales to fill the window.
    Fullscreen renders to the offscreen surface and letterboxes a magnified, centred
    copy (F10 cycles the achievable zoom sizes)."""

    def __init__(self, windowed_scale, start_fullscreen):
        self.windowed_scale = windowed_scale
        # In-fullscreen magnification (#85, #92): F10 cycles the distinct zoom sizes the
        # current monitor can show (display.achievable_zoom_scales). fullscreen_scales is
        # that list (set on entering fullscreen); fullscreen_zoom_index points into it.
        self.fullscreen_scales = []
        self.fullscreen_zoom_index = 0
        # Transient toast showing the current scale/zoom after an F10 change (#89).
        self.zoom_toast = display.Toast()

        if start_fullscreen:
            # Open fullscreen at the largest "Fit" zoom; F10 cycles it in place.
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.display_surface = self.screen
            self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.is_fullscreen = True
            self.enter_fullscreen_zoom()
        else:
            # Open the window at the saved scale (offscreen surface + upscale when >1x).
            self.screen = pygame.display.set_mode(display.window_size_for(windowed_scale))
            self.display_surface = self.screen
            self.game_surface = self.screen if windowed_scale == 1.0 else pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.scale_factor = windowed_scale
            self.offset_x = 0
            self.offset_y = 0
            self.is_fullscreen = False

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        if self.is_fullscreen:
            # Switch to windowed mode (back to a 1x window).
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.display_surface = self.screen
            self.game_surface = self.screen
            self.scale_factor = 1.0
            self.windowed_scale = 1.0
            self.offset_x = 0
            self.offset_y = 0
            self.is_fullscreen = False
        else:
            # Switch to fullscreen at the largest "Fit" zoom; F10 cycles it in place.
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.display_surface = self.screen
            self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.is_fullscreen = True
            self.enter_fullscreen_zoom()

    def set_windowed_scale(self, scale):
        """Switch to windowed mode at `scale`x the 960x540 base (e.g. 1x/1.5x/2x/2.5x).

        The sim always renders at 960x540; at >1x we render to an offscreen game_surface
        and present() scales it up to the window. At 1x we render straight to the window
        (no scaling)."""
        self.windowed_scale = scale
        self.screen = pygame.display.set_mode(display.window_size_for(scale))
        self.display_surface = self.screen
        self.game_surface = self.screen if scale == 1.0 else pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.scale_factor = scale
        self.offset_x = 0
        self.offset_y = 0
        self.is_fullscreen = False

    def enter_fullscreen_zoom(self):
        """Compute this monitor's distinct zoom sizes and start at the largest ("Fit").
        Call right after switching the display to fullscreen (screen must be active)."""
        self.fullscreen_scales = display.achievable_zoom_scales(self.screen.get_size())
        self.set_fullscreen_zoom_index(len(self.fullscreen_scales) - 1)

    def set_fullscreen_zoom_index(self, i):
        """Apply the i-th achievable fullscreen zoom (staying fullscreen): set the
        magnification of the 960x540 view and recompute the centring offsets. The
        achievable scales already fit the monitor, so the whole stage stays on-screen
        (letterboxed). Assumes the fullscreen display surface is active (screen)."""
        self.fullscreen_zoom_index = i
        self.scale_factor = self.fullscreen_scales[i]
        display_w, display_h = self.screen.get_size()
        scaled_w, scaled_h = display.window_size_for(self.scale_factor)
        self.offset_x = (display_w - scaled_w) // 2
        self.offset_y = (display_h - scaled_h) // 2

    def render_surface(self):
        """Get the surface to render the game onto (the offscreen 960x540 surface
        whenever we are scaling; the window itself at windowed 1x)."""
        return self.game_surface

    def present(self, display_target=None):
        """Present the rendered frame: letterbox/scale the 960x540 view per the current
        mode, draw the zoom toast, and flip.

        `display_target` overrides the surface blitted onto — the render-hash guard
        passes a scratch surface to capture pixels without a live window. The default
        (`None`) presents onto the live display surface, and only that path flips."""
        target = self.display_surface if display_target is None else display_target
        if self.is_fullscreen:
            # Letterbox: clear, then draw the magnified 960x540 view centred. The zoom
            # (scale_factor) is set by set_fullscreen_zoom_index; crisp at whole
            # multiples, smoothscale at fractional zooms (see display.scale_surface).
            target.fill((0, 0, 0))
            target.blit(display.scale_surface(self.game_surface, self.scale_factor), (self.offset_x, self.offset_y))
        elif self.game_surface is not self.screen:
            # Windowed at >1x: scale the offscreen 960x540 surface up to fill the window
            # (which is exactly window_size_for(scale), so no letterbox).
            target.blit(display.scale_surface(self.game_surface, self.scale_factor), (0, 0))

        # Zoom toast (#89): drawn on the window surface, above the scene, so it is crisp
        # and screen-positioned (and never lands in the 960x540 sim/goldens).
        if self.zoom_toast.active:
            text_utils.render_text(
                target,
                self.zoom_toast.text,
                (target.get_width() - HUD_PADDING, HUD_PADDING),
                24,
                WHITE,
                right_align=True,
            )
        self.zoom_toast.tick()

        if display_target is None:
            pygame.display.flip()

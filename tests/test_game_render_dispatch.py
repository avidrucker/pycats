"""game.py's per-frame render dispatch (screen_render.render_active_screen).

Regression for the "Options never renders / the game looks frozen selecting
Options" defect: the main menu -> options transition fired fine (the engine works),
but game.py's module-level main-loop render dispatch had NO `options` branch, so
`ScreenStateManager.render` was never called for that state and the loop just
re-presented the stale main-menu frame — indistinguishable from a hard freeze.

Every headless repro missed it because they call `ScreenStateManager.render()`
directly, bypassing this dispatch — which is the layer that was actually broken.

Able-to-fail: delete the `options` branch from render_active_screen and
`test_options_state_renders_via_screen_manager` goes red (render spy never called).
"""
import pygame

from pycats import screen_render


class _SpyScreenManager:
    """Records render() calls so we can assert a state actually drew something."""

    def __init__(self):
        self.render_calls = []

    def render(self, surface):
        self.render_calls.append(surface)

    def render_esc_quit_progress(self, surface):  # used by the playing branch
        pass

    def get_pause_menu(self):  # used by the pause branch
        return None


def _surface():
    return pygame.Surface((64, 64))


def _dispatch(state, sm, surface):
    screen_render.render_active_screen(
        state, sm, surface,
        battle=None, platforms=None,
        is_fullscreen=False, frame_input=None, fps=60.0,
    )


def test_options_state_renders_via_screen_manager():
    """The 'options' state must delegate to ScreenStateManager.render — otherwise
    Options never paints and the stale main-menu frame stays on screen (the
    apparent freeze). This is the branch game.py's loop was missing."""
    sm = _SpyScreenManager()
    surf = _surface()
    _dispatch("options", sm, surf)
    assert sm.render_calls == [surf]


def test_main_menu_state_renders_via_screen_manager():
    """Positive control: a menu state that always worked still delegates to render,
    so a green 'options' test can't be a no-op that never renders anything."""
    sm = _SpyScreenManager()
    surf = _surface()
    _dispatch("main_menu", sm, surf)
    assert sm.render_calls == [surf]


def test_win_screen_state_renders_via_screen_manager():
    """The other screen_manager-delegating menu state, for completeness."""
    sm = _SpyScreenManager()
    surf = _surface()
    _dispatch("win_screen", sm, surf)
    assert sm.render_calls == [surf]

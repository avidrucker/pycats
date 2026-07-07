"""Per-screen render dispatch for the live game loop.

`game.py`'s main loop is module-level code (it runs on import), so its inline
`if current_state == ...` render chain could never be unit-tested — and a missing
branch there (the `options` screen was never drawn, so selecting Options left the
stale main-menu frame on screen and looked like a hard freeze) slipped past every
headless repro, because those drive `ScreenStateManager.render()` directly and
bypass this dispatch entirely.

Extracting the dispatch into one importable, side-effect-free function makes the
screen->draw mapping testable in isolation (see tests/test_game_render_dispatch.py).
The loop calls `render_active_screen(...)` once per frame with the frame-local
collaborators it used to close over as module globals.
"""

from . import runtime_settings, text_utils
from .config import HUD_PADDING, HUD_SPACING, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from .render_battle import draw_shell_chrome


def render_active_screen(current_state, screen_manager, surface, *, battle, platforms, is_fullscreen, frame_input, fps):
    """Draw the screen for ``current_state`` onto ``surface``.

    Menu-like states (main_menu, options, char_select, win_screen) delegate to
    ``ScreenStateManager.render`` — which owns their per-state sub-renderers — while
    the battle states (playing, pause) composite through the ``battle`` object. The
    char_select and playing branches also layer the loop's shell chrome (display
    hints / FPS overlay / esc-hold progress) that isn't part of a menu surface.
    """
    if current_state == "main_menu":
        screen_manager.render(surface)

    elif current_state == "options":
        # The Options sub-menu (#121) — was missing here, so selecting Options left
        # the stale main-menu frame on screen and looked like a hard freeze even
        # though the loop kept running at 60fps. ScreenStateManager.render dispatches
        # to options_menu.render for this state.
        screen_manager.render(surface)

    elif current_state == "char_select":
        screen_manager.render(surface)

        # Draw fullscreen instructions on character select screen
        fs_text = (
            "F11: Toggle Fullscreen | "
            + ("F10: Fullscreen Zoom" if is_fullscreen else "F10: Window Size")
            + (" | ESC: Exit Fullscreen" if is_fullscreen else "")
        )
        text_utils.render_text(
            surface,
            fs_text,
            (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
            24,
            WHITE,
            right_align=True,
        )

        # Back-to-menu action hint (hold-B, #20) — gated by the non-battle
        # show_screen_hints toggle (#681). The F11/F10 display hints above stay
        # always-on (they are display-mode affordances, not per-screen action hints).
        if runtime_settings.show_screen_hints():
            back_text = "Hold B for 1 second to return to main menu"
            text_utils.render_text(
                surface,
                back_text,
                (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
                24,
                WHITE,
            )

    elif current_state == "playing":
        battle.render(surface, platforms)
        draw_shell_chrome(surface, fps, is_fullscreen, frame_input)
        screen_manager.render_esc_quit_progress(surface)

    elif current_state == "pause":
        battle.render_paused(surface, platforms, screen_manager.get_pause_menu())

    elif current_state == "win_screen":
        screen_manager.render(surface)

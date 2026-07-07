"""Playing-state shell-chrome render helper (#279).

`draw_shell_chrome` extracts the FPS / fullscreen-hint / debug-input overlays that
game.py's `playing` loop branch used to draw inline. They read shell state (fps,
is_fullscreen, frame_input) — NOT battle state — so they live in a render helper the
loop calls, rather than inside BattleScreen (which would re-couple shell state into
the battle object; cf. #100 Risks + #246).

Byte-parity oracle (render isn't golden-covered): the helper must paint a surface
byte-for-byte identical to the old inline block, for windowed/fullscreen and
input-present cases.
"""

import pygame

from pycats import runtime_settings, text_utils
from pycats.config import HUD_PADDING, HUD_SPACING, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from pycats.core.input import InputFrame
from pycats.render_battle import draw_shell_chrome


def _raw(surface):
    return pygame.image.tobytes(surface, "RGBA")


def _expected(fps, is_fullscreen, frame_input):
    """The exact inline block game.py's playing branch used to draw."""
    pygame.init()
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    if frame_input:
        text_utils.render_text(
            s,
            frame_input.__str__(),
            (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
            24,
            WHITE,
        )
    text_utils.render_text(
        s,
        f"FPS: {fps:.2f}",
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
        24,
        WHITE,
        right_align=True,
    )
    fs_text = (
        "F11: Toggle Fullscreen | "
        + ("F10: Fullscreen Zoom" if is_fullscreen else "F10: Window Size")
        + (" | ESC: Exit Fullscreen" if is_fullscreen else "")
    )
    text_utils.render_text(
        s,
        fs_text,
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 2),
        24,
        WHITE,
        right_align=True,
    )
    # #681: the in-battle ESC-hold leave-match hint, gated by the same toggles the
    # helper reads. Mirrors draw_shell_chrome so this stays a faithful parity oracle.
    if runtime_settings.show_controls() and runtime_settings.esc_hold_to_navigate():
        text_utils.render_text(
            s,
            "Hold ESC to leave match",
            (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 2),
            24,
            WHITE,
        )
    return s


def _actual(fps, is_fullscreen, frame_input):
    pygame.init()
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    draw_shell_chrome(s, fps, is_fullscreen, frame_input)
    return s


def test_draw_shell_chrome_matches_inline_windowed():
    fi = InputFrame(held=set(), pressed={1}, released=set())
    fps = 59.97
    assert _raw(_actual(fps, False, fi)) == _raw(_expected(fps, False, fi))


def test_draw_shell_chrome_matches_inline_fullscreen():
    # is_fullscreen flips the F10 label and adds the ESC hint — must be reproduced.
    fi = InputFrame(held={2}, pressed=set(), released=set())
    fps = 30.0
    assert _raw(_actual(fps, True, fi)) == _raw(_expected(fps, True, fi))

"""Acceptance coverage for unresolved hold-ESC-to-quit gaps (#113/#151)."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.core.input import InputFrame
from pycats.screen_manager import ScreenStateManager

P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v, "special": pygame.K_c}
P2 = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "attack": pygame.K_SLASH,
    "special": pygame.K_PERIOD,
}


def _frame(held=None, pressed=None):
    return InputFrame(
        held=set(held or []),
        pressed=set(pressed or []),
        released=set(),
    )


def test_main_menu_render_changes_while_esc_hold_progress_is_live(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    pygame.init()
    sm = ScreenStateManager(P1, P2)

    baseline = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    sm.render(baseline)

    for _ in range(sm.esc_quit_hold_frames // 2):
        sm.update(_frame(held={pygame.K_ESCAPE}))

    with_progress = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    sm.render(with_progress)

    assert pygame.image.tobytes(baseline, "RGBA") != pygame.image.tobytes(
        with_progress,
        "RGBA",
    )


def test_main_menu_render_clears_esc_hold_progress_after_early_release(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    pygame.init()
    sm = ScreenStateManager(P1, P2)

    baseline = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    sm.render(baseline)

    for _ in range(sm.esc_quit_hold_frames // 2):
        sm.update(_frame(held={pygame.K_ESCAPE}))
    sm.update(_frame())

    after_release = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    sm.render(after_release)

    assert pygame.image.tobytes(baseline, "RGBA") == pygame.image.tobytes(
        after_release,
        "RGBA",
    )

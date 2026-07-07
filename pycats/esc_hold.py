# pycats/esc_hold.py
"""Shared hold-Esc-to-back-out timer + its progress arc (#453/#113, design #507 §3b).

`ScreenStateManager` (the in-game screen ladder) and the CLI demo/sim playback
(`LivePresenter`) both tick the SAME `EscHoldTimer`, so they share one 2-second
threshold and one 0..1 progress semantic — "hold Esc ~2s to back out / quit,"
consistent everywhere. The timer is pure (no pygame), so it is unit-testable and
identical on both surfaces by construction; `draw_esc_hold_arc` is the one place
the progress arc's geometry lives, reused by both surfaces' renderers.
"""

from __future__ import annotations

import math

import pygame  # type: ignore

from .config import MAIN_MENU_SELECTED_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE


class EscHoldTimer:
    """Counts frames while Esc is held; fires at `hold_frames` (120 = 2s @ 60fps).

    Tick it once per frame with the current held state: `tick(True)` advances the
    count, `tick(False)` (release) resets it to zero — a hold must be continuous.
    `complete` is the fired state; `progress` is a 0..1 ratio for the arc."""

    def __init__(self, hold_frames: int = 120):
        self.hold_frames = hold_frames
        self.timer = 0

    def tick(self, held: bool) -> None:
        self.timer = self.timer + 1 if held else 0

    def reset(self) -> None:
        self.timer = 0

    @property
    def complete(self) -> bool:
        return self.timer >= self.hold_frames

    @property
    def progress(self) -> float:
        if self.hold_frames <= 0:
            return 0.0
        return min(1.0, self.timer / self.hold_frames)


def draw_esc_hold_arc(surface, progress: float) -> None:
    """Draw the circular hold-progress indicator (#453) for `progress` in 0..1.
    No-op at progress <= 0. Single source for the arc's geometry so the in-game
    ladder and CLI playback render identical feedback."""
    if progress <= 0:
        return

    radius = 28
    width = 6
    center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 155)
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center

    pygame.draw.circle(surface, WHITE, center, radius, 2)
    pygame.draw.arc(
        surface,
        MAIN_MENU_SELECTED_COLOR,
        rect,
        -math.pi / 2,
        -math.pi / 2 + math.tau * progress,
        width,
    )

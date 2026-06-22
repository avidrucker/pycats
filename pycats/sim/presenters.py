# pycats/sim/presenters.py
"""Presenters let the deterministic runner replay headless, live, or to video."""
from __future__ import annotations

import pygame

from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, FPS, WHITE, HUD_PADDING
from ..render_battle import render_battle, render_attacks
from .. import text_utils


class HeadlessPresenter:
    def show(self, platforms, players, attacks, frame): ...
    def close(self): ...


class LivePresenter:
    """Opens a real window and renders the replay.

    `cap_fps=True` paces the window to 60 FPS (so the on-screen FPS reads ~60
    when the renderer is keeping up). `cap_fps=False` runs uncapped, so the FPS
    readout shows the true achievable rate. `overlay=True` draws an FPS counter
    plus each fighter's stocks/damage."""

    def __init__(self, caption="PyCats replay", cap_fps=True, overlay=True):
        import os
        os.environ.pop("SDL_VIDEODRIVER", None)
        pygame.display.quit()
        pygame.display.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()
        self.cap_fps = cap_fps
        self.overlay = overlay

    def _draw_overlay(self, players):
        cap = "capped@60" if self.cap_fps else "uncapped"
        text_utils.render_text(
            self.screen, f"FPS: {self.clock.get_fps():.1f} ({cap})",
            (SCREEN_WIDTH - HUD_PADDING, HUD_PADDING), 24, WHITE, right_align=True)
        for i, p in enumerate(players):
            text_utils.render_text(
                self.screen,
                f"{p.char_name}: {p.lives} stocks  {int(p.percent)}%  [{p.state}]",
                (HUD_PADDING, HUD_PADDING + i * 22), 22, WHITE)

    def show(self, platforms, players, attacks, frame):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                raise KeyboardInterrupt
        self.screen.fill(BG_COLOR)
        render_battle(self.screen, players, platforms)
        render_attacks(self.screen, attacks)
        if self.overlay:
            self._draw_overlay(players)
        pygame.display.flip()
        self.clock.tick(FPS) if self.cap_fps else self.clock.tick()

    def close(self):
        pygame.display.quit()


class VideoPresenter:
    """Writes each frame to a video file. Requires imageio (+ imageio-ffmpeg)."""

    def __init__(self, path="battle.mp4", fps=FPS):
        try:
            import imageio.v2 as imageio
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "video mode needs imageio: pip install imageio imageio-ffmpeg"
            ) from exc
        self._imageio = imageio
        self._writer = imageio.get_writer(path, fps=fps)
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def show(self, platforms, players, attacks, frame):
        self._surface.fill(BG_COLOR)
        render_battle(self._surface, players, platforms)
        render_attacks(self._surface, attacks)
        arr = pygame.surfarray.array3d(self._surface).transpose(1, 0, 2)
        self._writer.append_data(arr)

    def close(self):
        self._writer.close()

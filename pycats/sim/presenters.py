# pycats/sim/presenters.py
"""Presenters let the deterministic runner replay headless, live, or to video."""
from __future__ import annotations

import pygame

from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, FPS
from ..render_battle import render_battle, render_attacks


class HeadlessPresenter:
    def show(self, platforms, players, attacks, frame): ...
    def close(self): ...


class LivePresenter:
    """Opens a real window and renders the replay at 60 FPS."""

    def __init__(self, caption="PyCats replay"):
        import os
        os.environ.pop("SDL_VIDEODRIVER", None)
        pygame.display.quit()
        pygame.display.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

    def show(self, platforms, players, attacks, frame):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                raise KeyboardInterrupt
        self.screen.fill(BG_COLOR)
        render_battle(self.screen, players, platforms)
        render_attacks(self.screen, attacks)
        pygame.display.flip()
        self.clock.tick(FPS)

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

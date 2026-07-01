# pycats/sim/presenters.py
"""Presenters let the deterministic runner replay headless, live, or to video."""
from __future__ import annotations

import pygame

from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, FPS, WHITE, HUD_PADDING
from ..render_battle import render_battle, render_attacks
from .. import text_utils
from .captions import draw_captions, caption_hold_frames


# --- Playback-speed scalar (#351) --------------------------------------------
# Slow-motion is presentation-only: the sim is fixed-timestep (#166/#80), so we pace
# the DISPLAY of frames, never the sim. `speed` < 1 is slow-mo, > 1 is fast-forward;
# 1.0 is real time (the default, byte-identical to before).

def frames_per_output(speed: float) -> int:
    """Video frames to emit per sim frame at `speed`. 0.5 -> 2 (each sim frame is
    written twice, so the 60fps video plays back 2x longer / half speed). Never < 1
    (fast-forward can't drop frames here — that would desync captions)."""
    if speed <= 0:
        return 1
    return max(1, round(1 / speed))


def tick_fps(speed: float) -> int:
    """Live display tick target at `speed`. 0.5 -> 30 (each frame dwells ~2x as long
    on screen). Clamped to >= 1."""
    return max(1, round(FPS * speed))


class HeadlessPresenter:
    def show(self, platforms, players, attacks, frame): ...
    def close(self): ...


class LivePresenter:
    """Opens a real window and renders the replay.

    `cap_fps=True` paces the window to 60 FPS (so the on-screen FPS reads ~60
    when the renderer is keeping up). `cap_fps=False` runs uncapped, so the FPS
    readout shows the true achievable rate. `overlay=True` draws an FPS counter
    plus each fighter's stocks/damage."""

    def __init__(self, caption="PyCats replay", cap_fps=True, overlay=True, captions=(),
                 speed=1.0):
        import os
        os.environ.pop("SDL_VIDEODRIVER", None)
        pygame.display.quit()
        pygame.display.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()
        self.cap_fps = cap_fps
        self.overlay = overlay
        self.captions = list(captions)  # demo captions (#306); presentation overlay
        self.speed = speed              # <1 slow-mo (#351); paces the tick, not the sim

    def _draw_overlay(self, players):
        cap = "capped@60" if self.cap_fps else "uncapped"
        text_utils.render_text(
            self.screen, f"FPS: {self.clock.get_fps():.1f} ({cap})",
            (SCREEN_WIDTH - HUD_PADDING, HUD_PADDING), 24, WHITE, right_align=True)
        for i, p in enumerate(players):
            text_utils.render_text(
                self.screen,
                f"{p.char_name}: {p.fighter.lives} stocks  {int(p.fighter.percent)}%  [{p.state}]",
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
        draw_captions(self.screen, self.captions, frame)
        pygame.display.flip()
        self.clock.tick(tick_fps(self.speed)) if self.cap_fps else self.clock.tick()
        # Caption dwell (#352): freeze on a caption's start frame — keep showing the
        # same frame for `hold` more sim-frame-durations so it's readable, WITHOUT
        # advancing the sim. Events still pump so the window stays responsive/quittable.
        for _ in range(caption_hold_frames(self.captions, frame)):
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    raise KeyboardInterrupt
            self.clock.tick(tick_fps(self.speed)) if self.cap_fps else self.clock.tick()

    def close(self):
        pygame.display.quit()


class VideoPresenter:
    """Writes each frame to a video file. Requires imageio (+ imageio-ffmpeg)."""

    def __init__(self, path="battle.mp4", fps=FPS, captions=(), speed=1.0):
        try:
            import imageio.v2 as imageio
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "video mode needs imageio: pip install imageio imageio-ffmpeg"
            ) from exc
        self._imageio = imageio
        self._writer = imageio.get_writer(path, fps=fps)
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.captions = list(captions)  # demo captions (#306); presentation overlay
        # Slow-mo (#351): write each sim frame `_dup` times at the same fps, so the
        # video plays back `1/speed`x longer while staying 60fps-smooth (not choppy
        # half-fps). speed 1.0 -> 1 (unchanged).
        self._dup = frames_per_output(speed)

    def show(self, platforms, players, attacks, frame):
        self._surface.fill(BG_COLOR)
        render_battle(self._surface, players, platforms)
        render_attacks(self._surface, attacks)
        draw_captions(self._surface, self.captions, frame)
        arr = pygame.surfarray.array3d(self._surface).transpose(1, 0, 2)
        # `_dup` copies for slow-mo (#351); a caption's start frame also freezes for
        # `hold` more sim-frame-durations (#352), each of which is `_dup` video frames.
        reps = self._dup * (1 + caption_hold_frames(self.captions, frame))
        for _ in range(reps):
            self._writer.append_data(arr)

    def close(self):
        self._writer.close()

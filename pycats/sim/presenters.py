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


class ScreenshotPresenter:
    """Renders chosen frames to an off-screen Surface and saves them as PNGs — for
    visual inspection of a demo (e.g. a shot per caption). Headless: it never opens a
    window, so it works under the `dummy` SDL driver the runner sets by default.

    `frames` (a {frame: label} dict) picks which frames to save. When omitted it
    defaults to each caption's window **start** (the dwelled frame a viewer reads),
    **mid** (the beat's action, still within the window and the run), and **end**
    (clamped to the run) — so flipping through the shots shows what each beat looks
    like. A `MANIFEST.txt` maps each shot to its caption text.

    `overlay=True` draws a per-fighter stocks/%/state line (no FPS — it's a still),
    so the inspector can read what each fighter is doing in the frame."""

    def __init__(self, out_dir, captions=(), frames=None, overlay=True):
        import os
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir
        self.captions = list(captions)
        self.overlay = overlay
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._frames = frames if frames is not None else self._default_frames(self.captions)
        self.saved = []            # (frame, path) in save order — inspection manifest
        self._manifest = []        # (label, caption text) lines

    @staticmethod
    def _default_frames(captions):
        """{frame: label} for each caption's start / mid / end, plus its `dwell` frame —
        the one the presenter actually FREEZES on (#412: `dwell_at`, else the window
        start), i.e. what a viewer reads. Dedup by frame."""
        out = {}
        for i, c in enumerate(captions, 1):
            if c.frames is None:
                continue
            s, e = c.frames
            mid = (s + e) // 2
            dwell = s if c.dwell_at is None else c.dwell_at
            for tag, f in (("start", s), ("dwell", dwell), ("mid", mid), ("end", e)):
                out.setdefault(f, f"cap{i:02d}_{tag}_f{f:04d}")
        return out

    def _draw_overlay(self, players):
        for i, p in enumerate(players):
            text_utils.render_text(
                self._surface,
                f"{p.char_name}: {p.fighter.lives} stocks  {int(p.fighter.percent)}%  [{p.state}]",
                (HUD_PADDING, HUD_PADDING + i * 22), 22, WHITE)

    def show(self, platforms, players, attacks, frame):
        if frame not in self._frames:
            return
        self._surface.fill(BG_COLOR)
        render_battle(self._surface, players, platforms)
        render_attacks(self._surface, attacks)
        if self.overlay:
            self._draw_overlay(players)
        draw_captions(self._surface, self.captions, frame)
        label = self._frames[frame]
        path = f"{self.out_dir}/{label}.png"
        pygame.image.save(self._surface, path)
        self.saved.append((frame, path))
        active = " | ".join(c.text for c in self.captions if c.frames and c.frames[0] <= frame <= c.frames[1])
        self._manifest.append(f"{label}.png  (frame {frame})  captions: {active}")

    def close(self):
        if self._manifest:
            with open(f"{self.out_dir}/MANIFEST.txt", "w", encoding="utf-8") as fh:
                fh.write("\n".join(self._manifest) + "\n")

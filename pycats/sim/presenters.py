# pycats/sim/presenters.py
"""Presenters let the deterministic runner replay headless, live, or to video."""

from __future__ import annotations

import pygame

from .. import text_utils
from ..config import BG_COLOR, FPS, HUD_PADDING, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from ..input_history import InputHistory
from ..render_battle import draw_input_history, render_attacks, render_battle
from .captions import caption_hold_frames, draw_captions

# Live-replay overlay text sizes (#444: named from inline literals).
OVERLAY_FPS_FONT_SIZE = 24  # the FPS readout (top-right)
OVERLAY_STAT_FONT_SIZE = 22  # each fighter's stocks/damage line
OVERLAY_STAT_LINE_SPACING = 22  # vertical stride between fighter stat lines

# Manual-advance mode (#393): at a caption's dwell frame the presenter freezes and
# waits for one of these keys instead of the timed #352 dwell. Esc / window-close quit.
ADVANCE_KEYS = (pygame.K_SPACE, pygame.K_RIGHT)
MANUAL_HINT_TEXT = "space / right = advance    esc = quit"
OVERLAY_HINT_FONT_SIZE = 20  # the small manual-advance hint (top-centre, ASCII-safe)


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


# --- Watch/demo input display (#434) -----------------------------------------
# Reuse #21's per-fighter InputHistory + render_battle.draw_input_history in the
# presenters, instead of the reverted #405 held-only overlay. One notation, one
# component, one maintenance site — the watch path shows the same strip the live
# game (battle_screen) does.


def record_player_histories(histories, players, pressed):
    """Record this frame's press-edge into each player's InputHistory via that
    player's own keymap (``player.controls``). Pure (no surface) so the data path
    is unit-testable; the pixel draw is separate. Mirrors ``battle_screen.step``'s
    ``p1_history.record(pressed, self.p1_keys)`` — but reuses each player's controls
    (the presenter has ``players``, not the P1_KEYS/P2_KEYS globals)."""
    for hist, player in zip(histories, players):
        hist.record(pressed, player.controls)


class _InputStripMixin:
    """Optional #21 input strip for a presenter. Recording is split from drawing so
    a sampling presenter (ScreenshotPresenter) can still build a correct history every
    frame while only drawing on the frames it saves."""

    def _init_input_strip(self, show_inputs):
        self.show_inputs = show_inputs
        self._input_histories = None  # lazily sized to len(players) on first record

    def _record_input_strip(self, players, inputs):
        if not self.show_inputs or inputs is None:
            return
        if self._input_histories is None:
            self._input_histories = [InputHistory() for _ in players]
        pressed = getattr(inputs, "pressed", None) or ()
        record_player_histories(self._input_histories, players, pressed)

    def _draw_input_strip(self, surface):
        if not self.show_inputs or not self._input_histories:
            return
        for i, hist in enumerate(self._input_histories):
            draw_input_history(surface, hist, f"P{i + 1}", topright=(i == 1))


class HeadlessPresenter:
    def show(self, platforms, players, attacks, frame, inputs=None): ...
    def close(self): ...


class LivePresenter(_InputStripMixin):
    """Opens a real window and renders the replay.

    `cap_fps=True` paces the window to 60 FPS (so the on-screen FPS reads ~60
    when the renderer is keeping up). `cap_fps=False` runs uncapped, so the FPS
    readout shows the true achievable rate. `overlay=True` draws an FPS counter
    plus each fighter's stocks/damage. `show_inputs=True` adds the #21 input strip
    (#434), same as the live game."""

    def __init__(
        self,
        caption="PyCats replay",
        cap_fps=True,
        overlay=True,
        captions=(),
        speed=1.0,
        interactive=None,
        show_inputs=False,
    ):
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
        self.speed = speed  # <1 slow-mo (#351); paces the tick, not the sim
        # Interactivity (#393): "manual" makes each caption's dwell frame wait for an
        # advance key (self-paced reading) instead of the timed #352 dwell. None = off.
        self.interactive = interactive
        self._init_input_strip(show_inputs)  # #434 input strip (default off)

    def _draw_overlay(self, players):
        cap = "capped@60" if self.cap_fps else "uncapped"
        text_utils.render_text(
            self.screen,
            f"FPS: {self.clock.get_fps():.1f} ({cap})",
            (SCREEN_WIDTH - HUD_PADDING, HUD_PADDING),
            OVERLAY_FPS_FONT_SIZE,
            WHITE,
            right_align=True,
        )
        for i, p in enumerate(players):
            text_utils.render_text(
                self.screen,
                f"{p.char_name}: {p.fighter.lives} stocks  {int(p.fighter.percent)}%  [{p.state}]",
                (HUD_PADDING, HUD_PADDING + i * OVERLAY_STAT_LINE_SPACING),
                OVERLAY_STAT_FONT_SIZE,
                WHITE,
            )

    def _tick(self):
        """Advance the display clock one frame at the current speed (#351)."""
        self.clock.tick(tick_fps(self.speed)) if self.cap_fps else self.clock.tick()

    @staticmethod
    def _consume_advance(events):
        """Classify a batch of pygame events for manual-advance mode (#393):
        ``"advance"`` on Space/Right, ``"quit"`` on Esc or window-close, else
        ``None`` (keep waiting). Pure — no window/loop, so it's unit-testable."""
        for ev in events:
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in ADVANCE_KEYS:
                    return "advance"
                if ev.key == pygame.K_ESCAPE:
                    return "quit"
        return None

    @staticmethod
    def _dwell_interrupt(events):
        """Classify a batch of pygame events for the timed dwell (#514):
        ``"skip"`` on **any** KEYDOWN (end the remaining dwell early), ``"quit"``
        on window-close, else ``None`` (keep counting down). Pure — no window/loop,
        so it's unit-testable; mirrors ``_consume_advance``. This is the CLI-near-term
        slice of #507's shared interaction reducer: interruptibility is a property of
        the dwell itself, so any key — not a designated advance key — ends it."""
        for ev in events:
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                return "skip"
        return None

    def _draw_manual_hint(self):
        """Small ASCII hint (top-centre, clear of bottom captions + the corner
        overlays) shown while a manual pause is held (#393)."""
        text_utils.render_text(
            self.screen, MANUAL_HINT_TEXT, (SCREEN_WIDTH // 2, HUD_PADDING), OVERLAY_HINT_FONT_SIZE, WHITE, center=True
        )

    def _wait_for_advance(self):
        """Freeze on the current frame until the viewer presses an advance key
        (#393). Space/Right resume; Esc or window-close raise KeyboardInterrupt.
        Draws the hint over the frozen frame and keeps ticking so the window stays
        responsive. The sim frame never advances — the runner is blocked inside this
        one show() call, so this is a pure presentation freeze (golden-safe)."""
        self._draw_manual_hint()
        pygame.display.flip()
        while True:
            action = self._consume_advance(pygame.event.get())
            if action == "advance":
                return
            if action == "quit":
                raise KeyboardInterrupt
            self._tick()

    def _hold(self, frame):
        """Freeze on a caption's dwell frame (#352). Manual mode (#393) waits for an
        advance key instead of the timed hold — the exit condition is generalized
        from a tick count to a keypress. No hold on a non-dwell frame."""
        hold = caption_hold_frames(self.captions, frame)
        if not hold:
            return
        if self.interactive == "manual":
            self._wait_for_advance()
            return
        # Timed dwell: keep showing the same frame for `hold` more sim-frame-durations
        # WITHOUT advancing the sim. Events still pump so the window stays quittable, and
        # any key ends the remaining dwell early (#514) — the dwell stays timed (it still
        # auto-advances after `hold`), a keypress only skips the rest of the wait. Non-
        # interactive playback gets an empty queue every tick -> full `hold` (golden-safe).
        for _ in range(hold):
            action = self._dwell_interrupt(pygame.event.get())
            if action == "quit":
                raise KeyboardInterrupt
            if action == "skip":
                return
            self._tick()

    def show(self, platforms, players, attacks, frame, inputs=None):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                raise KeyboardInterrupt
        self.screen.fill(BG_COLOR)
        render_battle(self.screen, players, platforms)
        render_attacks(self.screen, attacks)
        if self.overlay:
            self._draw_overlay(players)
        self._record_input_strip(players, inputs)  # #434
        self._draw_input_strip(self.screen)
        draw_captions(self.screen, self.captions, frame)
        pygame.display.flip()
        self._tick()
        self._hold(frame)

    def close(self):
        pygame.display.quit()


class VideoPresenter(_InputStripMixin):
    """Writes each frame to a video file. Requires imageio (+ imageio-ffmpeg)."""

    def __init__(self, path="battle.mp4", fps=FPS, captions=(), speed=1.0, show_inputs=False):
        try:
            import imageio.v2 as imageio
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError("video mode needs imageio: pip install imageio imageio-ffmpeg") from exc
        self._imageio = imageio
        self._writer = imageio.get_writer(path, fps=fps)
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.captions = list(captions)  # demo captions (#306); presentation overlay
        # Slow-mo (#351): write each sim frame `_dup` times at the same fps, so the
        # video plays back `1/speed`x longer while staying 60fps-smooth (not choppy
        # half-fps). speed 1.0 -> 1 (unchanged).
        self._dup = frames_per_output(speed)
        self._init_input_strip(show_inputs)  # #434 input strip (default off)

    def show(self, platforms, players, attacks, frame, inputs=None):
        self._surface.fill(BG_COLOR)
        render_battle(self._surface, players, platforms)
        render_attacks(self._surface, attacks)
        self._record_input_strip(players, inputs)  # #434
        self._draw_input_strip(self._surface)
        draw_captions(self._surface, self.captions, frame)
        arr = pygame.surfarray.array3d(self._surface).transpose(1, 0, 2)
        # `_dup` copies for slow-mo (#351); a caption's start frame also freezes for
        # `hold` more sim-frame-durations (#352), each of which is `_dup` video frames.
        reps = self._dup * (1 + caption_hold_frames(self.captions, frame))
        for _ in range(reps):
            self._writer.append_data(arr)

    def close(self):
        self._writer.close()


class ScreenshotPresenter(_InputStripMixin):
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

    def __init__(self, out_dir, captions=(), frames=None, overlay=True, show_inputs=False):
        import os

        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir
        self.captions = list(captions)
        self.overlay = overlay
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._frames = frames if frames is not None else self._default_frames(self.captions)
        self.saved = []  # (frame, path) in save order — inspection manifest
        self._manifest = []  # (label, caption text) lines
        self._init_input_strip(show_inputs)  # #434 input strip (default off)

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
                (HUD_PADDING, HUD_PADDING + i * 22),
                22,
                WHITE,
            )

    def show(self, platforms, players, attacks, frame, inputs=None):
        # Record every frame so a saved frame's strip reflects the full recent history,
        # even though only selected frames are rendered (#434).
        self._record_input_strip(players, inputs)
        if frame not in self._frames:
            return
        self._surface.fill(BG_COLOR)
        render_battle(self._surface, players, platforms)
        render_attacks(self._surface, attacks)
        if self.overlay:
            self._draw_overlay(players)
        self._draw_input_strip(self._surface)  # #434
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

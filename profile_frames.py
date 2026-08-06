# profile_frames.py
"""Headed frame-rate + freeze logger for the live game loop (#1241, tooling for #1236).

Boots the real game window exactly like `pycats.game.main()` and drives the loop itself,
timing every `App.step()`. Where `bench.py` profiles the headless sim, this profiles the
*live headed game* and logs stalls, to hunt the intermittent 1-2s freezes (#1236).

It writes (to a --log file, line-buffered so a hard hang still leaves the record, and stdout):

  * a per-second FPS summary (avg + worst frame that second, with the active FSM state),
  * one line per SLOW frame (a single step over --slow-ms), tagged with the FSM state it was
    in -- this is the "one frame took seconds" record,
  * a FREEZE line while a frame is *still* stuck (a separate thread notices a freeze in
    progress, so a 1-2s hang is logged even before the frame returns -- and a hang that never
    returns is still logged), plus a "resolved" slowframe line when it finally returns.

Freeze *duration* is not the whole story. The #1241 capture held ~50 FPS with no slow frame,
yet the screen was frozen -- the loop kept completing frames fast while nothing on screen moved.
A duration threshold cannot see that. So this also does NO-PROGRESS detection:

  * loop heartbeat (_Watchdog) -- if the loop stops completing frames for --no-progress-ms while
    no single frame is in flight (wedged between frames), log NO-PROGRESS. Fills the gap the
    in-flight FREEZE path leaves (it only fires while a frame is running).
  * render stall (_VisualStall) -- in a motion-expected state (--watch-states, default
    `playing`), fingerprint the rendered surface each frame; if it stops changing for
    --no-progress-ms, log NO-PROGRESS. This is the freeze the captured run missed: fast frames,
    frozen picture.

A legitimately static screen (an idle menu) is expected to hold a still image, so render-stall
is gated to --watch-states (states where the picture *should* be moving). Two limits to know:
the loop heartbeat is a Python thread, so a true hang that holds the GIL without releasing it
can starve it (a SIGALRM/subprocess watchdog would be needed for that); and if the OS compositor
stops repainting a window whose surface *is* still changing, the fingerprint won't catch it.

Nothing in pycats/ is modified -- this only wraps the public App.step() loop. Play the game
normally; reproduce the freeze; then read the log.

Usage (headed, from the repo root, with the venv python):
    python profile_frames.py --log frames.log
    python profile_frames.py --log frames.log --slow-ms 80 --freeze-ms 400
    python profile_frames.py --no-progress-ms 400 --watch-states playing,options
    python profile_frames.py --max-frames 300   # bounded (testing)
"""

from __future__ import annotations

import argparse
import platform
import sys
import threading
import time

import pygame  # type: ignore

from pycats.shell.app import App
from pycats.storage import runtime_settings, settings


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="profile_frames", description=__doc__)
    ap.add_argument("--log", default="frames.log", help="log file path (default: frames.log)")
    ap.add_argument(
        "--slow-ms",
        type=float,
        default=100.0,
        help="log any single frame slower than this many ms (default: 100)",
    )
    ap.add_argument(
        "--freeze-ms",
        type=float,
        default=500.0,
        help="watchdog: report a frame still running past this many ms (default: 500)",
    )
    ap.add_argument(
        "--no-progress-ms",
        type=float,
        default=400.0,
        help="report a stalled loop / frozen render surface after this many ms with no forward progress (default: 400)",
    )
    ap.add_argument(
        "--watch-states",
        default="playing",
        help="comma-separated FSM states where the picture SHOULD be moving; render-stall "
        "detection runs only in these (default: playing)",
    )
    ap.add_argument(
        "--summary-sec",
        type=float,
        default=1.0,
        help="seconds between FPS summary lines (default: 1.0)",
    )
    ap.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="stop after N frames (0 = run until you quit the window)",
    )
    ap.add_argument("--speed", type=float, default=1.0, help="present-rate factor, passed to App")
    return ap.parse_args(argv)


class _Sink:
    """Writes each line to both the log file (flushed immediately, so a hard hang still
    leaves the last lines on disk) and stdout."""

    def __init__(self, path):
        self._fh = open(path, "w", buffering=1, encoding="utf-8")  # line-buffered
        self.path = path

    def line(self, msg):
        stamp = f"{time.perf_counter():10.3f}"
        text = f"[{stamp}] {msg}"
        self._fh.write(text + "\n")
        self._fh.flush()
        print(text, flush=True)

    def close(self):
        self._fh.close()


class _Watchdog(threading.Thread):
    """A daemon thread that logs a freeze WHILE it is happening.

    The main loop stamps `frame_start`, `frame_no`, `state`, and toggles `in_frame` around
    each App.step(). This thread wakes often and, if a frame has been in flight longer than
    freeze_ms, logs it (once, plus a heartbeat each additional freeze_ms) -- capturing a hang
    the after-the-fact timer would only see once/if it returns."""

    def __init__(self, shared, sink, freeze_ms, no_progress_ms=None, poll_ms=50.0):
        super().__init__(daemon=True)
        self.s = shared
        self.sink = sink
        self.freeze_s = freeze_ms / 1000.0
        # None => heartbeat disabled (the isolated FREEZE-only tests use this).
        self.no_progress_s = None if no_progress_ms is None else no_progress_ms / 1000.0
        self.poll_s = poll_ms / 1000.0
        self._reported_at = 0.0  # frame_start of the freeze already reported
        self._last_beat = 0.0
        self._np_reported_at = None  # last_progress value already reported as a wedge

    def run(self):
        while not self.s["stop"]:
            time.sleep(self.poll_s)
            if not self.s["in_frame"]:
                # Between frames. The in-flight FREEZE path can't fire here (no frame is
                # running), so a loop that stops COMPLETING frames would go unreported.
                # Heartbeat: last_progress is bumped after each finished frame; if it stops
                # advancing, the loop has wedged.
                if self.no_progress_s is not None:
                    last = self.s.get("last_progress")
                    if last is not None:
                        idle = time.perf_counter() - last
                        if idle >= self.no_progress_s and self._np_reported_at != last:
                            self._np_reported_at = last
                            self.sink.line(
                                f"NO-PROGRESS frame={self.s['frame_no']} state={self.s['state']!r} "
                                f"loop stalled {idle:5.2f}s (no frame completed)"
                            )
                continue
            start = self.s["frame_start"]
            stuck = time.perf_counter() - start
            if stuck < self.freeze_s:
                continue
            # Still inside the same frame that we haven't fully reported yet.
            if self._reported_at != start:
                self._reported_at = start
                self._last_beat = stuck
                self.sink.line(
                    f"FREEZE  frame={self.s['frame_no']} state={self.s['state']!r} stuck {stuck:5.2f}s and counting..."
                )
            elif stuck - self._last_beat >= self.freeze_s:
                self._last_beat = stuck
                self.sink.line(
                    f"FREEZE  frame={self.s['frame_no']} state={self.s['state']!r} still stuck {stuck:5.2f}s..."
                )


def _fingerprint(surface, grid=8):
    """A cheap, allocation-light fingerprint of what's on screen: a fixed grid of pixel
    samples hashed together. A live battle moves many of these every frame; a frozen screen
    keeps them all identical. Sampling a grid (not one point) avoids a false "frozen" when the
    few sampled points happen to sit on unchanging background. Returns None if there's no
    surface to read."""
    if surface is None:
        return None
    w, h = surface.get_size()
    if w == 0 or h == 0:
        return None
    step_x = max(1, w // grid)
    step_y = max(1, h // grid)
    vals = []
    surface.lock()
    try:
        for y in range(step_y // 2, h, step_y):
            for x in range(step_x // 2, w, step_x):
                vals.append(tuple(surface.get_at((x, y))))
    finally:
        surface.unlock()
    return hash(tuple(vals))


class _VisualStall:
    """Detects a frozen render loop that the per-frame *duration* checks can't see.

    The #1241 capture held ~50 FPS with no slow frame while the screen was frozen: the loop
    kept completing frames fast, but nothing on screen moved. In a motion-expected state
    (watch_states), a surface fingerprint that stops changing for longer than no_progress_ms
    means the picture is frozen even though every frame is quick. A legitimately static screen
    (an idle menu) is expected to hold a still image, so states outside watch_states are
    ignored -- otherwise every idle menu would read as a freeze."""

    def __init__(self, sink, no_progress_ms, watch_states):
        self.sink = sink
        self.no_progress_s = no_progress_ms / 1000.0
        self.watch_states = set(watch_states)
        self._last_fp = None
        self._since = None  # perf_counter when the surface last changed
        self._reported = False

    def sample(self, fp, *, frame_no, state, now):
        # Outside a watched state, or with no surface, a still picture is expected: reset.
        if state not in self.watch_states or fp is None:
            self._last_fp = fp
            self._since = now
            self._reported = False
            return
        if fp != self._last_fp:
            self._last_fp = fp
            self._since = now
            self._reported = False
            return
        # Same picture as last frame while motion was expected.
        if self._since is None:
            self._since = now
            return
        stuck = now - self._since
        if stuck >= self.no_progress_s and not self._reported:
            self._reported = True
            self.sink.line(
                f"NO-PROGRESS frame={frame_no} state={state!r} render frozen {stuck:5.2f}s (surface unchanged)"
            )


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

    pygame.init()
    pygame.display.set_caption("PyCats - FRAME PROFILER (#1236)")

    prefs = settings.load()
    runtime_settings.seed(prefs)
    app = App(prefs=prefs, speed=args.speed)

    watch_states = [s.strip() for s in args.watch_states.split(",") if s.strip()]

    sink = _Sink(args.log)
    sink.line(
        f"start python={platform.python_version()} platform={platform.system()} "
        f"slow_ms={args.slow_ms} freeze_ms={args.freeze_ms} no_progress_ms={args.no_progress_ms} "
        f"watch_states={watch_states} log={sink.path}"
    )

    shared = {
        "frame_start": time.perf_counter(),
        "frame_no": 0,
        "state": "?",
        "in_frame": False,
        "last_progress": time.perf_counter(),
        "stop": False,
    }
    watchdog = _Watchdog(shared, sink, args.freeze_ms, no_progress_ms=args.no_progress_ms)
    watchdog.start()
    stall = _VisualStall(sink, args.no_progress_ms, watch_states)

    window = []  # dts (ms) accumulated in the current summary window
    window_open = time.perf_counter()
    frame_no = 0
    try:
        while app.running:
            frame_no += 1
            try:
                state = app.screen_manager.get_state()
            except Exception:
                state = "?"
            shared["frame_no"] = frame_no
            shared["state"] = state
            shared["frame_start"] = time.perf_counter()
            shared["in_frame"] = True

            t0 = time.perf_counter()
            app.step()
            dt_ms = (time.perf_counter() - t0) * 1000.0

            shared["in_frame"] = False
            now = time.perf_counter()
            shared["last_progress"] = now  # heartbeat: a frame just completed
            window.append(dt_ms)

            # Render-stall: fingerprint the presented surface (only in watched states, to keep
            # the cost off the states we don't check). Catches a frozen picture behind fast
            # frames -- the freeze the duration checks miss.
            if state in stall.watch_states:
                fp = _fingerprint(pygame.display.get_surface())
                stall.sample(fp, frame_no=frame_no, state=state, now=now)

            # A frame that took much longer than the ~16.7ms budget = a stall.
            if dt_ms > args.slow_ms:
                sink.line(f"slowframe frame={frame_no} dt={dt_ms:7.1f}ms state={state!r}")

            if now - window_open >= args.summary_sec and window:
                span = now - window_open
                fps = len(window) / span
                worst = max(window)
                avg = sum(window) / len(window)
                sink.line(
                    f"fps      {fps:5.1f}  frames={len(window):3d}  "
                    f"avg={avg:5.1f}ms worst={worst:7.1f}ms state={state!r}"
                )
                window.clear()
                window_open = now

            if args.max_frames and frame_no >= args.max_frames:
                break
    finally:
        shared["stop"] = True
        sink.line(f"stop frames={frame_no}")
        sink.close()
        pygame.quit()


if __name__ == "__main__":
    main()

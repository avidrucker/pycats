# profile_frames.py
"""Headed frame-rate + freeze logger for the live game loop (#1241, tooling for #1236).

Boots the real game window exactly like `pycats.game.main()` and drives the loop itself,
timing every `App.step()`. Where `bench.py` profiles the headless sim, this profiles the
*live headed game* and logs stalls, to hunt the intermittent 1-2s freezes (#1236).

It writes (to a --log file, line-buffered so a hard hang still leaves the record, and stdout):

  * a per-second FPS summary (avg + worst frame that second, with the active FSM state),
  * one line per SLOW frame (a single step over --slow-ms), tagged with the FSM state it was
    in -- this is the "the game froze" record,
  * a WATCHDOG line while a frame is *still* stuck (a separate thread notices a freeze in
    progress, so a 1-2s hang is logged even before the frame returns -- and a hang that never
    returns is still logged), plus a "resolved" slowframe line when it finally returns.

Nothing in pycats/ is modified -- this only wraps the public App.step() loop. Play the game
normally; reproduce the freeze; then read the log.

Usage (headed, from the repo root, with the venv python):
    python profile_frames.py --log frames.log
    python profile_frames.py --log frames.log --slow-ms 80 --freeze-ms 400
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

    def __init__(self, shared, sink, freeze_ms, poll_ms=50.0):
        super().__init__(daemon=True)
        self.s = shared
        self.sink = sink
        self.freeze_s = freeze_ms / 1000.0
        self.poll_s = poll_ms / 1000.0
        self._reported_at = 0.0  # frame_start of the freeze already reported
        self._last_beat = 0.0

    def run(self):
        while not self.s["stop"]:
            time.sleep(self.poll_s)
            if not self.s["in_frame"]:
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


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

    pygame.init()
    pygame.display.set_caption("PyCats - FRAME PROFILER (#1236)")

    prefs = settings.load()
    runtime_settings.seed(prefs)
    app = App(prefs=prefs, speed=args.speed)

    sink = _Sink(args.log)
    sink.line(
        f"start python={platform.python_version()} platform={platform.system()} "
        f"slow_ms={args.slow_ms} freeze_ms={args.freeze_ms} log={sink.path}"
    )

    shared = {
        "frame_start": time.perf_counter(),
        "frame_no": 0,
        "state": "?",
        "in_frame": False,
        "stop": False,
    }
    watchdog = _Watchdog(shared, sink, args.freeze_ms)
    watchdog.start()

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
            window.append(dt_ms)

            # A frame that took much longer than the ~16.7ms budget = a stall.
            if dt_ms > args.slow_ms:
                sink.line(f"slowframe frame={frame_no} dt={dt_ms:7.1f}ms state={state!r}")

            now = time.perf_counter()
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

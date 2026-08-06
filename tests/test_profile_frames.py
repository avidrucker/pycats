"""DEV (#1241) — the headed frame/freeze profiler's detection logic.

`profile_frames.py` is a diagnostic entry point (sibling to bench.py/watch.py) that wraps the
live `App.step()` loop to hunt the #1236 intermittent 1-2s freezes. The risk surface is its
stall detection:

  (a) the after-the-fact `slowframe` line for a frame that exceeded the slow threshold,
  (b) the `_Watchdog` thread's `FREEZE` line emitted *while a frame is still stuck*,
  (c) the `_Watchdog`'s `NO-PROGRESS` line when the loop stops completing frames while no
      single frame is in flight (a wedge the in-flight `FREEZE` path misses), and
  (d) `_VisualStall`'s `NO-PROGRESS` line when the loop keeps completing frames fast but the
      rendered surface stops changing -- the freeze the per-frame *duration* checks cannot see
      (each frame is quick; the screen just doesn't move). This is the case the captured
      #1241 run missed: steady ~50 FPS, no slow frame, yet the screen was frozen.

These drive each detector over synthetic input — no window, no real App — and assert the log
records land. Red without `_Watchdog`/`_Sink`/`_VisualStall` (import fails); red if any
detector stops writing its line.
"""

from __future__ import annotations

import time

from profile_frames import _Sink, _VisualStall, _Watchdog


def _run_one_frame(shared, sink, *, state, sleep_s, slow_ms):
    """Replicate one iteration of profile_frames.main()'s loop body over a fake step that
    just sleeps, so the test controls exactly how long the frame 'takes'."""
    shared["frame_no"] += 1
    shared["state"] = state
    shared["frame_start"] = time.perf_counter()
    shared["in_frame"] = True
    t0 = time.perf_counter()
    time.sleep(sleep_s)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    shared["in_frame"] = False
    if dt_ms > slow_ms:
        sink.line(f"slowframe frame={shared['frame_no']} dt={dt_ms:7.1f}ms state={state!r}")


def test_watchdog_and_slowframe_log_a_stalled_frame(tmp_path):
    log = tmp_path / "frames.log"
    sink = _Sink(str(log))
    shared = {
        "frame_start": time.perf_counter(),
        "frame_no": 0,
        "state": "?",
        "in_frame": False,
        "stop": False,
    }
    watchdog = _Watchdog(shared, sink, freeze_ms=100.0, poll_ms=20.0)
    watchdog.start()
    try:
        # A normal frame: under both thresholds -> produces no slowframe/FREEZE line.
        _run_one_frame(shared, sink, state="main_menu", sleep_s=0.01, slow_ms=100.0)
        # A 0.35s stall: long enough for the 20ms-poll watchdog to catch it in-flight past
        # freeze_ms=100, and for the after-the-fact slow check to fire on return.
        _run_one_frame(shared, sink, state="options", sleep_s=0.35, slow_ms=100.0)
    finally:
        shared["stop"] = True
        watchdog.join(timeout=1.0)
        sink.close()

    text = log.read_text()
    # (a) the watchdog logged the freeze WHILE it was still stuck, tagged with the FSM state
    assert "FREEZE  frame=2 state='options'" in text
    # (b) the completed slow frame logged after it returned
    assert "slowframe frame=2" in text
    assert "state='options'" in text
    # the normal frame tripped neither detector
    assert "frame=1" not in text


def test_visualstall_logs_a_frozen_render_surface():
    """The captured #1241 run held ~50 FPS with no slow frame, yet the screen was frozen.
    _VisualStall catches that: in a watched (motion-expected) state, a rendered-surface
    fingerprint that stops changing for longer than no_progress_ms is a frozen render loop
    even though every frame completes fast. Red without _VisualStall; red if it stops
    writing NO-PROGRESS."""

    import io

    class _Cap:
        def __init__(self):
            self.buf = io.StringIO()

        def line(self, msg):
            self.buf.write(msg + "\n")

    sink = _Cap()
    stall = _VisualStall(sink, no_progress_ms=100.0, watch_states=["playing"])
    t = 1000.0  # synthetic perf_counter clock (no real sleeping)

    # Screen is changing frame to frame -> live, nothing reported.
    stall.sample(hash("scene-a"), frame_no=1, state="playing", now=t)
    stall.sample(hash("scene-b"), frame_no=2, state="playing", now=t + 0.02)
    assert sink.buf.getvalue() == ""

    # Then the surface freezes: identical fingerprint across a >100ms span while still
    # in 'playing'. Every "frame" is fast; only the *content* stopped moving.
    frozen = hash("scene-frozen")
    stall.sample(frozen, frame_no=3, state="playing", now=t + 0.04)  # freeze begins
    stall.sample(frozen, frame_no=4, state="playing", now=t + 0.09)  # 0.05s unchanged
    assert sink.buf.getvalue() == ""  # under threshold, not yet reported
    stall.sample(frozen, frame_no=5, state="playing", now=t + 0.20)  # 0.16s unchanged

    text = sink.buf.getvalue()
    assert "NO-PROGRESS frame=5 state='playing'" in text
    assert "render frozen" in text
    assert "surface unchanged" in text


def test_visualstall_ignores_a_legitimately_static_menu():
    """A static menu (a state NOT in watch_states) is expected to hold a still image, so an
    unchanging surface there must NOT be flagged -- otherwise every idle menu reads as a
    freeze. Guards the motion-expected gate."""

    import io

    class _Cap:
        def __init__(self):
            self.buf = io.StringIO()

        def line(self, msg):
            self.buf.write(msg + "\n")

    sink = _Cap()
    stall = _VisualStall(sink, no_progress_ms=100.0, watch_states=["playing"])
    same = hash("still-menu")
    stall.sample(same, frame_no=1, state="main_menu", now=2000.0)
    stall.sample(same, frame_no=2, state="main_menu", now=2000.5)  # 0.5s unchanged, but gated

    assert sink.buf.getvalue() == ""


def test_watchdog_logs_no_progress_when_loop_wedges_between_frames():
    """The in-flight FREEZE path only fires while a frame is *running* (in_frame True). If the
    loop stops completing frames while in_frame is False -- wedged in the summary/logging code,
    or the loop simply stops iterating -- no frame is 'in flight', so FREEZE never fires. The
    heartbeat catches it: last_progress stops advancing. Red without the heartbeat branch."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        log = f"{d}/frames.log"
        sink = _Sink(log)
        shared = {
            "frame_start": time.perf_counter(),
            "frame_no": 7,
            "state": "playing",
            "in_frame": False,
            "last_progress": time.perf_counter(),
            "stop": False,
        }
        watchdog = _Watchdog(shared, sink, freeze_ms=1000.0, no_progress_ms=100.0, poll_ms=20.0)
        watchdog.start()
        try:
            # The loop has wedged: in_frame stays False and last_progress is never bumped.
            time.sleep(0.30)
        finally:
            shared["stop"] = True
            watchdog.join(timeout=1.0)
            sink.close()

        text = open(log, encoding="utf-8").read()
        assert "NO-PROGRESS frame=7 state='playing'" in text
        assert "loop stalled" in text
        # The in-flight FREEZE path must NOT fire -- no frame was ever in flight.
        assert "FREEZE" not in text

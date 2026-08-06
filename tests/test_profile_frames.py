"""DEV (#1241) — the headed frame/freeze profiler's detection logic.

`profile_frames.py` is a diagnostic entry point (sibling to bench.py/watch.py) that wraps the
live `App.step()` loop to hunt the #1236 intermittent 1-2s freezes. The risk surface is its
stall detection: (a) the after-the-fact `slowframe` line for a frame that exceeded the slow
threshold, and (b) the `_Watchdog` thread's `FREEZE` line emitted *while a frame is still
stuck*. This drives both over a synthetic stalled frame — no window, no real App — and asserts
the log records land. Red without `_Watchdog`/`_Sink` (import fails); red if either detector
stops writing its line.
"""

from __future__ import annotations

import time

from profile_frames import _Sink, _Watchdog


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

"""Shared hold-Esc timer (#515, design #507 §3b).

`EscHoldTimer` is the pure frame-counter lifted out of `ScreenStateManager`
(#453/#113): count frames while Esc is held, reset on release, fire at a fixed
threshold, expose a 0..1 progress for the arc. Both surfaces — the in-game screen
ladder and the CLI demo/sim playback — tick the SAME timer, so they share one
threshold and one progress semantic. Pure (no pygame/window/clock), so it is
unit-testable and behaves identically on both surfaces by construction.
"""

from pycats.esc_hold import EscHoldTimer


def test_starts_incomplete_at_zero_progress():
    t = EscHoldTimer(hold_frames=4)
    assert not t.complete
    assert t.progress == 0.0


def test_counts_held_frames_to_completion():
    t = EscHoldTimer(hold_frames=4)
    for _ in range(4):
        t.tick(held=True)
    assert t.complete
    assert t.progress == 1.0


def test_partial_hold_is_incomplete_with_fractional_progress():
    t = EscHoldTimer(hold_frames=4)
    t.tick(held=True)
    t.tick(held=True)
    assert not t.complete
    assert t.progress == 0.5


def test_release_resets_the_count():
    t = EscHoldTimer(hold_frames=4)
    t.tick(held=True)
    t.tick(held=True)
    t.tick(held=False)  # released before the threshold
    assert t.progress == 0.0
    assert not t.complete


def test_reset_zeroes_the_count():
    t = EscHoldTimer(hold_frames=4)
    for _ in range(3):
        t.tick(held=True)
    t.reset()
    assert t.progress == 0.0
    assert not t.complete


def test_progress_caps_at_one_past_threshold():
    t = EscHoldTimer(hold_frames=4)
    for _ in range(10):  # held well past the threshold
        t.tick(held=True)
    assert t.complete
    assert t.progress == 1.0


def test_zero_threshold_reports_zero_progress():
    # Guard the div-by-zero the old esc_quit_progress() had (#453).
    t = EscHoldTimer(hold_frames=0)
    t.tick(held=True)
    assert t.progress == 0.0

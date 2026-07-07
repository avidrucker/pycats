"""Interruptible timed dwell (#514, epic #308, design #507 §3a).

A caption pause stays a TIMED dwell (#352) — it still auto-advances on its own
after `dwell` frames — but pressing **any key** ends the *remaining* dwell at once
and playback resumes. "Do nothing -> it advances itself; press anything -> skip the
rest of the wait." This is the CLI-near-term slice of #507's shared reducer: the
any-key decision lives in a pure classifier (`LivePresenter._dwell_interrupt`),
unit-testable with no window/loop.

Golden-safe: non-interactive playback feeds the loop an empty event queue every
tick -> the dwell always runs its full `caption_hold_frames` -> identical to today.

Hold-Esc-2s exit is #515 (out of scope here); this slice only permits an early exit.
"""


import pygame as pg
import pytest

import pycats.sim.presenters as pr
from pycats.esc_hold import EscHoldTimer
from pycats.sim.captions import Caption
from pycats.sim.presenters import LivePresenter


@pytest.fixture(autouse=True)
def _pg():
    pg.init()


def _timed_presenter(captions, cap_fps=False):
    """A LivePresenter with just the attributes the timed-dwell loop needs, built via
    __new__ so no real window opens (mirrors test_cli_hold_esc._presenter). The dwell
    loop also services the #515 hold-Esc timer each tick, so it needs `_esc_hold`."""
    p = LivePresenter.__new__(LivePresenter)
    p.screen = pg.Surface((320, 180))
    p.clock = pg.time.Clock()
    p.cap_fps = cap_fps
    p.overlay = False
    p.speed = 1.0
    p.captions = list(captions)
    p._esc_hold = EscHoldTimer()
    p._init_input_strip(False)
    return p


# --- the pure any-key/quit classifier -----------------------------------------

def test_dwell_interrupt_skips_on_any_keydown():
    # "Any key" is literal: Space, a letter, Esc — every KEYDOWN ends the dwell.
    assert LivePresenter._dwell_interrupt([pg.event.Event(pg.KEYDOWN, key=pg.K_SPACE)]) == "skip"
    assert LivePresenter._dwell_interrupt([pg.event.Event(pg.KEYDOWN, key=pg.K_a)]) == "skip"
    assert LivePresenter._dwell_interrupt([pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)]) == "skip"


def test_dwell_interrupt_quits_on_window_close():
    assert LivePresenter._dwell_interrupt([pg.event.Event(pg.QUIT)]) == "quit"


def test_dwell_interrupt_none_on_no_events():
    # No input -> keep counting down the timed dwell (this is the golden-safe path).
    assert LivePresenter._dwell_interrupt([]) is None


# --- the timed-dwell loop: full count untouched, early exit on a key ----------

def _event_source(trigger_call, events):
    """A drop-in for pygame.event.get that returns `events` only on the
    `trigger_call`-th invocation (0-indexed), else []."""
    calls = {"n": 0}

    def get():
        i = calls["n"]
        calls["n"] += 1
        return list(events) if i == trigger_call else []

    return get


def test_untouched_dwell_runs_its_full_count(monkeypatch):
    # No key ever arrives -> the loop ticks the caption's full dwell (10), exactly as
    # the timed #352 dwell did before #514. This is the byte-identical golden path.
    monkeypatch.setattr(pr.pygame.event, "get", lambda: [])
    p = _timed_presenter([Caption("beat", frames=(0, 5), dwell=10)])
    ticks = {"n": 0}
    p._tick = lambda: ticks.__setitem__("n", ticks["n"] + 1)

    p._hold(0)  # frame 0 is the dwell frame
    assert ticks["n"] == 10, "untouched timed dwell must run its full count"


def test_any_key_ends_remaining_dwell_early(monkeypatch):
    # A KEYDOWN on tick k=3 (< dwell=10) ends the remaining dwell: the loop stops at 3
    # ticks, not 10. Red without the early-break (would run all 10), green with it.
    p = _timed_presenter([Caption("beat", frames=(0, 5), dwell=10)])
    ticks = {"n": 0}
    p._tick = lambda: ticks.__setitem__("n", ticks["n"] + 1)
    monkeypatch.setattr(
        pr.pygame.event, "get", _event_source(3, [pg.event.Event(pg.KEYDOWN, key=pg.K_j)])
    )

    p._hold(0)
    assert ticks["n"] == 3, "any key must end the remaining dwell at once"


def test_window_close_during_dwell_still_quits(monkeypatch):
    # QUIT must keep quitting the run (raise KeyboardInterrupt) — #514 doesn't weaken it.
    p = _timed_presenter([Caption("beat", frames=(0, 5), dwell=10)])
    p._tick = lambda: None
    monkeypatch.setattr(
        pr.pygame.event, "get", _event_source(0, [pg.event.Event(pg.QUIT)])
    )
    with pytest.raises(KeyboardInterrupt):
        p._hold(0)

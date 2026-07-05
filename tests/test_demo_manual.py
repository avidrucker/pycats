"""Manual-advance demo mode (#393, epic #308, child of spike #355).

`watch.py --demo … --demo-manual` makes the live presenter PAUSE on each caption's
dwell frame and wait for the viewer to press an advance key (Space/Right), instead of
the timed #352 dwell — self-paced caption reading. Presenter-only, golden-safe: the
sim frame never advances during the hold (the runner is blocked inside one show()).

Tested headlessly: the freeze loop is driven with synthesized pygame events (no live
window / no timer wait), mirroring test_caption_dwell.py's monkeypatch style.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg
import pytest

import pycats.sim.presenters as pr
from pycats.sim.captions import Caption
from pycats.sim.presenters import LivePresenter


@pytest.fixture(autouse=True)
def _pg():
    pg.init()


def _manual_presenter(captions, interactive="manual", cap_fps=False):
    """A LivePresenter with just the attributes the freeze loop needs — built via
    __new__ so no real window opens (mirrors tests/test_hold_esc_integration's
    make_sm pattern; LivePresenter.__init__ opens a display)."""
    p = LivePresenter.__new__(LivePresenter)
    p.screen = pg.Surface((320, 180))
    p.clock = pg.time.Clock()
    p.cap_fps = cap_fps
    p.overlay = False
    p.speed = 1.0
    p.captions = list(captions)
    p.interactive = interactive
    p._init_input_strip(False)  # #434: show() now records/draws the input strip (off here)
    return p


# --- the pure advance/quit classifier -----------------------------------------

def test_consume_advance_returns_advance_on_space_or_right():
    assert LivePresenter._consume_advance([pg.event.Event(pg.KEYDOWN, key=pg.K_SPACE)]) == "advance"
    assert LivePresenter._consume_advance([pg.event.Event(pg.KEYDOWN, key=pg.K_RIGHT)]) == "advance"


def test_consume_advance_returns_quit_on_esc_or_window_close():
    assert LivePresenter._consume_advance([pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE)]) == "quit"
    assert LivePresenter._consume_advance([pg.event.Event(pg.QUIT)]) == "quit"


def test_consume_advance_keeps_waiting_on_other_or_no_events():
    # A non-advance key must NOT resume — the whole point is waiting for input, not a
    # timer, so anything but Space/Right/Esc/QUIT leaves the presenter paused.
    assert LivePresenter._consume_advance([pg.event.Event(pg.KEYDOWN, key=pg.K_a)]) is None
    assert LivePresenter._consume_advance([]) is None


# --- the freeze loop: waits without a key, resumes with one -------------------

class _StopTick(Exception):
    pass


def test_manual_hold_waits_for_input_and_does_not_time_out(monkeypatch):
    # dwell=3 is small; the sentinel fires after 10 ticks. A TIMED dwell would return
    # after 3 ticks (no sentinel). Manual mode has no timer, so it ticks past 3 and
    # hits the sentinel — proving the freeze is gated on input, not a frame count.
    monkeypatch.setattr(pr, "render_battle", lambda *a, **k: None)
    monkeypatch.setattr(pr, "render_attacks", lambda *a, **k: None)
    monkeypatch.setattr(pr, "draw_captions", lambda *a, **k: None)
    monkeypatch.setattr(pr.pygame.display, "flip", lambda: None)

    p = _manual_presenter([Caption("beat", frames=(0, 5), dwell=3)])
    ticks = {"n": 0}

    def fake_tick():
        ticks["n"] += 1
        if ticks["n"] > 10:
            raise _StopTick

    p._tick = fake_tick
    pg.event.clear()                       # no advance key queued
    with pytest.raises(_StopTick):
        p.show([], [], [], 0)              # frame 0 is the dwell frame -> manual pause


def test_manual_hold_resumes_immediately_on_advance_key(monkeypatch):
    # Drive the freeze loop directly (show()'s top-of-frame pump would drain the key
    # before the hold — in real use the viewer presses DURING the pause, which is what
    # _wait_for_advance's own event read catches).
    monkeypatch.setattr(pr.pygame.display, "flip", lambda: None)
    p = _manual_presenter([Caption("beat", frames=(0, 5), dwell=3)])
    ticks = {"n": 0}
    p._tick = lambda: ticks.__setitem__("n", ticks["n"] + 1)

    pg.event.clear()
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_SPACE))
    p._wait_for_advance()                  # advance queued -> returns at once
    assert ticks["n"] == 0, "resumed on the key without waiting a single tick"


def test_manual_hold_quit_key_raises_keyboardinterrupt(monkeypatch):
    monkeypatch.setattr(pr.pygame.display, "flip", lambda: None)
    p = _manual_presenter([Caption("beat", frames=(0, 5), dwell=3)])
    p._tick = lambda: None
    pg.event.clear()
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE))
    with pytest.raises(KeyboardInterrupt):
        p._wait_for_advance()


def test_no_pause_on_a_non_dwell_frame(monkeypatch):
    # Frame 1 is not the caption's dwell frame -> no hold at all, even in manual mode.
    monkeypatch.setattr(pr, "render_battle", lambda *a, **k: None)
    monkeypatch.setattr(pr, "render_attacks", lambda *a, **k: None)
    monkeypatch.setattr(pr, "draw_captions", lambda *a, **k: None)
    monkeypatch.setattr(pr.pygame.display, "flip", lambda: None)

    p = _manual_presenter([Caption("beat", frames=(0, 5), dwell=3)])
    p._tick = lambda: None
    pg.event.clear()                       # no key, yet it must NOT hang
    p.show([], [], [], 1)                  # returns (no dwell here)


# --- watch.py --demo-manual wiring --------------------------------------------

class _SpyPresenter:
    """Captures the kwargs watch.main constructs LivePresenter with (#393)."""
    last_kwargs = {}

    def __init__(self, **kwargs):
        _SpyPresenter.last_kwargs = kwargs
        self.captions = []

    def show(self, *a, **k):
        pass

    def close(self):
        pass


def test_watch_demo_manual_flag_sets_interactive_manual(monkeypatch):
    import watch
    monkeypatch.setattr(watch, "LivePresenter", _SpyPresenter)
    watch.main(["--demo", "example", "--demo-manual", "--frames", "1", "--uncapped"])
    assert _SpyPresenter.last_kwargs.get("interactive") == "manual"


def test_watch_without_manual_flag_is_non_interactive(monkeypatch):
    import watch
    monkeypatch.setattr(watch, "LivePresenter", _SpyPresenter)
    watch.main(["--demo", "example", "--frames", "1", "--uncapped"])
    assert _SpyPresenter.last_kwargs.get("interactive") is None

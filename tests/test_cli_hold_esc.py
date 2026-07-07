"""Hold-Esc-2s to exit demo/sim playback (#515, epic #308, design #507 §3b).

The CLI playback surface reuses the in-game #453 convention via the SAME
`EscHoldTimer`: holding Esc for the 2s threshold exits the run (raises
KeyboardInterrupt, the existing quit signal); a *tap* does not (this replaces
#393's tap-Esc-quit). The timer is ticked once per displayed frame in both
`show()` and the timed-dwell loop, so a hold that spans a caption dwell keeps
counting instead of stalling.

Golden-safe: non-interactive playback reads an all-released keyboard
(`pygame.key.get_pressed()`), so the timer never advances -> byte-identical.

Driven headlessly: the held-source `_esc_held` is monkeypatched so the tests
don't depend on a live keyboard; the threshold is shrunk for speed.
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


def _presenter(hold_frames=4, captions=()):
    """A LivePresenter with just the attributes the playback loop needs, built via
    __new__ so no real window opens (mirrors test_dwell_interrupt._timed_presenter).
    A short `hold_frames` keeps the threshold test fast."""
    p = LivePresenter.__new__(LivePresenter)
    p.screen = pg.Surface((320, 180))
    p.clock = pg.time.Clock()
    p.cap_fps = False
    p.overlay = False
    p.speed = 1.0
    p.captions = list(captions)
    p._esc_hold = EscHoldTimer(hold_frames)
    p._init_input_strip(False)
    return p


# --- the per-frame service: accumulate a hold, quit at threshold ---------------

def test_full_hold_raises_keyboardinterrupt():
    p = _presenter(hold_frames=4)
    p._esc_held = lambda: True
    for _ in range(3):
        p._service_esc_hold()  # 3 held frames: below threshold, no quit
    with pytest.raises(KeyboardInterrupt):
        p._service_esc_hold()  # 4th consecutive held frame fires


def test_release_before_threshold_does_not_quit():
    p = _presenter(hold_frames=4)
    held = {"v": True}
    p._esc_held = lambda: held["v"]
    p._service_esc_hold()
    p._service_esc_hold()
    held["v"] = False  # released before 4 — resets the count
    p._service_esc_hold()
    held["v"] = True
    p._service_esc_hold()
    p._service_esc_hold()  # only 2 consecutive again — still no quit
    assert p._esc_hold.progress < 1.0


def test_tap_esc_does_not_quit():
    # A tap = one held frame then release, repeated. It must NEVER accumulate to the
    # threshold — this is the behaviour that replaces #393's tap-Esc-quit.
    p = _presenter(hold_frames=4)
    state = {"v": True}
    p._esc_held = lambda: state["v"]
    for _ in range(20):
        state["v"] = not state["v"]  # alternate held/released
        p._service_esc_hold()
    assert not p._esc_hold.complete


# --- the timed-dwell loop keeps counting a hold that spans a dwell -------------

def test_hold_across_a_dwell_still_quits(monkeypatch):
    # Esc held (already down, so no fresh KEYDOWN edge -> #514's any-key skip does not
    # fire) while a long dwell counts down: the dwell loop services the hold each tick
    # and quits at the threshold instead of stalling for the whole dwell.
    monkeypatch.setattr(pr.pygame.event, "get", lambda: [])  # no KEYDOWN edge
    p = _presenter(hold_frames=4, captions=[Caption("beat", frames=(0, 5), dwell=20)])
    p._esc_held = lambda: True
    p._tick = lambda: None
    with pytest.raises(KeyboardInterrupt):
        p._hold(0)  # frame 0 is the dwell frame


# --- golden-safety: non-interactive playback never quits ----------------------

def test_non_interactive_never_quits(monkeypatch):
    # Real _esc_held reads pygame.key.get_pressed(); headless it is all-released, so a
    # long non-interactive run never advances the timer -> byte-identical to today.
    monkeypatch.setattr(pr, "render_battle", lambda *a, **k: None)
    monkeypatch.setattr(pr, "render_attacks", lambda *a, **k: None)
    monkeypatch.setattr(pr, "draw_captions", lambda *a, **k: None)
    monkeypatch.setattr(pr.pygame.display, "flip", lambda: None)
    p = _presenter(hold_frames=4)  # uses the real _esc_held
    p._tick = lambda: None
    for f in range(50):
        p.show([], [], [], f)  # must not raise
    assert not p._esc_hold.complete

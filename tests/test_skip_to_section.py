"""Skip-to-next-section in demo/sim playback (#508, epic #308, spike #355, redesign #507).

A distinct key (→, ratified 2026-07-06) fast-forwards the *gameplay* between caption
beats: the sim keeps running every frame (state is a fold of 0..N-1, so frames can't be
dropped), but render + display pacing are suppressed until the cursor reaches the next
caption boundary, then normal rendering resumes. Desync-free by construction.

The seam (from the superseded #394, re-fit onto the post-#507 presenter):
- `LivePresenter.show()` returns a `"skip"` intent when → was pressed this displayed
  frame (in normal play, or during the following dwell — #514's any-key also ends it);
- `run_battle(..., boundaries=...)` owns the "next boundary > f" math and the unrendered
  fast-forward loop; `boundaries=None` (goldens/headless) keeps the sim path untouched.

Golden-safe: with no boundaries a skip intent is ignored -> show() every frame -> the
byte-identical path. Runner tests use a spy presenter; presenter tests use __new__.
"""


import pygame as pg
import pytest

import pycats.sim.presenters as pr
from pycats.esc_hold import EscHoldTimer
from pycats.sim.captions import Caption
from pycats.sim.presenters import SECTION_SKIP_KEY, LivePresenter
from pycats.sim.runner import run_battle


@pytest.fixture(autouse=True)
def _pg():
    pg.init()


# --- the runner seam: boundaries + the unrendered fast-forward loop ------------

class _SpyPresenter:
    """Records which frames it was asked to render, and reports a skip intent on a
    chosen frame (or always, when skip_on='all')."""

    def __init__(self, skip_on):
        self.skip_on = skip_on
        self.shown = []
        self.closed = False

    def show(self, platforms, players, attacks, frame, inputs=None):
        self.shown.append(frame)
        return "skip" if self.skip_on == "all" or frame == self.skip_on else None

    def close(self):
        self.closed = True


def test_skip_fast_forwards_to_next_boundary_unrendered():
    spy = _SpyPresenter(skip_on=1)
    snaps = run_battle(frames=16, boundaries=[4, 10], presenter=spy)
    # Frames between the skip (1) and the next boundary (4) are NOT rendered...
    assert 2 not in spy.shown and 3 not in spy.shown
    # ...rendering resumes exactly at the boundary, then runs normally.
    assert spy.shown == [0, 1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    # Every sim frame still ran — snaps are continuous (no dropped/duplicated frames).
    assert len(snaps) == 16


def test_skip_without_boundaries_is_a_noop():
    # boundaries=None (the golden/headless path): a skip intent is ignored entirely, so
    # show() is still called every frame -> byte-identical to non-interactive playback.
    spy = _SpyPresenter(skip_on=1)
    run_battle(frames=8, presenter=spy)  # boundaries defaults to None
    assert spy.shown == list(range(8))


def test_skip_chains_across_successive_boundaries():
    # Holding → : after resuming at a boundary the next frame skips again to the boundary
    # after it; past the last boundary, playback just continues normally.
    spy = _SpyPresenter(skip_on="all")
    run_battle(frames=16, boundaries=[4, 10], presenter=spy)
    assert spy.shown == [0, 4, 10, 11, 12, 13, 14, 15]


def test_skip_targets_the_nearest_boundary_even_if_unsorted():
    # The runner picks the nearest boundary strictly after f, regardless of list order.
    spy = _SpyPresenter(skip_on=0)
    run_battle(frames=12, boundaries=[10, 3, 6], presenter=spy)
    assert spy.shown == [0, 3, 4, 5, 6, 7, 8, 9, 10, 11]


# --- the presenter intent: → reports "skip", other keys do not ----------------

def _presenter(captions=()):
    p = LivePresenter.__new__(LivePresenter)
    p.screen = pg.Surface((320, 180))
    p.clock = pg.time.Clock()
    p.cap_fps = False
    p.overlay = False
    p.speed = 1.0
    p.captions = list(captions)
    p._esc_hold = EscHoldTimer()
    p._init_input_strip(False)
    return p


def _quiet(monkeypatch):
    for name in ("render_battle", "render_attacks", "draw_captions", "draw_esc_hold_arc"):
        monkeypatch.setattr(pr, name, lambda *a, **k: None)
    monkeypatch.setattr(pr.pygame.display, "flip", lambda: None)


def test_show_returns_skip_intent_on_the_section_key(monkeypatch):
    _quiet(monkeypatch)
    p = _presenter()
    p._tick = lambda: None
    pg.event.clear()
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=SECTION_SKIP_KEY))
    assert p.show([], [], [], 0) == "skip"


def test_show_returns_none_without_the_section_key(monkeypatch):
    _quiet(monkeypatch)
    p = _presenter()
    p._tick = lambda: None
    pg.event.clear()
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_a))  # a non-skip key
    assert p.show([], [], [], 0) is None


def test_section_key_during_a_dwell_reports_skip(monkeypatch):
    # #394's composition: → during a caption's dwell both ends the dwell (#514 any-key)
    # AND begins the fast-forward, so _hold surfaces the skip intent to show().
    monkeypatch.setattr(pr.pygame.event, "get", lambda: [pg.event.Event(pg.KEYDOWN, key=SECTION_SKIP_KEY)])
    p = _presenter([Caption("beat", frames=(0, 5), dwell=10)])
    p._tick = lambda: None
    assert p._hold(0) == "skip"


def test_other_key_during_a_dwell_does_not_report_skip(monkeypatch):
    # A non-skip key ends the dwell (#514) but must NOT trigger a section fast-forward.
    monkeypatch.setattr(pr.pygame.event, "get", lambda: [pg.event.Event(pg.KEYDOWN, key=pg.K_a)])
    p = _presenter([Caption("beat", frames=(0, 5), dwell=10)])
    p._tick = lambda: None
    assert p._hold(0) is None


# --- watch.py wiring: demo mode passes caption-start boundaries ----------------

class _StubPresenter:
    """Stands in for LivePresenter so watch.main runs headless (no window)."""

    def __init__(self, **kwargs):
        self.captions = []

    def close(self):
        pass


def test_watch_demo_passes_caption_start_boundaries(monkeypatch):
    import watch

    captured = {}

    def fake_run_battle(*a, **k):
        captured.update(k)
        return []

    monkeypatch.setattr(watch, "run_battle", fake_run_battle)
    monkeypatch.setattr(watch, "LivePresenter", _StubPresenter)
    watch.main(["--demo", "example", "--frames", "3", "--uncapped"])
    assert "boundaries" in captured
    assert captured["boundaries"] == sorted(captured["boundaries"])
    assert all(isinstance(b, int) for b in captured["boundaries"])
    assert captured["boundaries"], "demo mode should derive at least one caption boundary"

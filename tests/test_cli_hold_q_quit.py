"""Hold-`q`-2s also exits demo/sim playback — alternate to hold-Esc (#907).

`q` is an additional deliberate quit key for the live sim viewer: holding it the
same 2s threshold as Esc (#515) exits the run (raises KeyboardInterrupt), using
the SAME `EscHoldTimer` and progress arc. Esc-hold is unchanged; a *tap* of
either key still does nothing.

Golden-safe: the real `_esc_held` reads `pygame.key.get_pressed()`, all-released
under non-interactive playback, so neither key ever advances the timer.

Driven headlessly by faking `pygame.key.get_pressed()` so the tests don't depend
on a live keyboard; the threshold is shrunk for speed (mirrors test_cli_hold_esc).
"""

import pygame as pg
import pytest

import pycats.sim.presenters as pr
from pycats.esc_hold import EscHoldTimer
from pycats.sim.presenters import LivePresenter


@pytest.fixture(autouse=True)
def _pg():
    pg.init()


class _Keys:
    """Stand-in for `pygame.key.get_pressed()` — truthy only for the given keys."""

    def __init__(self, *down):
        self._down = set(down)

    def __getitem__(self, key):
        return key in self._down


def _presenter(hold_frames=4):
    """A LivePresenter built via __new__ so no real window opens (mirrors
    test_cli_hold_esc._presenter). Short `hold_frames` keeps the threshold fast."""
    p = LivePresenter.__new__(LivePresenter)
    p.screen = pg.Surface((320, 180))
    p.clock = pg.time.Clock()
    p.cap_fps = False
    p.overlay = False
    p.speed = 1.0
    p.captions = []
    p._esc_hold = EscHoldTimer(hold_frames)
    p._init_input_strip(False)
    return p


def test_q_counts_as_held(monkeypatch):
    # The real _esc_held must report a held `q` (Esc up) as held — the crux of #907.
    monkeypatch.setattr(pr.pygame.key, "get_pressed", lambda: _Keys(pg.K_q))
    p = _presenter()
    assert p._esc_held() is True


def test_full_hold_q_raises_keyboardinterrupt(monkeypatch):
    # Holding `q` the full threshold quits, same as Esc — through the real service path.
    monkeypatch.setattr(pr.pygame.key, "get_pressed", lambda: _Keys(pg.K_q))
    p = _presenter(hold_frames=4)
    for _ in range(3):
        p._service_esc_hold()  # below threshold
    with pytest.raises(KeyboardInterrupt):
        p._service_esc_hold()  # 4th consecutive held frame fires


def test_esc_still_quits(monkeypatch):
    # Regression: widening the predicate for `q` must not break Esc-hold (#515).
    monkeypatch.setattr(pr.pygame.key, "get_pressed", lambda: _Keys(pg.K_ESCAPE))
    p = _presenter(hold_frames=4)
    for _ in range(3):
        p._service_esc_hold()
    with pytest.raises(KeyboardInterrupt):
        p._service_esc_hold()


def test_unrelated_key_is_inert(monkeypatch):
    # Only Esc/`q` quit — an arbitrary held key must never accumulate the timer.
    monkeypatch.setattr(pr.pygame.key, "get_pressed", lambda: _Keys(pg.K_a))
    p = _presenter(hold_frames=4)
    assert p._esc_held() is False
    for _ in range(10):
        p._service_esc_hold()
    assert not p._esc_hold.complete


def test_tap_q_does_not_quit(monkeypatch):
    # A tap = alternating held/released; it must never reach the threshold (mirrors
    # the tap-Esc guard). Toggles the faked keystate between `q`-down and all-up.
    state = {"down": True}
    monkeypatch.setattr(
        pr.pygame.key,
        "get_pressed",
        lambda: _Keys(pg.K_q) if state["down"] else _Keys(),
    )
    p = _presenter(hold_frames=4)
    for _ in range(20):
        state["down"] = not state["down"]
        p._service_esc_hold()
    assert not p._esc_hold.complete

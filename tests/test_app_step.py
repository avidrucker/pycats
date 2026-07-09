"""App.step() loop-body wiring tests (#707, C3 of #280) — the #386 payoff.

Before C3 the per-frame loop body was inline in game.py's `while running:`; there was no
seam to run one frame, so the event-dispatch / quit-check / update→render→present wiring
had zero coverage. C3 moves that body onto `App.step()`, and — per the #707 ruling — the
only injected seam is the event source (`poll`), so these tests script `(InputFrame,
events)` through a fake poll and spy on the collaborators App already holds.

Construction is file-I/O-free (ruled Q2): `App(prefs, poll=...)` takes a plain prefs dict,
so there is no settings.load() here (no #345 trap). A test-level `pygame.init()` + the
SDL dummy driver give DisplayManager a real headless surface (same as the #698 tests).
"""

import pygame  # type: ignore

import pycats.app as app_mod
from pycats.app import App
from pycats.core.input import InputFrame

_PREFS = {"windowed_scale": 1.0, "fullscreen": False}


def _frame():
    return InputFrame(held=set(), pressed=set(), released=set())


def _poll_once(*events):
    """Fake poll: yields the given events on the first call, nothing after."""
    state = {"n": 0}

    def poll():
        state["n"] += 1
        return _frame(), (list(events) if state["n"] == 1 else [])

    return poll


def _app(poll):
    pygame.init()
    return App(prefs=dict(_PREFS), poll=poll)


def test_quit_event_stops_the_app():
    app = _app(_poll_once(pygame.event.Event(pygame.QUIT)))
    assert app.running is True
    app.step()
    assert app.running is False


def test_should_quit_game_stops_the_app(monkeypatch):
    app = _app(_poll_once())  # no events
    monkeypatch.setattr(app.screen_manager, "should_quit_game", lambda: True)
    app.step()
    assert app.running is False


def test_step_wires_update_then_render_then_present(monkeypatch):
    app = _app(_poll_once())
    order = []
    monkeypatch.setattr(app.screen_manager, "update", lambda *a, **k: order.append("update"))
    monkeypatch.setattr(app.screen_manager, "should_quit_game", lambda: False)
    monkeypatch.setattr(app_mod.screen_render, "render_active_screen", lambda *a, **k: order.append("render"))
    monkeypatch.setattr(app.dm, "present", lambda *a, **k: order.append("present"))
    app.step()
    assert order == ["update", "render", "present"]


def test_f11_routes_to_toggle_fullscreen_then_save(monkeypatch):
    app = _app(_poll_once(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11)))
    calls = []
    monkeypatch.setattr(app.dm, "toggle_fullscreen", lambda: calls.append("toggle"))
    monkeypatch.setattr(app, "save_prefs", lambda: calls.append("save"))
    # keep the rest of the frame inert so we isolate the hotkey→transition→persist wire
    monkeypatch.setattr(app.screen_manager, "update", lambda *a, **k: None)
    monkeypatch.setattr(app.screen_manager, "should_quit_game", lambda: False)
    monkeypatch.setattr(app_mod.screen_render, "render_active_screen", lambda *a, **k: None)
    monkeypatch.setattr(app.dm, "present", lambda *a, **k: None)
    app.step()
    assert calls == ["toggle", "save"]

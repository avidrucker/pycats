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


class _FakeClock:
    """Stand-in for pygame's C Clock (whose .tick is read-only, so it can't be patched).
    Records every tick() argument; get_fps() is a stub for the render call."""

    def __init__(self):
        self.tick_args = []

    def tick(self, *a):
        self.tick_args.append(a[0] if a else None)
        return 0

    def get_fps(self):
        return 60.0


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


def test_speed_defaults_to_real_time():
    app = _app(_poll_once())
    assert app.speed == 1.0


def test_speed_is_stored_from_constructor():
    pygame.init()
    app = App(prefs=dict(_PREFS), poll=_poll_once(), speed=0.25)
    assert app.speed == 0.25


def _tick_arg_for_speed(monkeypatch, speed, state="playing"):
    """Run one inert frame at `speed` in FSM `state` and return the argument App.step
    passed to clock.tick (the present-rate pacing target). `--speed` slows only the
    battle (`playing`) — every menu state paces at full 60 FPS (#938) — so the state
    the frame is in decides whether the factor applies."""
    pygame.init()
    app = App(prefs=dict(_PREFS), poll=_poll_once(), speed=speed)
    app.clock = _FakeClock()
    monkeypatch.setattr(app.screen_manager, "get_state", lambda: state)
    monkeypatch.setattr(app.screen_manager, "update", lambda *a, **k: None)
    monkeypatch.setattr(app.screen_manager, "should_quit_game", lambda: False)
    monkeypatch.setattr(app_mod.screen_render, "render_active_screen", lambda *a, **k: None)
    monkeypatch.setattr(app.dm, "present", lambda *a, **k: None)
    app.step()
    return app.clock.tick_args


def test_step_paces_clock_to_full_fps_at_default_speed(monkeypatch):
    # Able-to-fail: revert step to clock.tick(FPS) leaves this at 60 (still passes), but
    # the 0.5/0.25 playing tests below flip — together they pin the tick_fps wiring.
    assert _tick_arg_for_speed(monkeypatch, 1.0, state="playing") == [60]


def test_step_paces_battle_to_half_fps_at_half_speed(monkeypatch):
    # The battle (playing state) IS slowed by --speed.
    assert _tick_arg_for_speed(monkeypatch, 0.5, state="playing") == [30]


def test_step_paces_battle_to_quarter_fps_at_quarter_speed(monkeypatch):
    assert _tick_arg_for_speed(monkeypatch, 0.25, state="playing") == [15]


# --- #938: --speed must NOT slow the menus (only the battle) --------------------------
# The menu hold-to-quit/back timers are frame-counted (EscHoldTimer(120) = "2s @ 60fps"),
# ticked once per App.step; if a menu ran at 30 FPS those 120 frames would take 4s. So
# every non-playing state paces at full 60 FPS regardless of --speed. Able-to-fail today:
# the current always-tick_fps(self.speed) line yields 30/15 here.
def test_step_keeps_main_menu_at_full_fps_at_half_speed(monkeypatch):
    assert _tick_arg_for_speed(monkeypatch, 0.5, state="main_menu") == [60]


def test_step_keeps_main_menu_at_full_fps_at_quarter_speed(monkeypatch):
    assert _tick_arg_for_speed(monkeypatch, 0.25, state="main_menu") == [60]


def test_step_keeps_pause_at_full_fps_at_half_speed(monkeypatch):
    # Pause is a menu overlay (its own hold-timers), not the battle: full speed.
    assert _tick_arg_for_speed(monkeypatch, 0.5, state="pause") == [60]


def test_step_keeps_char_select_at_full_fps_at_half_speed(monkeypatch):
    assert _tick_arg_for_speed(monkeypatch, 0.5, state="char_select") == [60]


def _update_args_at_speed(monkeypatch, speed):
    """Capture the (frame_input, battle, platforms) App.step forwards to
    screen_manager.update at a given speed — the sim-facing arguments."""
    pygame.init()
    app = App(prefs=dict(_PREFS), poll=_poll_once(), speed=speed)
    app.clock = _FakeClock()
    seen = {}
    monkeypatch.setattr(app.screen_manager, "update", lambda *a, **k: seen.setdefault("args", a))
    monkeypatch.setattr(app.screen_manager, "should_quit_game", lambda: False)
    monkeypatch.setattr(app_mod.screen_render, "render_active_screen", lambda *a, **k: None)
    monkeypatch.setattr(app.dm, "present", lambda *a, **k: None)
    app.step()
    return seen["args"], app


def test_speed_does_not_reach_the_sim_update(monkeypatch):
    # Determinism guard: slow-mo is present-rate only. At any speed, App.step must forward
    # its OWN battle + platforms (unchanged) and the polled frame to the sim/update path;
    # speed only changes clock pacing, never what the sim sees, so outcomes/goldens can't
    # move. (battle/platforms are per-App builds, so this asserts identity within an app.)
    for speed in (1.0, 0.25):
        (frame_input, battle, platforms), app = _update_args_at_speed(monkeypatch, speed)
        assert frame_input == _frame()  # the polled input, untouched by speed
        assert battle is app.battle
        assert platforms is app.platforms


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

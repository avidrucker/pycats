"""Screen-flow engine backend parity (slice 1 of epic #100; #181).

A `StatechartScreenEngine` must be transition-equivalent to the legacy guard-table
FSM. These tests drive *controllable* guards through both backends and assert the
engines select transitions identically (document order, break-after-first) — the
screen-flow analogue of the fighter_fsm <-> fighter_chart parity guarantee.

Slice 1 only adds the engine seam + this guard; it does not rewire game.py or the
live ScreenStateManager off the legacy default.
"""
from pycats.systems.screen_engine import make_screen_engine

BACKENDS = ("legacy", "statechart")


def _table(flags):
    # 'a' has two ORDERED transitions; first matching guard wins (break-after-first).
    return {
        "a": [("b", lambda ctx: flags["go"]), ("c", lambda ctx: flags["alt"])],
        "b": [("a", lambda ctx: flags["back"])],
        "c": [],
    }


def test_screen_engine_initial_state_both_backends():
    for backend in BACKENDS:
        flags = {"go": False, "alt": False, "back": False}
        eng = make_screen_engine(_table(flags), initial="a", backend=backend)
        assert eng.state == "a", backend


def test_screen_engine_fires_first_matching_transition_both_backends():
    for backend in BACKENDS:
        flags = {"go": False, "alt": False, "back": False}
        eng = make_screen_engine(_table(flags), initial="a", backend=backend)
        eng.update(None)
        assert eng.state == "a", backend          # no guard true -> stay
        flags["go"] = True
        eng.update(None)
        assert eng.state == "b", backend          # first transition fires


def test_screen_engine_transition_order_priority_both_backends():
    # Both guards true: the FIRST listed ("b") must win in both backends.
    for backend in BACKENDS:
        flags = {"go": True, "alt": True, "back": False}
        eng = make_screen_engine(_table(flags), initial="a", backend=backend)
        eng.update(None)
        assert eng.state == "b", backend


def test_screen_engine_on_enter_and_on_update_fire_both_backends():
    """on_enter fires on entry to a state (not for the initial state); on_update
    fires each step for the current (post-transition) state — identical to the
    legacy FSM, in both backends."""
    for backend in BACKENDS:
        log = []
        flags = {"go": False}
        transitions = {"a": [("b", lambda ctx: flags["go"])], "b": []}
        on_enter = {"a": lambda ctx: log.append("enter_a"),
                    "b": lambda ctx: log.append("enter_b")}
        on_update = {"a": lambda ctx: log.append("update_a"),
                     "b": lambda ctx: log.append("update_b")}
        eng = make_screen_engine(transitions, "a", backend=backend,
                                 on_enter=on_enter, on_update=on_update)
        # initial state must NOT fire on_enter
        assert "enter_a" not in log, backend
        eng.update(None)                       # stay in a (guard false)
        assert log == ["update_a"], (backend, log)
        flags["go"] = True
        eng.update(None)                       # a -> b: enter_b then update_b
        assert log == ["update_a", "enter_b", "update_b"], (backend, log)


def test_screen_engine_force_jumps_and_fires_on_enter_both_backends():
    """force(label) jumps straight to a state (non-guard-driven, e.g. ESC-hold
    return-to-menu) and fires that state's on_enter, in both backends."""
    for backend in BACKENDS:
        log = []
        transitions = {"playing": [], "main_menu": []}
        on_enter = {"main_menu": lambda ctx: log.append("enter_mm")}
        eng = make_screen_engine(transitions, "playing", backend=backend,
                                 on_enter=on_enter)
        assert eng.state == "playing", backend
        eng.force("main_menu")
        assert eng.state == "main_menu", backend
        assert log == ["enter_mm"], (backend, log)


def _screen_like_table(sig):
    """The real screen-flow graph shape (main_menu/options/char_select/playing/
    pause/win_screen), with guards driven by a single controllable signal `sig`."""
    return {
        "main_menu":   [("char_select", lambda c: sig["v"] == "to_cs"),
                        ("options",     lambda c: sig["v"] == "to_opt")],
        "options":     [("main_menu",   lambda c: sig["v"] == "opt_back")],
        "char_select": [("playing",     lambda c: sig["v"] == "start"),
                        ("main_menu",   lambda c: sig["v"] == "cs_back")],
        "playing":     [("pause",       lambda c: sig["v"] == "pause"),
                        ("win_screen",  lambda c: sig["v"] == "ko")],
        "pause":       [("playing",     lambda c: sig["v"] == "resume"),
                        ("win_screen",  lambda c: sig["v"] == "stats"),
                        ("main_menu",   lambda c: sig["v"] == "quit")],
        "win_screen":  [("char_select", lambda c: sig["v"] == "rematch")],
    }


def test_screen_engine_full_path_parity():
    """A representative input/event trace must produce an IDENTICAL per-step state
    sequence on both backends (the screen-flow equivalence guard)."""
    script = ["to_opt", "opt_back", "to_cs", "start", "pause",
              "resume", "ko", "rematch", "noop", "start"]
    sig_l, sig_s = {"v": None}, {"v": None}
    legacy = make_screen_engine(_screen_like_table(sig_l), "main_menu", "legacy")
    chart = make_screen_engine(_screen_like_table(sig_s), "main_menu", "statechart")
    trace_l, trace_s = [], []
    for ev in script:
        sig_l["v"] = sig_s["v"] = ev
        legacy.update(None)
        chart.update(None)
        trace_l.append(legacy.state)
        trace_s.append(chart.state)
    assert trace_l == trace_s, f"{trace_l} != {trace_s}"
    # The trace must actually visit the interesting states (guard isn't vacuous).
    assert {"options", "char_select", "playing", "pause", "win_screen"} <= set(trace_l)

"""Screen-flow engine semantics, anchored on a recorded golden (ADR-0002, #100).

This originally cross-checked two live screen engines — the legacy guard-table FSM
(`systems/fsm.py` / `LegacyScreenEngine`) and the statechart engine — per step. ADR-0002
(#174), whose "delete legacy" ruling **extends to the screen backend** (epic #100),
retired the legacy engine: slice 4a (#234) froze its per-step transition sequence as a
recorded golden (`tests/golden/screen_parity.json`); slice 4b (#235) then deleted the
legacy engine and its FSM. The statechart engine is now the only screen engine.

The equivalence guard survives the deletion as **statechart == golden**
(`test_statechart_screen_trace_matches_golden`) — the frozen record stands in for the
deleted second engine, mirroring the fighter parity freeze (#176). The semantic unit
tests below (initial state, transition order, on_enter/on_update, force) pin the engine
semantics directly.

Regen the golden — only after a *reviewed, intended* screen-flow change — by running
this file with ``PYCATS_UPDATE_GOLDENS=1`` (records from the statechart engine, now the
sole engine).
"""
import json
import os
from pathlib import Path

from pycats.systems.screen_engine import make_screen_engine


def _table(flags):
    # 'a' has two ORDERED transitions; first matching guard wins (break-after-first).
    return {
        "a": [("b", lambda ctx: flags["go"]), ("c", lambda ctx: flags["alt"])],
        "b": [("a", lambda ctx: flags["back"])],
        "c": [],
    }


def test_screen_engine_initial_state():
    flags = {"go": False, "alt": False, "back": False}
    eng = make_screen_engine(_table(flags), initial="a")
    assert eng.state == "a"


def test_screen_engine_fires_first_matching_transition():
    flags = {"go": False, "alt": False, "back": False}
    eng = make_screen_engine(_table(flags), initial="a")
    eng.update(None)
    assert eng.state == "a"          # no guard true -> stay
    flags["go"] = True
    eng.update(None)
    assert eng.state == "b"          # first transition fires


def test_screen_engine_transition_order_priority():
    # Both guards true: the FIRST listed ("b") must win.
    flags = {"go": True, "alt": True, "back": False}
    eng = make_screen_engine(_table(flags), initial="a")
    eng.update(None)
    assert eng.state == "b"


def test_screen_engine_on_enter_and_on_update_fire():
    """on_enter fires on entry to a state (not for the initial state); on_update
    fires each step for the current (post-transition) state."""
    log = []
    flags = {"go": False}
    transitions = {"a": [("b", lambda ctx: flags["go"])], "b": []}
    on_enter = {"a": lambda ctx: log.append("enter_a"),
                "b": lambda ctx: log.append("enter_b")}
    on_update = {"a": lambda ctx: log.append("update_a"),
                 "b": lambda ctx: log.append("update_b")}
    eng = make_screen_engine(transitions, "a",
                             on_enter=on_enter, on_update=on_update)
    # initial state must NOT fire on_enter
    assert "enter_a" not in log
    eng.update(None)                       # stay in a (guard false)
    assert log == ["update_a"], log
    flags["go"] = True
    eng.update(None)                       # a -> b: enter_b then update_b
    assert log == ["update_a", "enter_b", "update_b"], log


def test_screen_engine_force_jumps_and_fires_on_enter():
    """force(label) jumps straight to a state (non-guard-driven, e.g. ESC-hold
    return-to-menu) and fires that state's on_enter."""
    log = []
    transitions = {"playing": [], "main_menu": []}
    on_enter = {"main_menu": lambda ctx: log.append("enter_mm")}
    eng = make_screen_engine(transitions, "playing", on_enter=on_enter)
    assert eng.state == "playing"
    eng.force("main_menu")
    assert eng.state == "main_menu"
    assert log == ["enter_mm"], log


def test_make_screen_engine_has_no_backend_param():
    """Slice 4c (#236): the backend-selection plumbing is gone — `make_screen_engine`
    builds the statechart engine unconditionally, with no `backend` parameter to
    select a (nonexistent) legacy engine. Able-to-fail: re-adding the param turns
    this red."""
    import inspect
    params = inspect.signature(make_screen_engine).parameters
    assert "backend" not in params, sorted(params)


# --------------------------------------------------------------------------- #
# Recorded-golden parity gate (ADR-0002 step 1, #234)
# --------------------------------------------------------------------------- #

GOLDEN_PATH = Path(__file__).parent / "golden" / "screen_parity.json"

# A representative input/event trace exercising the real screen-flow graph shape
# (main_menu/options/char_select/playing/pause/win_screen), one event per step.
SCRIPT = ["to_opt", "opt_back", "to_cs", "start", "pause",
          "resume", "ko", "rematch", "noop", "start"]

# States the trace must actually visit, so the golden isn't a vacuous "stayed put".
INTERESTING = {"options", "char_select", "playing", "pause", "win_screen"}


def _screen_like_table(sig):
    """The real screen-flow graph shape, with guards driven by a single
    controllable signal `sig` (one event per step)."""
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


def _run_trace():
    """Drive the screen engine through SCRIPT, returning the per-step state sequence."""
    sig = {"v": None}
    eng = make_screen_engine(_screen_like_table(sig), "main_menu")
    trace = []
    for ev in SCRIPT:
        sig["v"] = ev
        eng.update(None)
        trace.append(eng.state)
    return trace


def _load_golden():
    assert GOLDEN_PATH.exists(), (
        f"Screen-parity golden missing: {GOLDEN_PATH}\n"
        "Record it by running this file with PYCATS_UPDATE_GOLDENS=1."
    )
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_statechart_screen_trace_matches_golden():
    """THE GATE: the statechart engine — now the sole screen engine — reproduces the
    recorded golden screen-flow transition sequence (the frozen legacy record, #234).
    Doubles as the recorder under PYCATS_UPDATE_GOLDENS=1."""
    trace = _run_trace()
    if os.environ.get("PYCATS_UPDATE_GOLDENS") == "1":
        GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN_PATH.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
        return
    assert trace == _load_golden(), f"statechart diverged from golden:\n {trace}"
    # The trace must actually visit the interesting states (golden isn't vacuous).
    assert INTERESTING <= set(trace), sorted(set(trace))

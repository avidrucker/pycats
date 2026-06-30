"""Screen-flow backend equivalence, anchored on a recorded golden (ADR-0002, #100).

Previously this asserted the legacy and statechart screen engines were
transition-equivalent by driving **both live engines** and comparing them to each
*other* per step. ADR-0002 (#174) — whose "delete legacy" ruling **extends to the
screen backend** (`systems/fsm.py` / `LegacyScreenEngine`, epic #100) — removes the
legacy engine in slice 4b, so that live cross-check is going away.

To keep the equivalence from lapsing we anchor it on a **recorded golden** instead: a
frozen snapshot of the LEGACY screen engine's per-step transition sequence for a
representative script (`tests/golden/screen_parity.json`). This mirrors the fighter
parity freeze (#176):

  * the surviving gate is **statechart == golden**
    (`test_statechart_screen_trace_matches_golden`), with no dependence on a live
    legacy engine — it carries on after slice 4b deletes the legacy backend;
  * while legacy still exists (this slice) a second arm asserts **legacy == golden**
    (`test_legacy_screen_trace_matches_golden`), proving the golden faithfully froze
    legacy's behaviour before it is deleted. Slice 4b removes that arm (and the
    legacy entries in the semantic unit tests below) with nothing lost.

The earlier slices' semantic unit tests (initial state, transition order, on_enter/
on_update, force) still drive both backends directly; they pin the engine *semantics*
the golden gate then freezes.

Regen the golden — only after a *reviewed, intended* screen-flow change — by running
this file with ``PYCATS_UPDATE_GOLDENS=1`` (records from the legacy engine).
"""
import json
import os
from pathlib import Path

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


def _run_trace(backend):
    """Drive `backend` through SCRIPT, returning the per-step state sequence."""
    sig = {"v": None}
    eng = make_screen_engine(_screen_like_table(sig), "main_menu", backend)
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


def test_legacy_screen_trace_matches_golden():
    """The legacy screen engine still reproduces the recorded golden — i.e. the
    golden faithfully froze legacy's behaviour. Doubles as the recorder under
    PYCATS_UPDATE_GOLDENS=1. (Removed in slice 4b along with the legacy engine.)"""
    trace = _run_trace("legacy")
    if os.environ.get("PYCATS_UPDATE_GOLDENS") == "1":
        GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN_PATH.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
        return
    assert trace == _load_golden(), f"legacy diverged from golden:\n {trace}"


def test_statechart_screen_trace_matches_golden():
    """THE GATE: the statechart engine reproduces the recorded golden screen-flow
    transition sequence — no dependence on a live legacy engine. Survives slice 4b."""
    trace = _run_trace("statechart")
    assert trace == _load_golden(), f"statechart diverged from golden:\n {trace}"
    # The trace must actually visit the interesting states (golden isn't vacuous).
    assert INTERESTING <= set(trace), sorted(set(trace))

# tests/test_state_engine.py
from pycats.systems.fsm import FSM, Transition
from pycats.systems.state_engine import LegacyEngine


def _toggle_fsm():
    return FSM(
        state="a",
        table={
            "a": [Transition("b", lambda f, ctx: ctx.get("go", False))],
            "b": [Transition("a", lambda f, ctx: ctx.get("back", False))],
        },
    )


def test_legacy_engine_delegates_state():
    eng = LegacyEngine(_toggle_fsm())
    assert eng.state == "a"


def test_legacy_engine_tick_uses_guards():
    eng = LegacyEngine(_toggle_fsm())
    eng.tick({"go": True})
    assert eng.state == "b"


def test_legacy_engine_tick_single_hop():
    # a->b fires; b->a must NOT also fire in the same tick (one hop per tick)
    eng = LegacyEngine(_toggle_fsm())
    eng.tick({"go": True, "back": True})
    assert eng.state == "b"


def test_legacy_engine_force():
    eng = LegacyEngine(_toggle_fsm())
    eng.force("b")
    assert eng.state == "b"

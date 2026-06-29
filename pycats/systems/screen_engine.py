# pycats/systems/screen_engine.py
"""Swappable screen-flow state engines (slice 1 of epic #100).

The screen/menu flow has historically run on the hand-rolled `systems/fsm.py`
guard-table FSM (`ScreenStateManager`). This adds a statecharts-py twin behind the
same tiny surface, mirroring the fighter (`state_engine.py`) and match
(`match_engine.py`) dual-backend templates, so the port can land behind a legacy
default and be proven equivalent by a parity test before the flip.

Transition spec shape (backend-agnostic, shared by both engines):

    transitions = {state_id: [(target_id, guard), ...], ...}

where ``guard(ctx) -> bool``. Within a state the transitions are evaluated in
list order and the FIRST whose guard is True fires (break-after-first) — identical
semantics in both backends, which is what the parity guard pins.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from statecharts import state, statechart, transition, Session

from .fsm import FSM, Transition

ScreenGuard = Callable[[Any], bool]
ScreenTable = Dict[str, List[Tuple[str, ScreenGuard]]]


class LegacyScreenEngine:
    """Runs the transition spec on the hand-rolled FSM (the frozen baseline twin)."""

    def __init__(self, transitions: ScreenTable, initial: str) -> None:
        table = {
            st: [Transition(tgt, self._adapt(g)) for tgt, g in outs]
            for st, outs in transitions.items()
        }
        self._fsm = FSM(state=initial, table=table)

    @staticmethod
    def _adapt(guard: ScreenGuard):
        # The FSM calls guards as guard(fsm, ctx); the fsm arg is vestigial for
        # screen guards, so adapt to the backend-agnostic guard(ctx) contract.
        return lambda _fsm, ctx: guard(ctx)

    @property
    def state(self) -> str:
        return self._fsm.state

    def update(self, ctx: Any = None) -> None:
        self._fsm.update(ctx)


class StatechartScreenEngine:
    """Runs the same transition spec on a statecharts-py Session."""

    def __init__(self, transitions: ScreenTable, initial: str) -> None:
        self._ctx: Any = None
        self._ids = list(transitions.keys())
        states = []
        for st, outs in transitions.items():
            trs = [
                transition({"event": "step", "cond": self._mk_cond(g), "target": tgt})
                for tgt, g in outs
            ]
            states.append(state({"id": st}, *trs))
        self._session = Session(statechart({"initial": initial}, *states))

    def _mk_cond(self, guard: ScreenGuard):
        # Read the ctx stashed on the engine each update() so the chart cond sees
        # the same ctx the legacy guard(ctx) does.
        return lambda e, d: guard(self._ctx)

    @property
    def state(self) -> str:
        for st in self._ids:
            if self._session.in_state(st):
                return st
        raise RuntimeError("screen statechart in no known state")

    def update(self, ctx: Any = None) -> None:
        self._ctx = ctx
        self._session.send("step")


def make_screen_engine(transitions: ScreenTable, initial: str, backend: str = "legacy"):
    """Build the screen-flow engine. backend in {"legacy","statechart"}."""
    if backend == "statechart":
        return StatechartScreenEngine(transitions, initial)
    return LegacyScreenEngine(transitions, initial)

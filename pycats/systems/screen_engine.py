# pycats/systems/screen_engine.py
"""Screen-flow state engine (epic #100).

The screen/menu flow historically ran on a hand-rolled guard-table FSM. That legacy
engine has been retired (ADR-0002, screen addendum; slices 4a/4b of #100): the flow now
runs solely on a statecharts-py `Session`. Its behaviour was frozen as a recorded golden
(`tests/golden/screen_parity.json`) before the legacy engine was deleted, so
`tests/test_screen_parity.py` still guards the transition semantics.

Transition spec shape:

    transitions = {state_id: [(target_id, guard), ...], ...}    guard(ctx) -> bool
    on_enter    = {state_id: handler(ctx)}   # fired on ENTRY to a state (not initial)
    on_update   = {state_id: handler(ctx)}   # fired each update() for the current state

Within a state the transitions are evaluated in list order and the FIRST whose guard
is True fires (break-after-first). Per update(): at most one transition hops; if it
does, the target's on_enter fires; then the (post-hop) current state's on_update fires.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from statecharts import state, statechart, transition, Session

ScreenGuard = Callable[[Any], bool]
ScreenHandler = Callable[[Any], None]
ScreenTable = Dict[str, List[Tuple[str, ScreenGuard]]]
ScreenActions = Dict[str, ScreenHandler]


class StatechartScreenEngine:
    """Runs the transition spec on a statecharts-py Session."""

    def __init__(self, transitions: ScreenTable, initial: str,
                 on_enter: Optional[ScreenActions] = None,
                 on_update: Optional[ScreenActions] = None) -> None:
        self._ctx: Any = None
        self._ids = list(transitions.keys())
        self._on_enter = on_enter or {}
        self._on_update = on_update or {}
        states = []
        for st, outs in transitions.items():
            trs = [
                transition({"event": "step", "cond": self._mk_cond(g), "target": tgt})
                for tgt, g in outs
            ]
            # Force-event transitions: a non-guard-driven jump to any other state
            # (force(label) below), mirroring force_ko/force_idle on the fighter chart.
            trs += [
                transition({"event": "force_" + tgt, "target": tgt})
                for tgt in self._ids if tgt != st
            ]
            states.append(state({"id": st}, *trs))
        self._session = Session(statechart({"initial": initial}, *states))

    def _mk_cond(self, guard: ScreenGuard):
        # Read the ctx stashed on the engine each update() so the chart cond sees
        # the same ctx the guard(ctx) does.
        return lambda e, d: guard(self._ctx)

    @property
    def state(self) -> str:
        for st in self._ids:
            if self._session.in_state(st):
                return st
        raise RuntimeError("screen statechart in no known state")

    def update(self, ctx: Any = None) -> None:
        self._ctx = ctx
        prev = self.state
        self._session.send("step")          # at most one hop (no eventless transitions)
        cur = self.state
        if cur != prev and cur in self._on_enter:
            self._on_enter[cur](ctx)         # entry action
        if cur in self._on_update:
            self._on_update[cur](ctx)        # current (post-hop) state's update

    def force(self, label: str) -> None:
        # Non-guard-driven jump (e.g. ESC-hold return-to-menu); fire the target's
        # on_enter, mirroring a real entry.
        self._session.send("force_" + label)
        if label in self._on_enter:
            self._on_enter[label](None)


def make_screen_engine(transitions: ScreenTable, initial: str, backend: str = "statechart",
                       on_enter: Optional[ScreenActions] = None,
                       on_update: Optional[ScreenActions] = None):
    """Build the screen-flow engine (statecharts-py only).

    The `backend` parameter is now single-valued — the legacy engine was deleted in
    slice 4b of #100 — and is removed entirely in slice 4c along with the
    `PYCATS_SCREEN_BACKEND` selection plumbing.
    """
    return StatechartScreenEngine(transitions, initial, on_enter, on_update)

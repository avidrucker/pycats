# pycats/systems/screen_engine.py
"""Swappable screen-flow state engines (epic #100).

The screen/menu flow has historically run on the hand-rolled `systems/fsm.py`
guard-table FSM (`ScreenStateManager`). This adds a statecharts-py twin behind the
same tiny surface, mirroring the fighter (`state_engine.py`) and match
(`match_engine.py`) dual-backend templates, so the port can land behind a legacy
default and be proven equivalent by a parity test before the flip.

Transition spec shape (backend-agnostic, shared by both engines):

    transitions = {state_id: [(target_id, guard), ...], ...}    guard(ctx) -> bool
    on_enter    = {state_id: handler(ctx)}   # fired on ENTRY to a state (not initial)
    on_update   = {state_id: handler(ctx)}   # fired each update() for the current state

Within a state the transitions are evaluated in list order and the FIRST whose
guard is True fires (break-after-first) — identical semantics in both backends,
which is what the parity guard pins. Per update(): at most one transition hops; if
it does, the target's on_enter fires; then the (post-hop) current state's on_update
fires. This matches `systems/fsm.py` exactly.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from statecharts import state, statechart, transition, Session

from .fsm import FSM, Transition

ScreenGuard = Callable[[Any], bool]
ScreenHandler = Callable[[Any], None]
ScreenTable = Dict[str, List[Tuple[str, ScreenGuard]]]
ScreenActions = Dict[str, ScreenHandler]


class LegacyScreenEngine:
    """Runs the transition spec on the hand-rolled FSM (the frozen baseline twin)."""

    def __init__(self, transitions: ScreenTable, initial: str,
                 on_enter: Optional[ScreenActions] = None,
                 on_update: Optional[ScreenActions] = None) -> None:
        table = {
            st: [Transition(tgt, self._adapt_guard(g)) for tgt, g in outs]
            for st, outs in transitions.items()
        }
        self._fsm = FSM(
            state=initial,
            table=table,
            on_enter={st: self._adapt_action(h) for st, h in (on_enter or {}).items()},
            on_update={st: self._adapt_action(h) for st, h in (on_update or {}).items()},
        )

    @staticmethod
    def _adapt_guard(guard: ScreenGuard):
        # The FSM calls guards as guard(fsm, ctx); the fsm arg is vestigial for
        # screen guards, so adapt to the backend-agnostic guard(ctx) contract.
        return lambda _fsm, ctx: guard(ctx)

    @staticmethod
    def _adapt_action(handler: ScreenHandler):
        # FSM calls on_enter/on_update as fn(fsm, ctx); adapt to handler(ctx).
        return lambda _fsm, ctx: handler(ctx)

    @property
    def state(self) -> str:
        return self._fsm.state

    def update(self, ctx: Any = None) -> None:
        self._fsm.update(ctx)

    def force(self, label: str) -> None:
        # Non-guard-driven jump (e.g. ESC-hold return-to-menu); fire the target's
        # on_enter, mirroring a real entry.
        self._fsm.state = label
        h = self._fsm.on_enter.get(label)
        if h is not None:
            h(self._fsm, None)


class StatechartScreenEngine:
    """Runs the same transition spec on a statecharts-py Session."""

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
        prev = self.state
        self._session.send("step")          # at most one hop (no eventless transitions)
        cur = self.state
        if cur != prev and cur in self._on_enter:
            self._on_enter[cur](ctx)         # entry action, mirroring FSM._switch
        if cur in self._on_update:
            self._on_update[cur](ctx)        # current (post-hop) state's update

    def force(self, label: str) -> None:
        # Non-guard-driven jump (e.g. ESC-hold return-to-menu); fire the target's
        # on_enter, mirroring a real entry.
        self._session.send("force_" + label)
        if label in self._on_enter:
            self._on_enter[label](None)


def make_screen_engine(transitions: ScreenTable, initial: str, backend: str = "legacy",
                       on_enter: Optional[ScreenActions] = None,
                       on_update: Optional[ScreenActions] = None):
    """Build the screen-flow engine. backend in {"legacy","statechart"}."""
    if backend == "statechart":
        return StatechartScreenEngine(transitions, initial, on_enter, on_update)
    return LegacyScreenEngine(transitions, initial, on_enter, on_update)

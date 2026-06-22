# pycats/systems/state_engine.py
"""Swappable state-machine engines behind a common interface.

LegacyEngine wraps the hand-rolled FSM. StatechartEngine (added later) wraps a
statecharts-py Session. Both expose the same tiny surface so Player can use
either interchangeably.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StateEngine(Protocol):
    state: str

    def tick(self, ctx: Any) -> None: ...

    def force(self, label: str) -> None: ...


class LegacyEngine:
    """Wraps the existing pycats.systems.fsm.FSM verbatim."""

    def __init__(self, fsm) -> None:
        self._fsm = fsm

    @property
    def state(self) -> str:
        return self._fsm.state

    def tick(self, ctx: Any = None) -> None:
        self._fsm.update(ctx)

    def force(self, label: str) -> None:
        self._fsm.state = label


def make_state_engine(player, backend: str = "legacy") -> StateEngine:
    """Build the state engine for a Player. backend in {"legacy","statechart"}."""
    if backend == "statechart":
        from statecharts import Session
        from ..statecharts.fighter_chart import build_fighter_chart
        from .state_engine_sc import StatechartEngine

        return StatechartEngine(Session(build_fighter_chart(player)))
    return LegacyEngine(player._build_fsm())

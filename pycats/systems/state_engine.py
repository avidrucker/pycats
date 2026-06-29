# pycats/systems/state_engine.py
"""State-machine engine behind a common interface.

StatechartEngine wraps a statecharts-py Session and is the sole fighter-FSM
engine (ADR-0002: the legacy hand-rolled FSM backend was removed in #178). The
StateEngine Protocol is the tiny surface Player uses.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StateEngine(Protocol):
    state: str
    # Defensive-status region label ("vulnerable" | "intangible"). The
    # statechart backend mirrors this in an orthogonal region; the
    # authoritative value used elsewhere is Player.defensive_status, computed
    # directly from Player.invulnerable.
    defensive_status: str

    def tick(self, ctx: Any) -> None: ...

    def force(self, label: str) -> None: ...


def make_state_engine(player, backend: str = "statechart") -> StateEngine:
    """Build the state engine for a Player.

    The statechart engine is the only backend (ADR-0002, #178). ``backend`` is
    retained for signature stability; collapsing the now single-valued
    parameter and its plumbing is slice 3 (#168).
    """
    from statecharts import Session
    from ..charts.fighter_chart import build_fighter_chart
    from .state_engine_sc import StatechartEngine

    return StatechartEngine(Session(build_fighter_chart(player)))

# pycats/systems/match_engine.py
"""Match/stage state with swappable backends. The win-condition rule (by lives)
is the single source in win_condition.winner_index; this drives match phase."""
from __future__ import annotations

from statecharts import state, statechart, transition, Session

from .win_condition import winner_index


class LegacyMatchEngine:
    def __init__(self, players) -> None:
        self._players = players
        self.phase = "in_play"
        self.winner = 0

    def tick(self) -> None:
        w = winner_index(self._players)
        if w:
            self.phase = "match_over"
            self.winner = w


class StatechartMatchEngine:
    def __init__(self, players) -> None:
        self._players = players
        self.winner = 0
        chart = statechart(
            {"initial": "in_play"},
            state(
                {"id": "in_play"},
                transition({"event": "tick",
                            "cond": lambda e, d: winner_index(self._players) != 0,
                            "target": "match_over"}),
            ),
            state({"id": "match_over"}),
        )
        self._session = Session(chart)

    @property
    def phase(self) -> str:
        return "match_over" if self._session.in_state("match_over") else "in_play"

    def tick(self) -> None:
        if self.phase == "in_play":
            w = winner_index(self._players)
            self._session.send("tick")
            if self.phase == "match_over":
                self.winner = w


def make_match_engine(players, backend: str = "legacy"):
    if backend == "statechart":
        return StatechartMatchEngine(players)
    return LegacyMatchEngine(players)

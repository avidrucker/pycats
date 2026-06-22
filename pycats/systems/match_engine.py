# pycats/systems/match_engine.py
"""Match/stage state with swappable backends. Mirrors game.check_win_condition:
P1 out of lives -> winner 2; P2 out -> winner 1; else in_play."""
from __future__ import annotations

from statecharts import state, statechart, transition, Session


def _winner_from_lives(players) -> int:
    p1, p2 = players
    if p1.lives <= 0:
        return 2
    if p2.lives <= 0:
        return 1
    return 0


class LegacyMatchEngine:
    def __init__(self, players) -> None:
        self._players = players
        self.phase = "in_play"
        self.winner = 0

    def tick(self) -> None:
        w = _winner_from_lives(self._players)
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
                            "cond": lambda e, d: _winner_from_lives(self._players) != 0,
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
            w = _winner_from_lives(self._players)
            self._session.send("tick")
            if self.phase == "match_over":
                self.winner = w


def make_match_engine(players, backend: str = "legacy"):
    if backend == "statechart":
        return StatechartMatchEngine(players)
    return LegacyMatchEngine(players)

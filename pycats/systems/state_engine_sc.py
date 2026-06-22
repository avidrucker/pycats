"""StateEngine backed by a statecharts-py Session (the benchmark subject)."""
from __future__ import annotations

from typing import Any

LABELS = ("idle", "run", "jump", "fall", "shield", "dodge", "ko", "hurt",
          "stun", "attack")


class StatechartEngine:
    def __init__(self, session) -> None:
        self._session = session

    @property
    def state(self) -> str:
        for label in LABELS:
            if self._session.in_state(label):
                return label
        raise RuntimeError("statechart in no known fighter state")

    @property
    def defensive_status(self) -> str:
        return "intangible" if self._session.in_state("intangible") else "vulnerable"

    def tick(self, ctx: Any = None) -> None:
        self._session.send("tick")

    def force(self, label: str) -> None:
        self._session.send("force_" + label)

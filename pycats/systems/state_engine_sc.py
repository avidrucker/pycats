"""StateEngine backed by a statecharts-py Session (the benchmark subject)."""
from __future__ import annotations

from typing import Any

# Flat labels whose chart leaf id equals the label. "attack" is NOT here: the
# attacking region was split into startup/active/recovery sub-phases (Task 4),
# so it is mapped separately via in_state("attacking") -> "attack".
LABELS = ("idle", "run", "jump", "fall", "shield", "dodge", "ko", "hurt",
          "stun")


class StatechartEngine:
    def __init__(self, session) -> None:
        self._session = session

    @property
    def state(self) -> str:
        # The attacking region (startup/active/recovery sub-phases) collapses to
        # the single flat label "attack" so player.state is unchanged across the
        # whole move (Task 4).
        if self._session.in_state("attacking"):
            return "attack"
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

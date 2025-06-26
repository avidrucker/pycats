# pycats/systems/fsm.py
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List

StateFn = Callable[["FSM", Any], None]
GuardFn = Callable[["FSM", Any], bool]


@dataclass
class Transition:
    to_state: str
    guard: GuardFn  # returns True if transition should fire


@dataclass
class FSM:
    state: str
    on_enter: Dict[str, StateFn] = field(default_factory=dict)
    on_update: Dict[str, StateFn] = field(default_factory=dict)
    table: Dict[str, List[Transition]] = field(default_factory=dict)

    def update(self, ctx: Any = None):
        """Run guards then the current state's on_update."""
        for trans in self.table.get(self.state, []):
            if trans.guard(self, ctx):
                self._switch(trans.to_state, ctx)
                break
        if fn := self.on_update.get(self.state):
            fn(self, ctx)

    # ---------------------------------------------------------
    def _switch(self, nxt: str, ctx):
        if nxt == self.state:
            return
        if f := self.on_enter.get(nxt):
            f(self, ctx)  # treat as 'on_enter'
        self.state = nxt

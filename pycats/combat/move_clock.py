"""
pycats/combat/move_clock.py

MoveClock — the single source of truth for "where are we in the current move?".

Replaces the triple-tracked move-progress state that used to live on `Player`
(`current_move` / `move_frame` / `_move_hitbox_spawned`, plus the legacy
`attack_timer` and `done_attacking` shims that had to be hand-kept in sync). One
object owns the executing `MoveData` and the frame counter; `Player` derives
`attack_timer` (== `remaining`), `current_move` and `move_frame` from it, so the
legacy FSM and the statechart keep reading byte-identical values.

Frame convention (unchanged from the old inline clock): POST-increment.
``start()`` sets frame 0; the first ``tick()`` of the move makes ``frame == 1``.
The active window is ``startup < frame <= startup + active`` and the move
completes (becomes inactive) when ``frame >= startup + active + recovery``.

Invariant the golden snapshots rely on: while a move is live,
``remaining == total - frame`` (i.e. the legacy ``attack_timer`` equals
``total - move_frame``).
"""
from __future__ import annotations

from typing import NamedTuple, Optional

from pycats.combat.data import Hitbox, MoveData


class MoveTick(NamedTuple):
    """Result of a single :meth:`MoveClock.tick`.

    spawn    — the move's full hitbox tuple to add this frame (#130: multi-hitbox
               per move), or None on every frame except the one the active window
               opens.
    lifetime — that move's active-frame count (only meaningful when spawn is not
               None); mirrors the legacy ``lifetime=move.active``.
    in_air   — whether the spawning move is an aerial (#133: aerials don't clank);
               False on no-spawn ticks.
    """

    spawn: Optional[tuple[Hitbox, ...]]
    lifetime: int
    in_air: bool = False


class MoveClock:
    """Owns the currently-executing move and its frame counter."""

    def __init__(self) -> None:
        self._move: Optional[MoveData] = None
        self._frame: int = 0
        self._spawned: bool = False

    # -- lifecycle -----------------------------------------------------------
    def start(self, move: MoveData) -> None:
        """Begin executing ``move`` from frame 0."""
        self._move = move
        self._frame = 0
        self._spawned = False

    def reset(self) -> None:
        """Clear to the idle (no-move) state."""
        self._move = None
        self._frame = 0
        self._spawned = False

    # -- derived reads (back the Player properties) --------------------------
    @property
    def move(self) -> Optional[MoveData]:
        return self._move

    @property
    def frame(self) -> int:
        return self._frame

    @property
    def is_active(self) -> bool:
        return self._move is not None

    @property
    def remaining(self) -> int:
        """Frames until the move completes — the legacy ``attack_timer``. 0 when
        no move is active; never negative (a completed move clears the move)."""
        if self._move is None:
            return 0
        total = self._move.startup + self._move.active + self._move.recovery
        return total - self._frame

    # -- per-frame advance ---------------------------------------------------
    def tick(self) -> MoveTick:
        """Advance one frame while a move is live.

        Spawns the move's full hitbox tuple exactly once, on the first frame of
        the active window (#130). Clears the move when it completes, so
        ``remaining`` reads 0 and further ticks are no-ops. A no-op tick (no live
        move) returns ``MoveTick(None, 0)``.
        """
        if self._move is None:
            return MoveTick(None, 0)
        m = self._move
        self._frame += 1
        spawn: Optional[tuple[Hitbox, ...]] = None
        if m.startup < self._frame <= m.startup + m.active and not self._spawned:
            self._spawned = True
            spawn = m.hitboxes
        if self._frame >= m.startup + m.active + m.recovery:
            self._move = None
        return MoveTick(spawn, m.active, m.in_air)

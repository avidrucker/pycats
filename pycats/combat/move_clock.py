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

from typing import NamedTuple

from pycats.combat.data import Hitbox, MoveData


class MoveTick(NamedTuple):
    """Result of a single :meth:`MoveClock.tick`.

    spawn    — the hitboxes of the temporal window opening this frame (#130:
               multi-hitbox per move; #204: a move may open several windows on
               different frames), or None on frames where no window opens. A move
               with no per-box timing opens one window holding its full tuple.
    lifetime — the spawning window's length in frames (only meaningful when spawn
               is not None). For a no-timing move this is ``move.active``, mirroring
               the legacy ``lifetime=move.active``.
    in_air   — whether the spawning move is an aerial (#133: aerials don't clank);
               False on no-spawn ticks.
    """

    spawn: tuple[Hitbox, ...] | None
    lifetime: int
    in_air: bool = False


class MoveClock:
    """Owns the currently-executing move and its frame counter."""

    def __init__(self) -> None:
        self._move: MoveData | None = None
        self._frame: int = 0
        # Per-hitbox temporal windows (#204): start-frame -> (boxes, lifetime),
        # and the set of window start-frames already fired. A move with no per-box
        # timing has exactly one window (start = startup+1, lifetime = active), so
        # the spawn behavior + MoveTick shape are byte-identical to before.
        self._windows: dict[int, tuple[tuple[Hitbox, ...], int]] = {}
        self._spawned_starts: set[int] = set()

    # -- lifecycle -----------------------------------------------------------
    def start(self, move: MoveData) -> None:
        """Begin executing ``move`` from frame 0."""
        self._move = move
        self._frame = 0
        self._windows = self._compute_windows(move)
        self._spawned_starts = set()

    def reset(self) -> None:
        """Clear to the idle (no-move) state."""
        self._move = None
        self._frame = 0
        self._windows = {}
        self._spawned_starts = set()

    @staticmethod
    def _compute_windows(
        move: MoveData,
    ) -> dict[int, tuple[tuple[Hitbox, ...], int]]:
        """Group a move's hitboxes into temporal windows, keyed by START frame.

        A box with no per-box timing uses the move's default window
        ``[startup+1, startup+active]`` (today's single-window behavior); a timed
        box uses its own ``[active_start, active_end]``. Boxes sharing an identical
        window spawn together. Returns ``{start_frame: (boxes, lifetime)}`` where
        ``lifetime = end - start + 1``. At most one window per start frame (the
        same-start/same-end constraint, validated in data.py).
        """
        default_window = (move.startup + 1, move.startup + move.active)
        grouped: dict[tuple[int, int], list[Hitbox]] = {}
        order: list[tuple[int, int]] = []
        for hb in move.hitboxes:
            if hb.active_start is None:
                window = default_window
            else:
                window = (hb.active_start, hb.active_end)
            if window not in grouped:
                grouped[window] = []
                order.append(window)
            grouped[window].append(hb)
        return {start: (tuple(grouped[(start, end)]), end - start + 1) for (start, end) in order}

    # -- derived reads (back the Player properties) --------------------------
    @property
    def move(self) -> MoveData | None:
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

        Spawns each temporal window's hitboxes on that window's start frame (#204:
        sequential multi-hit). A move with no per-box timing has a single window
        opening on the first active frame, so this stays byte-identical to the old
        single-spawn behavior (#130). Clears the move when it completes, so
        ``remaining`` reads 0 and further ticks are no-ops. A no-op tick (no live
        move) returns ``MoveTick(None, 0)``.
        """
        if self._move is None:
            return MoveTick(None, 0)
        m = self._move
        self._frame += 1
        spawn: tuple[Hitbox, ...] | None = None
        lifetime = m.active
        window = self._windows.get(self._frame)
        if window is not None and self._frame not in self._spawned_starts:
            self._spawned_starts.add(self._frame)
            spawn, lifetime = window
        if self._frame >= m.startup + m.active + m.recovery:
            self._move = None
        return MoveTick(spawn, lifetime, m.in_air)

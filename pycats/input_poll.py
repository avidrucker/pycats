# pycats/input_poll.py
"""Present-layer input polling — the pygame-framework half of the old core/input.

`poll()` reads the pygame event queue (framework, not a value type), so per
ADR-0004 / decision #9 it cannot live in the rules core. It stays here and is
called once per tick by `game.py`. The pygame-free port (`InputFrame` +
`merge_frames`) remains in `core/input.py`.
"""

import pygame as pg  # type: ignore

from .core.input import InputFrame

_currently_held: set[int] = set()


def poll() -> tuple[InputFrame, list[pg.event.Event]]:
    """Call once per tick; returns edge-aware key info."""
    global _currently_held

    events = pg.event.get()

    keys_down = {e.key for e in events if e.type == pg.KEYDOWN}
    keys_up = {e.key for e in events if e.type == pg.KEYUP}

    # Maintain held keys manually based on KEYDOWN/KEYUP
    _currently_held.update(keys_down)
    _currently_held.difference_update(keys_up)

    return (
        InputFrame(
            held=_currently_held.copy(),  # defensive copy
            pressed=keys_down,
            released=keys_up,
        ),
        events,
    )

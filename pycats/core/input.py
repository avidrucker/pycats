# pycats/core/input.py
from dataclasses import dataclass
import pygame as pg  # type: ignore


@dataclass
class InputFrame:
    held: set[int]  # keys held down this frame
    pressed: set[int]  # keys that went down THIS frame
    released: set[int]  # keys that were up THIS frame


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

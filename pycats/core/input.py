# pycats/core/input.py
from dataclasses import dataclass
import pygame as pg  # type: ignore

#### TODO: research how key buffering is typically done for fighting games
#### TODO: implement buffered keys for smash attacks, consecutive regular attacks that require fresh presses, and directional inputs for attacks (e.g. up, down, left, right) that can be buffered for a short time


@dataclass
class InputFrame:
    held: set[int]  # keys held down this frame
    pressed: set[int]  # keys that went down THIS frame, i.e. "just pressed"
    released: set[int]  # keys that were up THIS frame, i.e. "just released"
    # buffered: set[int]   # keys pressed in the last N frames

    # to string method
    def __str__(self) -> str:
        return (
            f"InputFrame(held={self.held}, "
            f"pressed={self.pressed}, "
            f"released={self.released})"
        )


def merge_frames(frames) -> InputFrame:
    """Union several InputFrames into one (held/pressed/released each set-unioned).

    Used to drive both players from per-player controllers: each controller emits
    only its own keymap's keycodes (P1_KEYS / P2_KEYS are disjoint), so the union
    is unambiguous and order-independent. Inputs are not mutated.
    """
    held: set[int] = set()
    pressed: set[int] = set()
    released: set[int] = set()
    for fr in frames:
        held |= fr.held
        pressed |= fr.pressed
        released |= fr.released
    return InputFrame(held=held, pressed=pressed, released=released)


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

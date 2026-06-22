"""Deterministic scripted input for headless battle replays.

A timeline is a list of InputSpans; compile_timeline turns it into one
InputFrame per frame with correct held/pressed/released edges, so the headless
runner can drive Player.update without pygame events.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.input import InputFrame

ACTIONS = ("left", "right", "up", "down", "attack", "shield")


@dataclass(frozen=True)
class InputSpan:
    start: int            # first frame the action is held (inclusive)
    end: int              # first frame the action is NOT held (exclusive)
    player: int           # 1 or 2
    action: str           # one of ACTIONS


def compile_timeline(spans, keymaps):
    """spans -> list[InputFrame]. keymaps = [p1_controls, p2_controls]."""
    if not spans:
        return []
    total = max(s.end for s in spans)
    # held_keys[f] = set of keycodes held on frame f
    held_per_frame = [set() for _ in range(total)]
    for s in spans:
        keymap = keymaps[s.player - 1]
        key = keymap[s.action]
        for f in range(s.start, s.end):
            held_per_frame[f].add(key)

    frames = []
    prev = set()
    for f in range(total):
        held = held_per_frame[f]
        pressed = held - prev
        released = prev - held
        frames.append(InputFrame(held=set(held), pressed=set(pressed),
                                 released=set(released)))
        prev = held
    return frames


# A scripted battle that visits every action-state. Frame numbers chosen so each
# move resolves before the next begins (timers in config.py: DODGE_TIME=14,
# HURT_TIME=12, PLAYER_ATTACK_DURATION=12).
DEFAULT_SCRIPT = [
    InputSpan(10, 40, 1, "right"),    # P1 walk/run
    InputSpan(50, 51, 1, "up"),       # P1 jump
    InputSpan(60, 61, 1, "up"),       # P1 double jump
    InputSpan(90, 91, 1, "attack"),   # P1 attack
    InputSpan(110, 140, 1, "shield"), # P1 shield
    InputSpan(120, 121, 1, "left"),   # P1 roll dodge (shield held + dir)
    InputSpan(30, 60, 2, "left"),     # P2 walk toward P1
    InputSpan(95, 96, 2, "attack"),   # P2 attack (may hit P1)
    InputSpan(150, 151, 2, "up"),     # P2 jump
]


def default_timeline(keymaps):
    return compile_timeline(DEFAULT_SCRIPT, keymaps)

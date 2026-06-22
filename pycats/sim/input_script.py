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


# A scripted battle that exercises the hurt and ko states.
#
# Setup: the DEFAULT_SCRIPT already moves both players onto the thick main
# platform and leaves them ~48 px apart (P1 centre≈424, P2 centre≈472) from
# frames 120-149.  After P1's shield drops at frame 140, P1 is idle and P2 is
# idle — perfect for a grounded hit chain.
#
# Frame 141: P1 attacks P2 → P2 enters "hurt" (hurt_timer=12).
# Frames 142-164: P1 chases right to stay in range.
# Frames 165, 185, 210, 240: P1 lands additional hits, each raising P2's
# percent by 10 and increasing knockback velocity.  After ~4-5 hits P2's
# cumulative knockback is strong enough to carry it past the right blast zone
# (SCREEN_WIDTH + BLAST_PADDING = 1010 px), triggering "ko".
# P2 then respawns after RESPAWN_DELAY_FRAMES (120 frames) and transitions
# back to "idle", completing the ko→idle arc.
#
# Timer reference (config.py): HURT_TIME=12, PLAYER_ATTACK_DURATION=12,
# ATTACK_LIFETIME=12, RESPAWN_DELAY_FRAMES=120.
COMBAT_SCRIPT = list(DEFAULT_SCRIPT) + [
    InputSpan(141, 142, 1, "attack"),   # P1 hits P2 on the ground → P2 hurt
    InputSpan(142, 165, 1, "right"),    # P1 chases P2 rightward
    InputSpan(165, 166, 1, "attack"),   # second hit (P2 percent 20)
    InputSpan(166, 185, 1, "right"),    # keep chasing
    InputSpan(185, 186, 1, "attack"),   # third hit (P2 percent 30)
    InputSpan(186, 210, 1, "right"),    # keep chasing
    InputSpan(210, 211, 1, "attack"),   # fourth hit (P2 percent 40)
    InputSpan(211, 240, 1, "right"),    # keep chasing
    InputSpan(240, 241, 1, "attack"),   # fifth hit → enough knockback to KO P2
]

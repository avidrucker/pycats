"""Deterministic scripted input for headless battle replays.

A timeline is a list of InputSpans; compile_timeline turns it into one
InputFrame per frame with correct held/pressed/released edges, so the headless
runner can drive Player.update without pygame events.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.input import InputFrame

ACTIONS = ("left", "right", "up", "down", "attack", "shield", "smash")


@dataclass(frozen=True)
class InputSpan:
    start: int  # first frame the action is held (inclusive)
    end: int  # first frame the action is NOT held (exclusive)
    player: int  # 1 or 2
    action: str  # one of ACTIONS


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
        frames.append(InputFrame(held=set(held), pressed=set(pressed), released=set(released)))
        prev = held
    return frames


# A scripted battle that visits every action-state. Frame numbers chosen so each
# move resolves before the next begins (timers in config.py: DODGE_TIME=14,
# HURT_TIME=12, PLAYER_ATTACK_DURATION=12).
DEFAULT_SCRIPT = [
    InputSpan(10, 40, 1, "right"),  # P1 walk/run
    InputSpan(50, 51, 1, "up"),  # P1 jump
    InputSpan(60, 61, 1, "up"),  # P1 double jump
    InputSpan(90, 91, 1, "attack"),  # P1 attack
    InputSpan(110, 140, 1, "shield"),  # P1 shield
    InputSpan(120, 121, 1, "left"),  # P1 roll dodge (shield held + dir)
    InputSpan(30, 60, 2, "left"),  # P2 walk toward P1
    InputSpan(95, 96, 2, "attack"),  # P2 attack (may hit P1)
    InputSpan(150, 151, 2, "up"),  # P2 jump
]


def default_timeline(keymaps):
    return compile_timeline(DEFAULT_SCRIPT, keymaps)


# A scripted battle that exercises the hurt and ko states via a legitimate,
# fully-charged smash KO — NOT the pre-#475 self-destruct (the old version relied on
# the ledge-hang auto-drop timeout, which #475 removed; see #588).
#
# Intended characters: **Nalio (P1) vs Birky (P2)** — the combat golden passes these to
# run_battle (test_golden_combat). The default cat (used by test_runner) still produces
# attacks from the jab spans, so the "attacks appear" contract holds there too.
#
# Choreography (spike-derived in #588):
# - DEFAULT_SCRIPT settles both on the main platform ~48 px apart (~frame 120).
# - Frame 141-145: P1 closes the gap with a short walk (jab reach ~34-54 px).
# - Frames 148..428: P1 jabs IN PLACE every 8 frames (36 jabs). Birky, driven by no
#   inputs, is pinned near centre-stage (x≈501, gap ≈50) and racks to ~69% — jab-in-place
#   avoids the overshoot-to-the-ledge that a walking chase causes. (36, not 34, since #599:
#   the PM-correct smash — 1.3671× over 59f — is ~2.4% weaker than the old Brawl 1.4×/60f,
#   so the margin side-blast KO needs a few more % of rack-up to still land.)
# - Frame 452: after a 16-frame settle to idle (so the smash press registers), P1 holds
#   right+smash for ~62 frames → a FULLY charged forward-smash (charge = SMASH_CHARGE_FRAMES,
#   59f) fires ~frame 511. It deals ~+19% (→ ~88%) and launches Birky right off the blast
#   zone (SCREEN_WIDTH + BLAST_PADDING = 1010 px) → "ko" at ~69%→88%, P1 safe at x≈466.
#   (A vertical up-smash KO was ruled infeasible in the #588 spike: it needs ~140%+ and
#   pixel-perfect overlap; the side-blast fsmash is the sanctioned fallback.)
# - P2 respawns after RESPAWN_DELAY_FRAMES, completing the ko→idle arc.
_COMBAT_JAB_START = 148
_COMBAT_N_JABS = 36
_COMBAT_JAB_PERIOD = 8
_COMBAT_FSMASH_START = _COMBAT_JAB_START + _COMBAT_N_JABS * _COMBAT_JAB_PERIOD + 16  # 452
COMBAT_SCRIPT = (
    list(DEFAULT_SCRIPT)
    + [InputSpan(141, 146, 1, "right")]  # close the initial ~48px gap into jab range
    + [
        InputSpan(
            _COMBAT_JAB_START + i * _COMBAT_JAB_PERIOD, _COMBAT_JAB_START + i * _COMBAT_JAB_PERIOD + 1, 1, "attack"
        )
        for i in range(_COMBAT_N_JABS)  # rack Birky to ~69% with in-place jabs
    ]
    + [
        # fully-charged forward smash: right sets the f-smash direction; smash charges
        # (movement locks during smash_charge) and auto-fires at full charge → side KO.
        InputSpan(_COMBAT_FSMASH_START, _COMBAT_FSMASH_START + 62, 1, "right"),
        InputSpan(_COMBAT_FSMASH_START, _COMBAT_FSMASH_START + 62, 1, "smash"),
    ]
)

"""Shield mechanics — pure rules (#12).

Kept here next to combat/knockback.py (hitstun_frames) so the frame-duration
rules live together and stay import-light for headless tests.
"""
from __future__ import annotations

import math

from ..config import SHIELD_BREAK_STUN_MAX, SHIELD_BREAK_STUN_MIN, SHIELDSTUN_FACTOR


def shield_break_stun_frames(percent: float) -> int:
    """Frames of shield-break 'dizzy' stun for a fighter at ``percent`` damage.

    Melee / Project M formula (SmashWiki 'Stun'): ``(400 - p) + 90`` frames,
    i.e. ``SHIELD_BREAK_STUN_MAX - percent``, clamped to
    ``[SHIELD_BREAK_STUN_MIN, SHIELD_BREAK_STUN_MAX]``. Uniquely among stuns,
    MORE damage means a SHORTER dizzy (490 frames at 0%, 90 at >= 400%).

    Melee's mash-out (-3 frames per input) is intentionally NOT modelled: #12
    locks all inputs during the dizzy, so there is nothing to mash.
    """
    return int(max(SHIELD_BREAK_STUN_MIN, round(SHIELD_BREAK_STUN_MAX - percent)))


def shieldstun_frames(damage: float) -> int:
    """Frames a defender is locked in shield after blocking a hit of ``damage``%.

    SmashWiki *Shieldstun* / the project roadmap: Brawl/PM ``floor(damage *
    SHIELDSTUN_FACTOR)`` with factor 0.345. Attacks under ~2.9% give 0 frames
    (the floor yields that). Defender-only; applied after hitlag (#138). Unlike
    the shield-break dizzy, this is a short block-stun the shield *survives*.
    """
    return math.floor(damage * SHIELDSTUN_FACTOR)

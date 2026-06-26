"""Shield mechanics — pure rules (#12).

Kept here next to combat/knockback.py (hitstun_frames) so the frame-duration
rules live together and stay import-light for headless tests.
"""
from __future__ import annotations

from ..config import SHIELD_BREAK_STUN_MIN, SHIELD_BREAK_STUN_MAX


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

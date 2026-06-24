"""Authentic Brawl/Project-M knockback + hitstun (pure; no pygame).

KB = (((((p/10) + (p*d/20)) * (200/(w+100)) * 1.4) + 18) * (KBG/100)) + BKB
where p = target percent AFTER the hit, d = damage, w = weight, BKB/KBG per hitbox.
Source: https://www.ssbwiki.com/Knockback  (see spec #39 §2).
"""
import math

from ..config import HITSTUN_MULTIPLIER, HITSTUN_FLOOR


def knockback(percent: float, damage: float, weight: int,
              base_knockback: float, knockback_growth: float) -> float:
    """Knockback magnitude (Smash units). `percent` is the post-hit percent."""
    growth = ((percent / 10.0) + (percent * damage / 20.0)) * (200.0 / (weight + 100.0))
    growth = (growth * 1.4) + 18.0
    return (growth * (knockback_growth / 100.0)) + base_knockback


def hitstun_frames(kb: float) -> int:
    """Whole frames of hitstun for a knockback magnitude (floored, min HITSTUN_FLOOR)."""
    return max(HITSTUN_FLOOR, math.floor(kb * HITSTUN_MULTIPLIER))

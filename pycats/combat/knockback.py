"""Authentic Brawl/Project-M knockback + hitstun (pure; no pygame).

KB = (((((p/10) + (p*d/20)) * (200/(w+100)) * 1.4) + 18) * (KBG/100)) + BKB
where p = target percent AFTER the hit, d = damage, w = weight, BKB/KBG per hitbox.
Source: https://www.ssbwiki.com/Knockback  (see spec #39 §2).
"""
import math

from ..config import (
    HITSTUN_MULTIPLIER, HITSTUN_FLOOR,
    HITLAG_DAMAGE_FACTOR, HITLAG_BASE, HITLAG_CAP,
    SAKURAI_AIRBORNE_DEG, SAKURAI_GROUNDED_MAX_DEG,
    SAKURAI_GROUNDED_LOW_KB, SAKURAI_GROUNDED_HIGH_KB,
)


def knockback(percent: float, damage: float, weight: int,
              base_knockback: float, knockback_growth: float) -> float:
    """Knockback magnitude (Smash units). `percent` is the post-hit percent."""
    growth = ((percent / 10.0) + (percent * damage / 20.0)) * (200.0 / (weight + 100.0))
    growth = (growth * 1.4) + 18.0
    return (growth * (knockback_growth / 100.0)) + base_knockback


def sakurai_angle(kb: float, on_ground: bool) -> float:
    """Resolve the Sakurai-angle sentinel (361) to launch degrees.

    SmashWiki "Sakurai angle" (Brawl/PM): an airborne victim is launched at a
    fixed angle; a grounded victim scales LINEARLY from 0° (at/below LOW_KB) up
    to the max (at/above HIGH_KB) — so weak grounded hits stay flat and don't pop
    a grounded opponent straight up, while strong hits approach the airborne
    angle. `kb` is the pycats knockback() magnitude. Pure; no pygame.
    """
    if not on_ground:
        return SAKURAI_AIRBORNE_DEG
    if kb <= SAKURAI_GROUNDED_LOW_KB:
        return 0.0
    if kb >= SAKURAI_GROUNDED_HIGH_KB:
        return SAKURAI_GROUNDED_MAX_DEG
    frac = ((kb - SAKURAI_GROUNDED_LOW_KB)
            / (SAKURAI_GROUNDED_HIGH_KB - SAKURAI_GROUNDED_LOW_KB))
    return SAKURAI_GROUNDED_MAX_DEG * frac


def hitstun_frames(kb: float) -> int:
    """Whole frames of hitstun for a knockback magnitude (floored, min HITSTUN_FLOOR)."""
    return max(HITSTUN_FLOOR, math.floor(kb * HITSTUN_MULTIPLIER))


def hitlag_frames(damage: float) -> int:
    """Whole frames of hitlag (freeze frames) for a clean hit of `damage`%.

    SmashWiki Hitlag (Brawl/PM): floor(damage * HITLAG_DAMAGE_FACTOR + HITLAG_BASE),
    capped at HITLAG_CAP. The per-move (h), electric (e) and crouch-cancel (c)
    multipliers are 1 in this slice (#138). Both attacker and defender freeze for
    this many frames before the knockback slide.
    """
    return min(HITLAG_CAP, math.floor(damage * HITLAG_DAMAGE_FACTOR + HITLAG_BASE))


def decay_velocity(vx: float, decay: float) -> float:
    """Reduce a horizontal launch velocity toward 0 by `decay` per frame.

    Mirrors Smash's per-frame knockback decay (#43): a launched fighter bleeds
    momentum every frame rather than sliding at constant speed. Never overshoots
    or flips sign — once it reaches 0 it stays 0.
    """
    if vx > 0.0:
        return max(0.0, vx - decay)
    if vx < 0.0:
        return min(0.0, vx + decay)
    return 0.0

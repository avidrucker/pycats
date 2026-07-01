"""Smash-charge output scaling (#327 slice 3b).

A charged smash hits harder: at Attack spawn, each hitbox's offensive magnitudes
(damage / base_knockback / knockback_growth) scale by a factor derived from the
charge fraction `c ∈ [0,1]` captured at fire time (fighter.smash_charge_fraction,
#371). Uncharged (c=0) is an exact identity, so an uncharged smash — and every
non-chargeable move — spawns its authored values unchanged (golden-safe).
"""
from dataclasses import replace

from ..config import SMASH_CHARGE_SCALE


def charge_factor(fraction: float) -> float:
    """Output multiplier for a charge fraction: 1.0 at c=0, SMASH_CHARGE_SCALE at
    c=1, linear between. The fraction is clamped to [0, 1]."""
    c = max(0.0, min(1.0, fraction))
    return 1.0 + c * (SMASH_CHARGE_SCALE - 1.0)


def scale_hitboxes(hitboxes, fraction):
    """Return a new tuple with each hitbox's damage/base_knockback/knockback_growth
    scaled by charge_factor(fraction). Position/radius/angle/temporal-windows and
    WDSK are untouched. fraction == 0 returns the input tuple unchanged (identity),
    so an uncharged release is byte-identical to the authored move."""
    factor = charge_factor(fraction)
    if factor == 1.0:
        return hitboxes
    return tuple(
        replace(
            hb,
            damage=hb.damage * factor,
            base_knockback=hb.base_knockback * factor,
            knockback_growth=hb.knockback_growth * factor,
        )
        for hb in hitboxes
    )

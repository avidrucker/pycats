"""Spawn-time smash hitbox rewrites (#327 slices 3b + 4).

At Attack spawn, a smash's hitboxes are rewritten from live smash state:
- charge output scaling (3b; damage-only per #437): a smash's **damage** scales by a
  factor from the charge fraction `c ∈ [0,1]` (fighter.smash_charge_fraction, #371);
  knockback rises through knockback() (damage is an input) — BKB/KBG are NOT scaled
  (scaling them too compounds, #423/#426). c=0 is an exact identity, so uncharged +
  non-chargeable moves are unchanged.
- angled f-smash (4): a forward smash held up/down replaces its launch angle.
Both use dataclasses.replace (Hitbox is frozen) and are golden-safe (the default
cat has no smash, so neither path is reached on the sim/golden cat).
"""
from dataclasses import replace

from ..config import SMASH_CHARGE_SCALE


def charge_factor(fraction: float) -> float:
    """Output multiplier for a charge fraction: 1.0 at c=0, SMASH_CHARGE_SCALE at
    c=1, linear between. The fraction is clamped to [0, 1]."""
    c = max(0.0, min(1.0, fraction))
    return 1.0 + c * (SMASH_CHARGE_SCALE - 1.0)


def scale_hitboxes(hitboxes, fraction):
    """Return a new tuple with each hitbox's **damage** scaled by charge_factor(fraction).

    Charge scales damage only; knockback rises through knockback() (damage is an
    input to the KB formula). base_knockback / knockback_growth are NOT scaled —
    scaling them too double-counts, delivering a spurious extra x(SMASH_CHARGE_SCALE)
    on the KB output (#423/#426, findings doc §4). Position/radius/angle/temporal-
    windows and WDSK are untouched. fraction == 0 returns the input tuple unchanged
    (identity), so an uncharged release is byte-identical to the authored move."""
    factor = charge_factor(fraction)
    if factor == 1.0:
        return hitboxes
    return tuple(
        replace(hb, damage=hb.damage * factor)
        for hb in hitboxes
    )


def angle_smash_hitboxes(hitboxes, angle):
    """Return a new tuple with every hitbox's launch `angle` replaced by `angle`
    (for an angled f-smash, #327 slice 4). Damage/KB/position/windows are unchanged;
    the authored angle (often the Sakurai sentinel) is swapped for the aimed literal."""
    return tuple(replace(hb, angle=angle) for hb in hitboxes)

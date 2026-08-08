"""pycats/combat/units.py

Purpose: the single authoring-time seam from Smash *units* to pixels (#195, #785).

pycats splits per-fighter attributes by kind (the #120 convention):

- **RAW (no scaling)** — unitless combat scalars: `weight`, `damage`, `angle`,
  `base_knockback`/`knockback_growth`, `set_knockback`, frame counts, `max_jumps`.
  These are entered as the rukaidata source number verbatim.
- **`u()` — spatial px (integer)** — hitbox/hurtbox radii + offsets. Distances on the
  integer-pixel sim (#80), so `u()` rounds to an int.
- **`vel()` — velocity/accel px (float)** — the per-fighter movement/physics rates:
  `gravity`, `jump_vel`, `move_speed`, `dash_speed`, `max_fall_speed` (and the
  incoming `air_x_speed` / `air_accel`, #787). These are px-per-frame (or per-frame²)
  rates, so `vel()` keeps a float — it does NOT round to int like `u()`.

Both `u()` and `vel()` apply `config.PX_PER_UNIT ≈ 5.4 px/unit` — the factor is named
once here, not copied as a bare `× 5.4` per value. Author new character velocity data
**raw-first** through `vel()` (`move_speed=vel(1.2)`), so the rukaidata source value
stays visible in the source and the factor lives in one seam (#785).

Note (#785): the *existing* `config.py` velocity defaults (`MOVE_SPEED = 6`, …) and the
current cats are **game-tuned px**, not faithful rukaidata × 5.4 (e.g. `MAX_FALL_SPEED
= 13` is far above Mario's real term vel 1.7 × 5.4 ≈ 9.2). They stay as-is; sourcing
true raw for the shipped cats + any faithful re-tune is a separate design pass. `vel()`
is the authoring path for *new* faithful values (Gnok is its first consumer, #779).

The SIM stays integer-pixel for positions (a determinism asset, #80): `u` rounds to an
int, so `u(3.5) == 19` exactly. Existing baked literals are kept byte-identical
(ADR-0003 C1) and their derivation comments cite `PX_PER_UNIT` by name, not magic 5.4.
"""

from __future__ import annotations

from ..config import PX_PER_UNIT


def u(units: float) -> int:
    """Convert Smash spatial *units* to integer pixels via PX_PER_UNIT.

    `round(units * PX_PER_UNIT)` — the sim is integer-pixel (#80), so the result is
    an int. E.g. `u(3.5) == 19`, `u(3.1) == 17`. Use for hitbox radii/offsets when
    authoring character data; combat scalars stay raw.
    """
    return round(units * PX_PER_UNIT)


def vel(units: float) -> float:
    """Convert a Smash velocity/accel *unit rate* to px-per-frame via PX_PER_UNIT.

    `round(units * PX_PER_UNIT, 2)` — a px/frame (or px/frame²) rate, so unlike `u()`
    this keeps a **float** (velocities are not integer-pixel). Rounded to 2 decimals
    for clean, deterministic values. Use to author per-fighter movement scalars
    raw-first, e.g. `move_speed=vel(1.2)` (→ 6.48), `gravity=vel(0.1)` (→ 0.54); the
    upward jump is `jump_vel=-vel(2.8)` (→ -15.12), negated because pycats jumps are
    negative-y. Combat scalars (weight/%/angle/BKB/KBG/frames/jumps) stay RAW.
    """
    return round(units * PX_PER_UNIT, 2)

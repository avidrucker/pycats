"""
pycats/combat/data.py

Purpose: Frozen dataclass schema for fighter move/hitbox data, plus the
load_fighter_data() seam used by all consumers.

Contents:
- Circle      — 2-D collision circle, offset relative to fighter origin (facing right)
- Hitbox      — one active hitbox: a circle, damage amount, and launch angle
- MoveData    — one move: timing (frames) + one or more hitboxes
- Hurtbox     — the fighter's vulnerable body: one or more circles
- FighterData — full fighter data: hurtbox + named moves dict
- load_fighter_data(character) -> FighterData

Design notes:
- All timing values are integer frames.
- Circle offsets are facing-RIGHT-relative; consumers mirror for left-facing.
- Phase 0: load_fighter_data returns the same default for every character key.
  Phase 1+ will branch per character to TOML/JSON files.
- dict[str, MoveData] on a frozen dataclass is legal: the field holds a dict
  reference, we just never reassign the field.  Callers must not mutate it.
"""

from __future__ import annotations

from dataclasses import dataclass

# Movement-constant defaults live in config; FighterData uses them as field
# defaults so any data that doesn't specify movement == today's globals (the
# default cat / golden sim is unchanged). #126.
from ..config import GRAVITY, MAX_FALL_SPEED, MOVE_SPEED, JUMP_VEL, MAX_JUMPS


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Circle:
    """A 2-D circle, offset (dx, dy) from the fighter origin, radius r.

    All values in pixels. Offsets are facing-RIGHT-relative.
    """
    dx: int
    dy: int
    r: int


@dataclass(frozen=True)
class Hitbox:
    """One active hitbox for a move.

    Fields:
        circle           — position and size (facing-right coords)
        damage           — percentage damage dealt on hit
        angle            — launch angle in degrees (0 = directly right, 90 = up)
        base_knockback   — BKB: knockback at 0% (Phase 1)
        knockback_growth — KBG: how knockback scales with percent (Phase 1)
    """
    circle: Circle
    damage: float
    angle: int
    base_knockback: float = 0.0
    knockback_growth: float = 0.0


@dataclass(frozen=True)
class MoveData:
    """Timing and hitbox data for a single move.

    Fields:
        name      — human-readable move name
        in_air    — True if this is an aerial move, False for ground moves
        startup   — frames before hitbox becomes active
        active    — frames the hitbox is present
        recovery  — frames after the hitbox disappears before the fighter is free
        hitboxes  — one or more Hitbox instances (tuple, immutable)

    Total move duration = startup + active + recovery frames.
    """
    name: str
    in_air: bool
    startup: int
    active: int
    recovery: int
    hitboxes: tuple[Hitbox, ...]


# ---------------------------------------------------------------------------
# Fighter-level data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Hurtbox:
    """The fighter's vulnerable body, represented as a tuple of Circles.

    Circles are in facing-RIGHT-relative coords; consumers mirror for left.
    """
    circles: tuple[Circle, ...]


@dataclass(frozen=True)
class FighterData:
    """Complete data definition for one fighter character.

    Fields:
        hurtbox — the fighter's vulnerable body
        moves   — mapping of move key (e.g. "attack") to MoveData
        weight  — fighter weight fed to the knockback formula (#117/#123). The
                  Smash convention is Mario = 100; defaults to 100 so existing
                  data (the default cat) is unchanged and stays the baseline.
        gravity / max_fall_speed / move_speed / jump_vel / max_jumps —
                  per-character movement constants (#126), read per-fighter by
                  the physics/input layer. Each defaults to the matching config
                  global, so data that omits them behaves exactly as before.

    The dict is not frozen; callers must not mutate it.
    """
    hurtbox: Hurtbox
    moves: dict[str, MoveData]
    weight: int = 100
    gravity: float = GRAVITY
    max_fall_speed: float = MAX_FALL_SPEED
    move_speed: float = MOVE_SPEED
    jump_vel: float = JUMP_VEL
    max_jumps: int = MAX_JUMPS


# ---------------------------------------------------------------------------
# Loader seam
# ---------------------------------------------------------------------------

def load_fighter_data(character: str) -> FighterData:
    """Return FighterData for the named character.

    Phase 1 (#117/#123): per-archetype keys branch to their own definitions;
    every other string still maps to the shared default cat. The sim/golden path
    loads "P1"/"P2" (see sim/runner.py, game.py), so those stay on the default
    and goldens are unaffected by new archetypes.

    Args:
        character: an archetype key (e.g. "nalio"), a CAT_CHARACTERS key, or any
            string. Unknown strings fall through to the default cat.

    Returns:
        FighterData instance (frozen, deterministic, no RNG).
    """
    if character == "nalio":
        from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA
        return NALIO_FIGHTER_DATA
    # default cat for every other key (incl. the "P1"/"P2" sim path)
    from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
    return DEFAULT_FIGHTER_DATA

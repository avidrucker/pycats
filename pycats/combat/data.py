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
        circle  — position and size (facing-right coords)
        damage  — percentage damage dealt on hit
        angle   — launch angle in degrees (0 = directly right, 90 = straight up)

    Phase 0 only: base_knockback and knockback_growth are Phase 1 fields.
    """
    circle: Circle
    damage: float
    angle: int


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

    The dict is not frozen; callers must not mutate it.
    """
    hurtbox: Hurtbox
    moves: dict[str, MoveData]


# ---------------------------------------------------------------------------
# Loader seam
# ---------------------------------------------------------------------------

def load_fighter_data(character: str) -> FighterData:
    """Return FighterData for the named character.

    Phase 0: every character string maps to the same shared default.
    Phase 1+: branch per character to per-file definitions.

    Args:
        character: a CAT_CHARACTERS key (e.g. "calico", "ghost") or any string.

    Returns:
        FighterData instance (frozen, deterministic, no RNG).
    """
    # Phase 0: single default for all characters
    from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
    return DEFAULT_FIGHTER_DATA

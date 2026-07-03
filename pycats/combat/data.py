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
from ..config import GRAVITY, MAX_FALL_SPEED, MOVE_SPEED, JUMP_VEL, MAX_JUMPS, DASH_SPEED


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
        active_start     — per-hitbox temporal window (#204): inclusive START
                           frame in the MoveClock 1-indexed frame coordinate.
                           None = use the move's window [startup+1, startup+active]
                           (today's behavior — the box spawns with the move's
                           default group). Sequential multi-hit moves give boxes
                           different windows so they fire on different frames.
        active_end       — inclusive END frame of the window. Paired with
                           active_start: set both or neither.
        set_knockback    — weight-dependent SET knockback (WDSK, #211). When set
                           to the WDSK value, this hit's launch ignores the
                           victim's percent (a "set" hit) but still scales with the
                           victim's weight + KBG/BKB. None = normal percent-scaling
                           (today's behavior). The hit still deals its `damage` %;
                           only the knockback is set.
    """
    circle: Circle
    damage: float
    angle: int
    base_knockback: float = 0.0
    knockback_growth: float = 0.0
    active_start: int | None = None
    active_end: int | None = None
    set_knockback: int | None = None

    def __post_init__(self) -> None:
        s, e = self.active_start, self.active_end
        if (s is None) != (e is None):
            raise ValueError(
                "Hitbox active_start/active_end must be set together "
                f"(got start={s!r}, end={e!r})"
            )
        if s is not None:
            if s < 1:
                raise ValueError(f"Hitbox active_start {s} must be >= 1")
            if s > e:
                raise ValueError(
                    f"Hitbox window start {s} is after its end {e}"
                )


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
    # Rehit-rate (#213): frames between re-hits of the same target for a LOOPING
    # multi-hit move (the d-air drill). None = single hit per move-instance
    # (today's behavior, the #130 guarantee). A number N = the spawned hitbox
    # re-hits an overlapping target every N frames across its active window.
    rehit_rate: int | None = None
    # Projectile special (#223): when projectile_speed is set, the move spawns a
    # MOVING projectile (an Attack with velocity = facing * projectile_speed) that
    # lives projectile_lifetime frames, detached from the owner. None = a normal
    # static-hitbox move. projectile_speed is a ⚠🔬 GUESS in px/frame (derive via
    # rukaidata units/frame × PX_PER_UNIT / playtest — tracked like #192).
    projectile_speed: int | None = None
    projectile_lifetime: int | None = None
    # Smash charge (#327 slice 3a): a chargeable move is HELD to charge and
    # released to fire (the smash_charge state). Defaults False, so every existing
    # move is byte-identical (golden-safe); slice 3b scales a charged hit's output.
    chargeable: bool = False

    def __post_init__(self) -> None:
        # Per-hitbox temporal-window cross-checks (#204). Per-box shape (paired,
        # non-inverted, start >= 1) is enforced on Hitbox; here we need the move's
        # duration + the sibling boxes: a window must end within the move, and two
        # boxes that start on the same frame must share the same window (v1: one
        # window => one Attack; see move_clock._compute_windows).
        total = self.startup + self.active + self.recovery
        starts: dict[int, int] = {}
        for hb in self.hitboxes:
            if hb.active_start is None:
                continue
            if hb.active_end > total:
                raise ValueError(
                    f"Hitbox window [{hb.active_start}, {hb.active_end}] exceeds "
                    f"move '{self.name}' duration {total}"
                )
            prev_end = starts.get(hb.active_start)
            if prev_end is not None and prev_end != hb.active_end:
                raise ValueError(
                    f"move '{self.name}': two hitboxes share start frame "
                    f"{hb.active_start} with different ends ({prev_end} != "
                    f"{hb.active_end}); same start must share the same window"
                )
            starts[hb.active_start] = hb.active_end


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
        crouch_size / crouch_hurtbox — per-character crouch geometry (#124): the
                  (w, h) the body Rect resizes to when crouching (feet planted)
                  and the shorter/lower hurtbox used while crouched. Both default
                  to None = this fighter cannot crouch. Crouch effectiveness is
                  deliberately per-character (PM: Kirby hugs the ground, DK barely
                  lowers) — see docs and the #124 research notes.
        prone_size / prone_hurtbox — per-character prone/knockdown geometry (#173):
                  the lying-down counterpart of the crouch pair. While prone the
                  body Rect lowers further than crouch (a downed fighter lies flat)
                  and the hurtbox drops with it so high attacks whiff. Both default
                  to None = this fighter has no prone posture (it keeps the stand
                  box while prone). New fields, NOT reused crouch fields: prone is a
                  lower posture than crouch.

    The dict is not frozen; callers must not mutate it.
    """
    hurtbox: Hurtbox
    moves: dict[str, MoveData]
    weight: int = 100
    gravity: float = GRAVITY
    max_fall_speed: float = MAX_FALL_SPEED
    move_speed: float = MOVE_SPEED
    # Walk/dash/run (#388): `move_speed` is the WALK; `dash_speed` is the faster
    # tap-burst (#374 design). Defaults to the config global so existing data is
    # unchanged; the dash is only reached via `_start_dash` (slice 2b's double-tap).
    dash_speed: float = DASH_SPEED
    jump_vel: float = JUMP_VEL
    max_jumps: int = MAX_JUMPS
    # Per-fighter standing body box (#275). None = the global config.PLAYER_SIZE
    # (via owner.SIZE), so the default cat / sim path is unchanged. Symmetric with
    # crouch_size/prone_size; a small archetype (Kirby) sets a shorter box here.
    stand_size: tuple[int, int] | None = None
    crouch_size: tuple[int, int] | None = None
    crouch_hurtbox: Hurtbox | None = None
    prone_size: tuple[int, int] | None = None
    prone_hurtbox: Hurtbox | None = None


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
    if character == "birky":
        from pycats.characters.birky_cat import BIRKY_FIGHTER_DATA
        return BIRKY_FIGHTER_DATA
    if character == "narz":
        from pycats.characters.narz_cat import NARZ_FIGHTER_DATA
        return NARZ_FIGHTER_DATA
    # default cat for every other key (incl. the "P1"/"P2" sim path)
    from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
    return DEFAULT_FIGHTER_DATA


# ---------------------------------------------------------------------------
# Getup-attack (#225 / #146 slice 2): a generic wake-up attack out of `prone`.
# Started directly on the move clock from the getup transition (player.update),
# not via the move-selection seam — so the existing Attack/clank/multi-hit
# plumbing is reused. One low front hitbox for v1; a back hitbox (PM hits both
# sides) is a documented refinement. Frames/box are ⚠ playtest starting points.
# ---------------------------------------------------------------------------
GETUP_ATTACK = MoveData(
    name="getup attack",
    in_air=False,
    startup=4,
    active=3,
    recovery=14,
    hitboxes=(
        Hitbox(circle=Circle(dx=28, dy=42, r=24), damage=8.0, angle=70,
               base_knockback=40.0, knockback_growth=70.0),
    ),
)

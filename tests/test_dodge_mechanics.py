"""Dodge regression tests (#62).

Assert-based ports of the intent that previously lived only in print-based debug
scripts (`scripts/test_*dodge*.py`, relocated from `tests/` in #59 because they
poked the removed `Player.fsm` and asserted nothing). Written against the current
public API: drive `Player.update(...)` and assert on `player.state`,
`player.rect`, `player.on_ground`, `player.vel`, `player.dodge_timer`,
`player.spot_dodge_shield_held`, `player.air_dodge_ok`.

Two dodge families:
  - GROUND spot dodge (shield+down): special physics — no gravity, no fall-through;
    returns to shield while shield stays held.
  - AIR dodge (shield[+direction]): PM/Melee model (#184) — SETS ±DODGE_AIR_SPEED
    horizontally and HALTS vertical momentum (neutral → ~zero), consumes the air
    dodge, and exits into `helpless` (special-fall) until landing. Gravity still
    acts over the dodge frames. (Helpless behaviour: tests/test_air_dodge_helpless.py.)
"""
import pygame as pg

from pycats.config import DODGE_AIR_SPEED, DODGE_SPEED, DODGE_TIME, P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

CONTROLS = {
    "left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
    "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e,
}
LEFT, RIGHT, DOWN, SHIELD = pg.K_a, pg.K_d, pg.K_s, pg.K_q


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _grounded_player(plat_rect, thin):
    """A player settled on the given platform (one empty frame to land)."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(*plat_rect), thin=thin))
    p = Player(x=plat_rect[0] + plat_rect[2] // 2, y=plat_rect[1],
               controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="DodgeCat", facing_right=True)
    p.update(_frame(set(), set()), plats, pg.sprite.Group())  # settle on ground
    return p, plats


def _airborne_player():
    """A player a few frames into a fall (clearly airborne) over a thick floor."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(100, 500, 600, 40), thin=False))
    p = Player(x=300, y=200, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="AirCat", facing_right=True)
    for _ in range(3):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert not p.fighter.on_ground, "fixture precondition: player should be airborne"
    return p, plats


# ----------------------------------------------------------- ground spot dodge

def test_spot_dodge_on_thin_platform_does_not_fall_through():
    """A spot dodge (shield+down) on a THIN platform uses special physics: the
    player stays planted on the SAME platform for EVERY frame of the dodge — never
    begins falling through it (down is held, which would otherwise drop them).

    Per-frame (not just end-state) so a transient drop-and-recover can't hide, and
    so it genuinely exercises the no-gravity special physics."""
    p, plats = _grounded_player((300, 400, 200, 20), thin=True)
    settled_y = p.rect.y
    p.update(_frame({SHIELD, DOWN}, {SHIELD, DOWN}), plats, pg.sprite.Group())
    for _ in range(DODGE_TIME + 1):
        p.update(_frame({SHIELD, DOWN}, set()), plats, pg.sprite.Group())
        assert p.fighter.on_ground, "spot dodge left the ground (started falling through)"
        assert p.rect.y == settled_y, f"player dropped from y={settled_y} to y={p.rect.y}"


def test_spot_dodge_returns_to_shield_while_shield_held():
    """After the dodge window, with shield still held, the player is shielding."""
    p, plats = _grounded_player((600, 400, 200, 20), thin=False)
    p.update(_frame({SHIELD, DOWN}, {SHIELD, DOWN}), plats, pg.sprite.Group())
    assert p.state == "dodge" and p.fighter.spot_dodge_shield_held
    for _ in range(DODGE_TIME + 1):
        p.update(_frame({SHIELD, DOWN}, set()), plats, pg.sprite.Group())
    assert p.state == "shield", f"expected return to shield, got {p.state!r}"


# ----------------------------------------------------------------- air dodge

def test_right_air_dodge_applies_positive_dodge_speed():
    p, plats = _airborne_player()
    p.update(_frame({SHIELD, RIGHT}, {SHIELD, RIGHT}), plats, pg.sprite.Group())
    assert p.state == "dodge"
    assert p.fighter.vel.x == DODGE_AIR_SPEED, f"expected +{DODGE_AIR_SPEED}, got {p.fighter.vel.x}"


def test_left_air_dodge_applies_negative_dodge_speed():
    p, plats = _airborne_player()
    p.update(_frame({SHIELD, LEFT}, {SHIELD, LEFT}), plats, pg.sprite.Group())
    assert p.state == "dodge"
    assert p.fighter.vel.x == -DODGE_AIR_SPEED, f"expected -{DODGE_AIR_SPEED}, got {p.fighter.vel.x}"


def test_neutral_air_dodge_adds_no_horizontal_velocity():
    """Shield-only air dodge from a standstill imparts no horizontal velocity."""
    p, plats = _airborne_player()
    assert p.fighter.vel.x == 0
    p.update(_frame({SHIELD}, {SHIELD}), plats, pg.sprite.Group())
    assert p.state == "dodge"
    assert p.fighter.vel.x == 0, f"neutral air dodge imparted vel.x={p.fighter.vel.x}"


def test_neutral_air_dodge_halts_existing_horizontal_momentum():
    """PM/Melee air dodge (#184) HALTS momentum: a neutral air dodge replaces
    horizontal velocity with ~zero, not Brawl-style preserve. (Was
    test_neutral_air_dodge_preserves_existing_horizontal_momentum.)"""
    p, plats = _airborne_player()
    p.fighter.vel.x = 8.0
    p.update(_frame({SHIELD}, {SHIELD}), plats, pg.sprite.Group())
    assert p.fighter.vel.x == 0, f"neutral air dodge should halt momentum: vel.x={p.fighter.vel.x}"


def test_air_dodge_halts_vertical_velocity():
    """PM/Melee air dodge (#184) REPLACES vertical momentum (halt), not Brawl-style
    preserve: vel.y drops well below the pre-dodge falling speed. (Was
    test_air_dodge_preserves_vertical_velocity.) Gravity still acts over the dodge
    frames, so vel.y need not be exactly 0 — just halted relative to before."""
    p, plats = _airborne_player()
    vy_before = p.fighter.vel.y
    assert vy_before > 0
    p.update(_frame({SHIELD, RIGHT}, {SHIELD, RIGHT}), plats, pg.sprite.Group())
    assert p.fighter.vel.y < vy_before, (
        f"air dodge should halt vel.y below {vy_before}, got {p.fighter.vel.y}"
    )


def test_air_dodge_is_not_a_ground_spot_dodge():
    """An air dodge must not raise the ground-spot-dodge flag."""
    p, plats = _airborne_player()
    p.update(_frame({SHIELD, RIGHT}, {SHIELD, RIGHT}), plats, pg.sprite.Group())
    assert p.state == "dodge"
    assert p.fighter.spot_dodge_shield_held is False


def test_air_dodge_consumes_air_dodge_ok():
    """An air dodge spends the one available air dodge (air_dodge_ok True -> False)."""
    p, plats = _airborne_player()
    assert p.fighter.air_dodge_ok is True
    p.update(_frame({SHIELD, RIGHT}, {SHIELD, RIGHT}), plats, pg.sprite.Group())
    assert p.fighter.air_dodge_ok is False


# ------------------------------------------------------------- ground roll

def test_ground_side_dodge_rolls_at_full_dodge_speed():
    """A grounded side dodge (shield+direction) rolls at the full DODGE_SPEED for
    the whole window — not half speed/distance (`test_dodge_issues` / `test_left_right_dodge`)."""
    p, plats = _grounded_player((100, 400, 700, 40), thin=False)
    assert p.fighter.on_ground
    start_x = p.rect.centerx
    p.update(_frame({SHIELD, RIGHT}, {SHIELD, RIGHT}), plats, pg.sprite.Group())
    assert p.state == "dodge"
    speeds = [p.fighter.vel.x]
    for _ in range(DODGE_TIME - 1):
        p.update(_frame({SHIELD, RIGHT}, set()), plats, pg.sprite.Group())
        speeds.append(p.fighter.vel.x)
    moving = [s for s in speeds if s != 0]
    assert moving and all(s == DODGE_SPEED for s in moving), f"roll not at full speed: {speeds}"
    assert p.rect.centerx - start_x == DODGE_SPEED * DODGE_TIME, "roll distance is not full"


def test_ground_side_dodge_left_mirrors_right_at_full_speed():
    """Left ground roll is the mirror of right — full -DODGE_SPEED, full distance.
    Ports the left-vs-right symmetry intent of `test_left_right_dodge`."""
    p, plats = _grounded_player((100, 400, 700, 40), thin=False)
    assert p.fighter.on_ground
    start_x = p.rect.centerx
    p.update(_frame({SHIELD, LEFT}, {SHIELD, LEFT}), plats, pg.sprite.Group())
    assert p.state == "dodge"
    speeds = [p.fighter.vel.x]
    for _ in range(DODGE_TIME - 1):
        p.update(_frame({SHIELD, LEFT}, set()), plats, pg.sprite.Group())
        speeds.append(p.fighter.vel.x)
    moving = [s for s in speeds if s != 0]
    assert moving and all(s == -DODGE_SPEED for s in moving), f"left roll not full speed: {speeds}"
    assert start_x - p.rect.centerx == DODGE_SPEED * DODGE_TIME, "left roll distance is not full"


# ------------------------------------------- shield-then-direction (documented)

def test_shield_then_direction_air_dodge_is_neutral():
    """CURRENT behavior: the air dodge commits on the shield-press frame (consuming
    air_dodge_ok), so a direction pressed on a LATER frame does not redirect it —
    the result is a neutral air dodge (vel.x stays 0). This matches Melee/PM
    air-dodge commitment.

    (The relocated `test_shield_then_direction_debug` script expected the later
    direction to apply velocity; whether shield-then-direction *should* redirect is
    a separate design question, not current behavior.)"""
    p, plats = _airborne_player()
    p.update(_frame({SHIELD}, {SHIELD}), plats, pg.sprite.Group())       # shield first
    p.update(_frame({SHIELD, RIGHT}, {RIGHT}), plats, pg.sprite.Group())  # then direction
    assert p.state == "dodge"
    assert p.fighter.vel.x == 0, f"shield-then-direction redirected to vel.x={p.fighter.vel.x} (was neutral)"

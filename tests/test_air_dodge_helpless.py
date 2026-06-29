"""PM-faithful air dodge → helpless/special-fall (#184).

The Melee-style air dodge: it SETS (replaces) velocity — neutral → ~zero (halt),
directional → a fixed burst in the stick direction with vertical halted — and on
exit drops the fighter into a `helpless` state, locked out of normal actions until
it lands. (Wavedash — air dodge into the ground → traction slide — is deferred to
#184b.) Velocity-magnitude assertions also live in tests/test_dodge_mechanics.py;
this file pins the helpless state machine + the SET (not add) semantics.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE, DODGE_TIME, DODGE_AIR_SPEED

CONTROLS = {
    "left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
    "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e,
}
SHIELD, RIGHT, LEFT, UP, ATTACK = pg.K_q, pg.K_d, pg.K_a, pg.K_w, pg.K_e


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _high_airborne(floor_y=2000):
    """A clearly-airborne player with lots of air room below (so the full dodge +
    helpless window plays out before landing)."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, floor_y, 960, 40), thin=False))
    p = Player(x=300, y=100, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="AirCat", facing_right=True)
    for _ in range(3):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert not p.fighter.on_ground, "fixture precondition: airborne"
    return p, plats


def _air_dodge(p, plats, keys=(SHIELD,)):
    p.update(_frame(set(keys), set(keys)), plats, pg.sprite.Group())


def test_directional_air_dodge_sets_burst_not_adds():
    """A right air dodge SETS vel.x to +DODGE_AIR_SPEED even from leftward momentum
    (replace, not Brawl-style add)."""
    p, plats = _high_airborne()
    p.fighter.vel.x = -5.0
    _air_dodge(p, plats, (SHIELD, RIGHT))
    assert p.state == "dodge"
    assert p.fighter.vel.x == DODGE_AIR_SPEED, (
        f"directional air dodge should SET vel.x to {DODGE_AIR_SPEED}, got {p.fighter.vel.x}"
    )


def test_air_dodge_enters_helpless_after_timer():
    p, plats = _high_airborne()
    _air_dodge(p, plats)
    for _ in range(DODGE_TIME + 2):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "helpless", f"expected helpless after the dodge window, got {p.state!r}"


def test_helpless_blocks_jump_and_does_not_consume_a_jump():
    p, plats = _high_airborne()
    _air_dodge(p, plats)
    for _ in range(DODGE_TIME + 2):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "helpless"
    jumps_before = p.fighter.jumps_remaining
    p.update(_frame({UP}, {UP}), plats, pg.sprite.Group())
    assert p.state == "helpless", "jump must be locked out during helpless"
    assert p.fighter.jumps_remaining == jumps_before, "helpless must not consume a jump"


def test_helpless_blocks_attack():
    p, plats = _high_airborne()
    _air_dodge(p, plats)
    for _ in range(DODGE_TIME + 2):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "helpless"
    p.update(_frame({ATTACK}, {ATTACK}), plats, pg.sprite.Group())
    assert p.state == "helpless", "attack must be locked out during helpless"


def test_helpless_recovers_to_idle_on_landing():
    p, plats = _high_airborne(floor_y=400)  # land within a reasonable window
    _air_dodge(p, plats)
    landed_state = None
    for _ in range(180):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
        if p.fighter.on_ground:
            landed_state = p.state
            break
    assert p.fighter.on_ground, "fixture: should land within the window"
    assert landed_state == "idle", f"helpless should recover to idle on landing, got {landed_state!r}"
    assert p.fighter.air_dodge_active is False, "landing must clear air_dodge_active"

"""Angleable f-smash — up/down-aimed forward smash (#327 slice 4).

Input scheme: the HORIZONTAL component decides the f-smash; a forward smash held
with up/down aims it (angle modifier), while pure up/down stays u/d-smash. The
aimed angle is captured at the smash press (fighter.smash_angle_dir) and REPLACES
the fsmash hitboxes' launch angle at Attack spawn.

Golden-safe: only a real fsmash press sets smash_angle_dir; the default cat has no
smash, so the spawn path is unchanged on the sim/golden cat.
"""
import pygame as pg

from pycats.combat.charge import angle_smash_hitboxes
from pycats.combat.data import Circle, Hitbox, load_fighter_data
from pycats.config import FSMASH_ANGLE_UP
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s,
          attack=pg.K_v, special=pg.K_c, shield=pg.K_x, smash=pg.K_b)


def _frame(held=(), pressed=(), released=()):
    return InputFrame(held={P1[k] for k in held},
                      pressed={P1[k] for k in pressed},
                      released={P1[k] for k in released})


# ---- pure helper ------------------------------------------------------------

def test_angle_helper_replaces_only_the_angle():
    boxes = (
        Hitbox(circle=Circle(78, 30, 12), damage=18.0, angle=361,
               base_knockback=35.0, knockback_growth=95.0),
        Hitbox(circle=Circle(52, 30, 14), damage=14.0, angle=361,
               base_knockback=25.0, knockback_growth=72.0),
    )
    out = angle_smash_hitboxes(boxes, FSMASH_ANGLE_UP)
    assert all(h.angle == FSMASH_ANGLE_UP for h in out)
    # everything else untouched
    assert [h.damage for h in out] == [18.0, 14.0]
    assert out[0].circle == boxes[0].circle
    assert out[0].base_knockback == 35.0


# ---- input resolution (press seam) ------------------------------------------

def _mk():
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    p.fighter.on_ground = True
    return p


def test_forward_plus_up_is_an_up_angled_fsmash():
    p = _mk()
    p.handle_actions(_frame(held=("smash", "right", "up"), pressed=("smash",)),
                     pg.sprite.Group())
    assert p.fighter.pending_smash_key == "fsmash"
    assert p.fighter.smash_angle_dir == "up"


def test_forward_plus_down_is_a_down_angled_fsmash():
    p = _mk()
    p.handle_actions(_frame(held=("smash", "right", "down"), pressed=("smash",)),
                     pg.sprite.Group())
    assert p.fighter.pending_smash_key == "fsmash"
    assert p.fighter.smash_angle_dir == "down"


def test_forward_only_is_a_straight_fsmash():
    p = _mk()
    p.handle_actions(_frame(held=("smash", "right"), pressed=("smash", "right")),
                     pg.sprite.Group())
    assert p.fighter.pending_smash_key == "fsmash"
    assert p.fighter.smash_angle_dir is None


def test_pure_vertical_smash_is_updown_smash_no_angle():
    up = _mk()  # up HELD (not freshly pressed, else it would jump) + smash pressed
    up.handle_actions(_frame(held=("smash", "up"), pressed=("smash",)),
                      pg.sprite.Group())
    assert up.fighter.pending_smash_key == "usmash"
    assert up.fighter.smash_angle_dir is None

    dn = _mk()
    dn.handle_actions(_frame(held=("smash", "down"), pressed=("smash",)),
                      pg.sprite.Group())
    assert dn.fighter.pending_smash_key == "dsmash"
    assert dn.fighter.smash_angle_dir is None


# ---- integration: an angled fsmash spawns with the aimed angle --------------

def _ground():
    return [Platform(pg.Rect(0, 100, 600, 40), thin=False)]


def _grounded():
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    plats = _ground()
    grp = pg.sprite.Group()
    for _ in range(3):
        p.update(_frame(), plats, grp)
    return p, plats


def _fire_and_capture(p, plats, enter_frame):
    grp = pg.sprite.Group()
    p.update(enter_frame, plats, grp)             # enter charge (captures the angle)
    p.update(_frame(released=("smash",)), plats, grp)  # release -> fire
    for _ in range(14):
        p.update(_frame(), plats, grp)
        if len(grp):
            return next(iter(grp))
    return None


def test_up_angled_fsmash_spawns_with_the_up_angle():
    p, plats = _grounded()
    atk = _fire_and_capture(
        p, plats, _frame(held=("smash", "right", "up"), pressed=("smash",)))
    assert atk is not None
    assert all(h.angle == FSMASH_ANGLE_UP for h in atk.hitboxes)


def test_straight_fsmash_keeps_its_authored_angle():
    p, plats = _grounded()
    atk = _fire_and_capture(
        p, plats, _frame(held=("smash", "right"), pressed=("smash", "right")))
    assert atk is not None
    authored = load_fighter_data("nalio").moves["fsmash"].hitboxes[0].angle  # 361
    assert atk.hitboxes[0].angle == authored
    assert p.fighter.smash_angle_dir is None      # consumed / never set

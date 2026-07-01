"""Smash-charge output scaling (#327 slice 3b).

A charged smash's damage/BKB/KBG scale by `1 + c*(SMASH_CHARGE_SCALE - 1)` at
Attack spawn, using the charge fraction captured by 3a. c=0 is an exact identity
(uncharged == authored), so non-chargeable moves and the default cat are
untouched (golden-safe).
"""
import pygame as pg

from pycats.combat.charge import charge_factor, scale_hitboxes
from pycats.combat.data import Circle, Hitbox, load_fighter_data
from pycats.config import SMASH_CHARGE_SCALE, SMASH_CHARGE_FRAMES
from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s,
          attack=pg.K_v, special=pg.K_c, shield=pg.K_x, smash=pg.K_b)


def _boxes():
    return (
        Hitbox(circle=Circle(10, 20, 8), damage=14.0, angle=361,
               base_knockback=25.0, knockback_growth=96.0),
        Hitbox(circle=Circle(5, 20, 6), damage=10.0, angle=361,
               base_knockback=20.0, knockback_growth=90.0, active_start=3, active_end=4),
    )


# ---- pure helper ------------------------------------------------------------

def test_factor_endpoints_and_midpoint():
    assert charge_factor(0.0) == 1.0
    assert charge_factor(1.0) == SMASH_CHARGE_SCALE
    assert charge_factor(0.5) == 1.0 + 0.5 * (SMASH_CHARGE_SCALE - 1.0)
    assert charge_factor(-1.0) == 1.0            # clamped
    assert charge_factor(2.0) == SMASH_CHARGE_SCALE  # clamped


def test_scale_identity_at_zero():
    boxes = _boxes()
    out = scale_hitboxes(boxes, 0.0)
    assert [h.damage for h in out] == [14.0, 10.0]
    assert [h.base_knockback for h in out] == [25.0, 20.0]
    assert [h.knockback_growth for h in out] == [96.0, 90.0]


def test_scale_full_multiplies_offensive_magnitudes_only():
    boxes = _boxes()
    out = scale_hitboxes(boxes, 1.0)
    assert out[0].damage == 14.0 * SMASH_CHARGE_SCALE
    assert out[0].base_knockback == 25.0 * SMASH_CHARGE_SCALE
    assert out[0].knockback_growth == 96.0 * SMASH_CHARGE_SCALE
    # non-offensive fields untouched
    assert out[0].angle == 361
    assert out[0].circle == boxes[0].circle
    assert (out[1].active_start, out[1].active_end) == (3, 4)


def test_scale_interpolates_at_half():
    f = 1.0 + 0.5 * (SMASH_CHARGE_SCALE - 1.0)
    out = scale_hitboxes(_boxes(), 0.5)
    assert out[0].damage == 14.0 * f


# ---- integration: a full-charge fsmash spawns a scaled Attack ---------------

def _ground():
    return [Platform(pg.Rect(0, 100, 600, 40), thin=False)]


def _frame(held=(), pressed=(), released=()):
    return InputFrame(held={P1[k] for k in held},
                      pressed={P1[k] for k in pressed},
                      released={P1[k] for k in released})


def _grounded_nalio():
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    plats = _ground()
    grp = pg.sprite.Group()
    for _ in range(3):
        p.update(_frame(), plats, grp)
    return p, plats


def _charge_full_and_capture_attack(p, plats):
    grp = pg.sprite.Group()
    p.update(_frame(held=("smash", "right"), pressed=("smash", "right")), plats, grp)
    for _ in range(SMASH_CHARGE_FRAMES + 15):   # hold to max (auto-fire), let the window open
        p.update(_frame(held=("smash",)), plats, grp)
        if len(grp):
            return next(iter(grp))
    return None


def test_full_charge_fsmash_scales_the_spawned_hitbox():
    p, plats = _grounded_nalio()
    atk = _charge_full_and_capture_attack(p, plats)
    assert atk is not None, "no Attack spawned from the charged fsmash"
    authored = load_fighter_data("nalio").moves["fsmash"].hitboxes[0].damage  # 14.0
    assert atk.hitboxes[0].damage == authored * SMASH_CHARGE_SCALE
    assert atk.damage == authored * SMASH_CHARGE_SCALE   # primary-box mirror


def test_zero_fraction_spawn_is_authored():
    # A chargeable move whose fraction is 0 at spawn spawns its authored damage
    # (the identity path in the spawn seam), not a scaled value.
    p, plats = _grounded_nalio()
    grp = pg.sprite.Group()
    p.update(_frame(held=("smash", "right"), pressed=("smash", "right")), plats, grp)
    p.update(_frame(released=("smash",)), plats, grp)   # fires (recomputes fraction)
    p.fighter.smash_charge_fraction = 0.0               # pin c=0 for the spawn
    for _ in range(12):
        p.update(_frame(), plats, grp)
        if len(grp):
            break
    atk = next(iter(grp))
    authored = load_fighter_data("nalio").moves["fsmash"].hitboxes[0].damage
    assert atk.hitboxes[0].damage == authored

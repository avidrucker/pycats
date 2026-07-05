"""Smash-charge output scaling (#327 slice 3b; #437 damage-only fix).

A charged smash's **damage** scales by `1 + c*(SMASH_CHARGE_SCALE - 1)` at Attack
spawn, using the charge fraction captured by 3a. Knockback rises through the KB
formula (damage is an input) — base_knockback / knockback_growth are NOT scaled
(that would compound; #423/#426). c=0 is an exact identity (uncharged == authored),
so non-chargeable moves and the default cat are untouched (golden-safe).
"""
import pygame as pg

from pycats.combat.charge import charge_factor, scale_hitboxes
from pycats.combat.data import Circle, Hitbox, load_fighter_data
from pycats.combat.knockback import knockback
from pycats.config import SMASH_CHARGE_FRAMES, SMASH_CHARGE_SCALE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

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


def test_scale_full_multiplies_damage_only():
    # #437: charge scales DAMAGE only; base_knockback / knockback_growth stay at
    # the authored values (KB rises through the formula, not by scaling KB terms —
    # scaling all three compounds to a spurious extra x1.4, #423/#426).
    boxes = _boxes()
    out = scale_hitboxes(boxes, 1.0)
    assert out[0].damage == 14.0 * SMASH_CHARGE_SCALE
    assert out[1].damage == 10.0 * SMASH_CHARGE_SCALE
    # KB terms UNCHANGED from the authored move
    assert out[0].base_knockback == 25.0
    assert out[0].knockback_growth == 96.0
    assert out[1].base_knockback == 20.0
    assert out[1].knockback_growth == 90.0
    # non-offensive fields untouched
    assert out[0].angle == 361
    assert out[0].circle == boxes[0].circle
    assert (out[1].active_start, out[1].active_end) == (3, 4)


def test_full_charge_knockback_is_damage_only_not_compounded():
    # The behavioral crux (#423/#426): at full charge, the resulting knockback must
    # equal the formula's response to 1.4x DAMAGE with the authored BKB/KBG — NOT
    # 1.4x that value. Under the old all-three scaling, KB_buggy == 1.4 * KB_correct
    # exactly (derivation: #426 findings §4), so this asserts the fix removed that.
    authored = _boxes()[0]                      # damage 14, BKB 25, KBG 96
    hb = scale_hitboxes((authored,), 1.0)[0]    # full charge
    charged_damage = 14.0 * SMASH_CHARGE_SCALE
    percent, weight = 50.0, 100

    got = knockback(percent, hb.damage, weight, hb.base_knockback, hb.knockback_growth)
    kb_damage_only = knockback(percent, charged_damage, weight, 25.0, 96.0)
    kb_compounded = knockback(percent, charged_damage, weight,
                              25.0 * SMASH_CHARGE_SCALE, 96.0 * SMASH_CHARGE_SCALE)

    assert got == kb_damage_only                # fixed: KB from damage-only scaling
    assert got != kb_compounded                 # not the old compounded value
    # sanity: the old path was exactly SMASH_CHARGE_SCALE too strong
    assert abs(kb_compounded - SMASH_CHARGE_SCALE * kb_damage_only) < 1e-9


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

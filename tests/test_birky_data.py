"""Birky (Kirby archetype) stats + movement data — slice 1 of #228 (#237).

Birky is the first fighter to override the per-fighter movement scalars
(weight / gravity / max_fall_speed / move_speed / max_jumps / jump_vel). Its moves
and body geometry are placeholders reused from the default cat until slice 2; this
slice pins only the stat differentiation. All assertions go through
load_fighter_data("birky") — the loader is the seam (#229).
"""
from pycats.combat.data import load_fighter_data

# #229 PM-Kirby -> pycats stat table (proportional-to-Mario; pin/playtest later).
_EXPECTED = dict(weight=70, gravity=0.42, max_fall_speed=12, move_speed=5,
                 max_jumps=6, jump_vel=-11)


def test_birky_overrides_movement_scalars():
    fd = load_fighter_data("birky")
    assert fd.weight == _EXPECTED["weight"]
    assert fd.gravity == _EXPECTED["gravity"]
    assert fd.max_fall_speed == _EXPECTED["max_fall_speed"]
    assert fd.move_speed == _EXPECTED["move_speed"]
    assert fd.max_jumps == _EXPECTED["max_jumps"]
    assert fd.jump_vel == _EXPECTED["jump_vel"]


def test_birky_diverges_from_default_on_every_scalar():
    birky = load_fighter_data("birky")
    default = load_fighter_data("default")  # any non-archetype key -> default cat
    assert birky.weight != default.weight
    assert birky.gravity != default.gravity
    assert birky.max_fall_speed != default.max_fall_speed
    assert birky.move_speed != default.move_speed
    assert birky.max_jumps != default.max_jumps
    assert birky.jump_vel != default.jump_vel


def test_birky_reuses_default_hurtbox_and_attack_placeholder():
    birky = load_fighter_data("birky")
    default = load_fighter_data("default")
    assert birky.hurtbox == default.hurtbox            # body geometry not per-fighter
    # "attack" is still the slice-1 placeholder; "jab" is now Birky's own (slice 2, #240)
    assert birky.moves["attack"] == default.moves["attack"]


def test_birky_jab_is_authored_short_range_and_weak():
    """Birky's jab = PM3.6 Kirby jab1 (Attack11): 16f total, active ~f3, dmg 3,
    angle 361 (Sakurai), BKB 8, KBG 50; short reach (featherweight)."""
    birky = load_fighter_data("birky")
    default = load_fighter_data("default")
    jab = birky.moves["jab"]
    assert jab.in_air is False
    assert jab.startup > 0 and jab.active > 0 and jab.recovery > 0
    assert jab.startup + jab.active + jab.recovery == 16  # PM3.6 total / IASA 16
    assert jab.hitboxes, "jab must have at least one hitbox"
    hb = jab.hitboxes[0]
    assert hb.damage == 3.0
    assert hb.angle == 361                 # Sakurai-angle sentinel
    assert hb.base_knockback == 8.0 and hb.knockback_growth == 50.0
    # short reach: jab sits closer to the body than the default attack (dx=46)
    assert hb.circle.dx < default.moves["attack"].hitboxes[0].circle.dx

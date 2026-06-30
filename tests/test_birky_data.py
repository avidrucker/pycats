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


def test_birky_reuses_default_hurtbox_but_has_no_placeholder_moves():
    birky = load_fighter_data("birky")
    default = load_fighter_data("default")
    assert birky.hurtbox == default.hurtbox            # body geometry not per-fighter
    # Both moves are now Birky's own (attack = d-tilt #245, jab #240) — no placeholder.
    assert birky.moves["attack"] != default.moves["attack"]
    assert set(birky.moves) == {"attack", "jab", "ftilt", "utilt"}


def test_birky_attack_slot_is_kirby_down_tilt():
    """Birky's "attack" slot = PM3.6 Kirby d-tilt (AttackLw3): IASA 21, active 4-7,
    dmg 10, angle 20, BKB 40, KBG 30; a low, short-reach poke."""
    birky = load_fighter_data("birky")
    dtilt = birky.moves["attack"]
    assert dtilt.in_air is False
    assert dtilt.startup + dtilt.active + dtilt.recovery == 21  # PM3.6 IASA
    assert dtilt.hitboxes
    hb = dtilt.hitboxes[0]
    assert hb.damage == 10.0
    assert hb.angle == 20
    assert hb.base_knockback == 40.0 and hb.knockback_growth == 30.0
    assert hb.circle.dy > 30   # low (below body centre) — it's a down-tilt


def test_birky_ftilt_is_authored():
    """Birky's f-tilt = PM3.6 Kirby AttackS3S: IASA 28, active 5-8, dmg 11,
    angle 361 (Sakurai), BKB 8, KBG 100; a forward poke."""
    birky = load_fighter_data("birky")
    ftilt = birky.moves["ftilt"]
    assert ftilt.in_air is False
    assert ftilt.startup + ftilt.active + ftilt.recovery == 28  # PM3.6 IASA
    assert ftilt.hitboxes
    hb = ftilt.hitboxes[0]
    assert hb.damage == 11.0
    assert hb.angle == 361
    assert hb.base_knockback == 8.0 and hb.knockback_growth == 100.0


def test_birky_utilt_is_two_window():
    """Birky's u-tilt = PM3.6 Kirby AttackHi3: IASA 24, two windows — early f4-5
    (dmg 8, angle 92) and late f6-10 (dmg 6, angle 88), both BKB 40."""
    birky = load_fighter_data("birky")
    utilt = birky.moves["utilt"]
    assert utilt.in_air is False
    assert utilt.startup + utilt.active + utilt.recovery == 24  # PM3.6 IASA
    early = [h for h in utilt.hitboxes if h.active_end == 5]
    late = [h for h in utilt.hitboxes if h.active_start == 6]
    assert early and late, "u-tilt must have an early (f4-5) and a late (f6-10) window"
    assert all(h.damage == 8.0 and h.angle == 92 for h in early)
    assert all(h.damage == 6.0 and h.angle == 88 for h in late)
    assert all(h.base_knockback == 40.0 for h in utilt.hitboxes)


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

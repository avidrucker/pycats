"""Birky (Kirby archetype) stats + movement data — slice 1 of #228 (#237).

Birky is the first fighter to override the per-fighter movement scalars
(weight / gravity / max_fall_speed / move_speed / max_jumps / jump_vel). Its moves
and body geometry are placeholders reused from the default cat until slice 2; this
slice pins only the stat differentiation. All assertions go through
load_fighter_data("birky") — the loader is the seam (#229).
"""
import pygame

from pycats.battle_screen import BattleScreen
from pycats.combat.data import load_fighter_data
from pycats.config import PLAYER_SIZE

# #229 PM-Kirby -> pycats stat table (proportional-to-Mario; pin/playtest later).
_EXPECTED = dict(weight=70, gravity=0.42, max_fall_speed=12, move_speed=5,
                 max_jumps=6, jump_vel=-11)

# Birky's Kirby-proportioned body (#275): shorter than the default 40x60 (playtest).
_BIRKY_BODY = (40, 44)

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def test_birky_stand_size_is_a_smaller_kirby_body():
    birky = load_fighter_data("birky")
    default = load_fighter_data("default")
    assert birky.stand_size == _BIRKY_BODY
    assert default.stand_size is None          # default cat keeps the global PLAYER_SIZE
    assert _BIRKY_BODY[1] < PLAYER_SIZE[1]      # shorter than the 60-tall default


def test_birky_fighter_body_is_smaller_than_default():
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("birky", "nalio")  # nalio has no custom stand_size
    assert bs.player1.fighter.stand_size == _BIRKY_BODY
    assert bs.player1.fighter.rect.height == _BIRKY_BODY[1]
    # nalio falls back to the global body
    assert bs.player2.fighter.stand_size == PLAYER_SIZE
    assert bs.player2.fighter.rect.height == PLAYER_SIZE[1]


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


def test_birky_has_own_body_and_no_placeholder_moves():
    birky = load_fighter_data("birky")
    default = load_fighter_data("default")
    assert birky.hurtbox != default.hurtbox   # body-matched hurtbox now (#275)
    # Both moves are now Birky's own (attack = d-tilt #245, jab #240) — no placeholder.
    assert birky.moves["attack"] != default.moves["attack"]
    assert set(birky.moves) == {"attack", "jab", "ftilt", "utilt", "nair", "fair",
                                "bair", "uair", "dair"}


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


def test_birky_nair_is_two_window_sex_kick():
    """Birky's nair = PM3.6 Kirby AttackAirN: IASA 43, lingering — early f3-6
    (dmg 12, BKB 15) and late f7-29 (dmg 9, BKB 0), both angle 55."""
    birky = load_fighter_data("birky")
    nair = birky.moves["nair"]
    assert nair.in_air is True
    assert nair.startup + nair.active + nair.recovery == 43  # PM3.6 IASA
    early = [h for h in nair.hitboxes if h.active_end == 6]
    late = [h for h in nair.hitboxes if h.active_start == 7]
    assert early and late
    assert all(h.damage == 12.0 and h.base_knockback == 15.0 for h in early)
    assert all(h.damage == 9.0 and h.base_knockback == 0.0 for h in late)
    assert all(h.angle == 55 for h in nair.hitboxes)


def test_birky_fair_is_three_window_multihit():
    """Birky's fair = PM3.6 Kirby AttackAirF: IASA 40, drag hits (WDSK 30, dmg 5)
    in f7-8/f14-15 + a Sakurai finisher (angle 361, dmg 7, KBG 160) in f22-24."""
    birky = load_fighter_data("birky")
    fair = birky.moves["fair"]
    assert fair.in_air is True
    assert fair.startup + fair.active + fair.recovery == 40  # PM3.6 IASA
    drags = [h for h in fair.hitboxes if h.set_knockback == 30]
    finisher = [h for h in fair.hitboxes if h.angle == 361]
    assert drags and finisher
    assert all(h.damage == 5.0 for h in drags)
    assert all(h.damage == 7.0 and h.knockback_growth == 160.0 for h in finisher)
    assert all(h.active_start == 22 for h in finisher)


def test_birky_bair_is_two_window():
    """Birky's bair = PM3.6 Kirby AttackAirB: IASA 36, early f6-8 (dmg 14, BKB 10)
    + late f9-20 (dmg 10, BKB 0), both angle 361, behind the cat (dx < 0)."""
    birky = load_fighter_data("birky")
    bair = birky.moves["bair"]
    assert bair.in_air is True
    assert bair.startup + bair.active + bair.recovery == 36  # PM3.6 IASA
    early = [h for h in bair.hitboxes if h.active_end == 8]
    late = [h for h in bair.hitboxes if h.active_start == 9]
    assert early and late
    assert all(h.damage == 14.0 for h in early)
    assert all(h.damage == 10.0 for h in late)
    assert all(h.angle == 361 and h.circle.dx < 0 for h in bair.hitboxes)


def test_birky_uair_is_two_window_juggle():
    """Birky's uair = PM3.6 Kirby AttackAirHi: IASA 36, early f10-12 (dmg 15,
    angle 75) + late f13-15 (dmg 12, angle 30)."""
    birky = load_fighter_data("birky")
    uair = birky.moves["uair"]
    assert uair.in_air is True
    assert uair.startup + uair.active + uair.recovery == 36  # PM3.6 IASA
    early = [h for h in uair.hitboxes if h.active_end == 12]
    late = [h for h in uair.hitboxes if h.active_start == 13]
    assert early and late
    assert all(h.damage == 15.0 and h.angle == 75 for h in early)
    assert all(h.damage == 12.0 and h.angle == 30 for h in late)


def test_birky_dair_is_looping_spike_drill():
    """Birky's dair = PM3.6 Kirby AttackAirLw: IASA 50, a looping drill
    (rehit_rate 3), dmg 3, angle 270 (down spike), BKB 10."""
    birky = load_fighter_data("birky")
    dair = birky.moves["dair"]
    assert dair.in_air is True
    assert dair.startup + dair.active + dair.recovery == 50  # PM3.6 IASA
    assert dair.rehit_rate == 3
    assert dair.hitboxes
    assert all(h.damage == 3.0 and h.angle == 270 and h.base_knockback == 10.0
               for h in dair.hitboxes)


# --- Zone-anchored hitbox dy on the 40x44 body (#309) -------------------------
# Birky's move dy offsets were authored for the OLD 60-tall body, so on the 44 they
# sat too low — worst case the d-tilt centre hung below the feet, into the floor.
# After zone-anchoring, every hitbox centre resolves ON the body (dy <= height)
# except the d-air, the one deliberate (bounded) below-feet spike.

def test_no_birky_hitbox_center_below_feet_except_dair():
    """#309: every Birky hitbox centre lands on the body (dy <= stand_size height),
    except the bounded d-air spike. Able-to-fail: the pre-fix d-tilt dy was 48-50
    on a 44 body (below the feet)."""
    birky = load_fighter_data("birky")
    height = birky.stand_size[1]
    for key, move in birky.moves.items():
        if key == "dair":
            continue
        for hb in move.hitboxes:
            assert hb.circle.dy <= height, (
                f"{key} hitbox dy={hb.circle.dy} is below the feet (height={height})")


def test_birky_dair_is_a_bounded_below_feet_spike():
    """#309: d-air is the one move whose centres sit just below the feet (a spike),
    but bounded — not far below like the pre-fix 52-56 on a 44 body."""
    birky = load_fighter_data("birky")
    height = birky.stand_size[1]
    dair = birky.moves["dair"]
    assert all(hb.circle.dy > height for hb in dair.hitboxes)        # below the feet
    assert all(hb.circle.dy <= height + 10 for hb in dair.hitboxes)  # but just below


def test_birky_moves_land_in_intended_vertical_zones():
    """#309: overhead moves (u-tilt/u-air) sit near the head; the down-tilt sits low
    near the feet; the centre moves (jab/f-tilt/nair/fair/bair) sit mid-body. Able-to-
    fail: the pre-fix f-tilt (dy 34) and b-air (dy 33) exceeded the centre band on 44."""
    birky = load_fighter_data("birky")
    height = birky.stand_size[1]
    for key in ("utilt", "uair"):
        for hb in birky.moves[key].hitboxes:
            assert hb.circle.dy < height * 0.3, f"{key} not overhead"
    for hb in birky.moves["attack"].hitboxes:      # attack slot == d-tilt
        assert hb.circle.dy > height * 0.6, "d-tilt not low near the feet"
    for key in ("jab", "ftilt", "nair", "fair", "bair"):
        for hb in birky.moves[key].hitboxes:
            assert height * 0.3 <= hb.circle.dy <= height * 0.7, f"{key} not centred"

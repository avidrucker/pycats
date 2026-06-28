"""'Nalio' cat archetype data (#123, first impl slice of #117).

Nalio is the feline character that plays as the balanced all-rounder (Project M
Mario) archetype. Per the #119 spec (PM3.6 canonical, #120 unit convention):
combat numbers drop in raw; weight 100 == pycats default.

These tests pin Nalio as DISTINCT data reachable through the load_fighter_data
seam — without touching the default cat (so goldens stay green: the sim path
loads "P1"/"P2", never "nalio").
"""
import pygame

from pycats.combat.data import load_fighter_data, FighterData
from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
from pycats.entities import Player

P1_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                   down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                   shield=pygame.K_x)


def test_nalio_is_distinct_fighter_data():
    """load_fighter_data("nalio") returns its own FighterData, not the shared
    default object every other key still maps to."""
    fd = load_fighter_data("nalio")
    assert isinstance(fd, FighterData)
    assert fd is not DEFAULT_FIGHTER_DATA


def test_nalio_weight_is_pm_mario_100():
    """PM3.6 Mario weight = 100 (== pycats default → no knockback change)."""
    assert load_fighter_data("nalio").weight == 100


def test_fighter_data_weight_defaults_to_100():
    """The default cat keeps the Smash baseline weight without specifying it."""
    assert DEFAULT_FIGHTER_DATA.weight == 100


def test_nalio_attack_is_pm_down_tilt():
    """Nalio's 'attack' slot carries PM3.6 Mario's down-tilt (AttackLw3),
    entered raw per #120: dmg 9, BKB 30, KBG 80, angle 80, startup 5 / active 4 /
    recovery 21. Able-to-fail: any wrong value (or falling back to the default
    jab — dmg 10, angle 0, KBG 100) breaks this."""
    move = load_fighter_data("nalio").moves["attack"]
    assert (move.startup, move.active, move.recovery) == (5, 4, 21)
    hb = move.hitboxes[0]
    assert hb.damage == 9.0
    assert hb.angle == 80
    assert hb.base_knockback == 30.0
    assert hb.knockback_growth == 80.0


def test_nalio_jab_is_pm_attack11_single_hit_approx():
    """Nalio's neutral-A key carries PM3.6 Mario Attack11 (#154).

    rukaidata Attack11: total 16f / IASA 16, hitboxes active 2-3, three
    same-set hitboxes. pycats can express simultaneous hitboxes, but not WDSK's
    special knockback formula yet, so BKB/KBG are recorded raw as available.
    Radii are round(size u × 5.4): 3.52->19, 2.34->13, 2.73->15.
    """
    move = load_fighter_data("nalio").moves["jab"]
    assert move.name == "jab"
    assert move.in_air is False
    assert (move.startup, move.active, move.recovery) == (1, 2, 13)
    assert len(move.hitboxes) == 3
    assert tuple(hb.damage for hb in move.hitboxes) == (3.0, 3.0, 3.0)
    assert tuple(hb.angle for hb in move.hitboxes) == (83, 83, 85)
    assert tuple(hb.base_knockback for hb in move.hitboxes) == (0.0, 0.0, 0.0)
    assert tuple(hb.knockback_growth for hb in move.hitboxes) == (100.0, 100.0, 100.0)
    assert tuple(hb.circle.r for hb in move.hitboxes) == (19, 13, 15)


def test_nalio_dtilt_is_three_hitboxes():
    """Nalio's down-tilt is PM3.6 Mario's real 3-hitbox AttackLw3 (#132, on the
    #130 multi-hitbox engine) — not the single-hit approximation. All three are
    active 5-8 (simultaneous), angle 80 / BKB 30 / KBG 80; damages 9/9/8 and
    radii 13/17/21 (sizes 2.34/3.13/3.91 u × 5.4), in priority order (id 0->2).
    Able-to-fail: today's single box reds this."""
    move = load_fighter_data("nalio").moves["attack"]
    assert len(move.hitboxes) == 3, "down-tilt should declare its 3 real hitboxes"
    assert tuple(hb.damage for hb in move.hitboxes) == (9.0, 9.0, 8.0)
    assert tuple(hb.circle.r for hb in move.hitboxes) == (13, 17, 21)
    for hb in move.hitboxes:
        assert hb.angle == 80
        assert hb.base_knockback == 30.0
        assert hb.knockback_growth == 80.0


def test_nalio_nair_is_pm_neutral_air():
    """Nalio's neutral-air is PM3.6 Mario AttackAirN (#136), clean-hit form on the
    #130 multi-hitbox engine: 2 simultaneous hitboxes, in_air, damage 12, BKB 20,
    KBG 100, r15 (size 2.73 u × 5.4), startup 2 / active 4 / recovery 40. Angle is
    a literal placeholder for the Sakurai sentinel 361 (deferred). Able-to-fail:
    missing nair / wrong values red this."""
    move = load_fighter_data("nalio").moves["nair"]
    assert move.in_air is True
    assert (move.startup, move.active, move.recovery) == (2, 4, 40)
    assert len(move.hitboxes) == 2
    for hb in move.hitboxes:
        assert hb.damage == 12.0
        assert hb.base_knockback == 20.0
        assert hb.knockback_growth == 100.0
        assert hb.circle.r == 15


def test_default_cat_attack_is_unchanged():
    """Regression guard: branching Nalio must NOT alter the default cat's jab
    (the sim/golden path), which stays the placeholder (dmg 10, angle 0)."""
    hb = DEFAULT_FIGHTER_DATA.moves["attack"].hitboxes[0]
    assert hb.damage == 10.0
    assert hb.angle == 0


def test_player_named_nalio_loads_nalio_data():
    """End-to-end seam: a Player given char_name='nalio' loads Nalio's distinct
    moveset, not the default jab. Able-to-fail: without the loader branch the
    Player would get the default cat (angle 0)."""
    p = Player(100, 100, P1_CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio")
    assert p.fighter_data is load_fighter_data("nalio")
    assert p.fighter_data.moves["attack"].hitboxes[0].angle == 80

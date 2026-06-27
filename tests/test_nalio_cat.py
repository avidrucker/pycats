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

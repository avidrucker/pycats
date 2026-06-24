"""
Tests for pycats/combat/data.py schema, loader, and default character data.

All assertions run against load_fighter_data() so the loader is the single
swap-to-files seam even in tests.
"""

import pytest
from pycats.combat.data import (
    Circle,
    Hitbox,
    MoveData,
    Hurtbox,
    FighterData,
    load_fighter_data,
)


def test_hitbox_carries_knockback_fields():
    hb = Hitbox(circle=Circle(dx=1, dy=2, r=3), damage=10.0, angle=0,
                base_knockback=30.0, knockback_growth=100.0)
    assert hb.base_knockback == 30.0
    assert hb.knockback_growth == 100.0


# ---------------------------------------------------------------------------
# load_fighter_data returns FighterData for every CAT_CHARACTERS key
# ---------------------------------------------------------------------------

def test_load_fighter_data_calico_returns_fighter_data():
    fd = load_fighter_data("calico")
    assert isinstance(fd, FighterData)


def test_load_fighter_data_ghost_returns_fighter_data():
    fd = load_fighter_data("ghost")
    assert isinstance(fd, FighterData)


def test_load_fighter_data_unknown_char_returns_fighter_data():
    """Phase 0: any string maps to the same default."""
    fd = load_fighter_data("unknown_character_xyz")
    assert isinstance(fd, FighterData)


# ---------------------------------------------------------------------------
# Hurtbox has exactly 2 circles
# ---------------------------------------------------------------------------

def test_hurtbox_has_two_circles():
    fd = load_fighter_data("calico")
    assert len(fd.hurtbox.circles) == 2


def test_hurtbox_circles_are_Circle_instances():
    fd = load_fighter_data("calico")
    for c in fd.hurtbox.circles:
        assert isinstance(c, Circle)


# ---------------------------------------------------------------------------
# "attack" move exists and has correct shape
# ---------------------------------------------------------------------------

def test_attack_move_exists():
    fd = load_fighter_data("calico")
    assert "attack" in fd.moves


def test_attack_move_is_ground_move():
    fd = load_fighter_data("calico")
    attack = fd.moves["attack"]
    assert attack.in_air is False


def test_attack_move_startup_is_positive_int():
    fd = load_fighter_data("calico")
    attack = fd.moves["attack"]
    assert isinstance(attack.startup, int)
    assert attack.startup > 0


def test_attack_move_active_is_positive_int():
    fd = load_fighter_data("calico")
    attack = fd.moves["attack"]
    assert isinstance(attack.active, int)
    assert attack.active > 0


def test_attack_move_recovery_is_positive_int():
    fd = load_fighter_data("calico")
    attack = fd.moves["attack"]
    assert isinstance(attack.recovery, int)
    assert attack.recovery > 0


def test_attack_move_has_at_least_one_hitbox():
    fd = load_fighter_data("calico")
    attack = fd.moves["attack"]
    assert len(attack.hitboxes) >= 1


def test_attack_hitbox_is_Hitbox_instance():
    fd = load_fighter_data("calico")
    hb = fd.moves["attack"].hitboxes[0]
    assert isinstance(hb, Hitbox)


def test_attack_hitbox_circle_is_Circle_instance():
    fd = load_fighter_data("calico")
    hb = fd.moves["attack"].hitboxes[0]
    assert isinstance(hb.circle, Circle)


def test_attack_hitbox_damage_is_float():
    fd = load_fighter_data("calico")
    hb = fd.moves["attack"].hitboxes[0]
    assert isinstance(hb.damage, float)


def test_attack_hitbox_angle_is_int():
    fd = load_fighter_data("calico")
    hb = fd.moves["attack"].hitboxes[0]
    assert isinstance(hb.angle, int)


# ---------------------------------------------------------------------------
# Dataclasses are frozen (immutable)
# ---------------------------------------------------------------------------

def test_circle_is_frozen():
    c = Circle(dx=0, dy=0, r=10)
    with pytest.raises((AttributeError, TypeError)):
        c.dx = 99  # type: ignore[misc]


def test_hitbox_is_frozen():
    hb = Hitbox(circle=Circle(dx=27, dy=0, r=12), damage=10.0, angle=0)
    with pytest.raises((AttributeError, TypeError)):
        hb.damage = 99.0  # type: ignore[misc]


def test_move_data_is_frozen():
    md = MoveData(
        name="test",
        in_air=False,
        startup=3,
        active=3,
        recovery=6,
        hitboxes=(Hitbox(circle=Circle(dx=27, dy=0, r=12), damage=10.0, angle=0),),
    )
    with pytest.raises((AttributeError, TypeError)):
        md.startup = 99  # type: ignore[misc]


def test_hurtbox_is_frozen():
    hb = Hurtbox(circles=(Circle(dx=0, dy=-15, r=14), Circle(dx=0, dy=15, r=14)))
    with pytest.raises((AttributeError, TypeError)):
        hb.circles = ()  # type: ignore[misc]


def test_fighter_data_is_frozen():
    fd = load_fighter_data("calico")
    with pytest.raises((AttributeError, TypeError)):
        fd.hurtbox = None  # type: ignore[misc]

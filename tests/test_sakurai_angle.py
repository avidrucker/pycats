"""Real Sakurai-angle (361) launch resolution (#203, a #142 sub-system gate).

The angle id **361** is the *Sakurai angle* sentinel — a code, not a literal
degree. Before this gate, `Fighter.receive_hit` did `math.radians(atk.angle)`,
so 361 was taken as 361° (≡ 1°), a near-flat rightward launch; Nalio's n-air
used a literal `45` placeholder to dodge the bug.

Real behaviour (SmashWiki "Sakurai angle", Brawl/PM values):
  * airborne victim  -> a fixed angle (~40°), regardless of knockback;
  * grounded victim  -> scales LINEARLY from 0° (weak/low-KB) up to ~40°
    (strong/high-KB), so weak grounded hits stay flat and don't pop a grounded
    opponent straight up.

NOTE: the repo's own `docs/pm-reference/combat-knockback-hitstun.md` described
this *inverted* before this slice; the correct behaviour is encoded here.

The grounded threshold constants are playtest starting points (like the
crouch/prone numbers), so these tests pin the *mechanism* — monotonic, the two
extremes, airborne-fixed, and the end-to-end launch through receive_hit — not
brittle magic angles.
"""
import math
from types import SimpleNamespace

import pygame
import pytest

from pycats.combat.knockback import sakurai_angle
from pycats.config import (
    SAKURAI_AIRBORNE_DEG,
    SAKURAI_ANGLE_CODE,
    SAKURAI_GROUNDED_HIGH_KB,
    SAKURAI_GROUNDED_LOW_KB,
    SAKURAI_GROUNDED_MAX_DEG,
)
from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.platform import Platform

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


# ---------------------------------------------------------------- pure formula

def test_sentinel_is_361():
    assert SAKURAI_ANGLE_CODE == 361


def test_airborne_is_fixed_regardless_of_kb():
    """An airborne victim always launches at the fixed angle, weak or strong."""
    assert sakurai_angle(10.0, on_ground=False) == SAKURAI_AIRBORNE_DEG
    assert sakurai_angle(300.0, on_ground=False) == SAKURAI_AIRBORNE_DEG


def test_grounded_weak_is_flat():
    """A weak grounded hit (below the low threshold) launches flat (0°)."""
    assert sakurai_angle(SAKURAI_GROUNDED_LOW_KB - 1.0, on_ground=True) == 0.0


def test_grounded_strong_is_capped_at_max():
    """A strong grounded hit (above the high threshold) caps at the max angle."""
    assert (sakurai_angle(SAKURAI_GROUNDED_HIGH_KB + 1.0, on_ground=True)
            == SAKURAI_GROUNDED_MAX_DEG)


def test_grounded_scales_monotonically_between_thresholds():
    """Between the thresholds the angle rises with knockback (low-KB→flat)."""
    lo, hi = SAKURAI_GROUNDED_LOW_KB, SAKURAI_GROUNDED_HIGH_KB
    mid = (lo + hi) / 2.0
    a_lo = sakurai_angle(lo + 0.1, on_ground=True)
    a_mid = sakurai_angle(mid, on_ground=True)
    a_hi = sakurai_angle(hi - 0.1, on_ground=True)
    assert 0.0 <= a_lo < a_mid < a_hi <= SAKURAI_GROUNDED_MAX_DEG


def test_grounded_max_is_pm_starting_value():
    """The cap is the Brawl/PM Sakurai-angle range top (tuning start ~40°)."""
    assert 38.0 <= SAKURAI_GROUNDED_MAX_DEG <= 45.0
    assert 38.0 <= SAKURAI_AIRBORNE_DEG <= 45.0


# ----------------------------------------------------------- end-to-end launch

def _mk():
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P", facing_right=True)


def _ground():
    return [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]


def _settle(p, plats, n=3):
    grp = pygame.sprite.Group()
    for _ in range(n):
        p.update(InputFrame(held=set(), pressed=set(), released=set()), plats, grp)


def _atk(attacker, damage=10.0, bkb=30.0, kbg=100.0, angle=0):
    return SimpleNamespace(owner=attacker, damage=damage, base_knockback=bkb,
                           knockback_growth=kbg, angle=angle)


def _launch_angle_deg(vx, vy):
    """Recover the launch angle (deg, up-positive) from a velocity, dir +x."""
    return math.degrees(math.atan2(-vy, vx))


def test_airborne_361_launches_up_not_flat():
    """A 361 hit on an airborne defender resolves to ~40° — NOT the literal-361°
    (≡1°) near-flat launch the unfixed code produced."""
    attacker = _mk()
    defender = _mk()
    defender.fighter.on_ground = False
    defender.fighter.vel.x = 0.0
    defender.fighter.vel.y = 0.0
    defender.fighter.percent = 80.0  # ensure a non-trivial launch magnitude
    defender.fighter.receive_hit(_atk(attacker, angle=SAKURAI_ANGLE_CODE))
    deg = _launch_angle_deg(defender.fighter.vel.x, defender.fighter.vel.y)
    assert deg == pytest.approx(SAKURAI_AIRBORNE_DEG, abs=1.0)


def test_grounded_weak_361_stays_flat():
    """A weak 361 hit on a grounded defender launches flat (no upward pop)."""
    plats = _ground()
    attacker = _mk()
    _settle(attacker, plats)
    defender = _mk()
    _settle(defender, plats)
    assert defender.fighter.on_ground
    defender.fighter.vel.x = 0.0
    defender.fighter.vel.y = 0.0
    defender.fighter.receive_hit(_atk(attacker, angle=SAKURAI_ANGLE_CODE))
    assert defender.fighter.vel.y == pytest.approx(0.0, abs=1e-6)
    assert defender.fighter.vel.x > 0.0  # still launched horizontally


def test_non_sentinel_angle_is_unchanged():
    """A normal angle (90 = straight up) is untouched by the sentinel branch."""
    attacker = _mk()
    defender = _mk()
    defender.fighter.on_ground = False
    defender.fighter.vel.x = 0.0
    defender.fighter.vel.y = 0.0
    defender.fighter.percent = 80.0
    defender.fighter.receive_hit(_atk(attacker, angle=90))
    assert defender.fighter.vel.y < 0.0  # up
    assert defender.fighter.vel.x == pytest.approx(0.0, abs=1e-6)

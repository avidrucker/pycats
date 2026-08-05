"""tests/test_hitlag_c002.py

Fresh from-scratch red-green pins for **PYC-C-002-GRAPE**:

    In pycats a connecting hit freezes BOTH fighters for
    min(30, floor(damage * 0.3846154 + 5)) hitlag frames, holding
    position/velocity/hitstun during the freeze
    (`combat/knockback.py:hitlag_frames`).

This is a compound claim with four conjuncts; there is one able-to-fail test group
per conjunct, each proven non-vacuous by a named source mutation (revert-check):

1. Formula  — `hitlag_frames(d) == floor(d*0.3846154 + 5)` below the cap.
   Able-to-fail: drop the `+ HITLAG_BASE` term in `knockback.hitlag_frames`
   (config `HITLAG_BASE = 5 -> 0`) reds `test_c002_formula_reference_values`.
2. Cap      — a large damage floors to exactly 30.
   Able-to-fail: remove the `min(HITLAG_CAP, ...)` wrapper in `hitlag_frames`
   reds `test_c002_capped_at_30` + `test_c002_cap_clamps_a_would-be-larger_value`.
3. Both freeze — attacker AND defender get `hitlag_timer == hl`.
   Able-to-fail: zero the attacker assignment in `Fighter.receive_hit`
   (`atk.owner.fighter.hitlag_timer = hl -> = 0`) reds
   `test_c002_hit_freezes_both_attacker_and_defender`.
4. Held during freeze — position + hitstun countdown do not advance while
   `hitlag_timer > 0`, then resume.
   Able-to-fail: skip the freeze early-return in `Player._tick_life_and_hitlag`
   (drop `return True` under `if self.fighter.hitlag_timer > 0`) reds
   `test_c002_position_held_during_freeze_then_resumes` +
   `test_c002_hitstun_countdown_held_during_freeze`.

Each test docstring / this module carries the Claim ID `PYC-C-002-GRAPE`.
"""

import math

import pygame
import pytest
from helpers import P1

from pycats.combat.data import Circle, Hitbox
from pycats.combat.knockback import hitlag_frames
from pycats.config import HITLAG_BASE, HITLAG_CAP, HITLAG_DAMAGE_FACTOR
from pycats.core.input import InputFrame
from pycats.entities.attack import Attack
from pycats.entities.platform import Platform
from pycats.entities.player import Player

P2_CONTROLS = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_PERIOD,
    special=pygame.K_SLASH,
    shield=pygame.K_RSHIFT,
)


def _uncapped(damage: float) -> int:
    """The formula BEFORE the cap — a local oracle, independent of the source min()."""
    return math.floor(damage * HITLAG_DAMAGE_FACTOR + HITLAG_BASE)


# ---- conjunct 1: formula (below the cap) ----------------------------------


@pytest.mark.parametrize(
    "damage, expected",
    [
        (0, 5),  # floor(0*0.3846154 + 5) = floor(5.00) = 5  (base only)
        (9, 8),  # floor(9*0.3846154 + 5) = floor(8.46) = 8
        (12, 9),  # floor(12*0.3846154 + 5) = floor(9.62) = 9
        (13, 10),  # floor(13*0.3846154 + 5) = floor(10.00) = 10
        (60, 28),  # floor(60*0.3846154 + 5) = floor(28.08) = 28  (still below cap)
    ],
)
def test_c002_formula_reference_values(damage, expected):
    """PYC-C-002-GRAPE conjunct 1: hitlag = floor(d*0.3846154 + 5) below the cap.

    Every reference point here is strictly below HITLAG_CAP, so removing the cap
    would NOT change these — that keeps this test's failure attributable to the
    formula (the `+5` base), not to the cap conjunct.
    """
    assert expected < HITLAG_CAP, "reference point must be below the cap to isolate the formula"
    assert hitlag_frames(damage) == expected


def test_c002_zero_damage_is_the_base():
    """PYC-C-002-GRAPE conjunct 1: a 0% hit still freezes for exactly the base (5)."""
    assert hitlag_frames(0) == HITLAG_BASE == 5


# ---- conjunct 2: cap at 30 ------------------------------------------------


@pytest.mark.parametrize("damage", [100, 1000])
def test_c002_capped_at_30(damage):
    """PYC-C-002-GRAPE conjunct 2: large damage floors to exactly the cap (30).

    Each damage stays far above the cap even if the base/factor shift, so this
    test reds only when the `min(30, ...)` clamp is removed — it is isolated from
    the formula-conjunct mutation (dropping the base leaves 100/1000 still capped).
    """
    assert _uncapped(damage) > HITLAG_CAP, "damage must exceed the cap uncapped to test the clamp"
    assert hitlag_frames(damage) == HITLAG_CAP == 30


def test_c002_cap_clamps_a_would_be_larger_value():
    """PYC-C-002-GRAPE conjunct 2: the smallest damage the cap actually clamps.

    d=68 gives floor(68*0.3846154 + 5) = floor(31.15) = 31 uncapped; the cap pulls
    it down to exactly 30. d=67 already floors to 30 on its own, so 68 is the first
    value where the clamp changes the result — the precise cap boundary. This test
    encodes that exact boundary, so it also moves if the base/factor change (it is
    the boundary pin, not the base-robust cap pin above); removing the `min` reds it.
    """
    assert _uncapped(67) == 30  # floors to the cap without needing the clamp
    assert _uncapped(68) == 31  # first value the clamp must pull down
    assert hitlag_frames(68) == 30


# ---- conjunct 3: both fighters freeze -------------------------------------


def _mk(char, x, facing):
    controls = P1 if facing else P2_CONTROLS
    return Player(x, 100, controls, (255, 160, 64), eye_color=(0, 0, 0), char_name=char, facing_right=facing)


def _hit(owner, damage):
    hb = Hitbox(circle=Circle(dx=20, dy=30, r=14), damage=damage, angle=45, base_knockback=30.0, knockback_growth=100.0)
    return Attack(owner, hitbox=hb, lifetime=2)


def test_c002_hit_freezes_both_attacker_and_defender():
    """PYC-C-002-GRAPE conjunct 3: a connecting hit sets hitlag_timer on BOTH fighters.

    Damage 12 -> hl = 9 > 0, so a mutation that zeroes the attacker's assignment
    makes the attacker read 0 != 9 and this test reds (the freeze is not vacuously 0).
    """
    pygame.init()
    attacker = _mk("P1", 100, True)
    defender = _mk("P2", 130, False)
    atk = _hit(attacker, 12)
    defender.fighter.receive_hit(atk)
    hl = hitlag_frames(12)
    assert hl > 0, "the freeze must be non-zero for this test to be able to fail"
    assert defender.fighter.hitlag_timer == hl, "defender should freeze for hl frames"
    assert attacker.fighter.hitlag_timer == hl, "attacker should freeze for the same hl frames"


# ---- conjunct 4: position + hitstun held during the freeze ----------------


def test_c002_position_held_during_freeze_then_resumes():
    """PYC-C-002-GRAPE conjunct 4: position is pinned every freeze frame, then the slide moves it.

    Skipping the hitlag early-return in Player.update would let step_physics run
    during the freeze, so rect.x would move on frame 0 and this test reds.
    """
    pygame.init()
    attacker = _mk("P1", 100, True)
    defender = _mk("P2", 200, False)
    platforms = [Platform(pygame.Rect(0, 160, 600, 40), thin=False)]
    grp = pygame.sprite.Group()

    atk = _hit(attacker, 12)
    defender.fighter.receive_hit(atk)
    hl = hitlag_frames(12)
    assert defender.fighter.vel.length() > 0, "launch velocity is set at hit time (held until the freeze ends)"

    x0 = defender.rect.x
    noop = InputFrame(held=set(), pressed=set(), released=set())

    for f in range(hl):
        defender.update(noop, platforms, grp)
        assert defender.rect.x == x0, f"position must not move during hitlag (freeze frame {f})"
        assert defender.fighter.hitlag_timer == hl - 1 - f, "the freeze counts down one per frame"

    # Freeze over: the launch velocity now carries the fighter.
    defender.update(noop, platforms, grp)
    assert defender.rect.x != x0, "position should move once the freeze ends (knockback slide)"


def test_c002_hitstun_countdown_held_during_freeze():
    """PYC-C-002-GRAPE conjunct 4: the hitstun timer is frozen during hitlag, then ticks.

    hurt_timer is set at hit time and must not decrement while hitlag_timer > 0;
    dropping the early-return would let it tick during the freeze and red this test.
    """
    pygame.init()
    attacker = _mk("P1", 100, True)
    defender = _mk("P2", 200, False)
    platforms = [Platform(pygame.Rect(0, 160, 600, 40), thin=False)]
    grp = pygame.sprite.Group()

    atk = _hit(attacker, 12)
    defender.fighter.receive_hit(atk)
    hl = hitlag_frames(12)
    hurt0 = defender.fighter.hurt_timer
    assert hurt0 > 0, "the hit must impart hitstun for the countdown-freeze to be observable"
    noop = InputFrame(held=set(), pressed=set(), released=set())

    for f in range(hl):
        defender.update(noop, platforms, grp)
        assert defender.fighter.hurt_timer == hurt0, f"hitstun must not tick during hitlag (freeze frame {f})"

    # Freeze over: hitstun now begins to drain.
    defender.update(noop, platforms, grp)
    assert defender.fighter.hurt_timer < hurt0, "hitstun should tick down once the freeze ends"

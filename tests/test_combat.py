"""tests/test_combat.py

Unit tests for circle-based hit detection in process_hits (Task 5).

Test strategy:
  - Use lightweight synthetic player/attack stubs so we don't need pygame or a
    full game loop.  The combat system only reads these attributes:
      player: invulnerable, is_alive, rect (for hurtbox origin), facing_right,
              fighter_data.hurtbox.circles, receive_hit(), record_hit_landed()
      attack: active, owner, disappear_on_hit, hit_cx, hit_cy, hit_r,
              damage, angle, base_knockback, knockback_growth
  - Geometric values are chosen explicitly so tests are self-documenting.

Origin convention (from default_cat.py, confirmed in task-5-brief.md):
  Circle.dx/dy are offsets from the player rect top-left (origin_x=rect.x,
  origin_y=rect.y).  resolve_circle() adds dx when facing right, subtracts dx
  when facing left.
"""
from __future__ import annotations
import types
import pytest
import pygame

from pycats.combat.data import Circle, Hitbox, Hurtbox, FighterData
from pycats.combat.geometry import resolve_circle
from pycats.systems.combat import process_hits


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------

def _make_rect(x=100, y=100, w=40, h=60):
    r = pygame.Rect(x, y, w, h)
    return r


def _make_fighter_data(hurtbox_circles):
    hb = Hurtbox(circles=tuple(hurtbox_circles))
    return FighterData(hurtbox=hb, moves={})


def _make_player(rect, *, hurtbox_circles, facing_right=True,
                 invulnerable=False, is_alive=True):
    """Return a lightweight namespace that satisfies combat's player contract."""
    p = types.SimpleNamespace(
        rect=rect,
        facing_right=facing_right,
        invulnerable=invulnerable,
        is_alive=is_alive,
        fighter_data=_make_fighter_data(hurtbox_circles),
        state="idle",            # combat reads .state for the crouch hurtbox (#124)
        crouch_hurtbox=None,     # via p.fighter (set below) — None = no crouch box
        hits_received=0,
        hits_landed=0,
    )

    def receive_hit(atk):
        p.hits_received += 1

    def record_hit_landed():
        p.hits_landed += 1

    p.receive_hit = receive_hit
    p.record_hit_landed = record_hit_landed
    p.fighter = p
    return p


def _make_attack(owner, *, hit_cx, hit_cy, hit_r,
                 damage=10.0, angle=0, active=True,
                 disappear_on_hit=False, base_knockback=0.0, knockback_growth=0.0):
    """Return a lightweight namespace that satisfies combat's attack contract."""
    atk = types.SimpleNamespace(
        owner=owner,
        hit_cx=hit_cx,
        hit_cy=hit_cy,
        hit_r=hit_r,
        damage=damage,
        angle=angle,
        base_knockback=base_knockback,
        knockback_growth=knockback_growth,
        active=active,
        disappear_on_hit=disappear_on_hit,
        _killed=False,
    )

    def kill():
        atk._killed = True
        atk.active = False

    atk.kill = kill
    return atk


# ---------------------------------------------------------------------------
# Scenario geometry
# ---------------------------------------------------------------------------
# Player rect at (100, 100), 40×60.
# Hurtbox: single circle dx=20, dy=30 (rect-center), r=14
#   → absolute center when facing right: (120, 130)
# Attack hitbox that OVERLAPS: center (130, 130), r=12
#   dist to hurtbox center = 10 px < 14+12=26  → HIT
# Attack hitbox that MISSES: center (200, 130), r=12
#   dist to hurtbox center = 80 px > 26          → MISS

PLAYER_RECT = _make_rect(100, 100, 40, 60)
HURTBOX_CIRCLES = [Circle(dx=20, dy=30, r=14)]

HIT_ATK_CX = 130   # overlaps hurtbox
HIT_ATK_CY = 130
HIT_ATK_R  = 12

MISS_ATK_CX = 200   # too far right
MISS_ATK_CY = 130
MISS_ATK_R  = 12


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_hit_lands_when_circles_overlap():
    """Hitbox circle overlapping defender hurtbox circle → receive_hit called."""
    pygame.init()
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=HURTBOX_CIRCLES)
    defender = _make_player(PLAYER_RECT, hurtbox_circles=HURTBOX_CIRCLES)
    atk = _make_attack(owner, hit_cx=HIT_ATK_CX, hit_cy=HIT_ATK_CY, hit_r=HIT_ATK_R)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1, "defender should have received one hit"
    assert atk.active is False, "attack should deactivate after hitting"


def test_no_hit_when_circles_do_not_overlap():
    """Hitbox circle outside all defender hurtbox circles → no hit."""
    pygame.init()
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=HURTBOX_CIRCLES)
    defender = _make_player(PLAYER_RECT, hurtbox_circles=HURTBOX_CIRCLES)
    atk = _make_attack(owner, hit_cx=MISS_ATK_CX, hit_cy=MISS_ATK_CY, hit_r=MISS_ATK_R)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 0, "defender should not be hit when circles don't overlap"
    assert atk.active is True, "attack should remain active when no hit occurred"


def test_invulnerable_defender_is_skipped():
    """An intangible (invulnerable) defender is not hit even when circles overlap."""
    pygame.init()
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=HURTBOX_CIRCLES)
    defender = _make_player(PLAYER_RECT, hurtbox_circles=HURTBOX_CIRCLES,
                            invulnerable=True)
    atk = _make_attack(owner, hit_cx=HIT_ATK_CX, hit_cy=HIT_ATK_CY, hit_r=HIT_ATK_R)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 0, "invulnerable defender should not be hit"
    # attack should stay active since nothing was hit
    assert atk.active is True, "attack should remain active when defender is invulnerable"


def test_self_hit_is_excluded():
    """An attack does not hit its own owner."""
    pygame.init()
    owner = _make_player(PLAYER_RECT, hurtbox_circles=HURTBOX_CIRCLES)
    # The attack is centered right on the owner's hurtbox — circles definitely overlap.
    atk = _make_attack(owner, hit_cx=HIT_ATK_CX, hit_cy=HIT_ATK_CY, hit_r=HIT_ATK_R)

    process_hits([owner], [atk])

    assert owner.hits_received == 0, "owner should not be hit by their own attack"
    # active stays True since no valid target was hit
    assert atk.active is True, "attack should remain active when only target is owner"


def test_disappear_on_hit_kills_attack():
    """An attack with disappear_on_hit=True is killed (not just deactivated) on hit."""
    pygame.init()
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=HURTBOX_CIRCLES)
    defender = _make_player(PLAYER_RECT, hurtbox_circles=HURTBOX_CIRCLES)
    atk = _make_attack(owner, hit_cx=HIT_ATK_CX, hit_cy=HIT_ATK_CY, hit_r=HIT_ATK_R,
                       disappear_on_hit=True)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1, "defender should have received one hit"
    assert atk._killed is True, "disappear_on_hit attack should be killed on hit"


def test_dead_defender_is_skipped():
    """A dead (is_alive=False) defender is not hit even when circles overlap."""
    pygame.init()
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=HURTBOX_CIRCLES)
    defender = _make_player(PLAYER_RECT, hurtbox_circles=HURTBOX_CIRCLES,
                            is_alive=False)
    atk = _make_attack(owner, hit_cx=HIT_ATK_CX, hit_cy=HIT_ATK_CY, hit_r=HIT_ATK_R)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 0, "dead defender should not be hit"


def test_inactive_attack_does_not_hit():
    """An attack with active=False does not trigger any hit."""
    pygame.init()
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=HURTBOX_CIRCLES)
    defender = _make_player(PLAYER_RECT, hurtbox_circles=HURTBOX_CIRCLES)
    atk = _make_attack(owner, hit_cx=HIT_ATK_CX, hit_cy=HIT_ATK_CY, hit_r=HIT_ATK_R,
                       active=False)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 0, "inactive attack should not hit"


def test_hit_with_multi_circle_hurtbox():
    """Hitbox must overlap at least one circle of a multi-circle hurtbox."""
    pygame.init()
    # Two-circle hurtbox: upper at dy=15, lower at dy=45, both dx=20, r=14
    # rect at (100, 100): upper center=(120, 115), lower center=(120, 145)
    multi_circles = [Circle(dx=20, dy=15, r=14), Circle(dx=20, dy=45, r=14)]
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=multi_circles)
    defender = _make_player(PLAYER_RECT, hurtbox_circles=multi_circles)

    # attack aimed at lower circle center (120, 145), r=8
    # dist to lower: 0 → overlap. dist to upper: 30 px > 14+8=22 → no overlap with upper
    atk = _make_attack(owner, hit_cx=120, hit_cy=145, hit_r=8)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1, (
        "attack overlapping the lower hurtbox circle should register a hit"
    )


def test_body_center_hurtbox_is_facing_invariant():
    """A symmetric (body-centre) hurtbox does not move when the fighter turns
    around (#64). Player at (100,100), body 40 wide → centre x=120. A dx=20
    circle resolves to cx=120 whether facing right (100+20) or left (100+40-20).
    The old left-edge mirror put the left-facing hurtbox at 80, off-body."""
    pygame.init()
    circles = [Circle(dx=20, dy=30, r=14)]  # dx=20 == body centre of the 40-wide body
    owner = _make_player(_make_rect(0, 0), hurtbox_circles=circles)

    # A body-centre attack (120,130) connects regardless of defender facing.
    for facing in (True, False):
        d = _make_player(PLAYER_RECT, hurtbox_circles=circles, facing_right=facing)
        process_hits([owner, d], [_make_attack(owner, hit_cx=120, hit_cy=130, hit_r=6)])
        assert d.hits_received == 1, f"body-centre attack should hit (facing_right={facing})"

    # The old off-body mirror position (80,130) now misses a left-facing defender.
    d2 = _make_player(PLAYER_RECT, hurtbox_circles=circles, facing_right=False)
    process_hits([owner, d2], [_make_attack(owner, hit_cx=80, hit_cy=130, hit_r=6)])
    assert d2.hits_received == 0, "off-body (old-mirror) position should now miss"

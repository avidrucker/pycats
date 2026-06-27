"""tests/test_multi_hitbox.py

Multi-hitbox-per-move consumption (#130, #38 slice 4a).

A MoveData may carry >1 Hitbox. The engine must:
  1. activate the move's FULL hitbox tuple (not just hitboxes[0]),
  2. on a connect, test the boxes in PRIORITY ORDER (tuple order) and apply the
     FIRST box that overlaps the defender's hurtbox, and
  3. hit a given target AT MOST ONCE per move-instance (a defender overlapping
     two of a move's boxes takes one hit, from the higher-priority box).

Tests drive the real Attack (so we exercise circle resolution) + the real
process_hits, with lightweight player stubs (no full game loop).

Geometry: attacker rect at (0,0), facing right → a Hitbox Circle(dx,dy,r)
resolves to absolute centre (dx, dy). Defender rect at (100,100,40,60) with a
single hurtbox circle dx=20,dy=30,r=14 → absolute centre (120,130).
"""
from __future__ import annotations
import types
import pygame

from pycats.combat.data import Circle, Hitbox, Hurtbox, FighterData
from pycats.entities.attack import Attack
from pycats.systems.combat import process_hits


def _player(rect, *, hurtbox_circles, facing_right=True,
            invulnerable=False, is_alive=True):
    p = types.SimpleNamespace(
        rect=rect,
        facing_right=facing_right,
        invulnerable=invulnerable,
        is_alive=is_alive,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=tuple(hurtbox_circles)),
                                 moves={}),
        hits_received=0,
        hits_landed=0,
        last_damage=None,
        last_angle=None,
    )

    def receive_hit(atk):
        p.hits_received += 1
        p.last_damage = atk.damage
        p.last_angle = atk.angle

    def record_hit_landed():
        p.hits_landed += 1

    p.receive_hit = receive_hit
    p.record_hit_landed = record_hit_landed
    p.fighter = p
    return p


_DEF_HURTBOX = [Circle(dx=20, dy=30, r=14)]   # defender centre (120,130)


def _hb(dx, dy, r, *, damage, angle):
    return Hitbox(circle=Circle(dx=dx, dy=dy, r=r), damage=damage, angle=angle,
                  base_knockback=30.0, knockback_growth=80.0)


def test_non_first_hitbox_can_connect():
    """A move whose only connecting box is box[2] still lands — and applies
    box[2]'s params (today's engine drops everything past hitboxes[0])."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)

    move_boxes = (
        _hb(300, 130, 10, damage=99, angle=0),    # box[0] — far, misses
        _hb(320, 130, 10, damage=99, angle=0),    # box[1] — far, misses
        _hb(120, 130, 12, damage=8,  angle=80),   # box[2] — overlaps (120,130)
    )
    atk = Attack(owner, hitboxes=move_boxes, lifetime=4)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1, "box[2] should connect"
    assert defender.last_damage == 8, "the connecting box's damage must be applied"
    assert defender.last_angle == 80, "the connecting box's angle must be applied"


def test_overlapping_boxes_hit_once_in_priority_order():
    """A defender overlapping two of a move's boxes is hit ONCE, with the
    higher-priority (earlier in the tuple) box's params."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)

    move_boxes = (
        _hb(120, 130, 12, damage=9, angle=80),    # box[0] — overlaps, priority
        _hb(118, 130, 12, damage=5, angle=361),   # box[1] — also overlaps
    )
    atk = Attack(owner, hitboxes=move_boxes, lifetime=4)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1, "two overlapping boxes of one move = one hit"
    assert defender.last_damage == 9, "priority (first) box's params must win"
    assert defender.last_angle == 80


def test_single_box_via_hitbox_kwarg_unchanged():
    """Back-compat: a single-box Attack built with hitbox= behaves exactly as
    before (one connect, that box's params)."""
    pygame.init()
    owner = _player(pygame.Rect(0, 0, 40, 60), hurtbox_circles=_DEF_HURTBOX)
    defender = _player(pygame.Rect(100, 100, 40, 60), hurtbox_circles=_DEF_HURTBOX)

    atk = Attack(owner, hitbox=_hb(120, 130, 12, damage=10, angle=0), lifetime=3)

    process_hits([owner, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == 10
    assert defender.last_angle == 0

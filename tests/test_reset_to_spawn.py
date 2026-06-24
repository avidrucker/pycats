"""Issue #34 — Player.reset_to_spawn() is the single authoritative per-life reset.

The key invariant the consolidation protects: facing is restored from
`original_facing_right`, NOT a hardcoded literal (reset_game used to hardcode
True/False per player, which is correct only by coincidence on the current
config and would drift the moment a player is constructed facing the other way).
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.config import P1_COLOR, WHITE

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _player(facing_right):
    return Player(x=460, y=360, controls=C, color=P1_COLOR, eye_color=WHITE,
                  char_name="Cat", facing_right=facing_right)


def test_reset_restores_original_facing_left():
    p = _player(facing_right=False)   # constructed facing LEFT
    p.facing_right = True             # turned around during play
    p.reset_to_spawn()
    assert p.facing_right is False    # back to original, not a literal


def test_reset_restores_original_facing_right():
    p = _player(facing_right=True)
    p.facing_right = False
    p.reset_to_spawn()
    assert p.facing_right is True


def test_reset_clears_transient_state_and_position():
    p = _player(facing_right=True)
    # dirty a spread of per-life state
    p.is_alive = False
    p.dodge_timer = p.hurt_timer = p.stun_timer = p.attack_timer = 9
    p.invulnerable = True
    p.percent = 80
    p.vel.update(7, -7)
    p.rect.center = (9999, 9999)
    p.reset_to_spawn()
    assert p.is_alive
    assert (p.dodge_timer, p.hurt_timer, p.stun_timer, p.attack_timer) == (0, 0, 0, 0)
    assert p.invulnerable is False
    assert p.percent == 0
    assert (p.vel.x, p.vel.y) == (0, 0)
    assert p.rect.midbottom == (int(p.spawn_point.x), int(p.spawn_point.y))

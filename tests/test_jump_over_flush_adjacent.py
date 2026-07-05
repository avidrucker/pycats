"""Repro + spec for the jump-over-flush-adjacent-character bug (#22).

When fighter A is flush against a stationary fighter B and A jumps *toward/over* B,
B is shoved sideways by `resolve_player_push`, which applies its X-separation on
any rect overlap — including while A is airborne *above* B. Jumping over is fine
(PM allows it); displacing the grounded fighter is not.

This file is the deterministic, RNG-free repro. Both cases are now live
regression guards: the fix for #68 (a vertical-overlap gate in
resolve_player_push) holds the stationary fighter's displacement at ~0.
"""
import pygame as pg

from pycats.config import P1_COLOR, P2_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.core.physics import resolve_player_push
from pycats.entities.platform import Platform
from pycats.entities.player import Player

P1K = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
       "down": pg.K_s, "shield": pg.K_x, "attack": pg.K_v}
P2K = {"left": pg.K_LEFT, "right": pg.K_RIGHT, "up": pg.K_UP,
       "down": pg.K_DOWN, "shield": pg.K_COMMA, "attack": pg.K_SLASH}


def _flush_pair():
    """P1 and P2 standing flush (body-adjacent) on a wide thick platform.
    P1 is to the LEFT, P2 to the RIGHT; their bodies (40px wide) touch."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(100, 400, 700, 40), thin=False))
    p1 = Player(x=400, y=340, controls=P1K, color=P1_COLOR, eye_color=WHITE,
                char_name="P1", facing_right=True)
    p2 = Player(x=440, y=340, controls=P2K, color=P2_COLOR, eye_color=WHITE,
                char_name="P2", facing_right=False)
    players = [p1, p2]
    for _ in range(3):  # settle both onto the platform, flush
        _step(players, plats, set(), set())
    assert p2.rect.x - p1.rect.x == 40, "fixture: players must start flush"
    return p1, p2, players, plats


def _step(players, plats, held, pressed):
    fi = InputFrame(held=set(held), pressed=set(pressed), released=set())
    for p in players:
        p.update(fi, plats, pg.sprite.Group())
    resolve_player_push(players)


def _p1_jumps_toward_p2(p1, p2, players, plats):
    """P1 jumps while holding RIGHT (toward P2). P2 presses nothing.
    Returns P2's horizontal displacement (px) over the jump arc."""
    p2_start = p2.rect.centerx
    _step(players, plats, {pg.K_w, pg.K_d}, {pg.K_w})  # jump + toward
    for _ in range(40):
        _step(players, plats, {pg.K_d}, set())          # keep drifting toward
    return abs(p2.rect.centerx - p2_start)


def test_straight_up_jump_while_flush_does_not_displace_neighbor():
    """Correct behavior (regression guard): jumping STRAIGHT UP while flush moves
    neither fighter — no rect overlap, no push."""
    p1, p2, players, plats = _flush_pair()
    p1_start, p2_start = p1.rect.centerx, p2.rect.centerx
    _step(players, plats, {pg.K_w}, {pg.K_w})
    for _ in range(40):
        _step(players, plats, set(), set())
    assert p1.rect.centerx == p1_start, f"P1 drifted to {p1.rect.centerx}"
    assert p2.rect.centerx == p2_start, f"P2 displaced to {p2.rect.centerx}"


def test_jumping_over_flush_neighbor_should_not_shove_it():
    """Regression #68: a stationary fighter must not be shoved when a flush
    neighbor jumps over it. Before the fix P2 was ratcheted ~35px sideways by the
    X-push firing while P1 was airborne above it; the vertical-overlap gate in
    resolve_player_push now holds displacement at ~0."""
    p1, p2, players, plats = _flush_pair()
    displacement = _p1_jumps_toward_p2(p1, p2, players, plats)
    assert displacement <= 4, f"stationary P2 shoved {displacement}px by P1's flyover"

# tests/test_render_battle.py
import pygame
from pycats.sim.runner import build_stage, build_players
from pycats.render_battle import render_battle


def test_render_battle_draws_without_error():
    surface = pygame.Surface((960, 540))
    platforms = build_stage()
    p1, p2, players = build_players("legacy")
    # advance one frame so players have valid rects/tails
    from pycats.core.input import InputFrame
    empty = InputFrame(held=set(), pressed=set(), released=set())
    for p in players:
        p.update(empty, platforms, pygame.sprite.Group())
    render_battle(surface, players, platforms)  # must not raise
    assert surface.get_at((0, 0)) is not None

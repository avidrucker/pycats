"""Per-fighter body RENDER size (#282 — regression from #275).

The cat body composite must be sized to the fighter's `stand_size`, not the global
PLAYER_SIZE, so a small archetype (Birky, 40x44) renders shorter than a default-sized
one (Nalio, 40x60) and its drawn body doesn't hang below its collision box (clipping
into platforms).
"""
import pygame

from pycats.battle_screen import BattleScreen
from pycats.config import BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.render_battle import (
    _BODY_PAD_BOT,
    _BODY_PAD_TOP,
    _cat_body_surface,
    render_battle,
)

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def _battle():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("birky", "nalio")  # birky = 40x44, nalio = default 40x60
    return bs


def test_body_composite_sizes_to_stand_size():
    bs = _battle()
    birky, nalio = bs.player1, bs.player2
    birky_comp = _cat_body_surface(birky)
    nalio_comp = _cat_body_surface(nalio)
    # composite height = pad_top + stand_height + pad_bot — tracks the fighter's body
    assert birky_comp.get_height() == _BODY_PAD_TOP + birky.fighter.stand_size[1] + _BODY_PAD_BOT
    assert nalio_comp.get_height() == _BODY_PAD_TOP + nalio.fighter.stand_size[1] + _BODY_PAD_BOT
    # the small archetype renders shorter than the default-sized one
    assert birky_comp.get_height() < nalio_comp.get_height()


def test_birky_body_does_not_render_below_its_feet():
    """The drawn body must not hang below the collision box (the floor-clip)."""
    bs = _battle()
    birky = bs.player1
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surf.fill(BG_COLOR)
    render_battle(surf, bs.players, platforms=[])
    cx = birky.rect.centerx
    # a few px below the feet should remain background — no body overhang
    for dy in (5, 10, 14):
        y = birky.rect.bottom + dy
        if y < SCREEN_HEIGHT:
            assert surf.get_at((cx, y))[:3] == BG_COLOR, f"body clips {dy}px below feet"

"""Attack visuals should reflect resolved hitbox primitives (#154)."""
import pygame

from pycats.combat.data import Circle, Hitbox
from pycats.config import ATTACK_SIZE
from pycats.entities import Player
from pycats.entities.attack import Attack

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
          down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
          shield=pygame.K_x)


def test_attack_visual_bounds_follow_all_hitbox_circles():
    pygame.init()
    owner = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                   char_name="P1", facing_right=True)
    hitboxes = (
        Hitbox(circle=Circle(dx=32, dy=30, r=8), damage=3, angle=83),
        Hitbox(circle=Circle(dx=68, dy=30, r=16), damage=3, angle=85),
    )

    attack = Attack(owner, hitboxes=hitboxes, lifetime=2)

    assert attack.image.get_size() != ATTACK_SIZE
    assert attack.image.get_width() >= 60
    assert attack.image.get_height() >= 32

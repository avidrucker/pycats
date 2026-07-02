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

    # #326/H-b: the entity no longer owns a Surface; its `rect` carries the same
    # visual bounds (render_battle builds the Surface from that rect).
    assert attack.rect.size != ATTACK_SIZE
    assert attack.rect.width >= 60
    assert attack.rect.height >= 32


def test_attack_renders_reddish_visual_at_hitbox_center():
    """#326/H-b slice 2: render_attacks paints the attack visual (was Attack.image).
    A single-hitbox attack shows a red fill at its rect; the centre pixel reads
    red-dominant over a black background. Able-to-fail: corrupt the fill -> not red.
    """
    from pycats.render_battle import render_attacks
    owner = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                   char_name="P1", facing_right=True)
    atk = Attack(owner, hitbox=Hitbox(circle=Circle(dx=20, dy=20, r=10),
                                      damage=1, angle=0), lifetime=2)
    surf = pygame.Surface((400, 400))
    surf.fill((0, 0, 0))
    render_attacks(surf, [atk])
    px = surf.get_at(atk.rect.center)
    assert px[0] > 100 and px[0] > px[1] and px[0] > px[2], f"not red-dominant: {tuple(px)}"

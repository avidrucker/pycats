"""Issue #101 — thick (solid) platforms must block their UNDERSIDE face.

Companion to test_thick_platform_sides.py (#5, the horizontal side faces). #101
asks whether a fighter can clip *up through* a thick platform's bottom face. The
upward branch lives in `core.physics.solve_vertical` (vel.y < 0 and the actor was
below the platform → snap actor.top to the platform bottom, zero vel.y).

This drives the real `Player.update` loop: a fighter stands on a floor and jumps
straight up into a thick platform acting as a ceiling, and we assert it never
penetrates above the ceiling's bottom face.
"""
import pygame

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _stage():
    # Ceiling (thick): bottom face at y=140, x-band [200, 400].
    ceiling = Platform(pygame.Rect(200, 100, 200, 40), thin=False)
    # Floor (thick): top at y=300, same x-band, so the jump starts from rest.
    floor = Platform(pygame.Rect(200, 300, 200, 40), thin=False)
    return [ceiling, floor], ceiling, floor


def _jump_into_ceiling(backend):
    platforms, ceiling, floor = _stage()
    # Stand centred under the ceiling (x-band); midbottom on the floor top (y=300).
    p = Player(300, 300, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="P1", facing_right=True, state_backend=backend)
    attacks = pygame.sprite.Group()
    noop = InputFrame(set(), set(), set())
    jump = InputFrame(held={P1["up"]}, pressed={P1["up"]}, released=set())

    # settle onto the floor
    for _ in range(5):
        p.update(noop, platforms, attacks)
    assert p.fighter.on_ground, "fixture: player did not settle on the floor"

    min_top = p.rect.top
    penetrated = False
    p.update(jump, platforms, attacks)            # launch
    for _ in range(30):                           # rise, hit ceiling, fall back
        p.update(noop, platforms, attacks)
        min_top = min(min_top, p.rect.top)
        # penetration = the body crossed ABOVE the ceiling's bottom face
        if p.rect.top < ceiling.rect.bottom:
            penetrated = True
    return p, ceiling, min_top, penetrated


def test_thick_platform_underside_blocks_upward_entry():
    for backend in ("legacy", "statechart"):
        p, ceiling, min_top, penetrated = _jump_into_ceiling(backend)
        # Non-vacuous: the jump must actually carry the head up to the ceiling.
        assert min_top <= ceiling.rect.bottom + 4, (
            f"[{backend}] jump never reached the ceiling (min_top={min_top}, "
            f"ceiling bottom={ceiling.rect.bottom}) — fixture too weak")
        # The body must never clip up through the underside.
        assert not penetrated, (
            f"[{backend}] fighter clipped up through the thick platform underside")

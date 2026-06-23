"""Issue #5 — thick (solid) platforms must block their SIDE faces.

Project M fidelity: a thick platform is solid on all sides; a thin platform is a
one-way floor you pass through from the sides and from below. These tests drive
the real `Player.update` loop into a platform's side face and assert that a
thick wall blocks entry while a thin platform does not.

Repro/proof of the original defect: tools/repro_issue_5.py.
"""
import pygame

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player(backend="statechart"):
    # midbottom anchor; placed just LEFT of a wall at x=300, inside its band.
    return Player(260, 200, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True, state_backend=backend)


def _wall(thin=False):
    # A tall vertical platform: left face at x=300, spanning y[0,400] so the
    # player stays in the platform's vertical band for the whole test window.
    return [Platform(pygame.Rect(300, 0, 80, 400), thin=thin)]


def _hold(action):
    return InputFrame(held={P1[action]}, pressed=set(), released=set())


def _drive(p, platforms, action, frames):
    """Hold a direction for N frames; return True if the player ever overlapped
    a (solid) platform — i.e. penetrated it."""
    attacks = pygame.sprite.Group()
    penetrated = False
    reached_face = False
    for _ in range(frames):
        p.update(_hold(action), platforms, attacks)
        if p.rect.colliderect(platforms[0].rect):
            penetrated = True
        if p.rect.right >= platforms[0].rect.left - 1:
            reached_face = True
    return penetrated, reached_face


def test_thick_platform_left_face_blocks_entry():
    p = _mk_player()
    walls = _wall(thin=False)
    penetrated, reached_face = _drive(p, walls, "right", 15)

    # The player must actually be driven up to the wall (else the test is vacuous)
    assert reached_face, "player never reached the wall face — test setup is wrong"
    # ...and must never enter the solid platform body.
    assert not penetrated, "player penetrated the thick platform's left side face"
    assert p.rect.right <= walls[0].rect.left


def test_thick_platform_right_face_blocks_entry():
    # Player starts to the RIGHT of the wall, driving left into the right face.
    p = Player(420, 200, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="P1", facing_right=False, state_backend="statechart")
    walls = _wall(thin=False)
    attacks = pygame.sprite.Group()
    penetrated = reached_face = False
    for _ in range(15):
        p.update(_hold("left"), walls, attacks)
        if p.rect.colliderect(walls[0].rect):
            penetrated = True
        if p.rect.left <= walls[0].rect.right + 1:
            reached_face = True

    assert reached_face, "player never reached the wall face — test setup is wrong"
    assert not penetrated, "player penetrated the thick platform's right side face"
    assert p.rect.left >= walls[0].rect.right


def test_thin_platform_side_stays_passthrough():
    # PM fidelity: thin (soft) platforms are one-way floors — you pass through
    # their sides. The fix must NOT over-block these.
    p = _mk_player()
    thin = _wall(thin=True)
    _drive(p, thin, "right", 15)
    # The player should have moved THROUGH the thin platform's left face.
    assert p.rect.left > thin[0].rect.left, "thin platform wrongly blocked the side"


def test_landing_on_thick_top_is_not_side_ejected():
    # A player dropping onto a thick platform's top must land normally and must
    # NOT be shoved off the side by the horizontal resolver.
    p = Player(300, 280, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="P1", facing_right=True, state_backend="statechart")
    floor = [Platform(pygame.Rect(200, 300, 200, 40), thin=False)]  # top y=300
    attacks = pygame.sprite.Group()
    noop = InputFrame(set(), set(), set())
    for _ in range(20):
        p.update(noop, floor, attacks)

    assert p.on_ground, "player failed to land on the thick platform top"
    assert p.rect.bottom == floor[0].rect.top
    assert floor[0].rect.left <= p.rect.left and p.rect.right <= floor[0].rect.right, \
        "player was wrongly ejected sideways off the platform top"

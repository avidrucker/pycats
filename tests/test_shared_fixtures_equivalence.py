"""#884 (Child 2 of #833): the shared test infra in tests/helpers.py + the
conftest fixtures must be behaviourally identical to the hand-rolled Player /
control-map / ground boilerplate they replace across ~two dozen files.

Able-to-fail guard: if a fixture or helper drifts from the hand-rolled shape
(different control map, spawn coords, facing, or ground platform), these
assertions go red — so the mass migration can't quietly change what a migrated
test constructs.
"""

import pygame
from helpers import P1, advance, ground, mk_player

from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

# The exact hand-rolled construction the migrated files used to repeat inline.
_HANDROLLED_P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
    smash=pygame.K_b,
)


def _handrolled_player():
    return Player(100, 100, _HANDROLLED_P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


def test_p1_control_map_matches_handrolled():
    assert P1 == _HANDROLLED_P1


def test_mk_player_matches_handrolled_construction():
    ref = _handrolled_player()
    got = mk_player()
    assert got.controls == ref.controls
    assert got.rect.midbottom == ref.rect.midbottom == (100, 100)
    assert got.fighter.facing_right == ref.fighter.facing_right is True
    assert got.char_color == ref.char_color == (255, 160, 64)


def test_player_fixture_matches_handrolled(player):
    ref = _handrolled_player()
    assert player.controls == ref.controls
    assert player.rect.midbottom == ref.rect.midbottom
    assert player.fighter.facing_right == ref.fighter.facing_right


def test_ground_matches_handrolled():
    ref = [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]
    got = ground()
    assert len(got) == len(ref) == 1
    assert got[0].rect == ref[0].rect
    assert got[0].thin == ref[0].thin is False


def test_ground_fixture_matches_handrolled(ground):
    # `ground` here is the conftest fixture (a list), not the helper function.
    assert len(ground) == 1
    assert ground[0].rect == pygame.Rect(0, 100, 600, 40)
    assert ground[0].thin is False


def test_two_fighters_fixture_spawn_and_facing(two_fighters):
    p1, p2 = two_fighters
    assert p1.fighter.facing_right is True
    assert p2.fighter.facing_right is False
    assert p1.rect.midbottom == p2.rect.midbottom == (100, 100)
    assert p1.controls == P1


def test_advance_ticks_the_player_update():
    p = mk_player()
    start_y = p.rect.y
    frame = InputFrame(held=set(), pressed=set(), released=set())
    advance(p, 5, frame, [], pygame.sprite.Group())
    # 5 frames of gravity with no platforms: the fighter has fallen.
    assert p.rect.y > start_y

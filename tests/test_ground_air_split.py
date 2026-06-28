"""tests/test_ground_air_split.py

Ground/air attack-selection split (#38 slice, #136).

Pressing attack while airborne selects the character's neutral aerial ("nair")
when defined, else falls back to the ground "attack" move. Grounded neutral
attack selects "jab" when defined; directional ground normals fall back to the
legacy "attack" alias until each named move lands. The selector lives in
fighter_input.handle_actions and reads fighter.on_ground; we drive it directly
with on_ground set.
"""
import pygame

from pycats.entities.player import Player
from pycats.core.input import InputFrame

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _press_attack():
    return InputFrame(held=set(), pressed={P1["attack"]}, released=set())


def _press_down_attack():
    keys = {P1["attack"], P1["down"]}
    return InputFrame(held=keys, pressed={P1["attack"]}, released=set())


def _player(char_name):
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name=char_name, facing_right=True)


def test_grounded_nalio_neutral_attack_is_jab():
    pygame.init()
    p = _player("nalio")
    p.fighter.on_ground = True
    p.handle_actions(_press_attack(), pygame.sprite.Group())
    assert p.current_move is not None
    assert p.current_move.in_air is False, "grounded attack should be the ground move"
    assert p.current_move.hitboxes[0].damage == 3.0, "Nalio neutral-A = jab (3%)"


def test_grounded_nalio_down_attack_still_uses_down_tilt_alias():
    pygame.init()
    p = _player("nalio")
    p.fighter.on_ground = True
    p.handle_actions(_press_down_attack(), pygame.sprite.Group())
    assert p.current_move is not None
    assert p.current_move.in_air is False, "grounded attack should be the ground move"
    assert p.current_move.hitboxes[0].damage == 9.0, "Nalio down-A = down-tilt (9%)"


def test_airborne_nalio_attack_is_the_neutral_air():
    pygame.init()
    p = _player("nalio")
    p.fighter.on_ground = False
    p.handle_actions(_press_attack(), pygame.sprite.Group())
    assert p.current_move is not None
    assert p.current_move.in_air is True, "airborne attack should select the aerial"
    assert len(p.current_move.hitboxes) == 2, "Nalio nair has 2 hitboxes"
    assert p.current_move.hitboxes[0].damage == 12.0, "nair clean hit = 12%"


def test_airborne_default_cat_falls_back_to_ground_attack():
    """The default cat has no aerial -> airborne attack stays the ground move,
    so the sim/golden path is unchanged (golden safety)."""
    pygame.init()
    p = _player("P1")
    p.fighter.on_ground = False
    p.handle_actions(_press_attack(), pygame.sprite.Group())
    assert p.current_move is p.fighter_data.moves["attack"]
    assert p.current_move.in_air is False

# tests/test_player_seam.py
import pygame

from pycats.entities.player import Player

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player():
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


def test_player_exposes_state_property():
    p = _mk_player()
    assert p.state == "idle"


def test_player_force_ko_sets_label():
    p = _mk_player()
    p.engine.force("ko")
    assert p.state == "ko"


def test_player_engine_is_statechart():
    # ADR-0002 (#178): the statechart engine is the sole backend. The factory
    # builds it regardless of the retained `backend` param, so a default Player
    # gets a StatechartEngine (legacy is gone).
    from pycats.systems.state_engine_sc import StatechartEngine
    p = _mk_player()
    assert isinstance(p.engine, StatechartEngine)

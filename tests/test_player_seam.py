# tests/test_player_seam.py
from helpers import mk_player as _mk_player


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

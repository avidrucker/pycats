"""Live ScreenStateManager wire onto make_screen_engine (slice 1b of epic #100; #186).

Drives the REAL `ScreenStateManager` (real sub-managers + real guards, no mocks)
through a representative screen path on BOTH backends, proving the statecharts-py
engine is a behaviour-identical drop-in for the legacy FSM in the live screen flow.
The backend is selected via `PYCATS_SCREEN_BACKEND`, read in the manager's __init__.
"""
import pygame
import pytest

from pycats.core.input import InputFrame
from pycats.screen_manager import ScreenStateManager

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)

BACKENDS = ("legacy", "statechart")


def _mk(backend, monkeypatch):
    monkeypatch.setenv("PYCATS_SCREEN_BACKEND", backend)
    return ScreenStateManager(_P1, _P2)


def _empty():
    return InputFrame(held=set(), pressed=set(), released=set())


@pytest.mark.parametrize("backend", BACKENDS)
def test_live_screen_flow_identical_both_backends(backend, monkeypatch):
    sm = _mk(backend, monkeypatch)
    e = _empty()
    assert sm.get_state() == "main_menu", backend
    # main_menu -> char_select (real main-menu 'play' request drives the guard)
    sm.main_menu.action_requested = "play"
    sm.update(e)
    assert sm.get_state() == "char_select", backend
    # main_menu -> options -> back (real guards via sub-manager action_requested)
    sm.reset_to_main_menu()
    assert sm.get_state() == "main_menu", backend
    sm.main_menu.action_requested = "options"
    sm.update(e)
    assert sm.get_state() == "options", backend
    sm.options_menu.action_requested = "back"
    sm.update(e)
    assert sm.get_state() == "main_menu", backend


@pytest.mark.parametrize("backend", BACKENDS)
def test_reset_to_main_menu_force_path_both_backends(backend, monkeypatch):
    # The ESC-hold return-to-menu path: a non-guard-driven force jump to main_menu.
    sm = _mk(backend, monkeypatch)
    sm.main_menu.action_requested = "play"
    sm.update(_empty())
    assert sm.get_state() == "char_select", backend
    sm.reset_to_main_menu()
    assert sm.get_state() == "main_menu", backend


# --- #230 (slice 3 of #100): transition side-effects via entry/update actions ---
import types


@pytest.mark.parametrize("backend", BACKENDS)
def test_pause_to_win_screen_wires_stats_from_battle_via_on_enter(backend, monkeypatch):
    """pause -> win_screen (the 'end_match' stats view) wires the stats from the
    battle threaded into ctx, via _on_enter_win_screen — replacing game.py's
    previous_state loop hack. winner/loser unset => the from-pause stats branch."""
    sm = _mk(backend, monkeypatch)
    sm.engine.force("pause")
    assert sm.get_state() == "pause", backend
    sm.pause_menu.action_requested = "end_match"
    battle = types.SimpleNamespace(player1=object(), player2=object(),
                                   reset=lambda: None)
    sm.update(_empty(), battle)                      # battle now threaded into ctx
    assert sm.get_state() == "win_screen", backend
    wsm = sm.win_screen_manager
    assert wsm.from_pause is True, backend
    assert wsm.winner is battle.player1, backend
    assert wsm.loser is battle.player2, backend


@pytest.mark.parametrize("backend", BACKENDS)
def test_char_select_resets_battle_via_update_action(backend, monkeypatch):
    """Entering char_select with no winner resets the battle through
    _update_char_select (ctx battle) — replacing game.py's should_reset_game poll."""
    sm = _mk(backend, monkeypatch)
    sm.main_menu.action_requested = "play"
    sm.update(_empty())
    assert sm.get_state() == "char_select", backend
    reset_calls = []
    battle = types.SimpleNamespace(player1=None, player2=None,
                                   reset=lambda: reset_calls.append(1))
    sm.update(_empty(), battle)                      # winner/loser are None
    assert reset_calls, "char_select with no winner should reset the battle"

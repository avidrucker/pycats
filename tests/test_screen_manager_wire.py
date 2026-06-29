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

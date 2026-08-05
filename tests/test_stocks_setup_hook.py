"""ROUNDS v1 stocks/lives match-setup hook — the setup-site wiring (#1202).

The `starting_lives` helper (test_starting_lives.py) derives the count; these tests
prove the two setup paths — the headless sim (`sim/runner.build_players`) and the
live game (`screens/battle_screen.BattleScreen`) — actually honor a drafted stocks
card, and that a rematch (`reset`) re-applies it rather than snapping back to
INITIAL_LIVES. A stocks card is not live-only, so both paths must fire.
"""

from __future__ import annotations

import pygame

from pycats.config.stage import INITIAL_LIVES
from pycats.loadout.cards import load_cards
from pycats.screens.battle_screen import BattleScreen
from pycats.sim import runner

_PHOENIX = load_cards()["phoenix"]  # stocks add_n +1
_KEYS = {"left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w}


# --- headless sim path -------------------------------------------------------
def test_runner_default_is_initial_lives():
    p1, p2, _ = runner.build_players(p1_char="nalio", p2_char="nalio")
    assert p1.fighter.lives == INITIAL_LIVES
    assert p2.fighter.lives == INITIAL_LIVES


def test_runner_honors_drafted_stocks_card():
    p1, p2, _ = runner.build_players(p1_char="nalio", p2_char="nalio", p1_cards=(_PHOENIX,))
    assert p1.fighter.lives == INITIAL_LIVES + 1  # Phoenix drafted → +1 stock
    assert p2.fighter.lives == INITIAL_LIVES  # P2 drafted nothing


# --- live-game path ----------------------------------------------------------
def test_battle_screen_default_is_initial_lives():
    bs = BattleScreen(_KEYS, _KEYS)
    bs.create_from_selection("nalio", "nalio")
    assert bs.player1.fighter.lives == INITIAL_LIVES
    assert bs.player2.fighter.lives == INITIAL_LIVES


def test_battle_screen_honors_drafted_stocks_card():
    bs = BattleScreen(_KEYS, _KEYS)
    bs.create_from_selection("nalio", "nalio", p1_cards=(_PHOENIX,))
    assert bs.player1.fighter.lives == INITIAL_LIVES + 1
    assert bs.player2.fighter.lives == INITIAL_LIVES


def test_reset_reapplies_drafted_starting_lives():
    bs = BattleScreen(_KEYS, _KEYS)
    bs.create_from_selection("nalio", "nalio", p1_cards=(_PHOENIX,))
    bs.player1.fighter.lives = 1  # simulate mid-match stock loss
    bs.reset()
    assert bs.player1.fighter.lives == INITIAL_LIVES + 1  # Phoenix bonus, not bare INITIAL_LIVES
    assert bs.player2.fighter.lives == INITIAL_LIVES

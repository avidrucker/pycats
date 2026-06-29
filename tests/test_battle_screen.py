"""BattleScreen — de-globalized battle state + per-frame sim (slice 2 of #100; #193).

BattleScreen owns the battle state (player1/2, players, attacks) and the per-frame
sim step that used to live as module globals + an inline block in game.py's loop.
These tests pin its construction and deterministic stepping; a separate cross-check
(test_battle_screen_runner_parity) proves step() matches the golden-covered
sim/runner.py path.
"""
import pygame

from pycats.battle_screen import BattleScreen
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def test_battle_screen_create_from_selection_builds_two_players():
    bs = BattleScreen(_P1, _P2)
    assert bs.player1 is None and bs.player2 is None
    assert len(bs.players) == 0
    bs.create_from_selection("tabby", "calico")
    assert bs.player1 is not None and bs.player2 is not None
    assert set(bs.players) == {bs.player1, bs.player2}
    assert bs.player1.char_name == "P1" and bs.player2.char_name == "P2"


def test_battle_screen_step_matches_runner_sim_path():
    """The real oracle: BattleScreen.step must produce the SAME per-frame fighter +
    attack snapshots as sim/runner.run_battle (the golden-covered path) for identical
    fighters (calico/tabby — what build_players() uses), stage, and inputs. This
    proves the two parallel sim copies are equivalent, not just 'looks the same'."""
    from pycats.sim.runner import (run_battle, build_stage, snapshot,
                                    KEYMAPS, P1_KEYS, P2_KEYS)
    from pycats.sim.input_script import compile_timeline, InputSpan

    spans = [
        InputSpan(start=5, end=40, player=1, action="right"),
        InputSpan(start=12, end=14, player=1, action="attack"),
        InputSpan(start=20, end=55, player=2, action="left"),
        InputSpan(start=30, end=33, player=2, action="attack"),
    ]
    frame_inputs = compile_timeline(spans, KEYMAPS)
    n = len(frame_inputs)
    assert n > 40, "scenario should run a meaningful number of frames"

    runner_snaps = run_battle(frames=n, frame_inputs=frame_inputs)

    bs = BattleScreen(P1_KEYS, P2_KEYS)
    bs.create_from_selection("calico", "tabby")   # == build_players() fighters
    platforms = build_stage()

    class _M:  # BattleScreen owns no match engine; stub the match part of snapshot
        phase, winner = "in_play", 0

    for f in range(n):
        bs.step(frame_inputs[f], platforms)
        rs = runner_snaps[f]
        bp = snapshot(bs.players, bs.attacks, _M())
        assert bp[0] == rs[0], (f, "player parts diverged")
        assert bp[1] == rs[1], (f, "attack parts diverged")


def test_battle_screen_reset_restores_lives_and_clears_attacks():
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("calico", "tabby")
    bs.player1.fighter.lives = 1
    bs.player1.fighter.percent = 88.0
    bs.reset()
    from pycats.config import INITIAL_LIVES
    assert bs.player1.fighter.lives == INITIAL_LIVES
    assert bs.player1.fighter.percent == 0.0
    assert len(bs.attacks) == 0

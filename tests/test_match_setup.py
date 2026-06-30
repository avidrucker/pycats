"""Per-player character + CPU-level match setup (#244, #231 thread 4).

build_players / run_battle take a per-player character (loads its FighterData);
watch.cpu_controllers builds leveled AttackerControllers. The default path is
unchanged (golden-safe).
"""
import random

from pycats.sim.runner import build_players, run_battle
from pycats.sim.controllers import AttackerController
from watch import cpu_controllers


def test_build_players_loads_named_character_fighter_data():
    p1, p2, _ = build_players(p1_char="nalio")
    assert "neutral_b" in p1.fighter_data.moves, "P1 should be Nalio (has the fireball)"
    assert "neutral_b" not in p2.fighter_data.moves, "P2 left as the default cat"


def test_build_players_default_unchanged():
    p1, p2, _ = build_players()  # golden-safe default
    assert "neutral_b" not in p1.fighter_data.moves
    assert "neutral_b" not in p2.fighter_data.moves


def test_cpu_controllers_sets_per_player_levels():
    c1, c2 = cpu_controllers(5, 9, random.Random(0))
    assert isinstance(c1, AttackerController) and c1.level == 5
    assert isinstance(c2, AttackerController) and c2.level == 9


def test_cpu_controllers_none_for_unset_player():
    c1, c2 = cpu_controllers(None, 9, random.Random(0))
    assert c1 is None
    assert c2.level == 9


def test_run_battle_two_nalios_leveled_runs_headless():
    c1, c2 = cpu_controllers(5, 9, random.Random(7))
    snaps = run_battle(frames=30, controllers=(c1, c2),
                       p1_char="nalio", p2_char="nalio")
    assert len(snaps) == 30

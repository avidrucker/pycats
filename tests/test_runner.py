# tests/test_runner.py
from pycats.sim.runner import run_battle


def test_runner_is_deterministic():
    a = run_battle(backend="legacy", frames=120)
    b = run_battle(backend="legacy", frames=120)
    assert a == b


def test_runner_produces_one_snapshot_per_frame():
    snaps = run_battle(backend="legacy", frames=80)
    assert len(snaps) == 80


def test_runner_runs_statechart_backend():
    snaps = run_battle(backend="statechart", frames=80)
    assert len(snaps) == 80

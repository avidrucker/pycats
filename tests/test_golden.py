# tests/test_golden.py
"""Golden-snapshot regression oracle for the statechart engine.

Three deterministic scenarios are recorded:
- default:     200 frames with the default timeline
- combat:      COMBAT_SCRIPT inputs + 240-frame tail
- full_match:  ChaseController inputs captured once then frozen

Each test calls check_or_update(name, snaps) which compares the serialized
snapshots against tests/golden/<name>.json.  Set PYCATS_UPDATE_GOLDENS=1 to
(re)record them.
"""
from pycats.sim.runner import run_battle, KEYMAPS
from pycats.sim.input_script import compile_timeline, COMBAT_SCRIPT
from pycats.sim.controllers import ChaseController
from tests.golden_util import check_or_update

# ---- scenario constants ----
DEFAULT_FRAMES = 200
COMBAT_TAIL = 240


def test_golden_default():
    """200-frame default timeline produces a stable golden snapshot."""
    snaps = run_battle(backend="statechart", frames=DEFAULT_FRAMES)
    assert len(snaps) == DEFAULT_FRAMES
    check_or_update("default", snaps)


def test_golden_combat():
    """COMBAT_SCRIPT + tail: hurt and ko states must be reached; stable golden."""
    frame_inputs = compile_timeline(COMBAT_SCRIPT, KEYMAPS)
    frames = len(frame_inputs) + COMBAT_TAIL
    snaps = run_battle(backend="statechart", frames=frames, frame_inputs=frame_inputs)
    assert len(snaps) == frames

    # verify hurt and ko are exercised (emergent assertion)
    all_states = {p[1] for snap in snaps for p in snap[0]}
    assert "hurt" in all_states, f"'hurt' never reached; states={sorted(all_states)}"
    assert "ko" in all_states, f"'ko' never reached; states={sorted(all_states)}"

    check_or_update("combat", snaps)


def _capture_full_match_inputs():
    """Run once with ChaseController; freeze its emitted inputs."""
    ctrl = ChaseController(attacker_num=1)
    run_battle("statechart", frames=6000, controller=ctrl, stop_on_match_over=True)
    return ctrl.emitted


def test_golden_full_match():
    """Full match (all 3 P2 stocks) reaches match_over; golden-compared."""
    frame_inputs = _capture_full_match_inputs()
    n = len(frame_inputs)
    snaps = run_battle(backend="statechart", frames=n, frame_inputs=frame_inputs)

    # emergent assertions: match resolves, P1 wins, P2 is eliminated
    final = snaps[-1]
    players, _atk, phase, winner = final
    p1 = next(p for p in players if p[0] == "P1")
    p2 = next(p for p in players if p[0] == "P2")

    assert phase == "match_over", f"match did not resolve; phase={phase}"
    assert winner == 1, f"expected P1 (winner 1), got {winner}"
    assert p2[9] == 0, f"P2 should be out of stocks, has {p2[9]}"
    assert p1[9] == 3, f"P1 should keep all stocks, has {p1[9]}"

    # verify hurt/ko arcs and full stock drain
    states = {p[1] for snap in snaps for p in snap[0]}
    assert "hurt" in states and "ko" in states, sorted(states)
    p2_lives = [next(p for p in s[0] if p[0] == "P2")[9] for s in snaps]
    transitions = [p2_lives[0]] + [b for a, b in zip(p2_lives, p2_lives[1:]) if a != b]
    assert transitions == [3, 2, 1, 0], f"P2 stock transitions unexpected: {transitions}"

    check_or_update("full_match", snaps)

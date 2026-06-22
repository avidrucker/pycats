# tests/test_full_match.py
"""A full match to defeat: P1 (chase controller) KOs P2 through all 3 stocks.

The deterministic ChaseController generates the inputs once on a legacy run; we
then FREEZE that input list and replay it through both backends, so this stays a
clean byte-identical parity test on identical fixed inputs while also proving the
match reaches `match_over` with the correct winner (and exercises hurt + ko).
"""
from pycats.sim.runner import run_battle
from pycats.sim.controllers import ChaseController


def _captured_full_match_inputs():
    ctrl = ChaseController(attacker_num=1)
    run_battle("legacy", frames=6000, controller=ctrl, stop_on_match_over=True)
    return ctrl.emitted


def test_full_match_reaches_defeat_byte_identical():
    inputs = _captured_full_match_inputs()
    n = len(inputs)
    legacy = run_battle("legacy", frames=n, frame_inputs=inputs)
    statechart = run_battle("statechart", frames=n, frame_inputs=inputs)

    # byte-identical parity across the whole match
    assert len(legacy) == len(statechart) == n
    for f, (a, b) in enumerate(zip(legacy, statechart)):
        assert a == b, f"divergence at frame {f}:\n legacy={a}\n  state={b}"

    final = legacy[-1]
    players, _atk, phase, winner = final
    p1 = next(p for p in players if p[0] == "P1")
    p2 = next(p for p in players if p[0] == "P2")

    assert phase == "match_over", f"match did not resolve; phase={phase}"
    assert winner == 1, f"expected P1 (winner 1), got {winner}"
    assert p2[9] == 0, f"P2 should be out of stocks, has {p2[9]}"
    assert p1[9] == 3, f"P1 should keep all stocks, has {p1[9]}"

    # full stock progression and the hurt/ko arcs are exercised
    states = {p[1] for snap in legacy for p in snap[0]}
    assert "hurt" in states and "ko" in states, sorted(states)
    p2_lives = [next(p for p in s[0] if p[0] == "P2")[9] for s in legacy]
    transitions = [p2_lives[0]] + [b for a, b in zip(p2_lives, p2_lives[1:]) if a != b]
    assert transitions == [3, 2, 1, 0], transitions

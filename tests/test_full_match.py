# tests/test_full_match.py
"""Backend parity across a real chase battle that exercises the hurt/KO arc.

The deterministic ChaseController generates inputs once on a legacy run; we FREEZE
that input list and replay it through both backends, so this is a clean
byte-identical parity test on identical fixed inputs — its primary value — while
also driving at least one KO (hurt + ko states + a stock loss).

NOTE (#44): this used to assert a full 3-stock defeat. Realistic knockback decay
(#44) parks a launched target at ledges/off-platform spots the scripted chase bot
can't reliably finish off, so the *full-defeat* assertion is deferred to #46
(robust full-match bot). The byte-identical parity check and the KO-arc assertion
below are unchanged in spirit and remain the regression value here.
"""
from pycats.sim.runner import run_battle
from pycats.sim.controllers import ChaseController


def _captured_match_inputs():
    ctrl = ChaseController(attacker_num=1)
    run_battle("legacy", frames=6000, controller=ctrl, stop_on_match_over=True)
    return ctrl.emitted


def test_match_byte_identical_and_exercises_ko_arc():
    inputs = _captured_match_inputs()
    n = len(inputs)
    legacy = run_battle("legacy", frames=n, frame_inputs=inputs)
    statechart = run_battle("statechart", frames=n, frame_inputs=inputs)

    # byte-identical parity across the whole replay (the primary regression value)
    assert len(legacy) == len(statechart) == n
    for f, (a, b) in enumerate(zip(legacy, statechart)):
        assert a == b, f"divergence at frame {f}:\n legacy={a}\n  state={b}"

    # the hurt -> ko arc is exercised, and P2 loses at least one stock
    states = {p[1] for snap in legacy for p in snap[0]}
    assert "hurt" in states and "ko" in states, sorted(states)
    p2_lives = [next(p for p in s[0] if p[0] == "P2")[9] for s in legacy]
    assert min(p2_lives) < p2_lives[0], (
        f"expected at least one KO (a stock loss); P2 lives stayed {p2_lives[0]}"
    )
